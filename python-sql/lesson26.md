# Урок 26. Финальный проект — Проектирование

## Что мы строим

Этот урок открывает финальный проект курса. Три урока — три этапа: сегодня проектируем, в Уроке 27 реализуем, в Уроке 28 финализируем и разбираем что получилось.

**Проект: REST API для блога.**

Блог — идеальная учебная предметная область: все понимают как он работает, связи между сущностями естественные, и это прямая аналогия с тем что студенты увидят в Django. Когда дойдём до Django — там будет всё знакомое.

**Используемые библиотеки:**

```bash
pip install fastapi uvicorn sqlalchemy alembic
```

---

## Шаг 1. Предметная область — что именно реализуем

Наш блог поддерживает:
- Пользователи могут регистрироваться
- Авторизованные пользователи пишут посты
- Посты можно тегировать (несколько тегов на пост)
- Читатели оставляют комментарии к постам
- Посты можно фильтровать по тегам и автору

Намеренно упрощаем то что не относится к теме курса:
- Нет настоящей аутентификации (JWT, OAuth) — автора поста передаём в теле запроса
- Нет прав доступа — любой может удалить любой пост
- Нет пагинации с курсором — только простой `limit/offset`

Это учебный проект. В Уроке 28 честно объясним что именно здесь упрощено и как это делается по-настоящему.

---

## Шаг 2. Схема базы данных

### Сущности и связи

```
users ──────────────────< posts
                          posts >──────────────< tags
                          posts ──< comments
```

Четыре таблицы, три типа связей:
- `users` → `posts` — один пользователь, много постов (один-ко-многим)
- `posts` → `comments` — один пост, много комментариев (один-ко-многим)
- `posts` ↔ `tags` — пост может иметь несколько тегов, тег — несколько постов (многие-ко-многим)

Связь многие-ко-многим реализуется через таблицу ассоциации `post_tags` — она не несёт бизнес-логики, только хранит пары `(post_id, tag_id)`.

### Таблицы и столбцы

**`users` — пользователи**

| Столбец | Тип | Ограничения |
|---|---|---|
| `id` | INTEGER | PK, AUTOINCREMENT |
| `username` | STRING(50) | NOT NULL, UNIQUE |
| `email` | STRING(200) | NOT NULL, UNIQUE |
| `created_at` | STRING(10) | NOT NULL |

**`posts` — посты**

| Столбец | Тип | Ограничения |
|---|---|---|
| `id` | INTEGER | PK, AUTOINCREMENT |
| `title` | STRING(200) | NOT NULL |
| `content` | TEXT | NOT NULL |
| `created_at` | STRING(10) | NOT NULL |
| `author_id` | INTEGER | NOT NULL, FK → users.id |

**`comments` — комментарии**

| Столбец | Тип | Ограничения |
|---|---|---|
| `id` | INTEGER | PK, AUTOINCREMENT |
| `content` | TEXT | NOT NULL |
| `created_at` | STRING(10) | NOT NULL |
| `post_id` | INTEGER | NOT NULL, FK → posts.id |
| `author_id` | INTEGER | NOT NULL, FK → users.id |

**`tags` — теги**

| Столбец | Тип | Ограничения |
|---|---|---|
| `id` | INTEGER | PK, AUTOINCREMENT |
| `name` | STRING(50) | NOT NULL, UNIQUE |

**`post_tags` — таблица ассоциации (posts ↔ tags)**

| Столбец | Тип | Ограничения |
|---|---|---|
| `post_id` | INTEGER | PK, FK → posts.id |
| `tag_id` | INTEGER | PK, FK → tags.id |

Составной первичный ключ `(post_id, tag_id)` гарантирует что один тег не будет добавлен к одному посту дважды.

### Визуальная схема

