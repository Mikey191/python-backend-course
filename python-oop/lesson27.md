# Урок 27. Метаклассы: что такое `type`, паттерны Singleton и Registry

---

## Классы как объекты: фундаментальная идея

Прежде чем говорить о метаклассах, нужно прочно зафиксировать одну идею: в Python классы — **это обычные объекты**. Не шаблоны, не типы данных в особом смысле, а именно объекты — такие же, как числа, строки или списки.

Что это означает на практике?

```python
class User:
    def __init__(self, name):
        self.name = name

    def greet(self):
        return f"Привет, я {self.name}"


# Класс можно присвоить переменной — как любой объект
MyClass = User
obj = MyClass("Alice")
print(obj.greet())   # Привет, я Alice

# Класс можно передать в функцию
def create_instance(cls, *args):
    return cls(*args)

user = create_instance(User, "Bob")
print(user.greet())   # Привет, я Bob

# Класс можно хранить в словаре
registry = {"user": User}
obj = registry["user"]("Carol")
print(obj.greet())   # Привет, я Carol

# Класс можно вернуть из функции
def get_class(name):
    classes = {"user": User}
    return classes[name]

Cls = get_class("user")
print(Cls("Dave").greet())   # Привет, я Dave
```

Раз классы — это объекты, возникает закономерный вопрос: что является **классом** для класса? 

У каждого объекта есть тип — `type(obj)` возвращает его класс. Применим это к самому классу:

```python
user = User("Alice")

print(type(user))      # <class '__main__.User'> — тип объекта user
print(type(User))      # <class 'type'> — тип объекта User (самого класса!)
print(type(int))       # <class 'type'>
print(type(str))       # <class 'type'>
print(type(list))      # <class 'type'>
```

Тип класса `User` — это `type`. Тип встроенных классов `int`, `str`, `list` — тоже `type`. `type` — это **метакласс, класс всех классов**. Именно `type` отвечает за создание новых классов в Python.

---

## `type`: двойная роль

`type` в Python выполняет две разные роли, и это поначалу сбивает с толку.

**Роль 1: функция для получения типа.** `type(obj)` с одним аргументом возвращает тип (класс) объекта.

**Роль 2: метакласс, создающий новые классы.** `type(name, bases, namespace)` с тремя аргументами создаёт новый класс.

```python
# Роль 1: получение типа
print(type(42))           # <class 'int'>
print(type("hello"))      # <class 'str'>
print(type([1, 2, 3]))    # <class 'list'>

# Роль 2: создание нового класса
MyClass = type("MyClass", (), {"x": 10, "greet": lambda self: "Привет"})
obj = MyClass()
print(obj.x)       # 10
print(obj.greet()) # Привет
print(type(obj))   # <class '__main__.MyClass'>
```

Проверим, что все классы являются экземплярами `type`:

```python
class User:
    pass

print(isinstance(User, type))    # True — User является экземпляром type
print(isinstance(int, type))     # True
print(isinstance(str, type))     # True

# И сам type является экземпляром самого себя
print(isinstance(type, type))    # True — интригующий факт Python
print(type(type))                # <class 'type'>
```

Цепочка наследования `type` и `object`:

```python
print(issubclass(type, object))   # True — type наследует от object
print(issubclass(object, type))   # False — object не является метаклассом
print(type(object))               # <class 'type'> — object тоже создан type
```

Это замкнутая система: `type` является экземпляром самого себя, и `object` создан `type`, при этом `type` наследует от `object`. Не нужно слишком глубоко думать об этой рекурсии — примите её как встроенную особенность реализации CPython.

---

## `type` как фабрика классов

Самое практичное применение `type` с тремя аргументами — динамическое создание классов в рантайме. Это эквивалентно обычному `class` объявлению:

```python
# Обычное объявление класса
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __repr__(self):
        return f"Point({self.x}, {self.y})"


# Эквивалентное создание через type
def point_init(self, x, y):
    self.x = x
    self.y = y

def point_repr(self):
    return f"Point({self.x}, {self.y})"

PointDynamic = type(
    "Point",                         # имя класса
    (object,),                       # кортеж базовых классов
    {                                # словарь атрибутов
        "__init__": point_init,
        "__repr__": point_repr,
    }
)

p = PointDynamic(1, 2)
print(p)            # Point(1, 2)
print(type(p))      # <class '__main__.Point'>
```

Практическое применение — создание классов по конфигурации. Например, динамическое создание классов моделей:

```python
def create_model_class(name: str, fields: list) -> type:
    """
    Динамически создаёт класс модели с заданными полями.
    Аналог того, как Django создаёт модели из определений.
    """

    def __init__(self, **kwargs):
        for field in fields:
            setattr(self, field, kwargs.get(field))

    def __repr__(self):
        field_str = ", ".join(f"{f}={getattr(self, f)!r}" for f in fields)
        return f"{name}({field_str})"

    def to_dict(self):
        return {f: getattr(self, f) for f in fields}

    namespace = {
        "__init__": __init__,
        "__repr__": __repr__,
        "to_dict": to_dict,
        "_fields": fields,
    }

    return type(name, (object,), namespace)


# Создаём классы из конфигурации — например, прочитанной из YAML
UserModel = create_model_class("UserModel", ["id", "username", "email"])
OrderModel = create_model_class("OrderModel", ["id", "user_id", "total", "status"])

user = UserModel(id=1, username="alice", email="alice@example.com")
order = OrderModel(id=1, user_id=1, total=89990, status="pending")

print(user)           # UserModel(id=1, username='alice', email='alice@example.com')
print(order.to_dict()) # {'id': 1, 'user_id': 1, 'total': 89990, 'status': 'pending'}
```

---

## Как Python создаёт класс: последовательность шагов

Понимание того, что происходит при выполнении оператора `class`, критично для работы с метаклассами.

```python
class MyClass(Base1, Base2, metaclass=MyMeta):
    class_var = 42

    def method(self):
        pass
```

Python выполняет следующую последовательность:

```
Шаг 1: Определить метакласс
        → явно указан metaclass=MyMeta? Использовать его.
        → нет? Взять метакласс первого базового класса.
        → нет базовых классов? Использовать type.

Шаг 2: Вызвать MyMeta.__prepare__(name, bases, **kwargs)
        → возвращает словарь-пространство имён для тела класса
        → обычно возвращает обычный dict или OrderedDict

Шаг 3: Выполнить тело класса
        → все определения попадают в пространство имён из шага 2

Шаг 4: Вызвать MyMeta(name, bases, namespace)
        → это вызывает MyMeta.__call__
        → который вызывает MyMeta.__new__(mcs, name, bases, namespace)
        → а затем MyMeta.__init__(cls, name, bases, namespace)

Результат: новый объект-класс
```

Аналогия с обычными объектами: когда вы пишете `User("alice")`, Python вызывает `type.__call__(User, "alice")`, который вызывает `User.__new__(User, "alice")` и `User.__init__(user_obj, "alice")`. Так же работает и создание классов, только `type` заменяется на метакласс.

---

## Создание собственного метакласса

Метакласс создаётся наследованием от `type`:

```python
class MyMeta(type):
    """Простейший метакласс — пока ничего не меняет."""

    def __new__(mcs, name, bases, namespace):
        print(f"MyMeta.__new__: создаём класс {name!r}")
        cls = super().__new__(mcs, name, bases, namespace)
        return cls

    def __init__(cls, name, bases, namespace):
        print(f"MyMeta.__init__: инициализируем класс {name!r}")
        super().__init__(name, bases, namespace)


class MyClass(metaclass=MyMeta):
    x = 10

# Вывод при объявлении класса (не при создании объекта!):
# MyMeta.__new__: создаём класс 'MyClass'
# MyMeta.__init__: инициализируем класс 'MyClass'

obj = MyClass()   # здесь ничего не выводится — MyMeta не трогает создание экземпляров
```

Параметры `__new__` и `__init__` метакласса:

- `mcs` / `cls` — сам метакласс (аналог `cls` в `classmethod`)
- `name` — имя создаваемого класса (строка)
- `bases` — кортеж базовых классов
- `namespace` — словарь атрибутов класса (результат выполнения тела класса)

Важное отличие `__new__` от `__init__`:
- `__new__` вызывается **до** создания объекта-класса и **возвращает** его
- `__init__` вызывается **после** того, как объект-класс уже создан, и ничего не возвращает

Когда использовать какой:
- `__new__`: если нужно изменить сам объект-класс перед возвратом, или вернуть другой объект (например, для Singleton)
- `__init__`: если нужно что-то настроить после создания класса (регистрация, проверки)

---

## Метод `__call__` метакласса: контроль над созданием объектов

Самый мощный момент: метакласс контролирует не только создание классов, но и создание **экземпляров** этих классов. Когда вы пишете `MyClass(args)`, Python фактически вызывает `type.__call__(MyClass, args)` — то есть метод `__call__` метакласса.

```python
class TracingMeta(type):
    """Метакласс, логирующий каждое создание экземпляра."""

    def __call__(cls, *args, **kwargs):
        print(f"[TracingMeta] Создаём экземпляр {cls.__name__}")
        instance = super().__call__(*args, **kwargs)
        print(f"[TracingMeta] Экземпляр создан: {instance!r}")
        return instance


class TracedUser(metaclass=TracingMeta):
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return f"TracedUser({self.name!r})"


user = TracedUser("alice")
# [TracingMeta] Создаём экземпляр TracedUser
# [TracingMeta] Экземпляр создан: TracedUser('alice')
```

