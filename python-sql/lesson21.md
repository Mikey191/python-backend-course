# Урок 21. Практическая работа — Модуль 3. Мини-проект 2 — Каталог товаров

## О чём этот урок

В прошлом уроке мы строили To-Do API вместе — шаг за шагом, с объяснением каждого решения. Теперь ваша очередь.

Этот урок — самостоятельная работа. Задание разбито на шаги в том же порядке что и прошлый проект. Если вы застряли — вернитесь к Уроку 20 и найдите аналогичный фрагмент. Все паттерны которые нужны для этого проекта уже были показаны.

**Тема:** REST API для каталога товаров с категориями.

---

## Техническое задание

### Предметная область

Интернет-магазин хранит товары разбитые по категориям. Администратор управляет категориями и товарами через API.

### Схема базы данных

Две таблицы, одна связь:

```
categories                      products
┌───────────────────────┐       ┌──────────────────────────────────┐
│ id      INT      (PK) │◄──────│ category_id  INT   (FK, NOT NULL)│
│ name    TEXT  NOT NULL│       │ id           INT   (PK)          │
│         UNIQUE        │       │ name         TEXT  NOT NULL       │
└───────────────────────┘       │ description  TEXT  (nullable)    │
                                │ price        REAL  NOT NULL > 0  │
                                │ stock        INT   NOT NULL >= 0  │
                                │ created_at   TEXT  NOT NULL       │
                                └──────────────────────────────────┘
```

### Эндпоинты

**Категории:**

| Метод | URL | Действие | Успешный код |
|---|---|---|---|
| `GET` | `/categories` | Все категории | `200` |
| `GET` | `/categories/{id}` | Одна категория | `200` |
| `POST` | `/categories` | Создать категорию | `201` |
| `DELETE` | `/categories/{id}` | Удалить категорию | `204` |

**Товары:**

| Метод | URL | Действие | Успешный код |
|---|---|---|---|
| `GET` | `/products` | Все товары (с фильтрами) | `200` |
| `GET` | `/products/{id}` | Один товар | `200` |
| `POST` | `/products` | Создать товар | `201` |
| `PUT` | `/products/{id}/stock` | Обновить остаток | `200` |
| `DELETE` | `/products/{id}` | Удалить товар | `204` |

**Query-параметры для `GET /products`:**
- `category_id: int` (необязательный) — фильтр по категории
- `min_price: float` (необязательный) — товары дороже указанной цены
- `in_stock: bool` (необязательный) — только товары с остатком > 0

**Системный:**

| Метод | URL | Действие |
|---|---|---|
| `GET` | `/health` | Статус сервиса |

### Структура проекта

```
catalog_api/
├── main.py
├── database.py
├── exceptions.py
├── repositories/
│   ├── __init__.py
│   ├── categories.py
│   └── products.py
├── schemas/
│   ├── __init__.py
│   ├── categories.py
│   └── products.py
└── routers/
    ├── __init__.py
    ├── categories.py
    └── products.py
```

---

## Шаг 1. Спроектируйте связи и API

Перед написанием кода ответьте письменно на вопросы:

1. Какие поля обязательны при создании товара, а какие необязательны?
2. Что вернёт `GET /products/999` если товара нет?
3. Что вернёт `POST /categories` если категория с таким именем уже есть?
4. В каком порядке нужно удалять данные если захотим удалить категорию у которой есть товары?
5. Какие поля войдут в `ProductResponse` которых нет в `products` напрямую?

---

## Шаг 2. database.py

Реализуйте файл со следующим содержимым:

- Константа `DB_PATH = 'catalog.db'`
- Функция `init_db()` — создаёт таблицы через `CREATE TABLE IF NOT EXISTS`. Порядок: сначала `categories`, потом `products` (внешний ключ)
- Функция `get_connection()` — генератор с `yield` и `finally`
- Функции `get_category_repo()` и `get_product_repo()` — фабрики зависимостей через `Depends`

**Подсказка:** структура полностью аналогична `database.py` из Урока 20. Измените имена таблиц и путь к файлу.

---

## Шаг 3. exceptions.py

Реализуйте иерархию исключений:

- `AppException(Exception)` — базовый класс с `status_code` и `message`
- `NotFoundError(AppException)` — `404`, сообщение: `'{resource} с id={id} не найден'`
- `AlreadyExistsError(AppException)` — `400`, сообщение: `'Запись с {field}={value!r} уже существует'`

---

## Шаг 4. repositories/categories.py

Реализуйте `CategoryRepository` с методами:

- `get_all() -> list` — все категории, сортировка по `name`
- `get_by_id(category_id: int)` — одна или `None`
- `create(name: str) -> int | None` — возвращает `id` или `None` при `IntegrityError`
- `delete(category_id: int) -> bool` — `True` если удалена

---

