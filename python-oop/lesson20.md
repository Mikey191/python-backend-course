# Урок 20. Функция `super()` и делегирование методов родителя

---

## План урока

**1. Зачем нужен `super()` — проблема прямого вызова родителя по имени.**
Что происходит, если вместо `super()` написать `ParentClass.method(self, ...)`. Почему это работает в простых случаях, но ломается при переименовании класса, при множественном наследовании и при рефакторинге. `super()` как правильное решение этой проблемы.

**2. Что возвращает `super()` — прокси-объект.**
`super()` не возвращает родительский класс напрямую — он возвращает прокси-объект, который перенаправляет вызовы методов по цепочке MRO. Разница между «вызвать метод родителя» и «вызвать следующий метод по MRO».

**3. Синтаксис `super()` в Python 3.**
`super()` без аргументов — краткий синтаксис, доступный только в Python 3. `super(ClassName, self)` — явный синтаксис Python 2, всё ещё встречается в старом коде. Где можно и нельзя вызывать `super()` без аргументов.

**4. `super()` в `__init__`: делегирование инициализации.**
Правило: всегда вызывать `super().__init__()` в начале дочернего `__init__`. Почему «в начале» — атрибуты родителя нужны дочернему классу с первой строки. Что происходит, если вызвать в конце или не вызвать совсем.

**5. `super()` в обычных методах: расширение поведения.**
Паттерн «обёртка»: дочерний класс делает что-то до вызова родителя, вызывает родителя, делает что-то после. Выбор места вызова `super()` — до или после — определяет логику. Практические примеры с методами `save()`, `validate()`, `send()`.

**6. `super()` и цепочка вызовов при одиночном наследовании.**
Полная трассировка вызовов в трёхуровневой иерархии. Как `super()` в каждом классе передаёт управление следующему по MRO. Почему важно вызывать `super()` на каждом уровне.

**7. Неочевидный момент: `super()` идёт по MRO, а не «вверх к родителю».**
В случае одиночного наследования разницы нет. Но это разные концепции. Подготовка к уроку про множественное наследование: `super()` в классе B не всегда вызывает метод класса A — он может вызвать метод класса C, если C стоит раньше A в MRO.

**8. Практический пример: иерархия валидаторов.**
Класс `BaseValidator` → `TypeValidator` → `RangeValidator`. Каждый уровень добавляет свою проверку через `super().validate()`. Полная цепочка вызовов при валидации данных форм и API.

**9. Практический пример: иерархия middleware.**
Django Middleware как пример делегирования через `super()`. Класс `BaseMiddleware` → `LoggingMiddleware` → `AuthMiddleware`. Как `super().__call__()` передаёт запрос по цепочке обработчиков.

**10. `super()` для доступа к атрибутам класса-родителя.**
`super()` можно использовать не только для методов, но и для обращения к атрибутам класса. Когда это нужно и когда достаточно просто `ParentClass.attr`.

**11. Неочевидные моменты и типичные ошибки.**
Вызов `super().__init__()` после присваивания атрибутов, которые переопределяют метод — ситуация, когда порядок имеет значение. Забытый `super()` в середине иерархии обрывает цепочку. `super()` вне метода класса вызывает `RuntimeError`. Почему нельзя кешировать результат `super()` в атрибут.

**12. Вопросы (8 штук) и задачи (6 штук).**

---

## Зачем нужен `super()` — проблема прямого вызова

В предыдущем уроке мы видели, что дочерний класс может расширить метод родителя, вызвав его внутри переопределённого метода. Самый очевидный способ это сделать — вызвать метод родительского класса напрямую по имени:

```python
class User:
    def __init__(self, username, email):
        self.username = username
        self.email = email

    def get_info(self):
        return f"{self.username} ({self.email})"


class AdminUser(User):
    def __init__(self, username, email, admin_level):
        User.__init__(self, username, email)   # прямой вызов по имени
        self.admin_level = admin_level

    def get_info(self):
        return User.get_info(self) + f" [уровень {self.admin_level}]"   # прямой вызов
```

Это работает. Но у такого подхода есть серьёзные недостатки, которые проявляются при реальной разработке.

**Первый недостаток: привязка к конкретному имени класса.** Если вы переименуете `User` в `BaseUser`, придётся найти и исправить каждое место, где написано `User.__init__(self, ...)` и `User.get_info(self)`. С `super()` этого не нужно — он автоматически найдёт правильный класс.

**Второй недостаток: поломка при множественном наследовании.** Если в иерархии несколько родителей, прямой вызов по имени нарушает цепочку вызовов и некоторые классы могут быть вызваны несколько раз или не вызваны вовсе. `super()` работает корректно в любых иерархиях, потому что следует алгоритму MRO.

**Третий недостаток: хрупкость при рефакторинге.** Представьте, что между `User` и `AdminUser` вы вставляете промежуточный класс `StaffUser`. При прямых вызовах по имени вы разрываете цепочку — `AdminUser` всё ещё вызывает `User`, минуя `StaffUser`. С `super()` цепочка выстраивается автоматически.

`super()` — это правильный и идиоматичный способ обращаться к методам родительских классов в Python.

---

## Что возвращает `super()` — прокси-объект

Это часто вызывает путаницу: студенты думают, что `super()` возвращает объект родительского класса. Это неверно.

`super()` возвращает специальный прокси-объект, который знает две вещи: текущий класс (от которого нужно «начать смотреть выше») и текущий экземпляр. Когда вы вызываете метод на этом прокси-объекте, он ищет метод по MRO, начиная со следующего класса после текущего.

Разница между «вернуть родительский класс» и «вернуть прокси, который ищет по MRO» неважна при одиночном наследовании. Но она критична при множественном наследовании — об этом подробнее в уроке 25. Пока достаточно понимать: `super()` — это не `Parent`, это умный посредник, который следует MRO.

```python
class User:
    def get_info(self):
        return "User"


class AdminUser(User):
    def get_info(self):
        proxy = super()   # прокси-объект, не экземпляр User
        print(type(proxy))      # <class 'super'>
        print(proxy.__class__)  # <class 'super'>
        return proxy.get_info() + " + Admin"


admin = AdminUser("alice", "alice@example.com")
print(admin.get_info())
# <class 'super'>
# <class 'super'>
# User + Admin
```

---

## Синтаксис `super()` в Python 3

В Python 3 можно вызывать `super()` без аргументов — это сокращённый синтаксис, который Python заполняет автоматически:

```python
class AdminUser(User):
    def __init__(self, username, email, admin_level):
        super().__init__(username, email)   # Python 3: без аргументов
        self.admin_level = admin_level
```

В Python 2 (а также если нужно явно указать класс в нестандартных случаях) используется полный синтаксис:

```python
class AdminUser(User):
    def __init__(self, username, email, admin_level):
        super(AdminUser, self).__init__(username, email)   # явный синтаксис
        self.admin_level = admin_level
```

Оба варианта эквивалентны при одиночном наследовании. В Python 3 почти всегда используется краткий вариант без аргументов. Встретив в чужом коде `super(ClassName, self)` — знайте, что это либо старый код, либо специальный случай.

Важное ограничение: `super()` без аргументов работает только внутри метода, определённого в теле класса. Если вы попытаетесь вызвать `super()` вне метода класса или в динамически созданной функции, Python не сможет определить контекст и выбросит `RuntimeError`.

---

## `super()` в `__init__`: делегирование инициализации

Самый распространённый случай использования `super()` — в методе `__init__`. Правило простое: вызывайте `super().__init__()` в самом начале дочернего инициализатора, перед установкой собственных атрибутов.

Почему в начале? Потому что дочерний класс может использовать атрибуты, установленные в родительском `__init__`. Если вызвать `super().__init__()` в конце, собственные методы дочернего класса, вызванные в процессе инициализации, могут не найти нужных атрибутов.

Рассмотрим конкретный пример:

```python
class Connection:
    """Базовый класс соединения с внешним сервисом."""

    def __init__(self, host, port, timeout=30):
        self.host = host
        self.port = port
        self.timeout = timeout
        self._socket = None
        self.is_connected = False
        print(f"[Connection.__init__] host={host}, port={port}")

    def connect(self):
        print(f"[Connection.connect] подключение к {self.host}:{self.port}")
        self.is_connected = True

    def disconnect(self):
        self.is_connected = False
        print(f"[Connection.disconnect] отключение от {self.host}:{self.port}")


class DatabaseConnection(Connection):
    """Соединение с базой данных. Добавляет имя БД и пул соединений."""

    def __init__(self, host, port, database, pool_size=5, timeout=30):
        # Сначала инициализируем родителя — он устанавливает host, port, timeout
        super().__init__(host, port, timeout)
        # Теперь добавляем специфичные атрибуты
        self.database = database
        self.pool_size = pool_size
        self._pool = []
        print(f"[DatabaseConnection.__init__] database={database}, pool={pool_size}")

    def connect(self):
        # Расширяем метод родителя
        super().connect()   # устанавливает is_connected = True
        # После подключения инициализируем пул
        self._pool = [f"conn_{i}" for i in range(self.pool_size)]
        print(f"[DatabaseConnection.connect] пул из {self.pool_size} соединений создан")


class SecureDatabaseConnection(DatabaseConnection):
    """Зашифрованное соединение с БД. Добавляет SSL и аутентификацию."""

    def __init__(self, host, port, database, ssl_cert, pool_size=5):
        super().__init__(host, port, database, pool_size)
        self.ssl_cert = ssl_cert
        self.is_authenticated = False
        print(f"[SecureDatabaseConnection.__init__] ssl_cert={ssl_cert}")

    def connect(self):
        print("[SecureDatabaseConnection.connect] установка SSL...")
        super().connect()   # вызывает DatabaseConnection.connect, затем Connection.connect
        self.is_authenticated = True
        print("[SecureDatabaseConnection.connect] аутентификация завершена")
```

Проследим полную цепочку вызовов:

```python
secure_db = SecureDatabaseConnection(
    host="db.example.com",
    port=5432,
    database="production",
    ssl_cert="path/to/cert.pem"
)
```

Вывод при создании объекта:

```
[Connection.__init__] host=db.example.com, port=5432
[DatabaseConnection.__init__] database=production, pool=5
[SecureDatabaseConnection.__init__] ssl_cert=path/to/cert.pem
```

Вывод при подключении:

```python
secure_db.connect()
```

```
[SecureDatabaseConnection.connect] установка SSL...
[Connection.connect] подключение к db.example.com:5432
[DatabaseConnection.connect] пул из 5 соединений создан
[SecureDatabaseConnection.connect] аутентификация завершена
```

Обратите внимание на порядок: каждый уровень иерархии добавляет свою логику, а `super()` обеспечивает корректную передачу управления. В `__init__` инициализация идёт «сверху вниз» (от самого общего к самому специфичному). В `connect()` — логика «обёртки»: `SecureDatabase` начинает, вызывает `super()`, который вызывает `Database.connect()`, который в свою очередь вызывает `super()` — и только тогда выполняется `Connection.connect()`.

---

## Паттерн «обёртка»: до или после `super()`

Место вызова `super()` в методе определяет, когда выполнится логика родителя относительно логики дочернего класса. Это важное архитектурное решение.

**`super()` в начале — «пост-обработка»:** родительский код выполняется сначала, дочерний добавляет обработку результата.

**`super()` в конце — «пре-обработка»:** дочерний класс выполняет подготовку, затем вызывает родителя.

**`super()` в середине — «обёртка»:** дочерний класс делает что-то до и после.

Рассмотрим на примере валидатора форм:

```python
class BaseValidator:
    """Базовый валидатор. Проверяет, что значение передано."""

    def validate(self, value, field_name="field"):
        print(f"[BaseValidator] проверка {field_name!r}")
        if value is None:
            raise ValueError(f"Поле {field_name!r} не может быть None")
        return True   # базовая проверка пройдена


class TypeValidator(BaseValidator):
    """Валидирует тип значения."""

    def __init__(self, expected_type):
        self.expected_type = expected_type

    def validate(self, value, field_name="field"):
        # Сначала вызываем базовую проверку — она убедится, что value не None
        super().validate(value, field_name)
        # Затем добавляем проверку типа
        print(f"[TypeValidator] проверка типа {self.expected_type.__name__!r}")
        if not isinstance(value, self.expected_type):
            raise TypeError(
                f"Поле {field_name!r} ожидает {self.expected_type.__name__}, "
                f"получен {type(value).__name__}"
            )
        return True


class RangeValidator(TypeValidator):
    """Валидирует числовое значение в диапазоне."""

    def __init__(self, min_val, max_val):
        super().__init__(expected_type=(int, float))
        self.min_val = min_val
        self.max_val = max_val

    def validate(self, value, field_name="field"):
        # Сначала проверяем тип через TypeValidator (который вызовет BaseValidator)
        super().validate(value, field_name)
        # Затем проверяем диапазон
        print(f"[RangeValidator] проверка диапазона [{self.min_val}, {self.max_val}]")
        if not self.min_val <= value <= self.max_val:
            raise ValueError(
                f"Поле {field_name!r} должно быть от {self.min_val} до {self.max_val}, "
                f"получено {value}"
            )
        return True
```

