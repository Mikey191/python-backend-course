# Урок 20. Мини-проект 1 — To-Do API

## Что мы строим

Этот урок — не теория. Мы пишем рабочее приложение с нуля, шаг за шагом. Каждый шаг объяснён: что делаем, почему именно так, как это связано с предыдущим.

**To-Do API** — REST API для управления задачами с категориями:
- Задачи можно создавать, просматривать, обновлять статус, удалять
- Каждая задача принадлежит категории
- Задачи можно фильтровать по статусу и по категории

---

## Шаг 1. Проектирование — что строим и как это связано

Прежде чем писать код — понимаем структуру. Две сущности, одна связь:

```
categories (категории)          tasks (задачи)
┌───────────────────┐           ┌────────────────────────────┐
│ id    INT    (PK) │◄──────────│ category_id  INT  (FK)     │
│ name  TEXT        │           │ id           INT  (PK)     │
└───────────────────┘           │ title        TEXT          │
                                │ status       TEXT          │
                                │ priority     INT  (1-3)    │
                                │ created_at   TEXT          │
                                └────────────────────────────┘
```

**Эндпоинты которые нужно реализовать:**

```
Категории:
GET    /categories          — список всех категорий
POST   /categories          — создать категорию
DELETE /categories/{id}     — удалить категорию

Задачи:
GET    /tasks               — все задачи (с фильтрами по статусу и категории)
GET    /tasks/{id}          — одна задача
POST   /tasks               — создать задачу
PUT    /tasks/{id}/status   — обновить статус задачи
DELETE /tasks/{id}          — удалить задачу
```

**Структура файлов проекта:**

```
todo_api/
├── main.py
├── database.py
├── exceptions.py
├── repositories/
│   ├── __init__.py
│   ├── categories.py
│   └── tasks.py
├── schemas/
│   ├── __init__.py
│   ├── categories.py
│   └── tasks.py
└── routers/
    ├── __init__.py
    ├── categories.py
    └── tasks.py
```

**Как классы и модули связаны друг с другом:**

```
main.py
  │ подключает роутеры и обработчики исключений
  ├── routers/categories.py ──► schemas/categories.py  (валидация входа/выхода)
  │        │                ──► repositories/categories.py (работа с БД)
  │        └── Depends ──► database.py (соединение)
  │
  └── routers/tasks.py ──► schemas/tasks.py
           │           ──► repositories/tasks.py
           └── Depends ──► database.py

database.py   — get_connection() + зависимости для репозиториев
exceptions.py — NotFoundError, AlreadyExistsError, ValidationError
```

Каждый роутер знает только свои схемы и свой репозиторий. Репозиторий знает только SQL. Схемы знают только структуру данных. Зависимости скрыты в `database.py`.

---

## Шаг 2. База данных — database.py

Начинаем с фундамента. `database.py` отвечает за три вещи: создание таблиц, открытие соединения, фабрики зависимостей для репозиториев.

```python
# database.py
import sqlite3
from typing import Generator
from fastapi import Depends

# Путь к файлу базы данных — в одном месте
DB_PATH = 'todo.db'


def init_db() -> None:
    """
    Создаёт таблицы если они не существуют.
    Вызывается один раз при старте приложения.
    Используем CREATE TABLE IF NOT EXISTS — безопасно для повторного запуска.
    """
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    # Сначала таблица без внешних ключей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id   INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT    NOT NULL UNIQUE
        )
    ''')

    # Затем таблица с внешним ключом — categories уже существует
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            title       TEXT    NOT NULL,
            status      TEXT    NOT NULL DEFAULT 'new',
            priority    INTEGER NOT NULL DEFAULT 2
                        CHECK (priority IN (1, 2, 3)),
            created_at  TEXT    NOT NULL,
            category_id INTEGER NOT NULL,
            FOREIGN KEY (category_id) REFERENCES categories(id)
        )
    ''')

    connection.commit()
    connection.close()


def get_connection() -> Generator:
    """
    Зависимость FastAPI: открывает соединение на время запроса,
    закрывает в finally — даже при исключении.

    Используем yield (не return) чтобы иметь код "до" и "после":
    - до yield: открыть соединение
    - yield: передать соединение в эндпоинт
    - finally: закрыть соединение
    """
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row   # строки как словари: row['name']
    try:
        yield connection
    finally:
        connection.commit()
        connection.close()


# Фабрики репозиториев — ленивый импорт чтобы избежать циклических зависимостей
def get_category_repo(
    connection: sqlite3.Connection = Depends(get_connection)
):
    from repositories import CategoryRepository
    return CategoryRepository(connection)


def get_task_repo(
    connection: sqlite3.Connection = Depends(get_connection)
):
    from repositories import TaskRepository
    return TaskRepository(connection)
```

