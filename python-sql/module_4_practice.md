# Итоговая практическая работа — Менеджер событий

## О работе

Это финальная самостоятельная работа курса. Вы реализуете REST API для платформы управления событиями — от проектирования схемы до работающего приложения.

В отличие от Модуля 2 где вы работали с raw sqlite3, здесь используется полный стек который вы освоили в Модулях 3 и 4: **FastAPI + SQLAlchemy ORM + Alembic + Pydantic**.

Работа разбита на шаги в том же порядке что и финальный проект (Уроки 26-28). Если на каком-то шаге возникли вопросы — обращайтесь к соответствующему уроку. Каждый шаг указывает на нужный источник.

---

## Предметная область

Платформа для организации и посещения мероприятий. Организаторы создают события (митапы, концерты, вебинары), участники на них регистрируются. События можно тегировать и фильтровать.

---

## Шаг 1. Проектирование схемы БД
*(Урок 26 — Проектирование)*

### Сущности

**`users` — пользователи**

Хранит и организаторов и участников — роль определяется контекстом использования.

| Столбец | Тип | Ограничения |
|---|---|---|
| `id` | INTEGER | PK, AUTOINCREMENT |
| `username` | STRING(50) | NOT NULL, UNIQUE |
| `email` | STRING(200) | NOT NULL, UNIQUE |
| `created_at` | STRING(10) | NOT NULL |

**`tags` — теги**

| Столбец | Тип | Ограничения |
|---|---|---|
| `id` | INTEGER | PK, AUTOINCREMENT |
| `name` | STRING(50) | NOT NULL, UNIQUE |

**`events` — события**

| Столбец | Тип | Ограничения |
|---|---|---|
| `id` | INTEGER | PK, AUTOINCREMENT |
| `title` | STRING(200) | NOT NULL |
| `description` | TEXT | nullable |
| `event_date` | STRING(10) | NOT NULL |
| `status` | STRING(20) | NOT NULL, DEFAULT `'planned'` |
| `organizer_id` | INTEGER | NOT NULL, FK → users.id |

Допустимые значения `status`: `'planned'`, `'ongoing'`, `'finished'`, `'cancelled'`

**`registrations` — записи на событие (ассоциативная таблица с данными)**

| Столбец | Тип | Ограничения |
|---|---|---|
| `id` | INTEGER | PK, AUTOINCREMENT |
| `event_id` | INTEGER | NOT NULL, FK → events.id |
| `user_id` | INTEGER | NOT NULL, FK → users.id |
| `registered_at` | STRING(10) | NOT NULL |
| `status` | STRING(20) | NOT NULL, DEFAULT `'confirmed'` |

Допустимые значения `status`: `'confirmed'`, `'cancelled'`

Комбинация `(event_id, user_id)` должна быть уникальной — один пользователь не может зарегистрироваться на одно событие дважды. Реализуйте через `UniqueConstraint`.

<details>
<summary><b>Подсказка: запрет повторной регистрации</b></summary>

Один пользователь не должен иметь возможность зарегистрироваться на одно и то же событие несколько раз.

Например:

```text
(event_id=1, user_id=5)
```

может существовать в таблице только один раз.

При этом должны быть допустимы записи:

```text
(event_id=1, user_id=5)
(event_id=2, user_id=5)
(event_id=1, user_id=7)
```

То есть уникальным должен быть не отдельный столбец, а комбинация двух столбцов: `event_id` и `user_id`.

Для создания такого ограничения в SQLAlchemy используется `UniqueConstraint`, который добавляется через специальный атрибут модели `__table_args__`.

Пример использования:

```python
__table_args__ = (
    UniqueConstraint(
        'event_id',
        'user_id'
    ),
)
```

После добавления такого ограничения база данных не позволит создать две одинаковые записи с одной и той же парой значений `(event_id, user_id)`.

Проверьте работу ограничения: попробуйте зарегистрировать одного и того же пользователя на одно событие дважды.

</details>

---

**`event_tags` — связь событий и тегов (многие-ко-многим)**

Таблица ассоциации без дополнительных данных. Составной первичный ключ `(event_id, tag_id)`.

### Задание

Нарисуйте схему связей на бумаге или в любом инструменте. Обозначьте:
- Типы связей (один-ко-многим, многие-ко-многим)
- Внешние ключи
- Каскадное удаление (что должно удаляться при удалении события или пользователя)

---

## Шаг 2. Структура проекта

Создайте следующую структуру папок и файлов:

```
event_manager/
├── main.py
├── database.py
├── exceptions.py
├── constants.py
├── models.py
├── repositories/
│   ├── __init__.py
│   ├── users.py
│   ├── tags.py
│   ├── events.py
│   └── registrations.py
├── schemas/
│   ├── __init__.py
│   ├── users.py
│   ├── tags.py
│   ├── events.py
│   └── registrations.py
└── routers/
    ├── __init__.py
    ├── users.py
    ├── tags.py
    ├── events.py
    └── registrations.py
```