Трассируем цепочку вызовов:

```python
age_validator = RangeValidator(min_val=0, max_val=120)

# Успешная валидация
try:
    age_validator.validate(25, "age")
    print("Валидация прошла успешно")
except (ValueError, TypeError) as e:
    print(f"Ошибка: {e}")

# [BaseValidator] проверка 'age'
# [TypeValidator] проверка типа 'int'  (или 'float')
# [RangeValidator] проверка диапазона [0, 120]
# Валидация прошла успешно

print()

# Ошибка типа
try:
    age_validator.validate("двадцать пять", "age")
except (ValueError, TypeError) as e:
    print(f"Ошибка: {e}")

# [BaseValidator] проверка 'age'
# [TypeValidator] проверка типа 'int'  (или 'float')
# Ошибка: Поле 'age' ожидает int, получен str

print()

# Ошибка диапазона
try:
    age_validator.validate(200, "age")
except (ValueError, TypeError) as e:
    print(f"Ошибка: {e}")

# [BaseValidator] проверка 'age'
# [TypeValidator] проверка типа 'int'  (или 'float')
# [RangeValidator] проверка диапазона [0, 120]
# Ошибка: Поле 'age' должно быть от 0 до 120, получено 200
```

Каждый уровень иерархии добавляет свою проверку, и `super()` обеспечивает, что все проверки выполняются в правильном порядке. Если убрать `super().validate()` из любого класса — цепочка оборвётся и вышестоящие проверки перестанут выполняться.

---

## `super()` и цепочка вызовов при одиночном наследовании

Чтобы окончательно закрепить понимание, проследим полную трассировку вызовов в трёхуровневой иерархии на конкретном примере с HTTP-запросами:

```python
class BaseHandler:
    """Базовый обработчик HTTP-запросов."""

    def handle(self, request):
        print(f"[BaseHandler.handle] начало обработки {request['method']} {request['path']}")
        response = self.process(request)
        print(f"[BaseHandler.handle] ответ: {response['status']}")
        return response

    def process(self, request):
        return {"status": 200, "body": "OK"}


class LoggingHandler(BaseHandler):
    """Добавляет логирование запросов."""

    def handle(self, request):
        print(f"[LoggingHandler.handle] → запрос получен")
        response = super().handle(request)   # вызывает BaseHandler.handle
        print(f"[LoggingHandler.handle] ← ответ {response['status']} отправлен")
        return response


class AuthHandler(LoggingHandler):
    """Добавляет аутентификацию перед обработкой."""

    def handle(self, request):
        # Пре-обработка: проверяем авторизацию
        if "Authorization" not in request.get("headers", {}):
            print("[AuthHandler.handle] ✗ отказано в доступе")
            return {"status": 401, "body": "Unauthorized"}

        print("[AuthHandler.handle] ✓ аутентификация прошла")
        # Передаём управление вниз по MRO (LoggingHandler → BaseHandler)
        response = super().handle(request)
        # Пост-обработка: добавляем заголовок безопасности в ответ
        response["headers"] = {"X-Auth": "verified"}
        return response
```

Трассируем вызовы для авторизованного запроса:

```python
handler = AuthHandler()

authorized_request = {
    "method": "GET",
    "path": "/api/users",
    "headers": {"Authorization": "Bearer token123"}
}

response = handler.handle(authorized_request)
print(f"\nФинальный ответ: {response}")
```

```
[AuthHandler.handle] ✓ аутентификация прошла
[LoggingHandler.handle] → запрос получен
[BaseHandler.handle] начало обработки GET /api/users
[BaseHandler.handle] ответ: 200
[LoggingHandler.handle] ← ответ 200 отправлен

Финальный ответ: {'status': 200, 'body': 'OK', 'headers': {'X-Auth': 'verified'}}
```

Обратите внимание на структуру вызовов: это не просто «вызвать родителя». Это цепочка обёрток, каждая из которых выполняет свою часть логики до и/или после передачи управления следующему звену. Именно такая архитектура используется в системе middleware Django: каждый middleware «оборачивает» следующий, добавляя свою обработку запроса и ответа.

---

## Неочевидный момент: `super()` идёт по MRO, а не «к родителю»

В контексте одиночного наследования «следующий по MRO» всегда совпадает с «родительским классом». Но это разные концепции, и их важно различать уже сейчас.

Рассмотрим простой пример, который демонстрирует это:

```python
class A:
    def greet(self):
        print("A.greet")


class B(A):
    def greet(self):
        print("B.greet")
        super().greet()   # кто вызывается здесь?


class C(A):
    def greet(self):
        print("C.greet")
        super().greet()


class D(B, C):   # множественное наследование
    def greet(self):
        print("D.greet")
        super().greet()


# MRO для D: D → B → C → A → object
print(D.__mro__)
# (<class 'D'>, <class 'B'>, <class 'C'>, <class 'A'>, <class 'object'>)

d = D()
d.greet()
```

Вывод:

```
D.greet
B.greet
C.greet
A.greet
```

Когда `B.greet()` вызывает `super().greet()` — управление идёт не к `A` (прямому родителю `B`), а к `C` — следующему по MRO объекта `D`. Это контринтуитивно, если думать о `super()` как о «вызове родителя». Но это абсолютно корректно, если понимать `super()` как «следующий по MRO».

Этот пример мы разберём полностью в уроке про множественное наследование. Сейчас важно запомнить один принцип: **в классах, которые могут использоваться в иерархиях с множественным наследованием, всегда нужно вызывать `super()`** — даже если кажется, что следующий шаг — это `object`. Именно так вся цепочка остаётся целой.

---

## Практический пример: иерархия middleware

Паттерн middleware — один из самых важных в веб-разработке. Django обрабатывает каждый HTTP-запрос через цепочку middleware-классов, каждый из которых может модифицировать запрос, ответ или прервать обработку. Давайте реализуем упрощённую версию этой системы:

