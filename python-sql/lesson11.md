# Урок 11. Параметризованные запросы и безопасность

## Проблема: данные в строке запроса

В прошлом уроке мы выполняли запросы передавая SQL как обычную строку Python. Первый инстинкт при подстановке данных — использовать f-строку или конкатенацию:

```python
# Поиск пользователя по имени введённому пользователем
user_input = 'Алексей Смирнов'
query = f"SELECT * FROM users WHERE name = '{user_input}'"
cursor.execute(query)
```

Выглядит логично. Но это одна из самых опасных ошибок в работе с базами данных. Разберём почему.

---

## SQL-инъекция

**SQL-инъекция** — атака при которой злоумышленник передаёт в поле ввода не данные, а фрагмент SQL-кода. Этот код встраивается в запрос и выполняется базой данных.

Посмотрим на конкретный пример. Есть форма входа — пользователь вводит email:

```python
# Небезопасный код
email_input = input('Введите email: ')
query = f"SELECT * FROM users WHERE email = '{email_input}'"
cursor.execute(query)
```

При обычном вводе запрос выглядит корректно:

```sql
SELECT * FROM users WHERE email = 'alice@mail.ru'
```

Но злоумышленник вводит не email, а специально сконструированную строку:

```
' OR '1'='1
```

После подстановки запрос становится:

```sql
SELECT * FROM users WHERE email = '' OR '1'='1'
```

Условие `'1'='1'` всегда истинно — запрос вернёт **всех** пользователей из таблицы. Это утечка данных.

Другой пример — ввод который уничтожает данные:

```
'; DELETE FROM users; --
```

После подстановки:

```sql
SELECT * FROM users WHERE email = ''; DELETE FROM users; --'
```

Первый запрос выполняется, потом `DELETE FROM users` удаляет всех пользователей. `--` — комментарий в SQL, он "отрезает" хвост исходного запроса.

> SQL-инъекции входят в список OWASP Top 10 — десятку наиболее критичных уязвимостей веб-приложений. Это не академическая угроза — реальные взломы с утечками миллионов записей происходили именно через инъекции в местах где разработчики подставляли данные напрямую в строку запроса.

### Почему конкатенация строк опасна

Корень проблемы прост: при конкатенации Python не различает "это данные" и "это SQL-код". Всё становится единой строкой которую СУБД интерпретирует как команду. Злоумышленник управляет тем что попадёт в эту строку.

```python
# Все эти способы подстановки — небезопасны:
query = "SELECT * FROM users WHERE email = '" + email + "'"        # конкатенация
query = f"SELECT * FROM users WHERE email = '{email}'"              # f-строка
query = "SELECT * FROM users WHERE email = '%s'" % email            # %
```

Ни один из них не защищает от инъекции.

---

## Параметризованные запросы

Решение — **параметризованные запросы**: данные передаются отдельно от SQL-кода. СУБД получает запрос и данные как два независимых объекта — данные никогда не интерпретируются как код.

### Позиционные параметры — знак `?`

В SQLite параметры обозначаются знаком `?`. Значения передаются вторым аргументом `execute()` в виде кортежа:

```python
import sqlite3

with sqlite3.connect('shop.db') as connection:
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    email = 'alexey@gmail.com'
    cursor.execute('SELECT name, city FROM users WHERE email = ?', (email,))

    row = cursor.fetchone()
    if row:
        print(f'{row["name"]} — {row["city"]}')
```

Обратите внимание на `(email,)` — кортеж с одним элементом. Запятая обязательна: `(email)` — это просто переменная в скобках, не кортеж.

Теперь при любом вводе инъекция невозможна:

```python
# Злоумышленник передаёт вредоносную строку
evil_input = "' OR '1'='1"

cursor.execute('SELECT name FROM users WHERE email = ?', (evil_input,))
# СУБД воспримет evil_input как строку-данные, а не как SQL-код
# Запрос вернёт пустой результат — пользователя с таким email нет
```

`?` — это место для одного значения. Несколько параметров — несколько `?`:

```python
cursor.execute(
    'SELECT name FROM users WHERE city = ? AND created_at > ?',
    ('Москва', '2024-01-01')
)
```

Количество `?` должно точно совпадать с количеством элементов в кортеже.

### Именованные параметры — `:name`

Альтернативный синтаксис — именованные параметры через `:имя`. Значения передаются словарём:

```python
cursor.execute(
    'SELECT name FROM users WHERE city = :city AND created_at > :date',
    {'city': 'Москва', 'date': '2024-01-01'}
)
```

Именованные параметры удобнее когда:
- Параметров много и сложно отследить порядок
- Одно и то же значение используется несколько раз в запросе
- Запрос передаётся через словарь из формы или API

