# Урок 30. Введение в Data Classes: `@dataclass` и автогенерация методов

---

## Проблема: много повторяющегося кода

Представьте, что вам нужен класс для хранения информации о HTTP-запросе. Это простая структура данных — никакой сложной логики, только хранение нескольких полей. Без специальных инструментов это выглядит так:

```python
class HTTPRequest:
    def __init__(
        self,
        method: str,
        path: str,
        headers: dict,
        body: bytes | None = None,
        query_params: dict | None = None,
    ):
        self.method = method
        self.path = path
        self.headers = headers
        self.body = body
        self.query_params = query_params or {}

    def __repr__(self) -> str:
        return (
            f"HTTPRequest(method={self.method!r}, path={self.path!r}, "
            f"headers={self.headers!r}, body={self.body!r}, "
            f"query_params={self.query_params!r})"
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, HTTPRequest):
            return NotImplemented
        return (
            self.method == other.method
            and self.path == other.path
            and self.headers == other.headers
            and self.body == other.body
            and self.query_params == other.query_params
        )
```

Это 31 строка кода — для простой структуры данных с пятью полями. Причём весь этот код абсолютно предсказуем и однотипен: `__init__` просто присваивает поля, `__repr__` просто их выводит, `__eq__` просто сравнивает их попарно.

Теперь то же самое с `@dataclass`:

```python
from dataclasses import dataclass


@dataclass
class HTTPRequest:
    method: str
    path: str
    headers: dict
    body: bytes | None = None
    query_params: dict | None = None
```

7 строк вместо 31 — и все три метода (`__init__`, `__repr__`, `__eq__`) уже есть.

Декоратор `@dataclass` читает аннотации типов, которые вы пишете для полей, и автоматически генерирует весь шаблонный код. Это не магия — Python буквально создаёт те же методы, что вы написали бы вручную. Просто избавляет вас от рутины.

---

## Что такое Data Class

Data Class — класс, главная задача которого хранить данные. Не выполнять операции, не инкапсулировать поведение, не управлять состоянием — именно хранить структурированные данные с именованными полями.

Модуль `dataclasses` (стандартная библиотека, Python 3.7+) предоставляет декоратор `@dataclass`, который превращает обычное объявление класса в полноценный класс данных с автоматически сгенерированными методами.

По умолчанию `@dataclass` генерирует:
- `__init__` — конструктор со всеми полями как параметрами
- `__repr__` — строковое представление с именами и значениями полей
- `__eq__` — сравнение объектов по значениям всех полей

Дополнительно можно включить:
- `__lt__`, `__le__`, `__gt__`, `__ge__` — операторы сравнения (параметр `order=True`)
- `__hash__` — хеш-функция (при `frozen=True` или `unsafe_hash=True`)

---

## Синтаксис: поля с аннотациями типов

Поля dataclass объявляются как аннотации типов в теле класса:

```python
from dataclasses import dataclass
import datetime


@dataclass
class User:
    id: int                # обязательное поле — нет значения по умолчанию
    username: str          # обязательное поле
    email: str             # обязательное поле
    is_active: bool = True                             # необязательное — есть default
    created_at: datetime.datetime = datetime.datetime.now()   # необязательное
```

Правило: поля **без** значения по умолчанию должны объявляться перед полями **со** значением по умолчанию. Это то же правило, что для обычных параметров функции. При нарушении — `TypeError`:

```python
@dataclass
class Bad:
    name: str = "default"   # поле со значением
    id: int                 # поле без значения — ОШИБКА!

# TypeError: non-default argument 'id' follows default argument
```

Давайте посмотрим, что именно генерирует декоратор:

```python
@dataclass
class Point:
    x: float
    y: float
    label: str = ""


# Автоматически создаётся __init__:
# def __init__(self, x: float, y: float, label: str = "") -> None:
#     self.x = x
#     self.y = y
#     self.label = label

# Автоматически создаётся __repr__:
# def __repr__(self) -> str:
#     return f"Point(x={self.x!r}, y={self.y!r}, label={self.label!r})"

# Автоматически создаётся __eq__:
# def __eq__(self, other) -> bool:
#     if other.__class__ is self.__class__:
#         return (self.x, self.y, self.label) == (other.x, other.y, other.label)
#     return NotImplemented

p1 = Point(1.0, 2.0)
p2 = Point(1.0, 2.0)
p3 = Point(1.0, 2.0, "A")

print(p1)           # Point(x=1.0, y=2.0, label='')
print(p1 == p2)     # True — равны по значениям
print(p1 == p3)     # False — label отличается
```

---

## `__post_init__`: расширение инициализации

