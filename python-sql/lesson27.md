# Урок 27. Финальный проект — Реализация

## Что делаем в этом уроке

В Уроке 26 мы спроектировали схему, написали ORM-модели и применили первые миграции. Теперь строим поверх них полноценное API.

**Что используем и откуда это знаем:**

| Технология | Где изучали |
|---|---|
| FastAPI: роутеры, эндпоинты, параметры | Урок 16 |
| Pydantic-схемы, `response_model` | Урок 17 |
| Dependency Injection, `get_db()` | Урок 18 |
| Обработка ошибок, структура проекта | Урок 19 |
| SQLAlchemy ORM: Session, select, relationship | Урок 24 |
| Паттерн Repository | Урок 14 |

Всё что пишем ниже — комбинация этих тем. Ничего принципиально нового — только всё вместе в одном проекте.

---

## Шаг 1. schemas/ — Pydantic-схемы

Схемы описывают что принимает и что возвращает каждый эндпоинт. Принцип из Урока 17: отдельные схемы для создания (`Create`) и для ответа (`Response`).

### schemas/users.py

```python
# schemas/users.py
from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    """Данные для создания пользователя — тело POST /users."""
    username:   str = Field(min_length=1, max_length=50)
    email:      str = Field(min_length=3)
    created_at: str = Field(description='Дата в формате YYYY-MM-DD')


class UserResponse(BaseModel):
    """Данные пользователя в ответе."""
    id:         int
    username:   str
    email:      str
    created_at: str
```

### schemas/tags.py

```python
# schemas/tags.py
from pydantic import BaseModel, Field


class TagCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)


class TagResponse(BaseModel):
    id:   int
    name: str
```

### schemas/posts.py

```python
# schemas/posts.py
from pydantic import BaseModel, Field
from typing import Optional, List


class PostCreate(BaseModel):
    """
    Данные для создания поста.
    author_id — клиент передаёт явно (упрощение: нет настоящей аутентификации).
    tag_ids — список id тегов которые нужно привязать к посту.
    """
    title:     str = Field(min_length=1, max_length=200)
    content:   str = Field(min_length=1)
    status:    str = Field(default='published', description='draft или published')
    author_id: int = Field(gt=0)
    tag_ids:   List[int] = Field(default=[], description='Список id тегов')


class PostResponse(BaseModel):
    """
    Полный ответ поста — с именем автора и списком тегов.
    author_username и tags приходят через ORM relationship,
    не хранятся в таблице posts напрямую.
    """
    id:              int
    title:           str
    content:         str
    status:          str
    created_at:      str
    author_id:       int
    author_username: str          # из relationship post.author.username
    tags:            List[str]    # список имён тегов


class PostShortResponse(BaseModel):
    """
    Краткий ответ для списка постов — без content чтобы не грузить лишнее.
    """
    id:              int
    title:           str
    status:          str
    created_at:      str
    author_username: str
    tags:            List[str]
```

### schemas/comments.py

```python
# schemas/comments.py
from pydantic import BaseModel, Field


class CommentCreate(BaseModel):
    content:   str = Field(min_length=1)
    author_id: int = Field(gt=0)


class CommentResponse(BaseModel):
    id:              int
    content:         str
    created_at:      str
    post_id:         int
    author_id:       int
    author_username: str   # из relationship comment.author.username
```

### schemas/__init__.py

```python
# schemas/__init__.py
from .users    import UserCreate, UserResponse
from .tags     import TagCreate, TagResponse
from .posts    import PostCreate, PostResponse, PostShortResponse
from .comments import CommentCreate, CommentResponse
```

---

## Шаг 2. repositories/ — слой данных через ORM

Репозитории из Урока 14 переписываем под ORM из Урока 24. Главное отличие: вместо `cursor.execute('SELECT ...')` — `session.execute(select(Model))`. Соединение заменяется на `Session`.

### repositories/users.py

