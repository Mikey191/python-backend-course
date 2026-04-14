# Урок 21. Атрибуты `private` и `protected` при наследовании

---

## Напоминание: три уровня доступа

В модуле 2 мы подробно разобрали уровни доступа в Python. Здесь — краткое напоминание, необходимое для понимания поведения при наследовании.

Python не имеет аппаратных ограничений доступа — нет ключевых слов `private` или `protected`, как в Java или C++. Вместо этого используются соглашения об именовании:

```python
class MyClass:
    def __init__(self):
        self.public_attr = "доступен всем"
        self._protected_attr = "доступен классу и потомкам (соглашение)"
        self.__private_attr = "приватный (name mangling)"
```

При наследовании каждый из этих уровней ведёт себя принципиально по-разному. Именно это и является темой данного урока.

---

## Публичные атрибуты: полная прозрачность

Публичные атрибуты и методы наследуются без каких-либо ограничений. Дочерний класс видит их, может читать, изменять и переопределять. Это мы уже разобрали в уроках 19 и 20, здесь лишь зафиксируем для полноты картины:

```python
class User:
    def __init__(self, username):
        self.username = username   # публичный

    def get_display_name(self):    # публичный метод
        return self.username.capitalize()


class AdminUser(User):
    def greet(self):
        # Полный доступ к публичным атрибутам и методам родителя
        return f"Привет, {self.get_display_name()}!"


admin = AdminUser("alice")
print(admin.greet())         # Привет, Alice!
print(admin.username)        # alice — доступ снаружи тоже работает
```

Публичные атрибуты — это открытый контракт класса. Они предназначены для использования кем угодно: дочерними классами, внешним кодом, тестами.

---

## Защищённые атрибуты при наследовании

**Защищённый атрибут** (`_name`) — это атрибут с одним подчёркиванием. Технически он полностью доступен отовсюду: Python не ограничивает к нему доступ никак. Одно подчёркивание — это только соглашение, сигнал другим разработчикам: «это внутренняя деталь реализации, не используйте это снаружи».

В контексте наследования защищённые атрибуты образуют «внутренний API» класса для его потомков:

```python
class BaseAuth:
    def __init__(self, user):
        self._user = user                  # защищённый — для потомков
        self._session_data = {}            # защищённый — для потомков
        self._max_attempts = 3             # защищённый — настройка

    def _validate_token(self, token):      # защищённый метод — часть внутреннего API
        return token and len(token) > 10

    def authenticate(self, token):
        if self._validate_token(token):
            self._session_data["authenticated"] = True
            return True
        return False


class JWTAuth(BaseAuth):
    def __init__(self, user, secret_key):
        super().__init__(user)
        self._secret_key = secret_key      # защищённый атрибут дочернего класса

    def _validate_token(self, token):
        # Переопределяем защищённый метод родителя
        # Дочерний класс может расширять и изменять внутреннее поведение
        if not super()._validate_token(token):
            return False
        # Дополнительная проверка: токен должен содержать три части (JWT-формат)
        return len(token.split(".")) == 3

    def get_user_from_session(self):
        # Доступ к защищённому атрибуту родителя — допустимо для потомков
        return self._user if self._session_data.get("authenticated") else None
```

Важно понимать риск, который возникает при использовании защищённых атрибутов в потомках. Если родительский класс изменит имя или семантику `_session_data` — дочерний класс сломается. Это нарушение принципа инкапсуляции: дочерний класс стал зависеть от деталей реализации родителя.

Именно поэтому в хорошо спроектированных иерархиях важно различать:
- атрибуты, предназначенные для потомков — они остаются защищёнными стабильно,
- атрибуты, которые являются чисто внутренними деталями — их делают приватными.

---

## Механизм **name mangling**: как Python защищает приватные атрибуты

Приватные атрибуты с двойным подчёркиванием в начале (`__name`) обрабатываются Python специальным образом на уровне компилятора. Это называется **name mangling** (искажение имени): Python автоматически переименовывает `__attr` в `_ClassName__attr`, где `ClassName` — имя класса, в котором этот атрибут объявлен.

```python
class User:
    def __init__(self, username, password):
        self.username = username
        self.__password_hash = self._hash(password)   # станет _User__password_hash

    def _hash(self, password):
        return hash(password)   # упрощённо

    def check_password(self, password):
        return self.__password_hash == self._hash(password)


user = User("alice", "secret123")

# Смотрим реальные имена атрибутов
print(user.__dict__)
# {'username': 'alice', '_User__password_hash': <hash_value>}
#                         ^^^^^^^^^^^^^^^^^
#                         имя после name mangling

# Прямой доступ по исходному имени — AttributeError
try:
    print(user.__password_hash)
except AttributeError as e:
    print(e)   # 'User' object has no attribute '__password_hash'

# Доступ по трансформированному имени — работает (но не делайте так!)
print(user._User__password_hash)   # <hash_value> — это нарушение инкапсуляции
```

Зачем Python делает **name mangling** вместо полного запрета доступа? Потому что цели две, и они разные:

**Первая цель** — защита от случайных коллизий имён в иерархиях. Если родительский класс использует `__attr`, а дочерний класс тоже случайно объявит `__attr` — без name mangling они перезапишут друг друга. С name mangling они получают разные имена (`_Parent__attr` и `_Child__attr`) и не мешают друг другу.

