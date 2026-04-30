# Урок 28. Аннотации типов в Python: зачем и как использовать

---

## Зачем нужны аннотации типов в динамическом языке

Python — динамически типизированный язык. Переменная не имеет фиксированного типа, и это даёт гибкость: одна и та же переменная может хранить целое число, строку, список — в зависимости от контекста. Но эта гибкость имеет цену.

Рассмотрим функцию без аннотаций:

```python
def process_order(user, items, discount):
    total = sum(item["price"] * item["qty"] for item in items)
    final = total * (1 - discount)
    send_confirmation(user["email"], final)
    return final
```

Что принимает эта функция? Что такое `user` — словарь? Объект класса? Что такое `items` — список словарей? Объектов? Что такое `discount` — число от 0 до 1? Процент от 0 до 100? Что возвращает функция — `float`? Строку?

На эти вопросы нельзя ответить, не читая тело функции целиком. А при большой кодовой базе это становится серьёзной проблемой: разработчик вынужден каждый раз «разгадывать» намерения автора.

Теперь та же функция с аннотациями:

```python
from typing import Optional
from decimal import Decimal


def process_order(
    user: dict,
    items: list[dict],
    discount: float,
) -> Decimal:
    total = sum(Decimal(str(item["price"])) * item["qty"] for item in items)
    final = total * Decimal(str(1 - discount))
    send_confirmation(user["email"], final)
    return final
```

Теперь сразу понятно: `user` — словарь, `items` — список словарей, `discount` — число с плавающей точкой (от 0 до 1), возвращает `Decimal`. Это документация, встроенная непосредственно в сигнатуру функции.

Три главных преимущества аннотаций:

**Первое — читаемость.** Контракт функции виден без чтения её тела. Другой разработчик (и вы сами через месяц) сразу понимает, что ожидать.

**Второе — инструментальная поддержка.** IDE (PyCharm, VS Code с Pylance) использует аннотации для автодополнения и проверки. Вы получаете подсказки методов, предупреждения о несовместимых типах прямо в редакторе.

**Третье — статический анализ.** Инструменты вроде mypy находят ошибки типов до запуска программы — аналог компилятора в статически типизированных языках.

Критически важно понять: **Python не проверяет аннотации в рантайме**. Это подсказки для разработчика и инструментов, а не ограничения. Вы можете передать строку в функцию, аннотированную `int`, — Python не выдаст ошибку. Проверку выполняет mypy или IDE.

---

## Базовый синтаксис аннотаций

### Аннотации функций

```python
# Аннотация параметров и возвращаемого значения
def add(x: int, y: int) -> int:
    return x + y


def greet(name: str) -> str:
    return f"Привет, {name}!"


def is_valid_email(email: str) -> bool:
    return "@" in email and "." in email.split("@")[-1]


# Функция, ничего не возвращающая — аннотируется -> None
def log_message(message: str, level: str = "INFO") -> None:
    print(f"[{level}] {message}")
```

### Аннотации переменных

```python
# Аннотация переменной без значения (объявление намерения)
user_id: int
username: str

# Аннотация с присваиванием
max_connections: int = 100
service_name: str = "UserService"
debug_mode: bool = False
```

### Как Python хранит аннотации

Аннотации хранятся в атрибуте `__annotations__` и **не проверяются в рантайме**:

```python
def process(user_id: int, action: str) -> dict:
    return {}


print(process.__annotations__)
# {'user_id': <class 'int'>, 'action': <class 'str'>, 'return': <class 'dict'>}

# Python НЕ проверяет типы — передаём строку вместо int
result = process("not_an_int", "login")   # работает без ошибок!
print(result)   # {}
```

Для класса:

```python
class User:
    id: int
    username: str
    email: str
    is_active: bool = True


print(User.__annotations__)
# {'id': <class 'int'>, 'username': <class 'str'>,
#  'email': <class 'str'>, 'is_active': <class 'bool'>}
```

---

## Встроенные типы для аннотаций

