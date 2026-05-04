# Урок 32. Наследование Data Classes и совместимость с обычными классами

---

## Как dataclass наследует поля родителя

В обычном Python-наследовании дочерний класс получает все методы и атрибуты родителя. С dataclass работает та же логика, но с дополнительной механикой: все поля родительского dataclass включаются в автогенерированный `__init__`, `__repr__` и `__eq__` дочернего класса.

Порядок полей строго определён: **сначала поля родителя, затем поля дочернего класса**:

```python
from dataclasses import dataclass, fields


@dataclass
class Base:
    id: int
    name: str


@dataclass
class Child(Base):
    email: str
    is_active: bool = True


# Автогенерированный __init__ Child:
# def __init__(self, id: int, name: str, email: str, is_active: bool = True)
# Сначала поля Base (id, name), затем поля Child (email, is_active)

child = Child(1, "Alice", "alice@example.com")
print(child)
# Child(id=1, name='Alice', email='alice@example.com', is_active=True)

# fields() показывает ВСЕ поля, включая унаследованные
for f in fields(child):
    print(f"  {f.name}: {f.type}")
# id: int
# name: str
# email: str
# is_active: bool
```

Это отличается от обычного Python-наследования: там каждый класс управляет своими атрибутами через `__init__`. Здесь декоратор `@dataclass` читает аннотации всей иерархии классов и строит единый `__init__`.

---

## Проблема порядка полей: главная ловушка

Самая распространённая ошибка при наследовании dataclass — конфликт порядка полей. Правило Python: параметры без значения по умолчанию должны идти перед параметрами со значением. Но при наследовании это правило легко нарушить:

```python
@dataclass
class BaseUser:
    id: int
    username: str
    is_active: bool = True   # поле с дефолтом в родителе


@dataclass
class AdminUser(BaseUser):
    admin_level: int          # обязательное поле в дочернем классе!
    # Ошибка! Порядок в __init__ будет:
    # (id, username, is_active=True, admin_level)  — нарушение!
    # non-default argument 'admin_level' follows default argument
```

```python
try:
    @dataclass
    class AdminUser(BaseUser):
        admin_level: int
except TypeError as e:
    print(e)
# TypeError: non-default argument 'admin_level' follows default argument
```

### Решение 1: `kw_only=True` для всего дочернего класса

```python
@dataclass
class BaseUser:
    id: int
    username: str
    is_active: bool = True


@dataclass(kw_only=True)   # все поля AdminUser — только keyword arguments
class AdminUser(BaseUser):
    admin_level: int       # теперь передаётся по имени — нет конфликта порядка

admin = AdminUser(1, "alice", admin_level=2)
# id и username — позиционные (из BaseUser)
# admin_level — keyword-only (из AdminUser с kw_only=True)

print(admin)
# AdminUser(id=1, username='alice', is_active=True, admin_level=2)
```

### Решение 2: `field(kw_only=True)` для конкретных полей

```python
from dataclasses import field


@dataclass
class AdminUser(BaseUser):
    admin_level: int = field(kw_only=True)   # только это поле keyword-only
    department: str = field(kw_only=True, default="IT")


admin = AdminUser(1, "alice", admin_level=2)
admin2 = AdminUser(1, "bob", admin_level=3, department="Finance")
print(admin2)
```

### Решение 3: Не смешивать обязательные и необязательные поля в иерархии

```python
@dataclass
class BaseUser:
    id: int
    username: str
    # Все поля без дефолта!


@dataclass
class AdminUser(BaseUser):
    admin_level: int        # тоже без дефолта — проблем нет
    is_active: bool = True  # поля с дефолтом — после обязательных
    department: str = "IT"


admin = AdminUser(1, "alice", 2)
print(admin)
# AdminUser(id=1, username='alice', admin_level=2, is_active=True, department='IT')
```

На практике наиболее чистое решение — `kw_only=True` для дочерних классов с дополнительными обязательными полями. Это явно сигнализирует, что поля дочернего класса передаются по имени.

---

## Переопределение полей в дочернем классе

Можно объявить в дочернем классе поле с тем же именем, что и в родительском. Это изменит тип, дефолтное значение или метаданные поля — и переместит его в `__init__`:

```python
@dataclass
class Event:
    timestamp: str = "now"
    source: str = "unknown"
    level: str = "INFO"


@dataclass
class CriticalEvent(Event):
    # Переопределяем level — меняем значение по умолчанию
    level: str = "CRITICAL"
    # Переопределённое поле перемещается в конец!
    # __init__ теперь: (timestamp="now", source="unknown", level="CRITICAL")


e = CriticalEvent()
print(e)
# CriticalEvent(timestamp='now', source='unknown', level='CRITICAL')

e2 = CriticalEvent(timestamp="2024-01-01", source="api")
print(e2)
# CriticalEvent(timestamp='2024-01-01', source='api', level='CRITICAL')
```

Обратите внимание: переопределённое поле `level` перемещается в позицию дочерних полей. Это меняет порядок параметров `__init__`. Используйте переопределение осознанно — только когда нужно изменить дефолтное значение или метаданные, сохранив тип.

---

## `__post_init__` при наследовании

Критически важный момент: `__post_init__` НЕ вызывается по цепочке автоматически. Дочерний `__post_init__` должен явно вызвать `super().__post_init__()`:

```python
from dataclasses import dataclass


@dataclass
class BaseModel:
    id: int
    name: str

    def __post_init__(self) -> None:
        print(f"[BaseModel.__post_init__] id={self.id}")
        if self.id <= 0:
            raise ValueError(f"id должен быть положительным: {self.id}")
        self.name = self.name.strip()


@dataclass
class UserModel(BaseModel):
    email: str

    def __post_init__(self) -> None:
        # ОБЯЗАТЕЛЬНО вызвать super().__post_init__()!
        super().__post_init__()
        print(f"[UserModel.__post_init__] email={self.email}")
        self.email = self.email.lower().strip()
        if "@" not in self.email:
            raise ValueError(f"Некорректный email: {self.email!r}")


@dataclass
class AdminModel(UserModel):
    admin_level: int = field(kw_only=True, default=1)

    def __post_init__(self) -> None:
        super().__post_init__()   # вызывает UserModel.__post_init__ → BaseModel.__post_init__
        print(f"[AdminModel.__post_init__] level={self.admin_level}")
        if not 1 <= self.admin_level <= 3:
            raise ValueError(f"admin_level должен быть 1–3: {self.admin_level}")


from dataclasses import field

# Создаём объект — выполняется вся цепочка __post_init__
admin = AdminModel(1, "  Alice  ", "ALICE@EXAMPLE.COM", admin_level=2)
print(f"\nРезультат: {admin}")
# [BaseModel.__post_init__] id=1
# [UserModel.__post_init__] email=ALICE@EXAMPLE.COM
# [AdminModel.__post_init__] level=2
# Результат: AdminModel(id=1, name='Alice', email='alice@example.com', admin_level=2)
```

Что происходит, если не вызвать `super().__post_init__()`? Вся логика родительского `__post_init__` пропускается:

```python
@dataclass
class BrokenUserModel(BaseModel):
    email: str

    def __post_init__(self) -> None:
        # Забыли super().__post_init__()!
        self.email = self.email.lower()
        # BaseModel.__post_init__ НЕ выполнится:
        # id не валидируется, name не обрезается!


broken = BrokenUserModel(-1, "  bob  ", "BOB@EXAMPLE.COM")
print(broken.id)    # -1 — невалидный, но не проверен!
print(broken.name)  # '  bob  ' — не обрезан!
```

---

## `InitVar` в цепочке `__post_init__`

При использовании `InitVar` в иерархии нужно быть внимательным: дочерний `__post_init__` должен получить `InitVar`-параметры родителя и передать их через `super().__post_init__()`:

```python
from dataclasses import dataclass, InitVar, field


@dataclass
class SecureBase:
    name: str
    api_key: InitVar[str]   # не хранится
    key_prefix: str = field(init=False, default="")

    def __post_init__(self, api_key: str) -> None:
        self.key_prefix = api_key[:4] + "****"
        print(f"[SecureBase] key_prefix={self.key_prefix}")


@dataclass
class SecureService(SecureBase):
    service_url: str
    timeout: int = 30
    # Дочерний класс тоже принимает api_key — он передаётся родителю
    # InitVar объявлять заново НЕ нужно — он уже определён в родителе

    def __post_init__(self, api_key: str) -> None:
        # Передаём api_key в super().__post_init__
        super().__post_init__(api_key)
        print(f"[SecureService] url={self.service_url}")


svc = SecureService(
    name="PaymentService",
    api_key="sk-abc123xyz456",
    service_url="https://payments.example.com",
    timeout=60,
)
print(svc)
# [SecureBase] key_prefix=sk-a****
# [SecureService] url=https://payments.example.com
# SecureService(name='PaymentService', key_prefix='sk-a****',
#               service_url='https://payments.example.com', timeout=60)
```