```python
# repositories/users.py
import sqlite3
from sqlalchemy.orm import Session
from sqlalchemy import select
from models import User


class UserRepository:
    """
    Паттерн Repository (Урок 14) + SQLAlchemy ORM (Урок 24).
    Принимает Session через конструктор — DI-принцип тот же.
    """

    def __init__(self, session: Session):
        self.session = session

    def get_all(self) -> list:
        stmt = select(User).order_by(User.username)
        return self.session.execute(stmt).scalars().all()

    def get_by_id(self, user_id: int):
        return self.session.get(User, user_id)

    def get_by_email(self, email: str):
        stmt = select(User).where(User.email == email)
        return self.session.execute(stmt).scalars().first()

    def create(self, username: str, email: str, created_at: str):
        """
        Создаёт пользователя.
        IntegrityError — нарушение UNIQUE на username или email.
        Возвращает объект User или None при дублировании.
        """
        try:
            user = User(username=username, email=email, created_at=created_at)
            self.session.add(user)
            self.session.flush()   # получаем id без commit (Урок 24)
            return user
        except Exception:
            self.session.rollback()
            return None

    def delete(self, user_id: int) -> bool:
        user = self.session.get(User, user_id)
        if user is None:
            return False
        self.session.delete(user)
        return True
```

### repositories/tags.py

```python
# repositories/tags.py
from sqlalchemy.orm import Session
from sqlalchemy import select
from models import Tag


class TagRepository:

    def __init__(self, session: Session):
        self.session = session

    def get_all(self) -> list:
        return self.session.execute(select(Tag).order_by(Tag.name)).scalars().all()

    def get_by_id(self, tag_id: int):
        return self.session.get(Tag, tag_id)

    def get_by_ids(self, tag_ids: list) -> list:
        """Получить несколько тегов по списку id — для привязки к посту."""
        if not tag_ids:
            return []
        stmt = select(Tag).where(Tag.id.in_(tag_ids))
        return self.session.execute(stmt).scalars().all()

    def create(self, name: str):
        try:
            tag = Tag(name=name)
            self.session.add(tag)
            self.session.flush()
            return tag
        except Exception:
            self.session.rollback()
            return None

    def delete(self, tag_id: int) -> bool:
        tag = self.session.get(Tag, tag_id)
        if tag is None:
            return False
        self.session.delete(tag)
        return True
```

### repositories/posts.py

```python
# repositories/posts.py
from sqlalchemy.orm import Session, selectinload, joinedload
from sqlalchemy import select
from typing import Optional
from models import Post, Tag


class PostRepository:
    """
    Здесь активно используется жадная загрузка (Урок 24).
    Посты всегда загружаются с автором и тегами —
    чтобы роутер не генерировал N+1 запросов.
    """

    def __init__(self, session: Session):
        self.session = session

    def _base_query(self):
        """
        Базовый запрос с предзагрузкой связей.
        joinedload для author (многие-к-одному),
        selectinload для tags (многие-ко-многим).
        """
        return (
            select(Post)
            .options(
                joinedload(Post.author),
                selectinload(Post.tags)
            )
        )

    def get_all(
        self,
        author_id: Optional[int] = None,
        tag_name: Optional[str] = None,
        status: Optional[str] = None
    ) -> list:
        stmt = self._base_query()

        if author_id is not None:
            stmt = stmt.where(Post.author_id == author_id)
        if status is not None:
            stmt = stmt.where(Post.status == status)
        if tag_name is not None:
            # Фильтр по имени тега — через join с tags
            stmt = stmt.where(Post.tags.any(Tag.name == tag_name))

        stmt = stmt.order_by(Post.created_at.desc())
        return self.session.execute(stmt).unique().scalars().all()

    def get_by_id(self, post_id: int):
        stmt = self._base_query().where(Post.id == post_id)
        return self.session.execute(stmt).unique().scalars().first()

    def create(
        self,
        title: str,
        content: str,
        status: str,
        author_id: int,
        created_at: str,
        tags: list   # список объектов Tag
    ):
        post = Post(
            title=title,
            content=content,
            status=status,
            author_id=author_id,
            created_at=created_at
        )
        post.tags = tags   # ORM сам запишет в post_tags (Урок 24)
        self.session.add(post)
        self.session.flush()
        # Перечитываем с relationship чтобы вернуть полный объект
        return self.get_by_id(post.id)

    def delete(self, post_id: int) -> bool:
        post = self.session.get(Post, post_id)
        if post is None:
            return False
        self.session.delete(post)
        return True
```

