# Урок 29. Протоколы (`Protocol`): структурная типизация как альтернатива ABC

---

## Две модели типизации

Прежде чем изучать `Protocol`, нужно понять две фундаментально разные модели проверки типов.

**Номинальная типизация** (nominal typing) — тип определяется именем и иерархией наследования. Чтобы объект типа `B` мог использоваться там, где ожидается `A`, `B` должен явно наследовать от `A`. Именно так работают Java, C#, и ABC в Python:

```python
from abc import ABC, abstractmethod

class Sendable(ABC):
    @abstractmethod
    def send(self) -> None:
        pass

class Email(Sendable):   # ЯВНОЕ наследование обязательно
    def send(self) -> None:
        print("Отправка email")

class SMSMessage:
    def send(self) -> None:
        print("Отправка SMS")

def deliver(notification: Sendable) -> None:
    notification.send()

deliver(Email())       # OK — Email наследует Sendable
deliver(SMSMessage())  # Ошибка типа! SMSMessage не является Sendable
```

**Структурная типизация** (structural typing) — тип определяется структурой: набором методов и атрибутов. Если объект «выглядит как» нужный тип — он и есть этот тип. Именно так работает duck typing в Python, Go, TypeScript:

```python
# В Go это называется interface — любой тип, реализующий методы, удовлетворяет интерфейсу
# В Python это duck typing — но без поддержки статического анализа

def deliver(notification):   # annotation: object — mypy ничего не знает
    notification.send()   # mypy: что такое send()? что это вообще за объект?
```

Python исторически был duck typing языком — это гибко и удобно. Но у такого подхода есть недостаток: статический анализатор вроде mypy не может проверить, что переданный объект действительно имеет метод `send()`. Он видит только `object`.

`Protocol` решает этот конфликт: он позволяет описать структурный тип формально, чтобы mypy понимал требования — без необходимости явного наследования.

---

## `Protocol`: формализованный duck typing

`Protocol` был добавлен в Python 3.8 (PEP 544). Это механизм для формализованного описания структурных типов — протоколов поведения.

Объявление протокола:

```python
from typing import Protocol


class Sendable(Protocol):
    """Протокол для объектов, которые умеют себя отправлять."""

    def send(self) -> None:
        ...   # тело не важно — только сигнатура


class EmailNotification:
    """Этот класс НЕ наследует Sendable."""

    def __init__(self, recipient: str, message: str) -> None:
        self.recipient = recipient
        self.message = message

    def send(self) -> None:
        print(f"Email → {self.recipient}: {self.message}")


class SMSNotification:
    """Этот класс тоже НЕ наследует Sendable."""

    def __init__(self, phone: str, text: str) -> None:
        self.phone = phone
        self.text = text

    def send(self) -> None:
        print(f"SMS → {self.phone}: {self.text}")


def deliver(notification: Sendable) -> None:
    """Принимает любой объект, реализующий протокол Sendable."""
    notification.send()
```

Теперь `deliver` аннотирован типом `Sendable`. mypy проверит: у переданного объекта должен быть метод `send()` с правильной сигнатурой. И при этом классы `EmailNotification` и `SMSNotification` не обязаны наследовать `Sendable`:

```python
email = EmailNotification("alice@example.com", "Привет!")
sms = SMSNotification("+79001234567", "Код: 1234")

deliver(email)   # OK — EmailNotification имеет метод send()
deliver(sms)     # OK — SMSNotification тоже имеет send()

# Класс без метода send() — mypy выдаст ошибку
class BrokenClass:
    pass

deliver(BrokenClass())   # mypy: Argument 1 has incompatible type "BrokenClass"; expected "Sendable"
```

Это и есть структурная типизация: соответствие определяется структурой (наличием метода), а не именем (наследованием).

---

## Протокол с атрибутами

`Protocol` может требовать не только методы, но и атрибуты:

```python
from typing import Protocol


class HasId(Protocol):
    """Протокол для объектов с идентификатором."""
    id: int


class HasTimestamps(Protocol):
    """Протокол для объектов с временными метками."""
    created_at: str
    updated_at: str


class Entity(Protocol):
    """Объединённый протокол: id + временные метки."""
    id: int
    created_at: str
    updated_at: str


class User:
    def __init__(self, user_id: int, name: str) -> None:
        self.id = user_id
        self.name = name
        self.created_at = "2024-01-01"
        self.updated_at = "2024-01-01"


class Product:
    def __init__(self, product_id: int, title: str) -> None:
        self.id = product_id
        self.title = title
        self.created_at = "2024-01-01"
        self.updated_at = "2024-01-01"


def get_entity_id(entity: HasId) -> int:
    """Работает с любым объектом, имеющим атрибут id."""
    return entity.id


def format_entity(entity: Entity) -> str:
    """Работает с любым объектом, имеющим id и временные метки."""
    return f"Entity(id={entity.id}, created={entity.created_at})"


user = User(1, "Alice")
product = Product(42, "Ноутбук")

print(get_entity_id(user))      # 1
print(get_entity_id(product))   # 42
print(format_entity(user))      # Entity(id=1, created=2024-01-01)
```

