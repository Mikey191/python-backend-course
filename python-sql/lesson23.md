# Урок 23. SQLAlchemy Core

## Два уровня SQLAlchemy

SQLAlchemy — это не один инструмент, а два уровня абстракции над базой данных:

```
┌─────────────────────────────────────────┐
│           SQLAlchemy ORM                │  ← Урок 24
│  Модели-классы, session, relationship   │
├─────────────────────────────────────────┤
│           SQLAlchemy Core               │  ← Этот урок
│  Table, MetaData, select/insert/update  │
├─────────────────────────────────────────┤
│              Engine / Connection        │  ← Общее для обоих
│     Пул соединений, диалекты СУБД       │
└─────────────────────────────────────────┘
```

**Core** — низкоуровневый слой. Вы описываете таблицы как объекты Python, пишете запросы через Python-выражения, но SQL генерируется и выполняется библиотекой. Близко к raw SQL, но с преимуществами: проверка имён столбцов, переносимость между СУБД, защита от инъекций.

**ORM** — высокоуровневый слой над Core. Таблицы становятся классами, строки — объектами, SQL генерируется полностью автоматически.

Мы начинаем с Core — это мост между тем что вы уже умеете (raw SQL) и тем куда идём (ORM). Core обнажает механику: видно что происходит, понятно что генерируется. ORM это скроет.

---

## Установка

```bash
pip install sqlalchemy
```

SQLAlchemy работает с SQLite без дополнительных драйверов — SQLite встроен в Python.

---

## Engine — соединение с базой данных

**Engine** — центральный объект SQLAlchemy. Управляет пулом соединений и знает диалект конкретной СУБД.

```python
from sqlalchemy import create_engine

# SQLite — путь к файлу
engine = create_engine('sqlite:///shop.db')

# SQLite — база в памяти (для тестов)
engine = create_engine('sqlite:///:memory:')

# PostgreSQL (для справки — в этом курсе не используем)
# engine = create_engine('postgresql://user:password@localhost/dbname')
```

Строка соединения имеет формат: `диалект://путь_или_хост/имя_базы`.

`echo=True` — полезная опция при разработке: SQLAlchemy будет печатать в консоль каждый генерируемый SQL-запрос:

```python
engine = create_engine('sqlite:///shop.db', echo=True)
```

Engine не открывает соединение немедленно — он делает это лениво при первом запросе.

---

## MetaData и Table — описание схемы

**MetaData** — контейнер для описания схемы базы данных. Хранит информацию обо всех таблицах: их имена, столбцы, типы, ограничения и связи между таблицами. 

Нужен для: создания таблиц через `create_all()`, отражения существующей схемы через `reflect()`, и как привязка для объектов `Table`.

**Table** — описание конкретной таблицы: столбцы, типы, ограничения.

```python
from sqlalchemy import create_engine, MetaData, Table, Column
from sqlalchemy import Integer, String, Float, Text, ForeignKey

engine = create_engine('sqlite:///shop.db', echo=True)
metadata = MetaData()

# Описание таблицы categories
categories = Table(
    'categories',     # имя таблицы в БД
    metadata,         # привязка к контейнеру схемы
    Column('id',   Integer, primary_key=True, autoincrement=True),
    Column('name', String,  nullable=False, unique=True),
)

# Описание таблицы products
products = Table(
    'products',
    metadata,
    Column('id',          Integer, primary_key=True, autoincrement=True),
    Column('name',        String,  nullable=False),
    Column('price',       Float,   nullable=False),
    Column('stock',       Integer, nullable=False, default=0),
    Column('category_id', Integer, ForeignKey('categories.id'), nullable=False),
)
```

`ForeignKey('categories.id')` — строкой указывается таблица и столбец. SQLAlchemy создаёт ссылочную связь.

### Создание таблиц

```python
# Создать все таблицы описанные в metadata (если не существуют)
metadata.create_all(engine)
```

`create_all` генерирует `CREATE TABLE IF NOT EXISTS` для каждой таблицы. Порядок создания SQLAlchemy определяет сам — `categories` будет создана раньше `products` потому что на неё есть внешний ключ.

### Отражение существующей схемы

Если база данных уже существует — можно загрузить схему из неё, не описывая вручную:

```python
# Загрузить описание таблиц из существующей БД
metadata.reflect(bind=engine)

# Теперь можно обращаться к таблицам
users_table = metadata.tables['users']
print(users_table.columns.keys())  # ['id', 'name', 'email', 'city', 'created_at']
```