## Шаг 5. repositories/products.py

Реализуйте `ProductRepository` с методами:

- `get_all(category_id, min_price, in_stock) -> list`

  Все три параметра необязательные. Динамически строите WHERE:
  - `category_id` — `p.category_id = ?`
  - `min_price` — `p.price >= ?`
  - `in_stock=True` — `p.stock > 0`

  Запрос должен использовать JOIN с `categories` чтобы вернуть `category_name`.

- `get_by_id(product_id: int)` — одна запись с `category_name` или `None`

- `create(name, description, price, stock, category_id, created_at) -> int`

- `update_stock(product_id: int, new_stock: int) -> bool`

- `delete(product_id: int) -> bool`

**Подсказка:** паттерн динамического WHERE через список условий и параметров — точно такой же как в `TaskRepository.get_all()` из Урока 20.

---

## Шаг 6. schemas/categories.py

Реализуйте:

- `CategoryCreate` — поле `name: str`, минимум 1 символ, максимум 100
- `CategoryResponse` — поля `id: int`, `name: str`

---

## Шаг 7. schemas/products.py

Реализуйте:

- `ProductCreate` — поля:
  - `name: str` — минимум 1 символ, максимум 200
  - `description: Optional[str] = None` — необязательное
  - `price: float` — больше 0 (`gt=0`)
  - `stock: int` — не меньше 0 (`ge=0`), по умолчанию 0
  - `category_id: int` — больше 0 (`gt=0`)
  - `created_at: str` — дата создания

- `ProductStockUpdate` — одно поле `stock: int`, не меньше 0

- `ProductResponse` — все поля из `ProductCreate` плюс `id: int` и `category_name: str`

Не забудьте добавить `__init__.py` в каждую папку с реэкспортом классов.

---

## Шаг 8. routers/categories.py

Реализуйте роутер с эндпоинтами:

- `GET /` — `response_model=List[CategoryResponse]`
- `GET /{category_id}` — `response_model=CategoryResponse`, `404` если не найдена
- `POST /` — `response_model=CategoryResponse`, `status_code=201`, `400` если имя занято
- `DELETE /{category_id}` — `status_code=204`, `404` если не найдена

---

## Шаг 9. routers/products.py

Реализуйте роутер с эндпоинтами:

- `GET /` — принимает query-параметры `category_id`, `min_price`, `in_stock`. Передаёт их в `repo.get_all()`
- `GET /{product_id}` — `404` если не найден
- `POST /` — создаёт товар, возвращает полный объект через `get_by_id`
- `PUT /{product_id}/stock` — принимает `ProductStockUpdate`, обновляет остаток, возвращает обновлённый товар
- `DELETE /{product_id}` — `204`, `404` если не найден

---

## Шаг 10. main.py

Соберите приложение:

- `FastAPI(title='Catalog API', version='1.0')`
- `@app.on_event('startup')` — вызов `init_db()`
- Три обработчика исключений: `AppException`, `HTTPException`, `Exception`
- Подключение роутеров с префиксами `/categories` и `/products`
- Эндпоинт `GET /health`

---

## Шаг 11. Проверка

Запустите приложение и проверьте следующие сценарии:

1. `POST /categories {"name": "Электроника"}` → `201`, получить `id`
2. `POST /categories {"name": "Электроника"}` повторно → `400`
3. `POST /products` с корректными данными → `201`
4. `POST /products` с `price: -100` → `422`
5. `POST /products` с `category_id: 9999` → приложение не должно упасть
6. `GET /products?category_id=1` → только товары из категории 1
7. `GET /products?min_price=1000&in_stock=true` → фильтрация
8. `PUT /products/1/stock {"stock": 50}` → обновлённый товар
9. `GET /products/9999` → `{"error": true, "code": 404, ...}`
10. `DELETE /products/1` → `204`

---

## Критерии оценки

**Обязательно:**
- [ ] Все эндпоинты из технического задания реализованы
- [ ] Структура проекта соответствует заданию
- [ ] Все запросы параметризованы — никаких f-строк в SQL
- [ ] `response_model` указан для всех GET и POST эндпоинтов
- [ ] `404` при обращении к несуществующему ресурсу
- [ ] `400` при нарушении уникальности имени категории
- [ ] `422` при невалидных данных (проверяется Pydantic автоматически)
- [ ] Единый формат ошибок через обработчики в `main.py`
- [ ] `GET /products` поддерживает все три фильтра

**Хорошо:**
- [ ] `category_name` присутствует в `ProductResponse`
- [ ] Динамический WHERE без дублирования кода
- [ ] `__init__.py` с реэкспортом в каждой папке
- [ ] Эндпоинт `/health` присутствует
- [ ] Код читается и структурирован понятно

---

[Предыдущий урок](lesson20.md) | [Следующий урок](lesson22.md)