**Вторая цель** — сигнал разработчику: «это деталь реализации, не предназначенная для использования снаружи». Python доверяет разработчику и не ставит технических замков — но делает случайный доступ неудобным.

---

## Приватные атрибуты и наследование: ключевой момент

Вот самое важное, что нужно понять о приватных атрибутах при наследовании: **дочерний класс НЕ может обратиться к приватному атрибуту родителя через `self.__attr`**. Вместо этого Python создаёт новый атрибут с именем дочернего класса.

Рассмотрим это пошагово:

```python
class Parent:
    def __init__(self):
        self.__secret = "секрет родителя"   # станет _Parent__secret

    def reveal(self):
        return self.__secret   # внутри Parent — обращается к _Parent__secret


class Child(Parent):
    def __init__(self):
        super().__init__()
        self.__secret = "секрет ребёнка"   # станет _Child__secret — ДРУГОЙ атрибут!

    def reveal_child(self):
        return self.__secret   # обращается к _Child__secret


obj = Child()

# Смотрим, что реально хранится в объекте
print(obj.__dict__)
# {'_Parent__secret': 'секрет родителя', '_Child__secret': 'секрет ребёнка'}
#   ^^^^^^^^^^^^^^^^                       ^^^^^^^^^^^^^^^
#   атрибут родителя                       атрибут дочернего класса — отдельный!

print(obj.reveal())         # секрет родителя   — метод Parent видит _Parent__secret
print(obj.reveal_child())   # секрет ребёнка    — метод Child видит _Child__secret
```

Это означает, что дочерний класс не может случайно перезаписать приватный атрибут родителя. Каждый класс в иерархии имеет свою «приватную» область, изолированную name mangling.

Посмотрим на практическое следствие этого. Что происходит, когда дочерний класс пытается обратиться к приватному атрибуту родителя:

```python
class SecureConfig:
    def __init__(self, api_key):
        self.__api_key = api_key   # _SecureConfig__api_key

    def get_masked_key(self):
        # Возвращает маскированную версию ключа
        return self.__api_key[:4] + "****"


class ExtendedConfig(SecureConfig):
    def show_full_key(self):
        # Попытка обратиться к __api_key родителя
        try:
            return self.__api_key   # ищет _ExtendedConfig__api_key — не существует!
        except AttributeError as e:
            return f"AttributeError: {e}"

    def show_key_properly(self):
        # Правильный способ: использовать публичный метод родителя
        return self.get_masked_key()


config = ExtendedConfig("sk-abc123xyz")

print(config.get_masked_key())     # sk-a****
print(config.show_full_key())      # AttributeError: no attribute '_ExtendedConfig__api_key'
print(config.show_key_properly())  # sk-a****

# Посмотрим на __dict__
print(config.__dict__)
# {'_SecureConfig__api_key': 'sk-abc123xyz'}
# _ExtendedConfig__api_key НЕТ — он не создаётся при ошибочном обращении
```

**Вывод**: приватный атрибут родителя недоступен в дочернем классе через обычный синтаксис `self.__attr`. Если дочернему классу нужно работать с данными, хранящимися в приватном атрибуте — это должно происходить через публичный или защищённый интерфейс, который предоставляет родитель.

---

## Как правильно организовать доступ к данным родителя

Если дочернему классу нужен доступ к данным, которые родитель хранит в приватных атрибутах, есть три правильных способа.

**Способ 1: публичные или защищённые методы-геттеры.** Родитель предоставляет метод, который возвращает нужные данные. Это самый чистый подход:

```python
class User:
    def __init__(self, username, password):
        self.username = username
        self.__password_hash = hash(password)

    def check_password(self, password):
        return self.__password_hash == hash(password)

    def _get_password_hash(self):
        # Защищённый метод для использования потомками
        return self.__password_hash


class AdminUser(User):
    def transfer_credentials(self, other_admin):
        # Используем защищённый метод, а не прямой доступ к __password_hash
        return self._get_password_hash() == other_admin._get_password_hash()
```

**Способ 2: `@property` для контролируемого доступа.** Родитель предоставляет свойство, которое наследуется:

```python
class Token:
    def __init__(self, value, expires_in_seconds):
        self.__value = value
        self.__expires_in = expires_in_seconds

    @property
    def value(self):
        """Значение токена доступно через property."""
        return self.__value

    @property
    def is_expired(self):
        import time
        return time.time() > self.__expires_in


class RefreshableToken(Token):
    def get_authorization_header(self):
        # Используем property родителя — это правильно
        if self.is_expired:
            return None
        return f"Bearer {self.value}"
```

**Способ 3: через `_ClassName__attr` напрямую — только в крайнем случае.** Технически возможно, но считается нарушением инкапсуляции. Используйте только если нет другого выхода и вы точно знаете, что делаете:

```python
class Child(Parent):
    def access_parent_private(self):
        # Крайний случай — обход name mangling явно
        return self._Parent__secret   # работает, но нарушает инкапсуляцию
```

---

## Когда использовать `_` и когда `__`: практические критерии

Выбор между защищённым и приватным атрибутом — это архитектурное решение. Задайте себе вопрос: «Должны ли потомки этого класса работать с этим атрибутом?»