---

## `frozen` при наследовании: строгие правила

Python строго запрещает смешивать `frozen` и нефроzen dataclass в иерархии:

```python
@dataclass(frozen=True)
class FrozenBase:
    x: int
    y: int


try:
    @dataclass          # нефроzen дочерний — нельзя!
    class UnfrozenChild(FrozenBase):
        z: int
except TypeError as e:
    print(e)
# cannot inherit frozen dataclass from a non-frozen one

try:
    @dataclass(frozen=True)   # frozen дочерний от нефроzen — тоже нельзя!
    class FrozenChildOfUnfrozen(Child):
        z: int
except TypeError as e:
    print(e)
# cannot inherit frozen dataclass from a non-frozen one
```

Оба класса в иерархии должны иметь одинаковое значение `frozen`. Это правило распространяется на всю цепочку наследования:

```python
# Правильно: вся иерархия frozen
@dataclass(frozen=True)
class Point:
    x: float
    y: float


@dataclass(frozen=True)
class ColoredPoint(Point):
    color: str = "red"


@dataclass(frozen=True)
class LabeledColoredPoint(ColoredPoint):
    label: str = ""


# Создаём объект
lcp = LabeledColoredPoint(1.0, 2.0, "blue", "A")
print(lcp)
print(hash(lcp))   # frozen → хешируем
```

---

## Dataclass наследует от обычного класса

Dataclass можно унаследовать от обычного (не-dataclass) класса. Поля и методы обычного класса доступны, но не участвуют в dataclass-механизме:

```python
class Timestamped:
    """Обычный класс с временными метками."""

    def __init__(self) -> None:
        import datetime
        self.created_at = datetime.datetime.now()
        self.updated_at = self.created_at

    def touch(self) -> None:
        import datetime
        self.updated_at = datetime.datetime.now()


@dataclass
class UserRecord(Timestamped):
    """
    Dataclass наследует от обычного класса.
    created_at и updated_at не являются полями dataclass,
    но доступны через обычное наследование.
    """
    id: int
    username: str
    email: str

    def __post_init__(self) -> None:
        # Вызываем __init__ обычного класса явно
        Timestamped.__init__(self)
        self.email = self.email.lower()


user = UserRecord(1, "alice", "ALICE@EXAMPLE.COM")
print(user)
# UserRecord(id=1, username='alice', email='alice@example.com')
# created_at и updated_at не в __repr__ — они не поля dataclass

print(user.created_at)   # datetime — доступно через наследование
user.touch()
print(user.updated_at)   # обновилось
```

**Важный нюанс**: в `__post_init__` необходимо явно вызвать `__init__` обычного родителя. Автогенерированный `__init__` dataclass НЕ вызывает `__init__` обычного родителя — он управляет только полями dataclass.

---

## Обычный класс наследует от dataclass

Обычный класс может наследоваться от dataclass. Он получает все методы (`__init__`, `__repr__`, `__eq__`), но новые поля, добавленные в обычном классе, не участвуют в dataclass-механизме:

```python
@dataclass
class BaseDTO:
    id: int
    created_at: str


class UserDTO(BaseDTO):
    """
    Обычный класс, наследующий от dataclass.
    Добавляет методы, но не новые dataclass-поля.
    """

    def __init__(self, id: int, created_at: str, username: str, email: str) -> None:
        super().__init__(id, created_at)   # вызываем dataclass __init__
        self.username = username           # обычные атрибуты
        self.email = email

    def to_api_response(self) -> dict:
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "created_at": self.created_at,
        }

    def __repr__(self) -> str:
        return f"UserDTO(id={self.id}, username={self.username!r})"


user = UserDTO(1, "2024-01-01", "alice", "alice@example.com")
print(user)
print(user.to_api_response())
```

---

## Dataclass + ABC: формальный контракт с автогенерацией

Один из самых мощных паттернов: сочетание `ABC` и `@dataclass`. ABC определяет контракт (абстрактные методы), dataclass — данные и стандартные методы:

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