Начиная с Python 3.9, встроенные типы коллекций можно использовать напрямую для аннотаций:

```python
# Python 3.9+: встроенные типы с параметрами
def process_users(users: list[dict]) -> dict[str, int]:
    return {u["username"]: u["id"] for u in users}


def get_tags(post_id: int) -> set[str]:
    return {"python", "web"}


def get_coordinates() -> tuple[float, float]:
    return (55.75, 37.62)
```

До Python 3.9 нужно было импортировать типы из `typing`:

```python
# Python 3.8 и старше — нужен импорт из typing
from typing import List, Dict, Set, Tuple

def process_users(users: List[Dict]) -> Dict[str, int]:
    return {}
```

Сейчас (Python 3.9+) использование `List`, `Dict`, `Set`, `Tuple` из `typing` считается устаревшим, хотя всё ещё работает. Предпочтительны строчные встроенные типы.

**Практическое правило**: если ваш проект поддерживает Python 3.9+, используйте `list[T]`, `dict[K, V]`, `set[T]`. Если нужна совместимость с 3.8 — используйте `from __future__ import annotations` в начале файла:

```python
from __future__ import annotations   # откладывает вычисление аннотаций
# Теперь можно использовать list[T] даже в Python 3.8
```

---

## Модуль `typing`: расширенные типы

Модуль `typing` предоставляет инструменты для более точных аннотаций.

### `Optional[T]`

`Optional[T]` означает «значение типа T или None». Это эквивалент `Union[T, None]`:

```python
from typing import Optional


def find_user(user_id: int) -> Optional[dict]:
    """Возвращает пользователя или None, если не найден."""
    users = {1: {"id": 1, "name": "Alice"}}
    return users.get(user_id)


user = find_user(1)
if user is not None:   # нужно проверить перед использованием
    print(user["name"])

missing = find_user(99)
print(missing)   # None
```

В Python 3.10+ можно использовать `T | None` вместо `Optional[T]`:

```python
def find_user(user_id: int) -> dict | None:   # Python 3.10+
    ...
```

### `Union[T1, T2]`

`Union` указывает, что значение может быть одним из нескольких типов:

```python
from typing import Union


def parse_id(value: Union[str, int]) -> int:
    """Принимает id как строку или число, возвращает число."""
    if isinstance(value, str):
        return int(value)
    return value


print(parse_id("42"))   # 42
print(parse_id(42))     # 42
```

В Python 3.10+:

```python
def parse_id(value: str | int) -> int:
    ...
```

### `Any`

`Any` отключает проверку типов для данного значения. Используйте с осторожностью:

```python
from typing import Any


def process_raw_data(data: Any) -> None:
    """Принимает данные любого типа — не знаем заранее."""
    print(type(data), data)
```

### `Callable`

Для аннотации функций как аргументов или возвращаемых значений:

```python
from typing import Callable


def apply_transform(
    data: list[int],
    transform: Callable[[int], int]
) -> list[int]:
    """Применяет функцию-трансформер к каждому элементу."""
    return [transform(x) for x in data]


result = apply_transform([1, 2, 3], lambda x: x * 2)
print(result)   # [2, 4, 6]


# Более сложная сигнатура: функция с несколькими аргументами
def retry(
    func: Callable[..., Any],   # ... означает любые аргументы
    max_attempts: int = 3
) -> Callable[..., Any]:
    ...
```

### `Type[T]`

Когда функция принимает сам класс (не экземпляр):

```python
from typing import Type


class User:
    def __init__(self, name: str):
        self.name = name


def create_instance(cls: Type[User], name: str) -> User:
    """Принимает класс, возвращает его экземпляр."""
    return cls(name)


user = create_instance(User, "Alice")
```

---

## Работа с коллекциями: детали

### `list`, `dict`, `set`