Иногда автогенерированного `__init__` недостаточно: нужно провалидировать данные, вычислить производные поля или выполнить какую-то логику после создания объекта. Для этого существует специальный метод `__post_init__` — он вызывается сразу после автогенерированного `__init__`:

```python
from dataclasses import dataclass


@dataclass
class APIEndpoint:
    """Описание эндпоинта API."""
    base_url: str
    path: str
    method: str = "GET"
    full_url: str = ""   # вычисляется в __post_init__

    def __post_init__(self) -> None:
        # Вызывается сразу после __init__
        # Здесь self.base_url, self.path, self.method уже установлены

        # Нормализация данных
        self.method = self.method.upper()

        # Вычисление производного поля
        self.full_url = f"{self.base_url.rstrip('/')}/{self.path.lstrip('/')}"

        # Валидация
        if self.method not in {"GET", "POST", "PUT", "DELETE", "PATCH"}:
            raise ValueError(f"Недопустимый HTTP-метод: {self.method!r}")


endpoint = APIEndpoint(
    base_url="https://api.example.com",
    path="/users",
    method="get"
)
print(endpoint.method)    # GET — нормализован в __post_init__
print(endpoint.full_url)  # https://api.example.com/users

try:
    bad = APIEndpoint("https://api.example.com", "/users", "CONNECT")
except ValueError as e:
    print(e)   # Недопустимый HTTP-метод: 'CONNECT'
```

Другой распространённый случай — валидация значений при создании:

```python
from dataclasses import dataclass


@dataclass
class Price:
    """Цена товара в копейках (целое число для точности)."""
    amount: int       # сумма в копейках
    currency: str = "RUB"

    def __post_init__(self) -> None:
        if self.amount < 0:
            raise ValueError(f"Цена не может быть отрицательной: {self.amount}")
        if len(self.currency) != 3:
            raise ValueError(f"Валюта должна быть трёхбуквенным кодом: {self.currency!r}")
        self.currency = self.currency.upper()

    @property
    def in_rubles(self) -> float:
        return self.amount / 100


price = Price(15000, "rub")   # нормализуется
print(price)                  # Price(amount=15000, currency='RUB')
print(price.in_rubles)        # 150.0

try:
    Price(-100)
except ValueError as e:
    print(e)   # Цена не может быть отрицательной: -100
```

---

## Параметры декоратора `@dataclass`

`@dataclass` принимает несколько параметров, управляющих генерацией методов:

```python
@dataclass(
    init=True,        # генерировать __init__ (по умолчанию True)
    repr=True,        # генерировать __repr__ (по умолчанию True)
    eq=True,          # генерировать __eq__ (по умолчанию True)
    order=False,      # генерировать операторы сравнения (по умолчанию False)
    frozen=False,     # запретить изменение атрибутов (по умолчанию False)
    unsafe_hash=False # добавить __hash__ для изменяемого класса (по умолчанию False)
)
class MyDataClass:
    ...
```

Рассмотрим наиболее важные параметры.

### `order=True`: автоматическая сортировка

```python
from dataclasses import dataclass
import datetime


@dataclass(order=True)
class Task:
    """Задача в системе управления проектами."""
    priority: int          # меньше = выше приоритет
    deadline: datetime.date
    title: str
    # Поля сравниваются в порядке объявления: сначала priority, затем deadline, затем title


tasks = [
    Task(3, datetime.date(2024, 3, 15), "Обновить документацию"),
    Task(1, datetime.date(2024, 1, 10), "Исправить критический баг"),
    Task(2, datetime.date(2024, 2, 20), "Добавить пагинацию"),
    Task(1, datetime.date(2024, 1, 5), "Настроить мониторинг"),
]

for task in sorted(tasks):
    print(task)
# Task(priority=1, deadline=datetime.date(2024, 1, 5), title='Настроить мониторинг')
# Task(priority=1, deadline=datetime.date(2024, 1, 10), title='Исправить критический баг')
# Task(priority=2, deadline=datetime.date(2024, 2, 20), title='Добавить пагинацию')
# Task(priority=3, deadline=datetime.date(2024, 3, 15), title='Обновить документацию')

print(tasks[0] > tasks[1])   # True: priority 3 > priority 1
```

Порядок сравнения полей — это порядок их объявления. Это важно: если поля объявлены в неудобном порядке — сортировка будет работать неожиданно.

### `frozen=True`: иммутабельные dataclass

