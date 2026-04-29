# Урок 25. Множественное наследование и алгоритм MRO (C3-линеаризация)

---

## Что такое множественное наследование

В Python класс может наследовать от нескольких родительских классов одновременно. Это называется множественным наследованием:

```python
class A:
    pass

class B:
    pass

class C(A, B):   # C наследует от A и B одновременно
    pass
```

Большинство популярных языков — Java, C#, Swift — намеренно не поддерживают множественное наследование для классов, считая его источником сложности. Вместо него они предлагают интерфейсы или трейты. Python занимает другую позицию: множественное наследование поддерживается, но требует понимания механизма разрешения конфликтов.

Два основных сценария, когда множественное наследование действительно полезно:

**Сценарий 1: Mixin-классы.** Это небольшие классы, которые добавляют конкретную функциональность к любому классу. Mixin не является самостоятельной сущностью — он только «подмешивает» возможности. Например, `JSONSerializableMixin` добавляет метод `to_json()` к любому классу, `LoggingMixin` добавляет логирование.

**Сценарий 2: Объединение интерфейсов.** Когда класс должен удовлетворять нескольким контрактам одновременно. Например, `StorageItem` должен быть одновременно `Serializable` и `Cacheable`.

В обоих случаях множественное наследование заменяет сложные конфигурации через композицию более лаконичным синтаксисом наследования.

---

## Проблема «ромба» (Diamond Problem)

Главная сложность множественного наследования — «ромбовидная» иерархия. Рассмотрим классический пример:

```python
class A:
    def method(self):
        print("A.method")


class B(A):
    def method(self):
        print("B.method")


class C(A):
    def method(self):
        print("C.method")


class D(B, C):
    pass
```

Схема иерархии выглядит как ромб:

```
    A
   / \
  B   C
   \ /
    D
```

Вопрос: когда мы вызываем `D().method()`, какой метод будет вызван — `B.method` или `C.method`? Оба они переопределяют `A.method`. `D` напрямую не переопределяет ничего.

Наивный алгоритм «поиска в глубину» (DFS) дал бы: `D → B → A → C`. Это значит, что сначала нашли бы `A.method` через `B`, и метод `C.method` никогда не был бы рассмотрен. Это неверно — `C` стоит ближе к `D` в иерархии, чем `A`.

Именно для решения этой проблемы Python 2.3 перешёл на алгоритм C3-линеаризации, который гарантирует корректный и предсказуемый порядок разрешения методов.

```python
d = D()
d.method()   # B.method — почему именно B, объяснит следующий раздел

print(D.__mro__)
# (<class 'D'>, <class 'B'>, <class 'C'>, <class 'A'>, <class 'object'>)
```

---

## Алгоритм C3-линеаризации

C3 — это алгоритм, который вычисляет MRO (Method Resolution Order) для любого класса.

Способ **построить этот (MRO) порядок так, чтобы не было противоречий**.

Он гарантирует три свойства:

1. **Монотонность**: если `X` стоит перед `Y` в MRO дочернего класса, то `X` стоит перед `Y` в MRO любого его потомка.
2. **Сохранение локального порядка**: если класс объявлен как `D(B, C)`, то `B` всегда стоит перед `C` в MRO.
3. **Согласованность**: MRO уважает порядок MRO всех родителей.

**Формула C3:**

```
L[C(B1, B2, ..., BN)] = C + merge(L[B1], L[B2], ..., L[BN], [B1, B2, ..., BN])
```

Где `L[X]` — линеаризация (MRO) класса `X`, `merge` — специальная операция объединения списков.

**Алгоритм `merge`:**
1. Берём первый элемент (голову) первого списка.
2. Проверяем: входит ли этот элемент в **хвост** (все элементы кроме первого) любого другого списка?
3. Если нет — добавляем элемент в результат и удаляем его из **всех** списков (не только первого).
4. Если да — переходим к следующему списку и берём его голову.
5. Повторяем, пока все списки не опустеют.
6. Если не удалось взять ни один элемент (все головы входят в чьи-то хвосты) — `TypeError`.

Вычислим MRO для ромбовидной иерархии пошагово:

```
L[A] = [A, object]
L[B] = [B, A, object]
L[C] = [C, A, object]
L[D] = D + merge(L[B], L[C], [B, C])
     = D + merge([B, A, object], [C, A, object], [B, C])
```

Шаг 1: голова первого списка — `B`. Входит ли `B` в хвост других списков?
- хвост `[C, A, object]` — нет
- хвост `[C]` — нет
Добавляем `B`, удаляем из всех списков:

```
D + B + merge([A, object], [C, A, object], [C])
```

Шаг 2: голова первого списка — `A`. Входит ли `A` в хвост других списков?
- хвост `[C, A, object]` — **да** (A входит в хвост)
Пропускаем, берём голову следующего списка — `C`. Входит ли `C` в хвост других списков?
- хвост `[object]` — нет
- пустой хвост `[]` — нет
Добавляем `C`, удаляем из всех списков:

```
D + B + C + merge([A, object], [A, object], [])
```

Шаг 3: голова первого списка — `A`. Хвост второго списка — `[object]`. `A` не входит в `[object]`. Добавляем `A`:

```
D + B + C + A + merge([object], [object], [])
```

Шаг 4: добавляем `object`:

```
L[D] = [D, B, C, A, object]
```

Это именно то, что мы видели в `D.__mro__`. Алгоритм C3 гарантирует, что `C` стоит перед `A` — потому что `C` является потомком `A` и ближе к `D` в иерархии.

---

## Практическая работа с `__mro__`

Python предоставляет несколько способов увидеть MRO класса:

```python
class A:
    pass

class B(A):
    pass

class C(A):
    pass

class D(B, C):
    pass

# Способ 1: атрибут __mro__ — кортеж
print(D.__mro__)
# (<class '__main__.D'>, <class '__main__.B'>, <class '__main__.C'>,
#  <class '__main__.A'>, <class 'object'>)

# Способ 2: метод mro() — список
print(D.mro())
# [<class '__main__.D'>, <class '__main__.B'>, <class '__main__.C'>,
#  <class '__main__.A'>, <class 'object'>]

# Более читаемый вывод — только имена классов
print([cls.__name__ for cls in D.__mro__])
# ['D', 'B', 'C', 'A', 'object']
```

Как читать MRO: при обращении к любому методу или атрибуту Python перебирает классы в порядке MRO слева направо и возвращает первый найденный. `D → B → C → A → object`.

Проверим на нашем примере с методами:

```python
class A:
    def greet(self):
        return "Hello from A"

class B(A):
    def greet(self):
        return "Hello from B"

class C(A):
    def greet(self):
        return "Hello from C"

class D(B, C):
    pass

class E(C, B):   # изменили порядок родителей
    pass

print(D().greet())   # Hello from B — B стоит первым в MRO
print(E().greet())   # Hello from C — C стоит первым в MRO

print([cls.__name__ for cls in D.__mro__])   # ['D', 'B', 'C', 'A', 'object']
print([cls.__name__ for cls in E.__mro__])   # ['E', 'C', 'B', 'A', 'object']
```

**Порядок объявления родителей в `class D(B, C)` прямо влияет на MRO**: первый родитель в списке стоит раньше в MRO.

---

## `super()` при множественном наследовании: кооперативный вызов

Теперь вернёмся к `super()` — но с новым пониманием. В уроке 20 мы говорили, что `super()` идёт «по MRO, а не к родителю». Теперь покажем, что это значит на практике при множественном наследовании.

Рассмотрим иерархию, где каждый класс вызывает `super()`:

```python
class A:
    def process(self):
        print("A.process — финальный")
        return "A"


class B(A):
    def process(self):
        print("B.process — начало")
        result = super().process()   # следующий по MRO объекта
        print("B.process — конец")
        return "B → " + result


class C(A):
    def process(self):
        print("C.process — начало")
        result = super().process()   # следующий по MRO объекта
        print("C.process — конец")
        return "C → " + result


class D(B, C):
    def process(self):
        print("D.process — начало")
        result = super().process()   # следующий по MRO: B
        print("D.process — конец")
        return "D → " + result


d = D()
print("MRO:", [cls.__name__ for cls in D.__mro__])
print()
print(d.process())
```

Вывод:

```
MRO: ['D', 'B', 'C', 'A', 'object']

D.process — начало
B.process — начало
C.process — начало
A.process — финальный
C.process — конец
B.process — конец
D.process — конец
D → B → C → A
```

Проследим цепочку:
1. `d.process()` → `D.process()` вызывает `super().process()`
2. Следующий по MRO после `D` — `B`, вызывается `B.process()`
3. `B.process()` вызывает `super().process()` — **следующий по MRO объекта `d`** — это `C` (не `A`!)
4. `C.process()` вызывает `super().process()` — следующий — `A`
5. `A.process()` — финальный, не вызывает `super()` (точнее, вызывает `object.process`, которого нет)