```python
# Список строк
def get_usernames(users: list[dict]) -> list[str]:
    return [u["username"] for u in users]


# Словарь с конкретными типами ключей и значений
def count_by_status(orders: list[dict]) -> dict[str, int]:
    result: dict[str, int] = {}
    for order in orders:
        status = order["status"]
        result[status] = result.get(status, 0) + 1
    return result


# Множество уникальных значений
def get_unique_emails(users: list[dict]) -> set[str]:
    return {u["email"] for u in users}
```

### `tuple`: особый случай

Кортеж может быть аннотирован двумя способами:

```python
# Фиксированная длина и типы: (int, str, bool)
def get_user_record(user_id: int) -> tuple[int, str, bool]:
    return (user_id, "alice", True)


# Однородный кортеж произвольной длины: tuple[int, ...]
def get_ids() -> tuple[int, ...]:
    return (1, 2, 3, 4, 5)
```

### Абстрактные типы для обобщённых функций

Когда функция должна работать с разными типами коллекций:

```python
from typing import Iterable, Sequence, Mapping


def print_all(items: Iterable[str]) -> None:
    """Принимает любой итерируемый объект строк: list, tuple, generator..."""
    for item in items:
        print(item)


def first(sequence: Sequence[int]) -> int | None:
    """Принимает любую последовательность (list, tuple, str) — не только list."""
    return sequence[0] if sequence else None


def get_value(mapping: Mapping[str, int], key: str) -> int:
    """Принимает любой словарь-подобный объект."""
    return mapping.get(key, 0)
```

`Iterable`, `Sequence`, `Mapping` более гибки, чем `list`, `tuple`, `dict`. Функция, принимающая `Iterable[str]`, работает со списком, кортежем, генератором, множеством — с любым итерируемым.

---

## `Literal`: конкретные значения

`Literal` позволяет указать, что параметр принимает только конкретные значения:

```python
from typing import Literal


def make_request(
    method: Literal["GET", "POST", "PUT", "DELETE", "PATCH"],
    url: str,
    body: dict | None = None
) -> dict:
    """Принимает только стандартные HTTP-методы."""
    ...


def set_log_level(level: Literal["DEBUG", "INFO", "WARNING", "ERROR"]) -> None:
    ...


def get_order_status() -> Literal["pending", "confirmed", "shipped", "delivered", "cancelled"]:
    ...
```

mypy проверит: если вы вызовете `make_request("CONNECT", "/api")`, это будет ошибкой типа. `Literal` — мощный инструмент для документирования возможных значений и их проверки.

---

## Аннотации в классах и прямые ссылки

### Аннотации атрибутов и методов

```python
class UserService:
    # Атрибуты класса — аннотируются на уровне класса
    _cache: dict[int, dict]
    _max_cache_size: int = 1000

    def __init__(self, database_url: str) -> None:
        self.database_url: str = database_url
        self._cache: dict[int, dict] = {}

    def get_user(self, user_id: int) -> dict | None:
        return self._cache.get(user_id)

    def create_user(self, username: str, email: str) -> dict:
        user = {"id": len(self._cache) + 1, "username": username, "email": email}
        self._cache[user["id"]] = user
        return user

    def get_all_users(self) -> list[dict]:
        return list(self._cache.values())
```

### Прямые ссылки (forward references)

Проблема возникает, когда метод возвращает экземпляр своего же класса (фабричный метод):

```python
class User:
    def __init__(self, name: str, email: str) -> None:
        self.name = name
        self.email = email

    @classmethod
    def from_dict(cls, data: dict) -> "User":   # строка-ссылка!
        return cls(data["name"], data["email"])

    def copy(self) -> "User":   # тоже строка
        return User(self.name, self.email)
```

Проблема: в момент объявления класс `User` ещё не определён полностью, поэтому `-> User` вызовет `NameError`. Решение — строковая аннотация `"User"`.

В Python 3.11+ добавили `Self` из `typing`:

```python
from typing import Self


class User:
    @classmethod
    def from_dict(cls, data: dict) -> Self:   # Python 3.11+
        return cls(data["name"], data["email"])
```

