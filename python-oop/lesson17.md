# Урок 17. Сравнения, сортировка и хеширование: `__eq__`, `__lt__`, `@total_ordering`, `__hash__`

---

## Как Python сравнивает объекты по умолчанию

Когда вы пишете `a == b`, Python не сравнивает содержимое объектов автоматически. Без явной реализации `__eq__` Python сравнивает идентичность объектов — то есть проверяет, является ли `a` тем же самым объектом в памяти, что и `b`, а не просто объектом с теми же данными.

```python
class User:
    def __init__(self, username, email):
        self.username = username
        self.email = email


alice1 = User("alice", "alice@example.com")
alice2 = User("alice", "alice@example.com")

print(alice1 == alice2)    # False — разные объекты в памяти
print(alice1 is alice2)    # False — это не один и тот же объект
print(alice1 == alice1)    # True  — объект равен самому себе
```

Два объекта `User` с одинаковыми данными не считаются равными, потому что они занимают разные адреса в памяти. Это поведение по умолчанию наследуется от базового класса `object`, в котором `__eq__` реализован именно как проверка идентичности.

В большинстве прикладных задач такое поведение неправильное. Если `alice1` и `alice2` представляют одного и того же пользователя в базе данных, они должны считаться равными — и именно это мы реализуем через `__eq__`.

---

## Метод `__eq__`: равенство объектов

Метод `__eq__` вызывается при операторе `==`. Он принимает два аргумента: `self` и `other` (второй операнд), и должен вернуть `True`, `False` или специальное значение `NotImplemented`.

```python
class User:
    def __init__(self, id, username, email):
        self.id = id
        self.username = username
        self.email = email

    def __eq__(self, other):
        # Сначала проверяем, что other — это объект того же типа.
        # Если нет — возвращаем NotImplemented, а не False.
        if not isinstance(other, User):
            return NotImplemented
        # Равенство определяем по полю id — уникальному идентификатору в БД
        return self.id == other.id

    def __repr__(self):
        return f"User(id={self.id}, username={self.username!r})"


alice1 = User(1, "alice", "alice@example.com")
alice2 = User(1, "alice", "alice_new@example.com")   # другой email, но тот же id
bob = User(2, "bob", "bob@example.com")

print(alice1 == alice2)   # True  — одинаковый id
print(alice1 == bob)      # False — разные id
print(alice1 == "alice")  # False — NotImplemented → Python попробует другую сторону
```

Возврат `NotImplemented` — важная деталь. Когда `__eq__` встречает объект несовместимого типа, правильно вернуть `NotImplemented`, а не `False`. Это сигнал Python: «я не знаю, как сравнивать с этим типом, попробуй спросить другую сторону». Python тогда вызовет `other.__eq__(self)`. Если и это вернёт `NotImplemented` — результатом станет `False`.

Если вернуть `False` вместо `NotImplemented`, вы отключите этот механизм рефлексии, и некоторые корректные сравнения перестанут работать.

---

## Методы сравнения: полный список

Python поддерживает шесть операторов сравнения, каждый из которых соответствует магическому методу:

| Оператор | Метод | Описание |
|---|---|---|
| `==` | `__eq__` | равно |
| `!=` | `__ne__` | не равно |
| `<`  | `__lt__` | меньше |
| `<=` | `__le__` | меньше или равно |
| `>`  | `__gt__` | больше |
| `>=` | `__ge__` | больше или равно |

Хорошая новость: в Python 3 вам не нужно реализовывать все шесть. Во-первых, `__ne__` автоматически является отрицанием `__eq__` — если вы определили `__eq__`, Python сам реализует `!=` как `not __eq__`. Во-вторых, `>` является зеркальным отражением `<`: если Python не может выполнить `a > b` через `a.__gt__(b)`, он попробует `b.__lt__(a)`. Это называется рефлексией операторов.

Но реализовывать `__lt__`, `__le__`, `__gt__`, `__ge__` вручную всё равно утомительно, если они связаны одной логикой. Именно для этого существует `@total_ordering`.

---

## `@functools.total_ordering`: полный набор из двух методов

Декоратор `@total_ordering` из модуля `functools` позволяет определить только `__eq__` и один из методов упорядочивания (`__lt__`, `__le__`, `__gt__` или `__ge__`), а остальные пять Python сгенерирует автоматически.

