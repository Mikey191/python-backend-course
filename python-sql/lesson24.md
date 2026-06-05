# Урок 24. SQLAlchemy ORM

## Типы связей между таблицами

В реляционных базах данных таблицы связываются друг с другом через внешние ключи. Но один внешний ключ может выражать принципиально разные отношения между данными. Таких отношений три.

### Один-ко-многим (One-to-Many)

Самая распространённая связь. Одна запись в таблице A связана с несколькими записями в таблице B.

```
Категория «Электроника»  →  Ноутбук Lenovo
                         →  Смартфон Samsung
                         →  Планшет Apple
```

Одна категория — много товаров. Внешний ключ всегда находится на стороне "многих" — в нашем случае в таблице `products`:

```python
class Product(Base):
    __tablename__ = 'products'
    category_id = Column(Integer, ForeignKey('categories.id'))  # здесь
```

### Многие-к-одному (Many-to-One)

Это та же самая связь, просто смотрим с другой стороны. Много товаров принадлежат одной категории. Технически в базе данных разницы нет — внешний ключ один и тот же. Разница только в том с какой стороны мы идём по связи в коде.

Когда загружаем товар и хотим узнать его категорию — это "многие к одному". Именно поэтому для `product.category` используют `joinedload` — мы получаем один объект, не коллекцию.

### Один-к-одному (One-to-One)

Одна запись в A связана ровно с одной записью в B. Пример: пользователь и его профиль с дополнительными данными. В нашем учебном проекте эта связь не используется, но важно знать что она существует.

### Многие-ко-многим (Many-to-Many)

Одна запись в A связана со многими записями в B, и одна запись в B — со многими в A.

```
Пост «FastAPI»  →  Тег «python»
                →  Тег «backend»
                →  Тег «api»

Тег «python»  →  Пост «FastAPI»
              →  Пост «SQLAlchemy»
              →  Пост «Django»
```

Эту связь нельзя выразить одним внешним ключом — нужна промежуточная таблица которая хранит пары `(post_id, tag_id)`. В SQLAlchemy она описывается через `secondary`. Мы добавим эту связь в финальном проекте — там она появится естественно.

### Какие связи есть в нашей учебной базе `shop.db`

```
categories ──< products          один-ко-многим
              (одна категория — много товаров)

users ──< orders                  один-ко-многим
              (один пользователь — много заказов)

orders ──< order_items            один-ко-многим
              (один заказ — много позиций)

products ──< order_items          один-ко-многим
              (один товар — много позиций в разных заказах)
```

Заметьте: в `shop.db` нет связи многие-ко-многим. Таблица `order_items` — это не связь многие-ко-многим между `orders` и `products`, а самостоятельная сущность с собственными данными (`quantity`, `price_at_time`). Это тонкое но важное различие.

---

## От таблиц к классам

В Уроке 23 мы описывали таблицы через объекты `Table` и писали запросы через `select()`, `insert()` — близко к SQL, но уже с преимуществами Python.

ORM делает следующий шаг: таблица становится **классом**, строка таблицы — **объектом** этого класса. Вы не пишете SQL вручную — вы работаете с объектами, а ORM сам генерирует нужные запросы.

```
Таблица users:           Класс User:
┌─────────────────┐      class User(Base):
│ id    INTEGER   │  →       id    = Column(Integer, primary_key=True)
│ name  TEXT      │  →       name  = Column(String)
│ email TEXT      │  →       email = Column(String)
└─────────────────┘

Строка таблицы:          Объект класса:
│ 1 │ Алексей │ alex@  │  →  user = User(id=1, name='Алексей', email='alex@')
```

---

## Установка и импорты

```bash
pip install sqlalchemy
```

```python
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Session, relationship
```

---

## DeclarativeBase — основа всех моделей

Все модели ORM наследуются от базового класса. В SQLAlchemy 2.x создаётся через `DeclarativeBase`:

```python
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass
```

`Base` — не модель таблицы, это общий предок. Он хранит метаданные всех моделей и нужен для создания таблиц. Все ваши модели будут наследоваться от него.

Это нужно для `Base.metadata.create_all(engine)` который создаёт таблицы. Без наследования от `Base` SQLAlchemy не будет знать о существовании модели.

---

## Декларативные модели

Модель — это класс унаследованный от `Base`. Каждый атрибут-класса типа `Column` соответствует столбцу таблицы:

```python
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class Category(Base):
    __tablename__ = 'categories'   # имя таблицы в БД

    id   = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String,  nullable=False, unique=True)

    # Связь: одна категория → много товаров
    # back_populates создаёт обратную ссылку в Product
    products = relationship('Product', back_populates='category')

    def __repr__(self):
        return f'<Category id={self.id} name={self.name!r}>'


class Product(Base):
    __tablename__ = 'products'

    id          = Column(Integer, primary_key=True, autoincrement=True)
    name        = Column(String,  nullable=False)
    price       = Column(Float,   nullable=False)
    stock       = Column(Integer, nullable=False, default=0)
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=False)

    # Обратная ссылка: каждый товар знает свою категорию
    category = relationship('Category', back_populates='products')

    def __repr__(self):
        return f'<Product id={self.id} name={self.name!r} price={self.price}>'
```

**Что здесь важно:**

`__tablename__` — обязательный атрибут, имя таблицы в базе данных.

