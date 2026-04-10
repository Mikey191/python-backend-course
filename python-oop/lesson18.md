# Урок 18. Арифметические методы: `__add__`, `__mul__` и другие

---

## Зачем нужны арифметические магические методы

Когда вы пишете `3 + 5`, Python вызывает `(3).__add__(5)`. Когда пишете `"hello" + " world"` — вызывается `"hello".__add__(" world")`. Когда пишете `[1, 2] + [3, 4]` — вызывается `[1, 2].__add__([3, 4])`. За каждым арифметическим оператором в Python стоит магический метод.

Это означает, что вы можете дать любому собственному классу поведение, которое логически соответствует арифметике — и тогда объекты этого класса будут работать с операторами `+`, `-`, `*`, `/` точно так же, как встроенные типы.

На первый взгляд это кажется экзотической возможностью, далёкой от практики веб-разработки. Но подумайте о конкретных задачах: сложение денежных сумм при подсчёте итога заказа, накопление временных интервалов для метрик производительности, суммирование статистики по запросам. Всё это — арифметика над пользовательскими объектами.

Более того, стандартная функция `sum()` использует операцию сложения. Если ваш объект реализует `__add__`, то `sum(list_of_objects)` будет работать автоматически — при одном дополнительном условии, о котором мы поговорим подробно.

---

## Полная таблица арифметических методов

Арифметические методы делятся на четыре группы.

**Бинарные методы** — вызываются для операций с двумя операндами:

| Оператор | Метод |
|---|---|
| `a + b` | `a.__add__(b)` |
| `a - b` | `a.__sub__(b)` |
| `a * b` | `a.__mul__(b)` |
| `a / b` | `a.__truediv__(b)` |
| `a // b` | `a.__floordiv__(b)` |
| `a % b` | `a.__mod__(b)` |
| `a ** b` | `a.__pow__(b)` |

**Отражённые методы** — вызываются, когда левый операнд вернул `NotImplemented`:

| Оператор | Метод (вызывается на правом операнде) |
|---|---|
| `a + b` | `b.__radd__(a)` |
| `a - b` | `b.__rsub__(a)` |
| `a * b` | `b.__rmul__(a)` |
| `a / b` | `b.__rtruediv__(a)` |

**Инкрементные методы** — вызываются для операций присваивания:

| Оператор | Метод |
|---|---|
| `a += b` | `a.__iadd__(b)` |
| `a -= b` | `a.__isub__(b)` |
| `a *= b` | `a.__imul__(b)` |

**Унарные методы** — вызываются для операций с одним операндом:

| Оператор | Метод |
|---|---|
| `-a` | `a.__neg__()` |
| `+a` | `a.__pos__()` |
| `abs(a)` | `a.__abs__()` |
| `round(a, n)` | `a.__round__(n)` |

---

## Механика: что происходит при `a + b`

Прежде чем переходить к примерам, важно точно понять последовательность действий Python при вычислении `a + b`:

```
Шаг 1: вызвать a.__add__(b)
        → если вернул результат (не NotImplemented) — использовать его

Шаг 2: если a.__add__(b) вернул NotImplemented или не определён —
        вызвать b.__radd__(a)
        → если вернул результат — использовать его

Шаг 3: если оба вернули NotImplemented —
        выбросить TypeError: unsupported operand type(s) for +
```

Исключение: если `b` является подклассом `a`, Python сначала попробует `b.__radd__(a)` — подкласс имеет приоритет.

Эта последовательность объясняет, зачем нужны отражённые методы и почему правильно возвращать `NotImplemented` вместо выброса исключения.

---

## Простейший пример: класс `Vector2D`

Начнём с классического учебного примера, который демонстрирует чистую механику арифметических методов. Двумерный вектор — понятный объект, чья арифметика интуитивно ясна.

```python
class Vector2D:
    """
    Двумерный вектор. Поддерживает сложение, вычитание,
    умножение на скаляр и унарные операции.
    """

    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __add__(self, other):
        # Сложение двух векторов: (x1+x2, y1+y2)
        if not isinstance(other, Vector2D):
            return NotImplemented   # не знаем, как складывать с другим типом
        return Vector2D(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        # Вычитание векторов: (x1-x2, y1-y2)
        if not isinstance(other, Vector2D):
            return NotImplemented
        return Vector2D(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar):
        # Умножение вектора на скаляр: (x*k, y*k)
        if not isinstance(scalar, (int, float)):
            return NotImplemented
        return Vector2D(self.x * scalar, self.y * scalar)

    def __rmul__(self, scalar):
        # Отражённое умножение: scalar * vector
        # Вызывается при 2 * v, когда int не знает, как умножиться на Vector2D
        return self.__mul__(scalar)   # коммутативна, делегируем в __mul__

    def __neg__(self):
        # Унарный минус: -vector = (-x, -y)
        return Vector2D(-self.x, -self.y)

    def __pos__(self):
        # Унарный плюс: обычно возвращает копию объекта
        return Vector2D(self.x, self.y)

    def __abs__(self):
        # abs(vector) = длина вектора (евклидова норма)
        import math
        return math.sqrt(self.x ** 2 + self.y ** 2)

    def __eq__(self, other):
        if not isinstance(other, Vector2D):
            return NotImplemented
        return self.x == other.x and self.y == other.y

    def __repr__(self):
        return f"Vector2D({self.x}, {self.y})"

    def __str__(self):
        return f"({self.x}, {self.y})"
```