```python
from functools import total_ordering


@total_ordering
class Version:
    """
    Версия программного обеспечения в формате major.minor.patch.
    Поддерживает все операторы сравнения через @total_ordering.
    """

    def __init__(self, major, minor=0, patch=0):
        self.major = major
        self.minor = minor
        self.patch = patch

    def __eq__(self, other):
        if not isinstance(other, Version):
            return NotImplemented
        return (self.major, self.minor, self.patch) == (other.major, other.minor, other.patch)

    def __lt__(self, other):
        if not isinstance(other, Version):
            return NotImplemented
        # Сравниваем кортежи — Python сравнивает их поэлементно:
        # сначала major, при равенстве — minor, при равенстве — patch
        return (self.major, self.minor, self.patch) < (other.major, other.minor, other.patch)

    def __repr__(self):
        return f"Version({self.major}.{self.minor}.{self.patch})"

    def __str__(self):
        return f"{self.major}.{self.minor}.{self.patch}"
```

Проверим, что все шесть операторов работают — хотя мы определили только два:

```python
v1 = Version(1, 0, 0)
v2 = Version(1, 2, 0)
v3 = Version(2, 0, 0)
v4 = Version(1, 0, 0)

print(v1 == v4)    # True
print(v1 != v2)    # True  — автоматически из __eq__
print(v1 < v2)     # True  — определён явно
print(v2 > v1)     # True  — сгенерирован из __lt__
print(v1 <= v4)    # True  — сгенерирован из __lt__ и __eq__
print(v3 >= v2)    # True  — сгенерирован из __lt__ и __eq__
```

Сравнение кортежей `(major, minor, patch)` — стандартный приём в Python. Кортежи сравниваются поэлементно: сначала первый элемент, при равенстве — второй, и так далее. Это позволяет реализовать многоуровневое сравнение одной строкой.

**Ограничение `@total_ordering`:** декоратор генерирует методы через вызов `__lt__` и `__eq__`, что добавляет небольшой накладной расход при каждом сравнении. Для горячих путей кода (например, сортировка миллионов объектов) иногда оправдана ручная реализация всех шести методов. В большинстве веб-приложений разница незначительна.

---

## Сортировка через `__lt__`

Как только у класса определён `__lt__`, его объекты можно сортировать с помощью `sorted()` и `list.sort()` — без дополнительных параметров:

```python
versions = [Version(2, 0, 0), Version(1, 0, 0), Version(1, 2, 0), Version(1, 0, 5)]

sorted_versions = sorted(versions)
for v in sorted_versions:
    print(v)
# 1.0.0
# 1.0.5
# 1.2.0
# 2.0.0

# Обратная сортировка
for v in sorted(versions, reverse=True):
    print(v)
# 2.0.0
# 1.2.0
# 1.0.5
# 1.0.0
```

Применим это к более реальному примеру. В веб-приложении часто нужно сортировать задачи по приоритету:

```python
@total_ordering
class Task:
    """
    Задача в системе управления проектами.
    Приоритет: 1 = критический, 2 = высокий, 3 = средний, 4 = низкий.
    При равном приоритете сортируем по дате создания.
    """

    def __init__(self, title, priority, created_at):
        self.title = title
        self.priority = priority       # меньше число = выше приоритет
        self.created_at = created_at   # строка ISO-8601 для простоты

    def __eq__(self, other):
        if not isinstance(other, Task):
            return NotImplemented
        return self.priority == other.priority and self.created_at == other.created_at

    def __lt__(self, other):
        if not isinstance(other, Task):
            return NotImplemented
        # Сначала по приоритету, затем по дате
        return (self.priority, self.created_at) < (other.priority, other.created_at)

    def __repr__(self):
        return f"Task({self.title!r}, priority={self.priority})"


tasks = [
    Task("Исправить баг авторизации", priority=1, created_at="2024-01-15"),
    Task("Обновить документацию",    priority=4, created_at="2024-01-10"),
    Task("Добавить пагинацию",       priority=2, created_at="2024-01-12"),
    Task("Исправить опечатку",       priority=4, created_at="2024-01-08"),
    Task("Оптимизировать запросы",   priority=2, created_at="2024-01-11"),
]

for task in sorted(tasks):
    print(task)
# Task('Исправить баг авторизации', priority=1)
# Task('Оптимизировать запросы', priority=2)
# Task('Добавить пагинацию', priority=2)
# Task('Исправить опечатку', priority=4)
# Task('Обновить документацию', priority=4)
```

Задачи отсортированы сначала по приоритету, затем по дате: задачи с одинаковым приоритетом `2` упорядочены так, что более ранняя (`2024-01-11`) идёт первой. Задачи с приоритетом `4` тоже упорядочены по дате (`2024-01-08` раньше `2024-01-10`).

---

## Связь `__eq__` и `__hash__`: главное правило

Здесь мы подходим к самому важному и одновременно самому неочевидному моменту темы. Между `__eq__` и `__hash__` существует жёсткий контракт:

> **Если два объекта равны по `__eq__`, они обязаны иметь одинаковый `__hash__`.**