**Ключевые решения:**
- `DB_PATH` — константа в одном месте. При переименовании файла меняем здесь и только здесь.
- `init_db()` без `Depends` — вызывается один раз при старте, не на каждый запрос.
- Ленивый импорт в фабриках (`from repositories import ...` внутри функции) — избегает циклического импорта: `database.py` импортирует репозитории, репозитории импортируют... ничего из database.

---

## Шаг 3. Исключения — exceptions.py

Централизованные исключения вместо разбросанных `HTTPException` по роутерам:

```python
# exceptions.py


class AppException(Exception):
    """
    Базовый класс для всех бизнес-исключений приложения.
    Хранит HTTP-код и сообщение — обработчик в main.py сделает из них ответ.
    """
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(message)


class NotFoundError(AppException):
    """Ресурс не найден — 404."""
    def __init__(self, resource: str, resource_id: int):
        super().__init__(
            status_code=404,
            message=f'{resource} с id={resource_id} не найден'
        )


class AlreadyExistsError(AppException):
    """Нарушение уникальности — 400."""
    def __init__(self, field: str, value: str):
        super().__init__(
            status_code=400,
            message=f'Запись с {field}={value!r} уже существует'
        )


class InvalidStatusError(AppException):
    """Неверный статус задачи — 400."""
    def __init__(self, status: str, allowed: list):
        super().__init__(
            status_code=400,
            message=f'Статус {status!r} недопустим. Допустимые: {allowed}'
        )
```

**Почему три разных класса, а не один с параметром `type`?**

Читаемость. `raise NotFoundError('Задача', task_id)` — сразу понятно что произошло. `raise AppException(404, f'Задача с id={task_id} не найдена')` — то же самое, но больше деталей в голове держать при чтении. Отдельные классы — это документация по коду.

---

## Шаг 4. Репозитории — repositories/

### repositories/categories.py

```python
# repositories/categories.py
import sqlite3


class CategoryRepository:
    """
    Слой данных для таблицы categories.
    Получает соединение снаружи (DI) — не создаёт его сам.
    Каждый метод создаёт свой курсор — курсор дешёвый объект.
    """

    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection

    def get_all(self) -> list:
        """Все категории, отсортированные по имени."""
        cursor = self.connection.cursor()
        cursor.execute('SELECT * FROM categories ORDER BY name')
        return cursor.fetchall()

    def get_by_id(self, category_id: int):
        """Одна категория по id или None."""
        cursor = self.connection.cursor()
        cursor.execute('SELECT * FROM categories WHERE id = ?', (category_id,))
        return cursor.fetchone()

    def create(self, name: str) -> int | None:
        """
        Создаёт категорию.
        Возвращает id или None если имя уже занято (UNIQUE).
        IntegrityError перехватывается здесь — роутер получает None.
        """
        cursor = self.connection.cursor()
        try:
            cursor.execute(
                'INSERT INTO categories (name) VALUES (?)',
                (name,)
            )
            return cursor.lastrowid   # id только что созданной строки
        except sqlite3.IntegrityError:  # ошибка нарушения ограничений целостности данных
            return None

    def delete(self, category_id: int) -> bool:
        """
        Удаляет категорию.
        Возвращает True если строка была найдена и удалена.
        rowcount == 0 означает что WHERE не нашёл строк.
        """
        cursor = self.connection.cursor()
        cursor.execute(
            'DELETE FROM categories WHERE id = ?',
            (category_id,)
        )
        return cursor.rowcount > 0
```