```python
import time


class BaseMiddleware:
    """
    Базовый middleware. Принимает следующий обработчик в цепочке.
    Паттерн: каждый middleware оборачивает следующий.
    """

    def __init__(self, get_response):
        # get_response — это следующий обработчик в цепочке
        # (другой middleware или финальный view-обработчик)
        self.get_response = get_response

    def __call__(self, request):
        # Базовая реализация просто передаёт запрос дальше
        return self.get_response(request)


class TimingMiddleware(BaseMiddleware):
    """Измеряет время обработки каждого запроса."""

    def __call__(self, request):
        start_time = time.perf_counter()

        # Передаём запрос дальше по цепочке
        response = super().__call__(request)

        # После получения ответа — добавляем заголовок с временем обработки
        elapsed = time.perf_counter() - start_time
        response["X-Processing-Time"] = f"{elapsed * 1000:.2f}ms"
        print(f"[Timing] {request['path']}: {elapsed * 1000:.2f}ms")

        return response


class LoggingMiddleware(BaseMiddleware):
    """Логирует все входящие запросы и исходящие ответы."""

    def __call__(self, request):
        print(f"[Logging] → {request['method']} {request['path']}")

        response = super().__call__(request)

        print(f"[Logging] ← {response['status']}")
        return response


class AuthMiddleware(BaseMiddleware):
    """Проверяет аутентификацию. При неуспехе — прерывает цепочку."""

    PUBLIC_PATHS = {"/", "/health", "/login"}

    def __call__(self, request):
        path = request.get("path", "/")

        # Публичные пути — пропускаем без проверки
        if path in self.PUBLIC_PATHS:
            return super().__call__(request)

        # Проверяем токен
        token = request.get("headers", {}).get("Authorization")
        if not token:
            # Прерываем цепочку — дальнейшие middleware не вызываются
            print(f"[Auth] ✗ нет токена для {path}")
            return {"status": 401, "body": "Unauthorized", "headers": {}}

        print(f"[Auth] ✓ токен проверен")
        request["user"] = self._get_user_from_token(token)
        return super().__call__(request)

    def _get_user_from_token(self, token):
        # Упрощённая имитация получения пользователя по токену
        return {"id": 1, "username": "alice", "role": "admin"}


def final_view(request):
    """Финальный обработчик — имитация view-функции."""
    user = request.get("user", {})
    return {
        "status": 200,
        "body": f"Привет, {user.get('username', 'гость')}!",
        "headers": {}
    }


# Собираем цепочку middleware (как это делает Django)
# Порядок: последний добавленный оборачивает финальный view первым
pipeline = AuthMiddleware(
    LoggingMiddleware(
        TimingMiddleware(
            final_view
        )
    )
)
```

Тестируем цепочку:

```python
# Авторизованный запрос
print("=== Запрос с токеном ===")
request1 = {
    "method": "GET",
    "path": "/api/users",
    "headers": {"Authorization": "Bearer secret-token"}
}
response1 = pipeline(request1)
print(f"Ответ: {response1['body']}\n")

# Неавторизованный запрос
print("=== Запрос без токена ===")
request2 = {
    "method": "GET",
    "path": "/api/users",
    "headers": {}
}
response2 = pipeline(request2)
print(f"Ответ: {response2['status']}\n")

# Публичный путь — без проверки авторизации
print("=== Публичный путь ===")
request3 = {
    "method": "GET",
    "path": "/health",
    "headers": {}
}
response3 = pipeline(request3)
print(f"Ответ: {response3['status']}")
```

Вывод:

```
=== Запрос с токеном ===
[Auth] ✓ токен проверен
[Logging] → GET /api/users
[Timing] /api/users: 0.03ms
[Logging] ← 200
Ответ: Привет, alice!

=== Запрос без токена ===
[Auth] ✗ нет токена для /api/users
Ответ: 401

=== Публичный путь ===
[Logging] → GET /health
[Timing] /health: 0.02ms
[Logging] ← 200
Ответ: 200
```

Обратите внимание: при неавторизованном запросе `LoggingMiddleware` и `TimingMiddleware` вообще не вызываются — `AuthMiddleware` прерывает цепочку, вернув ответ без вызова `super().__call__()`. Это именно тот контроль, который нужен при проектировании систем безопасности.

---

## Практический пример: иерархия сериализаторов

Рассмотрим ещё один практический пример — иерархию сериализаторов, аналогичную тому, как устроены сериализаторы в Django REST Framework:

```python
class BaseSerializer:
    """
    Базовый сериализатор. Знает только об общих полях.
    """

    def __init__(self, data):
        self._data = data
        self._errors = {}

    def validate(self):
        """Возвращает True если данные корректны, иначе заполняет _errors."""
        if not isinstance(self._data, dict):
            self._errors["non_field_error"] = "Ожидается словарь"
            return False
        return True

    def to_representation(self):
        """Преобразует данные для ответа API."""
        return dict(self._data)

    @property
    def errors(self):
        return self._errors

    @property
    def is_valid(self):
        return len(self._errors) == 0


class UserSerializer(BaseSerializer):
    """
    Сериализатор пользователя. Добавляет валидацию обязательных полей.
    """

    REQUIRED_FIELDS = {"username", "email"}

    def validate(self):
        # Сначала выполняем базовую проверку через super()
        if not super().validate():
            return False

        # Затем проверяем обязательные поля
        for field in self.REQUIRED_FIELDS:
            if field not in self._data:
                self._errors[field] = f"Поле '{field}' обязательно"

        if "email" in self._data and "@" not in self._data["email"]:
            self._errors["email"] = "Некорректный email"

        return self.is_valid

    def to_representation(self):
        # Берём базовое представление от родителя
        data = super().to_representation()
        # Убираем чувствительные поля из ответа
        data.pop("password", None)
        data.pop("password_hash", None)
        return data


class AdminUserSerializer(UserSerializer):
    """
    Сериализатор администратора. Добавляет поле admin_level.
    """

    def validate(self):
        # Сначала выполняем всю валидацию UserSerializer
        if not super().validate():
            return False

        # Дополнительная проверка для администраторов
        admin_level = self._data.get("admin_level", 1)
        if not isinstance(admin_level, int) or not 1 <= admin_level <= 3:
            self._errors["admin_level"] = "Уровень администратора: от 1 до 3"

        return self.is_valid

    def to_representation(self):
        data = super().to_representation()
        # Для администраторов добавляем вычисляемое поле
        data["permissions_count"] = len(data.get("permissions", []))
        return data
```

Демонстрация:

```python
# Корректные данные для обычного пользователя
user_data = {
    "username": "alice",
    "email": "alice@example.com",
    "password": "secret123",  # будет удалён из ответа
}
serializer = UserSerializer(user_data)
if serializer.validate():
    print("Данные корректны:", serializer.to_representation())
else:
    print("Ошибки:", serializer.errors)
# Данные корректны: {'username': 'alice', 'email': 'alice@example.com'}

print()

# Данные администратора с ошибкой
admin_data = {
    "username": "bob",
    "email": "not-an-email",    # некорректный email
    "admin_level": 5,           # некорректный уровень
}
admin_serializer = AdminUserSerializer(admin_data)
if admin_serializer.validate():
    print("Данные корректны")
else:
    print("Ошибки:", admin_serializer.errors)
# Ошибки: {'email': 'Некорректный email', 'admin_level': 'Уровень администратора: от 1 до 3'}
```

---

## `super()` для доступа к атрибутам класса

