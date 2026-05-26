# Урок 17. Pydantic-схемы

## Проблема без схем

В прошлом уроке мы написали эндпоинт который создаёт товар:

```python
@router.post('/')
def create_product():
    # Как получить данные от клиента?
    # Как проверить что они правильные?
    # Как ответить в нужном формате?
    pass
```

Три вопроса без ответа. Клиент должен прислать название, цену, остаток — но как это получить? Что если он прислал цену как строку `"abc"`? Что если забыл поле?

Можно проверять вручную:

```python
@router.post('/')
def create_product(data: dict):
    if 'name' not in data:
        return {'error': 'name обязательно'}
    if not isinstance(data['price'], (int, float)):
        return {'error': 'price должна быть числом'}
    if data['price'] <= 0:
        return {'error': 'price должна быть положительной'}
    # ... и так для каждого поля
```

Это много кода, он дублируется в каждом эндпоинте и всё равно не решает задачу сериализации ответа. Именно для этого существует **Pydantic**.

---

## Что такое Pydantic

**Pydantic** — библиотека для валидации данных через аннотации типов Python. FastAPI использует Pydantic встроенно — устанавливать отдельно не нужно (он ставится вместе с FastAPI).

Главная идея: вы описываете структуру данных как класс, Pydantic автоматически проверяет что данные соответствуют этой структуре и преобразует их в нужные типы.

Студенты которые изучали Dataclasses увидят знакомый паттерн — класс с аннотированными полями. Pydantic работает похоже, но добавляет валидацию, сериализацию и интеграцию с FastAPI.

---

## BaseModel — основа схемы

Схема Pydantic — это класс унаследованный от `BaseModel`:

```python
from pydantic import BaseModel

class ProductCreate(BaseModel):
    name: str
    price: float
    stock: int
    category_id: int
```

Это и есть схема. Четыре строки вместо двадцати строк ручных проверок.

Pydantic автоматически:
- Проверяет что все поля присутствуют
- Преобразует типы где это возможно (`"42"` → `42` для `int`)
- Выбрасывает понятную ошибку если данные не соответствуют схеме

### Поля со значениями по умолчанию

```python
from pydantic import BaseModel
from typing import Optional

class ProductCreate(BaseModel):
    name: str                    # обязательное — нет значения по умолчанию
    price: float                 # обязательное
    stock: int = 0               # необязательное — есть значение по умолчанию
    category_id: int             # обязательное
    description: Optional[str] = None  # необязательное, может быть None
```

`Optional[str]` означает "строка или None". Это стандартная аннотация из модуля `typing`.

`description: Optional[str] = None` - необязательное поле которое может быть `None`. Через `Optional[тип]` из модуля `typing` со значением по умолчанию `None`: `description: Optional[str] = None`. 

Без `= None` поле всё равно будет обязательным — просто принимающим `None` как значение.

---

## Схема как параметр эндпоинта — REQUEST

Чтобы FastAPI принял тело запроса и провалидировал его через схему — объявите схему как параметр функции:

```python
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

router = APIRouter()


class ProductCreate(BaseModel):
    name: str
    price: float
    stock: int = 0
    category_id: int


@router.post('/')
def create_product(product: ProductCreate):
    # product — уже провалидированный объект с нужными типами
    print(product.name)        # str
    print(product.price)       # float
    print(product.stock)       # int
    print(product.category_id) # int

    return {'message': f'Товар {product.name!r} создан'}
```

FastAPI автоматически:
1. Читает тело запроса (JSON)
2. Передаёт данные в `ProductCreate`
3. Pydantic проверяет и преобразует типы
4. Функция получает готовый объект `product`

Если данные не прошли валидацию — FastAPI возвращает `422` с подробным описанием ошибки. Функция даже не вызывается.

### Что происходит при разных входных данных

