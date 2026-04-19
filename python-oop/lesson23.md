# Урок 23. Абстрактные классы: модуль `abc`, `ABC`, `@abstractmethod`

---

## Проблема, которую решают абстрактные классы

В уроке 21 мы разбирали паттерн ` `: базовый класс определяет алгоритм, а дочерние классы переопределяют отдельные шаги. Тогда мы использовали такой подход для «абстрактных» методов:

```python
class DataProcessor:
    def _transform(self, data):
        raise NotImplementedError("Дочерний класс должен реализовать _transform()")
```

Это работает — но только в момент вызова метода. Python не помешает создать объект «незаконченного» класса и не напомнит разработчику, что метод нужно переопределить. Проблема проявится только при выполнении программы, когда уже поздно:

```python
class DataProcessor:
    def process(self, data):
        return self._transform(data)

    def _transform(self, data):
        raise NotImplementedError("Реализуйте _transform()")


# Разработчик забыл реализовать _transform()
class MyProcessor(DataProcessor):
    pass   # не реализовали _transform — Python не жалуется


processor = MyProcessor()   # объект создаётся без ошибок

# Ошибка обнаружится только здесь — возможно, в продакшне
processor.process({"data": "important"})
# NotImplementedError: Реализуйте _transform()
```

В реальном проекте между созданием объекта и вызовом метода может быть много кода. Ошибка обнаруживается поздно — и в самый неудобный момент.

Абстрактные классы решают эту проблему: Python проверяет контракт прямо при создании объекта и немедленно сообщает об ошибке, если дочерний класс не реализовал обязательные методы.

---

## Что такое абстрактный класс

Абстрактный класс — это класс, который:
1. Нельзя инстанциировать напрямую — попытка создать его экземпляр вызовет `TypeError`.
2. Объявляет один или несколько абстрактных методов — методов без реализации, которые обязаны реализовать все дочерние классы.
3. Служит формальным контрактом: любой дочерний класс гарантированно предоставит определённый набор методов.

Ключевое отличие от обычного базового класса с `raise NotImplementedError`:

| | `raise NotImplementedError` | Абстрактный класс (ABC) |
|---|---|---|
| Проверка | В момент вызова | В момент создания объекта |
| Явность контракта | Неформальная | Формальная, задокументированная |
| Защита от создания | Нет | Да |
| IDE-подсказки | Нет | Да |

---

## Модуль `abc` и класс `ABC`

Абстрактные классы в Python реализованы через модуль `abc` (Abstract Base Classes). Есть два способа создать абстрактный класс:

**Способ 1: наследование от `ABC` — рекомендуемый современный синтаксис:**

```python
from abc import ABC, abstractmethod


class MyAbstractClass(ABC):
    @abstractmethod
    def my_method(self):
        pass
```

**Способ 2: явное использование метакласса `ABCMeta` — более низкоуровневый:**

```python
from abc import ABCMeta, abstractmethod


class MyAbstractClass(metaclass=ABCMeta):
    @abstractmethod
    def my_method(self):
        pass
```

Оба способа эквивалентны. `ABC` — это просто вспомогательный класс, определённый как `class ABC(metaclass=ABCMeta): pass`. Он существует для удобства: вместо указания метакласса явно можно просто наследоваться от `ABC`.

Первый способ предпочтительнее в большинстве случаев — он чище и читается естественно: «мой класс является абстрактным базовым классом».

---

## Декоратор `@abstractmethod`

`@abstractmethod` — главный инструмент модуля `abc`. Он помечает метод как абстрактный: дочерний класс обязан его переопределить. Если дочерний класс не реализует хотя бы один абстрактный метод — создать его экземпляр невозможно:

```python
from abc import ABC, abstractmethod


class Shape(ABC):
    """Абстрактный базовый класс для геометрических фигур."""

    @abstractmethod
    def area(self) -> float:
        """Возвращает площадь фигуры."""
        pass

    @abstractmethod
    def perimeter(self) -> float:
        """Возвращает периметр фигуры."""
        pass

    def describe(self):
        """Конкретный метод — реализован в ABC, доступен всем потомкам."""
        return f"Фигура: площадь={self.area():.2f}, периметр={self.perimeter():.2f}"
```

Попытка создать экземпляр абстрактного класса — немедленная ошибка:

```python
try:
    shape = Shape()   # TypeError сразу!
except TypeError as e:
    print(e)
# Can't instantiate abstract class Shape with abstract methods area, perimeter
```

Дочерний класс без реализации всех абстрактных методов — тоже ошибка:

```python
class IncompleteCircle(Shape):
    def area(self):
        return 3.14 * 5 ** 2
    # perimeter не реализован!


try:
    c = IncompleteCircle()   # TypeError!
except TypeError as e:
    print(e)
# Can't instantiate abstract class IncompleteCircle with abstract method perimeter
```

Правильная реализация — все методы переопределены:

```python
import math


class Circle(Shape):
    def __init__(self, radius):
        self.radius = radius

    def area(self) -> float:
        return math.pi * self.radius ** 2

    def perimeter(self) -> float:
        return 2 * math.pi * self.radius


class Rectangle(Shape):
    def __init__(self, width, height):
        self.width = width
        self.height = height

    def area(self) -> float:
        return self.width * self.height

    def perimeter(self) -> float:
        return 2 * (self.width + self.height)


circle = Circle(5)
rect = Rectangle(4, 6)

print(circle.describe())    # Фигура: площадь=78.54, периметр=31.42
print(rect.describe())      # Фигура: площадь=24.00, периметр=20.00

# Полиморфизм: код работает с любой фигурой через общий интерфейс
shapes = [circle, rect, Circle(3)]
total_area = sum(s.area() for s in shapes)
print(f"Суммарная площадь: {total_area:.2f}")   # 131.97
```

Обратите внимание: `describe()` — обычный конкретный метод в абстрактном классе. ABC может иметь любое количество конкретных методов наряду с абстрактными. Абстрактным может быть только тот метод, который помечен `@abstractmethod`.

---

## Частичная реализация абстрактного метода

Важный и часто неизвестный момент: `@abstractmethod` не запрещает писать тело метода в абстрактном классе. Метод всё равно считается абстрактным (дочерний класс обязан его переопределить), но базовая реализация доступна через `super()`.

Это мощный паттерн: абстрактный класс предоставляет базовую логику, а дочерние классы обязаны её расширить:

```python
class BaseValidator(ABC):
    """
    Абстрактный валидатор. Определяет обязательный метод validate().
    Предоставляет базовую реализацию, которую потомки могут расширить через super().
    """

    @abstractmethod
    def validate(self, value):
        """
        Базовая валидация: проверяет, что значение не None.
        Дочерние классы ОБЯЗАНЫ переопределить этот метод,
        но МОГУТ вызвать super() для базовой проверки.
        """
        if value is None:
            raise ValueError("Значение не может быть None")
        return True


class StringValidator(BaseValidator):
    def __init__(self, min_length=0, max_length=None):
        self.min_length = min_length
        self.max_length = max_length

    def validate(self, value):
        super().validate(value)   # запускаем базовую проверку (не None)
        if not isinstance(value, str):
            raise TypeError(f"Ожидается строка, получен {type(value).__name__}")
        if len(value) < self.min_length:
            raise ValueError(f"Строка слишком короткая (минимум {self.min_length})")
        if self.max_length and len(value) > self.max_length:
            raise ValueError(f"Строка слишком длинная (максимум {self.max_length})")
        return True


class EmailValidator(StringValidator):
    def validate(self, value):
        super().validate(value)   # вызывает StringValidator.validate → BaseValidator.validate
        if "@" not in value or "." not in value.split("@")[-1]:
            raise ValueError(f"Некорректный email: {value!r}")
        return True


# EmailValidator обязан реализовывать validate() — он это делает
# Цепочка вызовов через super() гарантирует все проверки
email_v = EmailValidator(min_length=5, max_length=254)

try:
    email_v.validate(None)            # ValueError: Значение не может быть None
except ValueError as e:
    print(e)

try:
    email_v.validate("bad")           # ValueError: Строка слишком короткая
except ValueError as e:
    print(e)

try:
    email_v.validate("notanemail")    # ValueError: Некорректный email
except ValueError as e:
    print(e)

email_v.validate("alice@example.com")   # OK — проходит все три уровня
print("Email прошёл валидацию")
```

---

## Абстрактные свойства, классовые и статические методы

Иногда нужно объявить абстрактным не обычный метод, а свойство (`@property`), классовый метод (`@classmethod`) или статический метод (`@staticmethod`).

**Современный способ** — комбинировать `@abstractmethod` с нужным декоратором. Важно: `@abstractmethod` должен идти **последним** (ближайшим к функции):

```python
from abc import ABC, abstractmethod


class BaseStorage(ABC):
    """Абстрактный класс хранилища данных."""

    @property
    @abstractmethod
    def storage_name(self) -> str:
        """Название хранилища. Должно быть реализовано как property."""
        pass

    @classmethod
    @abstractmethod
    def from_config(cls, config: dict):
        """Фабричный метод создания из конфигурации."""
        pass

    @staticmethod
    @abstractmethod
    def validate_key(key: str) -> bool:
        """Проверка корректности ключа."""
        pass

    @abstractmethod
    def save(self, key: str, value) -> None:
        pass

    @abstractmethod
    def load(self, key: str):
        pass
```

Дочерний класс обязан реализовать все эти методы — включая property и classmethod:

```python
class InMemoryStorage(BaseStorage):
    def __init__(self):
        self._data = {}

    @property
    def storage_name(self) -> str:
        return "InMemory"

    @classmethod
    def from_config(cls, config: dict):
        # config игнорируется — InMemory не требует конфигурации
        return cls()

    @staticmethod
    def validate_key(key: str) -> bool:
        return isinstance(key, str) and len(key) > 0

    def save(self, key: str, value) -> None:
        if not self.validate_key(key):
            raise ValueError(f"Некорректный ключ: {key!r}")
        self._data[key] = value

    def load(self, key: str):
        return self._data.get(key)
```