Используйте **защищённый** (`_attr`), если:
- атрибут является частью «контракта» для потомков — они могут и должны его читать,
- метод является «точкой расширения» для дочерних классов (паттерн Template Method),
- значение может быть переопределено в дочернем классе как настройка.

Используйте **приватный** (`__attr`), если:
- атрибут является деталью реализации, которая не должна быть видна даже потомкам,
- изменение этого атрибута из дочернего класса может нарушить инварианты родителя,
- вы хотите защититься от случайных коллизий имён при глубоком наследовании.

Посмотрим на пример из Django ORM как образец правильного выбора:

```python
# Упрощённая имитация Django Model
class Model:
    _meta = None           # ЗАЩИЩЁННЫЙ: потомки (конкретные модели) читают _meta

    def __init__(self):
        self.__state = {}  # ПРИВАТНЫЙ: состояние объекта — только для внутреннего использования

    def _do_insert(self, manager):   # ЗАЩИЩЁННЫЙ: точка расширения для потомков
        pass

    def save(self):
        # Алгоритм сохранения
        if not self.__state.get("adding"):
            self._do_insert(self.__class__._default_manager)
        else:
            self._do_update(self.__class__._default_manager)
```

`_meta` защищённый, потому что модели-потомки обращаются к `MyModel._meta.fields`. `__state` приватный, потому что это внутренний механизм Django, который конкретные модели не должны трогать.

---

## Паттерн Template Method с защищёнными методами

Один из самых мощных паттернов, реализуемых через защищённые методы — Template Method. Родительский класс определяет алгоритм как последовательность шагов, некоторые из которых вынесены в защищённые методы. Потомки переопределяют только эти шаги, сохраняя общую структуру алгоритма.

```python
class DataProcessor:
    """
    Базовый класс обработки данных.
    Определяет алгоритм: загрузить → валидировать → трансформировать → сохранить.
    Каждый шаг — защищённый метод, который можно переопределить.
    """

    def process(self, raw_data):
        """
        Шаблонный метод — определяет алгоритм.
        Не переопределяется в потомках.
        """
        data = self._load(raw_data)
        if not self._validate(data):
            raise ValueError(f"Данные не прошли валидацию: {data}")
        transformed = self._transform(data)
        self._save(transformed)
        return transformed

    def _load(self, raw_data):
        """Загрузка данных. Можно переопределить для разных источников."""
        print(f"[DataProcessor._load] загрузка {len(raw_data)} байт")
        return raw_data

    def _validate(self, data):
        """Базовая валидация — проверяет, что данные не пустые."""
        return bool(data)

    def _transform(self, data):
        """Трансформация по умолчанию — без изменений."""
        return data

    def _save(self, data):
        """Сохранение. По умолчанию — вывод в консоль."""
        print(f"[DataProcessor._save] сохранено {len(str(data))} символов")


class UserDataProcessor(DataProcessor):
    """Обработчик данных пользователей. Переопределяет только нужные шаги."""

    def __init__(self, required_fields):
        self._required_fields = required_fields   # защищённый атрибут конфигурации

    def _validate(self, data):
        # Расширяем базовую валидацию — добавляем проверку обязательных полей
        if not super()._validate(data):
            return False
        if not isinstance(data, dict):
            return False
        return all(field in data for field in self._required_fields)

    def _transform(self, data):
        # Нормализуем: email в нижнем регистре, username без пробелов
        result = dict(data)
        if "email" in result:
            result["email"] = result["email"].lower().strip()
        if "username" in result:
            result["username"] = result["username"].strip()
        return result


class CSVUserDataProcessor(UserDataProcessor):
    """Обработчик пользователей из CSV. Переопределяет только загрузку."""

    def _load(self, raw_data):
        # raw_data — строка CSV, конвертируем в список словарей
        print("[CSVUserDataProcessor._load] парсинг CSV")
        lines = raw_data.strip().split("\n")
        headers = lines[0].split(",")
        rows = []
        for line in lines[1:]:
            values = line.split(",")
            rows.append(dict(zip(headers, values)))
        # Для простоты обрабатываем первую запись
        return rows[0] if rows else {}
```

Демонстрация:

```python
processor = UserDataProcessor(required_fields=["username", "email"])

# Корректные данные
result = processor.process({"username": " Alice ", "email": "ALICE@EXAMPLE.COM"})
print(result)
# [DataProcessor._load] загрузка 53 байт
# [DataProcessor._save] сохранено 50 символов
# {'username': 'Alice', 'email': 'alice@example.com'}

# Некорректные данные — отсутствует обязательное поле
try:
    processor.process({"username": "Bob"})
except ValueError as e:
    print(e)
# Данные не прошли валидацию: {'username': 'Bob'}

# CSV-обработчик переопределяет только _load, остальное берётся от родителей
csv_processor = CSVUserDataProcessor(required_fields=["username", "email"])
csv_data = "username,email,age\ncarol,CAROL@EXAMPLE.COM,28"
result = csv_processor.process(csv_data)
print(result)
# [CSVUserDataProcessor._load] парсинг CSV
# [DataProcessor._save] сохранено ...
# {'username': 'carol', 'email': 'carol@example.com', 'age': '28'}
```