```json
// Корректный запрос
{"name": "Ноутбук", "price": 75000, "category_id": 1}
// → product.name="Ноутбук", product.price=75000.0, product.stock=0 (default)

// Автоматическое преобразование типов
{"name": "Ноутбук", "price": "75000", "category_id": "1"}
// → price="75000" преобразуется в 75000.0, category_id="1" в 1

// Отсутствует обязательное поле
{"name": "Ноутбук", "category_id": 1}
// → 422: field required: price

// Неверный тип который нельзя преобразовать
{"name": "Ноутбук", "price": "дорого", "category_id": 1}
// → 422: value is not a valid number: price
```

---

### Работа с объектом схемы в коде

После того как Pydantic создал объект схемы — с ним можно работать как с обычным Python-объектом.

**Доступ к полям через атрибуты:**

```python
user = UserCreate(name='Алексей', email='alex@mail.ru', city='Москва')

print(user.name)    # Алексей
print(user.email)   # alex@mail.ru
print(user.city)    # Москва
```

**`model_dump()` — превращает объект в словарь:**

```python
user = UserCreate(name='Алексей', email='alex@mail.ru', city='Москва')

data = user.model_dump()
print(data)
# {'name': 'Алексей', 'email': 'alex@mail.ru', 'city': 'Москва'}
```

Это стандартный способ получить все поля объекта как обычный Python-словарь. Используется когда нужно:
- вернуть данные клиенту в JSON-ответе
- передать данные в репозиторий сразу все поля
- залогировать входящие данные

```python
# Типичное применение в эндпоинте
@app.post('/users')
def create_user(user: UserCreate):
    return {
        'message': f'Пользователь {user.name!r} получен',
        'data': user.model_dump()   # {'name': ..., 'email': ..., 'city': ...}
    }
```

> **Примечание:** в старых версиях Pydantic (v1) этот метод назывался `.dict()`. В Pydantic v2 который поставляется с современными версиями FastAPI — `.model_dump()`. Если встретите `.dict()` в старых примерах в интернете — это одно и то же.

---

## Схема ответа — RESPONSE

Схемы работают в обе стороны. **Request-схема** описывает что клиент присылает. **Response-схема** описывает что сервер возвращает.

```python
class ProductResponse(BaseModel):
    id: int
    name: str
    price: float
    stock: int
    category_id: int
```

Response-схема указывается в декораторе через `response_model`:

```python
@router.get('/{product_id}', response_model=ProductResponse)
def get_product(product_id: int):
    with get_connection() as connection:
        repo = ProductRepository(connection)
        product = repo.get_by_id(product_id)
        if product is None:
            raise HTTPException(status_code=404, detail='Товар не найден')
        return dict(product)
```

`response_model` делает три вещи:
1. **Фильтрует** лишние поля — если в `dict(product)` есть поле которого нет в схеме, оно не попадёт в ответ
2. **Валидирует** ответ — убеждается что данные соответствуют схеме
3. **Документирует** — в `/docs` появляется описание структуры ответа

Это особенно важно для безопасности: даже если репозиторий вернул лишние данные (например хэш пароля), `response_model` не пропустит их в ответ.

---

## Разделение схем: Create vs Response

Для одной сущности обычно нужны разные схемы для разных операций. Стандартный паттерн — три схемы:

```python
from pydantic import BaseModel
from typing import Optional


# Базовые поля — общие для Create и Response
class ProductBase(BaseModel):
    name: str
    price: float
    stock: int = 0
    category_id: int


# Схема для создания (POST) — то что клиент присылает
# id не нужен — его назначает база данных
class ProductCreate(ProductBase):
    pass


# Схема для ответа (GET, POST-response) — то что сервер возвращает
# id добавляется — он уже есть после сохранения в БД
class ProductResponse(ProductBase):
    id: int
```

Наследование от `ProductBase` избавляет от дублирования полей. `ProductCreate` и `ProductResponse` расширяют базу только тем что нужно им.