Отражение полезно когда работаете с уже существующей базой — нашей `shop.db` из первых модулей.

---

## Connection — выполнение запросов

Для выполнения запросов нужно получить соединение из engine. Правильный способ — контекстный менеджер:

```python
with engine.connect() as connection:
    # Все запросы здесь
    result = connection.execute(...)
```

При выходе из блока `with` — соединение возвращается в пул (не закрывается физически, но освобождается).

**Engine** — фабрика соединений. Он управляет пулом соединений, знает диалект СУБД и параметры подключения. Сам по себе не выполняет запросы. 

**Connection** — активное соединение из пула, через которое выполняются конкретные запросы. Правильный паттерн: один Engine на приложение, Connection берётся из него через `with engine.connect()` на время запроса.

---

## SELECT через Core

Core предоставляет функцию `select()` для построения запросов:

```python
from sqlalchemy import select

with engine.connect() as connection:

    # SELECT * FROM categories
    stmt = select(categories)
    result = connection.execute(stmt)

    for row in result:
        print(row.id, row.name)
        # Доступ по имени столбца — как sqlite3.Row
```

### Выбор конкретных столбцов

```python
# SELECT name, price FROM products
stmt = select(products.c.name, products.c.price)
```

`products.c` — аксессор к столбцам таблицы (`c` от "columns"). `products.c.name` — конкретный столбец.

### WHERE

```python
from sqlalchemy import and_, or_

# SELECT * FROM products WHERE price > 10000
stmt = select(products).where(products.c.price > 10000)

# WHERE price > 1000 AND stock > 0
stmt = select(products).where(
    and_(products.c.price > 1000, products.c.stock > 0)
)

# WHERE category_id = 1 OR category_id = 2
stmt = select(products).where(
    products.c.category_id.in_([1, 2])
)

with engine.connect() as connection:
    result = connection.execute(stmt)
    rows = result.fetchall()
    for row in rows:
        print(row.name, row.price)
```

### ORDER BY и LIMIT

```python
from sqlalchemy import desc

# SELECT * FROM products ORDER BY price DESC LIMIT 5
stmt = (
    select(products)
    .order_by(desc(products.c.price))
    .limit(5)
)
```

### JOIN

```python
# SELECT products.name, categories.name AS category_name
# FROM products
# INNER JOIN categories ON products.category_id = categories.id

stmt = (
    select(
        products.c.name,
        products.c.price,
        categories.c.name.label('category_name')  # AS category_name
    )
    .join(categories, products.c.category_id == categories.c.id)
    .order_by(products.c.name)
)

with engine.connect() as connection:
    result = connection.execute(stmt)
    for row in result:
        print(f'{row.name} ({row.category_name}): {row.price} руб.')
```

`.label('category_name')` — аналог `AS category_name` в SQL. 

`.label('alias')` задаёт псевдоним для столбца или выражения в результате запроса. Генерирует `AS alias` в SQL. 

**Например**: `categories.c.name.label('category_name')` → `categories.name AS category_name`. Без label имя столбца может быть неудобным (особенно для агрегатов вроде `func.count()`).

### Агрегатные функции

```python
from sqlalchemy import func

# SELECT COUNT(*), AVG(price), MAX(price) FROM products
stmt = select(
    func.count().label('total'),
    func.avg(products.c.price).label('avg_price'),
    func.max(products.c.price).label('max_price')
)

with engine.connect() as connection:
    row = connection.execute(stmt).fetchone()
    print(f'Товаров: {row.total}')
    print(f'Средняя цена: {row.avg_price:.2f}')
    print(f'Максимальная: {row.max_price}')
```

---

## INSERT через Core

```python
from sqlalchemy import insert

# Один INSERT
stmt = insert(categories).values(name='Электроника')

with engine.connect() as connection:
    result = connection.execute(stmt)
    connection.commit()   # фиксируем изменения
    print(f'Создана категория с id={result.inserted_primary_key[0]}')
```

`result.inserted_primary_key` — кортеж с первичным ключом вставленной строки. Кортеж потому что первичный ключ может быть составным (несколько столбцов). 

Аналог `inserted_primary_key` из сырых запросов - `cursor.lastrowid`. Он только для автоинкремента, только одно число. 