`super()` можно использовать не только для методов, но и для доступа к атрибутам класса. Это полезно, когда дочерний класс переопределяет атрибут, но нужно обратиться к исходному значению:

```python
class HTTPResponse:
    DEFAULT_HEADERS = {
        "Content-Type": "text/plain",
        "X-Frame-Options": "DENY",
    }

    def get_headers(self):
        return dict(self.DEFAULT_HEADERS)


class JSONResponse(HTTPResponse):
    DEFAULT_HEADERS = {
        **HTTPResponse.DEFAULT_HEADERS,  # берём родительские заголовки
        "Content-Type": "application/json",  # переопределяем Content-Type
    }

    def get_headers(self):
        # Один из способов: обратиться к атрибуту родителя через super()
        parent_headers = super().DEFAULT_HEADERS   # атрибут класса родителя
        return {**parent_headers, "Content-Type": "application/json"}
```

Однако для атрибутов класса чаще используют прямое обращение по имени класса (`HTTPResponse.DEFAULT_HEADERS`), а `super()` оставляют для методов. Это более читаемо и явно.

---

## Неочевидные моменты и типичные ошибки

**Порядок вызова `super().__init__()` имеет значение.** Если какой-то атрибут, установленный дочерним классом, используется в методе, вызываемом в `super().__init__()` — нужно установить этот атрибут до вызова `super()`. В противном случае атрибут не будет существовать в момент, когда он нужен:

```python
class Base:
    def __init__(self):
        self.setup()   # вызывается в __init__ родителя!

    def setup(self):
        print("Base.setup")


class Child(Base):
    def __init__(self, config):
        # НЕВЕРНО: self.config ещё не установлен, когда Base.__init__
        # вызовет self.setup(), а setup() может обращаться к self.config
        super().__init__()
        self.config = config   # слишком поздно!

    def setup(self):
        # Здесь self.config не существует — AttributeError
        print(f"Child.setup: {self.config}")


# ВЕРНО: устанавливаем config до вызова super()
class FixedChild(Base):
    def __init__(self, config):
        self.config = config   # сначала устанавливаем атрибут
        super().__init__()     # теперь Base.__init__ → self.setup() найдёт self.config

    def setup(self):
        print(f"FixedChild.setup: {self.config}")


fixed = FixedChild({"debug": True})
# FixedChild.setup: {'debug': True}
```

**Пропуск `super()` в середине иерархии обрывает цепочку.** Если в трёхуровневой иерархии средний класс не вызывает `super()`, верхний класс никогда не получит управления:

```python
class A:
    def process(self):
        print("A.process")  # никогда не будет вызван

class B(A):
    def process(self):
        print("B.process")
        # super().process() — ЗАБЫЛИ!  Цепочка оборвана

class C(B):
    def process(self):
        print("C.process")
        super().process()   # вызывает B.process, но не A.process

C().process()
# C.process
# B.process
# (A.process не выполнилась — цепочка прервана в B)
```

**`super()` нельзя вызвать вне метода класса.** Вызов `super()` без аргументов использует магию компилятора Python — ячейку `__class__` — которая доступна только внутри методов, объявленных в теле класса. Попытка использовать `super()` в обычной функции или вне класса приводит к `RuntimeError`:

```python
def standalone_function():
    return super()   # RuntimeError: super(): no arguments

# Также нельзя присвоить результат super() в атрибут и вызвать позже:
class MyClass:
    def __init__(self):
        self._super = super()   # сохраняем прокси

    def method(self):
        # self._super.some_method()  — может работать некорректно в
        # зависимости от контекста, лучше не делать так
        pass
```

---

## Итоги урока

`super()` — это не просто удобный способ вызвать метод родителя. Это инструмент, который следует MRO и обеспечивает корректную работу в любых иерархиях наследования, включая множественное.

Главные правила: вызывайте `super().__init__()` в начале дочернего `__init__`, вызывайте `super()` в каждом методе, который его нужен — пропуск в середине иерархии обрывает цепочку, и используйте `super()` вместо прямого обращения к родительскому классу по имени.

Паттерн «обёртка» — самое распространённое применение `super()`. Дочерний класс выполняет логику до и/или после вызова родительского метода. Именно на этом принципе построены системы middleware в Django.

В следующем уроке мы рассмотрим поведение атрибутов `private` и `protected` при наследовании — включая механизм name mangling и практические последствия для проектирования классов.

---

## Контрольные вопросы

**Вопрос 1.** Почему вызов родительского метода через `ParentClass.method(self, ...)` хуже, чем через `super().method(...)`? Назовите три недостатка прямого вызова.

> **Ответ.** Первый: привязка к конкретному имени класса — при переименовании родителя придётся исправлять все прямые вызовы. Второй: поломка при множественном наследовании — прямой вызов нарушает MRO и может привести к тому, что часть классов в иерархии будет вызвана дважды или не вызвана совсем. Третий: хрупкость при рефакторинге — вставка промежуточного класса в иерархию разрывает цепочку, потому что дочерний класс обходит промежуточный, обращаясь напрямую к более далёкому предку.

---

**Вопрос 2.** Что возвращает вызов `super()`? Это экземпляр родительского класса?

> **Ответ.** Нет. `super()` возвращает специальный прокси-объект типа `super`. Этот объект знает текущий класс и текущий экземпляр, и при вызове метода на нём ищет метод по MRO, начиная со следующего класса после текущего. Это принципиально отличается от «экземпляра родительского класса» — именно поэтому `super()` корректно работает при множественном наследовании.

---

**Вопрос 3.** Почему рекомендуется вызывать `super().__init__()` в начале дочернего `__init__`, а не в конце?

> **Ответ.** Если родительский `__init__` вызывает какой-либо метод, переопределённый в дочернем классе (например, `setup()`), то дочерняя реализация этого метода может обращаться к атрибутам, установленным в `__init__` дочернего класса. Если `super().__init__()` вызывается в конце — эти атрибуты ещё не существуют в момент вызова, что приводит к `AttributeError`. Вызов в начале гарантирует, что атрибуты родителя инициализированы до того, как дочерний класс начнёт с ними работать.

---

**Вопрос 4.** Что произойдёт, если в трёхуровневой иерархии `C → B → A` класс `B` не вызывает `super().process()` в своём методе `process()`?

> **Ответ.** Цепочка вызовов оборвётся на классе `B`. Когда `C.process()` вызовет `super().process()`, выполнится `B.process()`. Но поскольку `B.process()` не вызывает `super()`, метод `A.process()` никогда не будет выполнен. Это распространённая ошибка при рефакторинге — разработчик добавляет промежуточный класс и забывает вызвать `super()`, тем самым прерывая цепочку.

---