В реальных проектах схем может быть больше — `ProductUpdate` для частичного обновления, `ProductDetail` с вложенными данными категории и так далее.

---

## Pydantic и вложенные объекты

Схемы могут содержать другие схемы — для вложенных данных:

```python
class CategoryResponse(BaseModel):
    id: int
    name: str


class ProductDetail(BaseModel):
    id: int
    name: str
    price: float
    stock: int
    category: CategoryResponse   # вложенный объект
```

FastAPI и Pydantic автоматически сериализуют вложенные схемы в JSON:

```json
{
    "id": 1,
    "name": "Ноутбук Lenovo",
    "price": 75000.0,
    "stock": 12,
    "category": {
        "id": 1,
        "name": "Электроника"
    }
}
```

---

## Валидация через Field

Pydantic предоставляет `Field` для дополнительных ограничений на поля — аналог `CHECK` в SQL:

```python
from pydantic import BaseModel, Field


class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    price: float = Field(gt=0, description='Цена в рублях, больше нуля')
    stock: int = Field(ge=0, default=0, description='Остаток на складе')
    category_id: int = Field(gt=0)
```

Основные параметры `Field`:

| Параметр | Значение | Пример |
|---|---|---|
| `gt` | больше (greater than) | `gt=0` — положительное |
| `ge` | больше или равно | `ge=0` — неотрицательное |
| `lt` | меньше (less than) | `lt=100` |
| `le` | меньше или равно | `le=100` |
| `min_length` | минимальная длина строки | `min_length=1` |
| `max_length` | максимальная длина строки | `max_length=200` |
| `default` | значение по умолчанию | `default=0` |
| `description` | описание для документации | появится в `/docs` |

```json
// Запрос с ценой -100
{"name": "Тест", "price": -100, "category_id": 1}

// Ответ 422:
{
  "detail": [
    {
      "loc": ["body", "price"],
      "msg": "Input should be greater than 0",
      "type": "greater_than"
    }
  ]
}
```

---

## Полный пример: схемы + репозиторий + эндпоинты

Собираем всё вместе. Структура файлов:

```
project/
├── main.py
├── database.py
├── repositories.py
├── schemas.py        ← все схемы в одном файле
└── routers/
    └── products.py
```

```python
# schemas.py
from pydantic import BaseModel, Field
from typing import Optional


class ProductBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
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
```

```python
# routers/products.py
from fastapi import APIRouter, HTTPException
from typing import List
from database import get_connection
from repositories import ProductRepository
from schemas import ProductCreate, ProductResponse

router = APIRouter()


@router.get('/', response_model=List[ProductResponse])
def get_products():
    with get_connection() as connection:
        repo = ProductRepository(connection)
        return [dict(p) for p in repo.get_all()]


@router.get('/{product_id}', response_model=ProductResponse)
def get_product(product_id: int):
    with get_connection() as connection:
        repo = ProductRepository(connection)
        product = repo.get_by_id(product_id)
        if product is None:
            raise HTTPException(status_code=404, detail='Товар не найден')
        return dict(product)


@router.post('/', response_model=ProductResponse, status_code=201)
def create_product(product: ProductCreate):
    with get_connection() as connection:
        repo = ProductRepository(connection)
        product_id = repo.create(
            name=product.name,
            price=product.price,
            stock=product.stock,
            category_id=product.category_id
        )
        created = repo.get_by_id(product_id)
        return dict(created)
```

Три вещи которые стоит отметить:

**`response_model=List[ProductResponse]`** — аннотация типа означающая "список объектов типа `ProductResponse`". FastAPI провалидирует каждый элемент списка через схему `ProductResponse`. Без `List[]` FastAPI ожидал бы один объект а не коллекцию.

**`status_code` в декораторе** — это код по умолчанию для успешного ответа этого эндпоинта. FastAPI устанавливает его автоматически без дополнительного кода в функции. Если внутри функции нужно вернуть другой код (например при ошибке) — используют `HTTPException` с нужным статусом. Декоратор описывает "счастливый путь", исключения — остальные случаи.

