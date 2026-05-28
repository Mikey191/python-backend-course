# Урок 18. Подключение SQLite к FastAPI

## Проблема с текущим подходом

В прошлых уроках мы подключали базу данных прямо внутри каждого эндпоинта:

```python
@router.get('/{product_id}', response_model=ProductResponse)
def get_product(product_id: int):
    with get_connection() as connection:   # соединение создаётся здесь
        repo = ProductRepository(connection)
        product = repo.get_by_id(product_id)
        ...
```

Это работает, но у подхода есть недостаток: каждый эндпоинт сам управляет соединением. Если завтра нужно изменить способ создания соединения — придётся менять каждую функцию. А если нужно передавать разные соединения для тестов и для продакшна — это вообще неудобно.

FastAPI предлагает элегантное решение — **Dependency Injection**.

---

## Что такое Dependency Injection

**Dependency Injection** (DI, внедрение зависимостей) — паттерн при котором объект получает свои зависимости снаружи, а не создаёт их самостоятельно.

Звучит абстрактно — посмотрим на конкретный пример из того что уже знакомо.

В Модуле 2 мы передавали соединение в репозиторий снаружи:

```python
# Репозиторий не создаёт соединение сам — получает его снаружи
class UserRepository:
    def __init__(self, connection):   # зависимость передаётся в конструктор
        self.connection = connection
```

Это уже DI — только ручной. FastAPI автоматизирует этот же принцип для эндпоинтов: вместо того чтобы создавать соединение внутри функции, FastAPI создаёт его автоматически и **передаёт** в функцию.

---

## Зависимость в FastAPI — функция `Depends`

В FastAPI зависимость — это обычная функция. FastAPI вызывает её перед вызовом эндпоинта и передаёт результат как параметр.

Напишем зависимость для соединения с базой данных:

```python
# database.py
import sqlite3
from typing import Generator


def get_connection(db_path='shop.db') -> Generator:
    """
    Зависимость FastAPI: создаёт соединение, отдаёт его эндпоинту,
    закрывает после завершения запроса.
    """
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    try:
        yield connection      # передаём соединение в эндпоинт
    finally:
        connection.close()    # выполнится в любом случае — и при успехе, и при ошибке
```

`yield` превращает функцию в генератор. FastAPI понимает этот паттерн:
1. Выполняет код до `yield` — создаёт соединение
2. Передаёт значение из `yield` в эндпоинт
3. После завершения эндпоинта выполняет код после `yield` — закрывает соединение

Это гарантирует что соединение закроется всегда — даже если эндпоинт выбросил исключение. `finally` выполнится в любом случае. Без `finally` при исключении в эндпоинте соединение не закроется — оно зависнет открытым, потребляя ресурсы. При большой нагрузке это приведёт к исчерпанию соединений.

---

## Использование зависимости в эндпоинте

Зависимость подключается через `Depends` из FastAPI:

```python
from fastapi import APIRouter, Depends, HTTPException
from typing import List
import sqlite3

from database import get_connection
from repositories import ProductRepository
from schemas import ProductCreate, ProductResponse

router = APIRouter()


@router.get('/', response_model=List[ProductResponse])
def get_products(connection: sqlite3.Connection = Depends(get_connection)):
    repo = ProductRepository(connection)
    return [dict(p) for p in repo.get_all()]


@router.get('/{product_id}', response_model=ProductResponse)
def get_product(
    product_id: int,
    connection: sqlite3.Connection = Depends(get_connection)
):
    repo = ProductRepository(connection)
    product = repo.get_by_id(product_id)
    if product is None:
        raise HTTPException(status_code=404, detail='Товар не найден')
    return dict(product)
```

`connection: sqlite3.Connection = Depends(get_connection)` — это объявление зависимости:
- `sqlite3.Connection` — аннотация типа (для читаемости и IDE)
- `Depends(get_connection)` — говорит FastAPI "вызови `get_connection()` и передай результат сюда"

Сравните с предыдущим подходом:

```python
# Было: соединение управляется вручную внутри функции
@router.get('/{product_id}')
def get_product(product_id: int):
    with get_connection() as connection:
        repo = ProductRepository(connection)
        ...

# Стало: соединение приходит снаружи через DI
@router.get('/{product_id}', response_model=ProductResponse)
def get_product(product_id: int, connection = Depends(get_connection)):
    repo = ProductRepository(connection)
    ...
```

`Depends(get_connection)` — передаём функцию как зависимость (без скобок). FastAPI сам вызовет её в нужный момент перед выполнением эндпоинта. `get_connection()` с скобками — вызов функции немедленно при объявлении параметра, что неверно: соединение создастся один раз при запуске приложения, а не на каждый запрос.

Функция стала чище — она не знает как создаётся соединение. Это знание инкапсулировано в `get_connection`.

При тестировании можно подменить зависимость. Вместо реального `get_connection` который открывает `shop.db` — передать `get_test_connection` которая открывает `':memory:'` (базу в памяти). Эндпоинт не меняется вообще. Без DI эндпоинт жёстко привязан к конкретному файлу базы данных и подменить его сложно.

---

## Зависимость для репозитория

Можно пойти дальше и сделать зависимость не только для соединения, но и для самого репозитория:

```python
# database.py
import sqlite3
from typing import Generator
from repositories import ProductRepository, UserRepository


def get_connection(db_path='shop.db') -> Generator:
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
    finally:
        connection.close()


def get_product_repo(
    connection: sqlite3.Connection = Depends(get_connection)
) -> ProductRepository:
    return ProductRepository(connection)


def get_user_repo(
    connection: sqlite3.Connection = Depends(get_connection)
) -> UserRepository:
    return UserRepository(connection)
```

```python
# routers/products.py
@router.get('/', response_model=List[ProductResponse])
def get_products(repo: ProductRepository = Depends(get_product_repo)):
    return [dict(p) for p in repo.get_all()]


@router.get('/{product_id}', response_model=ProductResponse)
def get_product(product_id: int, repo: ProductRepository = Depends(get_product_repo)):
    product = repo.get_by_id(product_id)
    if product is None:
        raise HTTPException(status_code=404, detail='Товар не найден')
    return dict(product)
```

Теперь эндпоинт вообще не знает про SQLite — он работает только с репозиторием. Зависимости выстроены в цепочку: FastAPI сам разберётся в нужном порядке.

```
FastAPI получает запрос
    → вызывает get_connection() → открывает соединение
    → передаёт соединение в get_product_repo() → создаёт репозиторий
    → передаёт репозиторий в get_product() → выполняет бизнес-логику
    → возвращает ответ
    → вызывает finally в get_connection() → закрывает соединение
```

Если завтра нужно сменить SQLite на PostgreSQL в коде эндпоинтов изменится только `database.py`. Функция `get_connection` будет создавать соединение с PostgreSQL вместо SQLite. Репозитории, схемы и эндпоинты не изменятся вообще. Именно это и есть главное преимущество DI и слоистой архитектуры — изменения изолированы в одном месте.

---

## Полный цикл запроса

Теперь у нас есть все части. Посмотрим на полный путь HTTP-запроса через приложение:

```
Клиент: GET /products/5
          │
          ▼
      uvicorn (сервер)
          │ принимает HTTP-запрос
          ▼
      FastAPI (роутер)
          │ находит эндпоинт get_product(product_id=5)
          │ вызывает зависимость get_connection()
          │ создаёт соединение с shop.db
          │ создаёт ProductRepository(connection)
          ▼
      def get_product(product_id=5, repo=...)
          │ вызывает repo.get_by_id(5)
          ▼
      ProductRepository.get_by_id(5)
          │ выполняет SQL: SELECT * FROM products WHERE id = 5
          ▼
      SQLite (shop.db)
          │ возвращает строку
          ▼
      ProductRepository → возвращает sqlite3.Row
          │
          ▼
      get_product → dict(product) → FastAPI валидирует через ProductResponse
          │
          ▼
      FastAPI → сериализует в JSON
          │
          ▼
      uvicorn → отправляет HTTP-ответ 200 OK
          │
          ▼
Клиент: {"id": 5, "name": "Планшет Apple iPad", "price": 55000.0, ...}
```