`ForeignKey('categories.id')` — внешний ключ через строку `'таблица.столбец'`. ORM знает что `category_id` ссылается на `id` таблицы `categories`.

`relationship('Product', back_populates='category')` — описывает связь на Python-уровне. Не создаёт столбец в БД — только инструкцию как загружать связанные объекты. `back_populates` связывает два relationship в пару.

> **`ForeignKey` отвечает за связь в базе данных, а `relationship` — за удобную навигацию по этой связи в Python-коде.**

`__repr__` — необязательный, но полезный метод. Без него объект выведется как `<Product object at 0x...>`.

---

## Почему нужен промежуточный класс Base

Это вопрос который возникает у всех кто видит этот паттерн впервые. Действительно — зачем создавать пустой класс `Base` если можно было бы написать просто `class Category(DeclarativeBase)`?

Попробуем именно так:

```python
from sqlalchemy.orm import DeclarativeBase

# Можно ли так?
class Category(DeclarativeBase):
    __tablename__ = 'categories'
    id   = Column(Integer, primary_key=True)
    name = Column(String)

class Product(DeclarativeBase):
    __tablename__ = 'products'
    id   = Column(Integer, primary_key=True)
    name = Column(String)
```

Технически SQLAlchemy это допустит. Но вы получите **два независимых реестра метаданных** — по одному на каждый класс. `Category` ничего не знает о `Product` и наоборот. Это сломает несколько вещей сразу.

### Что делает DeclarativeBase под капотом

Когда вы пишете `class Base(DeclarativeBase): pass` — создаётся не просто класс. Внутри него появляется объект `Base.metadata` — реестр всей схемы базы данных. Каждый класс унаследованный от `Base` автоматически регистрирует себя в этом реестре.

```python
class Base(DeclarativeBase):
    pass

class Category(Base):
    __tablename__ = 'categories'
    ...

class Product(Base):
    __tablename__ = 'products'
    ...

# Теперь Base.metadata знает обо всех таблицах
print(Base.metadata.tables.keys())
# dict_keys(['categories', 'products'])
```

`Base.metadata` — это единая точка входа для операций со схемой:

```python
# Создать все таблицы одной командой
Base.metadata.create_all(engine)

# Удалить все таблицы
Base.metadata.drop_all(engine)
```

Если бы каждая модель наследовалась от `DeclarativeBase` напрямую — вам пришлось бы вызывать `create_all` для каждого класса отдельно и следить за порядком (сначала `categories`, потом `products` из-за внешнего ключа). SQLAlchemy бы потерял способность строить граф зависимостей автоматически.

### Что ещё получают классы-наследники

Когда класс наследуется от `Base` — он получает несколько вещей которые не видны явно но работают постоянно.

**Инструментированные атрибуты.** Каждый `Column` в классе заменяется специальным дескриптором. Именно поэтому ORM знает когда вы изменили атрибут:

```python
product = session.get(Product, 1)
product.price = 6000   # дескриптор фиксирует изменение

session.commit()
# ORM знает что изменился именно price — генерирует только:
# UPDATE products SET price = 6000 WHERE id = 1
# А не UPDATE для всех столбцов
```

Обычный Python-класс не умеет отслеживать присвоение атрибутов. `Base` встраивает этот механизм в каждую модель.

**Identity Map — кэш объектов.** Session помнит все загруженные объекты по их первичному ключу. Если вы дважды запросите `Product` с `id=1` в одной сессии — второй запрос вернёт тот же Python-объект из кэша без обращения к базе.

```python
with Session(engine) as session:
    p1 = session.get(Product, 1)
    p2 = session.get(Product, 1)   # нет SQL-запроса
    print(p1 is p2)   # True — это один и тот же объект
```

**Конструктор `__init__`.** `Base` генерирует конструктор который принимает значения столбцов как keyword-аргументы. Именно поэтому можно писать `Product(name='Ноутбук', price=75000)` без явного определения `__init__`.

**Связь с Session.** ORM отслеживает к какой сессии принадлежит объект, в каком он состоянии (new, persistent, detached) и нужно ли его синхронизировать с базой. Всё это работает потому что классы зарегистрированы в общем реестре через `Base`.

### Итог по `DeclarativeBase`

`Base` — не просто пустой класс для красоты. Это **общий реестр** всех моделей приложения. Единый `Base.metadata` позволяет SQLAlchemy видеть всю схему целиком: строить граф зависимостей для миграций, создавать таблицы в правильном порядке, понимать как модели связаны между собой через внешние ключи.

Паттерн выглядит избыточным для двух таблиц. Когда их двадцать — вы оцените что одна команда `Base.metadata.create_all(engine)` создаёт всё сразу в правильном порядке.

---

## Параметры Column — полный справочник

В примерах курса мы использовали только базовые параметры. На практике `Column` принимает значительно больше аргументов, каждый из которых решает конкретную задачу.

<details>
<summary>Подробнее о параметрах Column</summary>

### Типы данных

Первый аргумент `Column` — тип данных. Основные типы SQLAlchemy и их соответствие в SQL:

| SQLAlchemy тип | SQL тип | Когда использовать |
|---|---|---|
| `Integer` | INTEGER | Целые числа, id, счётчики |
| `String(n)` | VARCHAR(n) | Строки ограниченной длины |
| `Text` | TEXT | Длинные тексты без ограничения |
| `Float` | REAL / FLOAT | Числа с плавающей точкой |
| `Numeric(p, s)` | NUMERIC(p,s) | Деньги — точная арифметика |
| `Boolean` | BOOLEAN / INTEGER | True/False |
| `Date` | DATE | Только дата (2024-06-25) |
| `DateTime` | DATETIME | Дата и время |
| `JSON` | JSON / TEXT | JSON-данные (PostgreSQL, MySQL) |

> В наших проектах даты хранятся как `String(10)` в формате `YYYY-MM-DD` — это сознательное учебное упрощение. В продакшне используют `DateTime` или `Date` чтобы база данных сама следила за корректностью формата.

### Параметры Column

```python
Column(
    ТипДанных,          # Integer, String, Float и т.д.
    primary_key=False,  # является ли первичным ключом
    autoincrement=True, # автоинкремент (только для primary_key=True)
    nullable=True,      # может ли содержать NULL
    unique=False,       # должно ли значение быть уникальным в таблице
    default=None,       # значение по умолчанию на уровне Python/ORM
    server_default=None,# значение по умолчанию на уровне базы данных
    index=False,        # создать индекс для ускорения поиска
    comment='',         # комментарий к столбцу (для документации схемы)
    name='',            # имя столбца в БД если отличается от атрибута
)
```

Разберём каждый параметр подробнее.

---

**`primary_key=True`**

Делает столбец первичным ключом. SQLAlchemy автоматически добавляет `NOT NULL` и `UNIQUE`. Обычно используется вместе с `autoincrement=True`.

```python
id = Column(Integer, primary_key=True, autoincrement=True)
```

---

**`nullable=True/False`**

Определяет может ли столбец содержать `NULL`. По умолчанию `nullable=True` — NULL разрешён. Для обязательных полей нужно явно указывать `nullable=False`.

```python
name  = Column(String(200), nullable=False)   # обязательное
notes = Column(Text,        nullable=True)    # необязательное (можно не писать True)
```

---

**`unique=True`**

Гарантирует уникальность значений в столбце. Попытка вставить дубликат вызовет `IntegrityError`.

```python
email    = Column(String(200), nullable=False, unique=True)
username = Column(String(50),  nullable=False, unique=True)
```

---

**`default` vs `server_default`**

Это важное различие которое легко перепутать.

`default` — значение по умолчанию на уровне Python. Применяется когда вы создаёте объект через ORM и не указываете значение. До базы данных не доходит — Python подставляет его сам перед INSERT.

```python
status = Column(String(20), default='pending')

# При создании объекта:
order = Order(user_id=1)   # status не указан
# Python сам подставит 'pending' до отправки в базу
```

`server_default` — значение по умолчанию на уровне базы данных. Прописывается в схеме таблицы как `DEFAULT`. Работает даже при прямых SQL-запросах, без ORM. Для строковых значений нужно оборачивать в `text()`:

```python
from sqlalchemy import text

status     = Column(String(20), server_default='pending')
created_at = Column(DateTime,   server_default=text('CURRENT_TIMESTAMP'))
```

Когда использовать что:
- `default` — когда значение генерируется Python-кодом (например `datetime.now()` или UUID)
- `server_default` — когда значение должно проставляться базой данных всегда, в том числе при прямых SQL-запросах и миграциях

```python
# Типичный правильный вариант для created_at:
from sqlalchemy import DateTime, func

created_at = Column(DateTime, server_default=func.now(), nullable=False)
# func.now() — функция базы данных, работает везде
```

---

**`index=True`**

Создаёт индекс для столбца. Индекс — это дополнительная структура которую база данных строит для ускорения поиска. Запросы `WHERE email = ?` на таблице с миллионом строк без индекса — полный перебор. С индексом — мгновенный поиск.

```python
email = Column(String(200), nullable=False, unique=True, index=True)
# unique=True уже создаёт индекс — явный index=True здесь избыточен
# Но для неуникальных столбцов которые часто ищут — важен

city = Column(String(100), index=True)
# WHERE city = 'Москва' будет работать быстро даже на большой таблице
```

Правило: добавляйте `index=True` для столбцов которые часто используются в `WHERE`, `ORDER BY` или `JOIN`. Не для всех — индекс ускоряет чтение но замедляет запись.

---

**`comment`**

Текстовый комментарий к столбцу. Хранится в схеме базы данных и виден в инструментах просмотра БД. Полезен в командных проектах.

```python
price = Column(
    Float,
    nullable=False,
    comment='Цена в рублях без НДС'
)
```

---

**`name`**

Имя столбца в базе данных если оно отличается от имени атрибута в Python. Редко нужен, но полезен при работе с существующей базой где имена столбцов не совпадают с Python-конвенциями.

```python
# В Python: user.created_at
# В базе данных: столбец называется 'creation_date'
created_at = Column(DateTime, name='creation_date')
```

---

### Составные ограничения через `__table_args__`

Некоторые ограничения нельзя задать на уровне отдельного столбца — они касаются комбинации столбцов. Для этого используется атрибут класса `__table_args__`:

```python
from sqlalchemy import UniqueConstraint, CheckConstraint, Index

class OrderItem(Base):
    __tablename__ = 'order_items'
    __table_args__ = (
        # Один товар не может встречаться в одном заказе дважды
        UniqueConstraint('order_id', 'product_id', name='uq_order_product'),

        # Количество всегда положительное
        CheckConstraint('quantity > 0', name='ck_quantity_positive'),

        # Составной индекс для частого запроса по заказу и статусу
        Index('ix_order_status', 'order_id', 'status'),
    )

    id         = Column(Integer, primary_key=True)
    order_id   = Column(Integer, ForeignKey('orders.id'))
    product_id = Column(Integer, ForeignKey('products.id'))
    quantity   = Column(Integer, nullable=False)
    status     = Column(String(20))
```

`name=` в ограничениях — это имя которое появится в сообщении об ошибке при нарушении. `IntegrityError: UNIQUE constraint failed: uq_order_product` читается гораздо лучше чем безымянная ошибка.

---

</details>

### Быстрый справочник: когда что использовать

| Задача | Параметр |
|---|---|
| Поле обязательно для заполнения | `nullable=False` |
| Значение должно быть уникальным | `unique=True` |
| Значение по умолчанию в Python | `default=значение` |
| Значение по умолчанию в БД | `server_default=text('значение')` |
| Ускорить поиск по столбцу | `index=True` |
| Уникальность по паре столбцов | `UniqueConstraint` в `__table_args__` |
| Ограничение на значение | `CheckConstraint` в `__table_args__` |
| Добавить документацию к столбцу | `comment='описание'` |

---

## Engine и создание таблиц

```python
engine = create_engine('sqlite:///shop_orm.db', echo=False)

# Создать все таблицы описанные в моделях (если не существуют)
Base.metadata.create_all(engine)
```

`Base.metadata` — автоматически собирает информацию обо всех классах-моделях. `create_all` создаёт таблицы в правильном порядке с учётом зависимостей.

---

## Session — менеджер работы с БД

В ORM вы не работаете с `Connection` напрямую. Вместо этого используется **Session** — объект который отслеживает все изменения и управляет транзакцией.

```python
from sqlalchemy.orm import Session

# Создание сессии через контекстный менеджер
with Session(engine) as session:
    # Вся работа с БД здесь
    pass
    # При выходе — соединение возвращается в пул
```

Session отслеживает три состояния объектов:
- **New** — объект создан, но ещё не в БД (`session.add()` вызван, `commit()` — нет)
- **Persistent** — объект сохранён в БД и синхронизирован
- **Detached** — объект отсоединён от сессии (после закрытия сессии)

Если сравнивать `Connection` и `Session`, то:

`Connection` — низкоуровневый объект для выполнения SQL-запросов. Не знает про объекты-модели.

`Session` — высокоуровневый объект ORM. Отслеживает состояние объектов (new, persistent, detached), накапливает изменения через **unit of work** паттерн, управляет identity map (кэшем объектов). 

*Session использует Connection внутри себя.*

---

### Unit of Work — отслеживание изменений

Одной из ключевых возможностей ORM является автоматическое отслеживание изменений объектов.

За это отвечает паттерн **Unit of Work** ("единица работы").

Идея проста: пока объекты находятся внутри `Session`, SQLAlchemy запоминает все изменения, которые происходят с ними. Когда вызывается `session.commit()`, ORM анализирует накопленные изменения и самостоятельно решает какие SQL-запросы нужно выполнить:

* для новых объектов — `INSERT`
* для изменённых объектов — `UPDATE`
* для удалённых объектов — `DELETE`

Например:

```python
product = session.get(Product, 1)

product.price = 6000
product.name = 'Новый телефон'

session.commit()
```

Разработчик не пишет `UPDATE` вручную. SQLAlchemy сама определяет что объект был изменён и генерирует необходимый запрос.

Именно этот механизм автоматического отслеживания изменений называется **Unit of Work**.

---

### Instrumented Attributes — как ORM замечает изменения

Возникает вопрос: как SQLAlchemy понимает что объект был изменён?

Когда модель наследуется от `Base`, её поля становятся не обычными атрибутами Python, а специальными отслеживаемыми атрибутами — **instrumented attributes**.

Например:

```python
product.price = 6000
```

На первый взгляд выглядит как обычное присваивание.

Но на самом деле SQLAlchemy перехватывает эту операцию через специальный дескриптор:

1. Запоминает старое значение.
2. Сохраняет новое значение.
3. Помечает объект как изменённый (*dirty*).

После этого `Session` знает что объект нужно проверить при следующем `commit()`.

Упрощённо процесс выглядит так:

```text
product.price = 6000
        ↓
Instrumented Attribute
        ↓
Объект помечается как dirty
        ↓
session.commit()
        ↓
Unit of Work генерирует UPDATE
```

---

## CREATE — создание объектов

```python
with Session(engine) as session:

    # Создаём категорию
    electronics = Category(name='Электроника')
    session.add(electronics)

    # Создаём ещё одну
    books = Category(name='Книги')
    session.add(books)

    # Фиксируем изменения — оба INSERT выполняются здесь
    session.commit()

    # После commit id назначены базой данных
    print(electronics.id)   # 1
    print(books.id)         # 2
```

`session.add()` — говорит сессии "следи за этим объектом". Запрос в БД ещё не идёт.
`session.commit()` — генерирует `INSERT` и фиксирует транзакцию. После этого `id` доступен.

### Создание с автоматической связью