Атрибуты в протоколе объявляются как аннотации без значения по умолчанию. mypy проверит, что у переданного объекта есть атрибуты с правильными типами.

---

## `Protocol` с `@property`

Интересная особенность: если протокол требует атрибут, класс может реализовать его как атрибут экземпляра или как `@property` — mypy принимает оба варианта:

```python
from typing import Protocol


class HasStatus(Protocol):
    """Протокол: объект должен иметь атрибут status."""
    status: str


class OrderWithAttribute:
    """Реализация через атрибут экземпляра."""

    def __init__(self) -> None:
        self.status: str = "pending"


class OrderWithProperty:
    """Реализация через @property."""

    def __init__(self) -> None:
        self._status: str = "pending"

    @property
    def status(self) -> str:
        return self._status

    @status.setter
    def status(self, value: str) -> None:
        self._status = value


def get_status(entity: HasStatus) -> str:
    return entity.status


order1 = OrderWithAttribute()
order2 = OrderWithProperty()

print(get_status(order1))   # pending
print(get_status(order2))   # pending
```

Это особенно удобно для протоколов read-only атрибутов:

```python
class ReadOnlyId(Protocol):
    """Объект должен предоставлять id только для чтения."""

    @property
    def id(self) -> int:
        ...


class ImmutableRecord:
    def __init__(self, record_id: int) -> None:
        self._id = record_id

    @property
    def id(self) -> int:
        return self._id
```

---

## `@runtime_checkable`: протоколы и `isinstance()`

По умолчанию протоколы предназначены только для статического анализа — их нельзя использовать в `isinstance()`. Для добавления рантайм-проверки используется декоратор `@runtime_checkable`:

```python
from typing import Protocol, runtime_checkable


@runtime_checkable
class Closeable(Protocol):
    def close(self) -> None:
        ...


class DatabaseConnection:
    def close(self) -> None:
        print("Соединение закрыто")


class NetworkSocket:
    def close(self) -> None:
        print("Сокет закрыт")


class Timer:
    def start(self) -> None:
        print("Таймер запущен")
    # close() нет!


db = DatabaseConnection()
socket = NetworkSocket()
timer = Timer()

print(isinstance(db, Closeable))      # True — есть метод close()
print(isinstance(socket, Closeable))  # True — есть метод close()
print(isinstance(timer, Closeable))   # False — нет метода close()
```

Однако `@runtime_checkable` имеет важное ограничение: в рантайме проверяется только **наличие** методов с нужными именами, но не их сигнатуры. Это отличает его от статической проверки mypy:

```python
@runtime_checkable
class Serializable(Protocol):
    def serialize(self, format: str) -> str:
        ...


class WrongSerializer:
    def serialize(self) -> bytes:   # неверная сигнатура!
        return b"data"


ws = WrongSerializer()
print(isinstance(ws, Serializable))   # True в рантайме (метод есть)
# Но mypy выдаст ошибку (сигнатура не совпадает)
```

Это принципиальная разница между `@runtime_checkable` и ABC: ABC с `__subclasshook__` или `register()` также даёт возможность рантайм-проверки, но ABC явно требует регистрации или наследования.

---

## Наследование протоколов

Протоколы могут наследоваться друг от друга, объединяя требования:

```python
from typing import Protocol


class Readable(Protocol):
    def read(self) -> str:
        ...


class Writable(Protocol):
    def write(self, data: str) -> None:
        ...


class Closeable(Protocol):
    def close(self) -> None:
        ...


# Комбинированный протокол
class ReadWriteCloseable(Readable, Writable, Closeable, Protocol):
    """Объект умеет читать, писать и закрываться."""
    pass


class FileHandle:
    """Этот класс удовлетворяет всем трём протоколам."""

    def __init__(self, path: str) -> None:
        self.path = path
        self._data: list[str] = []

    def read(self) -> str:
        return "\n".join(self._data)

    def write(self, data: str) -> None:
        self._data.append(data)

    def close(self) -> None:
        print(f"Файл {self.path} закрыт")


def process_stream(stream: ReadWriteCloseable) -> None:
    stream.write("Hello")
    content = stream.read()
    print(f"Содержимое: {content}")
    stream.close()


fh = FileHandle("data.txt")
process_stream(fh)   # OK — FileHandle реализует все методы
```

Важно: при объявлении составного протокола нужно явно указывать `Protocol` в списке базовых классов. Если его не указать — это будет обычный ABC, а не протокол.

---

## `Protocol` vs ABC: когда что использовать

Это ключевой вопрос урока — и практический, и концептуальный.

