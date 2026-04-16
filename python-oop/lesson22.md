# Урок 22. Полиморфизм: duck typing, `isinstance()`, `issubclass()`

---

## Что такое полиморфизм

**Полиморфизм** — это способность разных объектов отвечать на одни и те же вызовы, реализуя их по-своему. Слово происходит от греческого «много форм» — и это точное описание: один и тот же интерфейс, множество реализаций.

Самый наглядный способ понять, зачем нужен полиморфизм — посмотреть на код без него. Предположим, у нас есть несколько типов уведомлений: email, SMS и push-уведомление. Без полиморфизма код рассылки выглядел бы так:

```python
def send_notification(notification, notification_type):
    if notification_type == "email":
        # логика отправки email
        print(f"Email: {notification['body']} → {notification['recipient']}")
    elif notification_type == "sms":
        # логика отправки SMS
        print(f"SMS: {notification['body']} → {notification['phone']}")
    elif notification_type == "push":
        # логика отправки push
        print(f"Push: {notification['body']} → {notification['device_token']}")
    else:
        raise ValueError(f"Неизвестный тип: {notification_type}")
```

Каждый раз, когда нужно добавить новый тип уведомления, эту функцию нужно изменить. Она знает о всех типах, она содержит логику всех типов, она нарушает принцип открытости/закрытости: открыт для расширения — закрыт для изменения.

С полиморфизмом:

```python
def send_notification(notification):
    notification.send()   # каждый объект знает, как отправлять себя
```

Функция больше не знает о типах. Она просто вызывает `send()` — а каждый объект реализует этот метод по-своему. Добавление нового типа уведомления не требует изменения этой функции.

В Python существуют две модели полиморфизма. Первая — через наследование: все объекты унаследованы от общего базового класса. Вторая — через `duck typing`: объекты вообще не связаны иерархией, но реализуют одинаковый интерфейс. Python поддерживает обе модели, и понимание обеих — ключ к написанию гибкого кода.

---

## Полиморфизм через наследование

Классический подход к полиморфизму: базовый класс определяет интерфейс, дочерние классы предоставляют конкретные реализации:

```python
class Notification:
    def __init__(self, recipient, subject, body):
        self.recipient = recipient
        self.subject = subject
        self.body = body

    def send(self):
        raise NotImplementedError(
            f"{self.__class__.__name__} должен реализовать метод send()"
        )

    def __repr__(self):
        return f"{self.__class__.__name__}(recipient={self.recipient!r})"


class EmailNotification(Notification):
    def send(self):
        print(f"[Email] → {self.recipient}: {self.subject}")
        return {"type": "email", "status": "sent"}


class SMSNotification(Notification):
    def __init__(self, phone, subject, body):
        super().__init__(phone, subject, body)

    def send(self):
        print(f"[SMS] → {self.recipient}: {self.body[:160]}")
        return {"type": "sms", "status": "sent"}


class PushNotification(Notification):
    def __init__(self, device_token, subject, body):
        super().__init__(device_token, subject, body)

    def send(self):
        print(f"[Push] → {self.recipient}: {self.subject}")
        return {"type": "push", "status": "sent"}


def notify_all(notifications):
    """
    Эта функция не знает и не хочет знать о конкретных типах уведомлений.
    Она просто вызывает send() — полиморфизм делает остальное.
    """
    results = []
    for notification in notifications:
        result = notification.send()
        results.append(result)
    return results


# Все объекты разных типов, но один код их обрабатывает
notifications = [
    EmailNotification("alice@example.com", "Добро пожаловать", "Привет!"),
    SMSNotification("+79001234567", "Код", "Ваш код: 1234"),
    PushNotification("device_abc", "Новость", "Вышло обновление"),
]

results = notify_all(notifications)
# [Email] → alice@example.com: Добро пожаловать
# [SMS] → +79001234567: Ваш код: 1234
# [Push] → device_abc: Новость
```

Ключевой момент: функция `notify_all` написана один раз и никогда не потребует изменений при добавлении нового типа уведомления. Добавьте `SlackNotification(Notification)` с методом `send()` — и функция автоматически заработает с ним.

---

## Duck typing: типизация по поведению, а не по происхождению

В Python объект не обязан наследоваться от определённого класса, чтобы быть использованным в определённом контексте. Достаточно, чтобы он реализовал нужные методы. Это называется duck typing — термин восходит к поговорке: «Если что-то ходит как утка и крякает как утка, то это, вероятно, утка».

Классический пример в Python: функция, работающая с «файлоподобными» объектами. Стандартная библиотека Python не требует, чтобы вы передавали именно файл — она требует объект с методом `write()`:

```python
import json

# Стандартный файл
with open("data.json", "w") as f:
    json.dump({"key": "value"}, f)   # f — файл

# io.StringIO — не файл, но работает так же
import io
buffer = io.StringIO()
json.dump({"key": "value"}, buffer)  # buffer — не файл, но имеет write()
print(buffer.getvalue())   # '{"key": "value"}'

# Наш собственный класс — тоже работает, если реализует write()
class LogWriter:
    def __init__(self):
        self.log = []

    def write(self, text):
        self.log.append(text)
        return len(text)


log = LogWriter()
json.dump({"key": "value"}, log)   # работает! json.dump просто вызывает write()
print(log.log)   # ['{"key": "value"}']
```

