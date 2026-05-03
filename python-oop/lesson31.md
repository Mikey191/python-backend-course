# Урок 31. Углубляемся в Data Classes: `field()`, `__post_init__`, `ClassVar`

---

## Что осталось за рамками предыдущего урока

В уроке 30 мы рассмотрели основы `@dataclass`: автогенерацию методов, базовые параметры `field()`, `frozen=True`, `order=True` и `__post_init__` для простых случаев. Но у dataclass есть несколько мощных механизмов, которые нужно знать для реального использования:

- `InitVar` — как передать данные в инициализацию, не сохраняя их в объекте
- `metadata` — как хранить произвольную информацию о поле
- `kw_only` — как контролировать способ передачи аргументов
- `replace()` — как «изменять» иммутабельные объекты
- `slots=True` — как автоматически оптимизировать память
- Полная логика `__hash__` — почему dataclass нехешируем по умолчанию

Разберём каждый из этих механизмов подробно.

---

## `field()` в деталях: все параметры

Функция `field()` принимает следующие параметры:

```python
from dataclasses import field

field(
    default=MISSING,          # значение по умолчанию
    default_factory=MISSING,  # фабрика для изменяемых дефолтов
    init=True,                # включать в __init__
    repr=True,                # включать в __repr__
    hash=None,                # включать в __hash__ (None = следовать compare)
    compare=True,             # включать в __eq__ и порядковые методы
    metadata=None,            # произвольные метаданные (маппинг)
    kw_only=MISSING,          # только keyword argument в __init__
)
```

Большинство параметров мы уже знаем. Остановимся на тех, что требуют дополнительного разбора.

### `hash` — отдельно от `compare`

Параметр `hash` управляет включением поля в `__hash__` независимо от `compare`:

```python
from dataclasses import dataclass, field
import datetime


@dataclass(frozen=True)
class CacheEntry:
    key: str
    value: str
    # created_at влияет на сравнение (compare=True по умолчанию),
    # но НЕ влияет на хеш (hash=False) — хеш только по key
    created_at: datetime.datetime = field(
        default_factory=datetime.datetime.now,
        hash=False,    # не включать в __hash__
        compare=True,  # но включать в __eq__
    )


e1 = CacheEntry("user:1", "alice", datetime.datetime(2024, 1, 1))
e2 = CacheEntry("user:1", "alice", datetime.datetime(2024, 6, 1))

# Разные created_at — объекты НЕ равны (compare=True)
print(e1 == e2)   # False

# Но хеши одинаковые (hash=False для created_at)
print(hash(e1) == hash(e2))   # True (хеш только по key и value)

# Это позволяет использовать в словаре с предсказуемым поведением
cache: dict[CacheEntry, str] = {e1: "cached"}
# (на практике словари обычно используют строку как ключ,
#  но иллюстрирует независимость hash от compare)
```

Это редкий, но полезный паттерн: объекты «равны» по одним критериям, но хешируются по другим.

### `kw_only=True` — только именованные аргументы

```python
from dataclasses import dataclass, field


@dataclass
class UserEvent:
    user_id: int
    action: str
    # kw_only=True — можно передать только как именованный аргумент
    timestamp: str = field(default="", kw_only=True)
    source: str = field(default="api", kw_only=True)


# Позиционные аргументы работают для user_id и action
event = UserEvent(42, "login", timestamp="2024-01-01", source="web")
# event = UserEvent(42, "login", "2024-01-01")  # TypeError — timestamp только kw_only
```

Параметр `kw_only=True` можно применить ко всему классу сразу:

```python
@dataclass(kw_only=True)
class Config:
    host: str
    port: int
    debug: bool = False


# Все поля только keyword-only
cfg = Config(host="localhost", port=8080)
# Config("localhost", 8080)  # TypeError
```

`kw_only=True` особенно важен при наследовании dataclass — о чём подробнее в следующем уроке. Главная проблема без него: если дочерний класс добавляет обязательное поле, а родительский класс уже имеет необязательные поля — возникает конфликт «поле без дефолта идёт после поля с дефолтом». `kw_only` снимает это ограничение.

---

## `metadata`: произвольные метаданные поля

Параметр `metadata` позволяет прикрепить к полю любую дополнительную информацию — она не влияет на поведение dataclass, но доступна через `fields()`:

```python
from dataclasses import dataclass, field, fields


@dataclass
class UserForm:
    """
    Форма пользователя с метаданными для валидации и документации.
    Метаданные не влияют на __init__, __repr__, __eq__ —
    они просто хранятся и доступны через fields().
    """
    username: str = field(
        metadata={
            "label": "Имя пользователя",
            "min_length": 3,
            "max_length": 50,
            "pattern": r"^[a-zA-Z0-9_]+$",
            "description": "Только буквы, цифры и подчёркивание",
        }
    )
    email: str = field(
        metadata={
            "label": "Email",
            "format": "email",
            "description": "Используется для входа",
        }
    )
    age: int = field(
        metadata={
            "label": "Возраст",
            "min_value": 0,
            "max_value": 150,
            "required": False,
        }
    )
    password: str = field(
        repr=False,
        metadata={
            "label": "Пароль",
            "min_length": 8,
            "write_only": True,  # не возвращать в API-ответе
        }
    )


# Доступ к метаданным через fields()
for f in fields(UserForm):
    meta = f.metadata
    if meta:
        print(f"Поле '{f.name}': {meta.get('label', f.name)}")
        if "min_length" in meta:
            print(f"  Минимальная длина: {meta['min_length']}")
        if "format" in meta:
            print(f"  Формат: {meta['format']}")
```