Alembic инициализируете отдельно на Шаге 5.

---

## Шаг 3. constants.py и exceptions.py
*(Урок 19 — Обработка ошибок, Урок 26)*

### constants.py

Вынесите допустимые значения статусов в константы:

```python
EVENT_STATUSES        = ['planned', 'ongoing', 'finished', 'cancelled']
REGISTRATION_STATUSES = ['confirmed', 'cancelled']
```

Эти константы будут использоваться и в схемах (валидация), и в роутерах (проверка входных данных).

### exceptions.py

Реализуйте иерархию исключений:
- `AppException(Exception)` — базовый класс с `status_code` и `message`
- `NotFoundError(AppException)` — 404, сообщение: `'{resource} с id={id} не найден'`
- `AlreadyExistsError(AppException)` — 400, сообщение о дублировании
- `BusinessLogicError(AppException)` — 400, для нарушений бизнес-правил (например: нельзя зарегистрироваться на отменённое событие)

---

## Шаг 4. models.py — ORM-модели
*(Урок 24 — SQLAlchemy ORM, Урок 26)*

Реализуйте все пять сущностей как SQLAlchemy ORM-модели наследуя от `DeclarativeBase`.

**Требования:**

- `event_tags` — объявить как `Table` (не класс), так как дополнительных данных нет
- `Registration` — объявить как класс-модель (есть поля `registered_at` и `status`)
- Все `relationship` должны иметь `back_populates`
- Каскадное удаление через `cascade='all, delete-orphan'` для:
  - `User.events` (удаляем пользователя → удаляются его события)
  - `User.registrations` (удаляем пользователя → удаляются его регистрации)
  - `Event.registrations` (удаляем событие → удаляются все его регистрации)
- `ondelete='CASCADE'` в `ForeignKey` для таблицы `event_tags`
- `UniqueConstraint('event_id', 'user_id')` в модели `Registration`
- `__repr__` для каждой модели

---

## Шаг 5. Alembic — инициализация и первая миграция
*(Урок 25 — Миграции)*

1. Инициализируйте Alembic: `alembic init alembic`
2. Настройте `alembic.ini`: укажите `sqlite:///events.db`
3. Настройте `alembic/env.py`: импортируйте `Base` из `models.py`, установите `target_metadata = Base.metadata`
4. Сгенерируйте первую миграцию: `alembic revision --autogenerate -m "create initial tables"`
5. Проверьте сгенерированный файл — должны быть все пять таблиц в правильном порядке
6. Примените: `alembic upgrade head`
7. Проверьте через Python что таблицы созданы

---

## Шаг 6. database.py
*(Урок 18 — Подключение SQLite к FastAPI, Урок 26)*

Реализуйте:
- Константу `DATABASE_URL = 'sqlite:///events.db'`
- `engine` с `connect_args={'check_same_thread': False}`
- `get_db()` — генератор с `yield session`, `commit()` при успехе, `rollback()` при ошибке
- Фабрики зависимостей для каждого репозитория: `get_user_repo`, `get_tag_repo`, `get_event_repo`, `get_registration_repo`

Используйте ленивые импорты репозиториев внутри фабрик чтобы избежать циклических зависимостей.

---

## Шаг 7. schemas/ — Pydantic-схемы
*(Урок 17 — Pydantic-схемы)*

### schemas/users.py

- `UserCreate` — поля: `username` (1-50 символов), `email` (минимум 3 символа), `created_at`
- `UserResponse` — поля: `id`, `username`, `email`, `created_at`

### schemas/tags.py

- `TagCreate` — поле: `name` (1-50 символов)
- `TagResponse` — поля: `id`, `name`

### schemas/events.py

- `EventCreate` — поля: `title` (1-200 символов), `description` (необязательное), `event_date`, `status` (с валидатором через `field_validator` что значение входит в `EVENT_STATUSES`), `organizer_id` (больше 0), `tag_ids` (список id тегов, по умолчанию пустой)
- `EventStatusUpdate` — одно поле `status` с валидатором
- `EventResponse` — поля: `id`, `title`, `description`, `event_date`, `status`, `organizer_id`, `organizer_username` (из relationship), `tags` (список строк — имена тегов)
- `EventShortResponse` — как `EventResponse` но без `description` (для списков)

### schemas/registrations.py

- `RegistrationCreate` — поля: `user_id` (больше 0)
- `RegistrationStatusUpdate` — поле `status` с валидатором
- `RegistrationResponse` — поля: `id`, `event_id`, `user_id`, `registered_at`, `status`, `username` (из relationship через `registration.user.username`)