`json.dump` не проверяет `isinstance(f, io.IOBase)`. Она просто вызывает `f.write()`. Любой объект с методом `write()` автоматически является «файлоподобным» с точки зрения `json.dump`.

Теперь применим этот принцип к системе уведомлений. Сделаем её независимой от базового класса:

```python
class SlackNotification:
    """
    Этот класс НЕ наследует от Notification.
    Но он реализует метод send() — этого достаточно для duck typing.
    """

    def __init__(self, channel, message):
        self.channel = channel
        self.message = message

    def send(self):
        print(f"[Slack] #{self.channel}: {self.message}")
        return {"type": "slack", "status": "sent"}


# Функция notify_all работает с любым объектом, имеющим метод send()
slack = SlackNotification("engineering", "Сервер перезапущен")
email = EmailNotification("alice@example.com", "Alert", "Сервер перезапущен")

# Оба объекта работают в одной функции — хотя SlackNotification не является Notification
notify_all([email, slack])
```

Это принципиально важный момент: duck typing позволяет использовать объекты вместе, даже если они не связаны общим предком. Ограничение — только наличие нужных методов.

---

## Протоколы как основа duck typing

В Python существуют неформальные «протоколы» — наборы методов, которые объект должен реализовать, чтобы работать в определённом контексте. Вы уже знаете большинство из них по модулю о магических методах:

```python
# Протокол итерации: __iter__ и __next__
# Любой объект с этими методами работает в for-цикле
for item in my_object:   # Python вызывает __iter__, затем __next__
    pass

# Протокол контекстного менеджера: __enter__ и __exit__
# Любой объект с этими методами работает в with-блоке
with my_object as resource:
    pass

# Протокол последовательности: __len__ и __getitem__
# Любой объект с этими методами работает в функциях типа len(), []
print(len(my_object))
print(my_object[0])

# Протокол сравнения: __eq__, __lt__ и т.д.
# Любой объект с этими методами работает в sorted(), min(), max()
sorted_list = sorted([my_obj1, my_obj2, my_obj3])
```

Рассмотрим конкретный пример: создадим класс, который ведёт себя как список, не наследуясь от него:

```python
class ResponseList:
    """
    Коллекция HTTP-ответов. Реализует протокол последовательности
    без наследования от list.
    """

    def __init__(self, responses=None):
        self._responses = list(responses or [])

    def __len__(self):
        return len(self._responses)

    def __getitem__(self, index):
        return self._responses[index]

    def __iter__(self):
        return iter(self._responses)

    def append(self, response):
        self._responses.append(response)


responses = ResponseList([
    {"status": 200, "body": "OK"},
    {"status": 404, "body": "Not Found"},
    {"status": 500, "body": "Error"},
])

# Работает с len() — благодаря __len__
print(len(responses))   # 3

# Работает в for-цикле — благодаря __iter__
for r in responses:
    print(r["status"])

# Работает с индексом — благодаря __getitem__
print(responses[0])   # {'status': 200, 'body': 'OK'}

# Работает в list comprehension — благодаря __iter__
errors = [r for r in responses if r["status"] >= 400]
print(errors)   # [{'status': 404, ...}, {'status': 500, ...}]

# НЕ является экземпляром list
print(isinstance(responses, list))   # False
# Но ведёт себя как список там, где ожидается последовательность
```

---

## EAFP vs LBYL: два стиля работы с duck typing

При работе с duck typing возникает вопрос: как обработать ситуацию, когда объект не реализует нужный метод? Python-сообщество выработало два подхода.

**LBYL (Look Before You Leap) — «смотри перед прыжком»:** проверяем наличие атрибута/метода перед его использованием:

```python
def send_notification(notification):
    if hasattr(notification, 'send') and callable(notification.send):
        return notification.send()
    else:
        raise TypeError(f"Объект {notification!r} не поддерживает отправку")
```

**EAFP (Easier to Ask Forgiveness than Permission) — «проще попросить прощения, чем разрешения»:** просто вызываем метод и обрабатываем исключение:

```python
def send_notification(notification):
    try:
        return notification.send()
    except AttributeError:
        raise TypeError(f"Объект {notification!r} не имеет метода send()")
```

Python-сообщество предпочитает EAFP — это более идиоматично. EAFP лаконичнее, не страдает от race conditions (объект мог потерять атрибут между проверкой и использованием), и явно описывает, какое исключение мы ожидаем.

Однако в контексте обработки разных типов объектов часто используется гибридный подход:

```python
def process_data(data):
    """
    Обрабатывает данные разных форматов.
    Предпочитает duck typing, но проверяет тип для специальных случаев.
    """
    # Специальная обработка для строк — они итерируемы, но мы хотим другое поведение
    if isinstance(data, str):
        return data.strip()

    # Для всего остального — пробуем работать как с итерируемым
    try:
        return [process_data(item) for item in data]
    except TypeError:
        return data
```

---

## `isinstance()` в контексте полиморфизма: когда проверять тип

В уроке 19 мы познакомились с `isinstance()` как инструментом проверки принадлежности к иерархии. Теперь рассмотрим более тонкий вопрос: когда использование `isinstance()` в полиморфном коде является антипаттерном, а когда — легитимным инструментом.