```
Критерий                    Protocol         ABC
─────────────────────────────────────────────────────
Наследование обязательно?   Нет              Да
isinstance() в рантайме     Да (с @r_c)      Да (всегда)
Проверка сигнатур           Только mypy      Нет
Общие реализации методов    Нет (не принято) Да
Работа с внешними классами  Да               Нет (без register)
Контракт документирован     Через типы       Через ABC
Строгость проверки          Статически       Только наличие метода
```

**Используйте ABC когда:**
- Нужны общие реализации методов (Template Method через конкретные методы в ABC).
- Контракт должен быть явным и проверяемым в рантайме.
- Строите иерархию, где наследование имеет семантический смысл (AdminUser is-a User).
- Команда предпочитает явное наследование как документацию намерений.

**Используйте `Protocol` когда:**
- Работаете с классами из внешних библиотек, которые нельзя изменить.
- Хотите использовать duck typing, но с поддержкой статического анализа.
- Создаёте «тонкие» интерфейсы — минимальный набор требований.
- Пишете библиотечный код, который должен работать с разными реализациями.
- Описываете зависимости для тестирования (test doubles).

На практике в современном Python-коде часто используются оба: ABC для иерархий внутри проекта, `Protocol` для описания «входных» и «выходных» интерфейсов на границах модулей.

---

## Практический пример: протоколы в API-слое

Реализуем слой API с чёткими протоколами на границах компонентов:

```python
from __future__ import annotations
from typing import Protocol, runtime_checkable, Any
import json
import datetime


# ─── Протоколы ─────────────────────────────────────────────────────────────

@runtime_checkable
class Serializable(Protocol):
    """Объект умеет сериализовать себя в словарь."""

    def to_dict(self) -> dict[str, Any]:
        ...


class Validatable(Protocol):
    """Объект умеет валидировать себя."""

    def validate(self) -> list[str]:
        """Возвращает список ошибок (пустой если валиден)."""
        ...

    @property
    def is_valid(self) -> bool:
        ...


class Identifiable(Protocol):
    """Объект имеет уникальный идентификатор."""
    id: int | str


class Persistable(Serializable, Identifiable, Protocol):
    """Объект умеет сериализовать себя и имеет id — готов к сохранению."""
    pass


# ─── Конкретные классы (без наследования от протоколов) ────────────────────

class UserDTO:
    """DTO пользователя. Не наследует ни один протокол."""

    def __init__(self, user_id: int, username: str, email: str) -> None:
        self.id = user_id
        self.username = username
        self.email = email

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "username": self.username, "email": self.email}

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.username or len(self.username) < 3:
            errors.append("username: минимум 3 символа")
        if not self.email or "@" not in self.email:
            errors.append("email: некорректный формат")
        return errors

    @property
    def is_valid(self) -> bool:
        return not bool(self.validate())


class OrderDTO:
    """DTO заказа. Тоже не наследует протоколы."""

    def __init__(self, order_id: int, user_id: int, total: float) -> None:
        self.id = order_id
        self.user_id = user_id
        self.total = total
        self.created_at = datetime.datetime.now().isoformat()

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "total": self.total,
            "created_at": self.created_at,
        }

    def validate(self) -> list[str]:
        errors: list[str] = []
        if self.total <= 0:
            errors.append("total: должен быть положительным")
        return errors

    @property
    def is_valid(self) -> bool:
        return not bool(self.validate())


# ─── Функции, работающие через протоколы ───────────────────────────────────

def to_json_response(entity: Serializable, status: int = 200) -> dict[str, Any]:
    """Принимает любой Serializable объект и создаёт JSON-ответ."""
    return {
        "status": status,
        "data": entity.to_dict(),
        "timestamp": datetime.datetime.now().isoformat(),
    }


def validate_and_respond(entity: Validatable) -> dict[str, Any]:
    """Валидирует объект и возвращает результат."""
    errors = entity.validate()
    if errors:
        return {"status": 422, "errors": errors}
    return {"status": 200, "message": "Validation passed"}


def save_entity(entity: Persistable) -> dict[str, Any]:
    """Сохраняет объект (имитация). Требует id + to_dict()."""
    data = entity.to_dict()
    print(f"[DB] Сохранение записи id={entity.id}: {data}")
    return {"saved": True, "id": entity.id}


# ─── Демонстрация ───────────────────────────────────────────────────────────

user = UserDTO(1, "alice", "alice@example.com")
bad_user = UserDTO(2, "ab", "not-email")
order = OrderDTO(1001, 1, 89990.0)

# isinstance работает с @runtime_checkable
print(isinstance(user, Serializable))    # True — есть to_dict()
print(isinstance(user, Serializable))    # True

# Работа через протоколы — классы не связаны иерархией
print(to_json_response(user))
print(to_json_response(order))

print(validate_and_respond(user))        # 200 — валидный
print(validate_and_respond(bad_user))    # 422 — невалидный

print(save_entity(user))    # Работает: UserDTO реализует Persistable
print(save_entity(order))   # Работает: OrderDTO тоже реализует Persistable

# Сторонний класс без наследования — тоже работает если реализует протокол
class ThirdPartyProduct:
    """Класс из внешней библиотеки — нельзя изменить."""
    def __init__(self, pid: int, name: str) -> None:
        self.id = pid
        self.name = name

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "name": self.name}


product = ThirdPartyProduct(42, "Ноутбук")
print(isinstance(product, Serializable))   # True
print(to_json_response(product))           # Работает!
```