```python
from dataclasses import dataclass, FrozenInstanceError


@dataclass(frozen=True)
class Coordinate:
    """Географическая координата. Иммутабельна — как и должна быть."""
    latitude: float
    longitude: float
    altitude: float = 0.0


moscow = Coordinate(55.7558, 37.6173)

# Попытка изменить — немедленная ошибка
try:
    moscow.latitude = 0.0
except FrozenInstanceError as e:
    print(e)   # cannot assign to field 'latitude'

# Замороженный dataclass автоматически получает __hash__
# Можно использовать как ключ словаря и элемент множества
locations = {moscow, Coordinate(59.9343, 30.3351)}   # set с Coordinate!
print(len(locations))   # 2

cache: dict[Coordinate, str] = {
    moscow: "Москва",
}
print(cache[Coordinate(55.7558, 37.6173)])   # Москва — работает как ключ
```

`frozen=True` превращает dataclass в Value Object — объект, идентичность которого определяется значениями полей. Это идеально для географических координат, денежных сумм, точек на плоскости — любых данных, которые не должны изменяться после создания.

---

## `field()`: точная настройка отдельных полей

Функция `field()` позволяет настроить поведение конкретного поля:

```python
from dataclasses import dataclass, field
import datetime


@dataclass
class UserSession:
    user_id: int
    token: str
    # repr=False — не выводить в __repr__ (пароли, токены, секреты)
    refresh_token: str = field(repr=False, compare=False)
    # compare=False — не учитывать при сравнении
    last_accessed: datetime.datetime = field(
        default_factory=datetime.datetime.now,
        compare=False,
    )
    # init=False — не передаётся в конструктор, вычисляется в __post_init__
    session_key: str = field(init=False, repr=False)

    def __post_init__(self) -> None:
        # Поле с init=False инициализируется здесь
        self.session_key = f"session:{self.user_id}:{self.token[:8]}"


session1 = UserSession(1, "long-token-value-abc", "refresh-xyz-123")
session2 = UserSession(1, "long-token-value-abc", "refresh-xyz-456")

print(session1)
# UserSession(user_id=1, token='long-token-value-abc')
# refresh_token и session_key скрыты (repr=False)
# last_accessed скрыт (repr=False через параметр)

print(session1 == session2)
# True — last_accessed исключён из сравнения (compare=False)
# хотя refresh_token разный, сравниваются: user_id и token
```

### Изменяемые значения по умолчанию: `field(default_factory=...)`

Одна из самых частых ошибок в Python — использование изменяемого объекта как значения по умолчанию. В dataclass это явно запрещено:

```python
@dataclass
class BadRequest:
    headers: dict = {}   # TypeError! Нельзя использовать изменяемые дефолты
    tags: list = []      # TypeError!
```

Почему это запрещено? Если бы `{}` был разрешён, все экземпляры класса использовали бы один и тот же объект словаря — изменение в одном объекте затронуло бы все.

Правильный способ — использовать `field(default_factory=...)`:

```python
from dataclasses import dataclass, field


@dataclass
class HTTPRequest:
    path: str
    method: str = "GET"
    headers: dict = field(default_factory=dict)   # каждый раз создаётся новый dict
    tags: list = field(default_factory=list)       # каждый раз создаётся новый list


req1 = HTTPRequest("/api/users")
req2 = HTTPRequest("/api/orders")

req1.headers["Authorization"] = "Bearer token"
print(req1.headers)   # {'Authorization': 'Bearer token'}
print(req2.headers)   # {} — независимый словарь
```

`default_factory` принимает вызываемый объект (функцию или класс) без аргументов, который вызывается при создании каждого экземпляра. Можно передать `dict`, `list`, `set` — или собственную функцию:

```python
def default_headers():
    return {"Content-Type": "application/json", "Accept": "application/json"}


@dataclass
class APIRequest:
    url: str
    headers: dict = field(default_factory=default_headers)


req = APIRequest("https://api.example.com/users")
print(req.headers)
# {'Content-Type': 'application/json', 'Accept': 'application/json'}
```

---

## `ClassVar`: атрибуты класса в dataclass

По умолчанию все аннотированные поля становятся полями dataclass — параметрами `__init__`. Но иногда нужны атрибуты класса (не экземпляра). Для этого используется `ClassVar` из модуля `typing`:

```python
from dataclasses import dataclass
from typing import ClassVar


@dataclass
class APIClient:
    base_url: str
    timeout: int = 30

    # ClassVar — атрибут класса, НЕ поле dataclass
    # Не попадает в __init__, __repr__, __eq__
    MAX_RETRIES: ClassVar[int] = 3
    DEFAULT_TIMEOUT: ClassVar[int] = 30
    _instances: ClassVar[list] = []   # тоже атрибут класса


client = APIClient("https://api.example.com")
print(client)   # APIClient(base_url='https://api.example.com', timeout=30)
# MAX_RETRIES и DEFAULT_TIMEOUT не попали в __repr__

print(APIClient.MAX_RETRIES)   # 3
print(client.MAX_RETRIES)      # 3 — доступен через экземпляр тоже
```