Именно через `__call__` метакласса реализуется паттерн `Singleton`: мы перехватываем создание экземпляра и возвращаем уже существующий.

---

## Паттерн Singleton через метакласс

В уроке 5 курса мы реализовывали Singleton через `__new__` экземпляра. Теперь реализуем его правильно — через метакласс:

```python
import threading


class SingletonMeta(type):
    """
    Метакласс для паттерна Singleton.
    Гарантирует, что класс имеет только один экземпляр.
    Потокобезопасная реализация через блокировку.
    """

    _instances: dict = {}
    _lock: threading.Lock = threading.Lock()

    def __call__(cls, *args, **kwargs):
        # Двойная проверка для минимизации накладных расходов блокировки
        if cls not in cls._instances:
            with cls._lock:
                # Повторная проверка внутри блокировки
                if cls not in cls._instances:
                    instance = super().__call__(*args, **kwargs)
                    cls._instances[cls] = instance
        return cls._instances[cls]


class DatabaseConnection(metaclass=SingletonMeta):
    """
    Синглтон соединения с базой данных.
    В приложении должно быть только одно соединение с основной БД.
    """

    def __init__(self, host="localhost", port=5432, database="myapp"):
        # Этот код выполняется ТОЛЬКО при первом создании
        self.host = host
        self.port = port
        self.database = database
        self._connected = False
        print(f"DatabaseConnection.__init__ вызван для {host}:{port}/{database}")

    def connect(self):
        self._connected = True
        return self

    def __repr__(self):
        return f"DatabaseConnection({self.host}:{self.port}/{self.database})"


# Демонстрация Singleton
db1 = DatabaseConnection()
# DatabaseConnection.__init__ вызван для localhost:5432/myapp

db2 = DatabaseConnection()
# (ничего не выводится — __init__ не вызывается повторно)

db3 = DatabaseConnection(host="replica.example.com")
# (ничего не выводится — возвращается тот же объект)

print(db1 is db2)   # True — один и тот же объект
print(db1 is db3)   # True — аргументы игнорируются при повторном вызове
print(db1)          # DatabaseConnection(localhost:5432/myapp)

# Разные классы — разные синглтоны
class CacheConnection(metaclass=SingletonMeta):
    def __init__(self, host="localhost", port=6379):
        self.host = host
        self.port = port
        print(f"CacheConnection.__init__ вызван")


cache = CacheConnection()
# CacheConnection.__init__ вызван

print(cache is db1)   # False — разные синглтоны для разных классов
```

Почему метакласс лучше реализации через `__new__` экземпляра:

1. **Чёткое разделение ответственности**: метакласс отвечает за «политику создания», класс — за бизнес-логику.
2. **Переиспользование**: `SingletonMeta` применяется к любому классу через `metaclass=SingletonMeta`.
3. **Потокобезопасность** реализуется в одном месте, не разбросана по `__new__` разных классов.
4. **Аргументы конструктора**: при повторном вызове `__init__` не вызывается — поведение корректное.

Сравним с Singleton через `__new__`:

```python
# Singleton через __new__ (из урока 1)
class SingletonViaNew:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    # Проблема: __init__ вызывается при каждом "создании"!
    # Если __init__ меняет состояние — оно будет меняться каждый раз


s1 = SingletonViaNew()
s2 = SingletonViaNew()
print(s1 is s2)   # True — работает
# Но __init__ вызвался дважды — если там есть логика, она выполнится дважды
```

---

## Паттерн Registry через метакласс

`Registry` — это реестр, который автоматически отслеживает все подклассы базового класса. Каждый раз, когда объявляется новый подкласс, он автоматически регистрируется без явного вызова.

```python
class RegistryMeta(type):
    """
    Метакласс-реестр. Автоматически регистрирует все подклассы.
    """

    def __init__(cls, name, bases, namespace):
        super().__init__(name, bases, namespace)

        # Инициализируем реестр для базового класса
        if not hasattr(cls, '_registry'):
            cls._registry = {}

        # Регистрируем все подклассы (но не сам базовый класс)
        # Базовый класс — тот, у которого нет базовых классов в иерархии Registry
        if bases:
            registry_name = namespace.get('registry_name') or name.lower()
            cls._registry[registry_name] = cls

    @classmethod
    def get_registry(mcs, cls):
        return dict(cls._registry)
```

Применим к системе обработчиков уведомлений:

```python
class BaseNotificationHandler(metaclass=RegistryMeta):
    """Базовый обработчик уведомлений. Все подклассы регистрируются автоматически."""

    registry_name = None   # базовый класс не регистрируется

    def send(self, recipient: str, message: str) -> dict:
        raise NotImplementedError


class EmailHandler(BaseNotificationHandler):
    registry_name = "email"

    def send(self, recipient: str, message: str) -> dict:
        print(f"[Email] → {recipient}: {message}")
        return {"type": "email", "status": "sent", "recipient": recipient}


class SMSHandler(BaseNotificationHandler):
    registry_name = "sms"

    def send(self, recipient: str, message: str) -> dict:
        print(f"[SMS] → {recipient}: {message[:160]}")
        return {"type": "sms", "status": "sent", "recipient": recipient}


class PushHandler(BaseNotificationHandler):
    registry_name = "push"

    def send(self, recipient: str, message: str) -> dict:
        print(f"[Push] → {recipient}: {message}")
        return {"type": "push", "status": "sent", "recipient": recipient}


# Реестр заполняется автоматически при объявлении классов
print(BaseNotificationHandler._registry)
# {'email': <class 'EmailHandler'>, 'sms': <class 'SMSHandler'>, 'push': <class 'PushHandler'>}

def send_notification(channel: str, recipient: str, message: str) -> dict:
    """Отправляет уведомление через указанный канал."""
    handler_class = BaseNotificationHandler._registry.get(channel)
    if not handler_class:
        raise ValueError(f"Неизвестный канал: {channel!r}. "
                         f"Доступны: {list(BaseNotificationHandler._registry.keys())}")
    handler = handler_class()
    return handler.send(recipient, message)


send_notification("email", "alice@example.com", "Ваш заказ подтверждён")
# [Email] → alice@example.com: Ваш заказ подтверждён

send_notification("sms", "+79001234567", "Код: 1234")
# [SMS] → +79001234567: Код: 1234

try:
    send_notification("telegram", "@alice", "Привет")
except ValueError as e:
    print(e)   # Неизвестный канал: 'telegram'. Доступны: ['email', 'sms', 'push']
```

Ключевое преимущество: добавление нового канала — это просто объявление нового класса. Никаких изменений в `send_notification`, никаких явных регистраций. Именно так работают системы плагинов в Django и других фреймворках.

---

## `__init_subclass__`: современная альтернатива для Registry

Python 3.6 добавил хук `__init_subclass__`, который вызывается в базовом классе каждый раз, когда создаётся его подкласс. Для большинства задач Registry это более простая и читаемая альтернатива метаклассу:

```python
class BaseSerializer:
    """
    Базовый класс сериализатора.
    __init_subclass__ автоматически регистрирует все подклассы.
    """
    _registry: dict = {}

    def __init_subclass__(cls, format_name: str = None, **kwargs):
        super().__init_subclass__(**kwargs)
        if format_name:
            BaseSerializer._registry[format_name] = cls
            print(f"[Registry] Зарегистрирован сериализатор: {format_name!r} → {cls.__name__}")

    @classmethod
    def get(cls, format_name: str):
        serializer_class = cls._registry.get(format_name)
        if not serializer_class:
            raise ValueError(f"Нет сериализатора для формата {format_name!r}")
        return serializer_class()

    def serialize(self, data) -> str:
        raise NotImplementedError


class JSONSerializer(BaseSerializer, format_name="json"):
    def serialize(self, data) -> str:
        import json
        return json.dumps(data, ensure_ascii=False)


class CSVSerializer(BaseSerializer, format_name="csv"):
    def serialize(self, data) -> str:
        if not data:
            return ""
        if isinstance(data, list) and isinstance(data[0], dict):
            headers = list(data[0].keys())
            rows = [",".join(headers)]
            rows += [",".join(str(row.get(h, "")) for h in headers) for row in data]
            return "\n".join(rows)
        return str(data)


class XMLSerializer(BaseSerializer, format_name="xml"):
    def serialize(self, data) -> str:
        if isinstance(data, dict):
            items = "".join(f"<{k}>{v}</{k}>" for k, v in data.items())
            return f"<root>{items}</root>"
        return f"<data>{data}</data>"


# Регистрация произошла автоматически при объявлении классов
print(f"\nДоступные форматы: {list(BaseSerializer._registry.keys())}")

# Использование реестра
data = {"user": "alice", "action": "login", "status": "success"}

for format_name in ["json", "csv", "xml"]:
    serializer = BaseSerializer.get(format_name)
    print(f"\n{format_name.upper()}:")
    print(serializer.serialize(data))
```

**Сравнение `__init_subclass__` и метакласса:**

| | `__init_subclass__` | Метакласс |
|---|---|---|
| Синтаксис | Проще, встроен в класс | Отдельный класс, сложнее |
| Параметры | Через аргументы класса | Через атрибуты класса |
| Изменение создания экземпляра | Нет | Да (через `__call__`) |
| Изменение пространства имён | Нет | Да (через `__prepare__`) |
| Singleton | Нет | Да |
| Registry | Да — предпочтительно | Да |
| Конфликты при наследовании | Редко | Могут быть |