Обратное необязательно: два объекта с одинаковым хешем не обязаны быть равными (это называется коллизией).

Почему это правило существует? Чтобы понять это, нужно разобраться, как устроены словари и множества в Python.

Словарь (`dict`) хранит пары «ключ — значение» в хеш-таблице. Когда вы делаете `d[key]`, Python не перебирает все ключи — это было бы слишком медленно. Вместо этого он вычисляет `hash(key)`, получает «корзину» (bucket) в таблице и ищет ключ только там. Поиск выполняется за O(1).

Если два объекта равны (`a == b`), но имеют разные хеши (`hash(a) != hash(b)`), они попадут в разные корзины. Словарь попытается найти ключ `b` в корзине для хеша `b` — и не найдёт `a`, даже если `a == b`. Словарь окажется сломан.

Именно поэтому Python применяет жёсткую меру: как только вы переопределяете `__eq__` в классе, Python автоматически устанавливает `__hash__ = None`. Это делает объекты нехешируемыми — попытка использовать их как ключ словаря или элемент множества вызовет `TypeError`:

```python
class BrokenUser:
    def __init__(self, id):
        self.id = id

    def __eq__(self, other):
        if not isinstance(other, BrokenUser):
            return NotImplemented
        return self.id == other.id
    # __hash__ не определён — Python установил __hash__ = None


u = BrokenUser(1)
try:
    d = {u: "alice"}
except TypeError as e:
    print(e)   # unhashable type: 'BrokenUser'

try:
    s = {u}
except TypeError as e:
    print(e)   # unhashable type: 'BrokenUser'
```

Чтобы объект был одновременно сравниваемым по значению и хешируемым, необходимо явно реализовать оба метода.

---

## Метод `__hash__`: что такое хеш и как его реализовать

Хеш — это целое число, вычисляемое из данных объекта. Встроенная функция `hash()` возвращает его для любого хешируемого объекта. Хеш-функция должна удовлетворять двум требованиям:

1. **Детерминированность**: для одного и того же объекта `hash()` всегда возвращает одно и то же число на протяжении всего времени жизни программы.
2. **Согласованность с `__eq__`**: если `a == b`, то `hash(a) == hash(b)`.

**Желательное (но не обязательное) свойство**: разные объекты должны давать разные хеши. Коллизии допустимы, но они снижают производительность словарей и множеств.

Стандартный способ реализовать `__hash__` — вычислить хеш кортежа из тех же атрибутов, которые используются в `__eq__`. Встроенная функция `hash()` корректно работает с кортежами:

```python
class User:
    def __init__(self, id, username, email):
        self.id = id
        self.username = username
        self.email = email

    def __eq__(self, other):
        if not isinstance(other, User):
            return NotImplemented
        return self.id == other.id   # равенство по id

    def __hash__(self):
        # Хешируем тот же атрибут, что используется в __eq__
        # Если __eq__ сравнивает по id — __hash__ тоже должен использовать id
        return hash(self.id)

    def __repr__(self):
        return f"User(id={self.id}, username={self.username!r})"
```

Проверим, что объекты корректно работают в словарях и множествах:

```python
alice1 = User(1, "alice", "alice@example.com")
alice2 = User(1, "alice", "alice_new@example.com")   # другой email, тот же id
bob    = User(2, "bob",   "bob@example.com")

# Хеш одинаков для объектов с одинаковым id
print(hash(alice1) == hash(alice2))   # True — обязательное требование

# Множество автоматически дедуплицирует по __eq__ и __hash__
users = {alice1, alice2, bob}
print(len(users))   # 2 — alice1 и alice2 считаются одним объектом

# Использование как ключи словаря
permissions = {
    alice1: ["read", "write"],
    bob:    ["read"],
}

# Доступ по любому из равных объектов работает корректно
print(permissions[alice2])   # ['read', 'write'] — alice2 == alice1, хеши совпадают
```

---

## Если несколько атрибутов: хешируем кортеж

Когда равенство определяется по нескольким атрибутам, `__hash__` должен использовать все те же атрибуты:

```python
@total_ordering
class Permission:
    """
    Разрешение на выполнение действия над ресурсом.
    Два разрешения равны, если совпадают и ресурс, и действие.
    """

    def __init__(self, resource, action):
        self.resource = resource   # например, "users", "orders"
        self.action = action       # например, "read", "write", "delete"

    def __eq__(self, other):
        if not isinstance(other, Permission):
            return NotImplemented
        return self.resource == other.resource and self.action == other.action

    def __lt__(self, other):
        if not isinstance(other, Permission):
            return NotImplemented
        return (self.resource, self.action) < (other.resource, other.action)

    def __hash__(self):
        # Хешируем кортеж из тех же атрибутов, что используются в __eq__
        # hash(tuple) — стандартный паттерн для нескольких атрибутов
        return hash((self.resource, self.action))

    def __repr__(self):
        return f"Permission({self.resource!r}, {self.action!r})"

    def __str__(self):
        return f"{self.resource}:{self.action}"
```