Обратите внимание: `metadata` — это `MappingProxyType` (иммутабельный словарь). Передайте обычный dict, Python завернёт его в прокси.

---

## `metadata` для системы валидации

Практическое применение `metadata` — встроенная система валидации. Валидаторы хранятся прямо в описании полей, а функция валидации читает их через `fields()`:

```python
from dataclasses import dataclass, field, fields
from typing import Any, Callable


def min_length(n: int) -> Callable[[str], bool]:
    return lambda v: len(v) >= n


def max_length(n: int) -> Callable[[str], bool]:
    return lambda v: len(v) <= n


def min_value(n: int | float) -> Callable[[int | float], bool]:
    return lambda v: v >= n


def max_value(n: int | float) -> Callable[[int | float], bool]:
    return lambda v: v <= n


def is_email(v: str) -> bool:
    return "@" in v and "." in v.split("@")[-1]


@dataclass
class RegisterRequest:
    username: str = field(
        metadata={"validators": [
            (min_length(3), "username: минимум 3 символа"),
            (max_length(50), "username: максимум 50 символов"),
        ]}
    )
    email: str = field(
        metadata={"validators": [
            (is_email, "email: некорректный формат"),
        ]}
    )
    age: int = field(
        default=0,
        metadata={"validators": [
            (min_value(0), "age: должен быть >= 0"),
            (max_value(150), "age: должен быть <= 150"),
        ]}
    )


def validate_dataclass(obj: Any) -> dict[str, list[str]]:
    """
    Валидирует объект dataclass по правилам из metadata.
    Возвращает словарь {поле: список_ошибок}.
    """
    errors: dict[str, list[str]] = {}

    for f in fields(obj):
        validators = f.metadata.get("validators", [])
        value = getattr(obj, f.name)
        field_errors: list[str] = []

        for validator_fn, error_msg in validators:
            try:
                if not validator_fn(value):
                    field_errors.append(error_msg)
            except Exception as e:
                field_errors.append(f"{f.name}: ошибка валидации ({e})")

        if field_errors:
            errors[f.name] = field_errors

    return errors


# Тест
valid = RegisterRequest("alice_123", "alice@example.com", 28)
invalid = RegisterRequest("ab", "not-an-email", 200)

print("Валидный объект:", validate_dataclass(valid))
# Валидный объект: {}

print("Невалидный объект:", validate_dataclass(invalid))
# {'username': ['username: минимум 3 символа'],
#  'email': ['email: некорректный формат'],
#  'age': ['age: должен быть <= 150']}
```

---

## `InitVar`: параметры только для `__init__`

`InitVar[T]` — один из самых мощных инструментов dataclass, и при этом один из наименее известных.

Проблема: иногда нужно передать что-то в конструктор, использовать это при инициализации, но не сохранять в объекте. Например, пароль — мы берём его при создании, вычисляем хеш и сохраняем только хеш.

Без `InitVar` это выглядит так:

```python
@dataclass
class UserWithoutInitVar:
    username: str
    email: str
    password: str   # проблема: пароль хранится в объекте!

    def __post_init__(self) -> None:
        self._password_hash = hash(self.password)
        del self.password   # некрасиво и хрупко
```

С `InitVar`:

```python
from dataclasses import dataclass, field
from dataclasses import InitVar
import hashlib


@dataclass
class User:
    """
    Пользователь. Пароль передаётся при создании, но не хранится.
    Хранится только хеш пароля.
    """
    username: str
    email: str
    # InitVar — передаётся в __init__ и __post_init__, но НЕ становится атрибутом
    password: InitVar[str]

    # Это обычное поле с init=False — не передаётся в конструктор
    password_hash: str = field(init=False, repr=False)

    def __post_init__(self, password: str) -> None:
        # password передаётся как аргумент __post_init__ (не self.password!)
        if len(password) < 8:
            raise ValueError("Пароль слишком короткий (минимум 8 символов)")
        self.password_hash = hashlib.sha256(password.encode()).hexdigest()

    def check_password(self, password: str) -> bool:
        return self.password_hash == hashlib.sha256(password.encode()).hexdigest()


user = User("alice", "alice@example.com", "secure123")

print(user)
# User(username='alice', email='alice@example.com')
# password нет в __repr__! (repr=False для password_hash, InitVar вообще не поле)

print(user.check_password("secure123"))   # True
print(user.check_password("wrong"))       # False

# password не сохранился в объекте
try:
    print(user.password)
except AttributeError as e:
    print(e)   # 'User' object has no attribute 'password'
```

Ключевые моменты `InitVar`:
1. Объявляется как `field_name: InitVar[type]` (без `= field(...)`)
2. Генерируется параметр `__init__`
3. Передаётся в `__post_init__` как позиционный аргумент (в порядке объявления)
4. **НЕ** становится атрибутом объекта
5. Не попадает в `__repr__`, `__eq__`, `__hash__`

---

## `InitVar` для нескольких параметров инициализации

Можно использовать несколько `InitVar` одновременно:

```python
from dataclasses import dataclass, field, InitVar
import datetime


@dataclass
class APISession:
    """
    Сессия API. Создаётся из сырых данных, хранит обработанные.
    """
    user_id: int
    # raw_token — передаём токен, сохраняем только его хеш и префикс
    raw_token: InitVar[str]
    # expires_seconds — передаём время жизни, сохраняем дату истечения
    expires_seconds: InitVar[int] = 3600

    # Поля объекта (не InitVar)
    token_prefix: str = field(init=False)
    token_hash: str = field(init=False, repr=False)
    expires_at: datetime.datetime = field(init=False)
    created_at: datetime.datetime = field(
        init=False,
        default_factory=datetime.datetime.now
    )

    def __post_init__(self, raw_token: str, expires_seconds: int) -> None:
        # Оба InitVar приходят как аргументы в порядке объявления
        import hashlib
        self.token_prefix = raw_token[:8] + "..."
        self.token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        self.expires_at = datetime.datetime.now() + datetime.timedelta(seconds=expires_seconds)

    @property
    def is_expired(self) -> bool:
        return datetime.datetime.now() > self.expires_at


session = APISession(
    user_id=42,
    raw_token="Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
    expires_seconds=7200
)

print(session)
# APISession(user_id=42, token_prefix='Bearer e...',
#            expires_at=datetime.datetime(...), created_at=datetime.datetime(...))
# raw_token не сохранился!

print(f"Истёк: {session.is_expired}")   # False — только что создан
```

---

## `dataclasses.replace()`: создание изменённых копий

Функция `replace(obj, **changes)` создаёт новую копию dataclass с изменёнными значениями полей. Это особенно важно для `frozen=True` объектов — ведь их нельзя изменить напрямую:

```python
from dataclasses import dataclass, replace
import datetime


@dataclass(frozen=True)
class OrderStatus:
    """Статус заказа. Иммутабелен — каждое изменение создаёт новый объект."""
    order_id: int
    status: str
    updated_at: datetime.datetime = datetime.datetime.now()
    notes: str = ""


# Создаём начальный статус
initial = OrderStatus(order_id=1001, status="pending")
print(initial)

# "Изменяем" через replace — создаётся НОВЫЙ объект
confirmed = replace(initial, status="confirmed", notes="Оплата прошла")
print(confirmed)

shipped = replace(confirmed, status="shipped")
print(shipped)

# Исходный объект не изменился!
print(f"initial.status = {initial.status}")   # pending — не изменился
print(initial is confirmed)   # False — разные объекты
print(confirmed is shipped)   # False — разные объекты
```

`replace()` работает так: берёт все текущие значения полей объекта, заменяет указанные в `**changes`, и вызывает `__init__` с получившимися значениями. Это значит:
- Запускается `__post_init__` (если есть)
- Проходит валидация
- Если передать неправильный тип — ошибка (как при обычном создании)

### `replace()` и `InitVar`

Важный нюанс: `InitVar`-поля в `replace()` не передаются — они не являются атрибутами объекта:

```python
@dataclass(frozen=True)
class HashedConfig:
    name: str
    raw_secret: InitVar[str]
    secret_hash: str = field(init=False, default="")

    def __post_init__(self, raw_secret: str) -> None:
        object.__setattr__(self, "secret_hash", hash(raw_secret))


config = HashedConfig("app", "my-secret")

# replace() не знает о raw_secret — нельзя передать через replace
# Если __post_init__ нужен raw_secret, это проблема
new_config = replace(config, name="new-app")
# __post_init__ снова вызовется, но raw_secret не передаётся — ошибка!
```

Это ограничение важно учитывать при проектировании: если `__post_init__` использует `InitVar`, `replace()` будет работать корректно только если `__post_init__` не зависит от `InitVar` в части, которая меняется.

---

## `__post_init__` при `frozen=True`

Распространённая ловушка: в `frozen=True` dataclass нельзя присваивать атрибуты напрямую — даже в `__post_init__`. Ведь `frozen=True` переопределяет `__setattr__`:

```python
from dataclasses import dataclass, field


@dataclass(frozen=True)
class BrokenPoint:
    x: float
    y: float
    magnitude: float = field(init=False)

    def __post_init__(self) -> None:
        import math
        self.magnitude = math.sqrt(self.x**2 + self.y**2)   # FrozenInstanceError!


# @dataclass(frozen=True) перехватывает __setattr__
# Даже __post_init__ не может изменять атрибуты обычным способом
```

Правильное решение — использовать `object.__setattr__` напрямую:

```python
from dataclasses import dataclass, field
import math


@dataclass(frozen=True)
class Vector:
    x: float
    y: float
    # Вычисляемое поле с init=False
    magnitude: float = field(init=False, default=0.0)

    def __post_init__(self) -> None:
        # object.__setattr__ обходит замороженность
        # Это допустимо ТОЛЬКО в __post_init__ при инициализации
        object.__setattr__(self, "magnitude", math.sqrt(self.x**2 + self.y**2))


v = Vector(3.0, 4.0)
print(v.magnitude)   # 5.0

try:
    v.magnitude = 10.0   # FrozenInstanceError — после инициализации нельзя
except Exception as e:
    print(type(e).__name__, e)
```