Каждый слой делает своё дело. Репозиторий не знает про FastAPI. Эндпоинт не знает про SQL. Схема не знает про базу данных.

---

## Полный проект: структура и код

```
shop_api/
├── main.py
├── database.py
├── repositories.py      ← без изменений из Модуля 2
├── schemas.py
└── routers/
    ├── __init__.py
    ├── users.py
    ├── products.py
    └── orders.py
```

```python
# database.py
import sqlite3
from typing import Generator
from fastapi import Depends
from repositories import ProductRepository, UserRepository, OrderRepository


def get_connection() -> Generator:
    connection = sqlite3.connect('shop.db')
    connection.row_factory = sqlite3.Row
    try:
        yield connection
    finally:
        connection.close()


def get_product_repo(
    connection: sqlite3.Connection = Depends(get_connection)
) -> ProductRepository:
    return ProductRepository(connection)


def get_user_repo(
    connection: sqlite3.Connection = Depends(get_connection)
) -> UserRepository:
    return UserRepository(connection)


def get_order_repo(
    connection: sqlite3.Connection = Depends(get_connection)
) -> OrderRepository:
    return OrderRepository(connection)
```

```python
# schemas.py
from pydantic import BaseModel, Field
from typing import Optional, List


class ProductBase(BaseModel):
    name: str = Field(min_length=1)
    price: float = Field(gt=0)
    stock: int = Field(ge=0, default=0)
    category_id: int = Field(gt=0)

class ProductCreate(ProductBase):
    pass

class ProductResponse(ProductBase):
    id: int


class UserBase(BaseModel):
    name: str = Field(min_length=1)
    email: str
    city: str

class UserCreate(UserBase):
    created_at: str

class UserResponse(UserBase):
    id: int
    created_at: str


class OrderItemResponse(BaseModel):
    product_id: int
    quantity: int
    price_at_time: float

class OrderResponse(BaseModel):
    id: int
    user_id: int
    status: str
    created_at: str
```

```python
# routers/products.py
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from database import get_product_repo
from repositories import ProductRepository
from schemas import ProductCreate, ProductResponse

router = APIRouter()


@router.get('/', response_model=List[ProductResponse])
def get_products(repo: ProductRepository = Depends(get_product_repo)):
    return [dict(p) for p in repo.get_all()]


@router.get('/{product_id}', response_model=ProductResponse)
def get_product(
    product_id: int,
    repo: ProductRepository = Depends(get_product_repo)
):
    product = repo.get_by_id(product_id)
    if product is None:
        raise HTTPException(status_code=404, detail='Товар не найден')
    return dict(product)


@router.post('/', response_model=ProductResponse, status_code=201)
def create_product(
    product: ProductCreate,
    repo: ProductRepository = Depends(get_product_repo)
):
    product_id = repo.create(
        name=product.name,
        price=product.price,
        stock=product.stock,
        category_id=product.category_id
    )
    return dict(repo.get_by_id(product_id))


@router.delete('/{product_id}', status_code=204)
def delete_product(
    product_id: int,
    repo: ProductRepository = Depends(get_product_repo)
):
    deleted = repo.delete(product_id)
    if not deleted:
        raise HTTPException(status_code=404, detail='Товар не найден')
```

