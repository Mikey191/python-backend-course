# Урок 13. Функции для работы с БД

## От отдельных запросов к слою данных

К этому моменту у нас есть все инструменты: мы умеем подключаться к базе, выполнять запросы, параметризовать данные, генерировать тестовые записи. Но если представить реальное приложение — интернет-магазин, API, веб-сервис — становится понятно что запросы разбросаны по коду:

```python
# Где-то в одном файле
cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))

# Где-то в другом файле
cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))

# Ещё в одном месте
cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
```

Один и тот же запрос повторяется в разных местах. Если нужно изменить таблицу — придётся искать все места где она упоминается. Это хрупкий и неудобный код.

Решение — вынести всю SQL-логику в **отдельные функции**. Остальной код приложения не знает про SQL вообще: он просто вызывает `get_user_by_id(connection, 5)` и получает результат. Такой слой функций называют **слоем доступа к данным** (Data Access Layer).

---

## Почему соединение передаётся как параметр

Прежде чем писать функции — важный архитектурный вопрос: где создаётся соединение с базой?

### Плохой подход: соединение внутри функции

```python
def get_user_by_id(user_id):
    # Соединение открывается при каждом вызове
    with sqlite3.connect('shop.db') as connection:
        cursor = connection.cursor()
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        return cursor.fetchone()
```

Проблемы:
- Имя файла БД жёстко прописано внутри функции — при переименовании нужно менять каждую функцию
- Каждый вызов открывает и закрывает соединение — лишние накладные расходы
- Несколько функций в одной транзакции — невозможно: каждая живёт в своём соединении

### Правильный подход: соединение как параметр

```python
def get_user_by_id(connection, user_id):
    # Соединение создаётся снаружи и передаётся внутрь
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    return cursor.fetchone()
```

Соединение создаётся один раз на уровне вызывающего кода и передаётся в каждую функцию:

```python
with sqlite3.connect('shop.db') as connection:
    connection.row_factory = sqlite3.Row
    user   = get_user_by_id(connection, 1)
    orders = get_orders_by_user(connection, 1)
    # Обе функции работают в одном соединении и могут быть частью одной транзакции
```

Это даёт гибкость: функции не знают ни имени файла, ни как было открыто соединение — они просто используют то что им дали. Такой принцип называется **инверсия зависимостей** — зависимость (соединение) передаётся снаружи, а не создаётся внутри.

---

## Функции для таблицы users

Напишем полный набор функций для работы с пользователями. Это будет шаблон который потом повторится для каждой сущности.

### get_all — получить все записи

```python
def get_all_users(connection):
    """Возвращает список всех пользователей."""
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM users ORDER BY name')
    return cursor.fetchall()
```

```python
# Использование
with sqlite3.connect('shop.db') as connection:
    connection.row_factory = sqlite3.Row
    users = get_all_users(connection)
    for user in users:
        print(f'{user["id"]}. {user["name"]} — {user["city"]}')
```

### get_by_id — получить одну запись

```python
def get_user_by_id(connection, user_id):
    """Возвращает пользователя по id или None если не найден."""
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    return cursor.fetchone()
```

```python
user = get_user_by_id(connection, 5)
if user:
    print(f'Найден: {user["name"]}')
else:
    print('Пользователь не найден')
```

### create — создать запись

```python
def create_user(connection, name, email, city, created_at):
    """
    Создаёт нового пользователя.
    Возвращает id созданной записи или None при ошибке.
    """
    cursor = connection.cursor()
    try:
        cursor.execute(
            'INSERT INTO users (name, email, city, created_at) VALUES (?, ?, ?, ?)',
            (name, email, city, created_at)
        )
        return cursor.lastrowid   # id только что вставленной строки
    except sqlite3.IntegrityError:
        return None   # email уже существует
```

`cursor.lastrowid` — атрибут который содержит `id` последней вставленной строки. Это удобный способ узнать какой `id` назначила база данных.

```python
user_id = create_user(connection, 'Виктор Зубов', 'viktor@gmail.com', 'Москва', '2024-06-25')
if user_id:
    print(f'Пользователь создан с id={user_id}')
else:
    print('Ошибка: email уже занят')
```

### update — обновить запись

```python
def update_user_city(connection, user_id, new_city):
    """
    Обновляет город пользователя.
    Возвращает True если запись найдена и обновлена, False если нет.
    """
    cursor = connection.cursor()
    cursor.execute(
        'UPDATE users SET city = ? WHERE id = ?',
        (new_city, user_id)
    )
    return cursor.rowcount > 0   # rowcount — количество затронутых строк
```

`cursor.rowcount` — количество строк которые затронула последняя операция. Для `UPDATE` это количество обновлённых строк. Если `WHERE` не нашёл ни одной строки — `rowcount` будет `0`.

```python
success = update_user_city(connection, 5, 'Санкт-Петербург')
if success:
    print('Город обновлён')
else:
    print('Пользователь не найден')
```

### delete — удалить запись

```python
def delete_user(connection, user_id):
    """
    Удаляет пользователя по id.
    Возвращает True если запись была удалена, False если не найдена.
    """
    cursor = connection.cursor()
    cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
    return cursor.rowcount > 0
```

