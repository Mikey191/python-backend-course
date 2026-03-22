# Урок 9. Дескрипторы в Python: контроль доступа к атрибутам на уровне языка

На предыдущем занятии мы подробно разобрали механизм `property` и увидели, как с его помощью можно управлять доступом к атрибутам объекта. Это уже мощный инструмент инкапсуляции. Однако у него есть один существенный недостаток: при большом количестве атрибутов код начинает дублироваться.

В этом уроке мы разберём более универсальный и фундаментальный механизм — **дескрипторы**. Это низкоуровневый инструмент Python, на котором, в том числе, построен `property`.

---

## Проблема дублирования кода

Рассмотрим класс точки в трёхмерном пространстве:

```python
class Point3D:
    def __init__(self, x, y, z):
        self._x = x
        self._y = y
        self._z = z
```

Допустим, по условиям задачи координаты должны быть **только целыми числами**. Добавим проверку:

```python
class Point3D:
    @classmethod
    def verify_coord(cls, coord):
        if type(coord) != int:
            raise TypeError("Координата должна быть целым числом")
```

Теперь реализуем свойства:

```python
class Point3D:
    ...

    @property
    def x(self):
        return self._x

    @x.setter
    def x(self, coord):
        self.verify_coord(coord)
        self._x = coord

    @property
    def y(self):
        return self._y

    @y.setter
    def y(self, coord):
        self.verify_coord(coord)
        self._y = coord

    @property
    def z(self):
        return self._z

    @z.setter
    def z(self, coord):
        self.verify_coord(coord)
        self._z = coord
```

И используем:

```python
p = Point3D(1, 2, 3)
```

Чтобы всё корректно работало, нужно переписать `__init__`:

```python
def __init__(self, x, y, z):
    self.x = x
    self.y = y
    self.z = z
```

### Проблема

* Код повторяется 3 раза
* Логика одинаковая
* Отличается только имя атрибута

Если таких полей будет 10–20 — код станет трудно поддерживаемым.

---

## Что такое дескриптор

**Дескриптор — это класс, который управляет доступом к атрибутам других классов.**

Он реализует один или несколько методов:

```python
__get__(self, instance, owner)
__set__(self, instance, value)
__delete__(self, instance)
```

### Типы дескрипторов

| Тип                 | Методы                             | Назначение               |
| ------------------- | ---------------------------------- | ------------------------ |
| non-data descriptor | только `__get__`                   | только чтение            |
| data descriptor     | `__get__`, `__set__`, `__delete__` | чтение, запись, удаление |

---

## Первый дескриптор: базовая реализация

Создадим дескриптор для работы с целыми числами:

```python
class Integer:
    def __set_name__(self, owner, name):
        # owner — класс, где объявлен дескриптор
        # name — имя атрибута (x, y, z)
        self.name = "_" + name

    def __get__(self, instance, owner):
        # instance — объект (например, pt)
        return instance.__dict__[self.name]

    def __set__(self, instance, value):
        instance.__dict__[self.name] = value
```

---

### Использование дескриптора

Теперь применим его:

```python
class Point3D:
    x = Integer()
    y = Integer()
    z = Integer()

    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z
```

Создаём объект:

```python
pt = Point3D(1, 2, 3)
print(pt.__dict__)
```

Результат:

```python
{'_x': 1, '_y': 2, '_z': 3}
```

---

## Жизненный цикл дескриптора (по шагам)

### Шаг 1. Создание класса `Point3D`

Когда Python встречает:

```python
class Point3D:
    x = Integer()
```

происходит следующее:

1. Создаётся объект `Integer()`
2. Он сохраняется в `Point3D.__dict__['x']`
3. Вызывается метод:

```python
Integer.__set_name__(self, owner=Point3D, name='x')
```

**Что здесь важно**

* `self` → сам объект дескриптора (`Integer()`)
* `owner` → класс, в котором он объявлен (`Point3D`)
* `name` → имя атрибута (`x`)

**Что делает строка:**

```python
self.name = "_" + name
```

Она формирует имя **реального атрибута**, который будет храниться в объекте:

```
x → _x
y → _y
z → _z
```

---

### Шаг 2. Создание объекта

```python
pt = Point3D(1, 2, 3)
```

Внутри `__init__`:

```python
self.x = x
```

Но! Это **не обычное присваивание**.

Python видит, что `x` — это дескриптор, и вызывает:

```python
Integer.__set__(self=<Integer>, instance=pt, value=1)
```

**Параметры `__set__`**

```python
def __set__(self, instance, value):
```

* `self` → объект дескриптора (`Integer`)
* `instance` → объект, с которым работаем (`pt`)
* `value` → присваиваемое значение (например, `1`)

**Выполняется:**

```python
instance.__dict__[self.name] = value
```

То есть:

```python
pt.__dict__['_x'] = 1
```

---

### Шаг 3. Чтение значения

```python
print(pt.x)
```

Python снова видит дескриптор и вызывает:

```python
Integer.__get__(self=<Integer>, instance=pt, owner=Point3D)
```

**Параметры `__get__`**

```python
def __get__(self, instance, owner):
```

* `self` → дескриптор
* `instance` → объект (`pt`)
* `owner` → класс (`Point3D`)

**Важно**

Если обращение идёт через класс:

```python
Point3D.x
```

→ тогда:

```python
instance = None
owner = Point3D
```

---

**Что выполняется:**

```python
return instance.__dict__[self.name]
```

→ возвращает:

```python
pt.__dict__['_x']
```

---

### Визуальная схема работы

**Запись**