**Правило**: используйте `__init_subclass__` для Registry и аналогичных задач. Используйте метакласс только когда нужно изменить сам процесс создания класса или объектов — например, Singleton, или нужен `__prepare__`.

---

## Полный пример: система плагинов

Реализуем полноценную систему плагинов для обработки веб-хуков (webhooks):

```python
class WebhookPlugin:
    """
    Базовый класс для плагинов обработки webhook-событий.
    Использует __init_subclass__ для автоматической регистрации.
    """
    _registry: dict = {}

    def __init_subclass__(cls, event_type: str = None, **kwargs):
        super().__init_subclass__(**kwargs)
        if event_type:
            WebhookPlugin._registry[event_type] = cls

    @classmethod
    def get_handler(cls, event_type: str):
        handler_class = cls._registry.get(event_type)
        if not handler_class:
            return None
        return handler_class()

    @classmethod
    def supported_events(cls) -> list:
        return list(cls._registry.keys())

    def handle(self, payload: dict) -> dict:
        """Обрабатывает событие. Должен быть переопределён в подклассе."""
        raise NotImplementedError(f"{self.__class__.__name__} не реализует handle()")

    def validate_payload(self, payload: dict) -> bool:
        """Базовая валидация — проверяет наличие обязательных полей."""
        return bool(payload)


class OrderCreatedPlugin(WebhookPlugin, event_type="order.created"):
    """Обработчик события создания заказа."""

    def validate_payload(self, payload: dict) -> bool:
        return all(k in payload for k in ["order_id", "user_id", "total"])

    def handle(self, payload: dict) -> dict:
        order_id = payload["order_id"]
        user_id = payload["user_id"]
        total = payload["total"]
        print(f"[OrderCreated] Новый заказ #{order_id} от пользователя {user_id}, сумма: {total}")
        # В реальном приложении здесь: отправка email, обновление аналитики, etc.
        return {"processed": True, "order_id": order_id, "action": "send_confirmation_email"}


class PaymentCompletedPlugin(WebhookPlugin, event_type="payment.completed"):
    """Обработчик события успешной оплаты."""

    def validate_payload(self, payload: dict) -> bool:
        return all(k in payload for k in ["payment_id", "order_id", "amount"])

    def handle(self, payload: dict) -> dict:
        payment_id = payload["payment_id"]
        order_id = payload["order_id"]
        print(f"[PaymentCompleted] Оплата {payment_id} для заказа #{order_id}")
        return {"processed": True, "payment_id": payment_id, "action": "update_order_status"}


class UserRegisteredPlugin(WebhookPlugin, event_type="user.registered"):
    """Обработчик события регистрации пользователя."""

    def handle(self, payload: dict) -> dict:
        user_id = payload.get("user_id")
        email = payload.get("email")
        print(f"[UserRegistered] Новый пользователь {user_id}: {email}")
        return {"processed": True, "action": "send_welcome_email"}


class WebhookProcessor:
    """Процессор webhook-событий. Использует реестр плагинов."""

    def process(self, event_type: str, payload: dict) -> dict:
        handler = WebhookPlugin.get_handler(event_type)

        if handler is None:
            print(f"[WebhookProcessor] Нет обработчика для {event_type!r}")
            return {"processed": False, "reason": "unknown_event_type"}

        if not handler.validate_payload(payload):
            return {"processed": False, "reason": "invalid_payload"}

        return handler.handle(payload)


processor = WebhookProcessor()

print(f"Поддерживаемые события: {WebhookPlugin.supported_events()}\n")

events = [
    ("order.created", {"order_id": 1001, "user_id": 42, "total": 89990}),
    ("payment.completed", {"payment_id": "pay_abc", "order_id": 1001, "amount": 89990}),
    ("user.registered", {"user_id": 43, "email": "bob@example.com"}),
    ("unknown.event", {"data": "something"}),
]

for event_type, payload in events:
    result = processor.process(event_type, payload)
    print(f"Результат: {result}\n")
```

---

## Валидирующий метакласс

Покажем ещё одно применение метакласса — валидацию при объявлении класса. Это аналог ABC, но с другими возможностями:

```python
class APIViewMeta(type):
    """
    Метакласс для API-вью. При объявлении класса проверяет:
    1. Наличие обязательного атрибута endpoint_path
    2. Что все http-методы имеют правильные имена
    3. Автоматически добавляет метаданные
    """

    VALID_HTTP_METHODS = {'get', 'post', 'put', 'patch', 'delete', 'head', 'options'}

    def __new__(mcs, name, bases, namespace):
        cls = super().__new__(mcs, name, bases, namespace)

        # Пропускаем базовый класс
        is_base = not bases or all(
            not hasattr(b, '_is_api_view') for b in bases
        )
        if is_base:
            cls._is_api_view = True
            return cls

        # Проверяем обязательный атрибут endpoint_path
        if 'endpoint_path' not in namespace:
            raise TypeError(
                f"APIView-класс {name!r} должен объявить атрибут 'endpoint_path'"
            )

        # Проверяем имена методов — все публичные методы должны быть
        # либо стандартными HTTP-методами, либо начинаться с '_'
        for attr_name, attr_value in namespace.items():
            if callable(attr_value) and not attr_name.startswith('_'):
                if attr_name not in mcs.VALID_HTTP_METHODS:
                    import warnings
                    warnings.warn(
                        f"В {name!r} метод {attr_name!r} не является стандартным "
                        f"HTTP-методом. HTTP-методы: {mcs.VALID_HTTP_METHODS}",
                        UserWarning,
                        stacklevel=2
                    )

        # Автоматически добавляем метаданные
        cls._allowed_methods = [
            m.upper() for m in mcs.VALID_HTTP_METHODS
            if m in namespace
        ]

        print(f"[APIViewMeta] Зарегистрирован вью: {name!r} "
              f"на {namespace['endpoint_path']!r}, "
              f"методы: {cls._allowed_methods}")

        return cls


class BaseAPIView(metaclass=APIViewMeta):
    """Базовый класс для всех API-вью."""

    def dispatch(self, request: dict) -> dict:
        method = request.get("method", "GET").lower()
        handler = getattr(self, method, self._method_not_allowed)
        return handler(request)

    def _method_not_allowed(self, request: dict) -> dict:
        return {"status": 405, "error": "Method Not Allowed",
                "allowed": self._allowed_methods}


class UserListView(BaseAPIView):
    endpoint_path = "/api/users"

    def get(self, request: dict) -> dict:
        return {"status": 200, "data": [{"id": 1, "name": "Alice"}]}

    def post(self, request: dict) -> dict:
        return {"status": 201, "data": {"id": 2, **request.get("body", {})}}


class UserDetailView(BaseAPIView):
    endpoint_path = "/api/users/{id}"

    def get(self, request: dict) -> dict:
        user_id = request.get("path_params", {}).get("id")
        return {"status": 200, "data": {"id": user_id, "name": "Alice"}}

    def delete(self, request: dict) -> dict:
        user_id = request.get("path_params", {}).get("id")
        return {"status": 204, "deleted": user_id}


# Попытка объявить вью без endpoint_path вызовет ошибку при объявлении
try:
    class BrokenView(BaseAPIView):
        # endpoint_path не объявлен!
        def get(self, request):
            pass
except TypeError as e:
    print(f"TypeError при объявлении класса: {e}")


# Использование
list_view = UserListView()
detail_view = UserDetailView()

print(list_view.dispatch({"method": "GET"}))
print(list_view.dispatch({"method": "DELETE"}))  # не разрешён
print(detail_view.dispatch({"method": "GET", "path_params": {"id": "42"}}))
```

---

## Когда метакласс — правильный выбор

Метакласс — мощный, но сложный инструмент. Перед его применением задайте себе вопросы:

**Вместо метакласса можно использовать:**

```python
# Декоратор класса — часто проще и достаточно
def add_logging(cls):
    original_init = cls.__init__
    def new_init(self, *args, **kwargs):
        print(f"Создаём {cls.__name__}")
        original_init(self, *args, **kwargs)
    cls.__init__ = new_init
    return cls

@add_logging
class MyService:
    def __init__(self, name):
        self.name = name

# __init_subclass__ — для Registry, проще метакласса
class Base:
    _registry = {}
    def __init_subclass__(cls, name=None, **kwargs):
        super().__init_subclass__(**kwargs)
        if name:
            Base._registry[name] = cls
```

**Метакласс нужен когда:**

1. Нужно контролировать создание экземпляров (`__call__`) — паттерн Singleton.
2. Нужно изменить пространство имён ещё до выполнения тела класса (`__prepare__`).
3. Нужно изменить сам объект-класс до его возврата (`__new__`).
4. Нужно, чтобы логика применялась автоматически ко всем подклассам без `__init_subclass__`.
5. Конфликты метаклассов при множественном наследовании требуют явного контроля.

---

## Неочевидные моменты и типичные ошибки

**Конфликт метаклассов.** Если класс наследует от двух классов с разными метаклассами — `TypeError`:

```python
class MetaA(type):
    pass

class MetaB(type):
    pass

class A(metaclass=MetaA):
    pass

class B(metaclass=MetaB):
    pass

try:
    class C(A, B):   # TypeError!
        pass
except TypeError as e:
    print(e)
# metaclass conflict: the metaclass of a derived class must be a subclass of the metaclasses of all its bases
```

Решение — создать общий метакласс, наследующий от обоих:

```python
class MetaAB(MetaA, MetaB):
    pass

class C(A, B, metaclass=MetaAB):   # OK
    pass
```