```
users                    posts                    tags
┌──────────────┐         ┌──────────────────┐    ┌────────────┐
│ id      (PK) │◄────┐   │ id          (PK) │    │ id    (PK) │
│ username     │     └───│ author_id   (FK) │    │ name       │
│ email        │         │ title            │    └─────┬──────┘
│ created_at   │         │ content          │          │
└──────────────┘         │ created_at       │    post_tags
        ▲                └────────┬─────────┘    ┌────────────┐
        │                         │◄─────────────│ post_id FK │
        │               comments  │              │ tag_id  FK │
        │        ┌──────────────┐ │              └────────────┘
        │        │ id      (PK) │ │
        └────────│ author_id FK │ │
                 │ post_id   FK │◄┘
                 │ content      │
                 │ created_at   │
                 └──────────────┘
```

---

## Шаг 3. Структура проекта

```
blog_api/
├── main.py               ← FastAPI-приложение, роутеры, обработчики ошибок
├── database.py           ← engine, SessionLocal, get_db()
├── exceptions.py         ← AppException, NotFoundError, AlreadyExistsError
│
├── models.py             ← SQLAlchemy ORM-модели
│
├── repositories/         ← слой данных через ORM
│   ├── __init__.py
│   ├── users.py
│   ├── posts.py
│   ├── comments.py
│   └── tags.py
│
├── schemas/              ← Pydantic-схемы
│   ├── __init__.py
│   ├── users.py
│   ├── posts.py
│   ├── comments.py
│   └── tags.py
│
├── routers/              ← FastAPI-роутеры
│   ├── __init__.py
│   ├── users.py
│   ├── posts.py
│   ├── comments.py
│   └── tags.py
│
└── alembic/              ← миграции
    ├── env.py
    └── versions/
```

**Ключевое отличие от предыдущих проектов:** `models.py` содержит SQLAlchemy ORM-модели — классы с `relationship`. Репозитории работают через `Session` а не через `cursor.execute()`.

---

## Шаг 4. ORM-модели — models.py

```python
# models.py
from sqlalchemy import (
    Column, Integer, String, Text, ForeignKey, Table
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


# Таблица ассоциации для связи многие-ко-многим posts ↔ tags
# Не является отдельным классом-моделью — только таблица
post_tags = Table(
    'post_tags',
    Base.metadata,
    Column('post_id', Integer, ForeignKey('posts.id', ondelete='CASCADE'), primary_key=True),
    Column('tag_id',  Integer, ForeignKey('tags.id',  ondelete='CASCADE'), primary_key=True),
)


class User(Base):
    __tablename__ = 'users'

    id         = Column(Integer, primary_key=True, autoincrement=True)
    username   = Column(String(50),  nullable=False, unique=True)
    email      = Column(String(200), nullable=False, unique=True)
    created_at = Column(String(10),  nullable=False)

    # Один пользователь — много постов
    posts    = relationship('Post',    back_populates='author',
                            cascade='all, delete-orphan')
    # Один пользователь — много комментариев
    comments = relationship('Comment', back_populates='author',
                            cascade='all, delete-orphan')

    def __repr__(self):
        return f'<User {self.username!r}>'


class Post(Base):
    __tablename__ = 'posts'

    id         = Column(Integer, primary_key=True, autoincrement=True)
    title      = Column(String(200), nullable=False)
    content    = Column(Text,        nullable=False)
    created_at = Column(String(10),  nullable=False)
    author_id  = Column(Integer, ForeignKey('users.id'), nullable=False)

    # Пост принадлежит пользователю
    author = relationship('User', back_populates='posts')

    # Пост имеет много комментариев
    comments = relationship('Comment', back_populates='post',
                            cascade='all, delete-orphan')

    # Пост связан со многими тегами (через post_tags)
    tags = relationship('Tag', secondary=post_tags, back_populates='posts')

    def __repr__(self):
        return f'<Post {self.title!r}>'


class Comment(Base):
    __tablename__ = 'comments'

    id         = Column(Integer, primary_key=True, autoincrement=True)
    content    = Column(Text,    nullable=False)
    created_at = Column(String(10), nullable=False)
    post_id    = Column(Integer, ForeignKey('posts.id'),  nullable=False)
    author_id  = Column(Integer, ForeignKey('users.id'),  nullable=False)

    post   = relationship('Post', back_populates='comments')
    author = relationship('User', back_populates='comments')

    def __repr__(self):
        return f'<Comment post={self.post_id} by user={self.author_id}>'


class Tag(Base):
    __tablename__ = 'tags'

    id   = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, unique=True)

    # Тег связан со многими постами (через post_tags)
    posts = relationship('Post', secondary=post_tags, back_populates='tags')

    def __repr__(self):
        return f'<Tag {self.name!r}>'
```