Паттерн `object.__setattr__(self, field_name, value)` — стандартный способ инициализировать поля в `__post_init__` для `frozen=True` dataclass.

---

## `@dataclass(slots=True)`: оптимизация памяти

Python 3.10 добавил параметр `slots=True`, который автоматически добавляет `__slots__` ко всем полям dataclass:

```python
import sys
from dataclasses import dataclass


@dataclass
class PointNoSlots:
    x: float
    y: float
    z: float


@dataclass(slots=True)
class PointWithSlots:
    x: float
    y: float
    z: float


p1 = PointNoSlots(1.0, 2.0, 3.0)
p2 = PointWithSlots(1.0, 2.0, 3.0)

print(f"Без slots: {sys.getsizeof(p1)} байт (+ {sys.getsizeof(p1.__dict__)} для __dict__)")
print(f"С slots:   {sys.getsizeof(p2)} байт (нет __dict__)")

# Типичный вывод:
# Без slots: 48 байт (+ 232 для __dict__)
# С slots:   56 байт (нет __dict__)
```

### `slots=True` и `frozen=True` вместе

```python
@dataclass(slots=True, frozen=True)
class Coordinate:
    latitude: float
    longitude: float
    altitude: float = 0.0


coord = Coordinate(55.75, 37.62)
print(coord)   # Coordinate(latitude=55.75, longitude=37.62, altitude=0.0)

# Иммутабелен
try:
    coord.latitude = 0.0
except Exception as e:
    print(type(e).__name__)

# Хешируем (frozen=True)
print(hash(coord))

# Экономит память (slots=True)
try:
    coord.__dict__
except AttributeError:
    print("Нет __dict__")
```

### `slots=True` и `ClassVar`

При использовании `slots=True` все аннотированные поля становятся слотами. `ClassVar`-поля исключаются из слотов (они атрибуты класса, не экземпляра):

```python
from typing import ClassVar


@dataclass(slots=True)
class Config:
    host: str
    port: int
    DEBUG: ClassVar[bool] = False   # атрибут класса — не слот

config = Config("localhost", 8080)
print(Config.DEBUG)   # False
# config.extra = "test"  # AttributeError — нет __dict__
```

### Ограничение `slots=True` при наследовании

Если родительский класс без `slots=True`, дочерний с `slots=True` создаёт дополнительные слоты, но `__dict__` родителя сохраняется — полной экономии нет. Для максимальной эффективности все классы в иерархии должны использовать `slots=True`.

---

## Полный разбор `__hash__` в dataclass

Логика генерации `__hash__` в dataclass — один из самых запутанных аспектов. Разберём полную таблицу:

| `eq` | `frozen` | `unsafe_hash` | Результат |
|------|---------|---------------|-----------|
| False | False | False | `__hash__` от `object` (по id) |
| True | False | False | `__hash__ = None` (нехешируемый!) |
| True | True | False | `__hash__` генерируется автоматически |
| True | False | True | `__hash__` генерируется (небезопасно!) |
| False | True | False | `__hash__` генерируется |

Почему при `eq=True` и `frozen=False` Python устанавливает `__hash__ = None`? Потому что это опасно: если объект изменится после добавления в словарь, его хеш изменится, и словарь сломается. Python защищает от этого явно.

Три безопасных способа сделать dataclass хешируемым:

```python
# Способ 1: frozen=True — рекомендуется для Value Objects
@dataclass(frozen=True)
class ImmutablePoint:
    x: float
    y: float


# Способ 2: eq=False — тогда __hash__ от object (по id)
# Используйте только если не нужно равенство по значениям
@dataclass(eq=False)
class UniqueObject:
    name: str
    # hash по id, не по значению


# Способ 3: unsafe_hash=True — не рекомендуется
# Используйте только если знаете, что объект не изменится пока он в словаре
@dataclass(unsafe_hash=True)
class DangerouslyHashable:
    key: str   # если key изменится после добавления в dict — dict сломается
```

Практический совет: если объекту нужен `__hash__` — используйте `frozen=True`. Точка.

---

## `dataclasses.fields()` и программный доступ к полям

Функция `fields()` возвращает кортеж объектов `Field` — по одному для каждого поля dataclass:

```python
from dataclasses import dataclass, field, fields, Field


@dataclass
class Product:
    id: int
    name: str
    price: float = field(metadata={"currency": "RUB", "display": True})
    stock: int = field(default=0, metadata={"display": False})
    category: str = "general"


# Итерация по полям
for f in fields(Product):
    print(f"Поле: {f.name}")
    print(f"  Тип: {f.type}")
    print(f"  default: {f.default}")
    print(f"  init: {f.init}, repr: {f.repr}, compare: {f.compare}")
    print(f"  metadata: {dict(f.metadata)}")
    print()
```

Практическое применение — автоматическое создание схем:

```python
def generate_openapi_schema(cls) -> dict:
    """Генерирует упрощённую схему OpenAPI из dataclass."""
    schema = {
        "type": "object",
        "properties": {},
        "required": [],
    }

    for f in fields(cls):
        # Определяем тип для OpenAPI
        type_map = {int: "integer", float: "number", str: "string", bool: "boolean"}
        openapi_type = type_map.get(f.type, "string")

        prop: dict = {"type": openapi_type}

        # Добавляем информацию из metadata
        if f.metadata:
            if "description" in f.metadata:
                prop["description"] = f.metadata["description"]
            if "min_length" in f.metadata:
                prop["minLength"] = f.metadata["min_length"]

        schema["properties"][f.name] = prop

        # Обязательное поле — нет дефолта и не init=False
        from dataclasses import MISSING
        if f.default is MISSING and f.default_factory is MISSING and f.init:
            schema["required"].append(f.name)

    return schema


@dataclass
class CreateProductRequest:
    name: str = field(metadata={"description": "Название товара"})
    price: float = field(metadata={"description": "Цена в рублях"})
    category: str = field(default="general")
    description: str = field(default="", metadata={"description": "Описание"})


import json
schema = generate_openapi_schema(CreateProductRequest)
print(json.dumps(schema, ensure_ascii=False, indent=2))
```

---

## `make_dataclass()`: динамическое создание

`make_dataclass()` создаёт dataclass-класс динамически — аналог `type()` для обычных классов:

```python
from dataclasses import make_dataclass, field


# Создание простого dataclass
Point = make_dataclass("Point", ["x", "y"])
p = Point(1, 2)
print(p)   # Point(x=1, y=2)

# С типами
TypedPoint = make_dataclass(
    "TypedPoint",
    [("x", float), ("y", float)]
)
tp = TypedPoint(1.5, 2.5)
print(tp)   # TypedPoint(x=1.5, y=2.5)

# С значениями по умолчанию
UserDTO = make_dataclass(
    "UserDTO",
    [
        ("id", int),
        ("username", str),
        ("email", str),
        ("is_active", bool, field(default=True)),
        ("roles", list, field(default_factory=list)),
    ]
)

user = UserDTO(1, "alice", "alice@example.com")
print(user)   # UserDTO(id=1, username='alice', email='alice@example.com', is_active=True, roles=[])
```

Практическое применение — создание DTO из конфигурационного файла или схемы API:

```python
def create_dto_from_schema(schema_name: str, schema: dict) -> type:
    """Создаёт dataclass из JSON-схемы."""
    type_map = {
        "string": str,
        "integer": int,
        "number": float,
        "boolean": bool,
        "array": list,
        "object": dict,
    }

    fields_spec = []
    for field_name, field_info in schema.items():
        python_type = type_map.get(field_info["type"], str)
        if field_info.get("required", True):
            fields_spec.append((field_name, python_type))
        else:
            default = field_info.get("default")
            if default is None:
                fields_spec.append(
                    (field_name, python_type, field(default=None))
                )
            else:
                fields_spec.append(
                    (field_name, python_type, field(default=default))
                )

    return make_dataclass(schema_name, fields_spec)


# Схема из API-документации (обычно читается из JSON/YAML)
user_schema = {
    "id": {"type": "integer", "required": True},
    "username": {"type": "string", "required": True},
    "email": {"type": "string", "required": True},
    "age": {"type": "integer", "required": False, "default": None},
}

UserSchema = create_dto_from_schema("UserSchema", user_schema)
user = UserSchema(id=1, username="alice", email="alice@example.com")
print(user)   # UserSchema(id=1, username='alice', email='alice@example.com', age=None)
```

---

## Практический пример: ORM-подобная модель

Соберём всё изученное в один полноценный пример — ORM-подобный класс, использующий все возможности dataclass:

```python
from __future__ import annotations
from dataclasses import dataclass, field, fields, InitVar, replace
from typing import ClassVar, Any
import hashlib
import datetime


def not_empty(v: str) -> bool:
    return bool(v and v.strip())

def valid_email(v: str) -> bool:
    return "@" in v and "." in v.split("@")[-1]

def min_len(n: int):
    return lambda v: len(str(v)) >= n


@dataclass
class BaseModel:
    """
    Базовый класс для ORM-подобных моделей.
    Содержит общие поля и логику.
    """
    # ClassVar — атрибут класса, хранит имя таблицы
    __tablename__: ClassVar[str] = ""
    __indexes__: ClassVar[list[str]] = []

    id: int = field(init=False, default=0)
    created_at: datetime.datetime = field(
        init=False,
        default_factory=datetime.datetime.now,
        compare=False,
        repr=False,
    )
    updated_at: datetime.datetime = field(
        init=False,
        default_factory=datetime.datetime.now,
        compare=False,
        repr=False,
    )

    def touch(self) -> None:
        """Обновляет временную метку updated_at."""
        self.updated_at = datetime.datetime.now()

    def to_dict(self) -> dict[str, Any]:
        """Конвертирует в словарь для сохранения."""
        result: dict[str, Any] = {}
        for f in fields(self):
            if f.init is False and f.name in ("id", "created_at", "updated_at"):
                result[f.name] = getattr(self, f.name)
            elif f.metadata.get("db_column", True):  # включать ли в БД
                result[f.name] = getattr(self, f.name)
        return result

    @classmethod
    def validate(cls, obj: Any) -> dict[str, list[str]]:
        """Валидирует объект по правилам из metadata."""
        errors: dict[str, list[str]] = {}
        for f in fields(obj):
            validators = f.metadata.get("validators", [])
            value = getattr(obj, f.name)
            field_errors = []
            for fn, msg in validators:
                try:
                    if not fn(value):
                        field_errors.append(msg)
                except Exception:
                    field_errors.append(f"{f.name}: ошибка валидации")
            if field_errors:
                errors[f.name] = field_errors
        return errors


@dataclass
class UserModel(BaseModel):
    """
    Модель пользователя.
    Демонстрирует: InitVar, metadata, ClassVar, field(init=False).
    """
    __tablename__: ClassVar[str] = "users"
    __indexes__: ClassVar[list[str]] = ["username", "email"]

    username: str = field(
        metadata={
            "validators": [
                (not_empty, "username: не может быть пустым"),
                (min_len(3), "username: минимум 3 символа"),
            ],
            "db_column": True,
        }
    )
    email: str = field(
        metadata={
            "validators": [
                (valid_email, "email: некорректный формат"),
            ],
            "db_column": True,
        }
    )

    # InitVar — пароль передаётся при создании, но не сохраняется
    password: InitVar[str | None] = None

    # Результат обработки пароля — сохраняется
    password_hash: str = field(
        init=False,
        default="",
        repr=False,
        metadata={"db_column": True},
    )

    is_active: bool = field(
        default=True,
        metadata={"db_column": True},
    )
    roles: list[str] = field(
        default_factory=list,
        metadata={"db_column": True},
    )

    def __post_init__(self, password: str | None) -> None:
        if password is not None:
            if len(password) < 8:
                raise ValueError("Пароль слишком короткий (минимум 8 символов)")
            self.password_hash = hashlib.sha256(password.encode()).hexdigest()

    def check_password(self, password: str) -> bool:
        if not self.password_hash:
            return False
        return self.password_hash == hashlib.sha256(password.encode()).hexdigest()

    def set_password(self, new_password: str) -> None:
        if len(new_password) < 8:
            raise ValueError("Пароль слишком короткий")
        self.password_hash = hashlib.sha256(new_password.encode()).hexdigest()
        self.touch()

    def deactivate(self) -> None:
        self.is_active = False
        self.touch()


@dataclass
class ProductModel(BaseModel):
    """Модель продукта."""
    __tablename__: ClassVar[str] = "products"

    name: str = field(
        metadata={"validators": [(not_empty, "name: не может быть пустым")]}
    )
    price: float = field(
        metadata={"validators": [(lambda v: v >= 0, "price: не может быть отрицательной")]}
    )
    category: str = "general"
    stock_count: int = field(default=0, metadata={"db_column": True})


# ─── Демонстрация ────────────────────────────────────────────────────────────

print("=== Создание пользователя ===")
user = UserModel(
    username="alice",
    email="alice@example.com",
    password="secure123",
    roles=["admin"],
)
print(user)
print(f"Пароль прошёл проверку: {user.check_password('secure123')}")
print(f"Неверный пароль: {user.check_password('wrong')}")

print("\n=== Валидация ===")
valid_errors = BaseModel.validate(user)
print(f"Ошибки валидации: {valid_errors}")   # {}

bad_user = UserModel(username="ab", email="not-email")
bad_errors = BaseModel.validate(bad_user)
print(f"Ошибки невалидного: {bad_errors}")

print("\n=== Сохранение и update ===")
user_dict = user.to_dict()
print(f"Словарь для БД: {list(user_dict.keys())}")
# password не попадает (InitVar), password_hash попадает

print(f"\nТаблица: {UserModel.__tablename__}")
print(f"Индексы: {UserModel.__indexes__}")

print("\n=== Продукт ===")
product = ProductModel(name="Ноутбук", price=89990.0, stock_count=15)
print(product)

product_errors = BaseModel.validate(product)
print(f"Ошибки продукта: {product_errors}")   # {}

bad_product = ProductModel(name="", price=-100.0)
bad_product_errors = BaseModel.validate(bad_product)
print(f"Ошибки плохого продукта: {bad_product_errors}")
```

---

## `dataclasses.replace()` на практике: immutable workflow

Паттерн работы с иммутабельными dataclass через `replace()` — чистый и предсказуемый способ управлять состоянием:

```python
from dataclasses import dataclass, field, replace
import datetime


@dataclass(frozen=True)
class OrderState:
    """Иммутабельное состояние заказа. История хранится снаружи."""
    order_id: int
    status: str
    items: tuple[dict, ...]    # кортеж вместо списка (hashable)
    total: float
    user_id: int
    notes: str = ""
    updated_at: str = field(
        default_factory=lambda: datetime.datetime.now().isoformat()
    )

    VALID_TRANSITIONS: frozenset = frozenset({
        ("pending", "confirmed"),
        ("confirmed", "processing"),
        ("processing", "shipped"),
        ("shipped", "delivered"),
        ("pending", "cancelled"),
        ("confirmed", "cancelled"),
    })

    def transition_to(self, new_status: str, notes: str = "") -> "OrderState":
        """Переводит заказ в новый статус, возвращая новое состояние."""
        if (self.status, new_status) not in self.VALID_TRANSITIONS:
            raise ValueError(
                f"Недопустимый переход: {self.status!r} → {new_status!r}"
            )
        return replace(
            self,
            status=new_status,
            notes=notes,
            updated_at=datetime.datetime.now().isoformat(),
        )


# История состояний
order = OrderState(
    order_id=1001,
    status="pending",
    items=({"product_id": 1, "qty": 2},),
    total=3000.0,
    user_id=42,
)

# Каждый переход создаёт новый объект — можно хранить историю
history = [order]

confirmed = order.transition_to("confirmed", "Оплата подтверждена")
history.append(confirmed)

processing = confirmed.transition_to("processing")
history.append(processing)

shipped = processing.transition_to("shipped", "Передан в доставку")
history.append(shipped)

# Вывод истории
for state in history:
    print(f"{state.status}: {state.notes or '—'} @ {state.updated_at[:19]}")

# Недопустимый переход
try:
    order.transition_to("delivered")
except ValueError as e:
    print(f"\nОшибка: {e}")
```