**Вопрос 5.** Как выбор места вызова `super()` (до или после собственного кода метода) влияет на поведение?

> **Ответ.** Если `super()` вызывается в начале метода — родительский код выполняется сначала, а дочерний код является «пост-обработкой». Если в конце — дочерний код является «пре-обработкой», а родитель вызывается после. Если `super()` вызывается в середине — это «обёртка»: дочерний код выполняется и до, и после родительского. Выбор определяется логикой: например, в `__init__` почти всегда `super()` первым (чтобы атрибуты родителя были доступны), в `save()` с валидацией — `super()` после проверок.

---

**Вопрос 6.** Чем `super()` в классе `B` отличается при вызове `b = B()` и при вызове `d = D()`, где `D` наследует от `B` и `C`? Почему важно это понимать?

> **Ответ.** В первом случае `super()` в `B.method()` будет указывать на следующий класс по MRO объекта `b` — то есть на `A` (прямого родителя `B`). Во втором случае MRO объекта `d` другое: `D → B → C → A`. Поэтому `super()` в `B.method()` при вызове через объект `D` будет указывать на `C`, а не на `A`. Это означает, что `super()` в классе `B` не всегда вызывает один и тот же следующий класс — это зависит от полного MRO конкретного объекта. Именно поэтому «следующий по MRO» и «родительский класс» — разные концепции.

---

**Вопрос 7.** Можно ли вызвать `super()` без аргументов вне метода класса? Что произойдёт?

> **Ответ.** Нет, нельзя. `super()` без аргументов использует специальный механизм Python — неявную переменную `__class__`, которая создаётся компилятором только внутри методов, объявленных в теле класса. При вызове `super()` вне такого контекста Python не может определить, к какому классу относится вызов, и выбросит `RuntimeError: super(): __class__ cell not found`.

---

**Вопрос 8.** В примере с middleware из лекции `AuthMiddleware` при неавторизованном запросе не вызывает `super().__call__()`. Что это означает для цепочки обработки?

> **Ответ.** Это означает, что цепочка middleware прерывается: последующие middleware (`LoggingMiddleware`, `TimingMiddleware`) и финальный view-обработчик не вызываются вообще. `AuthMiddleware` сразу возвращает ответ `401 Unauthorized`. Именно такое поведение и нужно: нет смысла логировать время обработки или выполнять бизнес-логику, если запрос не прошёл аутентификацию. Это один из паттернов использования `super()`: дочерний класс может принять решение не передавать управление дальше по цепочке.

---

## Практические задачи

### Задача 1. Класс `ColoredPoint`

Создайте базовый класс `Point` с атрибутами `x` и `y` (числа) и методами `move(dx, dy)` (смещение), `distance_to_origin()` (расстояние до начала координат) и `__str__` в формате `"(x, y)"`. Создайте дочерний класс `ColoredPoint(Point)`, который добавляет атрибут `color` (строка). В `__init__` используйте `super().__init__()`. Переопределите `__str__` так, чтобы он возвращал строку в формате `"(x, y) [color]"`, используя `super().__str__()` для получения базовой части. Переопределите `move()` так, чтобы он выводил сообщение о перемещении вида `"Перемещаем [color] точку"` до вызова `super().move()`.

Пример использования:

```python
p = Point(1, 2)
cp = ColoredPoint(3, 4, "red")

print(p)    # (1, 2)
print(cp)   # (3, 4) [red]

cp.move(1, 1)
# Перемещаем red точку
print(cp)   # (4, 5) [red]

print(isinstance(cp, Point))        # True
print(isinstance(cp, ColoredPoint)) # True
```

**Решение:**

```python
import math


class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def move(self, dx, dy):
        self.x += dx
        self.y += dy

    def distance_to_origin(self):
        return math.sqrt(self.x ** 2 + self.y ** 2)

    def __str__(self):
        return f"({self.x}, {self.y})"

    def __repr__(self):
        return f"Point({self.x}, {self.y})"


class ColoredPoint(Point):
    def __init__(self, x, y, color):
        super().__init__(x, y)
        self.color = color

    def move(self, dx, dy):
        print(f"Перемещаем {self.color} точку")
        super().move(dx, dy)

    def __str__(self):
        return f"{super().__str__()} [{self.color}]"

    def __repr__(self):
        return f"ColoredPoint({self.x}, {self.y}, {self.color!r})"


p = Point(1, 2)
cp = ColoredPoint(3, 4, "red")

print(p)       # (1, 2)
print(cp)      # (3, 4) [red]

cp.move(1, 1)  # Перемещаем red точку
print(cp)      # (4, 5) [red]

print(isinstance(cp, Point))   # True
```

---

### Задача 2. Иерархия логгеров

Создайте иерархию классов для системы логирования. Базовый класс `Logger` принимает `name` (строка) и хранит список сообщений `self.messages = []`. Метод `log(level, message)` добавляет в список словарь `{"level": level, "message": message}` и выводит строку `"[level] message"`. Создайте дочерний класс `FileLogger(Logger)`, который дополнительно принимает `filepath` (строка) и переопределяет `log()` — сначала вызывает `super().log()`, затем выводит `"[File → filepath] записано"`. Создайте `FilteredLogger(Logger)`, который принимает `min_level` (строка: `"DEBUG"`, `"INFO"`, `"WARNING"`, `"ERROR"`) и переопределяет `log()` — пропускает сообщения ниже минимального уровня (порядок уровней: `DEBUG < INFO < WARNING < ERROR`), для остальных вызывает `super().log()`.

Пример использования:

```python
base = Logger("app")
base.log("INFO", "Приложение запущено")
# [INFO] Приложение запущено

file_log = FileLogger("app", "app.log")
file_log.log("ERROR", "Ошибка подключения")
# [ERROR] Ошибка подключения
# [File → app.log] записано

filtered = FilteredLogger("app", min_level="WARNING")
filtered.log("DEBUG", "Отладочное сообщение")   # игнорируется
filtered.log("WARNING", "Предупреждение")
# [WARNING] Предупреждение

print(len(filtered.messages))   # 1 — только WARNING записано
```

**Решение:**