### repositories/tasks.py

```python
# repositories/tasks.py
import sqlite3
from typing import Optional


class TaskRepository:
    """
    Слой данных для таблицы tasks.
    get_all() использует JOIN с categories — возвращает category_name
    чтобы роутер не делал дополнительный запрос.
    """

    # Базовый SELECT с JOIN — используется в нескольких методах
    # Вынесен в константу чтобы не дублировать
    BASE_SELECT = '''
        SELECT
            t.id,
            t.title,
            t.status,
            t.priority,
            t.created_at,
            t.category_id,
            c.name AS category_name
        FROM tasks AS t
        INNER JOIN categories AS c ON t.category_id = c.id
    '''

    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection

    def get_all(
        self,
        status: Optional[str] = None,
        category_id: Optional[int] = None
    ) -> list:
        """
        Все задачи с фильтрацией.
        Фильтры необязательны — если не переданы, возвращаем все.

        Динамически строим WHERE через список условий:
        - не используем f-строки для подстановки данных (SQL-инъекция)
        - условия собираем в список строк, параметры — в список значений
        - соединяем через AND
        """
        conditions = []
        params = []

        if status is not None:
            conditions.append('t.status = ?')
            params.append(status)

        if category_id is not None:
            conditions.append('t.category_id = ?')
            params.append(category_id)

        query = self.BASE_SELECT
        if conditions:
            query += ' WHERE ' + ' AND '.join(conditions)
        query += ' ORDER BY t.priority DESC, t.created_at'

        cursor = self.connection.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()

    def get_by_id(self, task_id: int):
        """Одна задача по id с названием категории или None."""
        cursor = self.connection.cursor()
        cursor.execute(
            self.BASE_SELECT + ' WHERE t.id = ?',
            (task_id,)
        )
        return cursor.fetchone()

    def create(
        self,
        title: str,
        priority: int,
        category_id: int,
        created_at: str
    ) -> int:
        """ca
        Создаёт задачу.
        Статус 'new' — значение по умолчанию из схемы БД.
        Возвращает id созданной строки.
        """
        cursor = self.connection.cursor()
        cursor.execute(
            '''INSERT INTO tasks (title, status, priority, category_id, created_at)
               VALUES (?, 'new', ?, ?, ?)''',
            (title, priority, category_id, created_at)
        )
        return cursor.lastrowid

    def update_status(self, task_id: int, new_status: str) -> bool:
        """
        Обновляет статус задачи.
        Возвращает True если задача найдена (rowcount > 0).
        """
        cursor = self.connection.cursor()
        cursor.execute(
            'UPDATE tasks SET status = ? WHERE id = ?',
            (new_status, task_id)
        )
        return cursor.rowcount > 0

    def delete(self, task_id: int) -> bool:
        """Удаляет задачу. Возвращает True если задача была."""
        cursor = self.connection.cursor()
        cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
        return cursor.rowcount > 0
```

### repositories/__init__.py

```python
# repositories/__init__.py
from .categories import CategoryRepository
from .tasks import TaskRepository
```

**Ключевые решения в репозиториях:**
- `BASE_SELECT` — константа класса. SQL с JOIN используется в `get_all` и `get_by_id`. Выносим чтобы не дублировать — правка в одном месте.
- Динамический WHERE в `get_all` — список условий и список параметров собираются отдельно. Никаких f-строк — всё через `?`.
- Репозитории не знают про исключения приложения — они возвращают `None` или `bool`. Роутер решает что с этим делать.

## Шаг 5. Схемы — schemas/

### schemas/categories.py

```python
# schemas/categories.py
from pydantic import BaseModel, Field


class CategoryCreate(BaseModel):
    """
    Схема для создания категории (тело POST-запроса).
    Клиент присылает только name — id назначает база данных.
    """
    name: str = Field(
        min_length=1,
        max_length=100,
        description='Название категории'
    )


class CategoryResponse(BaseModel):
    """
    Схема для ответа — то что видит клиент.
    Включает id который появился после сохранения в БД.
    """
    id: int
    name: str
```