Проверим все операции:

```python
v1 = Vector2D(1, 2)
v2 = Vector2D(3, 4)

# Бинарные операции — каждая возвращает новый объект
print(v1 + v2)    # (4, 6)
print(v2 - v1)    # (2, 2)
print(v1 * 3)     # (3, 6)
print(3 * v1)     # (3, 6) — работает через __rmul__

# Унарные операции
print(-v1)        # (-1, -2)
print(+v1)        # (1, 2)
print(abs(v2))    # 5.0 — длина вектора (3, 4, 5 — египетский треугольник)

# Цепочки операций — работают, потому что каждый метод возвращает новый объект
result = v1 + v2 - Vector2D(1, 1)
print(result)     # (3, 5)

# Исходные объекты не изменились
print(v1)   # (1, 2) — не изменился
print(v2)   # (3, 4) — не изменился
```

---

## Возвращаемый тип: почему всегда новый объект

Арифметические методы должны возвращать новый объект, а не изменять `self`. Это фундаментальное требование — нарушение его приводит к неожиданному поведению при цепочках операций.

```python
# НЕВЕРНАЯ реализация — изменяет self
class BadVector:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __add__(self, other):
        self.x += other.x   # ОШИБКА: изменяем исходный объект
        self.y += other.y
        return self         # и возвращаем его же


a = BadVector(1, 2)
b = BadVector(3, 4)

c = a + b   # a изменён, c == a == (4, 6)
print(a.x, a.y)   # 4 6 — a изменился! Это неожиданно
print(c is a)     # True — c и a — один и тот же объект

# Цепочка сломана:
d = a + b + b   # теперь непредсказуемо
```

Правило: `a + b` не должно менять ни `a`, ни `b`. Аналогия с числами: `x = 5; y = x + 3` не меняет `x`. Тот же принцип для пользовательских типов.

---

## `NotImplemented`: сигнал о несовместимости типов

Когда ваш метод не умеет работать с переданным типом, нужно вернуть `NotImplemented` — не `False`, не `None`, не выбросить исключение, а именно специальное значение `NotImplemented`.

```python
def __add__(self, other):
    if not isinstance(other, Vector2D):
        return NotImplemented   # правильно
    return Vector2D(self.x + other.x, self.y + other.y)
```

Это важно по двум причинам.

Первая: Python использует `NotImplemented` как сигнал для перехода к следующей попытке — вызову отражённого метода на правом операнде. Если вы выбросите исключение вместо возврата `NotImplemented`, Python не сможет попробовать второй вариант.

Вторая: это позволяет корректно обрабатывать случаи, когда правый операнд знает, как взаимодействовать с вашим типом, даже если левый — нет.

```python
v = Vector2D(1, 2)

# Этот код работает, даже если int не знает про Vector2D:
result = 3 * v
# Шаг 1: int.__mul__(v) → NotImplemented (int не знает Vector2D)
# Шаг 2: v.__rmul__(3) → Vector2D(3, 6) ← вот где решается задача
```

---

## Отражённые методы: `__radd__`, `__rsub__`, `__rmul__`

Отражённые методы решают одну конкретную проблему: что делать, когда левый операнд не умеет работать с вашим типом.

Рассмотрим пример без `__rmul__`:

```python
class Vector2D:
    def __mul__(self, scalar):
        if not isinstance(scalar, (int, float)):
            return NotImplemented
        return Vector2D(self.x * scalar, self.y * scalar)
    # __rmul__ не определён


v = Vector2D(1, 2)
print(v * 3)   # (3, 6) — работает: v.__mul__(3)
print(3 * v)   # TypeError! — int.__mul__(v) → NotImplemented, __rmul__ не найден
```

Добавляем `__rmul__`:

```python
def __rmul__(self, scalar):
    # Умножение коммутативно для скаляра, поэтому просто делегируем
    return self.__mul__(scalar)

print(3 * v)   # (3, 6) — теперь работает
```

Обратите внимание: для умножения на скаляр `__rmul__` просто делегирует в `__mul__`, потому что умножение коммутативно. Но для некоммутативных операций это важнее:

```python
class Matrix:
    def __sub__(self, other):
        # Матрица - матрица
        ...

    def __rsub__(self, other):
        # other - матрица: это НЕ то же самое, что матрица - other
        # Нельзя просто делегировать в __sub__!
        if not isinstance(other, Matrix):
            return NotImplemented
        return other.__sub__(self)   # порядок операндов инвертирован
```

Особый случай — `__radd__` с нулём. Функция `sum()` начинает с нуля: `sum([a, b, c])` вычисляется как `((0 + a) + b) + c`. Это означает, что первый вызов будет `0 + a`, то есть `(0).__add__(a)` → `NotImplemented` → `a.__radd__(0)`. Если `__radd__` не обработает случай `other == 0`, `sum()` не будет работать:

```python
def __radd__(self, other):
    # Специальная обработка нуля для совместимости с sum()
    if other == 0:
        return self
    if not isinstance(other, Vector2D):
        return NotImplemented
    return self.__add__(other)


v1 = Vector2D(1, 2)
v2 = Vector2D(3, 4)
v3 = Vector2D(5, 6)

# Теперь sum() работает!
total = sum([v1, v2, v3])
print(total)   # (9, 12)
```

---

## Инкрементные методы: `__iadd__`, `__isub__`, `__imul__`

Операторы `+=`, `-=`, `*=` по умолчанию работают через обычные методы: `a += b` превращается в `a = a.__add__(b)`. Но если вы определите `__iadd__`, Python использует его — и в этом случае `a += b` означает `a = a.__iadd__(b)`.

Ключевое отличие: `__iadd__` предназначен для изменяемых объектов, которые могут обновить себя «на месте», избегая создания нового объекта. Именно поэтому `__iadd__` должен изменить `self` и вернуть `self`.

```python
class RequestStats:
    """
    Статистика HTTP-запросов. Изменяемый объект-накопитель.
    Поддерживает += для добавления нового измерения.
    """

    def __init__(self, count=0, total_time=0.0):
        self.count = count
        self.total_time = total_time   # суммарное время в секундах

    @property
    def avg_time(self):
        return self.total_time / self.count if self.count else 0.0

    def __add__(self, other):
        # Создаём новый объект — для случаев вроде stats1 + stats2
        if not isinstance(other, RequestStats):
            return NotImplemented
        return RequestStats(
            count=self.count + other.count,
            total_time=self.total_time + other.total_time
        )

    def __iadd__(self, other):
        # Изменяем self на месте — для накопления: stats += new_measurement
        if not isinstance(other, RequestStats):
            return NotImplemented
        self.count += other.count
        self.total_time += other.total_time
        return self   # __iadd__ ОБЯЗАН вернуть self

    def __repr__(self):
        return (
            f"RequestStats(count={self.count}, "
            f"total_time={self.total_time:.3f}s, "
            f"avg={self.avg_time:.3f}s)"
        )
```

Демонстрируем разницу между `+` и `+=`:

```python
stats = RequestStats(count=0, total_time=0.0)

# Имитируем поступление данных о запросах
measurements = [
    RequestStats(1, 0.120),
    RequestStats(1, 0.085),
    RequestStats(1, 0.200),
    RequestStats(1, 0.095),
]

for m in measurements:
    stats += m   # вызывает __iadd__ — изменяет stats на месте, не создаёт новый

print(stats)
# RequestStats(count=4, total_time=0.500s, avg=0.125s)

# При += объект остаётся тем же (id не меняется)
original_id = id(stats)
stats += RequestStats(1, 0.100)
print(id(stats) == original_id)   # True — тот же объект

# __add__ создаёт новый объект
combined = stats + RequestStats(10, 1.500)
print(id(combined) == id(stats))  # False — новый объект
print(stats)    # не изменился
print(combined) # новый объект с суммой
```

Если `__iadd__` не определён, `a += b` работает как `a = a.__add__(b)` — создаётся новый объект. Это корректно для неизменяемых объектов (числа, строки). Для изменяемых объектов-накопителей `__iadd__` выгоднее: он экономит память и время на создание нового объекта.

---

## Унарные методы: `__neg__`, `__pos__`, `__abs__`

Унарные методы работают с одним операндом — самим объектом.

`__neg__` вызывается оператором `-obj` и обычно возвращает «отрицательную» версию объекта.

`__pos__` вызывается оператором `+obj`. На первый взгляд кажется бесполезным — зачем нужен унарный плюс? Но он полезен для нормализации: `+obj` может вернуть «канонический» вариант объекта. Например, для денежной суммы `+Money(-5, "RUB")` могла бы вернуть абсолютное значение, или проверить корректность.

`__abs__` вызывается встроенной функцией `abs(obj)` и обычно возвращает «модуль» или «длину» объекта.

```python
class Temperature:
    """Температура в градусах Цельсия."""

    def __init__(self, celsius):
        self.celsius = celsius

    def __neg__(self):
        # -temperature: инвертируем знак
        return Temperature(-self.celsius)

    def __pos__(self):
        # +temperature: нормализуем — возвращаем температуру,
        # округлённую до одного знака (каноническая форма)
        return Temperature(round(self.celsius, 1))

    def __abs__(self):
        # abs(temperature): отклонение от нуля
        return Temperature(abs(self.celsius))

    def __repr__(self):
        return f"Temperature({self.celsius}°C)"


t1 = Temperature(-15.37)
print(-t1)    # Temperature(15.37°C)   — инверсия знака
print(+t1)    # Temperature(-15.4°C)  — нормализация (округление)
print(abs(t1))# Temperature(15.37°C)  — абсолютное значение
```

---

## Метод `__round__`