```python
class Logger:
    LEVELS = {"DEBUG": 0, "INFO": 1, "WARNING": 2, "ERROR": 3}

    def __init__(self, name):
        self.name = name
        self.messages = []

    def log(self, level, message):
        self.messages.append({"level": level, "message": message})
        print(f"[{level}] {message}")


class FileLogger(Logger):
    def __init__(self, name, filepath):
        super().__init__(name)
        self.filepath = filepath

    def log(self, level, message):
        super().log(level, message)
        print(f"[File → {self.filepath}] записано")


class FilteredLogger(Logger):
    def __init__(self, name, min_level="DEBUG"):
        super().__init__(name)
        self.min_level = min_level

    def log(self, level, message):
        min_rank = self.LEVELS.get(self.min_level, 0)
        msg_rank = self.LEVELS.get(level, 0)
        if msg_rank < min_rank:
            return   # пропускаем — не вызываем super()
        super().log(level, message)


base = Logger("app")
base.log("INFO", "Приложение запущено")

file_log = FileLogger("app", "app.log")
file_log.log("ERROR", "Ошибка подключения")

filtered = FilteredLogger("app", min_level="WARNING")
filtered.log("DEBUG", "Отладочное сообщение")
filtered.log("WARNING", "Предупреждение")
print(len(filtered.messages))   # 1
```

---

### Задача 3. Иерархия форм

Создайте иерархию классов для обработки HTML-форм. Базовый класс `Form` принимает `data` (словарь) и хранит `self._errors = {}`. Метод `validate()` возвращает `True` если `_errors` пуст, и `False` иначе. Метод `clean()` возвращает словарь с очищенными данными (по умолчанию — копия `data`). Метод `save()` вызывает `clean()` и выводит сообщение о сохранении.

Создайте `RegistrationForm(Form)`, который добавляет проверки в `validate()` через `super().validate()`: обязательные поля `username`, `email`, `password`; email должен содержать `@`; пароль не короче 8 символов. Метод `clean()` вызывает `super().clean()` и удаляет поле `password` из результата (не возвращаем пароль).

Создайте `AdminRegistrationForm(RegistrationForm)`, который дополнительно проверяет наличие поля `admin_code` и его равенство строке `"SECRET2024"`. Метод `clean()` вызывает `super().clean()` и добавляет поле `role = "admin"`.

Пример использования:

```python
data = {"username": "alice", "email": "alice@example.com", "password": "secure123"}
form = RegistrationForm(data)
if form.validate():
    print(form.clean())
# {'username': 'alice', 'email': 'alice@example.com'}

admin_data = {**data, "admin_code": "SECRET2024"}
admin_form = AdminRegistrationForm(admin_data)
if admin_form.validate():
    print(admin_form.clean())
# {'username': 'alice', 'email': 'alice@example.com', 'role': 'admin'}
```

**Решение:**

```python
class Form:
    def __init__(self, data):
        self._data = data
        self._errors = {}

    def validate(self):
        return len(self._errors) == 0

    def clean(self):
        return dict(self._data)

    def save(self):
        cleaned = self.clean()
        print(f"Сохраняем: {cleaned}")
        return cleaned

    @property
    def errors(self):
        return self._errors


class RegistrationForm(Form):
    REQUIRED = {"username", "email", "password"}

    def validate(self):
        for field in self.REQUIRED:
            if not self._data.get(field):
                self._errors[field] = "Обязательное поле"

        email = self._data.get("email", "")
        if email and "@" not in email:
            self._errors["email"] = "Некорректный email"

        password = self._data.get("password", "")
        if password and len(password) < 8:
            self._errors["password"] = "Пароль не короче 8 символов"

        return super().validate()

    def clean(self):
        data = super().clean()
        data.pop("password", None)
        return data


class AdminRegistrationForm(RegistrationForm):
    ADMIN_CODE = "SECRET2024"

    def validate(self):
        result = super().validate()
        # Проверяем admin_code независимо от результата родителя
        code = self._data.get("admin_code")
        if code != self.ADMIN_CODE:
            self._errors["admin_code"] = "Неверный код администратора"
        return len(self._errors) == 0

    def clean(self):
        data = super().clean()
        data.pop("admin_code", None)
        data["role"] = "admin"
        return data


data = {"username": "alice", "email": "alice@example.com", "password": "secure123"}
form = RegistrationForm(data)
if form.validate():
    print(form.clean())

admin_data = {**data, "admin_code": "SECRET2024"}
admin_form = AdminRegistrationForm(admin_data)
if admin_form.validate():
    print(admin_form.clean())
else:
    print("Ошибки:", admin_form.errors)
```

---

### Задача 4. Иерархия репозиториев

Создайте иерархию классов для работы с данными в стиле паттерна Repository. Базовый класс `BaseRepository` хранит данные в словаре `self._store = {}` (ключ — id). Методы: `save(entity)` (принимает словарь с полем `id`, сохраняет в `_store`, выводит `"Сохранено: id"`), `find(id)` (возвращает объект или `None`), `delete(id)` (удаляет, выводит `"Удалено: id"`), `all()` (возвращает список всех объектов).

Создайте `LoggedRepository(BaseRepository)`, который переопределяет `save()`, `find()` и `delete()` через `super()`, добавляя логирование вида `"[LOG] save id=..."`, `"[LOG] find id=..."`, `"[LOG] delete id=..."` до вызова родительского метода.

Создайте `CachedRepository(LoggedRepository)`, который добавляет `self._cache = {}` и переопределяет `find()`: сначала ищет в кеше, если не найдено — вызывает `super().find()` и сохраняет результат в кеше. Переопределяет `save()` и `delete()` так, чтобы инвалидировать кеш при изменении данных.

Пример использования:

```python
repo = CachedRepository()

repo.save({"id": 1, "name": "Alice"})
# [LOG] save id=1
# Сохранено: 1

result = repo.find(1)
# [LOG] find id=1
print(result)  # {'id': 1, 'name': 'Alice'}

# Второй find — из кеша, без лога
result2 = repo.find(1)
print(result2)  # {'id': 1, 'name': 'Alice'}
# (логирования нет — взято из кеша)

repo.delete(1)
# [LOG] delete id=1
# Удалено: 1
```

**Решение:**

```python
class BaseRepository:
    def __init__(self):
        self._store = {}

    def save(self, entity):
        self._store[entity["id"]] = entity
        print(f"Сохранено: {entity['id']}")

    def find(self, id):
        return self._store.get(id)

    def delete(self, id):
        if id in self._store:
            del self._store[id]
            print(f"Удалено: {id}")

    def all(self):
        return list(self._store.values())


class LoggedRepository(BaseRepository):
    def save(self, entity):
        print(f"[LOG] save id={entity['id']}")
        super().save(entity)

    def find(self, id):
        print(f"[LOG] find id={id}")
        return super().find(id)

    def delete(self, id):
        print(f"[LOG] delete id={id}")
        super().delete(id)


class CachedRepository(LoggedRepository):
    def __init__(self):
        super().__init__()
        self._cache = {}

    def save(self, entity):
        # Инвалидируем кеш при сохранении
        self._cache.pop(entity["id"], None)
        super().save(entity)

    def find(self, id):
        if id in self._cache:
            # Возвращаем из кеша — без логирования
            return self._cache[id]
        # Не в кеше — идём в хранилище через super() (с логированием)
        result = super().find(id)
        if result is not None:
            self._cache[id] = result
        return result

    def delete(self, id):
        self._cache.pop(id, None)
        super().delete(id)


repo = CachedRepository()
repo.save({"id": 1, "name": "Alice"})
result = repo.find(1)
print(result)
result2 = repo.find(1)   # из кеша — без лога
print(result2)
repo.delete(1)
```