---

## Практический пример: протоколы для тестирования

Одно из лучших применений `Protocol` — описание зависимостей для тестирования. Вместо создания моков конкретных классов можно создавать простые объекты, реализующие только нужный протокол:

```python
from typing import Protocol, Any
from dataclasses import dataclass, field


# ─── Протоколы зависимостей ────────────────────────────────────────────────

class UserStorageProtocol(Protocol):
    """Протокол хранилища пользователей."""

    def get(self, user_id: int) -> dict[str, Any] | None:
        ...

    def save(self, user: dict[str, Any]) -> dict[str, Any]:
        ...

    def delete(self, user_id: int) -> bool:
        ...


class EmailSenderProtocol(Protocol):
    """Протокол для отправки email."""

    def send_email(
        self,
        recipient: str,
        subject: str,
        body: str,
    ) -> bool:
        ...


class CacheProtocol(Protocol):
    """Протокол кеша."""

    def get(self, key: str) -> Any | None:
        ...

    def set(self, key: str, value: Any, ttl: int = 300) -> None:
        ...

    def delete(self, key: str) -> None:
        ...


# ─── Сервис, использующий протоколы ────────────────────────────────────────

class UserService:
    """
    Сервис пользователей. Зависит только от протоколов —
    не от конкретных реализаций.
    """

    def __init__(
        self,
        storage: UserStorageProtocol,
        email_sender: EmailSenderProtocol,
        cache: CacheProtocol,
    ) -> None:
        self._storage = storage
        self._email_sender = email_sender
        self._cache = cache

    def get_user(self, user_id: int) -> dict[str, Any] | None:
        # Сначала ищем в кеше
        cached = self._cache.get(f"user:{user_id}")
        if cached is not None:
            return cached

        user = self._storage.get(user_id)
        if user:
            self._cache.set(f"user:{user_id}", user, ttl=600)
        return user

    def create_user(self, username: str, email: str) -> dict[str, Any]:
        user_data = {"username": username, "email": email}
        saved_user = self._storage.save(user_data)

        # Отправляем приветственное письмо
        self._email_sender.send_email(
            recipient=email,
            subject="Добро пожаловать!",
            body=f"Привет, {username}! Регистрация прошла успешно."
        )
        return saved_user

    def delete_user(self, user_id: int) -> bool:
        deleted = self._storage.delete(user_id)
        if deleted:
            self._cache.delete(f"user:{user_id}")
        return deleted


# ─── Производственные реализации ────────────────────────────────────────────

class PostgresUserStorage:
    """Реальное хранилище в PostgreSQL."""

    def __init__(self) -> None:
        self._data: dict[int, dict[str, Any]] = {}
        self._next_id = 1

    def get(self, user_id: int) -> dict[str, Any] | None:
        print(f"[PostgreSQL] SELECT * FROM users WHERE id={user_id}")
        return self._data.get(user_id)

    def save(self, user: dict[str, Any]) -> dict[str, Any]:
        user_with_id = {"id": self._next_id, **user}
        self._data[self._next_id] = user_with_id
        self._next_id += 1
        print(f"[PostgreSQL] INSERT INTO users: {user_with_id}")
        return user_with_id

    def delete(self, user_id: int) -> bool:
        if user_id in self._data:
            del self._data[user_id]
            print(f"[PostgreSQL] DELETE FROM users WHERE id={user_id}")
            return True
        return False


class RedisCache:
    """Реальный Redis-кеш."""

    def __init__(self) -> None:
        self._store: dict[str, Any] = {}

    def get(self, key: str) -> Any | None:
        print(f"[Redis] GET {key}")
        return self._store.get(key)

    def set(self, key: str, value: Any, ttl: int = 300) -> None:
        print(f"[Redis] SET {key} (ttl={ttl})")
        self._store[key] = value

    def delete(self, key: str) -> None:
        print(f"[Redis] DEL {key}")
        self._store.pop(key, None)


class SMTPEmailSender:
    """Реальная отправка через SMTP."""

    def send_email(self, recipient: str, subject: str, body: str) -> bool:
        print(f"[SMTP] → {recipient}: {subject}")
        return True


# ─── Тестовые заглушки (TEST DOUBLES) ──────────────────────────────────────
# Не наследуют от протоколов — просто реализуют нужные методы

@dataclass
class FakeUserStorage:
    """Тестовая заглушка хранилища. Хранит в памяти."""
    _data: dict[int, dict[str, Any]] = field(default_factory=dict)
    _next_id: int = field(default=1)

    def get(self, user_id: int) -> dict[str, Any] | None:
        return self._data.get(user_id)

    def save(self, user: dict[str, Any]) -> dict[str, Any]:
        user_with_id = {"id": self._next_id, **user}
        self._data[self._next_id] = user_with_id
        self._next_id += 1
        return user_with_id

    def delete(self, user_id: int) -> bool:
        return bool(self._data.pop(user_id, None))


@dataclass
class FakeEmailSender:
    """Тестовая заглушка email. Записывает отправленные письма."""
    sent_emails: list[dict[str, str]] = field(default_factory=list)

    def send_email(self, recipient: str, subject: str, body: str) -> bool:
        self.sent_emails.append({
            "recipient": recipient,
            "subject": subject,
            "body": body,
        })
        return True


@dataclass
class FakeCache:
    """Тестовая заглушка кеша."""
    _store: dict[str, Any] = field(default_factory=dict)

    def get(self, key: str) -> Any | None:
        return self._store.get(key)

    def set(self, key: str, value: Any, ttl: int = 300) -> None:
        self._store[key] = value

    def delete(self, key: str) -> None:
        self._store.pop(key, None)


# ─── Демонстрация: один сервис, две конфигурации ───────────────────────────

print("=== Продакшн конфигурация ===")
prod_service = UserService(
    storage=PostgresUserStorage(),
    email_sender=SMTPEmailSender(),
    cache=RedisCache(),
)
created = prod_service.create_user("alice", "alice@example.com")
print(f"Создан: {created}")
found = prod_service.get_user(1)
print(f"Найден (из кеша): {found}")

print("\n=== Тестовая конфигурация ===")
fake_storage = FakeUserStorage()
fake_email = FakeEmailSender()
fake_cache = FakeCache()

test_service = UserService(
    storage=fake_storage,
    email_sender=fake_email,
    cache=fake_cache,
)

test_user = test_service.create_user("bob", "bob@test.com")
print(f"Тестовый пользователь: {test_user}")
print(f"Отправлено писем: {len(fake_email.sent_emails)}")
print(f"Письмо: {fake_email.sent_emails[0]}")

# Проверяем, что FakeUserStorage удовлетворяет протоколу
print(f"\nFakeUserStorage is UserStorageProtocol: "
      f"{isinstance(fake_storage, UserStorageProtocol)}")
```