Встроенная функция `round(obj, ndigits)` вызывает `obj.__round__(ndigits)`. Это особенно полезно для объектов, содержащих числовые значения — денежные суммы, координаты, физические величины.

```python
class Coordinate:
    def __init__(self, lat, lon):
        self.lat = lat
        self.lon = lon

    def __round__(self, ndigits=0):
        # round(coord, 4) округляет обе координаты до 4 знаков
        return Coordinate(round(self.lat, ndigits), round(self.lon, ndigits))

    def __repr__(self):
        return f"Coordinate({self.lat}, {self.lon})"


c = Coordinate(55.75372891, 37.61990234)
print(round(c, 4))   # Coordinate(55.7537, 37.6199)
print(round(c, 2))   # Coordinate(55.75, 37.62)
print(round(c))      # Coordinate(56, 38)
```

---

## Практический пример: класс `Money`

Теперь применим все изученные инструменты к реальной задаче. Денежные суммы — пожалуй, самый частый случай арифметики над пользовательскими объектами в веб-приложениях. Суммирование позиций в корзине, применение скидки, расчёт налога — всё это операции над объектами «деньги».

```python
from decimal import Decimal, ROUND_HALF_UP


class Money:
    """
    Денежная сумма с валютой.

    Поддерживает:
    - Сложение и вычитание сумм в одной валюте
    - Умножение на числовой коэффициент (скидки, налоги)
    - Деление для вычисления доли
    - Сравнение через __eq__ и __lt__
    - Округление через round()
    - Совместимость с sum() через __radd__
    """

    def __init__(self, amount, currency="RUB"):
        # Используем Decimal для точных денежных вычислений
        # float даёт ошибки: 0.1 + 0.2 == 0.30000000000000004
        self.amount = Decimal(str(amount))
        self.currency = currency.upper()

    def _check_currency(self, other):
        """Проверяем совместимость валют перед операцией."""
        if self.currency != other.currency:
            raise ValueError(
                f"Нельзя выполнять операции с разными валютами: "
                f"{self.currency} и {other.currency}"
            )

    def __add__(self, other):
        if not isinstance(other, Money):
            return NotImplemented
        self._check_currency(other)
        return Money(self.amount + other.amount, self.currency)

    def __radd__(self, other):
        # Поддержка sum(): sum() начинает с 0, поэтому нужно обработать 0 + Money
        if other == 0:
            return self
        if not isinstance(other, Money):
            return NotImplemented
        return self.__add__(other)

    def __sub__(self, other):
        if not isinstance(other, Money):
            return NotImplemented
        self._check_currency(other)
        return Money(self.amount - other.amount, self.currency)

    def __mul__(self, factor):
        # Умножение на коэффициент: Money * 1.2 (наценка 20%)
        if not isinstance(factor, (int, float, Decimal)):
            return NotImplemented
        return Money(self.amount * Decimal(str(factor)), self.currency)

    def __rmul__(self, factor):
        # 1.2 * Money — тоже должно работать
        return self.__mul__(factor)

    def __truediv__(self, divisor):
        # Деление суммы на число: Money / 3 (разделить на троих)
        if not isinstance(divisor, (int, float, Decimal)):
            return NotImplemented
        if divisor == 0:
            raise ZeroDivisionError("Нельзя делить денежную сумму на ноль")
        return Money(self.amount / Decimal(str(divisor)), self.currency)

    def __neg__(self):
        # Отрицательная сумма (для корректировок, возвратов)
        return Money(-self.amount, self.currency)

    def __abs__(self):
        return Money(abs(self.amount), self.currency)

    def __round__(self, ndigits=2):
        # round(price, 2) — округление до копеек
        quantize_str = Decimal(10) ** -ndigits
        rounded = self.amount.quantize(quantize_str, rounding=ROUND_HALF_UP)
        return Money(rounded, self.currency)

    def __eq__(self, other):
        if not isinstance(other, Money):
            return NotImplemented
        return self.amount == other.amount and self.currency == other.currency

    def __lt__(self, other):
        if not isinstance(other, Money):
            return NotImplemented
        self._check_currency(other)
        return self.amount < other.amount

    def __bool__(self):
        # Сумма «истинна», если она ненулевая
        return self.amount != 0

    def __str__(self):
        return f"{self.amount:.2f} {self.currency}"

    def __repr__(self):
        return f"Money({self.amount!r}, {self.currency!r})"
```

Демонстрируем работу в контексте интернет-магазина:

```python
# Позиции в корзине
item1 = Money(1500, "RUB")   # ноутбук
item2 = Money(890, "RUB")    # мышь
item3 = Money(450, "RUB")    # коврик

# Сумма заказа через sum() — работает через __radd__
total = sum([item1, item2, item3])
print(f"Итого: {total}")   # Итого: 2840.00 RUB

# Применение скидки 10%
discount_rate = Decimal("0.10")
discount = total * discount_rate
print(f"Скидка: {discount}")   # Скидка: 284.0000 RUB

# Округление скидки до копеек
discount_rounded = round(discount, 2)
print(f"Скидка (округлено): {discount_rounded}")   # Скидка (округлено): 284.00 RUB

# Итого со скидкой
final = total - discount_rounded
print(f"К оплате: {final}")   # К оплате: 2556.00 RUB

# Разделить на количество человек
per_person = final / 3
print(f"На каждого: {round(per_person, 2)}")   # На каждого: 852.00 RUB

# Попытка сложить разные валюты
usd_price = Money(15, "USD")
try:
    wrong = item1 + usd_price
except ValueError as e:
    print(e)   # Нельзя выполнять операции с разными валютами: RUB и USD

# Возврат товара (отрицательная сумма)
refund = -item2
print(f"Возврат: {refund}")   # Возврат: -890.00 RUB

# Булев контекст
zero = Money(0, "RUB")
print(bool(total))   # True
print(bool(zero))    # False
```

---

## Практический пример: класс `Duration`

Второй практический пример — временные интервалы. В системах мониторинга веб-приложений нужно накапливать время выполнения запросов, вычислять среднее и суммарное время, сравнивать интервалы. Всё это — арифметика над `Duration`.

```python
class Duration:
    """
    Временной интервал. Хранит время в секундах (float).

    Применение:
    - Суммирование времён выполнения запросов
    - Вычисление средней длительности
    - Сравнение производительности эндпоинтов
    """

    def __init__(self, seconds):
        if seconds < 0:
            raise ValueError(f"Длительность не может быть отрицательной: {seconds}")
        self._seconds = float(seconds)

    @classmethod
    def from_ms(cls, milliseconds):
        """Создаёт Duration из миллисекунд."""
        return cls(milliseconds / 1000)

    @property
    def seconds(self):
        return self._seconds

    @property
    def milliseconds(self):
        return self._seconds * 1000

    def __add__(self, other):
        if not isinstance(other, Duration):
            return NotImplemented
        return Duration(self._seconds + other._seconds)

    def __radd__(self, other):
        # Поддержка sum() — обработка начального нуля
        if other == 0:
            return self
        if not isinstance(other, Duration):
            return NotImplemented
        return self.__add__(other)

    def __sub__(self, other):
        if not isinstance(other, Duration):
            return NotImplemented
        result = self._seconds - other._seconds
        if result < 0:
            raise ValueError(
                f"Нельзя вычесть большую длительность из меньшей: "
                f"{self} - {other}"
            )
        return Duration(result)

    def __mul__(self, factor):
        # Duration * n: интервал повторяется n раз
        if not isinstance(factor, (int, float)):
            return NotImplemented
        if factor < 0:
            raise ValueError("Множитель не может быть отрицательным")
        return Duration(self._seconds * factor)

    def __rmul__(self, factor):
        return self.__mul__(factor)

    def __truediv__(self, divisor):
        # Duration / n: делим интервал (например, для среднего)
        if isinstance(divisor, (int, float)):
            if divisor <= 0:
                raise ValueError("Делитель должен быть положительным числом")
            return Duration(self._seconds / divisor)
        if isinstance(divisor, Duration):
            # Duration / Duration: соотношение длительностей (безразмерное число)
            if divisor._seconds == 0:
                raise ZeroDivisionError("Нельзя делить на нулевую длительность")
            return self._seconds / divisor._seconds
        return NotImplemented

    def __eq__(self, other):
        if not isinstance(other, Duration):
            return NotImplemented
        return self._seconds == other._seconds

    def __lt__(self, other):
        if not isinstance(other, Duration):
            return NotImplemented
        return self._seconds < other._seconds

    def __bool__(self):
        return self._seconds > 0

    def __round__(self, ndigits=3):
        return Duration(round(self._seconds, ndigits))

    def __str__(self):
        if self._seconds < 1:
            return f"{self.milliseconds:.1f}ms"
        return f"{self._seconds:.3f}s"

    def __repr__(self):
        return f"Duration({self._seconds!r})"
```

Применяем в системе мониторинга:

```python
# Имитируем время выполнения запросов к разным эндпоинтам
request_times = [
    Duration.from_ms(120),
    Duration.from_ms(85),
    Duration.from_ms(200),
    Duration.from_ms(95),
    Duration.from_ms(150),
]

# Суммарное время через sum() — работает через __radd__
total = sum(request_times)
print(f"Суммарное время: {total}")   # Суммарное время: 0.650s

# Среднее время: Duration / int → Duration
avg = total / len(request_times)
print(f"Среднее время: {avg}")       # Среднее время: 130.0ms

# Округление
print(f"Среднее (округл.): {round(avg, 2)}")   # Среднее (округл.): 130.0ms

# Порог производительности
threshold = Duration.from_ms(100)
slow_requests = [t for t in request_times if t > threshold]
print(f"Медленных запросов: {len(slow_requests)}")   # 3

# Соотношение длительностей (Duration / Duration → float)
ratio = Duration.from_ms(200) / Duration.from_ms(100)
print(f"Самый медленный в {ratio:.1f}x раз медленнее порога")   # в 2.0x раз

# Бюджет на 10 запросов
budget = threshold * 10
print(f"Бюджет на 10 запросов: {budget}")   # Бюджет на 10 запросов: 1.000s

# Превышение бюджета?
print(f"Бюджет превышен: {total > budget}")   # Бюджет превышен: False
```