### schemas/tasks.py

```python
# schemas/tasks.py
from pydantic import BaseModel, Field
from typing import Optional

# Допустимые статусы — используются и в схеме и в роутере
VALID_STATUSES = ['new', 'in_progress', 'done', 'cancelled']


class TaskCreate(BaseModel):
    """
    Схема для создания задачи (тело POST-запроса).

    title — название задачи, минимум 1 символ
    priority — 1 (низкий), 2 (средний), 3 (высокий)
    category_id — обязательная ссылка на существующую категорию
    created_at — дата в формате YYYY-MM-DD, клиент передаёт

    Статус ('new') устанавливается автоматически при создании.
    """
    title: str = Field(min_length=1, max_length=200, description='Название задачи')
    priority: int = Field(ge=1, le=3, default=2, description='1=низкий, 2=средний, 3=высокий')
    category_id: int = Field(gt=0, description='id существующей категории')
    created_at: str = Field(description='Дата создания YYYY-MM-DD')


class TaskStatusUpdate(BaseModel):
    """
    Схема для обновления статуса (тело PUT-запроса).
    Отдельная схема — изменить можно только status, ничего больше.
    """
    status: str = Field(description=f'Допустимые: {VALID_STATUSES}')


class TaskResponse(BaseModel):
    """
    Схема ответа для задачи.
    Включает category_name из JOIN — клиент не делает второй запрос.
    """
    id: int
    title: str
    status: str
    priority: int
    created_at: str
    category_id: int
    category_name: str   # из JOIN с таблицей categories
```

### schemas/__init__.py

```python
# schemas/__init__.py
from .categories import CategoryCreate, CategoryResponse
from .tasks import TaskCreate, TaskStatusUpdate, TaskResponse, VALID_STATUSES
```

**Ключевые решения в схемах:**
- `TaskStatusUpdate` — отдельная схема для обновления статуса. Если бы использовали `TaskCreate` с `Optional` полями — клиент мог бы попытаться изменить `title` или `category_id`. Отдельная схема явно ограничивает что можно менять.
- `VALID_STATUSES` — список констант доступен из `schemas`. Роутер импортирует его оттуда и не дублирует.
- `category_name: str` в `TaskResponse` — поле которого нет в таблице `tasks`, оно приходит из JOIN. FastAPI/Pydantic принимают его из словаря — главное чтобы ключ совпадал с именем поля.

---

## Шаг 6. Роутеры — routers/

### routers/categories.py

```python
# routers/categories.py
from fastapi import APIRouter, Depends
from typing import List

from database import get_category_repo
from repositories import CategoryRepository
from schemas import CategoryCreate, CategoryResponse
from exceptions import NotFoundError, AlreadyExistsError

router = APIRouter()


@router.get(
    '/',
    response_model=List[CategoryResponse],
    s='Список всех категорий'
)
def get_categories(repo: CategoryRepository = Depends(get_category_repo)):
    """
    Возвращает все категории отсортированные по имени.
    Пустой список если категорий нет — это не ошибка.
    """
    return [dict(c) for c in repo.get_all()]


@router.post(
    '/',
    response_model=CategoryResponse,
    status_code=201,
    summary='Создать категорию'
)
def create_category(
    category: CategoryCreate,
    repo: CategoryRepository = Depends(get_category_repo)
):
    """
    Создаёт новую категорию.
    400 если категория с таким именем уже существует.
    """
    category_id = repo.create(category.name)
    if category_id is None:
        raise AlreadyExistsError('name', category.name)
    return dict(repo.get_by_id(category_id))


@router.delete(
    '/{category_id}',
    status_code=204,
    summary='Удалить категорию'
)
def delete_category(
    category_id: int,
    repo: CategoryRepository = Depends(get_category_repo)
):
    """
    Удаляет категорию по id.
    404 если категория не найдена.
    204 No Content при успехе — тела ответа нет.
    """
    if not repo.delete(category_id):
        raise NotFoundError('Категория', category_id)
```