---

## Встроенные функции для работы с dataclass

Модуль `dataclasses` предоставляет несколько полезных функций:

```python
from dataclasses import dataclass, field, fields, asdict, astuple
import datetime


@dataclass
class OrderItem:
    product_id: int
    product_name: str
    price: float
    quantity: int


@dataclass
class Order:
    order_id: int
    user_id: int
    items: list = field(default_factory=list)
    created_at: datetime.datetime = field(default_factory=datetime.datetime.now)
    status: str = "pending"


item1 = OrderItem(1, "Ноутбук", 89990.0, 1)
item2 = OrderItem(2, "Мышь", 1500.0, 2)

order = Order(
    order_id=1001,
    user_id=42,
    items=[item1, item2],
)

# asdict() — рекурсивно конвертирует dataclass в словарь
order_dict = asdict(order)
print(order_dict)
# {'order_id': 1001, 'user_id': 42, 'items': [{'product_id': 1, ...}, ...],
#  'created_at': datetime.datetime(...), 'status': 'pending'}

# astuple() — конвертирует в кортеж
item_tuple = astuple(item1)
print(item_tuple)   # (1, 'Ноутбук', 89990.0, 1)

# fields() — возвращает список полей dataclass
for f in fields(order):
    print(f"Поле: {f.name}: {f.type}, default={f.default}")
# Поле: order_id: int, default=MISSING
# Поле: user_id: int, default=MISSING
# Поле: items: list, default=MISSING
# ...
```

`asdict()` особенно полезен для сериализации в JSON:

```python
import json

# asdict конвертирует вложенные dataclass рекурсивно
# datetime нужно обработать отдельно для JSON
def order_to_json(order: Order) -> str:
    d = asdict(order)
    d["created_at"] = order.created_at.isoformat()
    d["items"] = [asdict(item) for item in order.items]
    return json.dumps(d, ensure_ascii=False)

print(order_to_json(order))
```

---

## Практический пример: DTO для веб-API

Data Classes идеально подходят для объектов передачи данных (DTO) в веб-приложениях:

```python
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any
import datetime


# ─── Request DTOs ──────────────────────────────────────────────────────────

@dataclass
class CreateUserRequest:
    """DTO для создания пользователя. Приходит из тела HTTP-запроса."""
    username: str
    email: str
    password: str
    roles: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.username = self.username.strip()
        self.email = self.email.lower().strip()

        if len(self.username) < 3:
            raise ValueError(f"username слишком короткий: {self.username!r}")
        if "@" not in self.email:
            raise ValueError(f"Некорректный email: {self.email!r}")
        if len(self.password) < 8:
            raise ValueError("Пароль слишком короткий (минимум 8 символов)")


@dataclass
class UpdateUserRequest:
    """DTO для обновления пользователя. Все поля опциональны."""
    username: str | None = None
    email: str | None = None
    is_active: bool | None = None
    roles: list[str] | None = None

    def __post_init__(self) -> None:
        if self.email is not None:
            self.email = self.email.lower().strip()


@dataclass
class PaginationParams:
    """Параметры пагинации из query string."""
    page: int = 1
    page_size: int = 20
    sort_by: str = "created_at"
    sort_order: str = "desc"

    def __post_init__(self) -> None:
        if self.page < 1:
            raise ValueError(f"page должен быть >= 1, получен {self.page}")
        if not 1 <= self.page_size <= 100:
            raise ValueError(f"page_size должен быть от 1 до 100, получен {self.page_size}")

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


# ─── Response DTOs ─────────────────────────────────────────────────────────

@dataclass(frozen=True)   # ответы иммутабельны — не изменяем их после создания
class UserResponse:
    """DTO для ответа API с данными пользователя."""
    id: int
    username: str
    email: str
    is_active: bool
    roles: tuple[str, ...]   # кортеж вместо списка (frozen требует хешируемых полей)
    created_at: str          # ISO-формат для JSON

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "is_active": self.is_active,
            "roles": list(self.roles),
            "created_at": self.created_at,
        }


@dataclass(frozen=True)
class PaginatedResponse:
    """Обёртка для пагинированных ответов."""
    data: tuple          # кортеж элементов
    total: int
    page: int
    page_size: int
    total_pages: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "data": [
                item.to_dict() if hasattr(item, "to_dict") else item
                for item in self.data
            ],
            "pagination": {
                "total": self.total,
                "page": self.page,
                "page_size": self.page_size,
                "total_pages": self.total_pages,
            }
        }


# ─── Error DTOs ────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class APIError:
    """DTO для ошибок API."""
    error_code: str
    message: str
    status_code: int
    details: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "error": self.error_code,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp,
        }

    @classmethod
    def validation_error(cls, errors: dict[str, list[str]]) -> APIError:
        return cls(
            error_code="VALIDATION_ERROR",
            message="Данные не прошли валидацию",
            status_code=422,
            details={"validation_errors": errors},
        )

    @classmethod
    def not_found(cls, resource: str, resource_id: int | str) -> APIError:
        return cls(
            error_code="NOT_FOUND",
            message=f"{resource} с id={resource_id!r} не найден",
            status_code=404,
        )


# ─── Демонстрация ───────────────────────────────────────────────────────────

print("=== Request DTO ===")
try:
    req = CreateUserRequest(
        username="  alice  ",
        email="ALICE@EXAMPLE.COM",
        password="secure123",
        roles=["admin"],
    )
    print(req)
    # Нормализованные данные:
    print(f"username: {req.username!r}")    # 'alice'
    print(f"email: {req.email!r}")          # 'alice@example.com'
except ValueError as e:
    print(f"Ошибка: {e}")

print("\n=== Валидация ===")
try:
    bad_req = CreateUserRequest("ab", "not-email", "short")
except ValueError as e:
    print(f"Ошибка: {e}")

print("\n=== Response DTO ===")
response = UserResponse(
    id=1,
    username="alice",
    email="alice@example.com",
    is_active=True,
    roles=("admin", "user"),
    created_at=datetime.datetime.now().isoformat(),
)
print(response)
print(response.to_dict())

# frozen=True — нельзя изменить
try:
    response.username = "bob"
except Exception as e:
    print(f"\nНельзя изменить frozen dataclass: {type(e).__name__}")

print("\n=== Error DTO ===")
error = APIError.validation_error({
    "username": ["Слишком короткое"],
    "email": ["Некорректный формат"],
})
print(error.to_dict())

not_found = APIError.not_found("User", 99)
print(not_found.to_dict())

print("\n=== Pagination ===")
pagination = PaginationParams(page=2, page_size=10)
print(f"page={pagination.page}, offset={pagination.offset}")
# page=2, offset=10
```

---

## Практический пример: Value Objects

Value Objects — объекты, идентичность которых определяется значениями полей, а не ссылкой. Dataclass с `frozen=True` идеально выражает это понятие:

```python
from dataclasses import dataclass, field
from typing import ClassVar


@dataclass(frozen=True, order=True)
class Money:
    """
    Денежная сумма. Value Object.
    Иммутабельна, хешируема, сравниваема.
    """
    amount: int    # в копейках для точности
    currency: str = "RUB"

    # Атрибут класса — список допустимых валют
    SUPPORTED_CURRENCIES: ClassVar[frozenset[str]] = frozenset({"RUB", "USD", "EUR"})

    def __post_init__(self) -> None:
        if self.amount < 0:
            raise ValueError(f"Сумма не может быть отрицательной: {self.amount}")
        if self.currency not in self.SUPPORTED_CURRENCIES:
            raise ValueError(
                f"Неподдерживаемая валюта: {self.currency!r}. "
                f"Поддерживаются: {self.SUPPORTED_CURRENCIES}"
            )

    @property
    def in_major_units(self) -> float:
        """Сумма в основных единицах (рублях, долларах...)."""
        return self.amount / 100

    def __str__(self) -> str:
        return f"{self.in_major_units:.2f} {self.currency}"

    def __add__(self, other: object) -> "Money":
        if not isinstance(other, Money):
            return NotImplemented
        if self.currency != other.currency:
            raise ValueError(
                f"Нельзя складывать {self.currency} и {other.currency}"
            )
        return Money(self.amount + other.amount, self.currency)

    def __sub__(self, other: object) -> "Money":
        if not isinstance(other, Money):
            return NotImplemented
        if self.currency != other.currency:
            raise ValueError(
                f"Нельзя вычитать {other.currency} из {self.currency}"
            )
        return Money(self.amount - other.amount, self.currency)

    def __mul__(self, factor: int | float) -> "Money":
        return Money(round(self.amount * factor), self.currency)


@dataclass(frozen=True)
class Address:
    """Почтовый адрес. Value Object."""
    country: str
    city: str
    street: str
    house: str
    apartment: str | None = None
    postal_code: str | None = None

    def __str__(self) -> str:
        parts = [self.country, self.city, self.street, self.house]
        if self.apartment:
            parts.append(f"кв. {self.apartment}")
        return ", ".join(parts)


# Демонстрация Value Objects

price1 = Money(150000, "RUB")   # 1500.00 RUB
price2 = Money(50000, "RUB")    # 500.00 RUB

total = price1 + price2
print(f"Итого: {total}")          # Итого: 2000.00 RUB
print(f"Скидка: {price1 - price2}")   # Скидка: 1000.00 RUB

discount_10pct = price1 * 0.9
print(f"Со скидкой 10%: {discount_10pct}")   # Со скидкой 10%: 1350.00 RUB

# Сортировка (order=True)
prices = [Money(30000), Money(10000), Money(20000)]
for p in sorted(prices):
    print(p)
# 100.00 RUB
# 200.00 RUB
# 300.00 RUB

# Использование как ключ словаря (frozen → hashable)
price_labels: dict[Money, str] = {
    Money(0): "Бесплатно",
    Money(50000): "Базовый",
    Money(150000): "Премиум",
}
print(price_labels[Money(50000)])   # Базовый

# Использование в множестве
unique_prices = {Money(10000), Money(20000), Money(10000)}
print(len(unique_prices))   # 2

addr = Address("Россия", "Москва", "ул. Пушкина", "10", "5", "101000")
print(addr)   # Россия, Москва, ул. Пушкина, 10, кв. 5
```