Демонстрация дедупликации и сортировки:

```python
# Набор разрешений с дублями
raw_permissions = [
    Permission("users", "read"),
    Permission("orders", "write"),
    Permission("users", "read"),    # дубль
    Permission("users", "delete"),
    Permission("orders", "read"),
    Permission("orders", "write"),  # дубль
]

# Дедупликация через set — работает благодаря __eq__ и __hash__
unique = set(raw_permissions)
print(f"Было {len(raw_permissions)}, после дедупликации: {len(unique)}")
# Было 6, после дедупликации: 4

# Отсортированный список разрешений для отображения в интерфейсе
for perm in sorted(unique):
    print(perm)
# orders:read
# orders:write
# users:delete
# users:read

# Использование как ключей кеша
cache = {}
p1 = Permission("users", "read")
p2 = Permission("users", "read")   # другой объект, но тот же хеш и равны

cache[p1] = "cached_result"
print(cache[p2])   # cached_result — найден по p2, хотя записывали по p1
```

---

## Изменяемые объекты и хешируемость

Теперь разберём, почему списки, словари и другие изменяемые типы не хешируемы.

```python
lst = [1, 2, 3]
print(hash(lst))   # TypeError: unhashable type: 'list'
```

Проблема в том, что содержимое списка можно изменить после создания. Представим такой сценарий:

```python
# Гипотетический код (не работает в реальности)
d = {}
key = [1, 2, 3]
d[key] = "value"

key.append(4)   # теперь key == [1, 2, 3, 4]
# Хеш изменился! Python уже не может найти ключ в той же корзине.
# d[key] не найдёт "value" — словарь сломан.
```

Именно поэтому Python запрещает хешировать изменяемые объекты: это предотвращает создание несогласованных структур данных.

Если вы создаёте собственный класс с изменяемыми атрибутами, которые участвуют в `__eq__`, вы должны явно запретить хеширование:

```python
class MutableConfig:
    def __init__(self, settings):
        self.settings = settings   # словарь — изменяемый

    def __eq__(self, other):
        if not isinstance(other, MutableConfig):
            return NotImplemented
        return self.settings == other.settings

    # Явно запрещаем хеширование — объект изменяемый
    __hash__ = None


cfg = MutableConfig({"debug": True})
try:
    {cfg}
except TypeError as e:
    print(e)   # unhashable type: 'MutableConfig'
```

Присваивание `__hash__ = None` — это именно то, что Python делает автоматически при переопределении `__eq__`. Явная запись делает намерение понятным для тех, кто читает код.

---

## Практический пример: класс `APIVersion`

Объединим всё изученное в полноценном примере из веб-разработки. Версия API — это объект, который нужно сравнивать, сортировать и использовать как ключ кеша.

```python
from functools import total_ordering


@total_ordering
class APIVersion:
    """
    Версия API в формате major.minor.

    Применение:
    - Сравнение для определения совместимости клиента
    - Сортировка для вывода доступных версий
    - Использование как ключ кеша ответов по версии API
    """

    SUPPORTED_VERSIONS = {"v1", "v2", "v3"}

    def __init__(self, major, minor=0):
        if not isinstance(major, int) or major < 1:
            raise ValueError(f"major должен быть положительным целым числом")
        self.major = major
        self.minor = minor

    @classmethod
    def from_string(cls, version_str):
        """Создаёт объект из строки вида 'v2' или 'v2.1'."""
        clean = version_str.lstrip("v")
        parts = clean.split(".")
        major = int(parts[0])
        minor = int(parts[1]) if len(parts) > 1 else 0
        return cls(major, minor)

    def is_compatible_with(self, other):
        """Версии совместимы, если major одинаковый."""
        return self.major == other.major

    def __eq__(self, other):
        if not isinstance(other, APIVersion):
            return NotImplemented
        return self.major == other.major and self.minor == other.minor

    def __lt__(self, other):
        if not isinstance(other, APIVersion):
            return NotImplemented
        return (self.major, self.minor) < (other.major, other.minor)

    def __hash__(self):
        return hash((self.major, self.minor))

    def __str__(self):
        if self.minor == 0:
            return f"v{self.major}"
        return f"v{self.major}.{self.minor}"

    def __repr__(self):
        return f"APIVersion({self.major}, {self.minor})"
```

Демонстрация всех возможностей:

```python
v1   = APIVersion(1, 0)
v2   = APIVersion(2, 0)
v2_1 = APIVersion(2, 1)
v3   = APIVersion(3, 0)

# Сравнение — все шесть операторов работают через @total_ordering
print(v1 < v2)     # True
print(v2 < v2_1)   # True
print(v3 > v2_1)   # True
print(v2 == APIVersion.from_string("v2"))   # True

# Сортировка доступных версий для отображения клиенту
available = [v3, v1, v2_1, v2]
print("Доступные версии:", [str(v) for v in sorted(available)])
# Доступные версии: ['v1', 'v2', 'v2.1', 'v3']

# Последняя версия
latest = max(available)
print(f"Последняя версия: {latest}")   # v3

# Совместимость
client_version = APIVersion.from_string("v2.3")
print(f"Совместима с v2: {client_version.is_compatible_with(v2)}")   # True
print(f"Совместима с v3: {client_version.is_compatible_with(v3)}")   # False

# Кеш ответов по версии API
response_cache = {}
response_cache[v2] = {"data": "cached response for v2"}

# Запрос с другим объектом той же версии попадает в кеш
request_version = APIVersion.from_string("v2")
print(response_cache[request_version])   # {'data': 'cached response for v2'}

# Дедупликация — узнаём уникальные версии из запросов
request_versions = [
    APIVersion.from_string("v2"),
    APIVersion.from_string("v1"),
    APIVersion.from_string("v2"),
    APIVersion.from_string("v3"),
    APIVersion.from_string("v1"),
]
unique_versions = set(request_versions)
print(f"Уникальных версий в запросах: {len(unique_versions)}")   # 3
print(sorted(unique_versions))
# [APIVersion(1, 0), APIVersion(2, 0), APIVersion(3, 0)]
```

---

## Неочевидные моменты и возможные ошибки

**Рефлексия операторов и `NotImplemented`.**

Когда Python вычисляет `a == b`, он сначала вызывает `a.__eq__(b)`. Если тот вернул `NotImplemented` — Python пробует `b.__eq__(a)`. Если и это `NotImplemented` — результат `False`. Это называется рефлексией. Именно поэтому правильно возвращать `NotImplemented` при несовместимом типе — а не `False` и не выбрасывать исключение.

```python
class Celsius:
    def __init__(self, value):
        self.value = value

    def __eq__(self, other):
        if isinstance(other, Celsius):
            return self.value == other.value
        if isinstance(other, (int, float)):
            return self.value == other
        return NotImplemented   # не False, а NotImplemented

    def __hash__(self):
        return hash(self.value)


c = Celsius(100)
print(c == 100)     # True  — Celsius.__eq__(100) → True
print(100 == c)     # True  — int.__eq__(c) → NotImplemented → Celsius.__eq__(100) → True
print(c == "hot")   # False — NotImplemented с обеих сторон → False
```

**`__hash__` не должен использовать изменяемые атрибуты.**

Если атрибут может измениться — он не должен участвовать в `__hash__`. Иначе объект, уже добавленный в словарь или множество, «потеряется» после изменения:

```python
class BrokenKey:
    def __init__(self, value):
        self.value = value

    def __eq__(self, other):
        return self.value == other.value

    def __hash__(self):
        return hash(self.value)   # ОПАСНО: value изменяемый


key = BrokenKey(10)
d = {key: "original"}
key.value = 99   # меняем атрибут, участвующий в хеше

print(d.get(key))      # None — объект потерян: хеш изменился, Python ищет в другой корзине
print(d.get(BrokenKey(10)))  # None — оригинальный ключ недоступен
```

Решение: хешировать только иммутабельные данные, или не давать изменять атрибуты после создания (через `@property` только для чтения).

**`hash()` в Python недетерминирован между запусками программы.**

По соображениям безопасности Python по умолчанию рандомизирует хеши строк и байтов при каждом запуске программы (hash randomization). Это означает, что `hash("hello")` даст разное число при каждом новом запуске Python. Внутри одного запуска хеши стабильны, но между запусками — нет. Поэтому хеши никогда не следует сохранять в базу данных или передавать по сети.

```python
# При одном запуске:
print(hash("hello"))   # 1234567890 (условно)
# При следующем запуске того же скрипта:
print(hash("hello"))   # 9876543210 (другое число)
```

Для стабильных хешей (например, для криптографии или идентификаторов) используйте модуль `hashlib`.

**Хеш `None` — корректен.**

```python
print(hash(None))   # 0 (всегда, None всегда хешируем)
print(None == None) # True
```

`None` является хешируемым и может использоваться как ключ словаря. Это не очевидно, поскольку интуитивно `None` ассоциируется с «отсутствием значения».

**Проблема с `@total_ordering` при наследовании.**