Устаревшие декораторы `@abstractproperty`, `@abstractclassmethod`, `@abstractstaticmethod` из модуля `abc` deprecated начиная с Python 3.3 и удалены в Python 3.11. Никогда не используйте их в новом коде — только комбинацию `@property + @abstractmethod`.

---

## `__abstractmethods__`: внутренний механизм

Под капотом Python отслеживает нереализованные абстрактные методы через атрибут `__abstractmethods__`. Это `frozenset` имён методов, помеченных как абстрактные и ещё не реализованных в классе:

```python
print(Shape.__abstractmethods__)
# frozenset({'area', 'perimeter'})

print(Circle.__abstractmethods__)
# frozenset() — все методы реализованы, множество пустое

# При создании объекта Python проверяет __abstractmethods__
# Если множество непустое — TypeError
```

Это знание полезно для программной проверки — например, в системе плагинов или при автоматическом тестировании:

```python
def is_concrete(cls):
    """Проверяет, что класс конкретный (готов к инстанциированию)."""
    return not bool(getattr(cls, '__abstractmethods__', set()))


print(is_concrete(Shape))    # False — есть нереализованные методы
print(is_concrete(Circle))   # True — все методы реализованы
print(is_concrete(int))      # True — встроенный тип
```

---

## Регистрация виртуальных подклассов через `register()`

В предыдущем уроке мы видели `__subclasshook__` для автоматической регистрации виртуальных подклассов. ABC предоставляет ещё один механизм — явную регистрацию через метод `register()`:

```python
class Drawable(ABC):
    @abstractmethod
    def draw(self):
        pass


class LegacyWidget:
    """Старый класс из внешней библиотеки — нельзя изменить."""
    def draw(self):
        print("Рисуем старый виджет")


# Регистрируем как виртуальный подкласс
Drawable.register(LegacyWidget)

widget = LegacyWidget()
print(isinstance(widget, Drawable))          # True — зарегистрирован
print(issubclass(LegacyWidget, Drawable))    # True

widget.draw()   # работает
```

Критически важный момент: регистрация через `register()` или `__subclasshook__` **не обязывает** класс реализовывать абстрактные методы. Python «доверяет» вам — предполагается, что вы регистрируете только классы, которые действительно реализуют протокол. Если `LegacyWidget` не имел бы метода `draw()`, он всё равно прошёл бы проверку `isinstance()`, но упал бы при вызове `draw()`.

```python
class EmptyWidget:
    pass   # нет метода draw()


Drawable.register(EmptyWidget)

empty = EmptyWidget()
print(isinstance(empty, Drawable))   # True — зарегистрирован, но...
try:
    empty.draw()   # AttributeError — метода нет!
except AttributeError as e:
    print(e)
```

Это объясняет, почему `register()` используется преимущественно для классов из внешних библиотек, которые реально реализуют нужные методы, но не могут быть изменены.

---

## Практический пример: интерфейс хранилища данных

Абстрактный класс — идеальный инструмент для описания интерфейса, который должны реализовать разные бэкенды. Классический пример: хранилище данных. В реальном проекте может быть несколько реализаций: в памяти (для тестов), файловое (для разработки), база данных (для продакшна).

```python
from abc import ABC, abstractmethod
from typing import Optional, List


class BaseStorage(ABC):
    """
    Абстрактный интерфейс хранилища данных.

    Любой класс, реализующий этот интерфейс, может использоваться
    как хранилище в бизнес-логике приложения — без изменения кода.

    Это принцип Dependency Inversion: бизнес-логика зависит от абстракции,
    а не от конкретной реализации.
    """

    @property
    @abstractmethod
    def storage_name(self) -> str:
        """Человекочитаемое название хранилища."""
        pass

    @abstractmethod
    def save(self, key: str, value: dict) -> None:
        """Сохраняет объект по ключу."""
        pass

    @abstractmethod
    def load(self, key: str) -> Optional[dict]:
        """Загружает объект по ключу. Возвращает None если не найден."""
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        """Удаляет объект. Возвращает True если был удалён."""
        pass

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Проверяет существование ключа."""
        pass

    @abstractmethod
    def keys(self) -> List[str]:
        """Возвращает список всех ключей."""
        pass

    # Конкретные методы доступны всем реализациям
    def save_many(self, items: dict) -> None:
        """Сохраняет несколько объектов за раз."""
        for key, value in items.items():
            self.save(key, value)

    def load_many(self, keys: List[str]) -> dict:
        """Загружает несколько объектов за раз."""
        return {key: self.load(key) for key in keys if self.exists(key)}

    def count(self) -> int:
        """Возвращает количество записей."""
        return len(self.keys())

    def __repr__(self):
        return f"{self.__class__.__name__}(name={self.storage_name!r}, count={self.count()})"


class InMemoryStorage(BaseStorage):
    """Хранилище в памяти. Используется в тестах и для кеширования."""

    def __init__(self):
        self._data: dict = {}

    @property
    def storage_name(self) -> str:
        return "InMemory"

    def save(self, key: str, value: dict) -> None:
        self._data[key] = dict(value)   # копия, не ссылка

    def load(self, key: str) -> Optional[dict]:
        return dict(self._data[key]) if key in self._data else None

    def delete(self, key: str) -> bool:
        if key in self._data:
            del self._data[key]
            return True
        return False

    def exists(self, key: str) -> bool:
        return key in self._data

    def keys(self) -> List[str]:
        return list(self._data.keys())


class LoggedStorage(BaseStorage):
    """
    Декоратор-хранилище: оборачивает другое хранилище, добавляя логирование.
    Сам является конкретным классом BaseStorage.
    """

    def __init__(self, backend: BaseStorage):
        if not isinstance(backend, BaseStorage):
            raise TypeError(
                f"backend должен быть BaseStorage, получен {type(backend).__name__}"
            )
        self._backend = backend

    @property
    def storage_name(self) -> str:
        return f"Logged({self._backend.storage_name})"

    def save(self, key: str, value: dict) -> None:
        print(f"[{self.storage_name}] SAVE key={key!r}")
        self._backend.save(key, value)

    def load(self, key: str) -> Optional[dict]:
        result = self._backend.load(key)
        status = "HIT" if result is not None else "MISS"
        print(f"[{self.storage_name}] LOAD key={key!r} → {status}")
        return result

    def delete(self, key: str) -> bool:
        result = self._backend.delete(key)
        print(f"[{self.storage_name}] DELETE key={key!r} → {'OK' if result else 'NOT FOUND'}")
        return result

    def exists(self, key: str) -> bool:
        return self._backend.exists(key)

    def keys(self) -> List[str]:
        return self._backend.keys()
```