**Антипаттерн: замена полиморфизма проверками типа.**

```python
# ПЛОХО: мы сами занимаемся диспетчеризацией — это задача полиморфизма
def serialize(obj):
    if isinstance(obj, EmailNotification):
        return {"type": "email", "to": obj.recipient}
    elif isinstance(obj, SMSNotification):
        return {"type": "sms", "phone": obj.recipient}
    elif isinstance(obj, PushNotification):
        return {"type": "push", "token": obj.recipient}
    # При добавлении нового типа нужно менять эту функцию!
```

Это именно та цепочка `if/elif`, от которой полиморфизм должен избавить.

**Легитимный случай 1: диспетчеризация по типу для встроенных типов.**

Когда у вас нет контроля над объектами (например, это встроенные типы Python), добавить к ним метод нельзя. Здесь `isinstance()` — единственный выход:

```python
import json
import datetime
from decimal import Decimal


class CustomJSONEncoder(json.JSONEncoder):
    """
    Расширенный JSON-энкодер, поддерживающий дополнительные типы.
    isinstance() здесь легитимен: мы не можем добавить метод к datetime или Decimal.
    """

    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        if isinstance(obj, datetime.date):
            return obj.isoformat()
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, set):
            return sorted(list(obj))
        # Для пользовательских объектов — duck typing
        if hasattr(obj, 'to_dict'):
            return obj.to_dict()
        return super().default(obj)


data = {
    "created_at": datetime.datetime.now(),
    "price": Decimal("19.99"),
    "tags": {"python", "web", "api"},
}

print(json.dumps(data, cls=CustomJSONEncoder, indent=2))
```

**Легитимный случай 2: валидация входных данных.**

```python
def process_payment(amount, currency):
    if not isinstance(amount, (int, float, Decimal)):
        raise TypeError(
            f"amount должен быть числом, получен {type(amount).__name__}"
        )
    if not isinstance(currency, str):
        raise TypeError(
            f"currency должна быть строкой, получен {type(currency).__name__}"
        )
    # Основная логика...
```

**Легитимный случай 3: специальная обработка конкретного подтипа.**

```python
def log_response(response):
    """Логирование ответа с дополнительной информацией для ошибок."""
    print(f"Status: {response.status_code}")

    # Для ошибочных ответов — дополнительное логирование
    if isinstance(response, ErrorResponse):
        print(f"Error code: {response.error_code}")
        print(f"Stack trace: {response.traceback}")
    # Для остальных — только базовая информация
```

---

## `isinstance()` с кортежем типов

`isinstance()` может принимать не только один тип, но и кортеж типов. Это позволяет проверить принадлежность к любому из нескольких типов за один вызов:

```python
def format_value(value):
    """Форматирует значение для отображения в API-ответе."""
    if isinstance(value, bool):
        # bool ОБЯЗАТЕЛЬНО проверяем перед int — bool является подклассом int!
        return str(value).lower()   # True → "true", False → "false"

    if isinstance(value, (int, float, Decimal)):
        return str(value)

    if isinstance(value, (list, tuple)):
        return [format_value(item) for item in value]

    if isinstance(value, dict):
        return {k: format_value(v) for k, v in value.items()}

    if isinstance(value, str):
        return value

    if isinstance(value, datetime.datetime):
        return value.isoformat()

    # Для всего остального — duck typing
    if hasattr(value, '__str__'):
        return str(value)

    raise TypeError(f"Не удаётся сериализовать объект типа {type(value).__name__}")


print(format_value(True))          # "true"
print(format_value(42))            # "42"
print(format_value([1, True, "a"])) # ["1", "true", "a"]
print(format_value({"x": 3.14}))   # {"x": "3.14"}
```

Обратите внимание на критически важную деталь: проверка `isinstance(value, bool)` идёт **раньше** `isinstance(value, (int, float))`. Это необходимо, потому что `bool` является подклассом `int` в Python:

```python
print(isinstance(True, int))    # True — bool является подклассом int!
print(isinstance(True, bool))   # True
print(isinstance(1, bool))      # False — int НЕ является bool

# Неправильный порядок приведёт к ошибке:
value = True
if isinstance(value, int):      # True пройдёт эту проверку!
    return str(value)           # вернёт "1", а не "true"
```

---

## Виртуальные подклассы: расширяем `isinstance()` через ABC

Это один из самых неочевидных механизмов Python. Абстрактные базовые классы (ABC) позволяют зарегистрировать класс как «виртуальный подкласс» другого класса — без реального наследования. После регистрации `isinstance()` будет возвращать `True` для объектов этого класса.

Предварительное знакомство — подробно ABC разберём в следующем уроке:

```python
from abc import ABC, abstractmethod


class Sendable(ABC):
    """
    Абстрактный базовый класс для отправляемых объектов.
    Определяет протокол: объект должен иметь метод send().
    """

    @abstractmethod
    def send(self):
        pass

    @classmethod
    def __subclasshook__(cls, subclass):
        """
        Хук для проверки: является ли subclass виртуальным подклассом Sendable?
        Возвращает True, если у класса есть метод send.
        Это позволяет isinstance() работать с любым классом, имеющим send().
        """
        if cls is Sendable:
            return hasattr(subclass, 'send') and callable(getattr(subclass, 'send'))
        return NotImplemented


class TelegramNotification:
    """
    Этот класс НЕ наследует ни от Notification, ни от Sendable.
    Но у него есть метод send() — благодаря __subclasshook__
    он пройдёт проверку isinstance(..., Sendable).
    """

    def __init__(self, chat_id, text):
        self.chat_id = chat_id
        self.text = text

    def send(self):
        print(f"[Telegram] chat_id={self.chat_id}: {self.text}")
        return {"type": "telegram", "status": "sent"}


telegram = TelegramNotification(123456, "Привет!")

# Без реального наследования — isinstance возвращает True благодаря __subclasshook__
print(isinstance(telegram, Sendable))     # True
print(issubclass(TelegramNotification, Sendable))  # True

# Работает в полиморфном коде
def send_if_sendable(obj):
    if isinstance(obj, Sendable):
        return obj.send()
    raise TypeError(f"Объект {obj!r} не является отправляемым")


send_if_sendable(telegram)   # [Telegram] chat_id=123456: Привет!
```

Это мощный механизм: вы можете определить протокол (набор методов) через ABC с `__subclasshook__`, и тогда `isinstance()` автоматически будет проверять, реализует ли объект этот протокол — без необходимости наследования. Это сочетание преимуществ duck typing (не нужно наследоваться) и явной типизации (можно использовать `isinstance()`).

---

## `issubclass()` в деталях: применение в метапрограммировании

`issubclass()` проверяет отношение между классами. Кроме базового использования из урока 19, у неё есть важные применения в паттернах, близких к метапрограммированию.

**Паттерн «реестр обработчиков»:** система регистрирует обработчики для разных базовых классов и использует `issubclass()` для диспетчеризации:

```python
class EventRegistry:
    """
    Реестр обработчиков событий.
    Диспетчеризация основана на иерархии типов событий.
    """

    def __init__(self):
        self._handlers = {}   # {EventClass: [handler_functions]}

    def register(self, event_class, handler):
        """Регистрирует обработчик для класса события."""
        if event_class not in self._handlers:
            self._handlers[event_class] = []
        self._handlers[event_class].append(handler)

    def dispatch(self, event):
        """
        Находит все обработчики для данного события.
        Учитывает иерархию: обработчик для базового класса
        вызывается для всех дочерних.
        """
        for event_class, handlers in self._handlers.items():
            if isinstance(event, event_class):   # isinstance учитывает наследование
                for handler in handlers:
                    handler(event)


# Определяем иерархию событий
class BaseEvent:
    def __init__(self, source):
        self.source = source


class UserEvent(BaseEvent):
    def __init__(self, source, user_id):
        super().__init__(source)
        self.user_id = user_id


class UserRegisteredEvent(UserEvent):
    def __init__(self, source, user_id, email):
        super().__init__(source, user_id)
        self.email = email


class UserDeletedEvent(UserEvent):
    def __init__(self, source, user_id):
        super().__init__(source, user_id)


# Создаём реестр и регистрируем обработчики
registry = EventRegistry()

# Обработчик для ВСЕХ событий
registry.register(BaseEvent, lambda e: print(f"[LOG] Событие от {e.source}"))

# Обработчик для ВСЕХ пользовательских событий
registry.register(UserEvent, lambda e: print(f"[AUDIT] Изменение пользователя {e.user_id}"))

# Обработчик только для регистрации
registry.register(
    UserRegisteredEvent,
    lambda e: print(f"[EMAIL] Отправляем приветствие на {e.email}")
)

# Диспетчеризация
event = UserRegisteredEvent("api", user_id=42, email="alice@example.com")
registry.dispatch(event)

# [LOG] Событие от api            ← BaseEvent handler
# [AUDIT] Изменение пользователя 42  ← UserEvent handler
# [EMAIL] Отправляем приветствие на alice@example.com  ← UserRegisteredEvent handler
```

**`issubclass()` для проверки в декораторах:**

```python
def requires_base_model(cls):
    """
    Декоратор, проверяющий что класс наследует от BaseModel.
    Использует issubclass() для проверки иерархии.
    """
    if not issubclass(cls, BaseModel):
        raise TypeError(
            f"Класс {cls.__name__} должен наследовать от BaseModel"
        )
    return cls


class BaseModel:
    pass


@requires_base_model
class UserModel(BaseModel):   # OK — является подклассом BaseModel
    pass


try:
    @requires_base_model
    class WrongModel:          # TypeError — не наследует от BaseModel
        pass
except TypeError as e:
    print(e)   # Класс WrongModel должен наследовать от BaseModel
```

---

## `type()` vs `isinstance()`: окончательное разграничение

Три сценария, демонстрирующих разницу:

```python
class Animal:
    pass

class Dog(Animal):
    pass

dog = Dog()

# Сценарий 1: isinstance() учитывает иерархию
print(isinstance(dog, Dog))     # True
print(isinstance(dog, Animal))  # True — Dog является Animal

# type() не учитывает иерархию
print(type(dog) == Dog)         # True
print(type(dog) == Animal)      # False — type() возвращает точный тип

# Сценарий 2: type() для точной проверки (редкий легитимный случай)
def process_number(n):
    if type(n) is int:   # именно int, не bool, не подкласс
        return n * 2
    raise TypeError("Нужен именно int, не подкласс")

print(process_number(5))     # 10
try:
    process_number(True)     # True — это bool, подкласс int
except TypeError as e:
    print(e)   # Нужен именно int, не подкласс

# Сценарий 3: isinstance() с кортежем — type() так не умеет
value = 42
print(isinstance(value, (int, float, str)))   # True
# type() потребует несколько проверок:
print(type(value) in (int, float, str))       # True — но менее читаемо
```

**Правило**: используйте `isinstance()` по умолчанию — он корректно работает с наследованием и виртуальными подклассами. Используйте `type() is` только в специфических случаях, когда вам нужна точная проверка типа без учёта наследования.

---

## Практический пример: полиморфная система сериализации

Реализуем гибкую систему сериализации, сочетающую duck typing, `isinstance()` для встроенных типов и ABC для проверки протокола:

```python
import json
import datetime
from decimal import Decimal
from abc import ABC, abstractmethod


class Serializable(ABC):
    """Протокол для объектов, умеющих сериализовать себя."""

    @abstractmethod
    def to_dict(self) -> dict:
        pass

    @classmethod
    def __subclasshook__(cls, subclass):
        if cls is Serializable:
            return hasattr(subclass, 'to_dict') and callable(getattr(subclass, 'to_dict'))
        return NotImplemented


class WebAPISerializer:
    """
    Сериализатор для Web API. Превращает любые объекты в JSON-совместимый формат.

    Стратегия:
    1. Duck typing: если есть to_dict() — используем его
    2. isinstance() для встроенных типов, которые нельзя расширить
    3. EAFP: при ошибке — понятное сообщение
    """

    def serialize(self, obj):
        """Основной метод сериализации."""
        return self._convert(obj)

    def _convert(self, obj):
        # Duck typing первым: если объект умеет сериализовать себя — доверяем ему
        if isinstance(obj, Serializable):
            return self._convert(obj.to_dict())

        # Встроенные примитивы — уже JSON-совместимы
        if isinstance(obj, (int, float, str, bool)) or obj is None:
            return obj

        # Дата/время — особый формат
        if isinstance(obj, datetime.datetime):
            return {"__type": "datetime", "value": obj.isoformat()}

        if isinstance(obj, datetime.date):
            return {"__type": "date", "value": obj.isoformat()}

        # Decimal — конвертируем в строку для точности
        if isinstance(obj, Decimal):
            return {"__type": "decimal", "value": str(obj)}

        # Коллекции — рекурсивно
        if isinstance(obj, dict):
            return {str(k): self._convert(v) for k, v in obj.items()}

        if isinstance(obj, (list, tuple)):
            return [self._convert(item) for item in obj]

        if isinstance(obj, set):
            return sorted([self._convert(item) for item in obj])

        # Последний шанс: объект с __dict__ (любой пользовательский класс)
        if hasattr(obj, '__dict__'):
            return self._convert(vars(obj))

        raise TypeError(
            f"Невозможно сериализовать объект типа {type(obj).__name__}"
        )

    def to_json(self, obj, **kwargs):
        """Конвертирует в строку JSON."""
        converted = self.serialize(obj)
        return json.dumps(converted, **kwargs)


# Объекты с to_dict() — работают через duck typing
class UserProfile:
    def __init__(self, user_id, username, email):
        self.user_id = user_id
        self.username = username
        self.email = email
        self.registered_at = datetime.date.today()

    def to_dict(self):
        return {
            "id": self.user_id,
            "username": self.username,
            "email": self.email,
            "registered": self.registered_at,
        }


class OrderItem:
    def __init__(self, product_name, quantity, price):
        self.product_name = product_name
        self.quantity = quantity
        self.price = Decimal(str(price))

    def to_dict(self):
        return {
            "product": self.product_name,
            "qty": self.quantity,
            "price": self.price,
            "total": self.price * self.quantity,
        }


serializer = WebAPISerializer()

# Проверяем isinstance с Serializable через __subclasshook__
print(isinstance(UserProfile(1, "a", "b"), Serializable))   # True

# Сериализуем сложную структуру
response_data = {
    "user": UserProfile(42, "alice", "alice@example.com"),
    "order": {
        "id": 1001,
        "created_at": datetime.datetime.now(),
        "items": [
            OrderItem("Ноутбук", 1, "89990.00"),
            OrderItem("Мышь", 2, "1500.00"),
        ],
        "discount": Decimal("0.10"),
    },
    "tags": {"premium", "new_user"},
}

result = serializer.to_json(response_data, indent=2, ensure_ascii=False)
print(result)
```

---

## Практический пример: диспетчер событий

Полный пример системы событий, сочетающей полиморфизм через наследование, duck typing и `isinstance()` для диспетчеризации:

```python
from typing import Callable, List


class Event:
    """Базовое событие системы."""

    def __init__(self, source: str):
        self.source = source
        self.timestamp = datetime.datetime.now()

    def __repr__(self):
        return f"{self.__class__.__name__}(source={self.source!r})"


class HTTPRequestEvent(Event):
    def __init__(self, source, method, path, status_code):
        super().__init__(source)
        self.method = method
        self.path = path
        self.status_code = status_code


class UserActionEvent(Event):
    def __init__(self, source, user_id, action):
        super().__init__(source)
        self.user_id = user_id
        self.action = action


class ErrorEvent(Event):
    def __init__(self, source, error_type, message, traceback=None):
        super().__init__(source)
        self.error_type = error_type
        self.message = message
        self.traceback = traceback


class EventBus:
    """
    Шина событий. Поддерживает несколько паттернов подписки:
    1. По конкретному типу события
    2. По базовому типу (все дочерние тоже получают)
    3. Duck typing: любой вызываемый объект является обработчиком
    """

    def __init__(self):
        self._subscribers: dict = {}

    def subscribe(self, event_type, handler: Callable):
        """
        Подписка на событие.
        handler — любой вызываемый объект (функция, метод, класс с __call__).
        Duck typing: не проверяем тип handler — просто вызываем его.
        """
        if not callable(handler):
            raise TypeError(f"Handler должен быть вызываемым, получен {type(handler)}")

        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)

    def publish(self, event: Event):
        """
        Публикация события. Вызывает все подходящие обработчики.
        isinstance() здесь легитимен: нам нужна диспетчеризация по типу.
        """
        if not isinstance(event, Event):
            raise TypeError(f"Ожидается Event, получен {type(event).__name__}")

        called_handlers = set()
        for event_type, handlers in self._subscribers.items():
            if isinstance(event, event_type):
                for handler in handlers:
                    handler_id = id(handler)
                    if handler_id not in called_handlers:
                        handler(event)
                        called_handlers.add(handler_id)


# Обработчики — любые вызываемые объекты (duck typing)
def log_all_events(event):
    print(f"[LOG] {event.timestamp.strftime('%H:%M:%S')} — {event}")


def monitor_errors(event):
    print(f"[ALERT] Ошибка: {event.error_type}: {event.message}")


class MetricsCollector:
    """Класс-обработчик — вызывается через __call__."""
    def __init__(self):
        self.request_count = 0
        self.error_count = 0

    def __call__(self, event):
        if isinstance(event, HTTPRequestEvent):
            self.request_count += 1
        elif isinstance(event, ErrorEvent):
            self.error_count += 1
        print(f"[METRICS] Запросов: {self.request_count}, Ошибок: {self.error_count}")


bus = EventBus()
metrics = MetricsCollector()

bus.subscribe(Event, log_all_events)                   # все события
bus.subscribe(HTTPRequestEvent, metrics)               # только HTTP-запросы
bus.subscribe(ErrorEvent, monitor_errors)              # только ошибки
bus.subscribe(ErrorEvent, metrics)                     # ошибки тоже в метрики

# Публикуем события
bus.publish(HTTPRequestEvent("api", "GET", "/users", 200))
print()
bus.publish(ErrorEvent("db", "ConnectionError", "Соединение прервано"))
```

---

## Неочевидные моменты и типичные ошибки

**`isinstance(True, int)` возвращает `True`.** Это самая частая ловушка при работе с `isinstance()`. `bool` является подклассом `int`, поэтому `True` проходит проверку `isinstance(obj, int)`. Всегда проверяйте `bool` перед `int`:

```python
print(isinstance(True, int))    # True — неожиданно!
print(isinstance(True, bool))   # True
print(isinstance(1, bool))      # False — int не является bool

# Правильный порядок проверок:
def process(value):
    if isinstance(value, bool):   # СНАЧАЛА bool
        return f"boolean: {value}"
    if isinstance(value, int):    # ПОТОМ int
        return f"integer: {value}"
```

**`issubclass()` выбрасывает `TypeError`, если первый аргумент не класс.** Это отличает её от `isinstance()`, которая принимает объекты:

```python
obj = "hello"

isinstance(obj, str)      # OK — obj это объект
try:
    issubclass(obj, str)  # TypeError — obj должен быть классом
except TypeError as e:
    print(e)   # issubclass() arg 1 must be a class

# Правильный способ проверить, является ли что-то классом:
print(isinstance(str, type))    # True — str это класс
print(isinstance(obj, type))    # False — "hello" это не класс
```

**`isinstance()` с несуществующим типом — TypeError.** Если второй аргумент не является классом или кортежем классов:

```python
try:
    isinstance(42, "int")   # TypeError
except TypeError as e:
    print(e)   # isinstance() arg 2 must be a type, a tuple of types, or a union
```

**Производительность `isinstance()`.** В горячих циклах (обработка тысяч объектов в секунду) многократные проверки `isinstance()` могут стать узким местом. В таких случаях предпочтительнее полиморфизм через методы — он работает через таблицу виртуальных методов и значительно быстрее.

---

## Итоги урока

Полиморфизм — это способность разных объектов отвечать на одни и те же вызовы. В Python он реализуется двумя способами: через наследование (классический ООП) и через duck typing (объект не обязан быть подклассом — достаточно иметь нужные методы).

Duck typing — идиоматичный стиль Python. Функции пишутся для «протоколов» (наборов методов), а не для конкретных типов. Любой объект, реализующий нужные методы, автоматически работает в этом контексте.