**Метакласс применяется ко всем подклассам.** Если вы объявили класс с метаклассом — все его подклассы автоматически используют тот же метакласс:

```python
class MyMeta(type):
    def __init__(cls, name, bases, ns):
        print(f"MyMeta создал класс: {name}")
        super().__init__(name, bases, ns)

class Base(metaclass=MyMeta):   # MyMeta создал класс: Base
    pass

class Child(Base):   # MyMeta создал класс: Child — автоматически!
    pass

class GrandChild(Child):   # MyMeta создал класс: GrandChild — тоже!
    pass
```

**`type(obj)` vs `obj.__class__`.** В нормальных случаях они совпадают. Но `__class__` можно переопределить, а `type()` — нет. `type()` возвращает реальный тип, `__class__` может возвращать то, что хочет класс:

```python
class Deceiver:
    @property
    def __class__(self):
        return int   # притворяемся int

d = Deceiver()
print(d.__class__)   # <class 'int'> — обманывает
print(type(d))       # <class 'Deceiver'> — правда
```

**`__prepare__` для упорядоченного пространства имён.** Метод `__prepare__` вызывается до выполнения тела класса и возвращает словарь, который будет использоваться как пространство имён. Это редко нужно, но позволяет, например, гарантировать порядок атрибутов:

```python
class OrderedMeta(type):
    @classmethod
    def __prepare__(mcs, name, bases, **kwargs):
        # Возвращаем обычный dict — в Python 3.7+ dict сохраняет порядок
        # Можно вернуть специальный словарь с дополнительным поведением
        return {}
```

---

## Итоги урока

Классы в Python — это объекты, а метакласс — это класс-для-классов. Метакласс по умолчанию — `type`, который создаёт все классы. `type(name, bases, namespace)` с тремя аргументами динамически создаёт новый класс.

Последовательность при объявлении класса: `__prepare__` готовит пространство имён, тело класса выполняется в нём, затем `metaclass.__new__` создаёт объект-класс, затем `metaclass.__init__` его настраивает. `metaclass.__call__` вызывается при создании каждого экземпляра класса.

Singleton реализуется через `__call__` метакласса: перехватываем создание экземпляра и возвращаем кешированный. Registry реализуется через `__init__` метакласса или, проще, через `__init_subclass__` базового класса.

Для большинства задач достаточно декораторов классов или `__init_subclass__`. Метакласс нужен только когда нужен контроль над самим процессом создания класса или его экземпляров.

---

## Вопросы

1. Что такое метакласс? Каким метаклассом является класс `str` и каким — обычный пользовательский класс?
2. Что делает `type(name, bases, namespace)` с тремя аргументами? Чем это отличается от `type(obj)` с одним аргументом?
3. Какова последовательность вызовов при объявлении класса с метаклассом? Чем `__new__` метакласса отличается от `__init__`?
4. Почему паттерн Singleton реализуется через `__call__` метакласса, а не через `__new__` экземпляра?
5. Как паттерн Registry через метакласс отличается от Registry через `__init_subclass__`? Когда предпочтительнее каждый подход?
6. Что произойдёт, если класс пытается наследовать от двух классов с разными метаклассами?
7. Что такое `__init_subclass__` и когда он вызывается? Как передать параметры в этот хук?
8. Почему метакласс автоматически применяется ко всем подклассам? Как это использовать и когда это может быть проблемой?

---

## Задачи

### **Задача 1**. 

`type` для динамического создания классов

Используя только `type(name, bases, namespace)`, создайте три класса динамически:
- `Rectangle` с атрибутами `width` и `height`, методами `area()` → `width * height`, `perimeter()` → `2 * (width + height)`, `__repr__` → `"Rectangle(width=W, height=H)"`.
- `Circle` с атрибутом `radius`, методами `area()` → `π * r²`, `perimeter()` → `2 * π * r`, `__repr__` → `"Circle(radius=R)"`.
- `Triangle` с атрибутами `a`, `b`, `c` (стороны), методами `area()` (формула Герона), `perimeter()`, `__repr__`.

Создайте функцию `shape_info(shape)`, которая принимает любую фигуру и выводит тип, площадь и периметр. Убедитесь через `isinstance`, что объекты являются экземплярами созданных классов.

**Пример использования**:

```python
r = Rectangle(4, 6)
c = Circle(5)
t = Triangle(3, 4, 5)

shape_info(r)   # Rectangle: area=24.00, perimeter=20.00
shape_info(c)   # Circle: area=78.54, perimeter=31.42
shape_info(t)   # Triangle: area=6.00, perimeter=12.00

print(isinstance(r, Rectangle))   # True
```

---

### **Задача 2**. 

Singleton через метакласс