```python
# Одно значение используется дважды — с именованным параметром не дублируем
params = {'min_price': 5000}
cursor.execute(
    '''SELECT name, price FROM products
       WHERE price > :min_price
       ORDER BY price''',
    params
)
```

### Параметры только для значений

Параметры `?` и `:name` работают только для **значений данных** — строк, чисел, дат. Нельзя параметризовать имена таблиц, столбцов или ключевые слова SQL:

```python
# Так не работает — нельзя параметризовать имя таблицы
cursor.execute('SELECT * FROM ?', ('products',))   # ошибка

# Если имя таблицы динамическое — только белый список:
allowed_tables = {'products', 'users', 'orders'}
table_name = 'products'  # значение из внешнего источника

if table_name in allowed_tables:
    cursor.execute(f'SELECT * FROM {table_name}')  # безопасно — проверено
else:
    raise ValueError(f'Недопустимое имя таблицы: {table_name}')
```

---

## executemany() — массовые операции

`executemany()` выполняет один запрос многократно — для каждого набора параметров из переданного списка. Это значительно эффективнее чем вызывать `execute()` в цикле.

```python
cursor.executemany(запрос, список_кортежей)
```

### Вставка нескольких строк

```python
import sqlite3

new_products = [
    ('Коврик для мыши', 900.00, 30, 2),
    ('Подставка для телефона', 600.00, 25, 2),
    ('USB-хаб 4 порта', 1200.00, 15, 2),
]

with sqlite3.connect('shop.db') as connection:
    cursor = connection.cursor()
    cursor.executemany(
        'INSERT INTO products (name, price, stock, category_id) VALUES (?, ?, ?, ?)',
        new_products
    )
# commit() вызовется автоматически при выходе из with
```

Вместо трёх отдельных `execute()` — один `executemany()`. СУБД обрабатывает всё как одну операцию, что быстрее и атомарнее.

### executemany() со списком словарей

Если данные приходят как список словарей (например из API или CSV) — используем именованные параметры:

```python
users_data = [
    {'name': 'Виктор Зубов',   'email': 'viktor@gmail.com',  'city': 'Москва',    'created_at': '2024-06-25'},
    {'name': 'Олег Кириллов',  'email': 'oleg@mail.ru',      'city': 'Казань',    'created_at': '2024-06-26'},
    {'name': 'Юлия Фёдорова',  'email': 'julia@yandex.ru',   'city': 'Самара',    'created_at': '2024-06-27'},
]

with sqlite3.connect('shop.db') as connection:
    cursor = connection.cursor()
    cursor.executemany(
        '''INSERT INTO users (name, email, city, created_at)
           VALUES (:name, :email, :city, :created_at)''',
        users_data
    )
```

### executemany() для UPDATE и DELETE

`executemany()` работает с любой изменяющей операцией — не только с `INSERT`:

```python
# Обновить остаток для нескольких товаров
stock_updates = [
    (100, 1),   # stock=100, id=1
    (50,  7),   # stock=50,  id=7
    (25,  9),   # stock=25,  id=9
]

with sqlite3.connect('shop.db') as connection:
    cursor = connection.cursor()
    cursor.executemany(
        'UPDATE products SET stock = ? WHERE id = ?',
        stock_updates
    )
```

### executemany() для SELECT-запросов

Использование SELECT-запросов технически возможно, но это бессмысленно — каждый следующий `execute` перезаписывает результат предыдущего в курсоре, и получить все результаты не выйдет. 

`executemany()` предназначен для изменяющих операций: `INSERT`, `UPDATE`, `DELETE`. Для множественных `SELECT` с разными параметрами используют цикл с `execute()` и сбором результатов.

### Производительность: execute() vs executemany()

```python
import sqlite3
import time

data = [(f'Товар {i}', float(i * 100), i % 50, 1) for i in range(1000)]

# Способ 1: execute() в цикле
start = time.time()
with sqlite3.connect(':memory:') as conn:
    conn.execute('CREATE TABLE t (name TEXT, price REAL, stock INT, cat_id INT)')
    for row in data:
        conn.execute('INSERT INTO t VALUES (?, ?, ?, ?)', row)
print(f'execute() в цикле: {time.time() - start:.3f} сек')

# Способ 2: executemany()
start = time.time()
with sqlite3.connect(':memory:') as conn:
    conn.execute('CREATE TABLE t (name TEXT, price REAL, stock INT, cat_id INT)')
    conn.executemany('INSERT INTO t VALUES (?, ?, ?, ?)', data)
print(f'executemany():     {time.time() - start:.3f} сек')

# executemany() быстрее — особенно заметно при сотнях и тысячах строк
```

---

## Правила безопасной работы с запросами

Подведём итог в виде практических правил:

**1. Всегда используйте параметры — никогда не вставляйте данные в строку запроса:**
```python
# Плохо
cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")

# Хорошо
cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
```