---

## Неочевидные моменты и типичные ошибки

**`__iadd__` должен возвращать `self`.** Это обязательное требование. Python выполняет `a = a.__iadd__(b)` — если метод вернёт `None`, переменная `a` станет `None`:

```python
class BadAccumulator:
    def __iadd__(self, other):
        self.value += other
        # Забыли return self!

acc = BadAccumulator()
acc.value = 0
acc += 5
print(acc)   # None — переменная потеряна
```

**Приоритет подкласса при отражении.** Если правый операнд является подклассом левого, Python вызывает отражённый метод подкласса первым — даже до обычного метода левого операнда. Это позволяет подклассам переопределять поведение операторов при взаимодействии с родительским классом:

```python
class Money:
    def __add__(self, other):
        print("Money.__add__")
        ...

class TaxedMoney(Money):
    def __radd__(self, other):
        print("TaxedMoney.__radd__")   # вызовется первым при Money + TaxedMoney
        ...

m = Money(100, "RUB")
t = TaxedMoney(50, "RUB")
result = m + t   # TaxedMoney.__radd__ вызовется ПЕРВЫМ
```

**`sum()` начинает с нуля — обязательно обработайте это в `__radd__`.**

```python
# Без обработки нуля в __radd__:
total = sum([Money(100, "RUB"), Money(200, "RUB")])
# TypeError: unsupported operand type(s) for +: 'int' and 'Money'
# Потому что sum() делает 0 + Money(100) → int.__add__(Money) → NotImplemented
# → Money.__radd__(0) — и здесь нужно проверить isinstance(other, int) and other == 0
```

**`__floordiv__` vs `__truediv__` vs `__mod__`.** Оператор `/` вызывает `__truediv__`, оператор `//` — `__floordiv__`, оператор `%` — `__mod__`. Это три разных метода. Если вы реализовали только `__truediv__`, оператор `//` всё равно не будет работать:

```python
d1 = Duration(10)
d2 = Duration(3)

d1 / 3    # работает через __truediv__
d1 // 3   # TypeError — __floordiv__ не определён
```

**Возвращаемый тип при смешанных операциях.** Когда вы умножаете `Money * float`, что должен вернуть метод — `Money` или `float`? Всегда возвращайте тот тип, который семантически корректен. `Money * 1.2` должен вернуть `Money` (сумма с наценкой), а не число.

---

## Итоги урока

Арифметические методы делятся на четыре группы: бинарные (`__add__`, `__sub__` и другие), отражённые (`__radd__`, `__rsub__`), инкрементные (`__iadd__`, `__isub__`) и унарные (`__neg__`, `__abs__`, `__round__`).

Бинарные методы должны возвращать новый объект, не изменяя `self`. При несовместимом типе правого операнда — возвращать `NotImplemented`, не исключение. Это позволяет Python перейти к отражённому методу.

Отражённые методы решают проблему `scalar * obj`: если `scalar.__mul__(obj)` вернул `NotImplemented`, Python вызовет `obj.__rmul__(scalar)`. Для поддержки `sum()` необходимо обработать случай `other == 0` в `__radd__`.

Инкрементные методы (`__iadd__` и другие) предназначены для изменяемых объектов-накопителей: они изменяют `self` на месте и обязаны вернуть `self`. Если `__iadd__` не определён, `+=` работает через `__add__` с созданием нового объекта.

---

## Вопросы

1. Опишите последовательность попыток Python при вычислении `a + b`. Когда вызывается `__radd__`?
2. Почему арифметические методы должны возвращать новый объект, а не изменять `self`? Что произойдёт при нарушении этого правила?
3. Почему `__iadd__` обязан возвращать `self`? Что произойдёт, если не вернуть значение?
4. Чем отличается `__iadd__` от `__add__` с точки зрения создания объектов? В каких случаях уместен каждый подход?
5. Почему `sum([obj1, obj2, obj3])` не работает без специальной обработки в `__radd__`? Что нужно добавить?
6. Почему при реализации денежной арифметики рекомендуется использовать `Decimal` вместо `float`?
7. Что делает Python, если правый операнд является подклассом левого? Почему это важно?
8. Когда `__pos__` возвращает не просто `self`, а новый объект? Приведите пример практического применения.

---

## Задачи

### Задача 1. 

Класс `Vector3D`

Создайте класс `Vector3D` — трёхмерный вектор с координатами `x`, `y`, `z` (числа). Реализуйте следующие арифметические методы:

- `__add__` и `__sub__` — покоординатное сложение и вычитание двух векторов.
- `__mul__` — умножение на скаляр (`int` или `float`), результат — новый `Vector3D`.
- `__rmul__` — поддержка `scalar * vector`.
- `__neg__` — унарный минус, инвертирует все координаты.
- `__abs__` — длина вектора (евклидова норма): `√(x² + y² + z²)`.

При передаче несовместимого типа возвращайте `NotImplemented`. Реализуйте `__eq__`, `__repr__` в формате `Vector3D(1, 2, 3)` и `__str__` в формате `(1, 2, 3)`.