Не забудьте `__init__.py` с реэкспортом всех схем.

---

## Шаг 8. repositories/ — слой данных
*(Урок 14 — Паттерн Repository, Урок 24 — SQLAlchemy ORM)*

### repositories/users.py — `UserRepository`

Методы:
- `get_all() -> list`
- `get_by_id(user_id: int)`
- `create(username, email, created_at)` — обработать `IntegrityError`, вернуть `None` при дубле
- `delete(user_id: int) -> bool`

### repositories/tags.py — `TagRepository`

Методы:
- `get_all() -> list`
- `get_by_id(tag_id: int)`
- `get_by_ids(tag_ids: list) -> list` — для привязки тегов к событию
- `create(name: str)` — обработать `IntegrityError`
- `delete(tag_id: int) -> bool`

### repositories/events.py — `EventRepository`

Методы:
- `get_all(organizer_id=None, tag_name=None, status=None) -> list` — с динамической фильтрацией

  Реализуйте динамический WHERE через список условий и параметров (паттерн из Урока 12 и Урока 20). Все три фильтра необязательны.

  Используйте жадную загрузку:
  - `joinedload` для `Event.organizer` (многие-к-одному)
  - `selectinload` для `Event.tags` (многие-ко-многим)

- `get_by_id(event_id: int)` — с жадной загрузкой `organizer` и `tags`
- `create(title, description, event_date, status, organizer_id, created_at, tags: list)` — принимает список объектов `Tag`
- `update_status(event_id: int, new_status: str) -> bool`
- `delete(event_id: int) -> bool`

### repositories/registrations.py — `RegistrationRepository`

Методы:
- `get_by_event(event_id: int) -> list` — с загрузкой `user`
- `get_by_event_and_user(event_id: int, user_id: int)` — для проверки дублирования
- `create(event_id, user_id, registered_at, status='confirmed')`
- `update_status(registration_id: int, new_status: str) -> bool`

---

## Шаг 9. routers/ — HTTP-эндпоинты
*(Урок 16 — FastAPI, Урок 19 — Обработка ошибок)*

### routers/users.py

| Метод | URL | Действие | Код |
|---|---|---|---|
| GET | `/` | Все пользователи | 200 |
| GET | `/{user_id}` | Один пользователь | 200 / 404 |
| POST | `/` | Создать пользователя | 201 / 400 |
| DELETE | `/{user_id}` | Удалить пользователя | 204 / 404 |

### routers/tags.py

| Метод | URL | Действие | Код |
|---|---|---|---|
| GET | `/` | Все теги | 200 |
| POST | `/` | Создать тег | 201 / 400 |
| DELETE | `/{tag_id}` | Удалить тег | 204 / 404 |

### routers/events.py

| Метод | URL | Действие | Код |
|---|---|---|---|
| GET | `/` | Список событий (с фильтрами) | 200 |
| GET | `/{event_id}` | Одно событие | 200 / 404 |
| POST | `/` | Создать событие | 201 |
| PUT | `/{event_id}/status` | Обновить статус | 200 / 404 / 400 |
| DELETE | `/{event_id}` | Удалить событие | 204 / 404 |

Query-параметры для `GET /`:
- `organizer_id: int` — необязательный
- `tag: str` — необязательный, фильтр по имени тега
- `status: str` — необязательный

### routers/registrations.py

| Метод | URL | Действие | Код |
|---|---|---|---|
| GET | `/{event_id}/registrations` | Все записи на событие | 200 / 404 |
| POST | `/{event_id}/registrations` | Зарегистрироваться на событие | 201 / 404 / 400 |
| PUT | `/{event_id}/registrations/{reg_id}/status` | Обновить статус записи | 200 / 404 / 400 |

**Бизнес-правила для регистрации (используйте `BusinessLogicError`):**
- Нельзя зарегистрироваться на событие со статусом `'finished'` или `'cancelled'`
- Нельзя зарегистрировать одного пользователя дважды на одно событие

**Важно:** роутер `registrations` подключается в `main.py` с префиксом `/events` — тогда пути `/events/{event_id}/registrations` складываются правильно.

<details>
<summary><b>Подсказка: проверка бизнес-правил при регистрации</b></summary>

Перед созданием новой регистрации необходимо выполнить несколько дополнительных проверок.

**Правило 1. Нельзя зарегистрироваться на завершённое или отменённое событие**

Если событие имеет статус finished или cancelled создание новой регистрации должно быть запрещено.

Пример:

```text
Событие:
id=10
status='cancelled'

Попытка регистрации:
user_id=5
```

Результат:

```text
Ошибка 400
```

---

**Правило 2. Нельзя зарегистрировать одного пользователя дважды**

Перед созданием регистрации необходимо проверить, существует ли уже запись с такой комбинацией:

```text
(event_id, user_id)
```

Если такая запись найдена, создание новой регистрации должно быть запрещено.

Пример:

```text
(event_id=10, user_id=5)
```

уже существует в таблице.

Повторная попытка создать такую же регистрацию должна завершаться ошибкой.

---

**Рекомендуемый порядок действий**

Перед вызовом метода создания регистрации:

1. Получить событие по `event_id`.
2. Если событие не найдено — вернуть ошибку `404`.
3. Проверить статус события.
4. Если статус равен:

   * `finished`
   * `cancelled`

   выбросить `BusinessLogicError`.

5. Проверить, существует ли уже регистрация данного пользователя на это событие.
6. Если регистрация существует — выбросить `BusinessLogicError`.
7. Если все проверки пройдены успешно — создать регистрацию.

---

Для ошибок бизнес-логики используйте исключение `BusinessLogicError` с понятным сообщением для пользователя.

Подумайте, в каком месте приложения лучше выполнять эти проверки: в роутере или в репозитории.

</details>

---

<details>
<summary><b>Подсказка: вложенные маршруты и префикс /events</b></summary>

Регистрация всегда относится к конкретному событию, поэтому маршруты регистрации удобно делать вложенными.

Например:

```text
/events/1/registrations
/events/5/registrations
/events/10/registrations
```

Из URL сразу видно, для какого события выполняется действие.

---

При описании эндпоинтов в роутере `registrations.py` не обязательно повторять весь путь целиком. Внутри роутера можно описывать только часть маршрута:

```python
@router.get('/{event_id}/registrations')
```

---

Затем в `main.py` роутер подключается с префиксом:

```python
app.include_router(
    registrations.router,
    prefix='/events'
)
```

После объединения префикса и маршрута получится итоговый путь:

```text
/events/{event_id}/registrations
```

Например:

```text
GET  /events/1/registrations
POST /events/1/registrations
```

</details>

---

## Шаг 10. main.py — сборка приложения
*(Урок 19 — Структура проекта, Урок 28)*

Реализуйте:
- `FastAPI(title='Event Manager API', version='1.0')`
- Три обработчика исключений: `AppException`, `HTTPException`, `Exception`
- `@app.on_event('startup')` — логирование старта (таблицы создаются через Alembic, не через `create_all`)
- Подключение всех четырёх роутеров с правильными префиксами и тегами
- Эндпоинт `GET /health`

---

## Шаг 11. Проверка

Запустите приложение и пройдите по сценариям:

```bash
alembic upgrade head
uvicorn main:app --reload
```

**Сценарии для проверки в `/docs`:**

1. Создать двух пользователей
2. Создать три тега (`митап`, `онлайн`, `бесплатно`)
3. Создать событие с двумя тегами и `organizer_id=1`
4. Попробовать создать событие с тем же `organizer_id` — должно работать (события не уникальны)
5. `GET /events?tag=митап` — должно вернуть событие
6. `GET /events?organizer_id=1` — фильтрация по организатору
7. `POST /events/1/registrations {"user_id": 2}` — зарегистрировать второго пользователя
8. `POST /events/1/registrations {"user_id": 2}` повторно — получить 400 (дубль)
9. `PUT /events/1/status {"status": "cancelled"}` — отменить событие
10. `POST /events/1/registrations {"user_id": 1}` — получить 400 (событие отменено)
11. `DELETE /events/1` — удалить событие, убедиться что регистрации удалились каскадно
12. `GET /events/1` — получить 404
13. `GET /health` — `{"status": "ok"}`

---

## Критерии оценки

**Обязательно:**
- Все эндпоинты из таблиц реализованы и работают
- Схема БД соответствует заданию (все таблицы, связи, ограничения)
- ORM-модели используют `relationship` с `back_populates`
- Миграции через Alembic (не `create_all` в `startup`)
- Все запросы параметризованы — никаких f-строк в SQL
- `response_model` указан для всех GET и POST эндпоинтов
- Единый формат ошибок через обработчики в `main.py`
- Оба бизнес-правила для регистрации проверяются
- Динамическая фильтрация событий работает корректно

**Хорошо:**
- Жадная загрузка (`joinedload`/`selectinload`) для связанных объектов
- `field_validator` для статусов в Pydantic-схемах
- `cascade='all, delete-orphan'` настроен корректно
- `BusinessLogicError` — отдельный класс исключения
- `__init__.py` с реэкспортом в каждой папке
- `constants.py` используется и в схемах и в репозиториях

---

## Что сдаётся

Папка `event_manager/` со всеми файлами. Приложение должно запускаться командой:

```bash
alembic upgrade head
uvicorn main:app --reload
```

без дополнительных настроек.

---

[Содержание](outline.md)