### repositories/comments.py

```python
# repositories/comments.py
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select
from models import Comment


class CommentRepository:

    def __init__(self, session: Session):
        self.session = session

    def get_by_post(self, post_id: int) -> list:
        stmt = (
            select(Comment)
            .options(joinedload(Comment.author))
            .where(Comment.post_id == post_id)
            .order_by(Comment.created_at)
        )
        return self.session.execute(stmt).unique().scalars().all()

    def create(self, content: str, post_id: int, author_id: int, created_at: str):
        comment = Comment(
            content=content,
            post_id=post_id,
            author_id=author_id,
            created_at=created_at
        )
        self.session.add(comment)
        self.session.flush()
        # Перечитываем с author для ответа
        stmt = (
            select(Comment)
            .options(joinedload(Comment.author))
            .where(Comment.id == comment.id)
        )
        return self.session.execute(stmt).unique().scalars().first()

    def delete(self, comment_id: int) -> bool:
        comment = self.session.get(Comment, comment_id)
        if comment is None:
            return False
        self.session.delete(comment)
        return True
```

### repositories/__init__.py

```python
# repositories/__init__.py
from .users    import UserRepository
from .tags     import TagRepository
from .posts    import PostRepository
from .comments import CommentRepository
```

---

## Шаг 3. database.py — зависимости для репозиториев

Дополняем `database.py` из Урока 26 фабриками репозиториев — по аналогии с Уроком 18:

```python
# database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from typing import Generator
from fastapi import Depends

DATABASE_URL = 'sqlite:///blog.db'

engine = create_engine(
    DATABASE_URL,
    connect_args={'check_same_thread': False}
)


def get_db() -> Generator:
    """Зависимость: Session на время запроса (Урок 18)."""
    with Session(engine) as session:
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise


# --- Фабрики репозиториев ---
# Принцип тот же что в Уроке 18 — цепочка зависимостей

def get_user_repo(session: Session = Depends(get_db)):
    from repositories import UserRepository
    return UserRepository(session)


def get_tag_repo(session: Session = Depends(get_db)):
    from repositories import TagRepository
    return TagRepository(session)


def get_post_repo(session: Session = Depends(get_db)):
    from repositories import PostRepository
    return PostRepository(session)


def get_comment_repo(session: Session = Depends(get_db)):
    from repositories import CommentRepository
    return CommentRepository(session)
```

---

## Шаг 4. routers/ — HTTP-эндпоинты

Роутеры строятся по схеме из Урока 19: один файл — одна сущность, `response_model` везде, исключения через `AppException`.

### routers/users.py

```python
# routers/users.py
from fastapi import APIRouter, Depends
from typing import List

from database import get_user_repo
from repositories import UserRepository
from schemas import UserCreate, UserResponse
from exceptions import NotFoundError, AlreadyExistsError

router = APIRouter()


@router.get('/', response_model=List[UserResponse])
def get_users(repo: UserRepository = Depends(get_user_repo)):
    return repo.get_all()


@router.get('/{user_id}', response_model=UserResponse)
def get_user(user_id: int, repo: UserRepository = Depends(get_user_repo)):
    user = repo.get_by_id(user_id)
    if user is None:
        raise NotFoundError('Пользователь', user_id)
    return user


@router.post('/', response_model=UserResponse, status_code=201)
def create_user(data: UserCreate, repo: UserRepository = Depends(get_user_repo)):
    user = repo.create(
        username=data.username,
        email=data.email,
        created_at=data.created_at
    )
    if user is None:
        raise AlreadyExistsError('username или email', data.username)
    return user


@router.delete('/{user_id}', status_code=204)
def delete_user(user_id: int, repo: UserRepository = Depends(get_user_repo)):
    if not repo.delete(user_id):
        raise NotFoundError('Пользователь', user_id)
```