`inserted_primary_key` работает корректно и для составных ключей, и не зависит от конкретного диалекта СУБД.

### Несколько строк за один INSERT

```python
# Аналог executemany — передаём список словарей
stmt = insert(categories)

with engine.connect() as connection:
    connection.execute(stmt, [
        {'name': 'Электроника'},
        {'name': 'Книги'},
        {'name': 'Одежда'},
    ])
    connection.commit()
```

---

## UPDATE через Core

```python
from sqlalchemy import update

# UPDATE products SET price = price * 1.1 WHERE category_id = 1
stmt = (
    update(products)
    .where(products.c.category_id == 1)
    .values(price=products.c.price * 1.1)
)

with engine.connect() as connection:
    result = connection.execute(stmt)
    connection.commit()
    print(f'Обновлено строк: {result.rowcount}')
```

`result.rowcount` — количество затронутых строк. Аналог `cursor.rowcount` в sqlite3.

---

## DELETE через Core

```python
from sqlalchemy import delete

# DELETE FROM products WHERE stock = 0
stmt = delete(products).where(products.c.stock == 0)

with engine.connect() as connection:
    result = connection.execute(stmt)
    connection.commit()
    print(f'Удалено товаров: {result.rowcount}')
```

---

## Транзакции

По умолчанию SQLAlchemy Core работает с автоматическим управлением транзакциями — каждый `execute` в контексте `begin()` образует транзакцию:

```python
# Явная транзакция через begin()
with engine.begin() as connection:
    # Все операции внутри одной транзакции
    connection.execute(insert(categories).values(name='Спорт'))
    connection.execute(
        insert(products).values(
            name='Гантели', price=2500, stock=10, category_id=...
        )
    )
    # commit() вызывается автоматически при выходе из with
    # При исключении — автоматический rollback
```

`engine.begin()` vs `engine.connect()`:
- `engine.connect()` — нужен явный вызов `connection.commit()` для фиксации изменений. Если забыть — изменения не сохранятся.
- `engine.begin()` — транзакция открывается автоматически. При успешном выходе из `with` — автоматический `commit`. При исключении — автоматический `rollback`.

*Для изменяющих операций предпочтительнее `engine.begin()`.*

---

## Почему Core ближе к SQL чем ORM

Посмотрим на соответствие Core и SQL:

| SQL | SQLAlchemy Core |
|---|---|
| `SELECT * FROM products` | `select(products)` |
| `WHERE price > 1000` | `.where(products.c.price > 1000)` |
| `ORDER BY price DESC` | `.order_by(desc(products.c.price))` |
| `INNER JOIN categories ON ...` | `.join(categories, ...)` |
| `INSERT INTO ... VALUES ...` | `insert(table).values(...)` |
| `UPDATE ... SET ... WHERE ...` | `update(table).where(...).values(...)` |
| `DELETE FROM ... WHERE ...` | `delete(table).where(...)` |

Структура один-в-один. Разница: вместо строки — Python-выражения с реальными объектами. SQLAlchemy знает имена столбцов — опечатка `products.c.nmae` даст ошибку немедленно, а не в рантайме.

### Что Core генерирует

С `echo=True` видно что SQLAlchemy генерирует:

```python
stmt = select(products).where(products.c.price > 10000)
```

Вывод в консоли:
```sql
SELECT products.id, products.name, products.price, products.stock, products.category_id
FROM products
WHERE products.price > :price_1
```

Параметр `:price_1` — SQLAlchemy автоматически параметризует все значения. Инъекция невозможна без усилий с вашей стороны.

---

## Работа с существующей базой shop.db

Подключимся к `shop.db` из первых модулей через Core:

```python
from sqlalchemy import create_engine, MetaData, select, func, desc, and_

# Подключаемся к существующей базе
engine = create_engine('sqlite:///shop.db', echo=False)
metadata = MetaData()

# Загружаем схему из существующей БД (reflect)
metadata.reflect(bind=engine)

# Получаем объекты таблиц
users     = metadata.tables['users']
products  = metadata.tables['products']
orders    = metadata.tables['orders']
categories = metadata.tables['categories']

# Запрос: топ-3 самых дорогих товара
stmt = (
    select(products.c.name, products.c.price)
    .order_by(desc(products.c.price))
    .limit(3)
)

with engine.connect() as connection:
    result = connection.execute(stmt)
    print('Топ-3 дорогих товара:')
    for row in result:
        print(f'  {row.name}: {row.price} руб.')
```