**Пример использования**:

```python
v1 = Vector3D(1, 2, 3)
v2 = Vector3D(4, 5, 6)

print(v1 + v2)     # (5, 7, 9)
print(v2 - v1)     # (3, 3, 3)
print(v1 * 2)      # (2, 4, 6)
print(3 * v1)      # (3, 6, 9)
print(-v1)         # (-1, -2, -3)
print(abs(v1))     # 3.7416573867739413

# Цепочка операций
result = (v1 + v2) * 2
print(result)      # (10, 14, 18)
print(v1)          # (1, 2, 3) — исходный не изменился

# Совместимость с sum()
vectors = [Vector3D(1, 0, 0), Vector3D(0, 1, 0), Vector3D(0, 0, 1)]
print(sum(vectors))   # (1, 1, 1)
```

---

### Задача 2. 

Класс `Percentage`

Создайте класс `Percentage`, представляющий процентное значение. Принимает `value` — число от 0 до 100. При значении вне диапазона — выбрасывать `ValueError`.

При инициализации создаётся атрибут `self.value` (число с плавающей точкой).

Реализуйте:

- `__add__` и `__sub__` — сложение и вычитание двух `Percentage`. Если результат вне `[0, 100]` — выбрасывать `ValueError`.
- `__mul__` — умножение `Percentage` на `Percentage`: `10% * 20% = 2%` (по правилу составных процентов: `a * b / 100`). Так же умножение на `int` или `float`: `Percentage(10) * 3 = Percentage(30)`.
- `__neg__` — не имеет смысла для процентов, выбрасывать `TypeError("Отрицательный процент не допускается")`.
- `__round__` — округление значения до `ndigits` знаков.

Реализуйте `__str__` в формате `"10.0%"` и `__repr__` в формате `Percentage(10.0)`.

**Пример использования**:

```python
tax = Percentage(20)
discount = Percentage(10)
base_commission = Percentage(5)

print(tax)          # 20.0%
print(tax + discount)   # 30.0%
print(tax - discount)   # 10.0%

# Составной процент: НДС от суммы со скидкой
effective = tax * discount   # 20% * 10% / 100 = 2%
print(effective)             # 2.0%

# Умножение на число
tripled = base_commission * 3
print(tripled)    # 15.0%

# Округление
p = Percentage(33.3333)
print(round(p, 2))   # 33.33%

try:
    neg = -tax
except TypeError as e:
    print(e)   # Отрицательный процент не допускается

try:
    over = Percentage(80) + Percentage(30)
except ValueError as e:
    print(e)   # Процент не может превышать 100
```

---

### Задача 3. 

Класс `TextBuffer`

Создайте класс `TextBuffer` — изменяемый буфер для накопления текста. Принимает начальную строку `text` (по умолчанию пустая строка).

При инициализации создаётся атрибут `self._text` (строка).

Реализуйте:

- `__add__` — конкатенация двух `TextBuffer`, возвращает новый `TextBuffer`.
- `__iadd__` — добавление текста к текущему буферу на месте (изменяет `self._text` и возвращает `self`). Принимает `TextBuffer` или `str`.
- `__mul__` — повторение текста: `TextBuffer("ab") * 3 = TextBuffer("ababab")`.
- `__rmul__` — поддержка `3 * buffer`.
- `__len__` — длина текущего текста.
- `__bool__` — `True`, если буфер не пуст.

Реализуйте `__str__` (возвращает текст) и `__repr__` в формате `TextBuffer('hello')`.

**Пример использования**:

```python
buf = TextBuffer()
print(bool(buf))   # False — пустой

buf += "Hello"
buf += TextBuffer(", World")
print(buf)         # Hello, World
print(len(buf))    # 12

# += изменяет тот же объект
original_id = id(buf)
buf += "!"
print(id(buf) == original_id)   # True — тот же объект

# + создаёт новый объект
new_buf = buf + TextBuffer(" Extra")
print(new_buf)                  # Hello, World! Extra
print(buf)                      # Hello, World! — не изменился

# Умножение
separator = TextBuffer("-") * 20
print(separator)   # --------------------
print(3 * TextBuffer("ab"))   # ababab
```

---

### Задача 4. 

Класс `Temperature`

Создайте класс `Temperature`, представляющий температуру. Принимает `celsius` (число).

При инициализации создаётся атрибут `self.celsius` (число с плавающей точкой).

Реализуйте:

- `__add__` и `__sub__` — сложение и вычитание двух `Temperature` или `Temperature` и числа (число трактуется как градусы Цельсия).
- `__mul__` — умножение температуры на число (масштабирование).
- `__neg__` — инверсия знака.
- `__abs__` — температура как абсолютное значение (всегда >= 0).
- `__round__` — округление до `ndigits` знаков.

Добавьте свойства `fahrenheit` (перевод в Фаренгейт: `C * 9/5 + 32`) и `kelvin` (перевод в Кельвины: `C + 273.15`). При получении `kelvin` — если значение отрицательное (ниже абсолютного нуля), выбрасывать `ValueError`.