```python
with Session(engine) as session:

    # Категория
    peripherals = Category(name='Периферия')
    session.add(peripherals)
    session.flush()   # отправить INSERT без commit — нужен id

    # Товар — ссылается на только что созданную категорию
    mouse = Product(
        name='Мышь Logitech MX Master',
        price=5500.00,
        stock=50,
        category_id=peripherals.id   # id уже доступен после flush
    )
    session.add(mouse)
    session.commit()
```

`session.flush()` — отправляет изменения в БД без финального `commit`. Транзакция ещё открыта, но `id` уже назначен. Объекты получают id от базы данных, но изменения можно откатить через `rollback()`. 

Полезно когда нужен `id` для связанного объекта в той же транзакции. `commit()` — финализирует транзакцию, изменения необратимы.

### Создание через relationship

Можно добавить товар прямо в `category.products` — ORM сам установит `category_id`:

```python
with Session(engine) as session:
    keyboard = Category(name='Периферия')

    # Вместо установки category_id вручную — добавляем в коллекцию
    keyboard.products = [
        Product(name='Клавиатура Keychron K2', price=8900, stock=20),
        Product(name='Коврик SteelSeries',     price=2200, stock=60),
    ]

    session.add(keyboard)   # добавляем только категорию — товары подтянутся
    session.commit()
```

ORM сам установит `category_id` для каждого товара.

---

### Множественное сохранение объектов

```python
with Session(engine) as session:

    electronics = Category(
        name='Электроника',
        products=[
            Product(
                name='Ноутбук Lenovo ThinkPad',
                price=95000,
                stock=10
            ),
            Product(
                name='Монитор Dell UltraSharp',
                price=32000,
                stock=15
            ),
        ]
    )

    peripherals = Category(
        name='Периферия',
        products=[
            Product(
                name='Клавиатура Keychron K8',
                price=8500,
                stock=25
            ),
            Product(
                name='Мышь Logitech MX Master',
                price=5500,
                stock=50
            ),
        ]
    )

    session.add_all([electronics, peripherals])
    session.commit()
```

`session.add_all()` принимает список объектов и добавляет их в текущую сессию. При выполнении `commit()` SQLAlchemy анализирует связи между объектами и автоматически выполняет INSERT в правильном порядке.

---

## READ — чтение данных

### session.get() — по первичному ключу

Самый быстрый способ получить объект если знаете `id`:

```python
with Session(engine) as session:
    product = session.get(Product, 1)
    if product:
        print(product.name)    # Мышь Logitech MX Master
        print(product.price)   # 5500.0
    else:
        print('Товар не найден')
```

`session.get()` сначала проверяет кэш сессии (identity map) — если объект с этим `id` уже был загружен, повторного запроса к БД не будет.

### session.execute() с select() — гибкие запросы

Современный способ запросов в SQLAlchemy 2.x:

```python
from sqlalchemy import select

with Session(engine) as session:

    # Все товары
    stmt = select(Product)
    products = session.execute(stmt).scalars().all()
    for p in products:
        print(p.name, p.price)
```

`session.execute(stmt).all()` возвращает список `Row` объектов — строк результата. 

Если в `select` указана одна модель, каждая строка это `Row` содержащий один элемент. 

`.scalars()` извлекает первый элемент из каждой строки — получаем список объектов модели напрямую. При `select(Product)` и `.scalars().all()` результат `[Product1, Product2, ...]`, без `.scalars()` — `[(Product1,), (Product2,), ...]`.

### Фильтрация

```python
with Session(engine) as session:

    # Товары дороже 5000
    stmt = select(Product).where(Product.price > 5000)
    expensive = session.execute(stmt).scalars().all()

    # Товары конкретной категории
    stmt = select(Product).where(Product.category_id == 1)

    # Несколько условий
    stmt = select(Product).where(
        Product.price > 1000,
        Product.stock > 0       # запятая = AND
    )

    # IN
    stmt = select(Product).where(Product.category_id.in_([1, 2, 3]))

    # LIKE
    stmt = select(Product).where(Product.name.ilike('%ноутбук%'))
    # ilike — LIKE без учёта регистра
```

### Сортировка, LIMIT, OFFSET

```python
from sqlalchemy import desc

stmt = (
    select(Product)
    .order_by(desc(Product.price))
    .limit(5)
    .offset(10)
)
```

### Один объект

```python
# Первый результат или None
product = session.execute(
    select(Product).where(Product.name == 'Мышь Logitech MX Master')
).scalars().first()

# Ровно один — выбросит исключение если 0 или >1
product = session.execute(stmt).scalars().one()
```

---

### Получение + добавление

В отличие от предыдущих примеров, где категория и товары создавались одновременно, здесь категория уже существует в базе данных. Сначала она загружается через `session.get()` или `select()`, после чего к ней добавляются новые товары через relationship или путём явного указания `category_id`.

```python
with Session(engine) as session:

    # Получаем существующую категорию
    keyboard_category = session.get(Category, 2)   # по id
    # ИЛИ через запрос:
    stmt = select(Category).where(Category.name == 'Периферия')
    keyboard_category = session.execute(stmt).scalars().first()

    # Добавляем новые товары в уже существующую категорию
    new_products = [
        Product(name='Клавиатура Keychron K2', price=8900, stock=20),
        Product(name='Коврик SteelSeries',     price=2200, stock=60),
    ]

    # Способ 1 — через relationship
    keyboard_category.products.extend(new_products)

    # Способ 2 — добавить каждый товар напрямую с category_id
    for p in new_products:
        p.category_id = keyboard_category.id
        session.add(p)

    session.commit()
```