Ключевое преимущество: метод `process()` в `BaseDataProcessor` никогда не переопределяется — алгоритм зафиксирован. Каждый дочерний класс подстраивает только те шаги, которые нужны, не трогая общую структуру.

---

## Наследование `@property` и его переопределение

`@property` при наследовании ведёт себя так же, как обычный метод — дочерний класс наследует его и может переопределить. Но здесь есть несколько нюансов, которые часто приводят к ошибкам.

**Наследование property работает автоматически:**

```python
class Shape:
    def __init__(self, color):
        self._color = color

    @property
    def color(self):
        return self._color

    @color.setter
    def color(self, value):
        if not isinstance(value, str):
            raise TypeError("Цвет должен быть строкой")
        self._color = value


class Circle(Shape):
    def __init__(self, radius, color):
        super().__init__(color)
        self._radius = radius

    @property
    def area(self):
        import math
        return math.pi * self._radius ** 2


circle = Circle(5, "red")
print(circle.color)     # red — property наследуется
circle.color = "blue"   # setter тоже наследуется
print(circle.color)     # blue
print(circle.area)      # 78.539...
```

**Переопределение только геттера — распространённая ловушка.** Если в дочернем классе определить только геттер через `@property`, сеттер из родителя теряется:

```python
class ValidatedShape(Shape):
    @property
    def color(self):
        # Только переопределяем геттер — возвращаем в верхнем регистре
        return self._color.upper()
    # Сеттер НЕ определён — он НЕ наследуется автоматически при переопределении геттера!


vs = ValidatedShape("red")
print(vs.color)        # RED — геттер работает

try:
    vs.color = "blue"  # AttributeError: can't set attribute
except AttributeError as e:
    print(e)
```

Это неочевидное поведение: при переопределении `@property` в дочернем классе вы создаёте новый объект-дескриптор, который не содержит сеттера родителя. Чтобы сохранить сеттер, нужно либо переопределить и его тоже, либо использовать специальный синтаксис:

```python
class ValidatedShape(Shape):
    @Shape.color.getter   # переопределяем только геттер, сохраняя сеттер
    def color(self):
        return self._color.upper()


vs = ValidatedShape("red")
print(vs.color)     # RED — геттер переопределён
vs.color = "blue"   # OK — сеттер из Shape работает
print(vs.color)     # BLUE
```

**Правильный способ переопределить и геттер, и сеттер в дочернем классе:**

```python
class StrictCircle(Shape):
    ALLOWED_COLORS = {"red", "blue", "green", "black", "white"}

    @property
    def color(self):
        return self._color

    @color.setter
    def color(self, value):
        if value not in self.ALLOWED_COLORS:
            raise ValueError(
                f"Недопустимый цвет: {value!r}. "
                f"Разрешены: {self.ALLOWED_COLORS}"
            )
        # Вызываем сеттер родителя через super() для выполнения его проверок тоже
        super(StrictCircle, StrictCircle).color.fset(self, value)


sc = StrictCircle("red")
print(sc.color)      # red

sc.color = "blue"    # OK — blue в списке разрешённых
print(sc.color)      # blue

try:
    sc.color = "purple"   # ValueError
except ValueError as e:
    print(e)   # Недопустимый цвет: 'purple'. Разрешены: {...}
```

Синтаксис `super(StrictCircle, StrictCircle).color.fset(self, value)` — это способ вызвать сеттер родительского `property` из сеттера дочернего. Он выглядит громоздко, но является стандартным решением. Альтернатива — использовать защищённый атрибут напрямую: `self._color = value` после своих проверок.

---

## Практический пример: безопасная иерархия с инкапсуляцией

Соберём полноценный пример, демонстрирующий все изученные концепции вместе:

```python
import hashlib
import datetime


class SecureUser:
    """
    Пользователь с безопасным хранением пароля.

    Атрибуты:
    - __password_hash: приватный — дочерние классы НЕ должны работать с хешем напрямую
    - _role: защищённый — дочерние классы могут читать и переопределять
    - _permissions: защищённый — дочерние классы могут расширять
    - username, email: публичные — открытый контракт
    """

    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.__password_hash = self.__hash_password(password)   # _SecureUser__password_hash
        self._role = "user"
        self._permissions = {"read"}
        self.__created_at = datetime.datetime.now()              # _SecureUser__created_at

    @staticmethod
    def __hash_password(password):
        """Приватный статический метод — детали хеширования скрыты."""
        return hashlib.sha256(password.encode()).hexdigest()

    def check_password(self, password):
        """Публичный интерфейс для проверки пароля."""
        return self.__password_hash == self.__hash_password(password)

    def change_password(self, old_password, new_password):
        """Публичный интерфейс для смены пароля."""
        if not self.check_password(old_password):
            raise ValueError("Неверный текущий пароль")
        self.__password_hash = self.__hash_password(new_password)
        print(f"Пароль пользователя {self.username} изменён")

    @property
    def role(self):
        return self._role

    @property
    def permissions(self):
        return frozenset(self._permissions)   # возвращаем неизменяемую копию

    @property
    def created_at(self):
        return self.__created_at

    def has_permission(self, permission):
        return permission in self._permissions

    def get_info(self):
        return f"{self.username} ({self.email}), роль: {self._role}"

    def __repr__(self):
        return f"SecureUser(username={self.username!r}, role={self._role!r})"


class AdminUser(SecureUser):
    """
    Администратор. Расширяет права и добавляет специфические методы.
    Работает с _role и _permissions через правильный интерфейс.
    """

    def __init__(self, username, email, password, admin_level=1):
        super().__init__(username, email, password)
        # Изменяем защищённые атрибуты родителя — это допустимо для потомков
        self._role = "admin"
        self._permissions = {
            "read", "write", "delete", "manage_users", "view_logs"
        }
        self._admin_level = admin_level   # защищённый атрибут дочернего класса

    def promote_user(self, user):
        """Только администратор может повышать роль пользователей."""
        if not self.has_permission("manage_users"):
            raise PermissionError("Недостаточно прав")
        user._role = "moderator"
        user._permissions.add("moderate")
        print(f"{self.username} повысил {user.username} до модератора")

    def reset_user_password(self, user, new_password):
        """
        Администратор может сбросить пароль пользователя.
        Но не может напрямую читать его хеш — только вызвать change_password,
        или установить новый пароль через специальный механизм.
        """
        # Правильный способ: использовать публичный интерфейс
        # Мы не имеем доступа к user.__password_hash напрямую
        user._SecureUser__password_hash = SecureUser._SecureUser__hash_password(new_password)
        # Примечание: это всё ещё технически возможно через name mangling,
        # но в реальном коде лучше предоставить отдельный метод в SecureUser
        print(f"Пароль {user.username} сброшен администратором {self.username}")

    def get_info(self):
        base = super().get_info()
        return f"{base} [уровень {self._admin_level}]"


class ReadOnlyUser(SecureUser):
    """
    Пользователь только для чтения. Переопределяет _permissions
    и блокирует операции изменения.
    """

    def __init__(self, username, email, password):
        super().__init__(username, email, password)
        self._role = "readonly"
        self._permissions = {"read"}   # только чтение

    def change_password(self, old_password, new_password):
        # Переопределяем публичный метод — запрещаем смену пароля
        raise PermissionError("Пользователи только для чтения не могут менять пароль")
```

Демонстрируем:

```python
# Создаём пользователей
admin = AdminUser("alice", "alice@example.com", "admin_pass", admin_level=2)
regular = SecureUser("bob", "bob@example.com", "user_pass")
readonly = ReadOnlyUser("carol", "carol@example.com", "readonly_pass")

# Смотрим реальные атрибуты admin
print(list(admin.__dict__.keys()))
# ['username', 'email', '_SecureUser__password_hash', '_role', '_permissions',
#  '_SecureUser__created_at', '_admin_level']
#   ^^^^^^^^^^^^^^^^^^^^^^                ^^^^^^^^^^^^^^^^^^^^^^
#   приватные родителя с prefix           приватный родителя

# Публичный интерфейс работает
print(admin.check_password("admin_pass"))   # True
print(admin.check_password("wrong"))        # False
print(admin.role)                           # admin
print(admin.permissions)                    # frozenset({...})

# Пытаемся изменить роль у regular через admin
admin.promote_user(regular)
print(regular.role)          # moderator
print(regular.has_permission("moderate"))   # True

# Пробуем изменить пароль readonly-пользователя
try:
    readonly.change_password("readonly_pass", "new_pass")
except PermissionError as e:
    print(e)   # Пользователи только для чтения не могут менять пароль

# isinstance корректно определяет иерархию
print(isinstance(admin, SecureUser))   # True
print(isinstance(admin, AdminUser))    # True

# Приватный атрибут недоступен напрямую даже из дочернего класса
try:
    _ = admin.__created_at
except AttributeError as e:
    print(e)   # 'AdminUser' object has no attribute '__created_at'
```

---

## Практический пример: базовая модель данных

Рассмотрим второй пример — базовую модель данных с автоинкрементным приватным идентификатором, аналогичную тому, как устроены модели в Django:

```python
class BaseModel:
    """
    Базовая модель данных. Каждая запись имеет уникальный id.
    id — приватный: никто снаружи и ни один потомок не должны его изменять.
    """
    _id_counter = 0   # счётчик на уровне класса

    def __init__(self):
        BaseModel._id_counter += 1
        self.__id = BaseModel._id_counter   # _BaseModel__id — неизменяемый идентификатор
        self._is_saved = False              # защищённый — потомки могут читать

    @property
    def id(self):
        """id доступен только для чтения через property."""
        return self.__id

    @property
    def is_saved(self):
        return self._is_saved

    def save(self):
        """Сохранение — переопределяется потомками через _before_save и _after_save."""
        self._before_save()
        self._is_saved = True
        print(f"[BaseModel] Запись #{self.__id} сохранена")
        self._after_save()

    def _before_save(self):
        """Хук: выполняется перед сохранением. Переопределяется в потомках."""
        pass

    def _after_save(self):
        """Хук: выполняется после сохранения. Переопределяется в потомках."""
        pass

    def __repr__(self):
        return f"{self.__class__.__name__}(id={self.__id})"


class UserModel(BaseModel):
    """Модель пользователя."""

    def __init__(self, username, email):
        super().__init__()   # инициализирует __id и _is_saved
        self.username = username
        self.email = email

    def _before_save(self):
        """Валидируем данные перед сохранением."""
        if not self.email or "@" not in self.email:
            raise ValueError(f"Некорректный email: {self.email!r}")
        print(f"[UserModel] Валидация пройдена для {self.username}")

    def _after_save(self):
        """Отправляем приветственное письмо после первого сохранения."""
        if self.is_saved:
            print(f"[UserModel] Приветственное письмо отправлено на {self.email}")


class PostModel(BaseModel):
    """Модель публикации."""

    def __init__(self, title, content, author_id):
        super().__init__()
        self.title = title
        self.content = content
        self.author_id = author_id

    def _before_save(self):
        if not self.title:
            raise ValueError("Публикация должна иметь заголовок")
        if len(self.content) < 10:
            raise ValueError("Публикация слишком короткая")
        print(f"[PostModel] Публикация '{self.title}' готова к сохранению")
```

