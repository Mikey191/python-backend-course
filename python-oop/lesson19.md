# Урок 19. Наследование в ООП: базовые концепции и синтаксис?

---

## Зачем нужно наследование

Представьте, что вы разрабатываете бэкенд интернет-магазина и вам нужно описать несколько типов пользователей: обычного покупателя, администратора и менеджера склада. У всех троих есть имя, email, дата регистрации и метод аутентификации. При этом у администратора есть дополнительные права, у менеджера — доступ к складским операциям.

Без наследования вы бы писали три отдельных класса, копируя одни и те же атрибуты и методы в каждый. Это нарушает один из ключевых принципов разработки — DRY (Don't Repeat Yourself). Каждый раз, когда вам понадобится изменить логику аутентификации, придётся менять код в трёх местах вместо одного.

Наследование решает эту проблему: вы описываете общую часть один раз в базовом классе, а каждый специализированный класс только добавляет или изменяет то, что отличает его от базового.

Но наследование — не универсальный инструмент. Прежде чем его применять, важно ответить на вопрос: существует ли между классами отношение «является» (is-a)?

- Администратор является пользователем — отношение `is-a` есть, наследование уместно.
- Пользователь содержит корзину — это отношение `has-a`, здесь нужна не наследование, а композиция (корзина как атрибут пользователя).

Нарушение этого правила приводит к классической архитектурной ошибке: классы наследуются ради повторного использования кода, хотя семантически между ними нет отношения «является». Такой код становится хрупким и трудно поддерживаемым.

---

## Синтаксис наследования в Python

Объявить дочерний класс в Python очень просто: имя родительского класса указывается в скобках после имени дочернего:

```python
class Parent:
    pass

class Child(Parent):
    pass
```

Дочерний класс автоматически получает все методы и атрибуты родителя. Никаких дополнительных действий не требуется — это происходит само по себе в момент объявления класса.

Рассмотрим первый конкретный пример. Базовый класс пользователя:

```python
class User:
    """Базовый класс для всех пользователей системы."""

    def __init__(self, username, email):
        self.username = username
        self.email = email
        self.is_active = True

    def deactivate(self):
        """Деактивировать аккаунт пользователя."""
        self.is_active = False
        print(f"Аккаунт {self.username} деактивирован")

    def get_info(self):
        status = "активен" if self.is_active else "деактивирован"
        return f"Пользователь: {self.username} ({self.email}), статус: {status}"

    def __repr__(self):
        return f"User(username={self.username!r}, email={self.email!r})"
```

Теперь создадим дочерний класс администратора:

```python
class AdminUser(User):
    """Администратор системы. Наследует все методы User."""
    pass   # пока не добавляем ничего нового
```

Несмотря на то что тело класса пустое, `AdminUser` уже обладает всем, что есть в `User`:

```python
admin = AdminUser("alice", "alice@example.com")

# Метод из родителя работает напрямую
print(admin.get_info())
# Пользователь: alice (alice@example.com), статус: активен

# Атрибуты из __init__ родителя тоже доступны
print(admin.username)   # alice
print(admin.is_active)  # True

admin.deactivate()
# Аккаунт alice деактивирован
```

---

## Проверка принадлежности: `isinstance()` и `issubclass()`

Python предоставляет две встроенные функции для проверки отношений наследования.

`isinstance(obj, Class)` проверяет, является ли объект экземпляром указанного класса или любого его потомка:

```python
admin = AdminUser("alice", "alice@example.com")

print(isinstance(admin, AdminUser))   # True — прямое соответствие
print(isinstance(admin, User))        # True — AdminUser является подклассом User
print(isinstance(admin, str))         # False — str не в иерархии

# Сравните с type() — он не учитывает наследование
print(type(admin) == AdminUser)   # True
print(type(admin) == User)        # False — type() не поднимается по иерархии
```

Именно поэтому `isinstance()` предпочтительнее `type()` при проверке типа: он корректно обрабатывает наследование. Если вы напишете `type(obj) == User`, то объект типа `AdminUser` не пройдёт проверку, хотя семантически он является пользователем.

`issubclass(Child, Parent)` проверяет отношение между классами, а не объектами:

```python
print(issubclass(AdminUser, User))    # True
print(issubclass(User, AdminUser))    # False — обратное неверно
print(issubclass(User, object))       # True — любой класс является подклассом object
print(issubclass(AdminUser, object))  # True — через User
```

Каждый класс в Python неявно наследуется от `object`, если не указан другой родитель. Это делает `object` общим предком всей иерархии классов.

Посмотреть на иерархию классов можно через атрибут `__mro__` (Method Resolution Order):

```python
print(AdminUser.__mro__)
# (<class 'AdminUser'>, <class 'User'>, <class 'object'>)

print(AdminUser.__bases__)
# (<class 'User'>,) — прямые родители
```

`__mro__` показывает порядок, в котором Python будет искать атрибуты и методы при обращении к объекту. В простом случае одиночного наследования этот порядок очевиден: сначала сам класс, затем его родитель, затем `object`.

---

## Что наследуется, а что нет

Дочерний класс наследует все публичные (`name`) и защищённые (`_name`) методы и атрибуты родителя. Приватные атрибуты (`__name`) подчиняются механизму name mangling — Python переименовывает их в `_ClassName__name`, что делает их труднодоступными из дочерних классов, но технически не делает недоступными.

Рассмотрим это на примере:

```python
class Base:
    class_attr = "атрибут класса"   # атрибут класса, общий для всех

    def __init__(self):
        self.public_attr = "публичный"
        self._protected_attr = "защищённый"
        self.__private_attr = "приватный"   # станет _Base__private_attr

    def public_method(self):
        return "публичный метод"

    def _protected_method(self):
        return "защищённый метод"

    def __private_method(self):
        return "приватный метод"


class Derived(Base):
    def show_inheritance(self):
        print(self.class_attr)          # доступен — наследуется
        print(self.public_attr)         # доступен — наследуется
        print(self._protected_attr)     # доступен — наследуется (но не рекомендуется)

        # self.__private_attr           # AttributeError — не виден под этим именем
        print(self._Base__private_attr) # работает, но это нарушение инкапсуляции


d = Derived()
print(d.public_method())     # публичный метод
print(d._protected_method()) # защищённый метод
print(d.class_attr)          # атрибут класса
d.show_inheritance()
```

Важно понимать: защищённые атрибуты и методы (с одним подчёркиванием) технически доступны в дочерних классах, но это соглашение, а не ограничение. Обращение к ним из дочернего класса допустимо, но из внешнего кода — нарушение договорённости.

---

## Переопределение методов

Дочерний класс может переопределить любой метод родителя, просто объявив метод с тем же именем. Переопределённый метод полностью скрывает родительский для объектов дочернего класса:

```python
class User:
    def __init__(self, username, email):
        self.username = username
        self.email = email
        self.is_active = True

    def get_info(self):
        return f"Пользователь: {self.username} ({self.email})"

    def __repr__(self):
        return f"User({self.username!r})"


class AdminUser(User):
    def __init__(self, username, email, admin_level=1):
        # Вызываем __init__ родителя, чтобы не потерять его логику
        super().__init__(username, email)
        # Добавляем специфичный атрибут
        self.admin_level = admin_level

    def get_info(self):
        # Переопределяем метод — добавляем информацию об уровне доступа
        base_info = super().get_info()   # берём строку из родительского метода
        return f"{base_info} [Администратор, уровень {self.admin_level}]"

    def __repr__(self):
        return f"AdminUser({self.username!r}, level={self.admin_level})"


user = User("bob", "bob@example.com")
admin = AdminUser("alice", "alice@example.com", admin_level=2)

print(user.get_info())
# Пользователь: bob (bob@example.com)

print(admin.get_info())
# Пользователь: alice (alice@example.com) [Администратор, уровень 2]
```

Обратите внимание на вызов `super().get_info()` внутри переопределённого метода. Это позволяет расширить поведение родительского метода, а не заменить его полностью. В следующем уроке мы разберём `super()` подробно, здесь важно зафиксировать саму идею: переопределение — это не всегда полная замена, часто это расширение.

---

## Инициализация в дочернем классе

Инициализатор `__init__` наследуется точно так же, как и другие методы. Но часто дочерний класс нуждается в дополнительных атрибутах, и здесь возникает три варианта поведения.

**Вариант 1: не определять `__init__` в дочернем классе.** Тогда Python будет использовать `__init__` родителя. Этот вариант подходит, если дочерний класс не требует новых атрибутов:

```python
class RegularUser(User):
    # __init__ не определён — будет использоваться User.__init__
    def can_post(self):
        return self.is_active


regular = RegularUser("charlie", "charlie@example.com")
print(regular.username)    # charlie — инициализирован через User.__init__
print(regular.can_post())  # True
```

**Вариант 2: полностью переопределить `__init__`.** Дочерний класс берёт на себя всю инициализацию. Это уместно, если логика создания объекта кардинально отличается от родительской, но тогда нужно самостоятельно инициализировать все нужные атрибуты:

```python
class APIKeyUser(User):
    def __init__(self, api_key):
        # НЕ вызываем super().__init__() — полная замена
        # Это означает, что self.username, self.email, self.is_active
        # НЕ будут установлены!
        self.api_key = api_key
        self.is_active = True   # нужно инициализировать вручную

# Это опасный подход — легко забыть про часть атрибутов родителя
```

**Вариант 3: расширить `__init__` родителя — самый распространённый и правильный.**

```python
class ModeratorUser(User):
    def __init__(self, username, email, moderated_sections):
        super().__init__(username, email)   # сначала инициализируем родительские атрибуты
        # затем добавляем специфичные для модератора
        self.moderated_sections = moderated_sections

    def can_moderate(self, section):
        return section in self.moderated_sections and self.is_active


mod = ModeratorUser("dave", "dave@example.com", ["news", "sport"])
print(mod.username)              # dave — от родителя
print(mod.moderated_sections)    # ['news', 'sport'] — от дочернего
print(mod.can_moderate("news"))  # True
```

Типичная ошибка — забыть вызвать `super().__init__()`. В этом случае родительские атрибуты не инициализируются, и при первом обращении к ним возникнет `AttributeError`. Этот баг особенно неприятен тем, что объект создаётся без ошибок — проблема проявляется только при использовании.

---

## Цепочка поиска атрибутов

Когда вы обращаетесь к атрибуту или методу объекта, Python ищет его в строго определённом порядке, который задаётся MRO (Method Resolution Order). В простом случае одиночного наследования порядок такой:

```
экземпляр → класс объекта → родительский класс → ... → object
```

```python
class Animal:
    sound = "..."    # атрибут класса

    def speak(self):
        return f"Animal говорит: {self.sound}"


class Dog(Animal):
    sound = "Гав"   # переопределяем атрибут класса


class Poodle(Dog):
    pass             # не переопределяем ничего


poodle = Poodle()

# Python ищет 'speak': нет в Poodle, нет в Dog, есть в Animal → вызывает Animal.speak
# Python ищет 'sound': нет в Poodle, есть в Dog → использует Dog.sound

print(poodle.speak())   # Animal говорит: Гав
```

Это поведение может быть неожиданным: метод `speak` определён в `Animal`, но `self.sound` внутри него разрешается через MRO объекта — то есть ищется в `Poodle`, затем в `Dog`, где и находится `"Гав"`. Метод родителя использует атрибут, переопределённый в дочернем классе. Это ключевая особенность полиморфизма, к которой мы вернёмся подробнее в следующих уроках.

---

## Практический пример: иерархия пользователей веб-приложения

Соберём полноценную иерархию, которая отражает реальную архитектуру прав в веб-приложении:

```python
import datetime
from functools import total_ordering


class User:
    """
    Базовый класс для всех пользователей системы.
    Содержит общую логику: аутентификация, базовые атрибуты, деактивация.
    """

    def __init__(self, username, email, created_at=None):
        self.username = username
        self.email = email
        self.is_active = True
        self.created_at = created_at or datetime.datetime.now()
        self._password_hash = None   # защищённый — только для внутреннего использования

    def set_password(self, password):
        """Устанавливает пароль (хеширование упрощено для примера)."""
        self._password_hash = hash(password)

    def check_password(self, password):
        """Проверяет пароль."""
        return self._password_hash == hash(password)

    def deactivate(self):
        self.is_active = False

    def get_permissions(self):
        """Возвращает набор разрешений пользователя."""
        return {"read"}   # базовые права: только чтение

    def get_info(self):
        return f"{self.username} ({self.email})"

    def __repr__(self):
        return f"{self.__class__.__name__}(username={self.username!r})"

    def __str__(self):
        return self.get_info()


class RegularUser(User):
    """
    Обычный зарегистрированный пользователь.
    Добавляет право создавать собственный контент.
    """

    def __init__(self, username, email, subscription_plan="free"):
        super().__init__(username, email)
        self.subscription_plan = subscription_plan

    def get_permissions(self):
        # Расширяем права родителя
        return super().get_permissions() | {"create", "edit_own", "delete_own"}

    def upgrade_plan(self, new_plan):
        self.subscription_plan = new_plan
        print(f"{self.username}: подписка изменена на '{new_plan}'")

    def get_info(self):
        base = super().get_info()
        return f"{base} [подписка: {self.subscription_plan}]"


class ModeratorUser(User):
    """
    Модератор: может управлять контентом других пользователей
    в назначенных разделах.
    """

    def __init__(self, username, email, sections=None):
        super().__init__(username, email)
        self.sections = sections or []

    def get_permissions(self):
        return super().get_permissions() | {"create", "edit_any", "delete_any", "ban_user"}

    def can_moderate(self, section):
        return self.is_active and section in self.sections

    def assign_section(self, section):
        if section not in self.sections:
            self.sections.append(section)
            print(f"{self.username}: назначен модератором раздела '{section}'")

    def get_info(self):
        base = super().get_info()
        sections_str = ", ".join(self.sections) if self.sections else "нет"
        return f"{base} [модератор: {sections_str}]"


class AdminUser(User):
    """
    Администратор: полный доступ ко всем функциям системы.
    """

    def __init__(self, username, email, admin_level=1):
        super().__init__(username, email)
        self.admin_level = admin_level   # 1=junior, 2=senior, 3=superadmin

    def get_permissions(self):
        # Администратор получает полный набор прав
        return {
            "read", "create", "edit_any", "delete_any",
            "ban_user", "manage_users", "access_admin_panel",
            "view_logs", "manage_settings"
        }

    def promote_user(self, user, new_class):
        """Повышает пользователя до другого типа (упрощённо)."""
        print(f"Администратор {self.username} повышает {user.username} до {new_class.__name__}")

    def get_info(self):
        base = super().get_info()
        return f"{base} [администратор уровня {self.admin_level}]"
```

Демонстрация работы иерархии:

```python
# Создаём пользователей разных типов
regular = RegularUser("bob", "bob@example.com", subscription_plan="pro")
mod = ModeratorUser("carol", "carol@example.com", sections=["news", "sport"])
admin = AdminUser("alice", "alice@example.com", admin_level=3)

# Все объекты имеют общие методы от User
for user in [regular, mod, admin]:
    print(user.get_info())

# Пользователь: bob (bob@example.com) [подписка: pro]
# Пользователь: carol (carol@example.com) [модератор: news, sport]
# Пользователь: alice (alice@example.com) [администратор уровня 3]

# isinstance учитывает иерархию
print(isinstance(admin, User))       # True — AdminUser является User
print(isinstance(admin, AdminUser))  # True

# Права у каждого свои
print("Права regular:", regular.get_permissions())
# {'read', 'create', 'edit_own', 'delete_own'}

print("Права admin:", admin.get_permissions())
# {'read', 'create', 'edit_any', ..., 'manage_settings'}

# Специфические методы только в своих классах
mod.assign_section("technology")
print(mod.can_moderate("news"))       # True
print(mod.can_moderate("science"))    # False

# Можно хранить разные типы в одном списке — все являются User
users = [regular, mod, admin]
active_users = [u for u in users if u.is_active]
print(f"Активных пользователей: {len(active_users)}")   # 3
```

---

## Практический пример: иерархия HTTP-ответов

Второй пример ближе к внутреннему устройству веб-фреймворков. Django и DRF возвращают объекты ответов — `HttpResponse`, `JsonResponse`, `HttpResponseNotFound` и другие. Все они построены на наследовании:

```python
import json


class HTTPResponse:
    """
    Базовый класс HTTP-ответа.
    Содержит общую логику формирования ответа.
    """

    DEFAULT_CONTENT_TYPE = "text/plain"

    def __init__(self, body="", status_code=200):
        self.body = body
        self.status_code = status_code
        self.headers = {
            "Content-Type": self.DEFAULT_CONTENT_TYPE,
        }

    def set_header(self, key, value):
        self.headers[key] = value
        return self   # позволяет чейнить: response.set_header(...).set_header(...)

    def is_success(self):
        return 200 <= self.status_code < 300

    def to_dict(self):
        """Представление ответа в виде словаря (для тестов)."""
        return {
            "status_code": self.status_code,
            "headers": self.headers,
            "body": self.body,
        }

    def __repr__(self):
        return f"{self.__class__.__name__}(status={self.status_code})"

    def __str__(self):
        return f"HTTP {self.status_code}"


class JSONResponse(HTTPResponse):
    """
    Ответ с телом в формате JSON.
    Автоматически сериализует данные и выставляет Content-Type.
    """

    DEFAULT_CONTENT_TYPE = "application/json"

    def __init__(self, data, status_code=200):
        # data — это словарь или список Python
        body = json.dumps(data, ensure_ascii=False)
        super().__init__(body=body, status_code=status_code)
        # Переопределяем Content-Type для JSON
        self.headers["Content-Type"] = self.DEFAULT_CONTENT_TYPE
        self._data = data   # сохраняем оригинальные данные

    @property
    def data(self):
        return self._data


class ErrorResponse(JSONResponse):
    """
    Ответ об ошибке. Всегда содержит поля error и message.
    """

    def __init__(self, error_code, message, status_code=400, details=None):
        data = {
            "error": error_code,
            "message": message,
        }
        if details:
            data["details"] = details

        super().__init__(data=data, status_code=status_code)
        self.error_code = error_code

    def __str__(self):
        return f"HTTP {self.status_code}: {self.error_code}"


class NotFoundResponse(ErrorResponse):
    """404 Not Found — специализированная ошибка отсутствия ресурса."""

    def __init__(self, resource_type, resource_id):
        super().__init__(
            error_code="NOT_FOUND",
            message=f"{resource_type} с идентификатором {resource_id} не найден",
            status_code=404,
        )
        self.resource_type = resource_type
        self.resource_id = resource_id


class RedirectResponse(HTTPResponse):
    """HTTP-перенаправление (301 или 302)."""

    def __init__(self, location, permanent=False):
        status_code = 301 if permanent else 302
        super().__init__(status_code=status_code)
        self.headers["Location"] = location

    def __str__(self):
        location = self.headers.get("Location", "")
        return f"HTTP {self.status_code} → {location}"
```

Демонстрируем использование:

```python
# Имитация обработчиков запросов (view-функций)
def get_user(user_id):
    users_db = {1: {"id": 1, "name": "Alice", "role": "admin"}}

    if user_id not in users_db:
        return NotFoundResponse("User", user_id)

    return JSONResponse(data=users_db[user_id])


def create_user(data):
    if "name" not in data:
        return ErrorResponse(
            error_code="VALIDATION_ERROR",
            message="Поле 'name' обязательно",
            status_code=422,
            details={"field": "name", "issue": "required"}
        )
    return JSONResponse(data={"created": True, "id": 42}, status_code=201)


# Работаем с ответами
response1 = get_user(1)
response2 = get_user(99)
response3 = create_user({})
response4 = RedirectResponse("/api/v2/users", permanent=True)

print(response1)           # HTTP 200
print(response2)           # HTTP 404: NOT_FOUND
print(response3)           # HTTP 400: VALIDATION_ERROR
print(response4)           # HTTP 301 → /api/v2/users

# isinstance позволяет единообразно обрабатывать ответы
responses = [response1, response2, response3, response4]
for r in responses:
    if isinstance(r, ErrorResponse):
        print(f"Ошибка: {r.error_code} ({r.status_code})")
    elif r.is_success():
        print(f"Успех: {r.status_code}")
    else:
        print(f"Другой ответ: {r}")

# Проверяем иерархию
print(isinstance(response2, NotFoundResponse))   # True
print(isinstance(response2, ErrorResponse))      # True
print(isinstance(response2, JSONResponse))       # True
print(isinstance(response2, HTTPResponse))       # True
```

Этот пример показывает, как наследование позволяет строить гибкие иерархии: `NotFoundResponse` — это одновременно `ErrorResponse`, `JSONResponse` и `HTTPResponse`. Код, который работает с любым `HTTPResponse`, автоматически работает и с `NotFoundResponse`.

---

## Наследование от встроенных типов

Python позволяет наследоваться от встроенных типов — `list`, `dict`, `str` и других. Это мощный инструмент для создания специализированных коллекций:

```python
class UserList(list):
    """
    Список пользователей с дополнительными методами фильтрации.
    Наследует всё поведение обычного списка.
    """

    def active(self):
        """Возвращает только активных пользователей."""
        return UserList(u for u in self if u.is_active)

    def by_type(self, user_class):
        """Возвращает пользователей определённого типа."""
        return UserList(u for u in self if isinstance(u, user_class))

    def emails(self):
        """Возвращает список email-адресов."""
        return [u.email for u in self]

    def __repr__(self):
        return f"UserList({len(self)} users)"
```

Использование:

```python
users = UserList([
    RegularUser("bob", "bob@example.com"),
    AdminUser("alice", "alice@example.com"),
    ModeratorUser("carol", "carol@example.com"),
    RegularUser("dave", "dave@example.com"),
])

# Все методы обычного списка работают
users[0].deactivate()
print(len(users))   # 4

# Дополнительные методы
active = users.active()
print(active)                       # UserList(3 users)
print(len(active))                  # 3

admins = users.by_type(AdminUser)
print(admins)                       # UserList(1 users)
print(admins[0].username)           # alice

print(users.emails())
# ['bob@example.com', 'alice@example.com', 'carol@example.com', 'dave@example.com']

# UserList всё ещё является list
print(isinstance(users, list))      # True
```

Важная особенность при наследовании от встроенных типов: некоторые методы (например, `list.copy()`, `list[:]`) возвращают экземпляры `list`, а не `UserList`. Это потому, что внутри они создают объект через `type(self)()` только в новых версиях Python и не всегда. Если вам нужно, чтобы все операции возвращали ваш тип — придётся переопределить соответствующие методы. Но для большинства практических задач базового наследования достаточно.

---

## Неочевидные моменты и типичные ошибки

**Мутация общего изменяемого атрибута класса.** Если в базовом классе определён изменяемый атрибут класса (список, словарь), и дочерний класс его изменяет — это затронет все классы, использующие этот атрибут:

```python
class Base:
    tags = []   # изменяемый атрибут класса — опасно!

class Child(Base):
    pass

child = Child()
child.tags.append("new_tag")   # изменяем через экземпляр

print(Base.tags)    # ['new_tag'] — неожиданно! Базовый класс тоже изменился
print(Child.tags)   # ['new_tag']
```

Правильный подход — инициализировать изменяемые атрибуты в `__init__`, а не на уровне класса:

```python
class Base:
    def __init__(self):
        self.tags = []   # атрибут экземпляра — каждый объект имеет свой список
```

**Переопределение метода без вызова родительского — нарушение логики.** Если базовый класс имеет важную логику в методе, а дочерний её полностью замещает — может нарушиться инвариант:

```python
class User:
    def deactivate(self):
        self.is_active = False
        self._log_deactivation()   # важная побочная операция

class BadAdminUser(User):
    def deactivate(self):
        # Полностью заменяем метод, забывая про _log_deactivation()
        if self.admin_level < 3:
            self.is_active = False
        # Логирование потеряно!
```

**Когда наследование — плохой выбор.** Глубокие иерархии наследования (3–4 уровня и более) становятся трудно понимаемыми и хрупкими. Изменение в базовом классе может сломать несколько дочерних. Если вы обнаруживаете, что дочерний класс переопределяет большинство методов родителя — возможно, лучше использовать композицию.

Принцип подстановки Лисков (LSP) гласит: дочерний класс должен быть полностью взаимозаменяем с родительским. Если вы не можете использовать `AdminUser` везде, где ожидается `User` — иерархия спроектирована неверно.

---

## Итоги урока

Наследование позволяет создавать иерархии классов, где дочерние классы автоматически получают методы и атрибуты родительских. Ключевой критерий применимости — отношение «является» (is-a): AdminUser является User, но не наоборот.

Дочерний класс наследует все публичные и защищённые методы и атрибуты. Любой метод можно переопределить, полностью заменив поведение или расширив его через `super()`. Инициализатор `__init__` наследуется как обычный метод — если дочерний класс объявляет свой, он должен явно вызвать `super().__init__()`, чтобы не потерять инициализацию родителя.

Функции `isinstance()` и `issubclass()` учитывают всю цепочку наследования. Python ищет атрибуты и методы по цепочке MRO: сначала в экземпляре, затем в классе, затем поднимается по иерархии до `object`.

В следующем уроке мы подробно разберём функцию `super()` — как именно она работает, почему она безопаснее прямого вызова родительского класса по имени, и как её использовать в нетривиальных случаях.

---

## Вопросы

1. Какой вопрос нужно задать, чтобы определить, уместно ли использовать наследование между двумя классами? Приведите пример корректного и некорректного применения наследования.
2. Чем `isinstance(obj, ClassName)` отличается от `type(obj) == ClassName`? Почему `isinstance()` предпочтительнее?
3. Что происходит, если дочерний класс не определяет `__init__`? Что произойдёт, если он определяет `__init__`, но не вызывает `super().__init__()`?
4. Объект `poodle` является экземпляром класса `Poodle`, который наследует от `Dog`, который наследует от `Animal`. Какой вывод даст `print(poodle.speak())`, если `speak()` определён в `Animal`, `sound = "Гав"` определён в `Dog`, а в `Poodle` ничего не переопределено?
5. Почему опасно использовать изменяемые объекты (список, словарь) как атрибуты класса в базовом классе при наследовании?
6. Что такое `__mro__` и зачем он нужен? Какой порядок будет в `__mro__` для класса `NotFoundResponse`, который наследует от `ErrorResponse → JSONResponse → HTTPResponse`?
7. В чём разница между полным переопределением метода и расширением через `super()`? Когда уместен каждый подход?
8. Что означает принцип подстановки Лисков в контексте наследования? Как понять, что иерархия его нарушает?

---

## Задачи

### **Задача 1**. 

Класс `PremiumUser`

Создайте класс `PremiumUser`, который наследует от класса `RegularUser` из лекции. 

Класс должен принимать те же аргументы, что и `RegularUser` (`username`, `email`, `subscription_plan`), плюс дополнительный аргумент `storage_gb` (объём облачного хранилища в гигабайтах, целое число). 

В `__init__` вызовите `super().__init__()` с нужными аргументами и дополнительно установите атрибут `storage_gb`. 

Переопределите метод `get_permissions()`, добавив к правам из `RegularUser` ещё `"priority_support"` и `"unlimited_api"`. 

Переопределите `get_info()`, добавив к строке родителя информацию о хранилище в формате `[хранилище: N ГБ]`. 

Реализуйте `__repr__` в формате `PremiumUser('alice', storage=100)`.

**Пример использования**:

```python
premium = PremiumUser("alice", "alice@example.com", subscription_plan="premium", storage_gb=100)

print(premium.get_info())
# alice (alice@example.com) [подписка: premium] [хранилище: 100 ГБ]

print(premium.get_permissions())
# {'read', 'create', 'edit_own', 'delete_own', 'priority_support', 'unlimited_api'}

print(isinstance(premium, RegularUser))   # True
print(isinstance(premium, User))          # True
print(repr(premium))   # PremiumUser('alice', storage=100)
```

---

### **Задача 2**. 

Класс `Vehicle` и дочерние классы

Создайте базовый класс `Vehicle` (транспортное средство) с атрибутами: `make` (марка, строка), `model` (модель, строка), `year` (год выпуска, целое число), `speed` (текущая скорость, по умолчанию 0). 

Реализуйте методы `accelerate(amount)` (увеличивает скорость на `amount`, но не выше `max_speed`) и `brake(amount)` (уменьшает скорость на `amount`, но не ниже 0). 

Добавьте абстрактный по смыслу атрибут класса `max_speed = 0` и метод `get_info()`. 

Реализуйте `__str__` в формате `"2024 Toyota Camry"` и `__repr__` в формате `Vehicle('Toyota', 'Camry', 2024)`.

Создайте дочерние классы:
- `Car(Vehicle)` — `max_speed = 250`, дополнительный атрибут `num_doors` (количество дверей, по умолчанию 4).
- `Truck(Vehicle)` — `max_speed = 120`, дополнительный атрибут `payload_tons` (грузоподъёмность в тоннах).
- `ElectricCar(Car)` — наследует от `Car`, добавляет `battery_kwh` (ёмкость батареи) и `range_km` (запас хода).

**Пример использования**:

```python
car = Car("Toyota", "Camry", 2024, num_doors=4)
truck = Truck("Volvo", "FH16", 2023, payload_tons=25)
electric = ElectricCar("Tesla", "Model S", 2024, battery_kwh=100, range_km=600)

car.accelerate(100)
car.accelerate(200)   # скорость не превысит max_speed=250
print(car.speed)      # 250

print(isinstance(electric, Car))      # True
print(isinstance(electric, Vehicle))  # True

print(str(car))        # 2024 Toyota Camry
print(car.get_info())  # содержит марку, модель, год, скорость
```

---

### **Задача 3**. 

Класс `LoggedList`

Создайте класс `LoggedList`, который наследует от встроенного `list`. 

Класс должен логировать все операции изменения: добавление элементов (`append`, `extend`, `insert`), удаление (`remove`, `pop`, `clear`) и присваивание по индексу (`__setitem__`). 

Логирование — вывод в консоль строки вида `"[LOG] append: 'значение'"`. 

Все остальные методы списка должны работать без изменений. Реализуйте `__repr__` в формате `LoggedList([...])`.

**Пример использования**:

```python
lst = LoggedList([1, 2, 3])
lst.append(4)
# [LOG] append: 4

lst.extend([5, 6])
# [LOG] extend: [5, 6]

lst[0] = 99
# [LOG] __setitem__: index=0, value=99

removed = lst.pop()
# [LOG] pop: index=-1

print(lst)   # [99, 2, 3, 4, 5]
print(len(lst))   # 5
print(isinstance(lst, list))   # True
```

---

### **Задача 4**. 

Иерархия уведомлений

Создайте иерархию классов для системы уведомлений веб-приложения. 

Базовый класс `Notification` принимает `recipient` (строка, email получателя), `subject` (строка, тема) и `body` (строка, тело сообщения). 

Добавьте метод `send()`, который выводит `"Отправка уведомления: [тип] → recipient"` и метод `to_dict()`, возвращающий словарь с полями `type`, `recipient`, `subject`, `body`. 

Атрибут `notification_type = "generic"` задаётся на уровне класса.

Создайте три дочерних класса:
- `EmailNotification(Notification)` — `notification_type = "email"`, добавляет атрибут `cc` (список email адресов копии, по умолчанию пустой). `to_dict()` дополняет словарь родителя полем `cc`.
- `SMSNotification(Notification)` — `notification_type = "sms"`, принимает `phone_number`. Переопределяет `send()`, выводя номер телефона. `to_dict()` добавляет `phone_number`.
- `PushNotification(Notification)` — `notification_type = "push"`, принимает `device_token` и `priority` (строка, по умолчанию `"normal"`). `to_dict()` добавляет оба поля.

**Пример использования**:

```python
email = EmailNotification(
    "user@example.com", "Сброс пароля", "Для сброса пароля перейдите по ссылке...",
    cc=["admin@example.com"]
)
sms = SMSNotification(
    "user@example.com", "Код подтверждения", "Ваш код: 1234",
    phone_number="+79001234567"
)
push = PushNotification(
    "user@example.com", "Новое сообщение", "У вас 3 непрочитанных сообщения",
    device_token="abc123xyz", priority="high"
)

notifications = [email, sms, push]
for n in notifications:
    n.send()

print(isinstance(sms, Notification))   # True
print(email.to_dict())   # {'type': 'email', 'recipient': ..., 'cc': [...]}
```

---

### **Задача 5**. 

Класс `TypedDict`

Создайте класс `TypedDict`, который наследует от встроенного `dict`. 

При создании принимает схему `schema` — словарь вида `{ключ: тип}`. 

При записи через `__setitem__` проверяет: если ключ есть в схеме, значение должно соответствовать указанному типу; иначе выбрасывать `TypeError` с информативным сообщением. 

Ключи, не описанные в схеме, принимаются без проверки. Реализуйте `__repr__` в формате `TypedDict(schema=..., data=...)`.

**Пример использования**:

```python
user_schema = {"username": str, "age": int, "is_active": bool}
d = TypedDict(user_schema)

d["username"] = "alice"     # OK
d["age"] = 28               # OK
d["is_active"] = True       # OK
d["extra"] = "anything"     # OK — нет в схеме

print(dict(d))
# {'username': 'alice', 'age': 28, 'is_active': True, 'extra': 'anything'}

try:
    d["age"] = "двадцать восемь"
except TypeError as e:
    print(e)   # Поле 'age' ожидает тип int, получен str

try:
    d["is_active"] = 1   # int, не bool
except TypeError as e:
    print(e)   # Поле 'is_active' ожидает тип bool, получен int

print(isinstance(d, dict))   # True
```

---

### **Задача 6**. 

Иерархия API-эндпоинтов

Создайте иерархию классов для описания API-эндпоинтов. Базовый класс `APIEndpoint` принимает `path` (строка, путь) и `auth_required` (булево, по умолчанию `True`). 

Добавьте метод `handle(request)`, который принимает словарь `request` и возвращает словарь-ответ. 

В базовой реализации — проверяет наличие ключа `"user"` в `request`, если `auth_required=True` и ключа нет — возвращает `{"error": "Unauthorized", "status": 401}`. Иначе вызывает метод `process(request)`, который нужно переопределить. 

Добавьте `__repr__` в формате `APIEndpoint(path='/api/users', auth=True)`.

Создайте дочерние классы:
- `ListEndpoint(APIEndpoint)` — принимает `items` (список данных). Метод `process()` возвращает `{"data": items, "count": len(items), "status": 200}`.
- `DetailEndpoint(APIEndpoint)` — принимает `items` (словарь `id → объект`). Метод `process()` ищет `request["id"]` в `items`. Если найден — `{"data": объект, "status": 200}`, если нет — `{"error": "Not Found", "status": 404}`.
- `PublicEndpoint(APIEndpoint)` — устанавливает `auth_required=False` по умолчанию, добавляет атрибут `cache_ttl` (время кеширования в секундах).

**Пример использования**:

```python
users_data = {1: {"id": 1, "name": "Alice"}, 2: {"id": 2, "name": "Bob"}}

list_ep = ListEndpoint("/api/users", items=list(users_data.values()))
detail_ep = DetailEndpoint("/api/users/<id>", items=users_data)
public_ep = PublicEndpoint("/api/status", cache_ttl=60)

# Авторизованный запрос
print(list_ep.handle({"user": "alice"}))
# {'data': [...], 'count': 2, 'status': 200}

# Неавторизованный запрос к защищённому эндпоинту
print(list_ep.handle({}))
# {'error': 'Unauthorized', 'status': 401}

# Запрос к публичному без авторизации — OK
print(public_ep.handle({}))

# Детальный запрос
print(detail_ep.handle({"user": "alice", "id": 1}))
# {'data': {'id': 1, 'name': 'Alice'}, 'status': 200}

print(detail_ep.handle({"user": "alice", "id": 99}))
# {'error': 'Not Found', 'status': 404}
```

---

[Предыдущий урок](lesson18.md) | [Следующий урок](lesson20.md)