class BaseSerializer(ABC):
    """ABC: определяет контракт сериализатора."""

    @abstractmethod
    def serialize(self, data: Any) -> str:
        """Сериализует данные в строку."""
        ...

    @abstractmethod
    def deserialize(self, raw: str) -> Any:
        """Десериализует строку в данные."""
        ...

    @property
    @abstractmethod
    def content_type(self) -> str:
        """MIME-тип формата."""
        ...


@dataclass
class JSONSerializer(BaseSerializer):
    """Dataclass + ABC: данные + контракт + автогенерация методов."""
    indent: int = 2
    ensure_ascii: bool = False
    sort_keys: bool = False

    @property
    def content_type(self) -> str:
        return "application/json"

    def serialize(self, data: Any) -> str:
        import json
        return json.dumps(
            data,
            indent=self.indent,
            ensure_ascii=self.ensure_ascii,
            sort_keys=self.sort_keys,
        )

    def deserialize(self, raw: str) -> Any:
        import json
        return json.loads(raw)


@dataclass
class CSVSerializer(BaseSerializer):
    """Сериализатор CSV с настройками."""
    delimiter: str = ","
    header: bool = True

    @property
    def content_type(self) -> str:
        return "text/csv"

    def serialize(self, data: Any) -> str:
        if not isinstance(data, list) or not data:
            return ""
        if isinstance(data[0], dict):
            headers = list(data[0].keys())
            rows = [self.delimiter.join(headers)] if self.header else []
            for row in data:
                rows.append(self.delimiter.join(str(row.get(h, "")) for h in headers))
            return "\n".join(rows)
        return "\n".join(self.delimiter.join(str(v) for v in row) for row in data)

    def deserialize(self, raw: str) -> list:
        lines = raw.strip().split("\n")
        if not lines:
            return []
        if self.header and len(lines) > 1:
            headers = lines[0].split(self.delimiter)
            return [dict(zip(headers, line.split(self.delimiter))) for line in lines[1:]]
        return [line.split(self.delimiter) for line in lines]


# Полиморфизм: функция принимает BaseSerializer, работает с любой реализацией
def export_data(serializer: BaseSerializer, data: Any) -> dict:
    raw = serializer.serialize(data)
    return {
        "content_type": serializer.content_type,
        "content": raw,
        "size": len(raw),
    }


users = [
    {"id": 1, "name": "Alice", "email": "alice@example.com"},
    {"id": 2, "name": "Bob", "email": "bob@example.com"},
]

json_ser = JSONSerializer(indent=2)
csv_ser = CSVSerializer()
compact_json = JSONSerializer(indent=0, sort_keys=True)

for serializer in [json_ser, csv_ser, compact_json]:
    result = export_data(serializer, users)
    print(f"\n--- {result['content_type']} ({result['size']} байт) ---")
    print(result["content"])

# isinstance проверяет наследование от ABC
print(isinstance(json_ser, BaseSerializer))   # True
print(isinstance(csv_ser, BaseSerializer))    # True

# Нельзя создать BaseSerializer напрямую
try:
    BaseSerializer()
except TypeError as e:
    print(f"\nАбстрактный класс: {e}")
```

---

## Практический пример: полная иерархия DTO

Реализуем корректную иерархию DTO для REST API с решением всех проблем наследования:

```python
from __future__ import annotations
from dataclasses import dataclass, field, fields, asdict
from typing import Any, ClassVar
import datetime


@dataclass
class BaseDTO:
    """
    Базовый DTO. Все поля без дефолтов — проблем с порядком не будет.
    """
    id: int

    def to_dict(self) -> dict[str, Any]:
        """Конвертирует в словарь для API-ответа."""
        return asdict(self)

    @classmethod
    def field_names(cls) -> list[str]:
        """Список имён всех полей включая унаследованные."""
        return [f.name for f in fields(cls)]


@dataclass
class TimestampedDTO(BaseDTO):
    """DTO с временными метками. Использует kw_only для своих полей."""
    created_at: str = field(
        kw_only=True,
        default_factory=lambda: datetime.datetime.now().isoformat()
    )
    updated_at: str = field(
        kw_only=True,
        default_factory=lambda: datetime.datetime.now().isoformat()
    )

    def __post_init__(self) -> None:
        # У BaseDTO нет __post_init__ — super() вызывает object.__post_init__
        # Но если добавить позже — super() обеспечит корректный вызов
        pass