Теперь напишем бизнес-логику, которая не знает о конкретной реализации хранилища:

```python
class UserRepository:
    """
    Репозиторий пользователей.
    Принимает любой BaseStorage — бизнес-логика независима от хранилища.
    """

    def __init__(self, storage: BaseStorage):
        self._storage = storage

    def create_user(self, user_id: str, name: str, email: str) -> dict:
        if self._storage.exists(f"user:{user_id}"):
            raise ValueError(f"Пользователь {user_id} уже существует")
        user = {"id": user_id, "name": name, "email": email}
        self._storage.save(f"user:{user_id}", user)
        return user

    def get_user(self, user_id: str) -> Optional[dict]:
        return self._storage.load(f"user:{user_id}")

    def delete_user(self, user_id: str) -> bool:
        return self._storage.delete(f"user:{user_id}")

    def list_users(self) -> List[dict]:
        user_keys = [k for k in self._storage.keys() if k.startswith("user:")]
        return [self._storage.load(k) for k in user_keys]


# Демонстрация: меняем хранилище без изменения бизнес-логики
print("=== InMemory хранилище ===")
mem_storage = InMemoryStorage()
repo = UserRepository(mem_storage)

repo.create_user("1", "Alice", "alice@example.com")
repo.create_user("2", "Bob", "bob@example.com")

print(repo.get_user("1"))
print(f"Пользователей: {len(repo.list_users())}")
repo.delete_user("2")
print(f"После удаления: {len(repo.list_users())}")

print("\n=== Logged хранилище ===")
logged_storage = LoggedStorage(InMemoryStorage())
logged_repo = UserRepository(logged_storage)

logged_repo.create_user("3", "Carol", "carol@example.com")
logged_repo.get_user("3")
logged_repo.get_user("99")    # MISS — ключ не найден
logged_repo.delete_user("3")

# isinstance работает для всех реализаций
print(isinstance(mem_storage, BaseStorage))     # True
print(isinstance(logged_storage, BaseStorage))  # True
```

---

## Практический пример: интерфейс аутентификации

Второй практический пример — система аутентификации. Django использует именно этот паттерн: несколько бэкендов аутентификации, каждый реализует одинаковый интерфейс:

```python
from abc import ABC, abstractmethod
from typing import Optional
import hashlib
import secrets


class BaseAuthBackend(ABC):
    """
    Абстрактный бэкенд аутентификации.
    Аналог django.contrib.auth.backends.BaseBackend.

    Каждая реализация определяет способ проверки учётных данных:
    база данных, JWT, OAuth, LDAP, API-ключи и т.д.
    """

    @property
    @abstractmethod
    def backend_name(self) -> str:
        """Уникальное имя бэкенда для логирования."""
        pass

    @abstractmethod
    def authenticate(self, credentials: dict) -> Optional[dict]:
        """
        Проверяет учётные данные и возвращает объект пользователя.
        Возвращает None если аутентификация не прошла.

        credentials — словарь с данными: {'username': ..., 'password': ...}
        или {'token': ...} для JWT, и т.д.
        """
        pass

    @abstractmethod
    def get_user(self, user_id: str) -> Optional[dict]:
        """Возвращает пользователя по его ID."""
        pass

    # Конкретный метод — общий для всех бэкендов
    def has_permission(self, user: dict, permission: str) -> bool:
        """Проверяет, имеет ли пользователь указанное разрешение."""
        permissions = user.get("permissions", [])
        return permission in permissions or "superuser" in user.get("roles", [])


class DatabaseAuthBackend(BaseAuthBackend):
    """
    Аутентификация через базу данных.
    Хранит пользователей в словаре (в реальности — запросы к БД).
    """

    def __init__(self):
        # Имитация базы данных пользователей
        self._users_db = {
            "alice": {
                "id": "user_1",
                "username": "alice",
                "password_hash": hashlib.sha256("password123".encode()).hexdigest(),
                "email": "alice@example.com",
                "roles": ["admin"],
                "permissions": ["read", "write", "delete"],
            },
            "bob": {
                "id": "user_2",
                "username": "bob",
                "password_hash": hashlib.sha256("qwerty".encode()).hexdigest(),
                "email": "bob@example.com",
                "roles": ["user"],
                "permissions": ["read"],
            },
        }

    @property
    def backend_name(self) -> str:
        return "DatabaseAuthBackend"

    def authenticate(self, credentials: dict) -> Optional[dict]:
        username = credentials.get("username")
        password = credentials.get("password")

        if not username or not password:
            return None

        user = self._users_db.get(username)
        if not user:
            return None

        password_hash = hashlib.sha256(password.encode()).hexdigest()
        if user["password_hash"] != password_hash:
            return None

        # Возвращаем безопасную копию без хеша пароля
        return {k: v for k, v in user.items() if k != "password_hash"}

    def get_user(self, user_id: str) -> Optional[dict]:
        for user in self._users_db.values():
            if user["id"] == user_id:
                return {k: v for k, v in user.items() if k != "password_hash"}
        return None


class APIKeyAuthBackend(BaseAuthBackend):
    """
    Аутентификация через API-ключ.
    Используется для machine-to-machine взаимодействия.
    """

    def __init__(self):
        self._api_keys = {
            "key_abc123": {
                "id": "service_1",
                "name": "Payment Service",
                "roles": ["service"],
                "permissions": ["read", "write"],
            }
        }

    @property
    def backend_name(self) -> str:
        return "APIKeyAuthBackend"

    def authenticate(self, credentials: dict) -> Optional[dict]:
        api_key = credentials.get("api_key")
        if not api_key:
            return None
        return self._api_keys.get(api_key)

    def get_user(self, user_id: str) -> Optional[dict]:
        for user in self._api_keys.values():
            if user["id"] == user_id:
                return user
        return None


class AuthenticationService:
    """
    Сервис аутентификации. Перебирает зарегистрированные бэкенды
    по порядку — возвращает результат первого успешного.
    """

    def __init__(self, backends: list):
        for backend in backends:
            if not isinstance(backend, BaseAuthBackend):
                raise TypeError(
                    f"Каждый бэкенд должен быть BaseAuthBackend, "
                    f"получен {type(backend).__name__}"
                )
        self._backends = backends

    def authenticate(self, credentials: dict) -> Optional[dict]:
        for backend in self._backends:
            user = backend.authenticate(credentials)
            if user is not None:
                print(f"[Auth] Успех через {backend.backend_name}")
                user["_auth_backend"] = backend.backend_name
                return user
        print("[Auth] Все бэкенды отказали")
        return None

    def check_permission(self, user: dict, permission: str) -> bool:
        backend_name = user.get("_auth_backend")
        for backend in self._backends:
            if backend.backend_name == backend_name:
                return backend.has_permission(user, permission)
        return False
```

Демонстрация:

```python
auth = AuthenticationService(backends=[
    DatabaseAuthBackend(),
    APIKeyAuthBackend(),
])

# Аутентификация пользователя через пароль
user = auth.authenticate({"username": "alice", "password": "password123"})
print(f"Пользователь: {user['username']}")
print(f"Может удалять: {auth.check_permission(user, 'delete')}")

print()

# Аутентификация сервиса через API-ключ
service = auth.authenticate({"api_key": "key_abc123"})
print(f"Сервис: {service['name']}")

print()

# Неудачная аутентификация
result = auth.authenticate({"username": "alice", "password": "wrong"})
print(f"Результат: {result}")   # None

print()

# isinstance работает со всеми бэкендами
backends = [DatabaseAuthBackend(), APIKeyAuthBackend()]
for b in backends:
    print(f"{b.backend_name}: является BaseAuthBackend → {isinstance(b, BaseAuthBackend)}")
```

---

## Когда ABC, а когда `raise NotImplementedError`

Выбор между двумя подходами зависит от контекста:

**Используйте ABC когда:**
- Вы проектируете интерфейс, который должны реализовать другие (плагины, бэкенды, стратегии).
- Хотите получить ошибку на этапе разработки, а не в рантайме.
- Работаете в команде — ABC служит документацией и контрактом.
- Нужна совместимость с `isinstance()` / `issubclass()`.

**Используйте `raise NotImplementedError` когда:**
- Метод является «точкой расширения», но его вызов в базовом классе допустим в некоторых сценариях.
- Хотите дать возможность создавать объект базового класса (например, для тестов с частичной реализацией).
- Класс не является истинным интерфейсом, а лишь предоставляет реализацию по умолчанию с возможностью переопределения.