```python
# Запрос: количество товаров по категориям
stmt = (
    select(
        categories.c.name.label('category'),
        func.count(products.c.id).label('product_count')
    )
    .join(products, categories.c.id == products.c.category_id)
    .group_by(categories.c.name)
    .order_by(desc('product_count'))
)

with engine.connect() as connection:
    for row in connection.execute(stmt):
        print(f'  {row.category}: {row.product_count} товаров')
```

---

## Core vs raw sqlite3 — итоговое сравнение

```python
# --- Raw sqlite3 ---
cursor.execute(
    'SELECT p.name, c.name FROM products p '
    'JOIN categories c ON p.category_id = c.id '
    'WHERE p.price > ?',
    (10000,)
)

# --- SQLAlchemy Core ---
stmt = (
    select(products.c.name, categories.c.name)
    .join(categories, products.c.category_id == categories.c.id)
    .where(products.c.price > 10000)
)
connection.execute(stmt)
```

**Плюсы Core над raw sqlite3:**
- Имена столбцов — реальные объекты, IDE даёт автодополнение
- Параметризация — автоматическая, нельзя забыть
- Переносимость — один код работает с SQLite и PostgreSQL
- Синтаксис — Python-выражения вместо конкатенации строк

**Плюсы raw sqlite3 над Core:**
- Нет зависимости от SQLAlchemy
- Для простых скриптов — проще и понятнее
- Полный контроль над SQL

---

## Вопросы

1. Чем Engine отличается от Connection в SQLAlchemy?
2. Зачем нужен MetaData и что он хранит?
3. Что делает `metadata.reflect(bind=engine)` и когда это полезно?
4. Почему `products.c.nmae` даст ошибку сразу, а `cursor.execute('SELECT nmae FROM products')` — только при выполнении?
5. Чем `engine.begin()` отличается от `engine.connect()` по поведению транзакций?
6. Как SQLAlchemy Core защищает от SQL-инъекций?
7. Для чего используется `.label()` в запросе и что оно генерирует в SQL?
8. В чём преимущество Core над raw sqlite3 при смене SQLite на PostgreSQL?
9. Что вернёт `result.inserted_primary_key` после INSERT и почему это удобнее чем `cursor.lastrowid`?

---

## Задачи

Для задач используйте `shop.db` из первого модуля. Загружайте схему через `metadata.reflect(bind=engine)`.

---

### **Задача 1.** 

Подключитесь к `shop.db` через `create_engine` с `echo=True`. Выполните `SELECT * FROM categories` через Core и выведите названия всех категорий. Посмотрите в консоли какой SQL генерирует SQLAlchemy.

---

### **Задача 2.** 

Напишите запрос через Core: все товары дороже 5000 рублей, отсортированные по цене по убыванию. Выведите название и цену.

---

### **Задача 3.** 

Используя JOIN через Core, выведите список всех товаров с названием их категории. Используйте `.label()` для псевдонима столбца категории.

---

### **Задача 4.** 

Через Core получите количество товаров и среднюю цену в каждой категории. Используйте `func.count()`, `func.avg()`, `GROUP BY`. Округлите среднюю цену до 2 знаков через `func.round()`.

---

### **Задача 5.** 

Создайте новую базу `test.db` через Core: опишите таблицы `tags` (id, name UNIQUE) и `product_tags` (product_id, tag_id — составной первичный ключ). Создайте таблицы через `metadata.create_all()`. 

Вставьте 3 тега (новинка, скидка, хит продаж) и 2 связи product_tag (1, 1 и 1, 3) через INSERT.

---

### **Задача 6.** 

Через Core обновите цену всех товаров из категории с id=4 (книги): увеличьте на 15%. Выведите количество обновлённых строк через `result.rowcount`.

---

### **Задача 7.** 

Через Core удалите все товары с нулевым остатком (`stock = 0`). Сначала выведите их список через SELECT, потом удалите через DELETE. Используйте `engine.begin()` для транзакции.

---

### **Задача 8.** 

Сравните производительность: вставьте 1000 строк в таблицу через обычный цикл `execute()` и через один `execute()` со списком словарей. Замерьте время через `time.time()`. Используйте `sqlite:///:memory:` чтобы не засорять реальную базу.

---

[Предыдущий урок](lesson22.md) | [Следующий урок](lesson24.md)