### routers/tags.py

```python
# routers/tags.py
from fastapi import APIRouter, Depends
from typing import List

from database import get_tag_repo
from repositories import TagRepository
from schemas import TagCreate, TagResponse
from exceptions import NotFoundError, AlreadyExistsError

router = APIRouter()


@router.get('/', response_model=List[TagResponse])
def get_tags(repo: TagRepository = Depends(get_tag_repo)):
    return repo.get_all()


@router.post('/', response_model=TagResponse, status_code=201)
def create_tag(data: TagCreate, repo: TagRepository = Depends(get_tag_repo)):
    tag = repo.create(data.name)
    if tag is None:
        raise AlreadyExistsError('name', data.name)
    return tag


@router.delete('/{tag_id}', status_code=204)
def delete_tag(tag_id: int, repo: TagRepository = Depends(get_tag_repo)):
    if not repo.delete(tag_id):
        raise NotFoundError('Тег', tag_id)
```

### routers/posts.py

```python
# routers/posts.py
from fastapi import APIRouter, Depends
from typing import List, Optional

from database import get_post_repo, get_tag_repo
from repositories import PostRepository, TagRepository
from schemas import PostCreate, PostResponse, PostShortResponse
from exceptions import NotFoundError

router = APIRouter()


def _serialize_post(post) -> dict:
    """
    Преобразует ORM-объект Post в словарь для Pydantic.
    Нужен потому что PostResponse содержит вычисляемые поля:
    author_username (из relationship) и tags (список имён из relationship).
    Pydantic не умеет автоматически пройтись по relationship — помогаем ему.
    """
    return {
        'id':              post.id,
        'title':           post.title,
        'content':         post.content,
        'status':          post.status,
        'created_at':      post.created_at,
        'author_id':       post.author_id,
        'author_username': post.author.username,  # relationship
        'tags':            [tag.name for tag in post.tags],  # relationship
    }


def _serialize_post_short(post) -> dict:
    return {
        'id':              post.id,
        'title':           post.title,
        'status':          post.status,
        'created_at':      post.created_at,
        'author_username': post.author.username,
        'tags':            [tag.name for tag in post.tags],
    }


@router.get('/', response_model=List[PostShortResponse])
def get_posts(
    author_id: Optional[int] = None,
    tag:       Optional[str] = None,
    status:    Optional[str] = None,
    repo: PostRepository = Depends(get_post_repo)
):
    """
    Список постов с опциональной фильтрацией.
    GET /posts?author_id=1&tag=python&status=published
    """
    posts = repo.get_all(author_id=author_id, tag_name=tag, status=status)
    return [_serialize_post_short(p) for p in posts]


@router.get('/{post_id}', response_model=PostResponse)
def get_post(post_id: int, repo: PostRepository = Depends(get_post_repo)):
    post = repo.get_by_id(post_id)
    if post is None:
        raise NotFoundError('Пост', post_id)
    return _serialize_post(post)


@router.post('/', response_model=PostResponse, status_code=201)
def create_post(
    data: PostCreate,
    post_repo: PostRepository = Depends(get_post_repo),
    tag_repo:  TagRepository  = Depends(get_tag_repo)
):
    """
    Создание поста с тегами.
    tag_ids из запроса → загружаем объекты Tag через TagRepository →
    передаём в PostRepository.create() → ORM записывает в post_tags.

    Два репозитория в одном эндпоинте — оба получают одну Session
    через цепочку зависимостей (Урок 18).
    """
    # Загружаем теги по id
    tags = tag_repo.get_by_ids(data.tag_ids) if data.tag_ids else []

    post = post_repo.create(
        title=data.title,
        content=data.content,
        status=data.status,
        author_id=data.author_id,
        created_at=__import__('datetime').date.today().isoformat(),
        tags=tags
    )
    return _serialize_post(post)


@router.delete('/{post_id}', status_code=204)
def delete_post(post_id: int, repo: PostRepository = Depends(get_post_repo)):
    if not repo.delete(post_id):
        raise NotFoundError('Пост', post_id)
```