### Разбор ключевых решений

**`secondary=post_tags`** — SQLAlchemy знает что связь `Post.tags` проходит через таблицу `post_tags`. При добавлении тега к посту (`post.tags.append(tag)`) ORM сам вставит строку в `post_tags`. При удалении — сам удалит.

**`ondelete='CASCADE'` в `post_tags`** — при удалении поста или тега из основных таблиц связанные строки в `post_tags` удалятся автоматически на уровне БД. Это дополнение к `cascade='all, delete-orphan'` на уровне ORM — двойная защита.

**`cascade='all, delete-orphan'` в `User.posts`** — при удалении пользователя автоматически удалятся все его посты. При удалении поста — все его комментарии. Это каскад на уровне Python/ORM.

**Почему `post_tags` — `Table`, а не класс?** Таблица ассоциации без дополнительных данных не нуждается в классе. Если бы в `post_tags` был столбец `added_at` (когда тег добавлен) — нужен был бы отдельный класс. Пока его нет — хватает `Table`.

---

## Шаг 5. database.py

```python
# database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from typing import Generator

DATABASE_URL = 'sqlite:///blog.db'

engine = create_engine(
    DATABASE_URL,
    # SQLite-специфичная настройка: разрешает использовать одно соединение
    # из разных потоков — нужно для корректной работы с FastAPI
    connect_args={'check_same_thread': False}
)


def get_db() -> Generator:
    """
    Зависимость FastAPI: открывает Session на время запроса,
    закрывает в finally.

    Используем Session а не Connection — мы работаем с ORM.
    Session управляет identity map, unit of work и транзакциями.
    """
    with Session(engine) as session:
        try:
            yield session
            session.commit()    # фиксируем при успехе
        except Exception:
            session.rollback()  # откатываем при ошибке
            raise
```

**`check_same_thread: False`** — SQLite по умолчанию запрещает использовать соединение из другого потока. FastAPI использует потоки — эта настройка отключает это ограничение для нашего учебного проекта.

**`session.commit()` в `get_db()`** — в отличие от предыдущих проектов где мы вызывали `commit()` в репозитории или роутере, здесь commit централизован в зависимости. Это чистый паттерн: репозитории только изменяют объекты, транзакцию фиксирует тот кто владеет сессией.

---

## Шаг 6. exceptions.py

```python
# exceptions.py


class AppException(Exception):
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(message)


class NotFoundError(AppException):
    def __init__(self, resource: str, resource_id: int):
        super().__init__(404, f'{resource} с id={resource_id} не найден')


class AlreadyExistsError(AppException):
    def __init__(self, field: str, value: str):
        super().__init__(400, f'Значение {field}={value!r} уже занято')
```

---

## Шаг 7. Настройка Alembic и первая миграция

### Инициализация

```bash
cd blog_api
alembic init alembic
```

### alembic.ini

```ini
sqlalchemy.url = sqlite:///blog.db
```

### alembic/env.py

Добавляем путь к проекту и импорт моделей:

```python
# alembic/env.py — добавить в начало после стандартных импортов:
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import Base
target_metadata = Base.metadata
```

### Генерация первой миграции

```bash
alembic revision --autogenerate -m "create blog tables"
```

Alembic создаст файл в `alembic/versions/`. Откройте его и проверьте что там пять операций `create_table`: `users`, `tags`, `posts`, `comments`, `post_tags`.

Порядок важен — Alembic определяет его сам по зависимостям:
1. `users` (нет зависимостей)
2. `tags` (нет зависимостей)
3. `posts` (зависит от `users`)
4. `comments` (зависит от `posts` и `users`)
5. `post_tags` (зависит от `posts` и `tags`)