```
pt.x = 10
   ↓
__set__(Integer, pt, 10)
   ↓
pt.__dict__['_x'] = 10
```

**Чтение**

```
pt.x
   ↓
__get__(Integer, pt, Point3D)
   ↓
return pt.__dict__['_x']
```

---

## Добавляем валидацию

Теперь добавим проверку типов:

```python
class Integer:
    @classmethod
    def verify_coord(cls, value):
        if type(value) != int:
            raise TypeError("Координата должна быть целым числом")

    def __set_name__(self, owner, name):
        self.name = "_" + name

    def __get__(self, instance, owner):
        return getattr(instance, self.name)

    def __set__(self, instance, value):
        self.verify_coord(value)
        setattr(instance, self.name, value)
```

### Проверка

```python
pt = Point3D(1, 2, 3)
pt.x = 10      # OK
pt.y = "test"  # Ошибка
```

Ошибка:

```
TypeError: Координата должна быть целым числом
```

---

## Non-data descriptor (важное отличие)

Создадим дескриптор только для чтения:

```python
class ReadIntX:
    def __set_name__(self, owner, name):
        self.name = "_x"

    def __get__(self, instance, owner):
        return getattr(instance, self.name)
```

Добавим в класс:

```python
class Point3D:
    x = Integer()
    y = Integer()
    z = Integer()

    xr = ReadIntX()
```

Используем:

```python
pt = Point3D(1, 2, 3)
print(pt.xr)  # 1
```

Теперь попробуем:

```python
pt.xr = 100
print(pt.xr)
```

Результат:

```
100
```

### Почему так произошло

* `xr` стал обычным атрибутом объекта
* дескриптор проиграл приоритет

---

## Data descriptor (приоритет выше)

Добавим `__set__`:

```python
class ReadIntX:
    def __set_name__(self, owner, name):
        self.name = "_x"

    def __get__(self, instance, owner):
        return getattr(instance, self.name)

    def __set__(self, instance, value):
        setattr(instance, self.name, value)
```

Теперь:

```python
pt.__dict__['xr'] = 100
print(pt.xr)
```

Результат:

```
1
```

### Вывод

* Data descriptor **перекрывает** атрибуты экземпляра
* Non-data descriptor — **нет**

---

## Ключевая идея дескрипторов

> Дескриптор — это прокси-объект, который перехватывает доступ к атрибуту.

Он встраивается в механизм:

* чтения (`obj.attr`)
* записи (`obj.attr = value`)
* удаления (`del obj.attr`)

---

## Почему это используется редко

В обычной разработке чаще используют:

* `property`
* обычные атрибуты

**Причина:**

* дескрипторы сложнее читать
* сложнее дебажить
* неочевидны для новичков

---

## Где дескрипторы реально используются

### Кейc 1. ORM (Django, SQLAlchemy)

Пример из реальной жизни:

```python
class User(Model):
    name = StringField()
    age = IntegerField()
```

**Что происходит**

* `StringField` и `IntegerField` — это дескрипторы
* они:

  * валидируют данные
  * сохраняют их в БД
  * управляют доступом

**Пример логики:**

```python
class IntegerField:
    def __set__(self, instance, value):
        if not isinstance(value, int):
            raise TypeError("Must be int")
        instance.__dict__[self.name] = value
```

---

### Кейc 2. Валидация данных (альтернатива property)

Когда много одинаковых полей:

```python
class Product:
    price = PositiveNumber()
    weight = PositiveNumber()
    quantity = PositiveNumber()
```

Один дескриптор — много полей.

---

### Кейc 3. Логирование доступа

```python
class LoggedAttribute:
    def __get__(self, instance, owner):
        print("Чтение атрибута")
        return instance.__dict__[self.name]

    def __set__(self, instance, value):
        print("Изменение атрибута")
        instance.__dict__[self.name] = value
```

---

### Кейc 4. Lazy loading (ленивая загрузка)

```python
class LazyProperty:
    def __get__(self, instance, owner):
        value = expensive_function()
        setattr(instance, self.name, value)
        return value
```

Используется когда:

* данные дорогие в вычислении
* нужно вычислить один раз

---

### Кейc 5. Кэширование

```python
class CachedValue:
    def __get__(self, instance, owner):
        if self.name not in instance.__dict__:
            instance.__dict__[self.name] = compute()
        return instance.__dict__[self.name]
```

---

### Кейc 6. Контроль доступа (security / ACL)

```python
class ProtectedField:
    def __get__(self, instance, owner):
        if not instance.is_admin:
            raise PermissionError()
        return instance.__dict__[self.name]
```

---

## Итоговая модель понимания

* Обычный атрибут → просто значение
* property → обёртка над одним атрибутом
* descriptor → универсальный механизм управления атрибутами

> Дескрипторы — это способ вынести логику работы с атрибутом из класса в отдельный объект.

---

# Вопросы

1. Что такое дескриптор в Python?
2. Какие методы должен реализовывать дескриптор?
3. В чем разница между data descriptor и non-data descriptor?
4. Почему дескрипторы помогают избежать дублирования кода?
5. Что делает метод `__set_name__`?
6. Почему лучше использовать `getattr` и `setattr`, а не `__dict__`?
7. Что произойдет, если присвоить значение атрибуту, связанному с non-data descriptor?
8. Почему data descriptor имеет более высокий приоритет?
9. Когда лучше использовать property вместо дескриптора?
10. Как связаны property и дескрипторы?

---

[Предыдущий урок](lesson08.md) | [Следующий урок](lesson10.md)