### routers/comments.py

```python
# routers/comments.py
from fastapi import APIRouter, Depends
from typing import List

from database import get_comment_repo, get_post_repo
from repositories import CommentRepository, PostRepository
from schemas import CommentCreate, CommentResponse
from exceptions import NotFoundError

router = APIRouter()


def _serialize_comment(comment) -> dict:
    return {
        'id':              comment.id,
        'content':         comment.content,
        'created_at':      comment.created_at,
        'post_id':         comment.post_id,
        'author_id':       comment.author_id,
        'author_username': comment.author.username,
    }


@router.get('/{post_id}/comments', response_model=List[CommentResponse])
def get_comments(
    post_id: int,
    comment_repo: CommentRepository = Depends(get_comment_repo),
    post_repo:    PostRepository    = Depends(get_post_repo)
):
    """Комментарии поста. Сначала проверяем что пост существует."""
    if post_repo.get_by_id(post_id) is None:
        raise NotFoundError('Пост', post_id)
    return [_serialize_comment(c) for c in comment_repo.get_by_post(post_id)]


@router.post('/{post_id}/comments', response_model=CommentResponse, status_code=201)
def create_comment(
    post_id: int,
    data: CommentCreate,
    comment_repo: CommentRepository = Depends(get_comment_repo),
    post_repo:    PostRepository    = Depends(get_post_repo)
):
    """Создать комментарий к посту."""
    if post_repo.get_by_id(post_id) is None:
        raise NotFoundError('Пост', post_id)

    comment = comment_repo.create(
        content=data.content,
        post_id=post_id,
        author_id=data.author_id,
        created_at=__import__('datetime').date.today().isoformat()
    )
    return _serialize_comment(comment)


@router.delete('/comments/{comment_id}', status_code=204)
def delete_comment(
    comment_id: int,
    repo: CommentRepository = Depends(get_comment_repo)
):
    if not repo.delete(comment_id):
        raise NotFoundError('Комментарий', comment_id)
```

### routers/__init__.py

```python
# routers/__init__.py
# Пустой — роутеры импортируются в main.py напрямую
```

---

## Шаг 5. main.py — сборка приложения

```python
# main.py
import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse

from database import engine
from models import Base
from exceptions import AppException
from routers import users, tags, posts, comments

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title='Blog API',
    version='1.0',
    description='REST API для блога — финальный проект курса SQL + Python'
)


# -----------------------------------------------------------------
# Startup — таблицы создаются через Alembic (Урок 25)
# Здесь НЕ вызываем Base.metadata.create_all(engine)
# Миграции — единственный правильный способ управлять схемой
# -----------------------------------------------------------------

@app.on_event('startup')
def startup():
    logger.info('Blog API запущен. База данных: blog.db')


# -----------------------------------------------------------------
# Обработчики исключений — единый формат (Урок 19)
# -----------------------------------------------------------------

@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={'error': True, 'code': exc.status_code, 'message': exc.message}
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={'error': True, 'code': exc.status_code, 'message': exc.detail}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f'Необработанное исключение: {exc}', exc_info=True)
    return JSONResponse(
        status_code=500,
        content={'error': True, 'code': 500, 'message': 'Внутренняя ошибка сервера'}
    )


# -----------------------------------------------------------------
# Роутеры
# -----------------------------------------------------------------

app.include_router(users.router,    prefix='/users',    tags=['users'])
app.include_router(tags.router,     prefix='/tags',     tags=['tags'])
app.include_router(posts.router,    prefix='/posts',    tags=['posts'])
app.include_router(comments.router, prefix='/posts',    tags=['comments'])
#                                           ^^^^^^
# Комментарии привязаны к постам: /posts/{id}/comments
# prefix='/posts' + маршруты '/{post_id}/comments' внутри роутера


@app.get('/health', tags=['system'])
def health():
    return {'status': 'ok', 'service': 'blog-api'}
```