`isinstance()` уместен для: диспетчеризации по типу встроенных объектов, валидации входных данных, специальной обработки конкретного подтипа. Антипаттерн: заменять полиморфизм длинными цепочками `isinstance()`.

Абстрактные базовые классы с `__subclasshook__` позволяют расширить поведение `isinstance()`: класс может пройти проверку без реального наследования, если реализует нужные методы. Это мост между duck typing и явной типизацией.

`bool` является подклассом `int` — всегда проверяйте `bool` перед `int` при использовании `isinstance()`. `issubclass()` принимает только классы как первый аргумент — для проверки, что объект является классом, используйте `isinstance(obj, type)`.

В следующем уроке мы подробно рассмотрим абстрактные классы — модуль `abc`, декоратор `@abstractmethod` и то, как они формализуют протоколы, обеспечивая, что дочерние классы обязательно реализуют нужные методы.

---

## Контрольные вопросы

1. В чём принципиальное отличие полиморфизма через наследование и duck typing? Какой из них является более идиоматичным для Python?
2. Что такое «протокол» в контексте duck typing? Приведите два примера протоколов из стандартной библиотеки Python.
3. Когда использование `isinstance()` в полиморфном коде является антипаттерном, а когда — легитимным инструментом?
4. Почему при проверке через `isinstance()` нужно проверять `bool` перед `int`?
5. Что такое EAFP и LBYL? Какой стиль предпочтителен в Python и почему?
6. Что такое виртуальный подкласс и как его создать? Как это связывает duck typing и `isinstance()`?
7. Чем `issubclass()` отличается от `isinstance()` в плане допустимых аргументов? Как проверить, что объект является классом?
8. В примере с `EventBus` из лекции использование `isinstance()` в методе `publish()` является легитимным, а не антипаттерном. Объясните почему.

---

## Практические задачи

### Задача 1. 

Полиморфный рендерер

Создайте систему рендеринга HTML-компонентов. Базовый класс `HTMLComponent` с абстрактным методом `render() -> str`. Дочерние классы:
- `Heading(HTMLComponent)` — принимает `text` и `level` (1–6), рендерит `<h1>text</h1>`.
- `Paragraph(HTMLComponent)` — принимает `text`, рендерит `<p>text</p>`.
- `Button(HTMLComponent)` — принимает `text` и `action` (строка-URL), рендерит `<button onclick="...">text</button>`.
- `Link(HTMLComponent)` — принимает `text` и `href`, рендерит `<a href="...">text</a>`.

Напишите функцию `render_page(components: list) -> str`, которая рендерит список компонентов через полиморфизм (без проверки типов). Добавьте класс `RawHTML`, который **не наследует** от `HTMLComponent`, но имеет метод `render()`. Убедитесь, что `render_page()` работает и с `RawHTML` через duck typing.

**Пример использования**:

```python
components = [
    Heading("Добро пожаловать", level=1),
    Paragraph("Это наша платформа для разработчиков."),
    Button("Начать", action="/register"),
    Link("Документация", href="/docs"),
    RawHTML("<hr/>"),   # не является HTMLComponent, но работает
]

html = render_page(components)
print(html)
# <h1>Добро пожаловать</h1>
# <p>Это наша платформа для разработчиков.</p>
# <button onclick="/register">Начать</button>
# <a href="/docs">Документация</a>
# <hr/>
```

---

### Задача 2. 

Универсальный конвертер форматов

Напишите функцию `convert_to_string(value) -> str`, которая преобразует любое значение в строку для API-ответа. Правила: `bool` → `"true"` или `"false"` (до `int`!), `int` и `float` → строка числа, `None` → `"null"`, `list` и `tuple` → рекурсивно конвертировать каждый элемент, объединить через `", "` и обернуть в `"[...]"`, `dict` → конвертировать ключи и значения, формат `"{key: value, ...}"`, объект с методом `__str__`, не являющийся базовым типом → использовать `str(obj)`. Используйте правильный порядок `isinstance()` проверок.

Пример использования:

```python
print(convert_to_string(True))           # "true"
print(convert_to_string(42))             # "42"
print(convert_to_string(None))           # "null"
print(convert_to_string([1, True, None, "hi"]))   # "[1, true, null, hi]"
print(convert_to_string({"a": 1, "b": True}))     # "{a: 1, b: true}"
```

---

### Задача 3. 

Система хранилищ с duck typing

Создайте три класса хранилищ данных, которые реализуют одинаковый интерфейс (duck typing — без общего базового класса):
- `InMemoryStorage` — хранит данные в словаре.
- `FileStorage` — имитирует хранение: при `save()` выводит `"[File] записано: key"`, при `load()` возвращает данные из внутреннего словаря.
- `CacheStorage` — хранит данные с TTL (time-to-live). При `load()`, если данные просрочены (TTL секунд прошло) — возвращает `None`.

Каждый класс должен иметь методы `save(key, data)`, `load(key)`, `delete(key)`, `exists(key)`. Напишите функцию `backup(source, destination)`, которая копирует все данные из одного хранилища в другое через их общий интерфейс (без `isinstance()`). Продемонстрируйте, что все три хранилища взаимозаменяемы.

**Пример использования**:

```python
mem = InMemoryStorage()
file_storage = FileStorage()
cache = CacheStorage(ttl=60)

mem.save("user:1", {"name": "Alice"})
mem.save("user:2", {"name": "Bob"})

backup(mem, file_storage)   # Копируем из памяти в файл
backup(mem, cache)          # Копируем из памяти в кеш

print(file_storage.load("user:1"))   # {'name': 'Alice'}
print(cache.load("user:1"))          # {'name': 'Alice'}
print(cache.exists("user:99"))       # False
```

---

### Задача 4. 

Полиморфный pipeline обработки данных

Создайте систему pipeline для обработки данных. Каждый шаг pipeline — объект с методом `process(data) -> data`. Шаги:
- `Validator` — принимает `rules` (список функций-предикатов). Проверяет каждое правило, выбрасывает `ValueError` при нарушении.
- `Transformer` — принимает `transform_fn` (функция преобразования данных).
- `Filter` — принимает `predicate` (функция-предикат). Если данные — список, фильтрует его; иначе проверяет одиночный объект.
- `Logger` — выводит данные на каждом этапе, возвращает данные без изменений.

Напишите класс `Pipeline`, который принимает список шагов и метод `run(data)`, последовательно применяющий их. `Pipeline` не должен проверять типы шагов — только вызывать `step.process(data)`. Добавьте `LambdaStep` — обёртку над функцией: `LambdaStep(fn)`, `process(data)` просто вызывает `fn(data)`.

**Пример использования**:

```python
pipeline = Pipeline([
    Logger("[Input]"),
    Validator([
        lambda d: len(d) > 0,                   # не пустой список
        lambda d: all(isinstance(x, dict) for x in d)   # список словарей
    ]),
    Filter(lambda user: user.get("is_active", False)),
    Transformer(lambda users: [u["email"] for u in users]),
    LambdaStep(lambda emails: sorted(emails)),
    Logger("[Output]"),
])

users = [
    {"email": "charlie@example.com", "is_active": False},
    {"email": "alice@example.com",   "is_active": True},
    {"email": "bob@example.com",     "is_active": True},
]

result = pipeline.run(users)
print(result)   # ['alice@example.com', 'bob@example.com']
```

---

### Задача 5. 

Диспетчер команд с `isinstance()`

Создайте систему обработки команд REST API. Базовый класс `Command` с атрибутами `resource` (строка) и `payload` (словарь). Дочерние классы: `CreateCommand`, `UpdateCommand`, `DeleteCommand`, `ReadCommand`. Класс `CommandDispatcher` содержит словарь `{CommandClass: handler_function}` и метод `register(command_class, handler)`. Метод `dispatch(command)` использует `isinstance()` для нахождения подходящего обработчика — проверяет по иерархии (обработчик для базового класса вызывается для всех дочерних). Добавьте метод `dispatch_all(commands)` с подсчётом успешных и ошибочных обработок.

**Пример использования**:

```python
dispatcher = CommandDispatcher()

dispatcher.register(ReadCommand, lambda c: print(f"READ {c.resource}"))
dispatcher.register(CreateCommand, lambda c: print(f"CREATE {c.resource}: {c.payload}"))
dispatcher.register(UpdateCommand, lambda c: print(f"UPDATE {c.resource}: {c.payload}"))
dispatcher.register(DeleteCommand, lambda c: print(f"DELETE {c.resource}"))

commands = [
    ReadCommand("users"),
    CreateCommand("users", {"name": "Alice"}),
    UpdateCommand("users/1", {"name": "Bob"}),
    DeleteCommand("users/2"),
]

stats = dispatcher.dispatch_all(commands)
print(stats)   # {'success': 4, 'errors': 0}
```

---

### Задача 6. 

Протокол «экспортируемый»

Создайте ABC `Exportable` с методом `to_export_dict() -> dict` и `__subclasshook__`, который возвращает `True` для любого класса, имеющего метод `to_export_dict`. Создайте три класса:
- `ProductModel` (наследует `Exportable`) — атрибуты `name`, `price`, `category`. Реализует `to_export_dict()`.
- `OrderModel` (наследует `Exportable`) — атрибуты `order_id`, `items` (список), `total`. Реализует `to_export_dict()`.
- `LegacyReport` (НЕ наследует `Exportable`) — старый класс с методом `to_export_dict()`. Должен пройти проверку `isinstance(..., Exportable)` через `__subclasshook__`.

Напишите функцию `export_batch(objects: list) -> list`, которая:
1. Принимает любые объекты.
2. Проверяет через `isinstance(obj, Exportable)` — если объект поддерживает протокол, экспортирует его.
3. Для объектов, не поддерживающих протокол — добавляет в результат `{"error": "not exportable", "type": type(obj).__name__}`.

Пример использования:

```python
objects = [
    ProductModel("Ноутбук", 89990, "electronics"),
    OrderModel(1001, ["item1", "item2"], 91490),
    LegacyReport("Q1 2024", {"revenue": 1000000}),
    "just a string",   # не поддерживает протокол
    42,                # не поддерживает протокол
]

result = export_batch(objects)
for item in result:
    print(item)
```

---

[Предыдущий урок](lesson21.md) | [Следующий урок](lesson23.md)