Реализуйте `SingletonMeta` — потокобезопасный метакласс для паттерна Singleton. Примените его к трём классам:
- `AppConfig` — конфигурация приложения (хранит `debug`, `database_url`, `secret_key`).
- `RequestCounter` — счётчик запросов с методами `increment()` и `count`.
- `Logger` — логгер с методом `log(message)` и атрибутом `messages` (список).

Убедитесь, что: а) повторные вызовы конструктора возвращают тот же объект, б) `__init__` не вызывается повторно (состояние не сбрасывается), в) разные классы имеют независимые синглтоны.

**Пример использования**:

```python
cfg1 = AppConfig(debug=True, database_url="postgres://localhost/db")
cfg2 = AppConfig(debug=False)   # возвращает тот же объект, debug остаётся True

print(cfg1 is cfg2)    # True
print(cfg1.debug)      # True — не сброшен

counter = RequestCounter()
counter.increment()
counter.increment()

counter2 = RequestCounter()   # тот же объект
print(counter2.count)         # 2 — сохранилось

logger1 = Logger()
logger2 = Logger()
print(logger1 is logger2)     # True
print(cfg1 is logger1)        # False — разные синглтоны
```

---

### **Задача 3**. 

Registry через `__init_subclass__`

Создайте систему обработчиков команд для чат-бота. Базовый класс `Command` с `__init_subclass__`, который регистрирует подклассы по `command_name`. Каждый обработчик имеет метод `execute(args: list) -> str`. Реализуйте обработчики:
- `HelpCommand(command_name="/help")` — возвращает список доступных команд.
- `StatusCommand(command_name="/status")` — возвращает `"Сервер работает нормально"`.
- `EchoCommand(command_name="/echo")` — возвращает переданные аргументы объединёнными.
- `TimeCommand(command_name="/time")` — возвращает текущее время.

Напишите функцию `process_message(message: str) -> str`, которая: разбирает сообщение на команду и аргументы, находит обработчик через реестр, вызывает его.

**Пример использования**:

```python
print(process_message("/help"))
# Доступные команды: /help, /status, /echo, /time

print(process_message("/echo Hello World"))
# Hello World

print(process_message("/status"))
# Сервер работает нормально

print(process_message("/unknown"))
# Неизвестная команда: /unknown
```

---

### **Задача 4**. 

Валидирующий метакласс для моделей

Создайте метакласс `ModelMeta`, который при объявлении класса:
1. Проверяет, что все атрибуты, объявленные в `_required_fields` (список строк), действительно будут переданы в `__init__` (проверьте через `inspect.signature`).
2. Автоматически добавляет метод `fields() -> list`, возвращающий список `_required_fields`.
3. Автоматически добавляет метод `from_dict(cls, data: dict)`, создающий объект из словаря.
4. Выводит сообщение при регистрации каждой модели.

Создайте две модели: `UserModel(_required_fields=['username', 'email'])` и `ProductModel(_required_fields=['name', 'price', 'category'])`. Обе должны иметь соответствующие `__init__`.

**Пример использования**:

```python
user = UserModel(username="alice", email="alice@example.com")
print(UserModel.fields())   # ['username', 'email']

user2 = UserModel.from_dict({"username": "bob", "email": "bob@example.com"})
print(user2.username)   # bob

product = ProductModel.from_dict({"name": "Ноутбук", "price": 89990, "category": "electronics"})
print(ProductModel.fields())   # ['name', 'price', 'category']
```

---

### **Задача 5**. 

Комплексная система: Singleton + Registry

Создайте систему middleware для веб-приложения, объединяющую два паттерна:
- `MiddlewareRegistry` — метакласс, реализующий Registry: при объявлении подкласса `BaseMiddleware` автоматически регистрирует его по `middleware_name`.
- `MiddlewarePipeline` — Singleton (через метакласс или `__init_subclass__`): единственный экземпляр, управляющий цепочкой middleware.

Базовый класс `BaseMiddleware` использует `MiddlewareRegistry`. Каждый middleware имеет метод `process(request, next_handler)`.

Реализуйте три middleware:
- `LoggingMiddleware(middleware_name="logging")` — логирует запрос.
- `AuthMiddleware(middleware_name="auth")` — проверяет токен.
- `TimingMiddleware(middleware_name="timing")` — замеряет время.

`MiddlewarePipeline` (Singleton) позволяет: `add(middleware_name)`, `process(request)` — запускает цепочку.

**Пример использования**:

```python
pipeline = MiddlewarePipeline()
pipeline.add("logging")
pipeline.add("auth")
pipeline.add("timing")

pipeline2 = MiddlewarePipeline()
print(pipeline is pipeline2)   # True — Singleton

result = pipeline.process({"path": "/api/users", "token": "valid"})
print(result)
```

---

[Предыдущий урок](lesson26.md) | [Следующий урок](lesson28.md)