### Применение миграции

```bash
alembic upgrade head
```

```
INFO  Running upgrade  -> abc123def456, create blog tables
```

База данных `blog.db` создана со всеми таблицами.

### Проверка

```python
# Быстрая проверка через Python
from sqlalchemy import create_engine, inspect

engine = create_engine('sqlite:///blog.db')
inspector = inspect(engine)

print('Таблицы в базе данных:')
for table_name in inspector.get_table_names():
    print(f'  {table_name}')
    for col in inspector.get_columns(table_name):
        print(f'    {col["name"]}: {col["type"]}')
```

Ожидаемый вывод:
```
Таблицы в базе данных:
  alembic_version
    version_num: VARCHAR
  comments
    id: INTEGER
    content: TEXT
    ...
  post_tags
    post_id: INTEGER
    tag_id: INTEGER
  posts
    id: INTEGER
    title: VARCHAR(200)
    ...
  tags
    id: INTEGER
    name: VARCHAR(50)
  users
    id: INTEGER
    username: VARCHAR(50)
    ...
```

---

## Шаг 8. Добавление поля — вторая миграция

Симулируем реальный сценарий: после создания схемы приходит новое требование — у поста должен быть статус (`draft` / `published`).

Добавляем в модель:

```python
# models.py — в класс Post добавить:
status = Column(String(20), nullable=False, default='published')
```

Генерируем миграцию:

```bash
alembic revision --autogenerate -m "add status to posts"
```

Проверяем файл — должен содержать:

```python
def upgrade() -> None:
    op.add_column('posts',
        sa.Column('status', sa.String(length=20), nullable=False, server_default='published')
    )

def downgrade() -> None:
    op.drop_column('posts', 'status')
```

Применяем:

```bash
alembic upgrade head
```

```
INFO  Running upgrade abc123def456 -> 789xyz000aaa, add status to posts
```

Посмотрим историю:

```bash
alembic history
```

```
789xyz000aaa -> (head), add status to posts
abc123def456 -> 789xyz000aaa, create blog tables
<base> -> abc123def456
```

---

## Итог урока: что спроектировано

К концу этого урока у нас есть:

| Артефакт | Файл | Статус |
|---|---|---|
| Схема БД | (на бумаге / в уроке) | ✓ спроектировано |
| ORM-модели | `models.py` | ✓ написано |
| Настройка БД | `database.py` | ✓ написано |
| Исключения | `exceptions.py` | ✓ написано |
| Alembic | `alembic/` | ✓ настроен |
| Первая миграция | `alembic/versions/` | ✓ применена |
| База данных | `blog.db` | ✓ создана |
| Структура проекта | папки | ✓ создана |

Что ещё не написано:
- Репозитории (слой данных через ORM)
- Pydantic-схемы (валидация и сериализация)
- Роутеры (HTTP-эндпоинты)
- main.py (сборка приложения)

Это задача Урока 27.

---

## Вопросы для закрепления (с ответами)

**1.** Почему таблица `post_tags` реализована как `Table`, а не как отдельный класс-модель?

<details>
<summary>Ответ</summary>

Таблица ассоциации без дополнительных данных не нуждается в классе. Класс нужен когда с записью нужно работать как с объектом — получать, фильтровать, добавлять поля. `post_tags` содержит только пару `(post_id, tag_id)` и служит технической связью. ORM управляет ею автоматически через `secondary=post_tags` в `relationship`. Если бы добавилось поле `added_at` — понадобился бы класс.
</details>

---

**2.** Что делает `cascade='all, delete-orphan'` в `User.posts`?

<details>
<summary>Ответ</summary>

При удалении пользователя через ORM автоматически удалятся все его посты (cascade). При удалении поста из коллекции `user.posts` без удаления самого поста — он всё равно удалится из БД (delete-orphan: объект без владельца удаляется). Это гарантирует что в базе не останется постов без автора.
</details>

---