Или используйте `from __future__ import annotations` — тогда все аннотации автоматически становятся строками:

```python
from __future__ import annotations


class User:
    @classmethod
    def from_dict(cls, data: dict) -> User:   # работает без кавычек
        return cls(data["name"], data["email"])
```

---

## `TypeVar`: обобщённое программирование

`TypeVar` позволяет создавать функции, которые работают с разными типами, сохраняя связь между типами аргументов и возвращаемого значения:

```python
from typing import TypeVar

T = TypeVar('T')


def first_item(items: list[T]) -> T | None:
    """Возвращает первый элемент списка того же типа."""
    return items[0] if items else None


# mypy знает: если передать list[int], вернётся int | None
result_int: int | None = first_item([1, 2, 3])
result_str: str | None = first_item(["a", "b", "c"])
```

`TypeVar` с ограничениями:

```python
# T может быть только int или float
Numeric = TypeVar('Numeric', int, float)


def double(value: Numeric) -> Numeric:
    return value * 2


print(double(5))     # 10
print(double(3.14))  # 6.28


# T ограничен сверху — должен быть подклассом BaseModel
from typing import TypeVar

BM = TypeVar('BM', bound='BaseModel')


class BaseModel:
    def save(self) -> None:
        ...


def save_and_return(model: BM) -> BM:
    """Сохраняет и возвращает объект того же типа."""
    model.save()
    return model
```

---

## `TYPE_CHECKING`: импорты только для проверки типов

Циклические импорты — распространённая проблема при аннотировании. Если `users.py` импортирует из `orders.py`, а `orders.py` — из `users.py`, возникает цикл. `TYPE_CHECKING` — константа, которая `False` в рантайме, но `True` при анализе mypy:

```python
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from orders import Order   # импортируется только при анализе mypy, не в рантайме


class User:
    def __init__(self, name: str) -> None:
        self.name = name
        self.orders: list[Order] = []   # Order используется только как аннотация

    def add_order(self, order: Order) -> None:
        self.orders.append(order)
```

При запуске программы `from orders import Order` не выполняется — цикла нет. mypy при анализе видит этот импорт и проверяет типы корректно.

---

## Практический пример: полностью аннотированный сервис

Реализуем полноценный сервис с аннотациями типов:

```python
from __future__ import annotations

from typing import Optional, TypeVar
from dataclasses import dataclass, field
import datetime


@dataclass
class UserRecord:
    """Запись пользователя."""
    id: int
    username: str
    email: str
    is_active: bool = True
    created_at: datetime.datetime = field(default_factory=datetime.datetime.now)
    roles: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
            "roles": self.roles,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> UserRecord:
        return cls(
            id=int(data["id"]),
            username=str(data["username"]),
            email=str(data["email"]),
            is_active=bool(data.get("is_active", True)),
            roles=list(data.get("roles", [])),
        )


@dataclass
class CreateUserRequest:
    """DTO для создания пользователя."""
    username: str
    email: str
    password: str
    roles: list[str] = field(default_factory=list)


@dataclass
class UpdateUserRequest:
    """DTO для обновления пользователя."""
    username: str | None = None
    email: str | None = None
    is_active: bool | None = None
    roles: list[str] | None = None


class UserServiceError(Exception):
    """Базовая ошибка сервиса пользователей."""
    pass


class UserNotFoundError(UserServiceError):
    def __init__(self, user_id: int) -> None:
        super().__init__(f"Пользователь с id={user_id} не найден")
        self.user_id = user_id


class UserAlreadyExistsError(UserServiceError):
    def __init__(self, username: str) -> None:
        super().__init__(f"Пользователь {username!r} уже существует")
        self.username = username


class UserService:
    """
    Сервис управления пользователями.
    Все методы полностью аннотированы.
    """

    def __init__(self) -> None:
        self._storage: dict[int, UserRecord] = {}
        self._username_index: dict[str, int] = {}   # username → id
        self._next_id: int = 1

    def create_user(self, request: CreateUserRequest) -> UserRecord:
        """
        Создаёт нового пользователя.
        Выбрасывает UserAlreadyExistsError если username занят.
        """
        if request.username in self._username_index:
            raise UserAlreadyExistsError(request.username)

        user = UserRecord(
            id=self._next_id,
            username=request.username,
            email=request.email,
            roles=request.roles,
        )
        self._storage[user.id] = user
        self._username_index[user.username] = user.id
        self._next_id += 1
        return user

    def get_user(self, user_id: int) -> UserRecord | None:
        """Возвращает пользователя по id или None."""
        return self._storage.get(user_id)

    def get_user_or_raise(self, user_id: int) -> UserRecord:
        """Возвращает пользователя или выбрасывает UserNotFoundError."""
        user = self.get_user(user_id)
        if user is None:
            raise UserNotFoundError(user_id)
        return user

    def find_by_username(self, username: str) -> UserRecord | None:
        """Ищет пользователя по имени пользователя."""
        user_id = self._username_index.get(username)
        if user_id is None:
            return None
        return self._storage.get(user_id)

    def update_user(self, user_id: int, request: UpdateUserRequest) -> UserRecord:
        """Обновляет данные пользователя."""
        user = self.get_user_or_raise(user_id)

        if request.username is not None:
            if request.username != user.username:
                if request.username in self._username_index:
                    raise UserAlreadyExistsError(request.username)
                del self._username_index[user.username]
                user.username = request.username
                self._username_index[user.username] = user_id

        if request.email is not None:
            user.email = request.email

        if request.is_active is not None:
            user.is_active = request.is_active

        if request.roles is not None:
            user.roles = request.roles

        return user

    def delete_user(self, user_id: int) -> bool:
        """Удаляет пользователя. Возвращает True если был удалён."""
        user = self.get_user(user_id)
        if user is None:
            return False
        del self._storage[user_id]
        del self._username_index[user.username]
        return True

    def list_users(
        self,
        is_active: bool | None = None,
        roles: list[str] | None = None,
    ) -> list[UserRecord]:
        """
        Возвращает список пользователей с фильтрацией.
        Все параметры опциональны.
        """
        users = list(self._storage.values())

        if is_active is not None:
            users = [u for u in users if u.is_active == is_active]

        if roles is not None:
            users = [u for u in users if any(r in u.roles for r in roles)]

        return users

    def count(self) -> int:
        """Возвращает количество пользователей."""
        return len(self._storage)

    @staticmethod
    def validate_email(email: str) -> bool:
        """Базовая валидация email."""
        return "@" in email and "." in email.split("@")[-1]


# Демонстрация
def demonstrate_service() -> None:
    service = UserService()

    # Создание пользователей
    alice = service.create_user(CreateUserRequest(
        username="alice",
        email="alice@example.com",
        password="secure123",
        roles=["admin", "user"],
    ))
    bob = service.create_user(CreateUserRequest(
        username="bob",
        email="bob@example.com",
        password="password456",
    ))

    print(f"Создано пользователей: {service.count()}")
    print(f"Alice: {alice.to_dict()}")

    # Поиск
    found = service.get_user(1)
    print(f"Найден: {found.username if found else None}")

    not_found = service.get_user(99)
    print(f"Не найден: {not_found}")

    # Обновление
    updated = service.update_user(2, UpdateUserRequest(roles=["moderator"]))
    print(f"Bob после обновления: {updated.roles}")

    # Список с фильтром
    all_users = service.list_users()
    print(f"Всего пользователей: {len(all_users)}")

    admins = service.list_users(roles=["admin"])
    print(f"Администраторов: {len(admins)}")

    # Ошибка при дублировании
    try:
        service.create_user(CreateUserRequest(
            username="alice", email="other@example.com", password="pass"
        ))
    except UserAlreadyExistsError as e:
        print(f"Ошибка: {e}")

    # Ошибка при поиске несуществующего
    try:
        service.get_user_or_raise(99)
    except UserNotFoundError as e:
        print(f"Ошибка: {e}")


demonstrate_service()
```