Демонстрация:

```python
user1 = UserModel("alice", "alice@example.com")
user2 = UserModel("bob", "bob@example.com")
post = PostModel("Python ООП", "Объектно-ориентированное программирование в Python...", author_id=1)

print(user1.id)   # 1
print(user2.id)   # 2
print(post.id)    # 3

# id нельзя изменить
try:
    user1.id = 99   # AttributeError: can't set attribute
except AttributeError as e:
    print(e)

# Сохранение через шаблонный метод
user1.save()
# [UserModel] Валидация пройдена для alice
# [BaseModel] Запись #1 сохранена
# [UserModel] Приветственное письмо отправлено на alice@example.com

post.save()
# [PostModel] Публикация 'Python ООП' готова к сохранению
# [BaseModel] Запись #3 сохранена

# Смотрим атрибуты объекта
print(list(user1.__dict__.keys()))
# ['_BaseModel__id', '_is_saved', 'username', 'email']
#   ^^^^^^^^^^^^^^^ — приватный id с name mangling
```

---

## Неочевидные моменты и типичные ошибки

**Двойное подчёркивание с обеих сторон — это не приватный атрибут.** `__name__` (dunder-атрибуты) — это специальные атрибуты Python, к ним name mangling не применяется:

```python
class MyClass:
    def __init__(self):
        self.__private = 1      # name mangling применяется: _MyClass__private
        self.__dunder__ = 2    # name mangling НЕ применяется: __dunder__

obj = MyClass()
print(obj.__dict__)
# {'_MyClass__private': 1, '__dunder__': 2}
```

Это важно знать, чтобы не путать приватные атрибуты с магическими методами и атрибутами Python.

**Name mangling применяется только к именам с 2+ подчёркиваниями в начале и 0–1 в конце.** Одно подчёркивание в начале — не приватный, не обрабатывается. Два подчёркивания в начале и два в конце — dunder, не обрабатывается:

```python
class Demo:
    def __init__(self):
        self._one = 1          # одно подчёркивание — защищённый, нет mangling
        self.__two = 2         # два подчёркивания — name mangling → _Demo__two
        self.__three__ = 3     # dunder — нет name mangling
        self.___four = 4       # три подчёркивания — name mangling → _Demo___four (!)

print(Demo().__dict__)
# {'_one': 1, '_Demo__two': 2, '__three__': 3, '_Demo___four': 4}
```

**Name mangling защищает от коллизий при множественном наследовании.** Именно для этого он был создан. Рассмотрим пример без него (гипотетически):

```python
class A:
    def __init__(self):
        self.__data = "данные A"   # _A__data

class B:
    def __init__(self):
        self.__data = "данные B"   # _B__data

class C(A, B):
    def __init__(self):
        A.__init__(self)
        B.__init__(self)

c = C()
print(c.__dict__)
# {'_A__data': 'данные A', '_B__data': 'данные B'}
# Оба атрибута сохранены без конфликта — благодаря name mangling!
```

Без name mangling второй `__init__` перезаписал бы `__data` первого, и данные класса `A` были бы потеряны.

---

## Итоги урока

Три уровня доступа ведут себя при наследовании принципиально по-разному.

Публичные атрибуты и методы наследуются полностью — дочерний класс может читать, изменять и переопределять их без ограничений.

Защищённые атрибуты (`_name`) технически доступны в дочерних классах и образуют «внутренний API» для потомков. Это соглашение: потомки могут работать с ними, внешний код — нет. Защищённые методы являются точками расширения (паттерн Template Method).

Приватные атрибуты (`__name`) обрабатываются механизмом name mangling: `__attr` в классе `Foo` становится `_Foo__attr`. Это означает, что дочерний класс не может обратиться к приватному атрибуту родителя через `self.__attr` — он случайно создаст новый атрибут `_ChildClass__attr`. Правильный способ работать с данными, хранящимися в приватных атрибутах — через публичный интерфейс или `@property`.

Name mangling защищает от коллизий имён при множественном наследовании: каждый класс имеет свою «приватную» область.

В следующем уроке мы рассмотрим полиморфизм — механизм, который позволяет разным объектам реагировать на одни и те же вызовы по-разному, и разберём, как Python реализует его через duck typing.

---

## Вопросы

