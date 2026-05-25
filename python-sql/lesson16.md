# Урок 16. Введение в FastAPI

## Что такое FastAPI и зачем он нужен

В прошлом уроке мы разобрали как работает HTTP и что такое REST. Теперь нужно написать сервер который принимает HTTP-запросы и отвечает на них.

Можно написать сервер на чистом Python — но это много низкоуровневой работы: разбирать сырые HTTP-запросы, парсить заголовки, формировать ответы вручную. Фреймворки делают эту работу за нас.

**FastAPI** — современный Python-фреймворк для создания веб-API. Он выбран для этого курса по нескольким причинам:

- **Минимальный порог входа** — первый рабочий эндпоинт пишется в 5 строк
- **Автоматическая документация** — `/docs` генерируется из кода, ничего писать не нужно
- **Встроенная валидация** — неверные данные отклоняются автоматически
- **Современный синтаксис** — использует аннотации типов Python которые вы уже знаете

Важно помнить: в этом модуле мы не изучаем FastAPI полностью. Мы используем его чтобы понять анатомию бэкенда — роутеры, эндпоинты, параметры, ответы. Фреймворк — инструмент, архитектура — цель.

---

## Подготовка проекта

Перед установкой библиотек создадим отдельную папку проекта и виртуальное окружение.

Виртуальное окружение (**venv**) — это изолированная среда Python для конкретного проекта. Она позволяет устанавливать зависимости отдельно от других проектов и не засорять глобальную установку Python.

Создайте папку проекта и перейдите в неё:

```bash
mkdir fastapi_project  # создать папку fastapi_project
cd fastapi_project  # перейти в папку проекта
```

Создайте виртуальное окружение:

```bash
python -m venv venv
```

Активируйте его:

**Windows**

```bash
venv\Scripts\activate
```

**Linux / macOS**

```bash
source venv/bin/activate
```

После активации все устанавливаемые библиотеки будут находиться только внутри этого проекта. 

---

## Установка

```bash
pip install fastapi uvicorn
```

**FastAPI** — сам фреймворк.
**uvicorn** — ASGI-сервер который запускает FastAPI-приложение и слушает HTTP-запросы. Можно воспринимать его как "запускатель" — без него приложение не будет принимать запросы из браузера.

---

## Первое приложение

Создайте файл `main.py`:

```python
from fastapi import FastAPI

app = FastAPI()


@app.get('/')
def root():
    return {'message': 'Привет от FastAPI!'}
```

Запустите:

```bash
uvicorn main:app --reload
```

- `main` — имя файла (`main.py`)
- `app` — имя объекта FastAPI внутри файла
- `--reload` — автоматический перезапуск при изменении кода (только для разработки)

Откройте браузер: `http://127.0.0.1:8000`

```json
{"message": "Привет от FastAPI!"}
```

FastAPI автоматически превратил Python-словарь в JSON-ответ с кодом `200 OK`.

### Как это работает

```python
@app.get('/')       # декоратор регистрирует маршрут: GET /
def root():         # функция-обработчик (handler / view)
    return {...}    # FastAPI сериализует в JSON и отправляет клиенту
```

`@app.get('/')` — это декоратор. Он говорит FastAPI: "когда придёт GET-запрос на путь `/`, вызови функцию `root` и верни результат как JSON-ответ".

---

## Автоматическая документация

FastAPI генерирует интерактивную документацию автоматически — без единой строки дополнительного кода.

Откройте в браузере: `http://127.0.0.1:8000/docs`

Вы увидите **Swagger UI** — интерфейс где можно:
- Просмотреть все эндпоинты приложения
- Увидеть параметры каждого запроса
- Отправить тестовый запрос прямо из браузера и увидеть ответ

Это незаменимый инструмент при разработке — не нужен Postman или curl для базового тестирования.

Альтернативная документация доступна по адресу `/redoc` — другой стиль отображения той же информации.

---

## Роутеры и эндпоинты

**Эндпоинт** — это конкретная комбинация HTTP-метода и пути: `GET /products`, `POST /users`, `DELETE /orders/5`.

**Роутер** — группировщик эндпоинтов. Позволяет разбить большое приложение на модули: все эндпоинты для пользователей — в одном файле, для товаров — в другом.

### Эндпоинты для разных методов

```python
from fastapi import FastAPI

app = FastAPI()


@app.get('/products')
def get_products():
    """Получить список всех товаров."""
    return [
        {'id': 1, 'name': 'Ноутбук', 'price': 75000},
        {'id': 2, 'name': 'Мышь',    'price': 5500},
    ]


@app.post('/products')
def create_product():
    """Создать новый товар."""
    return {'message': 'Товар создан'}


@app.put('/products/{product_id}')
def update_product(product_id: int):
    """Обновить товар."""
    return {'message': f'Товар {product_id} обновлён'}


@app.delete('/products/{product_id}')
def delete_product(product_id: int):
    """Удалить товар."""
    return {'message': f'Товар {product_id} удалён'}
```