Ключевой момент: когда `B.process()` вызывает `super()`, он получает не свой родитель `A`, а следующий класс по MRO **конкретного объекта** `d` — то есть `C`. Это и есть кооперативное множественное наследование: каждый класс «передаёт эстафету» следующему по MRO.

Если какой-то класс в цепочке не вызовет `super()` — цепочка обрывается:

```python
class BrokenB(A):
    def process(self):
        print("BrokenB.process")
        # НЕ вызываем super() — цепочка обрывается!
        return "B"


class BrokenD(BrokenB, C):
    def process(self):
        return super().process()


print(BrokenD().process())
# BrokenB.process
# B
# C.process НИКОГДА не выполнится
```

**Правило кооперативного наследования**: если вы используете `super()` — все классы в иерархии должны вызывать `super()`. Один «некооперативный» класс ломает всю цепочку.

---

## Паттерн Mixin: правильное применение множественного наследования

Mixin — это класс, предназначенный исключительно для добавления функциональности через множественное наследование. Хороший Mixin:

- **не является самостоятельной сущностью** — нельзя создать объект только из Mixin
- **решает одну задачу** — логирование, сериализация, кеширование
- **минимально зависит от конкретного класса** — использует только то, что гарантированно будет в любом классе-потребителе
- **называется с суффиксом `Mixin`** — явное обозначение намерения

```python
import json
import datetime


class TimestampMixin:
    """
    Mixin: добавляет временные метки создания и обновления.
    Не имеет __init__ — атрибуты устанавливаются методом.
    """

    def set_timestamps(self):
        now = datetime.datetime.now()
        if not hasattr(self, 'created_at'):
            self.created_at = now
        self.updated_at = now

    def get_age_seconds(self) -> float:
        if not hasattr(self, 'created_at'):
            return 0.0
        return (datetime.datetime.now() - self.created_at).total_seconds()


class JSONSerializableMixin:
    """
    Mixin: добавляет JSON-сериализацию.
    Предполагает, что у класса есть метод to_dict().
    """

    def to_json(self, **kwargs) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, **kwargs)

    @classmethod
    def from_json(cls, json_str: str):
        data = json.loads(json_str)
        return cls(**data)


class ValidatableMixin:
    """
    Mixin: добавляет валидацию.
    Предполагает, что у класса есть метод _get_validation_rules().
    """

    def validate(self) -> dict:
        """Возвращает словарь {поле: список_ошибок}."""
        errors = {}
        rules = self._get_validation_rules() if hasattr(self, '_get_validation_rules') else {}
        for field, validators in rules.items():
            value = getattr(self, field, None)
            field_errors = []
            for validator_fn, error_msg in validators:
                if not validator_fn(value):
                    field_errors.append(error_msg)
            if field_errors:
                errors[field] = field_errors
        return errors

    @property
    def is_valid(self) -> bool:
        return not bool(self.validate())


class LoggingMixin:
    """
    Mixin: добавляет логирование операций.
    """

    def log(self, message: str, level: str = "INFO"):
        class_name = self.__class__.__name__
        print(f"[{level}] {class_name}: {message}")
```

Теперь создадим базовый класс и конкретные модели:

```python
class BaseModel:
    """Базовый класс модели. Определяет id и метод to_dict()."""

    _id_counter = 0

    def __init__(self, **kwargs):
        BaseModel._id_counter += 1
        self.id = BaseModel._id_counter

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()
                if not k.startswith('_')}

    def __repr__(self):
        return f"{self.__class__.__name__}(id={self.id})"


class UserModel(TimestampMixin, JSONSerializableMixin, ValidatableMixin, BaseModel):
    """
    Модель пользователя с временными метками, JSON-сериализацией и валидацией.
    MRO: UserModel → TimestampMixin → JSONSerializableMixin → ValidatableMixin → BaseModel → object
    """

    def __init__(self, username: str, email: str, **kwargs):
        super().__init__(**kwargs)
        self.username = username
        self.email = email
        self.set_timestamps()   # из TimestampMixin

    def _get_validation_rules(self) -> dict:
        return {
            "username": [
                (lambda v: v and len(v) >= 3, "Минимум 3 символа"),
                (lambda v: v and len(v) <= 50, "Максимум 50 символов"),
            ],
            "email": [
                (lambda v: v and "@" in v, "Некорректный email"),
            ],
        }

    def to_dict(self) -> dict:
        d = super().to_dict()
        # Конвертируем datetime для JSON
        for key in ('created_at', 'updated_at'):
            if key in d and isinstance(d[key], datetime.datetime):
                d[key] = d[key].isoformat()
        return d


class OrderModel(TimestampMixin, JSONSerializableMixin, LoggingMixin, BaseModel):
    """Модель заказа с временными метками, JSON и логированием."""

    def __init__(self, user_id: int, total: float, **kwargs):
        super().__init__(**kwargs)
        self.user_id = user_id
        self.total = total
        self.status = "pending"
        self.set_timestamps()
        self.log(f"Заказ создан для user_id={user_id}, total={total}")

    def confirm(self):
        self.status = "confirmed"
        self.set_timestamps()   # обновляем updated_at
        self.log(f"Заказ #{self.id} подтверждён")

    def to_dict(self) -> dict:
        d = super().to_dict()
        for key in ('created_at', 'updated_at'):
            if key in d and isinstance(d[key], datetime.datetime):
                d[key] = d[key].isoformat()
        return d
```

