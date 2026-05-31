# Урок 19. Обработка ошибок и структура проекта

## Ошибки — часть API

В предыдущих уроках мы уже использовали `raise HTTPException(status_code=404)`. Пришло время разобраться как обработка ошибок устроена в FastAPI системно — не только какой код ставить, но и как делать это единообразно во всём проекте.

Хорошо спроектированный API сообщает об ошибках предсказуемо: клиент всегда знает в каком формате придёт ошибка и что означает каждый код. Непоследовательная обработка ошибок — когда один эндпоинт возвращает `{'error': 'not found'}`, другой `{'message': 'Не найден'}`, третий пустой `200` — делает API неудобным и ненадёжным.

---

## HTTPException — стандартный способ вернуть ошибку

`HTTPException` — это исключение которое FastAPI перехватывает и превращает в HTTP-ответ с нужным кодом статуса:

```python
from fastapi import HTTPException

raise HTTPException(status_code=404, detail='Товар не найден')
```

FastAPI вернёт:

```json
HTTP/1.1 404 Not Found
Content-Type: application/json

{
    "detail": "Товар не найден"
}
```

Поле `detail` — это то что видит клиент. Оно может быть строкой, словарём или списком — всё зависит от того насколько подробную информацию нужно вернуть.

### Основные коды и когда их использовать

```python
# 404 — ресурс не найден
product = repo.get_by_id(product_id)
if product is None:
    raise HTTPException(status_code=404, detail='Товар не найден')

# 400 — неверный запрос (ошибка логики, не валидации)
user_id = repo.create(user.name, user.email, user.city, user.created_at)
if user_id is None:
    raise HTTPException(status_code=400, detail='Пользователь с таким email уже существует')

# 422 — ошибка валидации (FastAPI выбрасывает автоматически через Pydantic)
# Вы её не пишете вручную — она появляется сама когда данные не прошли схему

# 403 — нет прав на действие
# 401 — не авторизован
# 500 — внутренняя ошибка сервера (не пишется вручную — возникает при необработанных исключениях)
```

### 400 vs 422 — в чём разница

Оба кода означают "клиент прислал что-то неверное", но по-разному:

- `422 Unprocessable Entity` — Pydantic не смог разобрать данные: неверный тип, отсутствует обязательное поле, нарушено ограничение `Field(gt=0)`. FastAPI выбрасывает автоматически.
- `400 Bad Request` — данные технически корректны и прошли схему, но нарушают бизнес-логику: такой email уже занят, нельзя заказать товар которого нет на складе.

```python
# 422 — FastAPI сам, без вашего кода
# Клиент прислал {"name": "", "price": -100}
# → Pydantic: min_length нарушен, gt=0 нарушен

# 400 — вы пишете сами
# Клиент прислал {"email": "alice@mail.ru"} — технически верно
# Но alice уже есть в базе → бизнес-логика не выполнима
raise HTTPException(status_code=400, detail='Email уже занят')
```

---

## Единообразный формат ошибок

FastAPI по умолчанию возвращает ошибки в формате `{"detail": "..."}`. Это хорошая основа, но в реальных проектах часто нужен более структурированный формат. Для этого используют **кастомные обработчики исключений**.

### exception_handler — глобальный перехват

`@app.exception_handler(ТипИсключения)` — декоратор который регистрирует функцию как глобальный обработчик указанного типа исключений. Когда где-либо в приложении выбрасывается это исключение, FastAPI вызывает обработчик вместо стандартного поведения. Это позволяет задать единый формат ошибок для всего API — клиент получает предсказуемую структуру ответа независимо от эндпоинта.

```python
# main.py
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse

app = FastAPI()


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            'error': True,
            'code': exc.status_code,
            'message': exc.detail,
        }
    )
```

Теперь все `HTTPException` во всём приложении вернут единый формат:

```json
{
    "error": true,
    "code": 404,
    "message": "Товар не найден"
}
```

Клиент всегда знает что ожидать — структура ошибки предсказуема независимо от эндпоинта.

### Почему обработчик объявлен через async def

В FastAPI обработчики исключений могут быть как синхронными (`def`), так и асинхронными (`async def`). В примерах часто используют `async def`, потому что FastAPI построен на ASGI и изначально ориентирован на асинхронную обработку запросов.

В данном примере внутри обработчика нет `await`, поэтому технически его можно было бы написать и как обычную функцию:

```python
@app.exception_handler(HTTPException)
def http_exception_handler(request: Request, exc: HTTPException):
    ...
```

**Оба варианта корректны**.

Асинхронный вариант обычно используют как универсальный шаблон — если позже внутри обработчика появятся асинхронные операции (например запись логов, работа с Redis, отправка сообщений или обращение к БД через async-драйвер), код уже будет готов к использованию `await`.

### Перехват неожиданных исключений

Необработанные Python-исключения FastAPI превращает в `500 Internal Server Error`. Можно добавить обработчик чтобы логировать их и возвращать понятный ответ:

```python
import logging

logger = logging.getLogger(__name__)


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f'Необработанное исключение: {exc}', exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            'error': True,
            'code': 500,
            'message': 'Внутренняя ошибка сервера',
        }
    )
```

> В продакшне `500`-ответы не должны содержать детали ошибки — это утечка информации. Детали пишутся в лог, клиент получает только общее сообщение.

---

## Собственные исключения

Когда проект растёт — удобно создавать собственные классы исключений. Это делает код выразительнее и позволяет централизованно управлять обработкой:

```python
# exceptions.py


class AppException(Exception):
    """Базовое исключение приложения."""
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(message)


class NotFoundError(AppException):
    def __init__(self, resource: str, resource_id: int):
        super().__init__(
            status_code=404,
            message=f'{resource} с id={resource_id} не найден'
        )


class AlreadyExistsError(AppException):
    def __init__(self, field: str, value: str):
        super().__init__(
            status_code=400,
            message=f'Запись с {field}={value!r} уже существует'
        )
```

```python
# main.py — регистрируем обработчик для AppException
from exceptions import AppException

@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={'error': True, 'code': exc.status_code, 'message': exc.message}
    )
```

```python
# В роутере — выбрасываем конкретные исключения
from exceptions import NotFoundError, AlreadyExistsError

@router.get('/{product_id}', response_model=ProductResponse)
def get_product(product_id: int, repo=Depends(get_product_repo)):
    product = repo.get_by_id(product_id)
    if product is None:
        raise NotFoundError('Товар', product_id)
    return dict(product)

@router.post('/', response_model=ProductResponse, status_code=201)
def create_product(product: ProductCreate, repo=Depends(get_product_repo)):
    product_id = repo.create(product.name, product.price, product.stock, product.category_id)
    if product_id is None:
        raise AlreadyExistsError('category_id', str(product.category_id))
    return dict(repo.get_by_id(product_id))
```

Читается как текст: "если не найден — `NotFoundError`". Детали формирования HTTP-ответа скрыты в обработчике.

---

## Структура проекта

Пока в курсе мы работали с простой структурой. По мере роста приложения — больше сущностей, больше эндпоинтов, больше схем — нужна более чёткая организация.

### Почему структура важна с самого начала

Плохо организованный код не становится лучше со временем — он становится хуже. Когда все схемы в одном файле `schemas.py`, все репозитории в одном `repositories.py` — при росте проекта эти файлы разрастаются до нескольких сотен строк. Найти нужное становится сложно, случайные зависимости между несвязанными частями накапливаются.

Хорошая структура — та которая даёт ответ на вопрос "где лежит X?" без раздумий.

### Структура для учебного проекта

Для нашего курса подойдёт следующая организация:

```
shop_api/
│
├── main.py                  ← точка входа, регистрация роутеров и обработчиков
├── database.py              ← get_connection(), зависимости для репозиториев
├── exceptions.py            ← кастомные исключения
│
├── repositories/            ← по одному файлу на сущность
│   ├── __init__.py          ← реэкспорт для удобного импорта
│   ├── users.py             ← UserRepository
│   ├── products.py          ← ProductRepository
│   └── orders.py            ← OrderRepository
│
├── schemas/                 ← по одному файлу на сущность
│   ├── __init__.py
│   ├── users.py             ← UserCreate, UserResponse
│   ├── products.py          ← ProductCreate, ProductResponse
│   └── orders.py            ← OrderCreate, OrderResponse
│
└── routers/                 ← по одному файлу на сущность
    ├── __init__.py
    ├── users.py             ← эндпоинты /users
    ├── products.py          ← эндпоинты /products
    └── orders.py            ← эндпоинты /orders
```

Принцип организации — **по сущности, а не по типу файла**. Всё что касается пользователей: `repositories/users.py`, `schemas/users.py`, `routers/users.py`. Это называется "вертикальная нарезка" (vertical slice) — легко найти всё связанное с одной сущностью.

### Файлы `__init__.py` для удобного импорта

```python
# repositories/__init__.py
from .users import UserRepository
from .products import ProductRepository
from .orders import OrderRepository

# schemas/__init__.py
from .users import UserCreate, UserResponse
from .products import ProductCreate, ProductResponse
from .orders import OrderCreate, OrderResponse
```

С такими `__init__.py` импорты в роутерах становятся короче:

```python
# Без __init__.py
from repositories.users import UserRepository
from schemas.users import UserCreate, UserResponse

# С __init__.py
from repositories import UserRepository
from schemas import UserCreate, UserResponse
```

### Полный main.py финального проекта