Декораторы `@app.get`, `@app.post`, `@app.put`, `@app.delete` соответствуют HTTP-методам из прошлого урока.

---

## Path-параметры

**Path-параметр** — переменная часть URL. Обозначается фигурными скобками в пути:

```python
@app.get('/users/{user_id}')
def get_user(user_id: int):
    return {'user_id': user_id, 'name': 'Алексей Смирнов'}
```

FastAPI извлекает `user_id` из URL и передаёт в функцию. Аннотация типа `int` обязательна — FastAPI автоматически преобразует строку из URL в целое число. Если передать `/users/abc` — вернёт `422 Unprocessable Entity` автоматически.

```
GET /users/5   → user_id = 5   (int)
GET /users/abc → 422 ошибка валидации
```

Несколько path-параметров:

```python
@app.get('/users/{user_id}/orders/{order_id}')
def get_user_order(user_id: int, order_id: int):
    return {
        'user_id':  user_id,
        'order_id': order_id
    }
```

```
GET /users/3/orders/12 → {'user_id': 3, 'order_id': 12}
```

---

## Query-параметры

**Query-параметр** — параметр передаваемый в строке запроса после `?`:

```
GET /products?category_id=1&min_price=1000
```

В FastAPI query-параметры объявляются как обычные параметры функции (без `{}` в пути):

```python
@app.get('/products')
def get_products(category_id: int = None, min_price: float = 0):
    return {
        'category_id': category_id,
        'min_price':   min_price
    }
```

```
GET /products                          → category_id=None, min_price=0
GET /products?category_id=1            → category_id=1,    min_price=0
GET /products?category_id=1&min_price=5000 → category_id=1, min_price=5000.0
```

Значение после `=` в сигнатуре — это значение по умолчанию. `None` означает что параметр необязателен.

### Path vs Query — когда что использовать

| Path-параметр | Query-параметр |
|---|---|
| Идентифицирует конкретный ресурс | Фильтрует или настраивает выборку |
| Обязателен — часть URL | Необязателен — дополнение к URL |
| `/users/5` — конкретный пользователь | `/users?city=Москва` — фильтр по городу |
| `/orders/12` — конкретный заказ | `/products?min_price=1000` — фильтр по цене |

---

## APIRouter — разбивка на модули

Когда эндпоинтов становится много — держать их все в одном `main.py` неудобно. `APIRouter` позволяет разбить приложение на файлы по сущностям:

```python
# routers/users.py
from fastapi import APIRouter

router = APIRouter(prefix='/users', tags=['users'])


@router.get('/')
def get_users():
    return [{'id': 1, 'name': 'Алексей'}]


@router.get('/{user_id}')
def get_user(user_id: int):
    return {'id': user_id, 'name': 'Алексей'}


@router.post('/')
def create_user():
    return {'message': 'Пользователь создан'}
```

```python
# routers/products.py
from fastapi import APIRouter

router = APIRouter(prefix='/products', tags=['products'])


@router.get('/')
def get_products():
    return [{'id': 1, 'name': 'Ноутбук'}]
```

```python
# main.py
from fastapi import FastAPI
from routers import users, products

app = FastAPI()

app.include_router(users.router)
app.include_router(products.router)
```

`prefix='/users'` означает что все пути в этом роутере автоматически получают префикс `/users`. `@router.get('/')` становится `GET /users/`, `@router.get('/{user_id}')` — `GET /users/{user_id}`.

`tags=['users']` — группировка в документации `/docs`.

---

## Структура проекта

Минимальная структура FastAPI-проекта с которой мы будем работать:

```
project/
├── main.py           ← точка входа, подключает роутеры
├── database.py       ← get_connection(), init_db()
├── repositories.py   ← классы-репозитории (из Модуля 2)
├── schemas.py        ← Pydantic-схемы (следующий урок)
└── routers/
    ├── __init__.py
    ├── users.py      ← эндпоинты для пользователей
    └── products.py   ← эндпоинты для товаров
```

`main.py` — только инициализация приложения и подключение роутеров. Вся логика — в модулях.

---

## Полный пример: приложение с роутером

Соберём рабочее приложение которое отдаёт данные из нашей базы `shop.db`:

```python
# database.py
import sqlite3

def get_connection(db_path='shop.db'):
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    return connection
```