1. Чем технически отличается доступ к защищённому атрибуту (`_attr`) от публичного в Python? Что означает одно подчёркивание?
2. Что такое name mangling? Во что превращается атрибут `__secret` в классе `MyClass`?
3. Почему дочерний класс не может обратиться к приватному атрибуту родителя через `self.__attr`? Что происходит при такой попытке?
4. Для чего был создан механизм name mangling? Только ли для защиты от внешнего доступа?
5. Что такое паттерн Template Method и как защищённые методы участвуют в его реализации?
6. Применяется ли name mangling к dunder-атрибутам (`__name__`)? Почему?
7. При переопределении `@property` в дочернем классе — нужно ли заново определять сеттер? Что произойдёт, если определить только геттер?
8. Почему в примере с `BaseModel` идентификатор `__id` сделан приватным, а не защищённым? Какую проблему это решает?

---

## Задачи

### Задача 1. 

Класс `BankAccount` и `SavingsAccount`

Создайте класс `BankAccount` (банковский счёт) с приватным атрибутом `__balance` (баланс) и защищёнными `_owner` (владелец, строка) и `_transaction_history` (история транзакций, список). 

Реализуйте публичные методы: `deposit(amount)` (пополнение — увеличивает `__balance` и добавляет запись в историю), `withdraw(amount)` (снятие — если `amount > __balance`, выбрасывать `ValueError`), `get_balance()` (возвращает текущий баланс), `get_history()` (возвращает копию истории). 

Создайте дочерний класс `SavingsAccount` (сберегательный счёт), который принимает дополнительно `interest_rate` (процентная ставка, число). 

Добавьте метод `apply_interest()` — начисляет проценты на баланс, используя `deposit()` родителя. 

Переопределите `withdraw()` — добавьте ограничение: снятие не более 3 раз в месяц (считайте через `_transaction_history`). 

Дочерний класс не должен иметь прямого доступа к `__balance` — только через методы родителя.

**Пример использования**:

```python
acc = BankAccount("Alice")
acc.deposit(1000)
acc.withdraw(300)
print(acc.get_balance())   # 700
print(acc.get_history())   # [{'type': 'deposit', ...}, {'type': 'withdraw', ...}]

savings = SavingsAccount("Bob", interest_rate=0.05)
savings.deposit(5000)
savings.apply_interest()
print(savings.get_balance())   # 5250.0

# Ограничение на снятие
savings.withdraw(100)
savings.withdraw(100)
savings.withdraw(100)
try:
    savings.withdraw(100)   # 4-е снятие — ошибка
except ValueError as e:
    print(e)   # Превышен лимит снятий в этом месяце
```

---

### Задача 2. 

Класс `Animal` с паттерном **Template Method**

Создайте базовый класс `Animal` с публичными атрибутами `name` и `age`, защищённым `_sound` (строка, по умолчанию `"..."`) и защищёнными методами `_prepare_to_speak()` и `_after_speak()`. 

Реализуйте публичный метод `speak()` как шаблонный: он вызывает `_prepare_to_speak()`, выводит звук, затем вызывает `_after_speak()`. 

Создайте дочерние классы:
- `Dog(Animal)`: `_sound = "Гав"`, переопределяет `_prepare_to_speak()` (выводит `"[Dog] виляет хвостом"`) и `_after_speak()` (выводит `"[Dog] смотрит на хозяина"`).
- `Cat(Animal)`: `_sound = "Мяу"`, переопределяет только `_after_speak()` (выводит `"[Cat] отворачивается"`).
- `Parrot(Animal)`: принимает дополнительно `phrases` (список фраз). Переопределяет `_sound` как `None` и переопределяет `speak()` полностью — говорит случайную фразу из списка, при каждом вызове.

**Пример использования**:

```python
dog = Dog("Rex", 3)
cat = Cat("Whiskers", 5)
parrot = Parrot("Kesha", 2, phrases=["Привет!", "Хочу есть", "Кеша хороший"])

dog.speak()
# [Dog] виляет хвостом
# Rex говорит: Гав!
# [Dog] смотрит на хозяина

cat.speak()
# Whiskers говорит: Мяу!
# [Cat] отворачивается

parrot.speak()
# Kesha говорит: Хочу есть  (случайная фраза)
```

---

### Задача 3. 

Иерархия конфигураций с `@property`

Создайте класс `AppConfig` с приватными атрибутами `__host` и `__port`. Реализуйте `@property` для `host` (только геттер — хост нельзя менять после создания) и для `port` (геттер + сеттер с проверкой: порт должен быть целым числом от 1 до 65535). Добавьте `@property` `connection_string`, возвращающий `"host:port"`.

Создайте дочерний класс `DatabaseConfig(AppConfig)`, который принимает дополнительно `database_name` и `username`. 

Добавьте новые `@property`: `database_name` (только геттер — приватный `__db_name`) и `username` (геттер + сеттер, имя не должно содержать пробелов). 

Переопределите `connection_string`, добавив к строке родителя `"/database_name"`. Используйте `super().connection_string` для получения базовой части.

**Пример использования**:

```python
cfg = AppConfig("localhost", 8080)
print(cfg.host)              # localhost
print(cfg.port)              # 8080
print(cfg.connection_string) # localhost:8080

cfg.port = 9090
print(cfg.port)              # 9090

try:
    cfg.port = 99999          # ValueError
except ValueError as e:
    print(e)

db = DatabaseConfig("db.example.com", 5432, "mydb", "admin")
print(db.connection_string)  # db.example.com:5432/mydb

db.username = "superadmin"
print(db.username)           # superadmin

try:
    db.username = "bad user"  # ValueError — пробел
except ValueError as e:
    print(e)
```