`@total_ordering` добавляет методы в класс напрямую. Если подкласс не переопределяет `__lt__`, он унаследует метод родителя — но через механизм `@total_ordering`, который может привести к неожиданному поведению при смешанных сравнениях. В сложных иерархиях наследования предпочтительна явная реализация всех методов.

---

## Итоги урока

Методы `__eq__` и `__hash__` образуют неразрывную пару: переопределение одного без другого приводит к неработоспособным словарям и множествам. Основное правило: если `a == b`, то `hash(a) == hash(b)`.

Полный набор операторов сравнения реализуется через `@total_ordering`: достаточно определить `__eq__` и один из методов упорядочивания — остальные четыре будут сгенерированы автоматически.

Изменяемые объекты не должны быть хешируемыми: хеш вычисляется из данных объекта, и если данные изменятся, объект потеряется в словаре или множестве. При переопределении `__eq__` Python автоматически устанавливает `__hash__ = None`.

В следующем уроке мы рассмотрим арифметические магические методы: `__add__`, `__mul__` и их коллег, которые позволяют объектам участвовать в математических выражениях.

---

## Вопросы

1. Что делает Python при сравнении `a == b`, если в классе не определён `__eq__`? Когда это поведение проблематично?
2. Почему `__eq__` должен возвращать `NotImplemented` при несовместимом типе, а не `False`?
3. Что делает `@functools.total_ordering`? Какой минимальный набор методов нужно определить?
4. Что происходит с `__hash__` при переопределении `__eq__`? Почему Python так себя ведёт?
5. Почему списки в Python не хешируемы? Что произошло бы, если бы они были хешируемыми?
6. Два объекта имеют одинаковый хеш, но не равны по `__eq__`. Нарушает ли это правила хеширования?
7. Можно ли сохранить значение `hash(obj)` в базу данных и использовать его при следующем запуске программы?
8. Объект добавлен в `set`, затем изменён атрибут, участвующий в `__hash__`. Что произойдёт при попытке найти объект в `set`?

---

## Задачи

### **Задача 1**. 

Класс `Point`

Создайте класс `Point`, описывающий точку на плоскости с координатами `x` и `y` (числа с плавающей точкой). 

Реализуйте `__eq__` — две точки равны, если обе координаты совпадают. Реализуйте `__hash__` через хеш кортежа координат. 

Реализуйте `__lt__` через расстояние от начала координат (ближайшая точка меньше) и примените `@total_ordering`. 

Добавьте метод `distance_to_origin()`, возвращающий расстояние от начала координат. 

Реализуйте `__str__` в формате `(x, y)` и `__repr__` в формате `Point(x=1.0, y=2.0)`.

**Пример использования**:

```python
p1 = Point(0.0, 3.0)
p2 = Point(4.0, 0.0)
p3 = Point(1.0, 1.0)
p4 = Point(0.0, 3.0)

print(p1 == p4)   # True
print(p1 == p2)   # False
print(p1 < p2)    # False — расстояния одинаковы (3.0 == 4.0... нет, 3.0 < 5.0)

points = [p2, p1, p3]
for p in sorted(points):
    print(p, "→", round(p.distance_to_origin(), 2))

# Использование в множестве
seen = {p1, p2, p3, p4}
print(len(seen))   # 3 — p1 и p4 одинаковы
```

---

### **Задача 2**. 

Класс `SemanticVersion`

Создайте класс `SemanticVersion` для версий в формате `major.minor.patch`. Принимает три целых числа. 

Реализуйте `__eq__` (все три компонента равны), `__lt__` (лексикографическое сравнение кортежей), `__hash__`. 

Примените `@total_ordering`. 

Добавьте метод `is_compatible(other)` — версии совместимы, если `major` одинаковый. 

Добавьте `@classmethod from_string(cls, s)`, который парсит строку вида `"1.2.3"`. 

Реализуйте `__str__` в формате `"1.2.3"` и `__repr__` в формате `SemanticVersion(1, 2, 3)`.

**Пример использования**:

```python
v = SemanticVersion.from_string("2.1.0")
print(v)   # 2.1.0

versions = [
    SemanticVersion(1, 10, 0),
    SemanticVersion(2, 0, 0),
    SemanticVersion(1, 2, 3),
    SemanticVersion(1, 2, 3),  # дубль
    SemanticVersion(1, 9, 5),
]

unique = set(versions)
print(len(unique))   # 4

for v in sorted(unique):
    print(v)
# 1.2.3 / 1.9.5 / 1.10.0 / 2.0.0

v1 = SemanticVersion(1, 5, 0)
v2 = SemanticVersion(1, 7, 2)
v3 = SemanticVersion(2, 0, 0)

print(v1.is_compatible(v2))   # True  — одинаковый major
print(v1.is_compatible(v3))   # False — разный major
```