---

## Неочевидные моменты и типичные ошибки

**`InitVar` vs `field(init=False)` — чёткая разница.**

```python
# InitVar: параметр __init__, но НЕ атрибут объекта
raw_data: InitVar[str]    # передаём → используем → забываем

# field(init=False): атрибут объекта, НЕ параметр __init__
computed: str = field(init=False)   # не передаём → вычисляем в __post_init__
```

**`@dataclass` не перегенерирует `__init__` если он уже есть.** Если в теле класса объявлен `__init__`, декоратор не создаёт свой (если `init=True` — генерирует только если нет):

```python
@dataclass
class Tricky:
    x: int

    def __init__(self, x: int, y: int) -> None:   # пользовательский __init__
        self.x = x
        self.y = y   # y — не поле dataclass!

# Декоратор не перегенерирует __init__ — он уже есть
t = Tricky(1, 2)
print(t)   # Tricky(x=1) — y не в __repr__, он не поле dataclass
```

**`dataclass` и `copy`/`pickle`.** Dataclass прекрасно работает с `copy.copy()`, `copy.deepcopy()` и `pickle` — не нужно добавлять `__getstate__`/`__setstate__` (в отличие от `__slots__` без dataclass).

**`replace()` всегда вызывает `__init__`.** Это означает, что `__post_init__` тоже вызывается. Если валидация в `__post_init__` — значит, `replace()` тоже валидирует. Это хорошо!

---

## Итоги урока

`field()` принимает параметры `hash`, `kw_only` и `metadata` — последние два особенно полезны для расширенных сценариев. `metadata` хранит произвольную информацию о поле, доступную через `fields()`, и используется для систем валидации, генерации схем и ORM.

`InitVar[T]` — поле, которое передаётся в `__init__` и `__post_init__`, но не сохраняется в объекте. Идеально для паттерна «обработать при создании, не хранить»: пароли, токены, сырые данные.

В `frozen=True` dataclass нельзя присваивать атрибуты даже в `__post_init__` — нужен `object.__setattr__`.

`replace(obj, **changes)` создаёт копию с изменёнными полями — единственный способ «изменить» замороженный объект.

`slots=True` (Python 3.10+) автоматически добавляет `__slots__` — экономия памяти без ручного объявления.

`make_dataclass()` создаёт dataclass-класс динамически — для генерации схем из конфигурации или API-документации.

В следующем уроке мы рассмотрим наследование dataclass — включая `kw_only` для решения проблем с порядком полей и взаимодействие с обычными классами.

---

## Вопросы

1. Чем `InitVar[T]` принципиально отличается от `field(init=False)`? В каком сценарии нужен каждый из них?
2. Как в `__post_init__` при `frozen=True` dataclass правильно устанавливать значения вычисляемых полей?
3. Что делает `dataclasses.replace()` под капотом? Почему `replace()` проходит валидацию так же, как `__init__`?
4. Когда следует использовать параметр `hash` в `field()` отдельно от `compare`? Приведите конкретный пример.
5. Для чего используется `field(metadata={...})`? Влияет ли metadata на поведение dataclass?
6. Что такое `kw_only=True` для поля? В каком сценарии это критически важно?
7. В чём преимущество `@dataclass(slots=True)` перед ручным объявлением `__slots__`?
8. Почему dataclass с `eq=True` (по умолчанию) и `frozen=False` нехешируем? Как сделать его хешируемым тремя разными способами?

---

## Задачи

### **Задача 1**. 

`InitVar` для обработки данных при создании

Создайте dataclass `JWTToken` для хранения обработанного JWT-токена. Поля объекта: `user_id: int`, `username: str`, `roles: tuple[str, ...]`, `expires_at: datetime.datetime`, `token_prefix: str` (первые 10 символов токена). В конструктор передаётся `raw_token: InitVar[str]` и `secret: InitVar[str]`.

В `__post_init__`: распарсить `raw_token` (имитируйте парсинг: разбейте по `.`, возьмите части как `user_id`, `username`, `roles` — через простое соглашение, например `"1.alice.admin,user"`). Проверить, что `secret` не пустой. Установить `token_prefix`. Сделайте объект `frozen=True`.

**Пример использования**:

```python
token = JWTToken(
    raw_token="1.alice.admin,user.2024-12-31",
    secret="my-secret-key",
)

print(token.user_id)      # 1
print(token.username)     # alice
print(token.roles)        # ('admin', 'user')
print(token.token_prefix) # 1.alice.ad

# frozen — нельзя изменить
try:
    token.user_id = 2
except Exception as e:
    print(type(e).__name__)

# InitVar не сохранился
try:
    token.raw_token
except AttributeError:
    print("raw_token не сохранился")
```

---

### **Задача 2**. 