@dataclass
class UserDTO(TimestampedDTO):
    """DTO пользователя."""
    RESOURCE_TYPE: ClassVar[str] = "user"

    username: str = field(kw_only=True)
    email: str = field(kw_only=True)
    roles: tuple[str, ...] = field(kw_only=True, default_factory=tuple)
    is_active: bool = field(kw_only=True, default=True)

    def __post_init__(self) -> None:
        super().__post_init__()
        self.email = self.email.lower().strip()

    def to_dict(self) -> dict[str, Any]:
        d = super().to_dict()
        d["roles"] = list(d["roles"])   # кортеж → список для JSON
        d["resource_type"] = self.RESOURCE_TYPE
        return d


@dataclass
class AdminDTO(UserDTO):
    """DTO администратора."""
    RESOURCE_TYPE: ClassVar[str] = "admin"

    admin_level: int = field(kw_only=True, default=1)
    managed_sections: tuple[str, ...] = field(kw_only=True, default_factory=tuple)

    def __post_init__(self) -> None:
        super().__post_init__()
        if not 1 <= self.admin_level <= 3:
            raise ValueError(f"admin_level должен быть 1–3, получен {self.admin_level}")

    def to_dict(self) -> dict[str, Any]:
        d = super().to_dict()
        d["managed_sections"] = list(d["managed_sections"])
        return d


@dataclass
class OrderItemDTO(BaseDTO):
    """DTO позиции заказа."""
    product_id: int = field(kw_only=True)
    product_name: str = field(kw_only=True)
    quantity: int = field(kw_only=True)
    unit_price: float = field(kw_only=True)

    @property
    def total_price(self) -> float:
        return self.quantity * self.unit_price


@dataclass
class OrderDTO(TimestampedDTO):
    """DTO заказа с вложенными объектами."""
    user_id: int = field(kw_only=True)
    status: str = field(kw_only=True, default="pending")
    items: list[OrderItemDTO] = field(kw_only=True, default_factory=list)

    @property
    def total(self) -> float:
        return sum(item.total_price for item in self.items)

    def to_dict(self) -> dict[str, Any]:
        d = super().to_dict()
        # asdict() уже рекурсивно конвертирует items
        d["total"] = self.total
        d["items_count"] = len(self.items)
        return d


# ─── Демонстрация ────────────────────────────────────────────────────────────

print("=== Поля UserDTO (включая унаследованные) ===")
print(UserDTO.field_names())
# ['id', 'created_at', 'updated_at', 'username', 'email', 'roles', 'is_active']

print("\n=== Создание пользователей ===")
user = UserDTO(
    id=1,
    username="alice",
    email="ALICE@EXAMPLE.COM",
    roles=("admin", "user"),
)
print(user)

admin = AdminDTO(
    id=2,
    username="bob",
    email="bob@example.com",
    roles=("superadmin",),
    admin_level=3,
    managed_sections=("news", "finance"),
)
print(admin)

print("\n=== isinstance через иерархию ===")
print(isinstance(admin, UserDTO))         # True
print(isinstance(admin, TimestampedDTO))  # True
print(isinstance(admin, BaseDTO))         # True

print("\n=== to_dict() ===")
import json
print(json.dumps(user.to_dict(), ensure_ascii=False, indent=2))