**После `create()` делаем `get_by_id()`** — `repo.create()` возвращает только `id` новой записи — `cursor.lastrowid`. Чтобы вернуть клиенту полный объект (включая поля с `DEFAULT` значениями которые назначила база данных), нужно прочитать его из базы. Это стандартный паттерн: создал → прочитал → вернул.

---

## Что видно в /docs

После добавления схем документация становится значительно информативнее:

- Для `POST /products` — показывает пример тела запроса с типами и ограничениями
- Для `GET /products` — показывает структуру ответа
- Для каждого поля — описание из `Field(description=...)`
- Кнопка "Try it out" — автоматически формирует правильный JSON

Документация генерируется из схем без единой строки дополнительного кода.

---

## Вопросы

1. Чем Pydantic-схема отличается от обычного Python-класса?
2. Что произойдёт если клиент пришлёт `{"price": "75000"}` (строку) в поле объявленное как `float`?
3. Зачем нужны две разные схемы `ProductCreate` и `ProductResponse` для одной сущности?
4. Что делает `response_model` в декораторе эндпоинта?
5. Чем `Field(gt=0)` отличается от `Field(ge=0)`?
6. Как объявить необязательное поле которое может быть `None`?
7. Почему после `repo.create()` делается дополнительный вызов `repo.get_by_id()`?
8. Что такое `List[ProductResponse]` в `response_model=List[ProductResponse]`?
9. Как Pydantic связан с Dataclasses которые студенты уже знают?
10. Почему `status_code=201` указывается в декораторе, а не в теле функции?

---

## Задачи

### **Задача 1.** 

Создайте файл `schemas.py` и опишите в нём схему `UserCreate` с полями: `name` (строка, минимум 1 символ), `email` (строка), `city` (строка). Создайте экземпляр схемы в Python и убедитесь что он создаётся корректно.

---

### **Задача 2.** 

Добавьте схему `UserResponse` которая расширяет `UserCreate` полями `id: int` и `created_at: str`. Используйте наследование через базовый класс `UserBase`.

---

### **Задача 3.** 

Создайте эндпоинт `POST /users` который принимает `UserCreate` и возвращает словарь с сообщением  и переданными данными. Проверьте в `/docs` что поля задокументированы.

---

### **Задача 4.** 

Добавьте схему `ProductCreate` с полями `name`, `price` (больше 0), `stock` (не меньше 0, по умолчанию 0), `category_id`. Создайте эндпоинт `POST /products` и проверьте что при передаче отрицательной цены возвращается `422`.

---

### **Задача 5.** 

Создайте эндпоинт `GET /products/{product_id}` с `response_model=ProductResponse`. Данные возьмите из `shop.db` через `ProductRepository`. При отсутствии товара — `raise HTTPException(status_code=404)`.

---

### **Задача 6.** 

Создайте эндпоинт `GET /products` с `response_model=List[ProductResponse]` который возвращает все товары из `shop.db`. Убедитесь что ответ соответствует схеме и лишние поля (например `category_name` из JOIN) отфильтровываются.

---

### **Задача 7.** 

Реализуйте полный CRUD для пользователей с правильными схемами и статус-кодами: `GET /users` → `200`, `GET /users/{id}` → `200` или `404`, `POST /users` → `201`, `DELETE /users/{id}` → `200` или `404`.

---

### **Задача 8.** 

Создайте схему `OrderResponse` с вложенной схемой `UserShort` (только `id` и `name`). Реализуйте эндпоинт `GET /orders` который возвращает список заказов через JOIN, используя вложенную схему. Для вложенной схемы нужно собрать словарь с вложенным словарём — Pydantic сам превратит его в объект `UserShort`.

---

[Предыдущий урок](lesson16.md) | [Следующий урок](lesson18.md)