---

### **Задача 3**. 

Класс `HttpStatus`

Создайте класс `HttpStatus`, представляющий HTTP-статус-код. Принимает `code` (целое число) и `message` (строка). 

Реализуйте `__eq__` по коду, `__hash__` по коду, `__lt__` по коду. 

Примените `@total_ordering`. 

Добавьте свойства `is_success` (2xx), `is_client_error` (4xx), `is_server_error` (5xx).

Добавьте `__bool__` — статус «истинный», если он успешный (2xx). 

Реализуйте `__str__` в формате `"200 OK"` и `__repr__` в формате `HttpStatus(200, 'OK')`.

**Пример использования**:

```python
ok           = HttpStatus(200, "OK")
created      = HttpStatus(201, "Created")
not_found    = HttpStatus(404, "Not Found")
server_error = HttpStatus(500, "Internal Server Error")

print(ok == HttpStatus(200, "OK Response"))  # True — равенство по коду

if ok:
    print("Запрос успешен")   # выполнится

print(not_found.is_client_error)   # True
print(server_error.is_server_error) # True

statuses = [server_error, ok, not_found, created]
for s in sorted(statuses):
    print(s)
# 200 OK
# 201 Created
# 404 Not Found
# 500 Internal Server Error

# Дедупликация
responses = {ok, HttpStatus(200, "OK"), not_found}
print(len(responses))   # 2
```

---

### **Задача 4**. 

Класс `IPAddress`

Создайте класс `IPAddress` для работы с IPv4-адресами. Принимает строку вида `"192.168.1.1"`, где `192` - это первый октет, `168` - второй октет и т.д.

Реализуйте `__eq__` (по всем четырём октетам), `__lt__` (числовое сравнение адресов), `__hash__`. 

Примените `@total_ordering`. 

Добавьте метод `to_int()`, возвращающий адрес как 32-битное целое число (октет1 × 2²⁴ + октет2 × 2¹⁶ + ...).

Реализуйте `__str__` в формате `"192.168.1.1"` и `__repr__` в формате `IPAddress('192.168.1.1')`.

**Пример использования**:

```python
ip1 = IPAddress("192.168.1.1")
ip2 = IPAddress("192.168.1.100")
ip3 = IPAddress("10.0.0.1")
ip4 = IPAddress("192.168.1.1")

print(ip1 == ip4)    # True
print(ip1 < ip2)     # True
print(ip3 < ip1)     # True  — 10.x.x.x < 192.x.x.x

print(ip1.to_int())  # 3232235777

# Сортировка диапазона адресов
addresses = [ip2, ip1, ip3]
for ip in sorted(addresses):
    print(ip)
# 10.0.0.1
# 192.168.1.1
# 192.168.1.100

# Дедупликация
unique = {ip1, ip2, ip3, ip4}
print(len(unique))   # 3
```

---

### **Задача 5**. 

Класс `CacheKey`

Создайте класс `CacheKey` — ключ для кеширования HTTP-ответов. Принимает `method` (строка, приводится к верхнему регистру), `path` (строка) и `version` (строка, по умолчанию `"v1"`). 

Два ключа равны, если совпадают все три поля. 

Реализуйте `__hash__` через кортеж всех трёх полей. 

Реализуйте `__lt__` для сортировки: сначала по `version`, затем по `method`, затем по `path`. 

Примените `@total_ordering`. 

Реализуйте `__str__` в формате `"GET /api/users [v1]"` и `__repr__` в формате `CacheKey(method='GET', path='/api/users', version='v1')`.

**Пример использования**:

```python
k1 = CacheKey("GET", "/api/users", "v1")
k2 = CacheKey("get", "/api/users", "v1")  # method нормализуется к верхнему регистру
k3 = CacheKey("POST", "/api/users", "v1")
k4 = CacheKey("GET", "/api/users", "v2")

print(k1 == k2)   # True — method нормализован
print(k1 == k4)   # False — разные версии

# Кеш ответов API
cache = {k1: {"users": []}, k3: {"created": True}}
print(cache[k2])   # {"users": []} — k2 == k1

# Дедупликация запросов
requests = [k1, k2, k3, k4, CacheKey("GET", "/api/users", "v2")]
unique_requests = set(requests)
print(len(unique_requests))   # 3

for key in sorted(unique_requests):
    print(key)
```

---

### **Задача 6**. 

Класс `UserRole`

Создайте класс `UserRole`, описывающий роль пользователя с уровнем доступа. Принимает `name` (строка) и `level` (целое число: 0 = гость, 1 = пользователь, 2 = модератор, 3 = администратор). 