**3.** Зачем `ondelete='CASCADE'` в `ForeignKey` для `post_tags` если каскад уже настроен через ORM?

<details>
<summary>Ответ</summary>

Двойная защита. Каскад ORM работает только когда удаление идёт через SQLAlchemy (через `session.delete()`). Если кто-то удалит запись напрямую через SQL или другой инструмент — ORM-каскад не сработает. `ondelete='CASCADE'` на уровне базы данных гарантирует удаление связанных строк в любом случае.
</details>

---

**4.** Почему `get_db()` делает `session.commit()` внутри зависимости, а не оставляет это репозиторию?

<details>
<summary>Ответ</summary>

Централизация управления транзакцией. Репозитории — слой данных, они не должны знать о транзакционных границах. Сессия создаётся в `get_db()`, там же и фиксируется. Если в ходе одного запроса вызывается несколько репозиториев — все их изменения фиксируются одним `commit()`. При ошибке — одним `rollback()`.
</details>

---

**5.** В каком порядке Alembic создаёт таблицы и почему?

<details>
<summary>Ответ</summary>

В порядке зависимостей внешних ключей: сначала таблицы на которые ссылаются другие (`users`, `tags`), потом таблицы которые ссылаются на них (`posts`), потом зависящие от `posts` (`comments`, `post_tags`). Alembic анализирует `ForeignKey` и строит граф зависимостей. Нарушение порядка вызвало бы ошибку — нельзя создать внешний ключ на несуществующую таблицу.
</details>

---

**6.** Что произойдёт если добавить в `Post` поле без генерации миграции и запустить приложение?

<details>
<summary>Ответ</summary>

Приложение запустится, но при попытке обратиться к новому полю через ORM возникнет ошибка — в реальной таблице этого столбца нет. SQLAlchemy при `create_all` не трогает существующие таблицы. Единственный правильный путь — сгенерировать и применить миграцию через Alembic.
</details>

---

**7.** Зачем нужен `check_same_thread: False` в `connect_args` для SQLite?

<details>
<summary>Ответ</summary>

SQLite по умолчанию запрещает использовать одно соединение из разных потоков — это защита от race conditions. FastAPI обрабатывает запросы в потоках, и без этой настройки SQLite выбрасывал бы ошибку. В продакшне с PostgreSQL этой проблемы нет — PostgreSQL полностью поддерживает многопоточный доступ.
</details>

---

**8.** Почему у `post_tags` составной первичный ключ `(post_id, tag_id)`, а не отдельный `id`?

<details>
<summary>Ответ</summary>

Составной PK автоматически гарантирует уникальность пары — один тег не может быть добавлен к одному посту дважды. Это бизнес-правило выражено на уровне схемы БД. Отдельный `id` был бы избыточен и не обеспечивал бы эту гарантию без дополнительного `UNIQUE constraint`.
</details>

---

**9.** Как в моделях выражена связь многие-ко-многим и какую роль играет `back_populates`?

<details>
<summary>Ответ</summary>

Связь выражена через `relationship(..., secondary=post_tags)` с обеих сторон: в `Post.tags` и `Tag.posts`. `secondary` указывает промежуточную таблицу. `back_populates='posts'` в `Tag` и `back_populates='tags'` в `Post` связывают эти два `relationship` в пару — изменение с одной стороны автоматически отражается на другой. Без `back_populates` SQLAlchemy не знал бы что `Post.tags` и `Tag.posts` — это две стороны одной связи.
</details>

---

**10.** Что такое `server_default` в миграции и чем он отличается от `default` в модели?

<details>
<summary>Ответ</summary>

`default` в модели SQLAlchemy — значение по умолчанию на уровне Python: применяется когда объект создаётся через ORM. `server_default` — значение по умолчанию на уровне базы данных: применяется при INSERT даже если он идёт не через ORM (например напрямую через SQL). При добавлении `nullable=False` столбца в существующую таблицу Alembic использует `server_default` чтобы заполнить значение в уже существующих строках.
</details>

---

[Предыдущий урок](lesson25.md) | [Следующий урок](lesson27.md)