---

## Шаг 6. Запуск и проверка

```bash
# Убедитесь что миграции применены (Урок 25)
alembic upgrade head

# Запуск
uvicorn main:app --reload
```

### Сценарий проверки в /docs

**Создаём данные:**

```json
POST /users
{"username": "alexey", "email": "alex@mail.ru", "created_at": "2024-06-25"}
→ 201: {"id": 1, "username": "alexey", ...}

POST /tags
{"name": "python"}
→ 201: {"id": 1, "name": "python"}

POST /tags
{"name": "backend"}
→ 201: {"id": 2, "name": "backend"}
```

**Создаём пост с тегами:**

```json
POST /posts
{
    "title": "Введение в FastAPI",
    "content": "FastAPI — современный фреймворк...",
    "status": "published",
    "author_id": 1,
    "tag_ids": [1, 2]
}
→ 201: {
    "id": 1,
    "title": "Введение в FastAPI",
    "author_username": "alexey",
    "tags": ["python", "backend"],
    ...
}
```

**Фильтрация:**

```
GET /posts?tag=python             → посты с тегом python
GET /posts?author_id=1            → посты автора
GET /posts?status=published       → только опубликованные
```

**Комментарии:**

```json
POST /posts/1/comments
{"content": "Отличная статья!", "author_id": 1}
→ 201: {"id": 1, "content": "Отличная статья!", "author_username": "alexey", ...}

GET /posts/1/comments
→ [{"id": 1, "content": "Отличная статья!", ...}]
```

**Ошибки:**

```
GET /posts/9999
→ {"error": true, "code": 404, "message": "Пост с id=9999 не найден"}

POST /users {"username": "alexey", ...}  (дубль)
→ {"error": true, "code": 400, "message": "Значение username или email='alexey' уже занято"}
```

---

## Итог урока: что построено

```
blog_api/
├── main.py          ✓ FastAPI, роутеры, обработчики
├── database.py      ✓ engine, get_db(), фабрики репозиториев
├── exceptions.py    ✓ AppException, NotFoundError, AlreadyExistsError
├── models.py        ✓ из Урока 26
├── repositories/    ✓ UserRepo, TagRepo, PostRepo, CommentRepo (ORM)
├── schemas/         ✓ Create и Response схемы для всех сущностей
├── routers/         ✓ users, tags, posts, comments
└── alembic/         ✓ из Урока 26
```

**Полный цикл запроса (из Урока 18):**

```
HTTP GET /posts?tag=python
    │
    ▼ FastAPI разбирает query-параметр
    │
    ▼ Depends(get_db) → открывает Session
    ▼ Depends(get_post_repo) → создаёт PostRepository(session)
    │
    ▼ PostRepository.get_all(tag_name='python')
        │ select(Post).options(joinedload, selectinload)
        │ .where(Post.tags.any(Tag.name == 'python'))
        ▼
      SQLite → возвращает строки
        │
        ▼ ORM собирает объекты Post с загруженными author и tags
    │
    ▼ _serialize_post_short() → dict для Pydantic
    │
    ▼ response_model=List[PostShortResponse] → валидация и JSON
    │
    ▼ HTTP 200 OK + JSON
```

В Уроке 28 разберём что в этом коде сделано "учебно" и как это выглядело бы в продакшне.

---

[Предыдущий урок](lesson26.md) | [Следующий урок](lesson28.md)