Демонстрация:

```python
# MRO для каждой модели
print([cls.__name__ for cls in UserModel.__mro__])
# ['UserModel', 'TimestampMixin', 'JSONSerializableMixin', 'ValidatableMixin',
#  'BaseModel', 'object']

user = UserModel(username="alice", email="alice@example.com")
print(user)
print(user.is_valid)    # True — из ValidatableMixin
print(user.to_json(indent=2))   # из JSONSerializableMixin

# Невалидный пользователь
bad_user = UserModel(username="ab", email="not-email")
print(bad_user.is_valid)   # False
print(bad_user.validate())
# {'username': ['Минимум 3 символа'], 'email': ['Некорректный email']}

# from_json — из JSONSerializableMixin
# (упрощённо — в реальности нужно обработать datetime)

print()
order = OrderModel(user_id=1, total=89990.0)
# [INFO] OrderModel: Заказ создан для user_id=1, total=89990.0

order.confirm()
# [INFO] OrderModel: Заказ #2 подтверждён

print(order.to_json())

# isinstance работает для всех классов в MRO
print(isinstance(user, BaseModel))           # True
print(isinstance(user, JSONSerializableMixin)) # True
print(isinstance(user, TimestampMixin))      # True
```

---

## Паттерн Class-Based Views: миксины в стиле Django

Django использует множественное наследование с миксинами как основной механизм построения Class-Based Views. Реализуем упрощённую версию этой системы:

```python
class BaseView:
    """Базовый класс для всех вью. Определяет метод dispatch()."""

    def dispatch(self, request: dict) -> dict:
        method = request.get("method", "GET").lower()
        handler = getattr(self, method, self.method_not_allowed)
        return handler(request)

    def method_not_allowed(self, request: dict) -> dict:
        return {"status": 405, "error": "Method Not Allowed"}


class ListMixin:
    """Mixin для получения списка объектов (GET /resources/)."""

    def get_queryset(self) -> list:
        """Возвращает набор объектов. Переопределяется в конкретном вью."""
        return []

    def get(self, request: dict) -> dict:
        objects = self.get_queryset()
        return {
            "status": 200,
            "data": objects,
            "count": len(objects),
        }


class CreateMixin:
    """Mixin для создания объекта (POST /resources/)."""

    def create_object(self, data: dict) -> dict:
        """Создаёт объект из данных. Переопределяется в конкретном вью."""
        return {**data, "id": 1}

    def post(self, request: dict) -> dict:
        data = request.get("body", {})
        obj = self.create_object(data)
        return {"status": 201, "data": obj}


class RetrieveMixin:
    """Mixin для получения одного объекта (GET /resources/id/)."""

    def get_object(self, object_id) -> dict:
        """Возвращает конкретный объект. Переопределяется в конкретном вью."""
        return None

    def get(self, request: dict) -> dict:
        object_id = request.get("path_params", {}).get("id")
        obj = self.get_object(object_id)
        if obj is None:
            return {"status": 404, "error": f"Object {object_id} not found"}
        return {"status": 200, "data": obj}


class UpdateMixin:
    """Mixin для обновления объекта (PUT /resources/id/)."""

    def update_object(self, object_id, data: dict) -> dict:
        return {**data, "id": object_id}

    def put(self, request: dict) -> dict:
        object_id = request.get("path_params", {}).get("id")
        data = request.get("body", {})
        obj = self.update_object(object_id, data)
        return {"status": 200, "data": obj}


class DeleteMixin:
    """Mixin для удаления объекта (DELETE /resources/id/)."""

    def delete(self, request: dict) -> dict:
        object_id = request.get("path_params", {}).get("id")
        return {"status": 204, "deleted_id": object_id}


# Собираем вью из миксинов — аналог Django ModelViewSet
class UserListCreateView(ListMixin, CreateMixin, BaseView):
    """
    Вью для /api/users/:
    GET  → список пользователей (ListMixin)
    POST → создание пользователя (CreateMixin)
    """

    _users_db = [
        {"id": 1, "username": "alice"},
        {"id": 2, "username": "bob"},
    ]

    def get_queryset(self) -> list:
        return self._users_db

    def create_object(self, data: dict) -> dict:
        new_id = max(u["id"] for u in self._users_db) + 1
        user = {"id": new_id, **data}
        self._users_db.append(user)
        return user


class UserDetailView(RetrieveMixin, UpdateMixin, DeleteMixin, BaseView):
    """
    Вью для /api/users/id/:
    GET    → один пользователь (RetrieveMixin)
    PUT    → обновление (UpdateMixin)
    DELETE → удаление (DeleteMixin)
    """

    _users_db = {
        1: {"id": 1, "username": "alice"},
        2: {"id": 2, "username": "bob"},
    }

    def get_object(self, object_id) -> dict:
        return self._users_db.get(int(object_id))


# Демонстрация
list_view = UserListCreateView()
detail_view = UserDetailView()

print([cls.__name__ for cls in UserListCreateView.__mro__])
# ['UserListCreateView', 'ListMixin', 'CreateMixin', 'BaseView', 'object']

# GET /api/users/ — список
response = list_view.dispatch({"method": "GET"})
print(response)   # {'status': 200, 'data': [...], 'count': 2}

# POST /api/users/ — создание
response = list_view.dispatch({
    "method": "POST",
    "body": {"username": "carol", "email": "carol@example.com"}
})
print(response)   # {'status': 201, 'data': {'id': 3, 'username': 'carol', ...}}

# GET /api/users/1/ — один пользователь
response = detail_view.dispatch({
    "method": "GET",
    "path_params": {"id": "1"}
})
print(response)   # {'status': 200, 'data': {'id': 1, 'username': 'alice'}}

# DELETE /api/users/2/
response = detail_view.dispatch({
    "method": "DELETE",
    "path_params": {"id": "2"}
})
print(response)   # {'status': 204, 'deleted_id': '2'}

# Метод не поддерживается
response = list_view.dispatch({"method": "DELETE"})
print(response)   # {'status': 405, 'error': 'Method Not Allowed'}
```

---

## Проблема с `__init__` при множественном наследовании

Одна из самых сложных ситуаций — когда несколько классов в иерархии имеют `__init__` с разными параметрами. Проблема в том, что `super().__init__()` передаёт аргументы следующему по MRO классу, а тот может не ожидать этих аргументов.

Стандартное решение — использование `**kwargs` для «прозрачной» передачи аргументов по цепочке:

```python
class A:
    def __init__(self, **kwargs):
        print(f"A.__init__, kwargs={kwargs}")
        super().__init__(**kwargs)   # передаём остаток object.__init__


class B(A):
    def __init__(self, b_param, **kwargs):
        print(f"B.__init__, b_param={b_param}")
        super().__init__(**kwargs)   # передаём только то, что осталось
        self.b_param = b_param


class C(A):
    def __init__(self, c_param, **kwargs):
        print(f"C.__init__, c_param={c_param}")
        super().__init__(**kwargs)
        self.c_param = c_param


class D(B, C):
    def __init__(self, b_param, c_param, **kwargs):
        print(f"D.__init__")
        # Передаём все параметры — каждый класс возьмёт свой
        super().__init__(b_param=b_param, c_param=c_param, **kwargs)


d = D(b_param="hello", c_param="world")
print(f"b_param={d.b_param}, c_param={d.c_param}")
```

Вывод:

```
D.__init__
B.__init__, b_param=hello
C.__init__, c_param=world
A.__init__, kwargs={}
b_param=hello, c_param=world
```

Паттерн `**kwargs` позволяет каждому классу «взять» нужные ему параметры и передать остаток следующему по MRO. Это называется «кооперативной инициализацией».

---

## Неразрешимый MRO: когда Python выбрасывает `TypeError`

Не всегда C3 может построить корректный MRO. Если два родительских класса задают противоречивый порядок для общего предка — Python выбрасывает `TypeError`:

```python
class X:
    pass

class Y:
    pass

class A(X, Y):   # A говорит: X перед Y
    pass

class B(Y, X):   # B говорит: Y перед X — противоречие!
    pass

try:
    class C(A, B):   # невозможно удовлетворить оба требования
        pass
except TypeError as e:
    print(e)
# Cannot create a consistent method resolution order (MRO) for bases X, Y
```

`A` требует, чтобы `X` шёл перед `Y`. `B` требует, чтобы `Y` шёл перед `X`. Для `C(A, B)` оба требования должны выполняться одновременно — это невозможно.

Решение: переосмыслить иерархию. Обычно такая ситуация возникает при плохом проектировании и является сигналом, что нужно пересмотреть структуру классов.

---

## Когда множественное наследование — плохая идея

Не каждую проблему стоит решать через множественное наследование. Признаки того, что что-то идёт не так:

**Классу нужно несколько «настоящих» родителей.** Если вы пишете `class ElectricCar(Car, Battery)` — и `Car`, и `Battery` являются самостоятельными сущностями с состоянием — это сигнал использовать композицию:

```python
# Сомнительное наследование
class ElectricCar(Car, Battery):
    pass

# Лучше через композицию
class ElectricCar(Car):
    def __init__(self, make, model, battery_capacity):
        super().__init__(make, model)
        self.battery = Battery(battery_capacity)   # has-a, а не is-a
```

**Метод переопределяется неожиданным образом.** Если вы не можете с первого взгляда понять, какой именно метод будет вызван — иерархия слишком сложная.

**Глубина наследования больше 3.** Цепочки вида `D(C(B(A)))` при множественном наследовании становятся крайне трудными для понимания.

**Правило:** используйте множественное наследование только для Mixin-классов. Если оба родителя — «настоящие» классы предметной области, скорее всего нужна композиция.

---

## Неочевидные моменты и типичные ошибки

**`isinstance()` возвращает `True` для всех классов в MRO.** Это означает, что объект `UserModel` является экземпляром каждого из классов в его MRO:

```python
user = UserModel("alice", "alice@example.com")

print(isinstance(user, UserModel))            # True
print(isinstance(user, TimestampMixin))       # True
print(isinstance(user, JSONSerializableMixin)) # True
print(isinstance(user, ValidatableMixin))     # True
print(isinstance(user, BaseModel))            # True
print(isinstance(user, object))              # True
```

Это полезно: вы можете проверять, «умеет» ли объект что-то (например, `isinstance(obj, JSONSerializableMixin)`).

**Атрибуты класса при множественном наследовании.** Атрибуты класса (не экземпляра) ищутся по тому же MRO. Если оба родителя определяют один и тот же атрибут класса — победит тот, кто стоит раньше в MRO:

```python
class A:
    class_attr = "from A"

class B(A):
    class_attr = "from B"

class C(A):
    class_attr = "from C"

class D(B, C):
    pass

print(D.class_attr)   # from B — B стоит первым в MRO
```

**`super()` в Mixin-классах.** Mixin-класс должен вызывать `super()` даже если сам не наследует ни от чего (кроме `object`). Иначе он оборвёт цепочку:

```python
class LoggingMixin:
    def save(self):
        print(f"[LOG] Сохраняем {self}")
        super().save()   # передаём управление следующему по MRO
        print(f"[LOG] Сохранено")


class BaseModel:
    def save(self):
        print(f"Реальное сохранение в БД")


class UserModel(LoggingMixin, BaseModel):
    pass


user = UserModel()
user.save()
# [LOG] Сохраняем ...
# Реальное сохранение в БД
# [LOG] Сохранено
```

Если бы `LoggingMixin.save()` не вызывал `super().save()` — метод `BaseModel.save()` никогда не выполнился бы.

---

## Итоги урока

Множественное наследование в Python — мощный, но требующий понимания инструмент. Алгоритм C3-линеаризации обеспечивает предсказуемый и логичный порядок разрешения методов (MRO), решая проблему «ромба» корректнее, чем наивный DFS.

MRO можно просмотреть через `ClassName.__mro__`. При вызове любого метода Python перебирает классы в порядке MRO и использует первый найденный. `super()` возвращает прокси на следующий класс в MRO конкретного объекта — не на родительский класс в статическом смысле.

Основное применение множественного наследования — паттерн Mixin. Mixin добавляет одну конкретную функциональность и разработан для использования совместно с другими классами. Порядок объявления родителей влияет на MRO: первый родитель имеет более высокий приоритет.

`super()` при множественном наследовании должен вызываться в каждом классе — это обеспечивает «кооперативный» обход всей цепочки. `**kwargs` помогает решить проблему разных сигнатур `__init__` в цепочке.