```python
# Хороший пример для raise NotImplementedError:
class View:
    """Django-подобный базовый view. Можно создать напрямую для тестов."""

    def get(self, request):
        raise NotImplementedError("Реализуйте get() в дочернем классе")

    def post(self, request):
        raise NotImplementedError("Реализуйте post() в дочернем классе")

    def dispatch(self, request, method):
        handler = getattr(self, method.lower(), None)
        if handler:
            return handler(request)
        return {"status": 405}

# Можно создать экземпляр для тестирования dispatch()
view = View()
result = view.dispatch({"path": "/"}, "DELETE")
print(result)   # {'status': 405}
```

---

## Неочевидные моменты и типичные ошибки

**ABC может иметь `__init__` с реализацией.** Нельзя создать экземпляр ABC напрямую — но дочерний класс может вызвать `super().__init__()`:

```python
class BaseModel(ABC):
    def __init__(self, id: str):
        self.id = id                        # общая логика инициализации
        self._created_at = datetime.datetime.now()

    @abstractmethod
    def validate(self) -> bool:
        pass


class UserModel(BaseModel):
    def __init__(self, id: str, username: str):
        super().__init__(id)   # вызываем __init__ ABC
        self.username = username

    def validate(self) -> bool:
        return bool(self.username)


user = UserModel("u1", "alice")
print(user.id)          # u1
print(user.username)    # alice
```

**Дочерний абстрактный класс не обязан реализовывать все методы.** Если дочерний класс сам объявлен как ABC, он может оставить часть методов нереализованной:

```python
class SpecializedStorage(BaseStorage, ABC):
    """
    Промежуточный абстрактный класс.
    Реализует часть методов BaseStorage, но оставляет save() абстрактным.
    """

    def load(self, key: str):
        return self._data.get(key)

    def exists(self, key: str) -> bool:
        return key in self._data

    # save() и другие методы остаются абстрактными
```

**Python не проверяет сигнатуру.** `@abstractmethod` требует только, чтобы метод с таким именем существовал — сигнатура не проверяется:

```python
class WrongImplementation(Shape):
    def area(self, extra_param):   # сигнатура отличается — Python не протестует
        return 0

    def perimeter(self):
        return 0

w = WrongImplementation()   # OK — Python не проверил сигнатуру
print(w.area(0))            # 0
```

Это означает, что контроль сигнатур — ответственность разработчика или статического анализатора (mypy).

**Множественное наследование от нескольких ABC.** Если класс наследует от нескольких ABC, он обязан реализовать все абстрактные методы всех родителей:

```python
class Saveable(ABC):
    @abstractmethod
    def save(self):
        pass


class Loadable(ABC):
    @abstractmethod
    def load(self, key):
        pass


class StorageItem(Saveable, Loadable):
    """Должен реализовать и save(), и load()."""

    def save(self):
        print("Сохранено")

    def load(self, key):
        return {"key": key}


item = StorageItem()   # OK — оба метода реализованы
```

---

## Итоги урока

Абстрактные классы — это формализованный способ описать интерфейс в Python. Три ключевых инструмента: модуль `abc`, класс `ABC` (или метакласс `ABCMeta`) и декоратор `@abstractmethod`.

Класс с хотя бы одним `@abstractmethod` нельзя инстанциировать — Python проверяет `__abstractmethods__` и выбрасывает `TypeError` при любой попытке создания объекта. Дочерний класс обязан реализовать все абстрактные методы, иначе он сам становится абстрактным.

`@abstractmethod` можно комбинировать с `@property`, `@classmethod`, `@staticmethod` — `@abstractmethod` при этом должен идти последним. Абстрактный метод может иметь тело — дочерний класс может вызвать его через `super()`.

Регистрация виртуальных подклассов через `register()` или `__subclasshook__` позволяет классам без реального наследования проходить проверку `isinstance()` — но не обязывает их реализовывать абстрактные методы.

В следующем уроке мы рассмотрим собственные исключения — как создавать иерархии исключений через наследование от `Exception` и как они применяются в веб-приложениях.

---

## Вопросы

1. В чём принципиальное отличие абстрактного класса (ABC) от обычного базового класса с `raise NotImplementedError`? Когда ошибка обнаруживается в каждом случае?
2. Чем `class MyABC(ABC)` отличается от `class MyABC(metaclass=ABCMeta)`? Есть ли функциональная разница?
3. Можно ли написать тело (реализацию) у абстрактного метода? Как дочерний класс может им воспользоваться?
4. Что такое `__abstractmethods__` и как Python его использует?
5. Как правильно объявить абстрактное свойство (`@property`) и почему нельзя использовать устаревший `@abstractproperty`?
6. Виртуальный подкласс, зарегистрированный через `register()`, обязан ли реализовывать абстрактные методы родительского ABC?
7. Может ли дочерний класс ABC не реализовывать все абстрактные методы родителя? В каком случае это допустимо?
8. Проверяет ли Python сигнатуру метода при реализации абстрактного метода в дочернем классе?