Реализуйте `__str__` в формате `"-15.0°C"` и `__repr__` в формате `Temperature(-15.0)`.

Пример использования:

```python
t1 = Temperature(100)
t2 = Temperature(20)

print(t1 + t2)        # 120.0°C
print(t1 - t2)        # 80.0°C
print(t1 + 5)         # 105.0°C
print(t1 * 0.5)       # 50.0°C
print(-t2)            # -20.0°C
print(abs(Temperature(-15)))  # 15.0°C

print(t1.fahrenheit)  # 212.0
print(t2.kelvin)      # 293.15

t3 = Temperature(36.6789)
print(round(t3, 1))   # 36.7°C

# sum() работает
temps = [Temperature(20), Temperature(22), Temperature(18)]
total = sum(temps)
print(total / 3)      # 20.0°C
```

---

### Задача 5. 

Класс `RequestCount`

Создайте класс `RequestCount` — счётчик HTTP-запросов по статусным кодам. Используется для накопления статистики по группам ответов.

При инициализации объект принимает необязательные именованные аргументы: `success` (2xx, по умолчанию 0), `client_errors` (4xx, по умолчанию 0), `server_errors` (5xx, по умолчанию 0).

Создаются атрибуты `self.success`, `self.client_errors`, `self.server_errors`.

Реализуйте:

- `__add__` — суммирование двух `RequestCount`, возвращает новый объект.
- `__iadd__` — накопление статистики на месте (изменяет `self`, возвращает `self`). Принимает `RequestCount`.
- `__mul__` — умножение всех счётчиков на целое число (например, для масштабирования).
- `__rmul__` — поддержка `n * RequestCount`.

Добавьте свойство `total` — сумма всех счётчиков. Добавьте метод `error_rate()` — доля ошибочных запросов (4xx + 5xx) от общего числа. Если `total == 0` — возвращать `0.0`.

Реализуйте `__str__` в формате `"RequestCount(ok=10, 4xx=2, 5xx=0, total=12)"` и `__repr__` аналогично.

**Пример использования**:

```python
stats = RequestCount()

# Накапливаем статистику за каждую минуту
stats += RequestCount(success=95, client_errors=3, server_errors=2)
stats += RequestCount(success=88, client_errors=7, server_errors=5)

print(stats)
# RequestCount(ok=183, 4xx=10, 5xx=7, total=200)

print(f"Процент ошибок: {stats.error_rate():.1%}")
# Процент ошибок: 8.5%

# sum() по списку счётчиков
hourly = [
    RequestCount(success=300, client_errors=10, server_errors=2),
    RequestCount(success=280, client_errors=15, server_errors=5),
    RequestCount(success=310, client_errors=8,  server_errors=1),
]
total = sum(hourly)
print(total)
print(f"Всего запросов за час: {total.total}")

# Масштабирование (прогноз на день)
daily_forecast = total * 24
print(f"Прогноз на день: {daily_forecast.total}")
```

---

### Задача 6. 

Класс `Polynomial`

Создайте класс `Polynomial` — многочлен с целыми коэффициентами. Принимает коэффициенты в порядке убывания степени: `Polynomial(2, -3, 1)` означает `2x² - 3x + 1`.

При инициализации создаётся атрибут `self.coeffs` — список коэффициентов (от старшей степени к младшей). Удалите ведущие нули при создании (но оставьте хотя бы один коэффициент).

Реализуйте:

- `__add__` — сложение двух многочленов. Коэффициенты степеней суммируются; если степени разные — дополните нулями до нужной длины.
- `__sub__` — вычитание многочленов.
- `__mul__` — умножение многочлена на целое число (скаляр).
- `__rmul__` — поддержка `scalar * polynomial`.
- `__neg__` — инверсия всех коэффициентов.
- `__call__` — вычисление значения в точке `x`: `p(3)` вычисляет значение многочлена при x=3.

Добавьте свойство `degree` — степень многочлена (индекс старшего ненулевого коэффициента).

Реализуйте `__str__` в человекочитаемом формате (например, `"2x^2 - 3x + 1"`) и `__repr__` в формате `Polynomial(2, -3, 1)`.

**Пример использования**:

```python
p1 = Polynomial(2, -3, 1)   # 2x² - 3x + 1
p2 = Polynomial(1, 4)        # x + 4

print(p1)          # 2x^2 - 3x + 1
print(p2)          # x + 4
print(p1.degree)   # 2

print(p1 + p2)     # 2x^2 - 2x + 5
print(p1 - p2)     # 2x^2 - 4x - 3
print(p1 * 3)      # 6x^2 - 9x + 3
print(3 * p1)      # 6x^2 - 9x + 3
print(-p1)         # -2x^2 + 3x - 1

print(p1(0))    # 1    (2*0 - 3*0 + 1)
print(p1(1))    # 0    (2 - 3 + 1)
print(p1(2))    # 3    (8 - 6 + 1)
print(p1(3))    # 10   (18 - 9 + 1)
```

---

[Предыдущий урок](lesson17.md) | [Следующий урок](lesson19.md)