---

### Задача 4. 

Иерархия обработчиков запросов с инкапсуляцией

Создайте класс `RequestHandler` с приватным атрибутом `__request_count` (счётчик обработанных запросов, начинается с 0) и защищённым `_allowed_methods` (список допустимых HTTP-методов, по умолчанию `["GET"]`). 

Реализуйте:
- публичный метод `handle(method, path)`, который проверяет допустимость метода через `_is_allowed(method)`, при успехе вызывает `_process(method, path)` и увеличивает счётчик, при неуспехе возвращает `{"status": 405, "error": "Method Not Allowed"}`.
- защищённый метод `_is_allowed(method)` — проверяет метод против `_allowed_methods`.
- защищённый метод `_process(method, path)` — базовая реализация возвращает `{"status": 200, "path": path}`.
- `@property` `request_count` — только геттер, возвращает `__request_count`.

Создайте `APIHandler(RequestHandler)` с `_allowed_methods = ["GET", "POST", "PUT", "DELETE"]`. 

Переопределите `_process()` — добавляет в ответ поле `"api": True`. 

Добавьте защищённый `_rate_limit = 100` и переопределите `handle()`: если `request_count >= _rate_limit`, возвращать `{"status": 429, "error": "Too Many Requests"}` без вызова родителя.

**Пример использования**:

```python
handler = RequestHandler()
print(handler.handle("GET", "/index"))    # {'status': 200, 'path': '/index'}
print(handler.handle("POST", "/submit"))  # {'status': 405, 'error': 'Method Not Allowed'}
print(handler.request_count)             # 1 — только GET прошёл

api = APIHandler()
print(api.handle("POST", "/api/users"))  # {'status': 200, 'path': '/api/users', 'api': True}
print(api.handle("PATCH", "/api/x"))    # {'status': 405, ...}
print(api.request_count)               # 1
```

---

### Задача 5. 

Класс `EncryptedStorage`

Создайте класс `EncryptedStorage`, имитирующий защищённое хранилище данных. Данные хранятся в приватном словаре `__data`. Ключи шифруются при хранении через приватный метод `__encrypt_key(key)` (упрощённо: `"enc_" + key.upper()`), при чтении расшифровываются через `__decrypt_key(encrypted)`. 

Реализуйте публичные методы `store(key, value)`, `retrieve(key)` (возвращает значение или `None`), `remove(key)`, `keys()` (возвращает расшифрованные ключи). 

Создайте `TimestampedStorage(EncryptedStorage)`, который при каждом `store()` дополнительно сохраняет время записи. Для этого используйте только публичный интерфейс родителя — не обращайтесь к `__data` напрямую. 

Добавьте метод `get_with_timestamp(key)`, возвращающий кортеж `(value, timestamp)`.

Подсказка: для хранения времени `TimestampedStorage` может использовать отдельный словарь `self._timestamps`, а временные метки — хранить вместе с обычными ключами через специальное соглашение (например, ключ `_ts_key`).

**Пример использования**:

```python
storage = EncryptedStorage()
storage.store("username", "alice")
storage.store("api_key", "secret123")

print(storage.retrieve("username"))   # alice
print(storage.keys())                 # ['username', 'api_key'] (расшифрованные)

# Прямой доступ к __data невозможен
try:
    print(storage.__data)
except AttributeError:
    print("Прямой доступ запрещён")

ts = TimestampedStorage()
ts.store("token", "abc123")
val, timestamp = ts.get_with_timestamp("token")
print(val)       # abc123
print(timestamp) # datetime объект
```

---

### Задача 6. 

Иерархия ORM-моделей

Создайте базовый класс `ORMModel`, имитирующий базовую ORM-модель. Приватный `__fields = {}` хранит словарь `{имя_поля: значение}`. Публичный классовый атрибут `table_name = ""` задаётся в дочерних классах. Защищённый метод `_define_field(name, default=None)` добавляет поле с дефолтом в `__fields`. 

Реализуйте `__getattr__` для чтения полей из `__fields` и `__setattr__` для записи в `__fields`, если поле там есть (иначе — стандартное поведение). 

Публичный метод `to_dict()` возвращает копию `__fields`. 

Метод `save()` выводит `"INSERT INTO table_name: fields"`.

Создайте `UserORMModel(ORMModel)` с `table_name = "users"`. В `__init__` определите поля через `_define_field`: `username` (дефолт `""`), `email` (дефолт `""`), `is_active` (дефолт `True`).

**Пример использования**:

```python
user = UserORMModel()
user.username = "alice"
user.email = "alice@example.com"

print(user.username)   # alice
print(user.to_dict())  # {'username': 'alice', 'email': 'alice@example.com', 'is_active': True}
user.save()            # INSERT INTO users: {'username': 'alice', ...}

try:
    user.unknown_field = "value"   # создаётся обычный атрибут (не в __fields)
except AttributeError:
    pass
print(user.unknown_field)   # value — обычный атрибут
```

---

[Предыдущий урок](lesson20.md) | [Следующий урок](lesson22.md)