---

## Когда `@dataclass`, а когда обычный класс

Data Class — мощный инструмент, но не универсальный. Выбирайте его осознанно.

**Dataclass подходит, когда:**
- Класс в первую очередь хранит данные, а не реализует поведение.
- Поля известны заранее и стабильны.
- Нужны `__init__`, `__repr__`, `__eq__` со стандартным поведением.
- Создаёте DTO, Value Objects, конфигурационные объекты.

**Обычный класс предпочтительнее, когда:**
- Поведение важнее данных (много методов, мало полей).
- Нужна сложная инкапсуляция с приватными атрибутами.
- `__init__` или `__eq__` требуют нестандартной логики, которую неудобно писать через `__post_init__`.
- Класс является частью глубокой иерархии наследования.

Хорошее правило: если первое, о чём вы думаете — «какие данные хранит этот объект?», используйте dataclass. Если первое — «что этот объект умеет делать?», используйте обычный класс.

---

## Неочевидные моменты и типичные ошибки

**`order=True` и поля в неправильном порядке.** Поля сравниваются в порядке объявления. Если первое поле — `title: str`, а второе — `priority: int`, то сортировка будет идти сначала по алфавиту title, а не по приоритету:

```python
@dataclass(order=True)
class Task:
    title: str    # сначала сравнивается title!
    priority: int # потом priority

t1 = Task("A", 1)
t2 = Task("B", 1)
t3 = Task("A", 2)

print(sorted([t2, t1, t3]))
# [Task(title='A', priority=1), Task(title='A', priority=2), Task(title='B', priority=1)]
# Сортировка по title, а не по priority!
```

Если нужна сортировка по определённому полю, а не по всем — не используйте `order=True`. Используйте `key=` в `sorted()` или реализуйте `__lt__` вручную.

**`field(compare=False)` при `order=True`.** Если поле исключено из сравнения (`compare=False`), оно исключается и из `__lt__` и других операторов порядка. Это иногда приводит к неожиданному поведению.

**Dataclass и `__hash__`.** По умолчанию, если `eq=True` (по умолчанию), Python устанавливает `__hash__ = None` — объект нехешируем. Чтобы сделать dataclass хешируемым:
- Используйте `frozen=True` — тогда `__hash__` генерируется автоматически.
- Или `unsafe_hash=True` — добавляет `__hash__`, но объект остаётся изменяемым (небезопасно).

**`frozen=True` и проверка атрибутов в `__post_init__`**. После создания объекта любое присваивание атрибутов запрещено. Если попробовать присвоить значение уже созданному атрибуту, когда параметр frozen установлен в True это вызовет ошибку `dataclasses.FrozenInstanceError`. Однако при создании объекта часто требуется нормализовать или валидировать данные.

Рассмотрим класс для нормализации номера телефона:

```python
@dataclass(frozen=True)
class PhoneNumber:
    number: str  # атрибут, который нужно нормализовать
    country_code: str = "7"

    def __post_init__(self) -> None:
        cleaned = re.sub(r"[\s\-\(\)\+]", "", self.number)
        if cleaned.startswith(self.country_code):
            cleaned = cleaned[len(self.country_code):]
        if not cleaned.isdigit() or len(cleaned) != 10:
            raise ValueError(f"Некорректный номер телефона: {self.number!r}")
        # после нормализации нам нужно присвоить очищенное значение cleaned в атрибут number
        self.number = cleaned  # Ошибка FrozenInstanceError

p1 = PhoneNumber('+7 928 714 49 14')
```