В следующем уроке мы рассмотрим `__slots__` — механизм оптимизации памяти, который фиксирует набор атрибутов класса и имеет особое поведение при наследовании.

---

## Вопросы

1. Что такое «проблема ромба» (Diamond Problem) и почему наивный алгоритм DFS не решает её корректно?
2. Опишите алгоритм C3 в общих чертах. Что такое операция `merge` и каково её ключевое правило?
3. Чем `super()` при множественном наследовании отличается от `super()` при одиночном? Почему важно вызывать `super()` в каждом классе цепочки?
4. Что такое Mixin и каковы признаки хорошего Mixin-класса?
5. Как порядок объявления родителей в `class D(B, C)` влияет на MRO? Приведите пример с разным поведением.
6. Как правильно организовать `__init__` при множественном наследовании с несколькими параметрами? Какой паттерн помогает избежать конфликтов?
7. При каких условиях Python выбрасывает `TypeError` при определении класса с множественным наследованием?
8. Почему `isinstance(obj, SomeMixin)` возвращает `True`, если класс объекта использует этот Mixin? Как это используется на практике?

---

## Задачи

### **Задача 1**. 

Вычисление MRO вручную

Дана следующая иерархия классов:

```python
class A:
    pass

class B(A):
    pass

class C(A):
    pass

class D(B):
    pass

class E(C):
    pass

class F(D, E):
    pass
```

Задание: а) Нарисуйте схему иерархии (на бумаге или в комментарии). б) Вычислите MRO для класса `F` по алгоритму C3 пошагово. в) Проверьте результат через `F.__mro__`. г) Если бы у всех классов был метод `hello()`, печатающий имя класса, что вывела бы `F().hello()`?

Дополнительно: определите метод `hello()` во всех классах так, чтобы каждый вызывал `super().hello()`. Проследите полную цепочку вызовов.

---

### **Задача 2**. 

Миксины для модели Product

Создайте три Mixin-класса:
- `PriceMixin` — добавляет атрибуты `price` и `currency`, метод `format_price() -> str` (например, `"1 500.00 RUB"`), метод `apply_discount(percent: float) -> float` — цена со скидкой.
- `InventoryMixin` — добавляет `stock_quantity`, методы `is_available() -> bool`, `reserve(quantity) -> bool` (уменьшает stock если достаточно, возвращает True).
- `SEOMixin` — добавляет `slug` (строка из `name` с заменой пробелов на `-` и приведением к нижнему регистру), `meta_description` (первые 160 символов из `description`).

Создайте класс `BaseProduct` с атрибутами `id`, `name`, `description`. Создайте `Product(PriceMixin, InventoryMixin, SEOMixin, BaseProduct)`. Все параметры передаются через `__init__` с паттерном `**kwargs`. Продемонстрируйте MRO и работу всех методов.

**Пример использования**:

```python
p = Product(
    name="Python Book",
    description="Comprehensive guide to Python programming. Covers OOP, async, testing.",
    price=2500.0,
    currency="RUB",
    stock_quantity=15
)

print(p.format_price())         # 2 500.00 RUB
print(p.apply_discount(10))    # 2250.0
print(p.is_available())        # True
print(p.reserve(3))            # True
print(p.stock_quantity)        # 12
print(p.slug)                  # python-book
print(p.meta_description)      # Comprehensive guide... (до 160 символов)
```

---

### **Задача 3**. 

Кооперативный `__init__` в иерархии

Создайте иерархию классов для описания сотрудников. Базовый класс `Person(name, email)`. Mixin-классы:
- `EmployeeMixin(department, salary)` — добавляет `department`, `salary`, метод `annual_salary()`.
- `ManagerMixin(team_size)` — добавляет `team_size`, метод `get_team_bonus(percent)` (процент от суммы зарплат команды, упрощённо: `salary * team_size * percent / 100`).
- `RemoteMixin(timezone)` — добавляет `timezone`, метод `get_local_time()` (имитирует вывод часового пояса).

Создайте три конкретных класса через множественное наследование:
- `Employee(EmployeeMixin, Person)` — обычный сотрудник.
- `Manager(ManagerMixin, EmployeeMixin, Person)` — менеджер.
- `RemoteManager(RemoteMixin, ManagerMixin, EmployeeMixin, Person)` — удалённый менеджер.

Все `__init__` используют `**kwargs`. Выведите MRO для каждого класса и продемонстрируйте, что все атрибуты правильно инициализированы.

**Пример использования**:

```python
rm = RemoteManager(
    name="Alice",
    email="alice@example.com",
    department="Engineering",
    salary=300000,
    team_size=8,
    timezone="UTC+3"
)

print(rm.name)           # Alice
print(rm.annual_salary()) # 3600000
print(rm.get_team_bonus(10))   # 240000.0
print(rm.get_local_time())     # Alice работает в UTC+3
```

---

### **Задача 4**. 

Миксины для системы логирования и кеширования

Создайте два Mixin-класса:
- `CacheMixin` — кешируёт результаты метода `get(key)`. Хранит кеш в `self._cache = {}`. Переопределяет `get(key)`: сначала проверяет кеш, если есть — возвращает оттуда, если нет — вызывает `super().get(key)`, кеширует и возвращает. Метод `invalidate(key=None)` — очищает один ключ или весь кеш.
- `LoggingMixin` — логирует вызовы метода `get(key)`. Перед `super().get(key)` выводит `"[LOG] GET key={key}"`, после — `"[LOG] RESULT: {result}"`.

Создайте базовый класс `DataStore` с методом `get(key) -> str`, который возвращает `f"data for {key}"` (имитация запроса к хранилищу с выводом `"[DB] Запрос key={key}"`).

Создайте три комбинации:
- `CachedStore(CacheMixin, DataStore)` — только кеш.
- `LoggedStore(LoggingMixin, DataStore)` — только логирование.
- `CachedLoggedStore(CacheMixin, LoggingMixin, DataStore)` — оба.

Продемонстрируйте порядок вызовов для каждой комбинации и покажите, что при повторном обращении к `CachedStore` реального запроса к `DataStore` не происходит.

**Пример использования**:

```python
store = CachedLoggedStore()
store.get("user:1")
# [LOG] GET key=user:1
# [DB] Запрос key=user:1
# [LOG] RESULT: data for user:1

store.get("user:1")   # из кеша
# [LOG] GET key=user:1
# [LOG] RESULT: data for user:1  (без [DB] — взято из кеша)
```

---

### **Задача 5**. 

Неразрешимый MRO и рефакторинг

Дана проблемная иерархия. Определите, почему Python не может построить MRO для класса `Problematic`, и предложите два варианта рефакторинга.

```python
class Base:
    pass

class Left(Base):
    pass

class Right(Base):
    pass

class LeftChild(Left, Right):  # Left перед Right
    pass

class RightChild(Right, Left):  # Right перед Left — противоречие с LeftChild!
    pass

# Попытка создать Problematic вызовет TypeError
# class Problematic(LeftChild, RightChild):
#     pass
```

Задание: а) Объясните в комментарии, почему `Problematic(LeftChild, RightChild)` вызывает `TypeError`. б) Предложите и реализуйте Вариант 1: изменить порядок родителей в одном из классов, чтобы MRO стал разрешимым. в) Предложите Вариант 2: рефакторинг через композицию вместо наследования.

---

### **Задача 6**. 

Система миксинов для REST API

Реализуйте полноценную систему Class-Based Views с миксинами. Базовый класс `APIView` с атрибутом `serializer_fields = []` и методом `serialize(obj) -> dict` (возвращает только поля из `serializer_fields`). Mixin-классы:
- `PaginationMixin` — добавляет `page_size = 10`, метод `paginate(queryset, page=1) -> dict` с полями `data`, `page`, `total_pages`, `count`.
- `FilterMixin` — добавляет метод `filter_queryset(queryset, filters: dict) -> list` — фильтрует список словарей по переданным параметрам.
- `AuthRequiredMixin` — переопределяет `dispatch(request)`: если в запросе нет `headers.Authorization` — возвращает 401 без вызова `super()`.

Создайте `UserListAPIView(AuthRequiredMixin, PaginationMixin, FilterMixin, APIView)` с `serializer_fields = ["id", "username", "email"]` и `get(request)`, который: применяет фильтры из `request.get("query_params", {})`, пагинирует результат, сериализует каждый объект.

```python
view = UserListAPIView()

# Без авторизации
response = view.dispatch({"method": "GET", "headers": {}})
print(response)   # {'status': 401, 'error': 'Unauthorized'}

# С авторизацией и фильтрацией
response = view.dispatch({
    "method": "GET",
    "headers": {"Authorization": "Bearer token"},
    "query_params": {"department": "Engineering"}
})
print(response)  # {'data': [...], 'page': 1, 'total_pages': ..., 'count': ...}
```

---

[Предыдущий урок](lesson24.md) | [Следующий урок](lesson26.md)