```python
# routers/products.py
from fastapi import APIRouter, HTTPException
from database import get_connection

router = APIRouter(prefix='/products', tags=['products'])


@router.get('/')
def get_products(category_id: int = None):
    """Получить список товаров. Можно фильтровать по category_id."""
    with get_connection() as connection:
        cursor = connection.cursor()
        if category_id is not None:
            cursor.execute(
                'SELECT id, name, price, stock FROM products WHERE category_id = ?',
                (category_id,)
            )
        else:
            cursor.execute('SELECT id, name, price, stock FROM products')
        rows = cursor.fetchall()
    return [dict(row) for row in rows]


@router.get('/{product_id}')
def get_product(product_id: int):
    """Получить товар по id."""
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            'SELECT id, name, price, stock FROM products WHERE id = ?',
            (product_id,)
        )
        row = cursor.fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail='Товар не найден')

    return dict(row)
```

```python
# main.py
from fastapi import FastAPI
from routers import products

app = FastAPI(title='Shop API')
app.include_router(products.router)
```

Запустите и откройте `http://127.0.0.1:8000/docs` — вы увидите два эндпоинта с возможностью их протестировать прямо в браузере.

В обработчиках возвращается `dict(row)` вместо просто `row`, потому что `row` — это объект `sqlite3.Row` который FastAPI не умеет сериализовать в JSON напрямую. `dict(row)` преобразует его в обычный Python-словарь который FastAPI умеет конвертировать в JSON.

*В следующем уроке эту задачу возьмут на себя Pydantic-схемы.*

### HTTPException

`HTTPException` — способ вернуть ошибку с нужным кодом статуса:

```python
raise HTTPException(status_code=404, detail='Товар не найден')
```

FastAPI поймает это исключение и вернёт клиенту:

```json
HTTP/1.1 404 Not Found

{"detail": "Товар не найден"}
```

---

## Вопросы

1. Для чего нужен `uvicorn` если FastAPI уже является фреймворком?
2. Что делает флаг `--reload` при запуске через uvicorn?
3. Чем path-параметр отличается от query-параметра в FastAPI?
4. Что произойдёт если отправить `GET /users/abc` когда параметр объявлен как `user_id: int`?
5. Зачем нужен `APIRouter` если можно зарегистрировать все маршруты в `main.py`?
6. Что делает `prefix='/users'` в `APIRouter`?
7. Как FastAPI узнаёт что параметр функции — это query-параметр, а не path-параметр?
8. Что вернёт `raise HTTPException(status_code=404, detail='Не найдено')`?
9. Почему в обработчике возвращается `dict(row)` вместо просто `row`?
10. Что такое `/docs` и как оно появляется без дополнительного кода?

---

## Задачи

### **Задача 1.** 

Создайте файл `main.py` с одним эндпоинтом `GET /` который возвращает `{'status': 'ok', 'version': '1.0'}`. Запустите через uvicorn и проверьте в браузере.

---

### **Задача 2.** 

Добавьте эндпоинт `GET /users/{user_id}` который возвращает словарь с `id` и заглушкой имени. Убедитесь что при передаче нечислового `user_id` возвращается `422` (через документацию или DevTools).

---

### **Задача 3.** 

Создайте эндпоинт `GET /products` с двумя необязательными query-параметрами: `min_price: float = 0` и `max_price: float = None`. Верните словарь с полученными параметрами чтобы убедиться что они передаются корректно.

---

### **Задача 4.** 

Создайте файл `routers/categories.py` с роутером (`prefix='/categories'`) и двумя эндпоинтами: `GET /` (список заглушек) и `GET /{category_id}` (одна заглушка). Подключите роутер в `main.py`.

**Пример категорий**:

```python
CATEGORIES = [
    {'id': 1, 'name': 'Электроника'},
    {'id': 2, 'name': 'Книги'},
]
```

---

### **Задача 5.** 

Создайте эндпоинт `GET /products/{product_id}` который читает данные из `shop.db`. Если товар не найден — возвращает `404` через `HTTPException`. Используйте репозиторий из Модуля 2.

---

### **Задача 6.** 

Создайте эндпоинт `GET /users` с query-параметром `city: str = None`. Если `city` передан — фильтруйте пользователей из `shop.db` по городу. Если не передан — возвращайте всех. Используйте параметризованные запросы.

---

### **Задача 7.** 

Создайте полноценный роутер `routers/products.py` с эндпоинтами `GET /products/` и `GET /products/{product_id}`. Оба читают из `shop.db`. Подключите в `main.py`. Откройте `/docs` и убедитесь что эндпоинты отображаются.

---

### **Задача 8.** 

Создайте два роутера — `routers/users.py` и `routers/products.py` — каждый с `GET /` и `GET /{id}`. Подключите оба в `main.py`. Откройте `/docs` и убедитесь что в документации они разделены по тегам.

---

[Предыдущий урок](lesson15.md) | [Следующий урок](lesson17.md)