```python
# main.py
import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse

from routers import users, products, orders
from exceptions import AppException

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title='Shop API',
    version='1.0',
    description='REST API для интернет-магазина'
)

# --- Обработчики исключений ---

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
    logging.error(f'Необработанное исключение: {exc}', exc_info=True)
    return JSONResponse(
        status_code=500,
        content={'error': True, 'code': 500, 'message': 'Внутренняя ошибка сервера'}
    )


# --- Роутеры ---

app.include_router(users.router,    prefix='/users',    tags=['users'])
app.include_router(products.router, prefix='/products', tags=['products'])
app.include_router(orders.router,   prefix='/orders',   tags=['orders'])


# --- Проверочный эндпоинт ---

@app.get('/health', tags=['system'])
def health_check():
    return {'status': 'ok'}
```

`/health` — стандартный эндпоинт для проверки что сервис живёт. Используется системами мониторинга и оркестрации.

---

## Итоговая архитектура: как слои связаны

```
HTTP-запрос
    │
    ▼
main.py         — регистрирует роутеры и обработчики исключений
    │
    ▼
routers/        — принимает запрос, вызывает зависимости, возвращает ответ
    │               не содержит SQL, не знает про детали хранения
    │
    ├── Depends → database.py — создаёт соединение, передаёт в репозиторий
    │
    ├── schemas/ — валидирует входящие данные (request)
    │              фильтрует и форматирует ответ (response_model)
    │
    └── repositories/ — выполняет SQL-запросы
                        не знает про HTTP, не знает про схемы

exceptions.py   — общие исключения, один формат ошибок во всём приложении
```

Каждый слой знает только про соседей. Роутер не лезет в SQL. Репозиторий не знает про HTTP. Изменения в одном слое минимально затрагивают другие.

---

## Вопросы для закрепления

1. В чём разница между `400` и `422`? Кто их выбрасывает?
2. Что такое `exception_handler` и зачем он нужен?
3. Почему детали `500`-ошибки не должны попадать клиенту?
4. Почему организация файлов "по сущности" лучше чем "по типу файла"?
5. Что даёт `__init__.py` с реэкспортом в папках `repositories/` и `schemas/`?
6. Чем кастомное исключение `NotFoundError` лучше прямого `raise HTTPException(status_code=404)`?
7. Что такое эндпоинт `/health` и зачем он нужен?
8. Роутер вызывает репозиторий, репозиторий работает с БД. Почему роутер не должен работать с БД напрямую?
9. Можно ли зарегистрировать несколько `exception_handler` для разных типов исключений?
10. Как структура проекта влияет на работу в команде?

---

## Задачи

### **Задача 1.** 

Добавьте в `main.py` глобальный обработчик `HTTPException` который возвращает ошибки в формате `{'error': True, 'code': N, 'message': '...'}`. Проверьте что `GET /products/9999` возвращает именно такой формат.

**Пример использования**:

```python
@app.get('/products/{product_id}')
def get_product(product_id: int):
    raise HTTPException(status_code=404, detail='Товар не найден')
```

---

### **Задача 2.** 

Создайте файл `exceptions.py` с классами `NotFoundError` и `AlreadyExistsError`. Зарегистрируйте обработчик `AppException` в `main.py`. Используйте `NotFoundError` в эндпоинте `GET /users/{user_id}`.

**Пример использования**:

```python
@app.get('/users/{user_id}')
def get_user(user_id: int):
    from exceptions import NotFoundError
    raise NotFoundError('Пользователь', user_id)
```

---

### **Задача 3.** 

Реорганизуйте проект по структуре из урока: создайте папки `repositories/`, `schemas/`, `routers/` с файлами по сущностям и `__init__.py` с реэкспортом. Перенесите в них код из предыдущих уроков.

```
shop_api/
├── main.py
├── database.py
├── exceptions.py
├── repositories/
│   ├── __init__.py     ← from .users import UserRepository; from .products import ProductRepository
│   ├── users.py        ← class UserRepository
│   └── products.py     ← class ProductRepository
├── schemas/
│   ├── __init__.py     ← from .users import UserCreate, UserResponse; ...
│   ├── users.py        ← UserCreate, UserResponse
│   └── products.py     ← ProductCreate, ProductResponse
└── routers/
    ├── __init__.py     ← пустой или с реэкспортом
    ├── users.py        ← router для /users
    └── products.py     ← router для /products
```

---

### **Задача 4.** 

Добавьте обработчик для общего `Exception` который логирует ошибку и возвращает `500` с общим сообщением. Проверьте его работу создав эндпоинт который намеренно вызывает `ZeroDivisionError`.

---

### **Задача 5.** 

Добавьте эндпоинт `GET /health` который возвращает статус приложения и имя базы данных. Проверьте что он возвращает `200` и корректный JSON.

---

### **Задача 6.** 

Используя структуру из урока (разбивка по сущностям), реализуйте полный API для пользователей и товаров: все файлы разложены по папкам, `__init__.py` с реэкспортом, единый формат ошибок, `/health` эндпоинт. Запустите и проверьте все эндпоинты в `/docs`.

---

[Предыдущий урок](lesson18.md) | [Следующий урок](lesson20.md)