```python
# routers/users.py
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from database import get_user_repo
from repositories import UserRepository
from schemas import UserCreate, UserResponse

router = APIRouter()


@router.get('/', response_model=List[UserResponse])
def get_users(repo: UserRepository = Depends(get_user_repo)):
    return [dict(u) for u in repo.get_all()]


@router.get('/{user_id}', response_model=UserResponse)
def get_user(user_id: int, repo: UserRepository = Depends(get_user_repo)):
    user = repo.get_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail='Пользователь не найден')
    return dict(user)


@router.post('/', response_model=UserResponse, status_code=201)
def create_user(user: UserCreate, repo: UserRepository = Depends(get_user_repo)):
    user_id = repo.create(user.name, user.email, user.city, user.created_at)
    if user_id is None:
        raise HTTPException(status_code=400, detail='Email уже занят')
    return dict(repo.get_by_id(user_id))


@router.delete('/{user_id}', status_code=204)
def delete_user(user_id: int, repo: UserRepository = Depends(get_user_repo)):
    if not repo.delete(user_id):
        raise HTTPException(status_code=404, detail='Пользователь не найден')
```

```python
# main.py
from fastapi import FastAPI
from routers import products, users

app = FastAPI(title='Shop API', version='1.0')

app.include_router(products.router, prefix='/products', tags=['products'])
app.include_router(users.router,    prefix='/users',    tags=['users'])
```

---

## Вопросы

1. Что такое Dependency Injection и где вы уже встречали этот принцип в курсе?
2. Почему в `get_connection()` используется `yield` вместо `return`?
3. Зачем `finally` в `get_connection()`? Что произойдёт без него при исключении в эндпоинте?
4. Чем `Depends(get_connection)` отличается от `get_connection()` (с вызовом скобками)?
5. Что происходит с соединением если в эндпоинте выбрасывается `HTTPException`?
6. Почему для `DELETE`-эндпоинта используется `status_code=204` а не `200`?
7. Как FastAPI понимает порядок выполнения цепочки зависимостей `get_product_repo → get_connection`?
8. Какое преимущество даёт DI при написании тестов?
9. Что изменится в коде эндпоинтов если завтра нужно сменить SQLite на PostgreSQL?

---

## Задачи

### **Задача 1.** 

Напишите функцию `get_connection()` с `yield` и `finally`. Убедитесь что она правильно закрывает соединение: добавьте `print('соединение закрыто')` в `finally` и проверьте что он выводится после каждого запроса. Подключите к любому эндпоинту и сделайте запрос.

---

### **Задача 2.** 

Создайте эндпоинт `GET /categories` который использует `Depends(get_connection)` и возвращает все категории из `shop.db`.

---

### **Задача 3.** 

Создайте функцию-зависимость `get_user_repo` которая принимает `connection` через `Depends(get_connection)` и возвращает `UserRepository`. Используйте её в эндпоинте `GET /users`.

---

### **Задача 4.** 

Реализуйте полный CRUD для товаров (`GET /products`, `GET /products/{id}`, `POST /products`, `DELETE /products/{id}`) используя `Depends` и `ProductRepository`. Все эндпоинты должны использовать одну зависимость `get_product_repo`.

---

### **Задача 5.** 

Проверьте что соединение закрывается при ошибке: создайте эндпоинт который поднимает `HTTPException` и добавьте `print` в `finally` зависимости. Убедитесь что соединение закрывается и в этом случае. При запросе `GET /test-error` в консоли появится `✓ Соединение закрыто` — несмотря на исключение.

**Пример использования**:

```python
app = FastAPI()


@app.get('/test-error')
def test_error(connection: sqlite3.Connection = Depends(get_connection)):
    raise HTTPException(status_code=400, detail='Тестовая ошибка')
    # finally в get_connection выполнится даже здесь
```

---

### **Задача 6.** 

Создайте два роутера `users.py` и `products.py` с полными CRUD-операциями. Подключите оба в `main.py`. Откройте `/docs` и убедитесь что все эндпоинты работают через интерактивную документацию.

---

### **Задача 7.** 

Добавьте в `routers/users.py` эндпоинт `GET /users/{user_id}/orders` который возвращает все заказы пользователя. Используйте `Depends(get_connection)` напрямую и выполните JOIN-запрос через cursor.

---

[Предыдущий урок](lesson17.md) | [Следующий урок](lesson19.md)