Ошибка происходит потому что под капотом `dataclass` генерирует примерно такое поведение:

```python
def __setattr__(self, name, value):
    raise FrozenInstanceError(...)
```

К моменту, когда мы встречаем строку `self.number = cleaned` объект уже создан. Поэтому вызвав присвоение будет выбрасываться ошибка `FrozenInstanceError`.

Изменить такое поведение можно вызовом свойства `__setattr__` из класса object вместо обычного присваивания:

```python
object.__setattr__(self, 'number', cleaned)
```

> Важно: это **не "хак"**, а **официальный паттерн**, 
> предусмотренный дизайном `dataclasses`.

---

## Итоги урока

`@dataclass` — декоратор, автоматически генерирующий `__init__`, `__repr__`, `__eq__` из аннотаций типов. Он избавляет от шаблонного кода при создании классов-контейнеров данных.

Поля без значения по умолчанию объявляются перед полями со значением. Изменяемые объекты в качестве значений по умолчанию требуют `field(default_factory=...)`. `__post_init__` вызывается после автогенерированного `__init__` — для валидации и вычисляемых полей.

Параметр `frozen=True` делает объект иммутабельным и хешируемым — идеально для Value Objects. `order=True` добавляет операторы сравнения для сортировки. Атрибуты класса (не экземпляра) объявляются через `ClassVar`.

`asdict()`, `astuple()`, `fields()` — встроенные функции для работы с dataclass.

В следующем уроке мы разберём `field()` подробнее, включая `InitVar`, `__post_init__` с нестандартными параметрами, и посмотрим, как dataclass взаимодействует с наследованием.

---

## Вопросы

1. Какие три метода автоматически генерирует `@dataclass` по умолчанию? Как это уменьшает количество шаблонного кода?
2. Почему нельзя объявить поле с `default=[]` в dataclass? Как правильно объявить поле со списком по умолчанию?
3. Что такое `__post_init__` и когда он вызывается? Приведите два примера его использования.
4. Чем `frozen=True` отличается от обычного dataclass? Почему `frozen=True` добавляет `__hash__`?
5. В каком порядке сравниваются поля при `order=True`? Как изменить порядок сортировки?
6. Что делает `field(repr=False)` и `field(compare=False)`? Приведите пример, когда каждый из них полезен.
7. Как объявить атрибут класса (не экземпляра) в dataclass? Почему нельзя просто написать `MAX_SIZE = 100`?
8. Что делают функции `asdict()` и `astuple()`? В чём их практическое применение?

---

## Задачи

### **Задача 1**. 

Конфигурация приложения

Создайте dataclass `AppConfig` для хранения конфигурации веб-приложения. Поля:
- `app_name: str` — обязательное
- `debug: bool = False`
- `host: str = "localhost"`
- `port: int = 8000`
- `database_url: str = "sqlite:///db.sqlite3"`
- `secret_key: str = field(repr=False)` — обязательное, не выводится в repr
- `allowed_hosts: list[str] = field(default_factory=list)`
- `max_connections: int = 100`
- `base_url: str = field(init=False)` — вычисляется в `__post_init__`

В `__post_init__`: вычислить `base_url` как `http://host:port`, проверить что `port` в диапазоне 1–65535.

Добавьте метод `is_production() -> bool` (True если `debug=False`). Сделайте dataclass `frozen=True`.

**Пример использования**:

```python
config = AppConfig(
    app_name="MyWebApp",
    secret_key="super-secret-key-123",
    port=8080,
    allowed_hosts=["localhost", "myapp.com"],
)

print(config)
# AppConfig(app_name='MyWebApp', debug=False, host='localhost', port=8080, ...)
# secret_key не виден!

print(config.base_url)       # http://localhost:8080
print(config.is_production()) # True

try:
    AppConfig("App", "key", port=99999)
except ValueError as e:
    print(e)
```

---

### **Задача 2**. 

Система задач с сортировкой

Создайте dataclass `Task` для системы управления задачами. Поля:
- `id: int`
- `title: str`
- `priority: int` — от 1 (критичный) до 5 (низкий)
- `status: str = "todo"` — возможные значения: `"todo"`, `"in_progress"`, `"done"`
- `tags: list[str] = field(default_factory=list)`
- `created_at: datetime.datetime = field(default_factory=datetime.datetime.now, compare=False)`