Это паттерн называется Dependency Injection через протоколы. Сервис зависит от абстракций (протоколов), а не от конкретных реализаций. Тестирование становится тривиальным: подменяем реальные реализации заглушками.

---

## Стандартные протоколы из `typing` и `collections.abc`

Python уже содержит множество встроенных протоколов. Вы их использовали с самого начала курса:

```python
from typing import SupportsInt, SupportsFloat, SupportsLen
from collections.abc import Iterable, Sequence, Mapping, Callable, Iterator


# SupportsInt — объект поддерживает int()
def to_int(value: SupportsInt) -> int:
    return int(value)


print(to_int(3.14))   # 3 — float реализует __int__
print(to_int("42"))   # 42 — str реализует __int__


# SupportsLen — объект поддерживает len()
def is_empty(collection: SupportsLen) -> bool:
    return len(collection) == 0


print(is_empty([]))      # True
print(is_empty("hello")) # False
print(is_empty({}))      # True


# Iterable — объект можно итерировать
def print_all(items: Iterable[str]) -> None:
    for item in items:
        print(item)


print_all(["a", "b"])            # list — Iterable
print_all(("c", "d"))            # tuple — Iterable
print_all(x for x in ["e", "f"]) # generator — Iterable
```

Эти протоколы — прямые аналоги `Protocol`, только определены в стандартной библиотеке. `Iterable` из `collections.abc` — это структурный тип: любой объект с `__iter__` является `Iterable`.

---

## Обобщённые протоколы: `Protocol[T]`

Протоколы можно параметризовать типами — точно как `list[T]` или `dict[K, V]`:

```python
from typing import Protocol, TypeVar, Generic

T = TypeVar('T')
ID = TypeVar('ID', int, str)


class Repository(Protocol[T]):
    """
    Обобщённый протокол репозитория.
    T — тип хранимой сущности.
    """

    def get(self, entity_id: int) -> T | None:
        ...

    def save(self, entity: T) -> T:
        ...

    def delete(self, entity_id: int) -> bool:
        ...

    def list_all(self) -> list[T]:
        ...


# ─── Конкретные реализации ──────────────────────────────────────────────────

from dataclasses import dataclass, field


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


class UserRepository:
    """Репозиторий пользователей — реализует Repository[User]."""

    def __init__(self) -> None:
        self._data: dict[int, User] = {}
        self._next_id: int = 1

    def get(self, entity_id: int) -> User | None:
        return self._data.get(entity_id)

    def save(self, entity: User) -> User:
        if not entity.id:
            entity.id = self._next_id
            self._next_id += 1
        self._data[entity.id] = entity
        return entity

    def delete(self, entity_id: int) -> bool:
        return bool(self._data.pop(entity_id, None))

    def list_all(self) -> list[User]:
        return list(self._data.values())


class ProductRepository:
    """Репозиторий продуктов — реализует Repository[Product]."""

    def __init__(self) -> None:
        self._data: dict[int, Product] = {}
        self._next_id: int = 1

    def get(self, entity_id: int) -> Product | None:
        return self._data.get(entity_id)

    def save(self, entity: Product) -> Product:
        if not entity.id:
            entity.id = self._next_id
            self._next_id += 1
        self._data[entity.id] = entity
        return entity

    def delete(self, entity_id: int) -> bool:
        return bool(self._data.pop(entity_id, None))

    def list_all(self) -> list[Product]:
        return list(self._data.values())


# ─── Обобщённая функция ─────────────────────────────────────────────────────

def get_or_raise(repo: Repository[T], entity_id: int) -> T:
    """
    Возвращает сущность из репозитория или выбрасывает ValueError.
    Работает с любым Repository[T].
    """
    entity = repo.get(entity_id)
    if entity is None:
        raise ValueError(f"Сущность с id={entity_id} не найдена")
    return entity


def save_all(repo: Repository[T], entities: list[T]) -> list[T]:
    """Сохраняет список сущностей. Работает с любым Repository[T]."""
    return [repo.save(entity) for entity in entities]


# ─── Демонстрация ───────────────────────────────────────────────────────────

user_repo = UserRepository()
product_repo = ProductRepository()

# Сохраняем пользователей
users = save_all(user_repo, [
    User(0, "alice", "alice@example.com"),
    User(0, "bob", "bob@example.com"),
])
print(f"Сохранено пользователей: {len(users)}")

# Сохраняем продукты
products = save_all(product_repo, [
    Product(0, "Ноутбук", 89990.0),
    Product(0, "Мышь", 1500.0),
])
print(f"Сохранено продуктов: {len(products)}")

# Обобщённая функция работает с обоими репозиториями
alice = get_or_raise(user_repo, 1)
print(f"Пользователь: {alice}")

laptop = get_or_raise(product_repo, 1)
print(f"Продукт: {laptop}")

# Попытка получить несуществующего
try:
    get_or_raise(user_repo, 99)
except ValueError as e:
    print(f"Ошибка: {e}")
```

---

## Неочевидные моменты и типичные ошибки

**Тело методов протокола.** Методы в протоколе должны иметь `...` или `pass` как тело. Не нужно писать `raise NotImplementedError` — это синтаксис ABC, а не протокола. Хотя Python не запретит это, mypy может предупредить.

```python
class Serializable(Protocol):
    def to_dict(self) -> dict:
        ...   # правильно

    def to_json(self) -> str:
        pass  # тоже допустимо

    def to_xml(self) -> str:
        raise NotImplementedError  # работает, но не идиоматично
```

**`__init__` в протоколе.** Не добавляйте `__init__` с параметрами в протокол. `Protocol` описывает интерфейс объекта, а не способ его создания. Если нужен конструктор с параметрами — это признак того, что вам нужен ABC или обычный класс, а не протокол.

**`@classmethod` в протоколе.** Можно объявить:

```python
class HasFromDict(Protocol):
    @classmethod
    def from_dict(cls, data: dict) -> "HasFromDict":
        ...
```

Но mypy проверяет это ограниченно — лучше использовать обычные методы в протоколах.

**Совместимость проверяется mypy, не Python.** В рантайме Python не знает о протоколах (если нет `@runtime_checkable`). Передать объект неправильного типа в функцию с аннотацией-протоколом — не ошибка в рантайме. Только mypy её поймает.

**Нельзя наследовать от `Protocol` и обычного класса одновременно.** Если класс наследует от `Protocol` и от обычного класса — это ABC, а не протокол:

```python
class MyClass:
    pass

# Это создаёт обычный класс, не протокол!
class Bad(Protocol, MyClass):
    pass
```

**Mypy проверяет сигнатуры полностью.** Если протокол требует `def method(self, x: int) -> str`, а класс реализует `def method(self, x: str) -> int` — mypy выдаст ошибку, даже если метод с таким именем есть. `@runtime_checkable` + `isinstance()` этого не проверяет.

---

## Итоги урока

`Protocol` — механизм структурной типизации в Python, добавленный в версии 3.8. Он формализует duck typing: любой класс, реализующий нужные методы и атрибуты, автоматически является «подтипом» протокола — без наследования и регистрации.

Главное отличие от ABC: ABC требует явного `class MyClass(BaseABC)`, а `Protocol` нет. Это делает `Protocol` идеальным для работы с внешними классами и для описания зависимостей при тестировании.