---

### Задача 5. Иерархия обработчиков платежей

Создайте иерархию классов для обработки платежей. Базовый класс `PaymentProcessor` принимает `amount` (число) и `currency` (строка). Метод `process()` выводит `"Обработка платежа: amount currency"` и возвращает словарь `{"success": True, "amount": amount, "currency": currency}`. Метод `validate()` возвращает `True`, если `amount > 0`.

Создайте `FeePaymentProcessor(PaymentProcessor)`, который принимает дополнительно `fee_percent` (процент комиссии, число). Переопределите `process()`: сначала вызывает `super().process()`, затем рассчитывает комиссию и добавляет в результат поля `fee` и `total`. Переопределите `validate()` — вызывает `super().validate()` и дополнительно проверяет `0 <= fee_percent <= 100`.

Создайте `LoggedPaymentProcessor(FeePaymentProcessor)`, который переопределяет `process()`: выводит `"[LOG] Начало транзакции"` до `super().process()` и `"[LOG] Транзакция завершена: success"` после.

Пример использования:

```python
proc = LoggedPaymentProcessor(amount=1000, currency="RUB", fee_percent=2.5)

if proc.validate():
    result = proc.process()
    print(result)

# [LOG] Начало транзакции
# Обработка платежа: 1000 RUB
# [LOG] Транзакция завершена: True
# {'success': True, 'amount': 1000, 'currency': 'RUB', 'fee': 25.0, 'total': 1025.0}
```

**Решение:**

```python
class PaymentProcessor:
    def __init__(self, amount, currency):
        self.amount = amount
        self.currency = currency

    def validate(self):
        return self.amount > 0

    def process(self):
        print(f"Обработка платежа: {self.amount} {self.currency}")
        return {
            "success": True,
            "amount": self.amount,
            "currency": self.currency,
        }


class FeePaymentProcessor(PaymentProcessor):
    def __init__(self, amount, currency, fee_percent):
        super().__init__(amount, currency)
        self.fee_percent = fee_percent

    def validate(self):
        return super().validate() and 0 <= self.fee_percent <= 100

    def process(self):
        result = super().process()
        fee = round(self.amount * self.fee_percent / 100, 2)
        result["fee"] = fee
        result["total"] = round(self.amount + fee, 2)
        return result


class LoggedPaymentProcessor(FeePaymentProcessor):
    def process(self):
        print("[LOG] Начало транзакции")
        result = super().process()
        print(f"[LOG] Транзакция завершена: {result['success']}")
        return result


proc = LoggedPaymentProcessor(amount=1000, currency="RUB", fee_percent=2.5)

if proc.validate():
    result = proc.process()
    print(result)
```

---

### Задача 6. Иерархия экспортёров данных

Создайте иерархию классов для экспорта данных в разные форматы. Базовый класс `DataExporter` принимает `data` (список словарей) и `filename` (строка). Метод `export()` вызывает `prepare()`, затем `write()` и выводит `"Экспортировано в filename"`. Метод `prepare()` возвращает данные без изменений. Метод `write(prepared_data)` выводит `"Запись N записей"`.

Создайте `FilteredExporter(DataExporter)`, который принимает дополнительно `filter_fn` (функция-предикат). Переопределяет `prepare()`: вызывает `super().prepare()`, затем фильтрует данные через `filter_fn`.

Создайте `TransformedExporter(FilteredExporter)`, который принимает `transform_fn` (функция преобразования). Переопределяет `prepare()`: вызывает `super().prepare()` (включая фильтрацию), затем применяет `transform_fn` к каждому элементу.

Создайте `CSVExporter(TransformedExporter)`, который переопределяет `write()`, добавляя к выводу `"[CSV]"` и имитацию записи заголовка.

Пример использования:

```python
users = [
    {"id": 1, "name": "Alice", "age": 30, "active": True},
    {"id": 2, "name": "Bob",   "age": 17, "active": True},
    {"id": 3, "name": "Carol", "age": 25, "active": False},
    {"id": 4, "name": "Dave",  "age": 22, "active": True},
]

exporter = CSVExporter(
    data=users,
    filename="active_adults.csv",
    filter_fn=lambda u: u["active"] and u["age"] >= 18,
    transform_fn=lambda u: {"name": u["name"], "age": u["age"]}
)

exporter.export()
# [CSV] Заголовки: name, age
# Запись 2 записей
# Экспортировано в active_adults.csv
```

**Решение:**

```python
class DataExporter:
    def __init__(self, data, filename):
        self.data = data
        self.filename = filename

    def prepare(self):
        return list(self.data)

    def write(self, prepared_data):
        print(f"Запись {len(prepared_data)} записей")

    def export(self):
        prepared = self.prepare()
        self.write(prepared)
        print(f"Экспортировано в {self.filename}")


class FilteredExporter(DataExporter):
    def __init__(self, data, filename, filter_fn=None):
        super().__init__(data, filename)
        self.filter_fn = filter_fn or (lambda x: True)

    def prepare(self):
        data = super().prepare()
        return [item for item in data if self.filter_fn(item)]


class TransformedExporter(FilteredExporter):
    def __init__(self, data, filename, filter_fn=None, transform_fn=None):
        super().__init__(data, filename, filter_fn)
        self.transform_fn = transform_fn or (lambda x: x)

    def prepare(self):
        data = super().prepare()   # уже отфильтрованные данные
        return [self.transform_fn(item) for item in data]


class CSVExporter(TransformedExporter):
    def write(self, prepared_data):
        if prepared_data:
            headers = ", ".join(prepared_data[0].keys())
            print(f"[CSV] Заголовки: {headers}")
        super().write(prepared_data)


users = [
    {"id": 1, "name": "Alice", "age": 30, "active": True},
    {"id": 2, "name": "Bob",   "age": 17, "active": True},
    {"id": 3, "name": "Carol", "age": 25, "active": False},
    {"id": 4, "name": "Dave",  "age": 22, "active": True},
]

exporter = CSVExporter(
    data=users,
    filename="active_adults.csv",
    filter_fn=lambda u: u["active"] and u["age"] >= 18,
    transform_fn=lambda u: {"name": u["name"], "age": u["age"]}
)

exporter.export()