```python
if delete_user(connection, 16):
    print('Пользователь удалён')
else:
    print('Пользователь не найден')
```

---

## Функции с фильтрами и дополнительной логикой

Базовые CRUD-функции — это минимум. В реальном коде часто нужны выборки с фильтрами:

```python
def get_users_by_city(connection, city):
    """Возвращает пользователей из указанного города."""
    cursor = connection.cursor()
    cursor.execute(
        'SELECT * FROM users WHERE city = ? ORDER BY name',
        (city,)
    )
    return cursor.fetchall()


def search_users(connection, query):
    """Ищет пользователей по имени или email (частичное совпадение)."""
    cursor = connection.cursor()
    cursor.execute(
        'SELECT * FROM users WHERE name LIKE ? OR email LIKE ?',
        (f'%{query}%', f'%{query}%')
    )
    return cursor.fetchall()
```

---

## Несколько таблиц — функции с JOIN

Функции не ограничены одной таблицей. Запрос с JOIN — тот же принцип:

```python
def get_orders_with_users(connection):
    """Возвращает все заказы с именами пользователей."""
    cursor = connection.cursor()
    cursor.execute('''
        SELECT
            o.id        AS order_id,
            u.name      AS user_name,
            o.status,
            o.created_at
        FROM orders AS o
        INNER JOIN users AS u ON o.user_id = u.id
        ORDER BY o.created_at DESC
    ''')
    return cursor.fetchall()


def get_order_total(connection, order_id):
    """Возвращает итоговую сумму заказа."""
    cursor = connection.cursor()
    cursor.execute('''
        SELECT
            o.id,
            ROUND(SUM(oi.quantity * oi.price_at_time), 2) AS total
        FROM orders AS o
        INNER JOIN order_items AS oi ON o.id = oi.order_id
        WHERE o.id = ?
        GROUP BY o.id
    ''', (order_id,))
    row = cursor.fetchone()
    return row['total'] if row else None
```

---

## Функции и транзакции

Когда несколько операций должны выполниться как одна — функции передают одно соединение и транзакция охватывает все вызовы:

```python
def create_order(connection, user_id, items, created_at):
    """
    Создаёт заказ с позициями как одну атомарную операцию.
    items — список словарей: [{'product_id': 1, 'quantity': 2, 'price': 5000.0}, ...]
    Возвращает id созданного заказа.
    """
    cursor = connection.cursor()

    # Вставляем заказ
    cursor.execute(
        'INSERT INTO orders (user_id, status, created_at) VALUES (?, ?, ?)',
        (user_id, 'pending', created_at)
    )
    order_id = cursor.lastrowid

    # Вставляем позиции
    order_items = [
        (order_id, item['product_id'], item['quantity'], item['price'])
        for item in items
    ]
    cursor.executemany(
        'INSERT INTO order_items (order_id, product_id, quantity, price_at_time) VALUES (?, ?, ?, ?)',
        order_items
    )

    return order_id
```

```python
# Транзакция управляется снаружи через with
with sqlite3.connect('shop.db') as connection:
    connection.row_factory = sqlite3.Row

    items = [
        {'product_id': 1, 'quantity': 1, 'price': 75000.0},
        {'product_id': 7, 'quantity': 2, 'price': 5500.0},
    ]
    order_id = create_order(connection, user_id=3, items=items, created_at='2024-06-25')
    print(f'Заказ #{order_id} создан')
    # При выходе из with — автоматический commit
    # При исключении — автоматический rollback
```

Функция `create_order` не знает про транзакцию — она просто делает INSERT. Транзакция управляется снаружи. Это чистое разделение ответственности.

---

## Собираем всё вместе: db_utils.py

На практике функции для работы с БД выносят в отдельный модуль. Это и есть тот самый слой данных:

```python
# db_utils.py
import sqlite3


def get_connection(db_path='shop.db'):
    """Создаёт и возвращает настроенное соединение."""
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    return connection


# --- Users ---

def get_all_users(connection):
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM users ORDER BY name')
    return cursor.fetchall()


def get_user_by_id(connection, user_id):
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    return cursor.fetchone()


def create_user(connection, name, email, city, created_at):
    cursor = connection.cursor()
    try:
        cursor.execute(
            'INSERT INTO users (name, email, city, created_at) VALUES (?, ?, ?, ?)',
            (name, email, city, created_at)
        )
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        return None


def update_user_city(connection, user_id, new_city):
    cursor = connection.cursor()
    cursor.execute('UPDATE users SET city = ? WHERE id = ?', (new_city, user_id))
    return cursor.rowcount > 0


def delete_user(connection, user_id):
    cursor = connection.cursor()
    cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
    return cursor.rowcount > 0


# --- Products ---

def get_all_products(connection):
    cursor = connection.cursor()
    cursor.execute('''
        SELECT p.*, c.name AS category_name
        FROM products AS p
        INNER JOIN categories AS c ON p.category_id = c.id
        ORDER BY p.name
    ''')
    return cursor.fetchall()


def get_product_by_id(connection, product_id):
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM products WHERE id = ?', (product_id,))
    return cursor.fetchone()


def create_product(connection, name, price, stock, category_id):
    cursor = connection.cursor()
    cursor.execute(
        'INSERT INTO products (name, price, stock, category_id) VALUES (?, ?, ?, ?)',
        (name, price, stock, category_id)
    )
    return cursor.lastrowid


def update_product_stock(connection, product_id, new_stock):
    cursor = connection.cursor()
    cursor.execute('UPDATE products SET stock = ? WHERE id = ?', (new_stock, product_id))
    return cursor.rowcount > 0


def delete_product(connection, product_id):
    cursor = connection.cursor()
    cursor.execute('DELETE FROM products WHERE id = ?', (product_id,))
    return cursor.rowcount > 0


# --- Orders ---

def get_orders_with_users(connection):
    cursor = connection.cursor()
    cursor.execute('''
        SELECT o.id AS order_id, u.name AS user_name, o.status, o.created_at
        FROM orders AS o
        INNER JOIN users AS u ON o.user_id = u.id
        ORDER BY o.created_at DESC
    ''')
    return cursor.fetchall()


def create_order(connection, user_id, items, created_at):
    cursor = connection.cursor()
    cursor.execute(
        'INSERT INTO orders (user_id, status, created_at) VALUES (?, ?, ?)',
        (user_id, 'pending', created_at)
    )
    order_id = cursor.lastrowid
    order_items = [
        (order_id, item['product_id'], item['quantity'], item['price'])
        for item in items
    ]
    cursor.executemany(
        'INSERT INTO order_items (order_id, product_id, quantity, price_at_time) VALUES (?, ?, ?, ?)',
        order_items
    )
    return order_id
```

```python
# main.py — использование модуля
from db_utils import get_connection, get_all_users, create_user, get_orders_with_users

with get_connection('shop.db') as connection:
    # Читаем пользователей
    users = get_all_users(connection)
    print(f'Пользователей: {len(users)}')

    # Создаём нового
    user_id = create_user(connection, 'Новый Пользователь', 'new@test.ru', 'Омск', '2024-06-26')
    print(f'Создан пользователь id={user_id}')

    # Читаем заказы
    orders = get_orders_with_users(connection)
    for order in orders[:3]:
        print(f'Заказ #{order["order_id"]} — {order["user_name"]} — {order["status"]}')
```

Код в `main.py` не содержит ни одной SQL-строки. Он работает с данными через функции — это и есть разделение слоёв.

---

## Вопросы для закрепления

1. Что такое слой доступа к данным и какую проблему он решает?
2. Почему соединение передаётся в функцию как параметр, а не создаётся внутри?
3. Что возвращает `cursor.lastrowid` и когда это полезно?
4. Что такое `cursor.rowcount` и для каких операций он полезен?
5. Функция `create_user` возвращает `None` при `IntegrityError`. Это хороший подход?
6. Почему в функции `create_order` транзакция не управляется внутри самой функции?
7. Можно ли создать один курсор на уровне модуля и использовать его во всех функциях?
8. Как функция `get_user_by_id` должна вести себя если пользователь не найден?
9. Зачем выносить функцию `get_connection()` в `db_utils.py` если она просто вызывает `sqlite3.connect()`?
10. Как изменится код в `main.py` если переименовать таблицу `users` в `accounts`?

---

## Задачи

### **Задача 1.** 

Напишите функцию `get_all_categories(connection)` которая возвращает все категории из таблицы `categories`. Вызовите её и выведите результат.

---

### **Задача 2.** 

Напишите функцию `get_product_by_id(connection, product_id)` которая возвращает товар по `id` или `None`. Проверьте оба случая: существующий `id` и несуществующий.

---

### **Задача 3.** 

Напишите функцию `create_product(connection, name, price, stock, category_id)` которая создаёт товар и возвращает его `id`. Используйте `cursor.lastrowid`.

---

### **Задача 4.** 

Напишите функцию `update_product_price(connection, product_id, new_price)` которая обновляет цену товара. Используйте `cursor.rowcount` чтобы вернуть `True` при успехе и `False` если товар не найден.

---

### **Задача 5.** 

Напишите функцию `delete_product(connection, product_id)` которая удаляет товар. Верните `True` если удалён, `False` если не найден. Проверьте оба случая.

---

### **Задача 6.** 

Напишите функцию `get_products_by_category(connection, category_id)` которая возвращает товары из указанной категории отсортированные по цене. Проверьте для двух разных категорий.

---

### **Задача 7.** 

Напишите функцию `get_user_orders(connection, user_id)` которая возвращает все заказы пользователя с суммой каждого заказа. Используйте JOIN с `order_items`.

---

### **Задача 8.** 

Создайте файл `db_utils.py` с функциями `get_connection`, `get_all_users`, `get_user_by_id`, `create_user`, `update_user_city`, `delete_user`. В `main.py` импортируйте их и выполните полный CRUD-цикл: создать пользователя, получить его, обновить город, удалить.

---

[Предыдущий урок](lesson12.md) | [Следующий урок](lesson14.md)