---

## Задачи

### **Задача 1**. 

Абстрактный класс `Shape`

Создайте абстрактный класс `Shape` с абстрактными методами `area() -> float`, `perimeter() -> float`, абстрактным свойством `name -> str` и конкретным методом `describe()`, возвращающим строку `"Фигура: {name}, площадь: {area:.4f}, периметр: {perimeter:.4f}"`. 

Реализуйте три конкретных класса:
- `Circle(Shape)` — принимает `radius`. `name = "Окружность"`.
- `Rectangle(Shape)` — принимает `width` и `height`. `name = "Прямоугольник"`.
- `Triangle(Shape)` — принимает три стороны `a`, `b`, `c`. `name = "Треугольник"`. Для площади используйте формулу Герона. Если стороны не образуют корректный треугольник — выбрасывать `ValueError` в `__init__`.

Напишите функцию `print_shapes_info(shapes)`, которая выводит информацию обо всех фигурах и суммарную площадь.

**Формула**:

```
S = sqrt(p * (p - a) * (p - b) * (p - c))
```

где p:

```
p = (a + b + c) / 2
```

---

**Пример использования**:

```python
shapes = [Circle(5), Rectangle(4, 6), Triangle(3, 4, 5)]

try:
    Shape()   # TypeError
except TypeError as e:
    print(e)

print_shapes_info(shapes)
# Фигура: Окружность, площадь: 78.5398, периметр: 31.4159
# Фигура: Прямоугольник, площадь: 24.0000, периметр: 20.0000
# Фигура: Треугольник, площадь: 6.0000, периметр: 12.0000
# Суммарная площадь: 108.54
```

---

### **Задача 2**. 

Абстрактный класс `PaymentGateway`

Создайте абстрактный класс `PaymentGateway` для платёжных шлюзов. 

Абстрактные методы: 
- `charge(amount, currency, card_token) -> dict` (списание), 
- `refund(transaction_id, amount) -> dict` (возврат). 

Абстрактное свойство: 
- `gateway_name -> str`. 

Конкретный метод: 
- `process_order(order: dict) -> dict` — обрабатывает заказ: проверяет наличие полей `amount`, `currency`, `card_token`, вызывает `charge()`, при успехе возвращает `{"success": True, "transaction": result}`, при исключении — `{"success": False, "error": str(e)}`.

Реализуйте два шлюза:
- `StripeGateway` — всегда успешно списывает. 
  - Метод `charge` генерирует ответ (словарь) с полями:
    -  `transaction_id` ("stripe_" + str(amount)),
    -  `amount`,
    -  `currency`,
    -  `status`, всегда равный `"succeeded"`.
  - Метод `refund` добавляет к имитации ответа:
    - `transaction_id`,
    - `refunded`, всегда равный `True`,
    - `amount`
- `FailingGateway` — всегда выбрасывает `RuntimeError("Payment declined")` при `charge()` и `RuntimeError("Refund not available")` при `refund()`.

**Пример использования**:

```python
stripe = StripeGateway()
failing = FailingGateway()

order = {"amount": 1500, "currency": "RUB", "card_token": "tok_abc"}
print(stripe.process_order(order))
# {'success': True, 'transaction': {'transaction_id': 'stripe_1500', ...}}

print(failing.process_order(order))
# {'success': False, 'error': 'Payment declined'}

print(isinstance(stripe, PaymentGateway))   # True
```

---

### **Задача 3**. 

Абстрактная цепочка валидаторов

Создайте абстрактный класс `BaseValidator` с абстрактным методом `validate(value) -> bool` и частичной реализацией: базовый `validate()` проверяет `value is not None` и выбрасывает `ValueError("Значение не может быть None")` если это не так, или возвращает `True`. Конкретный метод `is_valid(value) -> bool` — обёртка, перехватывающая `ValueError` и возвращающая `False`.

Реализуйте три валидатора:
- `LengthValidator(min_len, max_len)` — проверяет длину строки.
- `PatternValidator(pattern)` — проверяет строку на соответствие регулярному выражению. Работа с регулярными выражениями в Python осуществляется с помощью модуля `re`. Для создания шаблона регулярного выражения можно использовать `re.compile(pattern)`. Для проверки строки на соответствие этому шаблону можно использовать `pattern.match(value)` или `pattern.fullmatch(value)`.
- `RangeValidator(min_val, max_val)` — проверяет числовое значение.

Создайте `CompositeValidator(validators)` — также наследует `BaseValidator`, принимает список валидаторов. Метод `validate(value)` запускает все валидаторы и собирает все ошибки в список, затем если ошибки есть — выбрасывает `ValueError` со всеми сообщениями через `; `.

**Пример использования**:

```python
validator = CompositeValidator([
    LengthValidator(3, 20),
    PatternValidator(r'^[a-zA-Z0-9_]+$'),
])

print(validator.is_valid("alice_123"))   # True
print(validator.is_valid("ab"))          # False — слишком короткое
print(validator.is_valid("alice @123")) # False — запрещённый символ

try:
    validator.validate("ab!")
except ValueError as e:
    print(e)   # Строка слишком короткая (мин. 3); Недопустимые символы
```