Система метаданных для OpenAPI

Создайте dataclass `APIField` с `metadata`, описывающим поле для OpenAPI-схемы. Затем создайте dataclass `CreateOrderRequest` с полями `user_id`, `items`, `promo_code`, `notes`, где каждое поле аннотировано через `metadata` с ключами: `openapi_type`, `description`, `required`, `example`, и опционально `min_value`, `max_items`.

Напишите функцию `generate_openapi_properties(cls) -> dict`, которая читает `metadata` через `fields()` и генерирует словарь свойств в формате OpenAPI.

**Пример использования**:

```python
schema = generate_openapi_properties(CreateOrderRequest)
import json
print(json.dumps(schema, ensure_ascii=False, indent=2))
# {
#   "user_id": {"type": "integer", "description": "...", "example": 42},
#   "items": {"type": "array", "description": "...", "maxItems": 100},
#   ...
# }
```

---

### **Задача 3**. 

Иммутабельный workflow с `replace()`

Создайте систему управления состоянием HTTP-запроса через иммутабельный dataclass. `@dataclass(frozen=True)` класс `RequestContext` с полями: `request_id: str`, `method: str`, `path: str`, `headers: dict` (используйте `frozenset` пар или просто `dict` — `frozen` не делает содержимое неизменяемым), `user_id: int | None = None`, `authenticated: bool = False`, `rate_limit_remaining: int = 100`, `start_time: float = field(default_factory=time.time, compare=False)`.

Напишите функцию-pipeline, которая создаёт начальный контекст и через `replace()` проходит через несколько стадий обработки: `authenticate(ctx, token) -> RequestContext`, `check_rate_limit(ctx) -> RequestContext`, `log_request(ctx) -> RequestContext`. Каждая функция возвращает новый контекст.

**Пример использования**:

```python
# Pipeline
initial = RequestContext(
    request_id="req-001",
    method="GET",
    path="/api/orders",
)

ctx = authenticate(initial, "valid-token-42")
ctx = check_rate_limit(ctx)
ctx = log_request(ctx)

print(f"user_id: {ctx.user_id}")
print(f"authenticated: {ctx.authenticated}")
print(f"rate_limit_remaining: {ctx.rate_limit_remaining}")
print("\nЛог:")
for entry in ctx.log_entries:
    print(f"  - {entry}")

# Начальный контекст не изменился
print(f"\nИсходный user_id: {initial.user_id}")   # None
```

---

### **Задача 4**. 

Динамическое создание DTO через `make_dataclass`

Напишите функцию `create_response_dto(name, fields_spec)`, которая принимает имя класса и спецификацию полей в виде списка словарей `{"name": str, "type": str, "required": bool, "default": any}` и создаёт dataclass через `make_dataclass`. Типы передаются как строки (`"str"`, `"int"`, `"float"`, `"bool"`, `"list"`, `"dict"`).

Созданный класс должен: иметь все указанные поля, иметь метод `to_dict() -> dict` (добавьте его через namespace), быть `frozen=True`.

**Пример использования**:

```python
UserDTO = create_response_dto("UserDTO", [
    {"name": "id", "type": "int", "required": True},
    {"name": "username", "type": "str", "required": True},
    {"name": "email", "type": "str", "required": True},
    {"name": "is_active", "type": "bool", "required": False, "default": True},
])

user = UserDTO(id=1, username="alice", email="alice@example.com")
print(user)
print(user.to_dict())
# {'id': 1, 'username': 'alice', 'email': 'alice@example.com', 'is_active': True}

# Создаём другой DTO из той же функции
ProductDTO = create_response_dto("ProductDTO", [
    {"name": "id", "type": "int", "required": True},
    {"name": "name", "type": "str", "required": True},
    {"name": "price", "type": "float", "required": True},
    {"name": "in_stock", "type": "bool", "required": False, "default": True},
])

product = ProductDTO(id=42, name="Ноутбук", price=89990.0)
print(product)
print(product.to_dict())
```

---

### **Задача 5**. 

Полная система конфигурации с валидацией

Создайте систему конфигурации приложения, используя все изученные инструменты. Dataclass `DatabaseConfig` с полями `host`, `port`, `database`, `InitVar` для `password` (сохраняем только маскированную версию), поле `masked_password: str = field(init=False)`. `DatabaseConfig` должен быть `frozen=True`.

Dataclass `AppConfig` с полями `app_name`, `debug`, `database: DatabaseConfig`, `allowed_hosts: tuple[str, ...]`, `max_connections: int`. В `metadata` каждого поля хранятся валидаторы. Напишите функцию `load_config(config_dict) -> AppConfig`, которая создаёт конфигурацию из словаря и валидирует её через `metadata`.

**Пример использования**:

```python
config_data = {
    "app_name": "MyWebApp",
    "debug": False,
    "database": {
        "host": "db.example.com",
        "port": 5432,
        "database": "production",
        "password": "super-secret-password",
    },
    "allowed_hosts": ["mywebapp.com", "www.mywebapp.com"],
    "max_connections": 50,
}

config = load_config(config_data)
print(config.app_name)
print(config.database.host)
print(config.database.masked_password)   # sup***
print(f"Валиден: {not validate_dataclass(config)}")
```

---

[Предыдущий урок](lesson30.md) | [Следующий урок](lesson32.md)