## UPDATE — обновление объектов

Самый простой способ: загрузить объект, изменить атрибут, сделать commit:

```python
with Session(engine) as session:
    product = session.get(Product, 1)
    if product:
        product.price = 6000.00   # просто присвоение
        product.stock = 45
        session.commit()   # ORM сам сгенерирует UPDATE
        print(f'Цена обновлена: {product.price}')
```

Session отслеживает изменения атрибутов — при `commit()` генерирует `UPDATE` только для изменённых столбцов. Это называется **unit of work** — паттерн накопления изменений.

### Массовое обновление

```python
from sqlalchemy import update

with Session(engine) as session:
    # UPDATE products SET price = price * 1.1 WHERE category_id = 1
    stmt = (
        update(Product)
        .where(Product.category_id == 1)
        .values(price=Product.price * 1.1)
    )
    result = session.execute(stmt)
    session.commit()
    print(f'Обновлено: {result.rowcount}')
```

---

## DELETE — удаление объектов

```python
with Session(engine) as session:
    product = session.get(Product, 1)
    if product:
        session.delete(product)
        session.commit()
```

### Массовое удаление

```python
from sqlalchemy import delete

with Session(engine) as session:
    stmt = delete(Product).where(Product.stock == 0)
    result = session.execute(stmt)
    session.commit()
    print(f'Удалено: {result.rowcount}')
```

---

## Связи: relationship и загрузка данных

Это один из главных плюсов ORM — работа со связанными объектами:

```python
with Session(engine) as session:
    category = session.get(Category, 1)
    print(category.name)        # Электроника
    print(category.products)    # список объектов Product
    for product in category.products:
        print(f'  {product.name}: {product.price}')
```

```python
with Session(engine) as session:
    product = session.get(Product, 3)
    print(product.name)           # Смартфон Samsung
    print(product.category.name)  # Электроника
```

Объект категории доступен через `product.category` — один запрос, никакого JOIN вручную.

### Ленивая загрузка (Lazy Loading) — поведение по умолчанию

По умолчанию `relationship` использует **lazy loading**: связанные объекты загружаются только в момент первого обращения к атрибуту.

```python
with Session(engine) as session:
    category = session.get(Category, 1)
    # SQL: SELECT * FROM categories WHERE id = 1
    # Пока products не запрошены — запроса за ними нет

    products = category.products
    # SQL: SELECT * FROM products WHERE category_id = 1
    # Запрос выполняется только здесь — в момент обращения
```

**Проблема ленивой загрузки — N+1**

Помните проблему N+1 из Урока 22? Вот как она выглядит с ORM:

```python
with Session(engine) as session:
    categories = session.execute(select(Category)).scalars().all()
    # SQL #1: SELECT * FROM categories

    for cat in categories:
        print(f'{cat.name}: {len(cat.products)} товаров')
        # SQL #2, #3, #4, #5, #6: отдельный SELECT для каждой категории
        # Итого: 1 + N запросов вместо одного JOIN
```

### Жадная загрузка (Eager Loading) — решение N+1

**`joinedload`** — загружает связанные объекты через JOIN в одном запросе:

```python
from sqlalchemy.orm import joinedload

with Session(engine) as session:
    stmt = select(Category).options(joinedload(Category.products))
    # SQL: SELECT categories.*, products.* FROM categories
    #      LEFT OUTER JOIN products ON categories.id = products.category_id

    categories = session.execute(stmt).unique().scalars().all()
    # .unique() — убирает дубликаты которые появляются при JOIN

    for cat in categories:
        print(f'{cat.name}: {len(cat.products)} товаров')
        # Никаких дополнительных запросов — данные уже загружены
```

*`joinedload()` не создаёт дубликаты сам по себе. Дубликаты появляются потому, что любой SQL JOIN размножает строки родительской таблицы при связи "один-ко-многим". Метод `.unique()` нужен, чтобы SQLAlchemy после JOIN вернула каждую родительскую сущность только один раз.*

*`.unique()` требуется именно в SQLAlchemy 2.0. В старых версиях ORM часто выполняла эту дедупликацию автоматически.*

**`selectinload`** — загружает связанные объекты отдельным `SELECT IN` запросом:

```python
from sqlalchemy.orm import selectinload

with Session(engine) as session:
    stmt = select(Category).options(selectinload(Category.products))
    # SQL #1: SELECT * FROM categories
    # SQL #2: SELECT * FROM products WHERE category_id IN (1, 2, 3, 4, 5)
    # Всего 2 запроса вместо N+1

    categories = session.execute(stmt).scalars().all()
```

**Когда что использовать:**
- `joinedload` — для связей "многие к одному" (`product.category`): один JOIN, один запрос
- `selectinload` — для связей "один ко многим" (`category.products`): избегает дублирования строк при JOIN с большими коллекциями

---

## Полная модель: shop_orm.py

Соберём все модели в один файл который будем использовать в финальном проекте:

```python
# shop_orm.py
from sqlalchemy import create_engine, Column, Integer, String, Float, Text, ForeignKey
from sqlalchemy.orm import DeclarativeBase, relationship, Session


class Base(DeclarativeBase):
    pass


class Category(Base):
    __tablename__ = 'categories'

    id       = Column(Integer, primary_key=True, autoincrement=True)
    name     = Column(String(100), nullable=False, unique=True)

    products = relationship('Product', back_populates='category',
                            cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Category {self.name!r}>'


class User(Base):
    __tablename__ = 'users'

    id         = Column(Integer, primary_key=True, autoincrement=True)
    name       = Column(String(200), nullable=False)
    email      = Column(String(200), nullable=False, unique=True)
    city       = Column(String(100), nullable=False)
    created_at = Column(String(10),  nullable=False)

    orders = relationship('Order', back_populates='user')

    def __repr__(self):
        return f'<User {self.name!r}>'


class Product(Base):
    __tablename__ = 'products'

    id          = Column(Integer, primary_key=True, autoincrement=True)
    name        = Column(String(200), nullable=False)
    price       = Column(Float,       nullable=False)
    stock       = Column(Integer,     nullable=False, default=0)
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=False)

    category    = relationship('Category', back_populates='products')
    order_items = relationship('OrderItem', back_populates='product')

    def __repr__(self):
        return f'<Product {self.name!r} price={self.price}>'


class Order(Base):
    __tablename__ = 'orders'

    id         = Column(Integer, primary_key=True, autoincrement=True)
    user_id    = Column(Integer, ForeignKey('users.id'), nullable=False)
    status     = Column(String(20), nullable=False, default='pending')
    created_at = Column(String(10), nullable=False)

    user  = relationship('User', back_populates='orders')
    items = relationship('OrderItem', back_populates='order',
                         cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Order #{self.id} status={self.status!r}>'


class OrderItem(Base):
    __tablename__ = 'order_items'

    id            = Column(Integer, primary_key=True, autoincrement=True)
    order_id      = Column(Integer, ForeignKey('orders.id'),   nullable=False)
    product_id    = Column(Integer, ForeignKey('products.id'), nullable=False)
    quantity      = Column(Integer, nullable=False, default=1)
    price_at_time = Column(Float,   nullable=False)

    order   = relationship('Order',   back_populates='items')
    product = relationship('Product', back_populates='order_items')

    def __repr__(self):
        return f'<OrderItem order={self.order_id} product={self.product_id} qty={self.quantity}>'
```

**`cascade='all, delete-orphan'`** — при удалении категории автоматически удаляются все её товары. При удалении заказа — все его позиции. Без cascade пришлось бы удалять вручную.

---

## CASCADE — что происходит при удалении связанных данных

Представьте: вы удаляете категорию «Электроника». Что должно произойти с товарами которые в неё входят? Это не риторический вопрос — база данных должна получить чёткий ответ. Без него она откажется удалять категорию, потому что товары ссылаются на неё через внешний ключ.

Это и есть задача CASCADE — определить что делать с дочерними записями когда родительская удаляется или изменяется.

### Варианты поведения

В SQL и SQLAlchemy есть несколько стратегий. Посмотрим на каждую через один и тот же сценарий: удаляем категорию.

**CASCADE (каскадное удаление)** — дочерние записи удаляются вместе с родительской.

```
Удалили категорию «Электроника»
    → Автоматически удалились все товары этой категории
```

```python
class Product(Base):
    category_id = Column(Integer, ForeignKey('categories.id', ondelete='CASCADE'))
```

Используется когда дочерние записи не имеют смысла без родительской. Товар без категории — бессмысленная запись.

**SET NULL** — внешний ключ в дочерних записях заменяется на `NULL`.

```
Удалили категорию «Электроника»
    → У товаров поле category_id стало NULL
    → Товары остались, но "без категории"
```

```python
class Product(Base):
    category_id = Column(Integer, ForeignKey('categories.id', ondelete='SET NULL'), nullable=True)
```

Используется когда дочерние записи могут существовать независимо. Например: удалили автора блога — его посты остаются, но поле `author_id` становится `NULL`.

**RESTRICT (или NO ACTION)** — запрещает удаление родительской записи если у неё есть дочерние.

```
Попытались удалить категорию «Электроника»
    → База данных: ОШИБКА. Сначала удалите или переместите все товары.
```

```python
class Product(Base):
    category_id = Column(Integer, ForeignKey('categories.id', ondelete='RESTRICT'))
```

Это поведение по умолчанию в большинстве СУБД когда `ondelete` не указан явно. Самое безопасное — вы не можете случайно удалить данные на которые кто-то ссылается.

**SET DEFAULT** — внешний ключ заменяется значением по умолчанию. Используется редко, в наших проектах не встречается.

### Два уровня CASCADE в SQLAlchemy

В SQLAlchemy CASCADE настраивается в двух местах и это важно понимать:

**Уровень базы данных** — через параметр `ondelete` в `ForeignKey`. Работает всегда, независимо от того используется ли SQLAlchemy. Даже если кто-то удалит запись прямым SQL-запросом — правило сработает.

```python
category_id = Column(Integer, ForeignKey('categories.id', ondelete='CASCADE'))
```

**Уровень ORM** — через параметр `cascade` в `relationship`. Работает только когда операция идёт через SQLAlchemy Session.

```python
class Category(Base):
    products = relationship('Product', back_populates='category',
                            cascade='all, delete-orphan')
```