Сделайте `order=True` так, чтобы задачи сортировались по приоритету (меньше число = выше), а при равном приоритете — по `id`. В `__post_init__` проверьте допустимость `priority` и `status`.

Создайте dataclass `TaskList` с полем `tasks: list[Task] = field(default_factory=list)` и методами `add(task)`, `get_by_priority() -> list[Task]`, `get_by_status(status) -> list[Task]`.

**Пример использования**:

```python
task_list = TaskList()
task_list.add(Task(3, "Обновить документацию", priority=4))
task_list.add(Task(1, "Исправить баг", priority=1, tags=["bug", "critical"]))
task_list.add(Task(2, "Добавить пагинацию", priority=2))

for task in task_list.get_by_priority():
    print(f"[{task.priority}] {task.title}")
```

---

### **Задача 3**. 

Иммутабельные Value Objects

Создайте набор Value Objects с `frozen=True`:

1. `Email(value: str)` — в `__post_init__` нормализует (lowercase) и валидирует. `__str__` возвращает строку.

2. `PhoneNumber(number: str, country_code: str = "7")` — нормализует номер в `__post_init__` (убирает пробелы, дефисы, скобки). Свойство `formatted` возвращает `+7 (999) 123-45-67`. 

3. `IPAddress(value: str)` — валидирует формат IPv4. Свойство `octets` возвращает кортеж четырёх целых чисел.

Все три должны быть хешируемыми и работать как ключи словарей и элементы множеств.

**Пример использования**:

```python
e1 = Email("ALICE@EXAMPLE.COM")
e2 = Email("alice@example.com")
print(e1 == e2)   # True — нормализованы

emails = {e1, e2}
print(len(emails))   # 1 — дедупликация через множество

ip = IPAddress("192.168.1.1")
print(ip.octets)   # (192, 168, 1, 1)

# Использование как ключи
user_map = {Email("alice@example.com"): "Alice"}
print(user_map[Email("ALICE@EXAMPLE.COM")])   # Alice
```

---

### **Задача 4**. 

REST API Response DTO

Создайте систему DTO для REST API ответов. Базовый dataclass `BaseResponse` с полями `success: bool` и `timestamp: str = field(default_factory=...)`. Дочерние dataclass:
- `SuccessResponse(BaseResponse)` — добавляет `data: dict`, `message: str = "OK"`.
- `ErrorResponse(BaseResponse)` — добавляет `error_code: str`, `message: str`, `details: dict = field(default_factory=dict)`.
- `PaginatedResponse(SuccessResponse)` — добавляет `total: int`, `page: int`, `page_size: int`. Свойство `total_pages`.

Все должны иметь метод `to_dict() -> dict`. Используйте `asdict()` там, где возможно.

**Пример использования**:

```python
ok = SuccessResponse(data={"user": "alice"})
err = ErrorResponse(error_code="NOT_FOUND", message="Пользователь не найден")
paginated = PaginatedResponse(
    data={"users": [...]},
    total=50,
    page=2,
    page_size=10,
)

print(ok.to_dict())
print(err.to_dict())
print(paginated.total_pages)   # 5
print(paginated.success)       # True
```

---

### **Задача 5**. 

Конфигурация роутинга

Создайте систему конфигурации маршрутов API с использованием dataclass. Dataclass `RouteParam` с полями `name: str`, `type: str` (`"int"`, `"str"`, `"uuid"`), `required: bool = True`. Dataclass `Route` (frozen=True) с полями `path: str`, `method: str`, `handler_name: str`, `params: tuple[RouteParam, ...] = field(default_factory=tuple)`, `auth_required: bool = True`, `rate_limit: int = 100`. В `__post_init__`: нормализовать `method` к верхнему регистру, проверить что path начинается с `/`. Свойство `path_params` — список обязательных параметров пути. Свойство `full_signature` — строка вида `"GET /api/users/{id}"`.

Dataclass `Router` с `routes: list[Route] = field(default_factory=list)`, методами `add_route(route)` и `find_route(method, path) -> Route | None`.

**Пример использования**:

```python
router = Router()
router.add_route(Route(
    "/api/users",
    "get",
    "list_users",
    auth_required=True,
))
router.add_route(Route(
    "/api/users/{id}",
    "get",
    "get_user",
    params=(RouteParam("id", "int"),),
))

print(router.find_route("GET", "/api/users").full_signature)
# GET /api/users

route = router.find_route("GET", "/api/users/{id}")
print(route.full_signature)   # GET /api/users/{id}
print(route.path_params)      # [RouteParam(name='id', type='int', required=True)]
```

---

[Предыдущий урок](lesson29.md) | [Следующий урок](lesson31.md)