Два объекта равны, если совпадают `name` и `level`. 

Реализуйте `__hash__`. 

Реализуйте `__lt__` по `level` (низший уровень = «меньше»). 

Примените `@total_ordering`. 

Реализуйте `__bool__` — роль «истинная», если `level > 0`. 

Реализуйте `__str__` в формате `"admin (level=3)"` и `__repr__` в формате `UserRole('admin', 3)`.

**Пример использования**:

```python
guest     = UserRole("guest",     level=0)
user      = UserRole("user",      level=1)
moderator = UserRole("moderator", level=2)
admin     = UserRole("admin",     level=3)

print(bool(guest))     # False — level=0
print(bool(user))      # True

print(user < moderator)   # True
print(admin > user)       # True

roles = [admin, guest, user, moderator]
for r in sorted(roles):
    print(r)
# guest (level=0)
# user (level=1)
# moderator (level=2)
# admin (level=3)

# Проверка прав: может ли пользователь выполнить действие
def require_level(required_role):
    def check(user_role):
        return user_role >= required_role
    return check

can_moderate = require_level(moderator)
print(can_moderate(admin))      # True
print(can_moderate(user))       # False

# Дедупликация
all_roles = [admin, UserRole("admin", 3), user, moderator]
unique = set(all_roles)
print(len(unique))   # 3
```

---

### **Задача 7**. 

Класс `Interval`

Создайте класс `Interval`, представляющий числовой отрезок `[start, end]`. Принимает `start` и `end` (числа); если `start > end` — выбрасывать `ValueError`. 

Два интервала равны, если совпадают оба конца. 

Реализуйте `__hash__`. 

Реализуйте `__lt__` — интервал «меньше», если его начало меньше; при равном начале — меньше тот, у кого меньше конец. 

Примените `@total_ordering`. 

Добавьте метод `contains(value)`, возвращающий `True`, если значение входит в отрезок. 

Добавьте метод `overlaps(other)` — перекрываются ли два отрезка. 

Реализуйте `__len__` как длину интервала (целая часть), `__bool__` — истинен, если длина > 0. 

Реализуйте `__str__` в формате `"[1, 5]"` и `__repr__` в формате `Interval(1, 5)`.

**Пример использования**:

```python
i1 = Interval(1, 5)
i2 = Interval(3, 8)
i3 = Interval(6, 10)
i4 = Interval(1, 5)

print(i1 == i4)          # True
print(i1 < i2)           # True — 1 < 3
print(i1.contains(3))    # True
print(i1.overlaps(i2))   # True  — пересекаются на [3, 5]
print(i1.overlaps(i3))   # False — не пересекаются

print(len(i1))   # 4
print(bool(Interval(5, 5)))   # False — длина 0

intervals = [i3, i1, i2, i4]
for i in sorted(set(intervals)):
    print(i)
# [1, 5]
# [3, 8]
# [6, 10]
```

---

### **Задача 8**. 

Класс `EndpointStat`

Создайте класс `EndpointStat` — статистика одного API-эндпоинта. Принимает `method` (строка, нормализуется к верхнему регистру), `path` (строка) и `request_count` (целое число, по умолчанию 0). 

Два объекта равны, если совпадают `method` и `path` (количество запросов не влияет на равенство). 

Реализуйте `__hash__` по `method` и `path`. 

Реализуйте `__lt__` по `request_count` в убывающем порядке (эндпоинт с большим числом запросов «меньше» для сортировки — чтобы `sorted()` выводил самые популярные первыми). 

Примените `@total_ordering`. 

Добавьте метод `increment(n=1)`, увеличивающий `request_count`. 

Реализуйте `__str__` в формате `"GET /api/users — 1500 запросов"` и `__repr__` в формате `EndpointStat('GET', '/api/users', 1500)`.

**Пример использования**:

```python
stats = [
    EndpointStat("GET",    "/api/users",   1500),
    EndpointStat("POST",   "/api/orders",  320),
    EndpointStat("get",    "/api/users",   200),  # дубль — нормализуется
    EndpointStat("DELETE", "/api/users",   45),
    EndpointStat("GET",    "/api/products",980),
]

# Дедупликация — дублирующиеся эндпоинты объединяются
unique = set(stats)
print(len(unique))   # 4 — GET /api/users появляется дважды, но это один эндпоинт

# Сортировка: самые популярные первыми
for s in sorted(unique):
    print(s)
# GET /api/users — 1500 запросов (или 200, зависит от реализации set)
# GET /api/products — 980 запросов
# POST /api/orders — 320 запросов
# DELETE /api/users — 45 запросов
```

---

[Предыдущий урок](lesson16.md) | [Следующий урок](lesson18.md)