**2. Для одной вставки — `execute()`, для нескольких — `executemany()`:**
```python
# Плохо: цикл с execute()
for item in items:
    cursor.execute('INSERT INTO ...', item)

# Хорошо: один executemany()
cursor.executemany('INSERT INTO ...', items)
```

**3. Динамические имена таблиц и столбцов — только через белый список:**
```python
ALLOWED_COLUMNS = {'name', 'price', 'stock'}

if column not in ALLOWED_COLUMNS:
    raise ValueError(f'Недопустимый столбец: {column}')

cursor.execute(f'SELECT {column} FROM products')
```

**4. Всегда обрабатывайте `IntegrityError` при вставке данных из внешних источников:**
```python
try:
    cursor.execute('INSERT INTO users ...', data)
except sqlite3.IntegrityError:
    # email уже существует — это ожидаемо, обрабатываем
    pass
```

---

## Вопросы

1. Что такое SQL-инъекция и почему она опасна?
2. Почему f-строки и конкатенация строк опасны при построении SQL-запросов?
3. Почему при одном параметре пишут `(value,)` с запятой, а не `(value)`?
4. В чём разница между `?` и `:name` в параметризованных запросах?
5. Можно ли параметризовать имя таблицы или столбца?
6. Чем `executemany()` лучше `execute()` в цикле?
7. Нужно ли вызывать `commit()` после `executemany()`?
8. Что произойдёт если количество `?` в запросе не совпадает с количеством элементов в кортеже?
9. Злоумышленник вводит `'; DROP TABLE users; --` в поле поиска. Что произойдёт если запрос параметризован? А если нет?
10. Можно ли использовать `executemany()` для `SELECT`-запросов?

---

## Задачи

### **Задача 1.** 

Напишите функцию `get_user_by_email(connection, email)` которая принимает соединение и email, возвращает строку пользователя или `None`. Используйте параметризованный запрос с `?`.

---

### **Задача 2.** 

Напишите функцию `get_products_by_price_range(connection, min_price, max_price)` которая возвращает список товаров в заданном ценовом диапазоне. Используйте два параметра `?`.

---

### **Задача 3.** 

Напишите функцию `search_products(connection, keyword)` которая ищет товары по ключевому слову в названии. Используйте параметр `?` с символом `%` для `LIKE`.

---

### **Задача 4.** 

Используя именованные параметры `:name`, напишите запрос который ищет заказы по статусу и дате (позже заданной). Передайте параметры словарём.

---

### **Задача 5.** 

Создайте список из 5 новых категорий и вставьте их одним `executemany()`. Проверьте результат через `SELECT COUNT(*)`.

**Пример списка**:

```python
new_categories = [
    ('Спорт',),
    ('Игрушки',),
    ('Канцелярия',),
    ('Продукты',),
    ('Автотовары',),
]
```

---

### **Задача 6.** 

Создайте список словарей с данными трёх пользователей и вставьте их через `executemany()` с именованными параметрами. Обработайте `IntegrityError` если email уже существует.

**Пример списка**:

```python
new_users = [
    {'name': 'Виктор Зубов',  'email': 'viktor@gmail.com', 'city': 'Москва',  'created_at': '2024-06-25'},
    {'name': 'Олег Кириллов', 'email': 'oleg@mail.ru',     'city': 'Казань',  'created_at': '2024-06-26'},
    {'name': 'Юлия Фёдорова', 'email': 'alexey@gmail.com', 'city': 'Самара',  'created_at': '2024-06-27'},
]
```

---

### **Задача 7.** 

Напишите функцию `bulk_update_stock(connection, updates)` которая принимает список кортежей `(новый_остаток, id_товара)` и обновляет остатки через `executemany()`.

**Пример списка**:

```python
updates = [(50, 1), (30, 2), (100, 7)]
```

---

### **Задача 8.** 

Напишите функцию `get_orders_by_status(connection, status)` с проверкой что статус входит в список допустимых значений. Если статус недопустим — выбросить `ValueError`. Для допустимых использовать параметризованный запрос.

**Пример допустимых данных**:

```python
ALLOWED_STATUSES = {'pending', 'shipped', 'delivered', 'cancelled'}
```

---

### **Задача 9.** 

Напишите скрипт который генерирует 20 тестовых товаров через list comprehension и вставляет их одним `executemany()`. Замерьте время выполнения через `time.time()` и сравните с вставкой тех же данных через `execute()` в цикле. Используйте `:memory:` чтобы не засорять реальную базу тестовыми данными.

**Пример генератора для генерации данных**:

```python
data = [
    (f'Тестовый товар {i}', float(i * 50 + 100), i % 30 + 1, (i % 5) + 1)
    for i in range(20)
]
```

---

[Предыдущий урок](lesson10.md) | [Следующий урок](lesson12.md)