### routers/tasks.py

```python
# routers/tasks.py
from fastapi import APIRouter, Depends
from typing import List, Optional

from database import get_task_repo
from repositories import TaskRepository
from schemas import TaskCreate, TaskStatusUpdate, TaskResponse, VALID_STATUSES
from exceptions import NotFoundError, InvalidStatusError

router = APIRouter()


@router.get(
    '/',
    response_model=List[TaskResponse],
    summary='Список задач с фильтрацией'
)
def get_tasks(
    status: Optional[str] = None,
    category_id: Optional[int] = None,
    repo: TaskRepository = Depends(get_task_repo)
):
    """
    Возвращает задачи с опциональными фильтрами.
    Параметры передаются как query: /tasks?status=done&category_id=2

    Если status передан — проверяем что он допустимый.
    Фильтрация происходит в репозитории через параметризованный SQL.
    """
    if status is not None and status not in VALID_STATUSES:
        raise InvalidStatusError(status, VALID_STATUSES)

    return [dict(t) for t in repo.get_all(status=status, category_id=category_id)]


@router.get(
    '/{task_id}',
    response_model=TaskResponse,
    summary='Одна задача по id'
)
def get_task(
    task_id: int,
    repo: TaskRepository = Depends(get_task_repo)
):
    """
    Возвращает задачу с id.
    404 если не найдена.
    """
    task = repo.get_by_id(task_id)
    if task is None:
        raise NotFoundError('Задача', task_id)
    return dict(task)


@router.post(
    '/',
    response_model=TaskResponse,
    status_code=201,
    summary='Создать задачу'
)
def create_task(
    task: TaskCreate,
    repo: TaskRepository = Depends(get_task_repo)
):
    """
    Создаёт задачу со статусом 'new'.
    category_id должен существовать — иначе FOREIGN KEY нарушен.

    После создания читаем задачу через get_by_id чтобы вернуть
    полный объект включая category_name из JOIN.
    """
    task_id = repo.create(
        title=task.title,
        priority=task.priority,
        category_id=task.category_id,
        created_at=task.created_at
    )
    return dict(repo.get_by_id(task_id))


@router.put(
    '/{task_id}/status',
    response_model=TaskResponse,
    summary='Обновить статус задачи'
)
def update_task_status(
    task_id: int,
    body: TaskStatusUpdate,
    repo: TaskRepository = Depends(get_task_repo)
):
    """
    Обновляет только статус задачи.
    Проверяем допустимость статуса до обращения к БД.
    404 если задача не найдена.
    """
    if body.status not in VALID_STATUSES:
        raise InvalidStatusError(body.status, VALID_STATUSES)

    updated = repo.update_status(task_id, body.status)
    if not updated:
        raise NotFoundError('Задача', task_id)

    return dict(repo.get_by_id(task_id))


@router.delete(
    '/{task_id}',
    status_code=204,
    summary='Удалить задачу'
)
def delete_task(
    task_id: int,
    repo: TaskRepository = Depends(get_task_repo)
):
    """
    Удаляет задачу по id.
    404 если не найдена. 204 при успехе.
    """
    if not repo.delete(task_id):
        raise NotFoundError('Задача', task_id)
```

### routers/__init__.py

```python
# routers/__init__.py
# Пустой — роутеры импортируются в main.py напрямую
```

---

## Шаг 7. Точка входа — main.py