---

## Инструменты статического анализа

Аннотации типов становятся по-настоящему полезными в связке с инструментами статического анализа.

**mypy** — самый популярный статический анализатор типов для Python:

```bash
pip install mypy
mypy my_module.py
```

Пример ошибок, которые находит mypy:

```python
# error.py
def add(x: int, y: int) -> int:
    return x + y

result = add("hello", 5)   # mypy: Argument 1 has incompatible type "str"; expected "int"
result2: str = add(1, 2)   # mypy: Incompatible types in assignment (str vs int)
```

Конфигурация через `mypy.ini`:

```ini
[mypy]
python_version = 3.11
strict = True              ; включает все строгие проверки
warn_return_any = True     ; предупреждать при возврате Any
warn_unused_imports = True
```

Режим `--strict` включает самый строгий набор проверок. Для нового проекта рекомендуется начать с него. Для существующего — начать с базовых проверок и постепенно добавлять строгость.

**Pyright** (используется в VS Code через расширение Pylance) — более быстрый альтернативный анализатор от Microsoft. Многие разработчики используют оба: mypy в CI, Pylance в IDE.

---

## Неочевидные моменты и типичные ошибки

**`list[int]` vs `List[int]`.** После Python 3.9 `list[int]` — правильный вариант. `List[int]` из `typing` устарел, но работает. С `from __future__ import annotations` `list[int]` работает и в Python 3.8.

**`Optional[Optional[T]]` — это просто `Optional[T]`.** Вложенные `Optional` не имеют смысла — `Union[Union[T, None], None]` упрощается до `Union[T, None]`. mypy это понимает.

**`None` как тип.** `-> None` означает «функция ничего не возвращает (возвращает объект None)». `None` в аннотации — это не `type(None)`, а специальный синтаксис для аннотаций. Если нужен `NoneType` в `Union`, используйте `None`: `Union[str, None]` или `str | None`.

**Не аннотировать `self` и `cls`.** Аннотировать `self: User` не принято и не нужно — mypy это понимает из контекста.

**`Any` не значит «всё проверено».** `Any` буквально отключает проверки для данной переменной. Это антипаттерн при неосторожном использовании. Предпочтительнее использовать конкретные типы или обобщённые (`TypeVar`).

**Аннотация `-> None` важна.** Хотя Python по умолчанию возвращает `None` из функций без `return`, явная аннотация `-> None` сигнализирует: «эта функция намеренно ничего не возвращает». mypy в строгом режиме требует этой аннотации.

---

## Итоги урока

Аннотации типов — это документация, встроенная в код, и инструмент статического анализа. Python не проверяет их в рантайме — это задача mypy, pyright и IDE.

Базовый синтаксис: `param: type`, `-> return_type`, `var: type = value`. Аннотации хранятся в `__annotations__`.

Для коллекций в Python 3.9+ используйте встроенные типы: `list[T]`, `dict[K, V]`, `set[T]`, `tuple[T, ...]`. До 3.9 или для совместимости — `from __future__ import annotations`.

`Optional[T]` (или `T | None`) — для nullable значений. `Union[T1, T2]` (или `T1 | T2`) — для нескольких возможных типов. `Literal[val1, val2]` — для конкретных значений. `Callable[[args], ret]` — для функций. `TypeVar` — для обобщённого программирования.

Прямые ссылки решаются строками (`"ClassName"`) или `from __future__ import annotations`. `TYPE_CHECKING` помогает избежать циклических импортов при аннотировании.

В следующем уроке мы рассмотрим протоколы — механизм `Protocol` из модуля `typing`, который является формализованной версией duck typing: он позволяет описать интерфейс через аннотации типов, не требуя явного наследования.

---

## Вопросы