---

### **Задача 4**. 

Абстрактный класс `ReportGenerator`

Создайте абстрактный класс `ReportGenerator` для генерации отчётов. Абстрактные методы: `_prepare_data(raw_data) -> list` (подготовка данных), `_format_report(data) -> str` (форматирование). Абстрактное свойство: `report_type -> str`. Конкретный шаблонный метод: `generate(raw_data) -> str` — вызывает `_prepare_data()`, затем `_format_report()`, добавляет заголовок с `report_type` и датой.

Реализуйте три генератора:
- `CSVReportGenerator` — форматирует данные как CSV.
- `JSONReportGenerator` — форматирует данные как JSON.
- `SummaryReportGenerator` — форматирует сводную статистику: количество, минимум, максимум, среднее по числовым полям .

Все три принимают список словарей как `raw_data`. `_prepare_data()` может делать очистку: убирать `None`-значения, приводить ключи к нижнему регистру.

**Пример использования**:

```python
data = [
    {"Name": "Alice", "Age": 30, "Salary": 150000},
    {"Name": "Bob",   "Age": None, "Salary": 120000},
    {"Name": "Carol", "Age": 25, "Salary": 180000},
]

csv_gen = CSVReportGenerator()
json_gen = JSONReportGenerator()
summary_gen = SummaryReportGenerator()

print(csv_gen.generate(data))
print(json_gen.generate(data))
print(summary_gen.generate(data))
```

---

### **Задача 5**. 

Регистрация виртуальных подклассов

Создайте ABC `Printable` с абстрактным методом `to_print() -> str` и `__subclasshook__`, который возвращает `True` для любого класса с методом `to_print`. Создайте ABC `Comparable` с абстрактным методом `compare_key()` и `__subclasshook__` для метода `compare_key`. Создайте три класса:
- `Product` — наследует `Printable`, `Comparable`. Имеет `name`, `price`. `to_print()` → `"Product: name (price)"`. `compare_key()` → `price`.
- `LegacyItem` — НЕ наследует ни от чего, но имеет `to_print()` и `compare_key()`.
- `SimpleTag` — НЕ наследует ни от чего, имеет только `to_print()`.

Напишите функцию `print_all(items)`, которая принимает список любых объектов, проверяет `isinstance(item, Printable)` и выводит те, что поддерживают протокол. Напишите функцию `sort_by_key(items)`, которая принимает список, фильтрует `isinstance(item, Comparable)`, сортирует и возвращает.

Пример использования:

```python
items = [
    Product("Ноутбук", 89990),
    Product("Мышь", 1500),
    LegacyItem("old", 500),
    SimpleTag("python"),
    "just a string",
    42,
]

print_all(items)     # выводит Product, LegacyItem, SimpleTag — все Printable
sort_by_key(items)   # сортирует Product и LegacyItem — только Comparable
```

---

### **Задача 6**. 

Система плагинов

Создайте систему плагинов для обработки файлов. Абстрактный класс `FileProcessor` с:
- абстрактным свойством `supported_extensions -> list` (список расширений, например `['.txt', '.md']`),
- абстрактным методом `process(filepath: str, content: str) -> str` (обработка содержимого),
- конкретным методом `can_handle(filepath: str) -> bool` — проверяет, входит ли расширение файла в `supported_extensions`,
- конкретным методом `handle(filepath: str, content: str) -> dict` — вызывает `process()`, возвращает словарь с `filepath`, `processor`, `result`.

Реализуйте три процессора:
- `MarkdownProcessor` — `['.md']`: добавляет HTML-обёртку `<article>...</article>`.
- `TextProcessor` — `['.txt']`: приводит текст к верхнему регистру и подсчитывает слова, возвращает `"WORDS: N\n{text.upper()}"`.
- `LogProcessor` — `['.log']`: фильтрует строки, содержащие `"ERROR"`, возвращает только их.

Создайте класс `ProcessorRegistry` со методами `register(processor)` и `process_file(filepath, content)`: ищет подходящий процессор через `can_handle()`, вызывает его или возвращает `{"error": "No processor found"}`.

Проверьте, что нельзя зарегистрировать объект, не являющийся `FileProcessor`.

**Пример использования**:

```python
registry = ProcessorRegistry()
registry.register(MarkdownProcessor())
registry.register(TextProcessor())
registry.register(LogProcessor())

print(registry.process_file("readme.md", "# Hello\nWorld"))
# {'filepath': 'readme.md', 'processor': 'MarkdownProcessor', 'result': '<article># Hello\nWorld</article>'}

print(registry.process_file("notes.txt", "hello world python"))
print(registry.process_file("app.log", "INFO ok\nERROR fail\nDEBUG x\nERROR crash"))
print(registry.process_file("data.csv", "a,b,c"))   # No processor found
```

---

[Предыдущий урок](lesson22.md) | [Следующий урок](lesson24.md)