`@runtime_checkable` добавляет поддержку `isinstance()`, но проверяет только наличие методов, не их сигнатуры. Статический анализ через mypy строже: проверяются и имена, и типы параметров, и возвращаемые значения.

Протоколы можно наследовать друг от друга, комбинируя требования. Обобщённые протоколы (`Protocol[T]`) позволяют описать параметризованные интерфейсы — например, репозиторий для любого типа сущности.

В следующем разделе курса — Модуль 6 — мы рассмотрим Data Classes: декоратор `@dataclass`, который использует аннотации типов для автоматической генерации `__init__`, `__repr__`, `__eq__` и других методов.

---

## Вопросы

1. В чём разница между номинальной и структурной типизацией? Как каждая из них реализована в Python?
2. Почему `Protocol` лучше подходит для работы с классами из внешних библиотек, чем ABC?
3. Что делает `@runtime_checkable`? Какое ограничение у него есть по сравнению со статической проверкой mypy?
4. В каких случаях предпочтительнее ABC, а в каких — `Protocol`?
5. Что такое обобщённый протокол `Protocol[T]` и зачем он нужен?
6. Можно ли объявить в протоколе атрибут экземпляра? Как класс может его реализовать?
7. Почему не следует добавлять `__init__` с параметрами в протокол?
8. Если класс имеет метод с правильным именем, но неправильной сигнатурой — пройдёт ли он проверку протокола? В рантайме и при анализе mypy?

---

## Задачи

### Задача 1. 

Объявление и использование протоколов

Объявите следующие протоколы и напишите функции, их использующие:

- `Printable` — объект имеет метод `to_string() -> str`.
- `Comparable` — объект имеет метод `compare_to(other) -> int` (отрицательное если меньше, 0 если равно, положительное если больше).
- `Cacheable` — объект имеет атрибут `cache_key: str` и метод `is_cache_valid() -> bool`.

Сделайте все три протокола `@runtime_checkable`. Создайте три класса без наследования от протоколов — `Temperature`, `Priority`, `APIResponse` — реализующие соответствующие протоколы. Напишите функции `print_item(item: Printable)`, `sort_items(items: list[Comparable])`, `should_update_cache(item: Cacheable) -> bool`. Проверьте `isinstance()` для каждого.

**Пример использования**:

```python
t1 = Temperature(20.5)
t2 = Temperature(-5.0)
p1 = Priority(1, "Critical")
p2 = Priority(3, "Low")
resp = APIResponse("/api/users", {"data": []}, max_age=100)

# isinstance проверки
print(isinstance(t1, Printable))     # True
print(isinstance(t1, Comparable))    # True
print(isinstance(resp, Cacheable))   # True
print(isinstance(t1, Cacheable))     # False

# Функции через протоколы
print_item(t1)
print_item(p1)
print_item(resp)

print(f"Кеш валиден: {not should_update_cache(resp)}")
resp.age(150)
print(f"Кеш валиден после старения: {not should_update_cache(resp)}")
```

---

### Задача 2. 

Протокол для системы уведомлений

Объявите протокол `NotificationChannel`:
- атрибут `channel_name: str`
- метод `send(recipient: str, subject: str, body: str) -> bool`
- метод `is_available() -> bool`

Объявите протокол `NotificationFormatter`:
- метод `format_subject(template: str, data: dict) -> str`
- метод `format_body(template: str, data: dict) -> str`

Создайте без наследования от протоколов:
- `SlackChannel` и `TelegramChannel` — реализуют `NotificationChannel`.
- `HTMLFormatter` и `PlainTextFormatter` — реализуют `NotificationFormatter`.

Напишите функцию `send_notification(channel: NotificationChannel, formatter: NotificationFormatter, recipient: str, subject_template: str, body_template: str, data: dict) -> bool`.

**Пример использования**:

```python
slack = SlackChannel("https://hooks.slack.com/xxx")
telegram = TelegramChannel("bot123:TOKEN")
html_fmt = HTMLFormatter()
plain_fmt = PlainTextFormatter()

data = {"username": "alice", "order_id": 1001}

send_notification(
    slack, plain_fmt, "engineering",
    "Новый заказ #{order_id}",
    "Пользователь {username} оформил заказ #{order_id}",
    data
)

send_notification(
    telegram, html_fmt, "alice_bot",
    "Заказ #{order_id} подтверждён",
    "Привет, {username}! Ваш заказ #{order_id} принят в обработку.",
    data
)
```

---

### Задача 3. 

Обобщённый репозиторий через `Protocol[T]`

Объявите обобщённый протокол `Storage[T]` с методами:
- `get(key: str) -> T | None`
- `set(key: str, value: T) -> None`
- `delete(key: str) -> bool`
- `keys() -> list[str]`

Создайте два класса-реализации без наследования:
- `InMemoryStorage[T]` — хранит в словаре.
- `TTLStorage[T]` — хранит с временем жизни записи.