`cascade='all, delete-orphan'` — наиболее полный вариант:
- `all` — операции сохранения, удаления, слияния применяются каскадно к дочерним объектам. Удаление удалит объект из коллекции Python
- `delete-orphan` — если товар убрать из `category.products` без явного удаления, ORM всё равно удалит его из базы (объект без "хозяина" — orphan — удаляется)

Если указать только `cascade='all'` без `delete-orphan`, то удаление объекта из коллекции не приведёт к удалению записи из базы. Объект останется существовать и его внешний ключ обычно будет установлен в `NULL` (если это допускается схемой БД).

### Что используем в учебных проектах и что в продакшне

**В учебных проектах** мы используем `cascade='all, delete-orphan'` в ORM и `ondelete='CASCADE'` в ForeignKey вместе. Это удобно: удалил одну запись — всё связанное автоматически подчистилось. Идеально для тестовых данных и экспериментов.

**В реальных проектах** выбор стратегии зависит от бизнес-логики:

- Удаляем пользователя → его заказы должны остаться для истории (архивирования, финансовой отчётности) — значит `SET NULL` или вообще запрет удаления
- Удаляем черновик поста → все его черновые комментарии можно удалить — `CASCADE`
- Удаляем товар из каталога → нельзя трогать исторические данные заказов — `RESTRICT`

Именно поэтому в `shop.db` мы храним `price_at_time` в `order_items` — цена товара могла измениться или товар мог быть удалён, но история заказа должна оставаться точной. В такой ситуации каскадное удаление товаров было бы катастрофой.

Общее правило в продакшне: **сначала `RESTRICT`, потом осознанно менять**. Лучше получить ошибку при попытке удалить нужные данные, чем молча потерять их через CASCADE.

## Практика: работа с shop.db через ORM

Подключимся к нашей уже существующей `shop.db`. 

Нужно создать [модели](#полная-модель-shop_ormpy) с `__tablename__` совпадающим с именами таблиц в БД и **не вызывать** `Base.metadata.create_all()` (чтобы не пересоздавать таблицы).

SQLAlchemy будет работать с существующими таблицами через модели (`autoload_with`). Это стандартный сценарий при добавлении ORM в проект с уже существующей БД:

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, DeclarativeBase

# Модели таблиц
...

# Подключаемся к существующей базе
engine = create_engine('sqlite:///shop.db')

# НЕ создаём таблицы заново — они уже есть
# Base.metadata.create_all(engine)  — не нужно

# Используем Session для запросов
with Session(engine) as session:

    # Все пользователи из Москвы
    from sqlalchemy import select
    stmt = select(User).where(User.city == 'Москва')
    moscow_users = session.execute(stmt).scalars().all()
    for u in moscow_users:
        print(u.name)

    # Пользователь с заказами (жадная загрузка)
    from sqlalchemy.orm import selectinload
    stmt = (
        select(User)
        .where(User.id == 1)
        .options(selectinload(User.orders))
    )
    user = session.execute(stmt).scalars().first()
    print(f'{user.name}: {len(user.orders)} заказов')
```

---

## Вопросы для закрепления

1. Что такое `DeclarativeBase` и зачем от него наследоваться?
2. Чем Session отличается от Connection в SQLAlchemy Core?
3. Зачем нужен `session.flush()` и чем он отличается от `session.commit()`?
4. Что такое ленивая загрузка и какую проблему она вызывает?
5. Чем `joinedload` отличается от `selectinload`?
6. Что означает `cascade='all, delete-orphan'` в relationship?
7. Как ORM знает какие столбцы изменились при `session.commit()`?
8. В чём разница между `session.execute(stmt).scalars().all()` и `session.execute(stmt).all()`?
9. Почему при `joinedload` нужен `.unique()` а при `selectinload` нет?
10. Можно ли использовать ORM-модели с существующей базой данных созданной через raw SQL?

---

## Задачи

### **Задача 1.** 

Создайте модели `Author` (id, name, country) и `Book` (id, title, year, author_id) в новой базе `library.db`. Создайте таблицы через `Base.metadata.create_all()`. Добавьте 2 авторов и по 2 книги каждому через Session.

---

### **Задача 2.** 

Используя модели из Задачи 1, получите все книги через `select(Book)` и выведите название и год. Затем получите конкретного автора через `session.get(Author, 1)` и выведите его книги через `relationship`.

---

### **Задача 3.** 

Загрузите всех авторов с их книгами за один запрос используя `selectinload`. Выведите для каждого автора количество книг. Сравните с вариантом без `selectinload` — посмотрите через `echo=True` сколько запросов выполняется.

---

### **Задача 4.** 

Подключитесь к `shop.db` из первого модуля. Используя ORM-модели (скопируйте из `shop_orm.py`), получите все товары дороже 10 000 рублей отсортированные по цене. Выведите название, цену и название категории через `joinedload`.

---

### **Задача 5.** 

Обновите цену всего одного товара через ORM (загрузить объект, изменить атрибут, commit). Затем сделайте массовое обновление через `update()` — поднимите цену всех товаров категории 4 на 10%. Используйте `echo=True` и сравните SQL который генерируется в обоих случаях.

---

### **Задача 6.** 

Используя `shop_orm.py`, получите пользователя с id=1 вместе с его заказами и позициями каждого заказа за минимальное количество запросов. Выведите структуру: пользователь → заказы → товары в каждом заказе.

---

[Предыдущий урок](lesson23.md) | [Следующий урок](lesson25.md)