**Вопрос 1.** Что происходит, если передать в функцию с аннотацией `def f(x: int)` строку вместо числа? Проверяет ли Python аннотации в рантайме?
**Вопрос 2.** В чём разница между `list[int]` и `List[int]` из `typing`? Когда что использовать?
**Вопрос 3.** Что такое `Optional[T]` и чем оно отличается от `T | None`? Когда нужно делать проверку на None?
**Вопрос 4.** Зачем нужен `TypeVar`? Приведите пример, где без него нельзя правильно аннотировать функцию.
**Вопрос 5.** Что такое прямая ссылка (forward reference) и как её решить?
**Вопрос 6.** Для чего используется `TYPE_CHECKING`? Как это помогает с циклическими импортами?
**Вопрос 7.** Чем `Iterable[str]` как тип параметра лучше `list[str]` в некоторых случаях?
**Вопрос 8.** Почему важно аннотировать `-> None` для функций, которые ничего не возвращают?

---

## Задачи

### **Задача 1**. 

Аннотирование существующих функций

Добавьте аннотации типов к следующим функциям. Используйте современный синтаксис Python 3.10+.

```python
# Дано: функции без аннотаций
def get_user_by_id(user_id, users_db):
    return users_db.get(user_id)

def filter_active_users(users):
    return [u for u in users if u.get("is_active")]

def format_user_response(user, include_email=True):
    result = {"id": user["id"], "username": user["username"]}
    if include_email:
        result["email"] = user["email"]
    return result

def calculate_order_total(items, discount_percent=0):
    total = sum(item["price"] * item["quantity"] for item in items)
    discount = total * discount_percent / 100
    return total - discount

def send_notification(user_ids, message, channel="email"):
    pass   # имитация отправки
```

Нужно добавить аннотации и при необходимости `from __future__ import annotations`.

---

### **Задача 2**. 

Класс с полными аннотациями

Создайте полностью аннотированный класс `ProductCatalog` — каталог товаров. 

Атрибуты: `_products: dict[int, dict[str, object]]`, `_next_id: int`, `_category_index: dict[str, list[int]]`. 

Методы:
- `add_product(name, price, category, tags) -> dict[str, object]`
- `get_product(product_id) -> dict[str, object] | None`
- `search_by_category(category) -> list[dict[str, object]]`
- `search_by_tag(tag) -> list[dict[str, object]]`
- `update_price(product_id, new_price) -> bool`
- `get_price_range(min_price, max_price) -> list[dict[str, object]]`
- `count() -> int`

Все параметры и возвращаемые значения должны быть аннотированы.

**Пример использования**:

```python
catalog = ProductCatalog()
catalog.add_product("Ноутбук", 89990.0, "electronics", ["portable", "work"])
catalog.add_product("Мышь", 1500.0, "electronics", ["portable"])
catalog.add_product("Стол", 15000.0, "furniture")

print(catalog.count())
print(catalog.search_by_category("electronics"))
print(catalog.search_by_tag("portable"))
print(catalog.get_price_range(1000.0, 20000.0))
print(catalog.update_price(1, 79990.0))
```

---

### **Задача 3**. 

`TypeVar` для обобщённых функций

Реализуйте следующие обобщённые функции с правильными аннотациями через `TypeVar`:

1. `safe_get(items, index, default)` — возвращает элемент списка по индексу или default, если индекс вне диапазона. Тип элементов и дефолтного значения должен совпадать.

2. `group_by(items, key_func)` — группирует список по ключу. Принимает список элементов любого типа и функцию-ключ, возвращает словарь.

3. `batch(items, size)` — разбивает список на батчи заданного размера. Тип элементов сохраняется.

4. `filter_by_type(items, target_type)` — фильтрует список, оставляя только элементы нужного типа. Возвращает типизированный список.

**Пример использования**:

```python
print(safe_get([1, 2, 3], 5, 0))           # 0
print(safe_get(["a", "b"], 1, "default"))   # "b"

users = [{"name": "Alice", "role": "admin"}, {"name": "Bob", "role": "user"}, {"name": "Carol", "role": "admin"}]
grouped = group_by(users, lambda u: u["role"])
print(grouped)  # {'admin': [...], 'user': [...]}

batches = list(batch([1, 2, 3, 4, 5], 2))
print(batches)  # [[1, 2], [3, 4], [5]]

mixed = [1, "hello", 2, "world", 3.14, True]
strings = filter_by_type(mixed, str)
print(strings)  # ["hello", "world"]
```

---

### **Задача 4**. 

Аннотации с `Literal` и `Union`

Создайте систему конфигурации HTTP-клиента с точными аннотациями. Используйте `Literal` для HTTP-методов, статусов и форматов. Используйте `Union` (или `|`) для параметров, которые могут быть нескольких типов.

```python
# Нужно полностью аннотировать:
class HTTPClient:
    def request(self, method, url, body=None, headers=None, timeout=30): ...
    def get(self, url, params=None): ...
    def post(self, url, data, content_type="json"): ...
    def parse_response(self, response, format="json"): ...
```

Правила аннотаций:
- `method` принимает только `"GET"`, `"POST"`, `"PUT"`, `"DELETE"`, `"PATCH"`.
- `body` может быть `dict`, `str`, `bytes` или `None`.
- `headers` — словарь строк или None.
- `timeout` — целое число или float.
- `params` — словарь строка→строка или None.
- `content_type` принимает только `"json"`, `"form"`, `"multipart"`.
- `format` в `parse_response` принимает `"json"`, `"text"`, `"bytes"`.
- Возвращаемые значения: `request` → `dict`, `get` → `dict`, `post` → `dict`, `parse_response` → `dict | str | bytes`.

**Пример использования**:

```python
client = HTTPClient("https://api.example.com")

response = client.get("/users", params={"page": "1", "limit": "10"})  # [GET] /users?page=1&limit=10, body=NoneType, timeout=30
print(response)  # {'status': 200, 'url': '/users?page=1&limit=10', 'method': 'GET'}

response = client.post("/users", {"name": "Alice"}, content_type="json")  # [POST] /users, body=dict, timeout=30
print(response)  # {'status': 200, 'url': '/users', 'method': 'POST'}

parsed = client.parse_response(response, format="text")
print(f"Тип результата: {type(parsed).__name__}")  # Тип результата: str
```

---

### **Задача 5**. 

Полностью аннотированный EventBus

Перепишите класс `EventBus` из урока 22 с полными аннотациями типов. Используйте `TypeVar`, `Callable`, `Type`. Все методы должны быть аннотированы. Используйте `from __future__ import annotations` для поддержки прямых ссылок.

```python
# Скелет класса для аннотирования:
class Event:
    def __init__(self, source): ...

class HTTPRequestEvent(Event):
    def __init__(self, source, method, path, status_code): ...

class EventBus:
    def subscribe(self, event_type, handler): ...
    def publish(self, event): ...
    def unsubscribe(self, event_type, handler): ...
    def subscriber_count(self, event_type): ...
```

**Пример использования**:

```python
bus = EventBus()


def log_all(event: Event) -> None:
    print(f"[LOG] {event}")


def handle_http(event: HTTPRequestEvent) -> None:
    print(f"[HTTP] {event.method} {event.path} → {event.status_code}")


bus.subscribe(Event, log_all)
bus.subscribe(HTTPRequestEvent, handle_http)

http_event = HTTPRequestEvent("nginx", "GET", "/api/users", 200)
user_event = UserActionEvent("app", user_id=1, action="login")

count = bus.publish(http_event)
print(f"Вызвано обработчиков: {count}")

count = bus.publish(user_event)
print(f"Вызвано обработчиков: {count}")

print(f"Подписчиков на Event: {bus.subscriber_count(Event)}")
print(f"Подписчиков на HTTPRequestEvent: {bus.subscriber_count(HTTPRequestEvent)}")
```

---

[Предыдущий урок](lesson27.md) | [Следующий урок](lesson29.md)