```python
# main.py
import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse

from database import init_db
from exceptions import AppException
from routers import categories, tasks

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

# Создаём приложение с метаданными для /docs
app = FastAPI(
    title='To-Do API',
    version='1.0',
    description='REST API для управления задачами и категориями'
)


# -----------------------------------------------------------------
# Событие старта — инициализация БД
# -----------------------------------------------------------------

@app.on_event('startup')
def startup():
    """
    Выполняется один раз при запуске uvicorn.
    Создаёт таблицы если они не существуют.
    Если таблицы уже есть — ничего не происходит (IF NOT EXISTS).
    """
    init_db()
    logger.info('База данных инициализирована')


# -----------------------------------------------------------------
# Обработчики исключений — единый формат ошибок
# -----------------------------------------------------------------

@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    """Наши бизнес-исключения: NotFoundError, AlreadyExistsError, ..."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            'error': True,
            'code': exc.status_code,
            'message': exc.message
        }
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Стандартные FastAPI-исключения (например от валидации пути)."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            'error': True,
            'code': exc.status_code,
            'message': exc.detail
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Всё остальное — логируем, клиенту общее сообщение."""
    logger.error(f'Необработанное исключение: {exc}', exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            'error': True,
            'code': 500,
            'message': 'Внутренняя ошибка сервера'
        }
    )


# -----------------------------------------------------------------
# Роутеры
# -----------------------------------------------------------------

app.include_router(
    categories.router,
    prefix='/categories',
    tags=['categories']
)

app.include_router(
    tasks.router,
    prefix='/tasks',
    tags=['tasks']
)


# -----------------------------------------------------------------
# Системный эндпоинт
# -----------------------------------------------------------------

@app.get('/health', tags=['system'])
def health_check():
    return {'status': 'ok', 'service': 'todo-api'}
```

---

## Шаг 8. Запуск и проверка

### Запуск

```bash
uvicorn main:app --reload
```

При запуске в консоли:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:__main__: База данных инициализирована
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### Проверка через /docs

Откройте `http://127.0.0.1:8000/docs`. Вы увидите все эндпоинты разбитые по группам: **categories**, **tasks**, **system**.

### Сценарии проверки

**1. Создать категории:**
```json
POST /categories
{"name": "Работа"}

POST /categories
{"name": "Личное"}
```

**2. Создать задачи:**
```json
POST /tasks
{
    "title": "Написать отчёт",
    "priority": 3,
    "category_id": 1,
    "created_at": "2024-06-25"
}

POST /tasks
{
    "title": "Купить продукты",
    "priority": 1,
    "category_id": 2,
    "created_at": "2024-06-25"
}
```

**3. Получить все задачи с фильтром:**
```
GET /tasks?status=new
GET /tasks?category_id=1
GET /tasks?status=new&category_id=1
```

**4. Обновить статус:**
```json
PUT /tasks/1/status
{"status": "in_progress"}
```

**5. Попробовать невалидные данные:**
```json
POST /tasks
{"title": "", "priority": 5, "category_id": 1, "created_at": "2024-06-25"}
// → 422: title min_length, priority le=3
```

**6. Попробовать несуществующий id:**
```
GET /tasks/9999
// → {"error": true, "code": 404, "message": "Задача с id=9999 не найдена"}
```

---

## Шаг 9. Полный список файлов — готовый проект

### Финальное дерево файлов

```
todo_api/
├── main.py
├── database.py
├── exceptions.py
├── repositories/
│   ├── __init__.py
│   ├── categories.py
│   └── tasks.py
├── schemas/
│   ├── __init__.py
│   ├── categories.py
│   └── tasks.py
└── routers/
    ├── __init__.py
    ├── categories.py
    └── tasks.py
```

### Итоги урока

Мы построили полноценный REST API с нуля за 9 шагов. Каждый шаг решал конкретную задачу:

| Шаг | Файл | Что сделали |
|---|---|---|
| 1 | — | Спроектировали схему БД и список эндпоинтов |
| 2 | database.py | Инициализация БД, соединение через yield, фабрики зависимостей |
| 3 | exceptions.py | Иерархия бизнес-исключений |
| 4 | repositories/ | SQL-запросы с динамической фильтрацией |
| 5 | schemas/ | Валидация входа и форматирование выхода |
| 6 | routers/ | HTTP-эндпоинты, коды статусов, обработка ошибок |
| 7 | main.py | Сборка приложения, startup, глобальные обработчики |
| 8 | — | Запуск и проверка сценариев |
| 9 | — | Готовый проект |

---

[Предыдущий урок](lesson19.md) | [Следующий урок](lesson21.md)