Напишите обобщённую функцию `copy_storage(source: Storage[T], destination: Storage[T]) -> int`, которая копирует все элементы из одного хранилища в другое и возвращает количество скопированных.

**Пример использования**:

```python
mem1: InMemoryStorage[dict] = InMemoryStorage()
mem2: InMemoryStorage[dict] = InMemoryStorage()
ttl: TTLStorage[dict] = TTLStorage(ttl=60)

mem1.set("user:1", {"name": "Alice"})
mem1.set("user:2", {"name": "Bob"})
mem1.set("user:3", {"name": "Carol"})

copied = copy_storage(mem1, mem2)
print(f"Скопировано: {copied}")
print(f"mem2 keys: {mem2.keys()}")

copied_to_ttl = copy_storage(mem1, ttl)
print(f"Скопировано в TTL: {copied_to_ttl}")
print(f"TTL keys: {ttl.keys()}")
```

---

### Задача 4. 

Протоколы как тест-дублёры

Напишите сервис `OrderService`, зависящий от трёх протоколов:
- `ProductCatalogProtocol` — `get_product(product_id) -> dict | None`, `check_availability(product_id, quantity) -> bool`.
- `PaymentGatewayProtocol` — `charge(amount, currency, card_token) -> dict`.
- `InventoryProtocol` — `reserve(product_id, quantity) -> bool`, `release(product_id, quantity) -> None`.

`OrderService.place_order(user_id, product_id, quantity, card_token)`:
1. Проверяет доступность товара через `ProductCatalogProtocol`.
2. Резервирует через `InventoryProtocol`.
3. Снимает оплату через `PaymentGatewayProtocol`.
4. Если оплата не прошла — освобождает резерв.

Создайте тестовые заглушки для каждого протокола (без наследования). Напишите тест сценария успешного и неуспешного заказа.

**Пример использования**:

```python
# Сценарий 1: Успешный заказ
print("=== Успешный заказ ===")
catalog = FakeCatalog()
payment = FakePayment(should_succeed=True)
inventory = FakeInventory()

service = OrderService(catalog, payment, inventory)
result = service.place_order(user_id=1, product_id=1, quantity=2, card_token="tok_valid")
print(f"Результат: {result}")
print(f"Остаток на складе: {inventory.stock}")

# Сценарий 2: Оплата не прошла
print("\n=== Неуспешная оплата ===")
catalog2 = FakeCatalog()
payment2 = FakePayment(should_succeed=False)
inventory2 = FakeInventory()

service2 = OrderService(catalog2, payment2, inventory2)
result2 = service2.place_order(user_id=1, product_id=1, quantity=1, card_token="tok_decline")
print(f"Результат: {result2}")
print(f"Резерв освобождён: {inventory2.release_calls}")
print(f"Склад восстановлен: {inventory2.stock}")
```

---

### Задача 5. Стандартные протоколы из `collections.abc`

Напишите следующие функции, используя только абстрактные типы из `collections.abc` и `typing`:

1. `flatten(nested: Iterable[Iterable[T]]) -> list[T]` — разворачивает вложенный итерируемый в плоский список.
2. `count_occurrences(items: Iterable[T]) -> Mapping[T, int]` — подсчитывает количество каждого элемента.
3. `apply_to_all(items: Sequence[T], func: Callable[[T], T]) -> list[T]` — применяет функцию к каждому элементу последовательности.
4. `merge_mappings(maps: Iterable[Mapping[str, int]]) -> dict[str, int]` — объединяет словари, суммируя значения при конфликте ключей.

Для каждой функции продемонстрируйте, что она работает с несколькими разными типами, удовлетворяющими протоколу.

**Пример использования**:

```python
# flatten — работает с разными Iterable
print(flatten([[1, 2], [3, 4], [5]]))                # list of lists
print(flatten(((1, 2), (3, 4))))                     # tuple of tuples
print(flatten([range(3), range(3, 6)]))               # list of ranges

# count_occurrences
print(count_occurrences([1, 2, 1, 3, 2, 1]))         # list
print(count_occurrences("hello world"))               # str (Iterable[str])
print(count_occurrences(("a", "b", "a")))            # tuple

# apply_to_all
print(apply_to_all([1, 2, 3], lambda x: x * 2))      # list
print(apply_to_all((1, 2, 3), lambda x: x ** 2))     # tuple
print(apply_to_all("abc", str.upper))                 # str

# merge_mappings
m1 = {"a": 1, "b": 2}
m2 = {"b": 3, "c": 4}
m3 = {"a": 5, "c": 1}
print(merge_mappings([m1, m2, m3]))   # {'a': 6, 'b': 5, 'c': 5}
# Работает и с разными Mapping-подобными объектами
from collections import Counter
print(merge_mappings([Counter("aab"), Counter("bcc")]))
```

---

[Предыдущий урок](lesson28.md) | [Следующий урок](lesson30.md)