print("\n=== Заказ с вложенными DTO ===")
order = OrderDTO(
    id=1001,
    user_id=1,
    items=[
        OrderItemDTO(1, product_id=10, product_name="Ноутбук", quantity=1, unit_price=89990.0),
        OrderItemDTO(2, product_id=20, product_name="Мышь", quantity=2, unit_price=1500.0),
    ]
)
print(f"Итого: {order.total:.2f} руб.")
print(json.dumps(order.to_dict(), ensure_ascii=False, indent=2))
```

---

## Практический пример: ABC + dataclass репозитории

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Generic, TypeVar

T = TypeVar("T")


class Repository(ABC, Generic[T]):
    """Абстрактный репозиторий. Контракт для всех хранилищ."""

    @abstractmethod
    def get(self, entity_id: int) -> T | None:
        ...

    @abstractmethod
    def save(self, entity: T) -> T:
        ...

    @abstractmethod
    def delete(self, entity_id: int) -> bool:
        ...

    @abstractmethod
    def list_all(self) -> list[T]:
        ...

    def get_or_raise(self, entity_id: int) -> T:
        """Конкретный метод — доступен всем репозиториям."""
        entity = self.get(entity_id)
        if entity is None:
            raise ValueError(f"Сущность с id={entity_id} не найдена")
        return entity


@dataclass
class User:
    id: int
    username: str
    email: str


@dataclass
class Product:
    id: int
    name: str
    price: float


@dataclass
class InMemoryUserRepository(Repository[User]):
    """
    In-memory репозиторий пользователей.
    Dataclass + ABC: конфигурация через поля, контракт через ABC.
    """
    initial_data: list[User] = field(default_factory=list)
    _storage: dict[int, User] = field(init=False, default_factory=dict, repr=False)
    _next_id: int = field(init=False, default=1, repr=False)

    def __post_init__(self) -> None:
        for user in self.initial_data:
            self._storage[user.id] = user
            self._next_id = max(self._next_id, user.id + 1)

    def get(self, entity_id: int) -> User | None:
        return self._storage.get(entity_id)

    def save(self, entity: User) -> User:
        if entity.id == 0:
            entity = User(self._next_id, entity.username, entity.email)
            self._next_id += 1
        self._storage[entity.id] = entity
        return entity

    def delete(self, entity_id: int) -> bool:
        return bool(self._storage.pop(entity_id, None))

    def list_all(self) -> list[User]:
        return list(self._storage.values())


@dataclass
class InMemoryProductRepository(Repository[Product]):
    """In-memory репозиторий продуктов."""
    _storage: dict[int, Product] = field(init=False, default_factory=dict, repr=False)
    _next_id: int = field(init=False, default=1, repr=False)

    def get(self, entity_id: int) -> Product | None:
        return self._storage.get(entity_id)

    def save(self, entity: Product) -> Product:
        if entity.id == 0:
            entity = Product(self._next_id, entity.name, entity.price)
            self._next_id += 1
        self._storage[entity.id] = entity
        return entity

    def delete(self, entity_id: int) -> bool:
        return bool(self._storage.pop(entity_id, None))

    def list_all(self) -> list[Product]:
        return list(self._storage.values())


# Обобщённая функция — работает с любым Repository[T]
def bulk_save(repo: Repository[T], entities: list[T]) -> list[T]:
    return [repo.save(entity) for entity in entities]


# Демонстрация
user_repo = InMemoryUserRepository(initial_data=[
    User(1, "alice", "alice@example.com"),
])

product_repo = InMemoryProductRepository()

saved_users = bulk_save(user_repo, [
    User(0, "bob", "bob@example.com"),
    User(0, "carol", "carol@example.com"),
])
print("Пользователи:", user_repo.list_all())

saved_products = bulk_save(product_repo, [
    Product(0, "Ноутбук", 89990.0),
    Product(0, "Мышь", 1500.0),
])
print("Продукты:", product_repo.list_all())

# get_or_raise — конкретный метод из ABC
try:
    user_repo.get_or_raise(99)
except ValueError as e:
    print(f"Ошибка: {e}")
```

---

## Композиция как альтернатива наследованию

Когда иерархия dataclass становится сложной, лучше использовать композицию — dataclass как поле другого dataclass:

```python
from dataclasses import dataclass, field, asdict
from typing import Any
import json


@dataclass(frozen=True)
class ContactInfo:
    """Value Object с контактными данными."""
    email: str
    phone: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "email", self.email.lower().strip())


@dataclass(frozen=True)
class Address:
    """Value Object с адресом."""
    country: str
    city: str
    street: str
    postal_code: str | None = None


@dataclass
class CustomerProfile:
    """
    Агрегат: содержит другие dataclass как поля.
    Вместо глубокого наследования — композиция.
    """
    id: int
    first_name: str
    last_name: str
    contact: ContactInfo        # вложенный dataclass
    address: Address | None = None
    orders_count: int = 0
    loyalty_points: int = 0

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def to_api_response(self) -> dict[str, Any]:
        """asdict() рекурсивно конвертирует вложенные dataclass."""
        return asdict(self)


@dataclass
class OrderAggregate:
    """Заказ как агрегат из нескольких dataclass."""
    id: int
    customer: CustomerProfile    # вложенный агрегат
    items: list[dict] = field(default_factory=list)
    status: str = "pending"

    @property
    def total(self) -> float:
        return sum(item.get("price", 0) * item.get("qty", 0) for item in self.items)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "customer_id": self.customer.id,
            "customer_name": self.customer.full_name,
            "customer_email": self.customer.contact.email,
            "items": self.items,
            "total": self.total,
            "status": self.status,
        }


# Демонстрация
customer = CustomerProfile(
    id=42,
    first_name="Alice",
    last_name="Smith",
    contact=ContactInfo(email="ALICE@EXAMPLE.COM", phone="+79001234567"),
    address=Address("Россия", "Москва", "ул. Пушкина"),
    loyalty_points=1500,
)

order = OrderAggregate(
    id=1001,
    customer=customer,
    items=[
        {"product": "Ноутбук", "price": 89990.0, "qty": 1},
        {"product": "Мышь", "price": 1500.0, "qty": 2},
    ]
)

print(f"Клиент: {customer.full_name}")
print(f"Email: {customer.contact.email}")   # нормализован
print(f"Итого заказа: {order.total:.2f} руб.")
print()
print("API-ответ заказа:")
print(json.dumps(order.to_dict(), ensure_ascii=False, indent=2))
print()
print("Полный профиль (asdict):")
# asdict рекурсивно конвертирует всю вложенную структуру
profile_dict = asdict(customer)
print(json.dumps(profile_dict, ensure_ascii=False, indent=2))
```

---

## Неочевидные моменты и типичные ошибки

**`__eq__` сравнивает только с объектами того же типа.** Это важная деталь: автогенерированный `__eq__` возвращает `NotImplemented` если `other.__class__ is not self.__class__`. Это значит, что `UserDTO(1, ...)` НЕ равен `AdminDTO(1, ...)` — даже если все общие поля совпадают:

```python
user = UserDTO(id=1, username="alice", email="a@a.com")
admin = AdminDTO(id=1, username="alice", email="a@a.com", admin_level=1)

print(user == admin)   # False — разные классы!
```

**Множественное наследование нескольких dataclass — почти всегда плохая идея:**

```python
@dataclass
class A:
    x: int

@dataclass
class B:
    y: int

# Технически работает, но создаёт запутанный порядок полей
@dataclass
class C(A, B):
    z: int

c = C(1, 2, 3)
print(c)   # C(x=1, y=2, z=3) — работает, но зачем?
```

Используйте компоузицию вместо множественного наследования dataclass.

**`replace()` при наследовании создаёт объект того же типа:**

```python
from dataclasses import replace

admin = AdminDTO(id=1, username="alice", email="a@a.com", admin_level=2)
updated = replace(admin, username="alice_updated")
print(type(updated).__name__)   # AdminDTO — не UserDTO!
print(updated.admin_level)      # 2 — сохранился
```

**Переопределение `__eq__` вручную отключает автогенерацию:**

```python
@dataclass
class MyDTO(BaseDTO):
    username: str

    def __eq__(self, other: object) -> bool:
        # Вручную — автогенерированный __eq__ dataclass заменён
        if not isinstance(other, MyDTO):
            return NotImplemented
        return self.username == other.username
        # id не проверяется — только username
```

---

## Вопросы

1. В каком порядке расположены поля в `__init__` дочернего dataclass? Как это соотносится с правилом «обязательные поля перед необязательными»?
2. Почему `__post_init__` при наследовании не вызывается автоматически по цепочке? Как это исправить?
3. Почему нельзя смешивать `frozen=True` и `frozen=False` в одной иерархии dataclass? Что произойдёт при попытке?
4. Dataclass наследует от обычного класса. Почему `__post_init__` должен явно вызвать `__init__` обычного родителя?
5. Каков результат `UserDTO(id=1, ...) == AdminDTO(id=1, ...)`? Почему?
6. В чём преимущество паттерна ABC + dataclass по сравнению с обычным dataclass-наследованием?
7. Когда использовать наследование dataclass, а когда — композицию?
8. Как `replace()` ведёт себя при наследовании dataclass? Что возвращает `replace(admin_dto, username="new")`?

---

## Задачи

### **Задача 1**. 

Иерархия с правильным `__post_init__`

Создайте трёхуровневую иерархию dataclass:

`BaseEntity` → поля `id: int`, `version: int = 1`. В `__post_init__`: проверить `id > 0`.

`AuditedEntity(BaseEntity)` → поля `created_by: str = field(kw_only=True)`, `updated_by: str = field(kw_only=True, default="")`. В `__post_init__`: вызвать `super().__post_init__()`, установить `updated_by = created_by` если пустой.

`SoftDeletableEntity(AuditedEntity)` → поля `is_deleted: bool = field(kw_only=True, default=False)`, `deleted_by: str = field(kw_only=True, default="")`. В `__post_init__`: вызвать `super().__post_init__()`, если `is_deleted=True` и `deleted_by=""` — выбросить ValueError.

Создайте конкретную `ArticleEntity(SoftDeletableEntity)` с полями `title: str = field(kw_only=True)`, `content: str = field(kw_only=True)`. Убедитесь что вся цепочка `__post_init__` работает.

**Пример использования**:

```python
article = ArticleEntity(
    id=1,
    created_by="alice",
    title="Введение в Python",
    content="Python — мощный язык программирования...",
)
print(article)
print(f"created_by: {article.created_by}")
print(f"updated_by: {article.updated_by}")   # = created_by автоматически

# Мягкое удаление
article.soft_delete("admin")
print(f"is_deleted: {article.is_deleted}")
print(f"deleted_by: {article.deleted_by}")

# Ошибка валидации id
try:
    ArticleEntity(-1, created_by="alice", title="Test", content="...")
except ValueError as e:
    print(f"Ошибка: {e}")

# Ошибка: удалён без указания кто
try:
    ArticleEntity(2, created_by="alice", title="Test", content="...",
                  is_deleted=True)
except ValueError as e:
    print(f"Ошибка: {e}")
```

---

### **Задача 2**. 

frozen-иерархия Value Objects

Создайте иерархию `frozen=True` dataclass для описания денежной транзакции. `Currency(frozen=True)` — `code: str` (ISO-4217, 3 буквы), `symbol: str`. В `__post_init__`: нормализовать `code` к верхнему регистру, проверить длину. `Money(frozen=True)` — `amount: int` (в копейках), `currency: Currency`. Свойство `in_major_units -> float`. Метод `convert_to(rate: float) -> Money`. `Transaction(frozen=True)` — `id: str`, `from_amount: Money`, `to_amount: Money`, `description: str = ""`. Свойство `exchange_rate -> float`. Метод `with_description(desc: str) -> Transaction` через `replace()`.

**Пример использования**:

```python
rub = Currency("rub", "₽")
usd = Currency("USD", "$")

price = Money(150000, rub)
converted = price.convert_to(0.011, usd)

txn = Transaction("txn-001", price, converted)
txn_with_desc = txn.with_description("Покупка ноутбука")

print(txn_with_desc)
print(f"Курс: {txn_with_desc.exchange_rate:.4f}")
print(f"Описание: {txn_with_desc.description}")
print(f"Исходный txn: {txn.description!r}")   # не изменился!

# frozen — нельзя изменить
try:
    txn.description = "test"
except Exception as e:
    print(type(e).__name__)
```

---

### **Задача 3**. 

ABC + dataclass для системы отчётов

Создайте систему генерации отчётов, объединяющую ABC и dataclass. `BaseReport(ABC)` — абстрактные методы `generate() -> str`, `get_title() -> str`. Конкретные dataclass:

`SalesReport(@dataclass)` — поля `period: str`, `total_sales: float`, `orders_count: int`. Реализует `generate()` — форматирует отчёт о продажах. `UserActivityReport(@dataclass)` — поля `period: str`, `active_users: int`, `new_registrations: int`, `churned_users: int`. Реализует `generate()`.

`ReportBundle(@dataclass)` — поле `reports: list[BaseReport]`. Метод `generate_all() -> list[str]`. Метод `summary() -> str`.

**Пример использования**:

```python
bundle = ReportBundle([
    SalesReport("Q1 2024", 1_500_000.0, 450),
    UserActivityReport("Q1 2024", 12_000, 800, 120),
])

for report in bundle.generate_all():
    print(report)
    print("---")

print(bundle.summary())

# isinstance
for r in bundle.reports:
    print(f"{type(r).__name__} is BaseReport: {isinstance(r, BaseReport)}")
```

---

[Предыдущий урок](lesson31.md)