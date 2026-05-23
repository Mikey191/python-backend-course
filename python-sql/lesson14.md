# Урок 14. Классы-репозитории

## От функций к классам

В прошлом уроке мы выстроили слой данных из функций. Код стал чище — SQL изолирован в `db_utils.py`, `main.py` не знает про SQL вообще. Но если посмотреть на `db_utils.py` внимательнее, видна закономерность:

```python
def get_all_users(connection): ...
def get_user_by_id(connection, user_id): ...
def create_user(connection, name, email, city, created_at): ...
def update_user_city(connection, user_id, new_city): ...
def delete_user(connection, user_id): ...

def get_all_products(connection): ...
def get_product_by_id(connection, product_id): ...
def create_product(connection, name, price, stock, category_id): ...
def update_product_stock(connection, product_id, new_stock): ...
def delete_product(connection, product_id): ...
```

Все функции для пользователей принимают одинаковый первый параметр — `connection`. Все функции для товаров — тоже. Это сигнал: группа функций которые работают с одним объектом и разделяют одно состояние — это кандидат на класс.

Именно здесь ООП решает конкретную задачу: `connection` становится атрибутом класса, а функции — методами. Повторяющийся параметр исчезает.

---

## Паттерн Repository

**Repository** (Репозиторий) — паттерн проектирования который изолирует логику доступа к данным за интерфейсом коллекции. Остальной код приложения видит репозиторий как обычный объект у которого можно попросить данные или сохранить их — без знания о том что внутри SQL и SQLite.

Ключевые идеи паттерна:
- **Один репозиторий — одна сущность.** `UserRepository` работает только с пользователями, `ProductRepository` — только с товарами
- **Интерфейс похож на коллекцию.** `get_all()`, `get_by_id()`, `create()`, `update()`, `delete()` — стандартный набор методов
- **Детали реализации скрыты.** Вызывающий код не знает что внутри — SQLite, PostgreSQL или вообще файл

---

## Первый репозиторий: UserRepository

Перепишем функции для пользователей из прошлого урока в класс:

```python
import sqlite3


class UserRepository:

    def __init__(self, connection):
        self.connection = connection

    def get_all(self):
        """Возвращает всех пользователей."""
        cursor = self.connection.cursor()
        cursor.execute('SELECT * FROM users ORDER BY name')
        return cursor.fetchall()

    def get_by_id(self, user_id):
        """Возвращает пользователя по id или None."""
        cursor = self.connection.cursor()
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        return cursor.fetchone()

    def create(self, name, email, city, created_at):
        """
        Создаёт пользователя.
        Возвращает id созданной записи или None при ошибке.
        """
        cursor = self.connection.cursor()
        try:
            cursor.execute(
                'INSERT INTO users (name, email, city, created_at) VALUES (?, ?, ?, ?)',
                (name, email, city, created_at)
            )
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            return None

    def update_city(self, user_id, new_city):
        """Обновляет город. Возвращает True если пользователь найден."""
        cursor = self.connection.cursor()
        cursor.execute(
            'UPDATE users SET city = ? WHERE id = ?',
            (new_city, user_id)
        )
        return cursor.rowcount > 0

    def delete(self, user_id):
        """Удаляет пользователя. Возвращает True если запись была."""
        cursor = self.connection.cursor()
        cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
        return cursor.rowcount > 0
```

Сравним с функциями из прошлого урока:

```python
# Было: функция
get_user_by_id(connection, user_id)

# Стало: метод репозитория
user_repo.get_by_id(user_id)
```

`connection` больше не передаётся при каждом вызове — он хранится в `self.connection` и используется всеми методами автоматически. Код вызова стал короче и читаемее.

---

## Использование репозитория

```python
import sqlite3
from repositories import UserRepository   # предположим что класс в отдельном файле

with sqlite3.connect('shop.db') as connection:
    connection.row_factory = sqlite3.Row
    users = UserRepository(connection)

    # Create
    user_id = users.create('Виктор Зубов', 'viktor@gmail.com', 'Москва', '2024-06-25')
    print(f'Создан пользователь: id={user_id}')

    # Read
    user = users.get_by_id(user_id)
    print(f'Найден: {user["name"]} — {user["city"]}')

    # Update
    users.update_city(user_id, 'Санкт-Петербург')
    user = users.get_by_id(user_id)
    print(f'Город обновлён: {user["city"]}')

    # Delete
    users.delete(user_id)
    print(f'После удаления: {users.get_by_id(user_id)}')  # None
```

Код читается почти как обычный русский текст: `users.create(...)`, `users.get_by_id(...)`, `users.delete(...)`.

---

## Второй репозиторий: ProductRepository

По той же схеме — репозиторий для товаров:

```python
class ProductRepository:

    def __init__(self, connection):
        self.connection = connection

    def get_all(self):
        """Возвращает все товары с названием категории."""
        cursor = self.connection.cursor()
        cursor.execute('''
            SELECT p.*, c.name AS category_name
            FROM products AS p
            INNER JOIN categories AS c ON p.category_id = c.id
            ORDER BY p.name
        ''')
        return cursor.fetchall()

    def get_by_id(self, product_id):
        """Возвращает товар по id или None."""
        cursor = self.connection.cursor()
        cursor.execute('SELECT * FROM products WHERE id = ?', (product_id,))
        return cursor.fetchone()

    def get_by_category(self, category_id):
        """Возвращает товары из указанной категории."""
        cursor = self.connection.cursor()
        cursor.execute(
            'SELECT * FROM products WHERE category_id = ? ORDER BY price DESC',
            (category_id,)
        )
        return cursor.fetchall()

    def create(self, name, price, stock, category_id):
        """Создаёт товар. Возвращает id."""
        cursor = self.connection.cursor()
        cursor.execute(
            'INSERT INTO products (name, price, stock, category_id) VALUES (?, ?, ?, ?)',
            (name, price, stock, category_id)
        )
        return cursor.lastrowid

    def update_stock(self, product_id, new_stock):
        """Обновляет остаток. Возвращает True если товар найден."""
        cursor = self.connection.cursor()
        cursor.execute(
            'UPDATE products SET stock = ? WHERE id = ?',
            (new_stock, product_id)
        )
        return cursor.rowcount > 0

    def update_price(self, product_id, new_price):
        """Обновляет цену. Возвращает True если товар найден."""
        cursor = self.connection.cursor()
        cursor.execute(
            'UPDATE products SET price = ? WHERE id = ?',
            (new_price, product_id)
        )
        return cursor.rowcount > 0

    def delete(self, product_id):
        """Удаляет товар. Возвращает True если запись была."""
        cursor = self.connection.cursor()
        cursor.execute('DELETE FROM products WHERE id = ?', (product_id,))
        return cursor.rowcount > 0
```

---

## Третий репозиторий: OrderRepository

Репозиторий для заказов сложнее — он работает с двумя таблицами и содержит бизнес-логику:

```python
class OrderRepository:

    def __init__(self, connection):
        self.connection = connection

    def get_all(self):
        """Возвращает все заказы с именами пользователей."""
        cursor = self.connection.cursor()
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

    def get_by_id(self, order_id):
        """Возвращает заказ с полным составом и итогом."""
        cursor = self.connection.cursor()
        cursor.execute('''
            SELECT
                o.id            AS order_id,
                u.name          AS user_name,
                o.status,
                o.created_at,
                p.name          AS product_name,
                oi.quantity,
                oi.price_at_time,
                ROUND(oi.quantity * oi.price_at_time, 2) AS item_total
            FROM orders AS o
            INNER JOIN users       AS u  ON o.user_id     = u.id
            INNER JOIN order_items AS oi ON o.id           = oi.order_id
            INNER JOIN products    AS p  ON oi.product_id  = p.id
            WHERE o.id = ?
        ''', (order_id,))
        return cursor.fetchall()

    def get_total(self, order_id):
        """Возвращает итоговую сумму заказа."""
        cursor = self.connection.cursor()
        cursor.execute('''
            SELECT ROUND(SUM(quantity * price_at_time), 2) AS total
            FROM order_items
            WHERE order_id = ?
        ''', (order_id,))
        row = cursor.fetchone()
        return row['total'] if row else None

    def create(self, user_id, items, created_at):
        """
        Создаёт заказ с позициями.
        items — список словарей: [{'product_id': 1, 'quantity': 2, 'price': 5000.0}]
        Возвращает id созданного заказа.
        """
        cursor = self.connection.cursor()
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
            '''INSERT INTO order_items (order_id, product_id, quantity, price_at_time)
               VALUES (?, ?, ?, ?)''',
            order_items
        )
        return order_id

    def update_status(self, order_id, new_status):
        """Обновляет статус заказа. Возвращает True если заказ найден."""
        cursor = self.connection.cursor()
        cursor.execute(
            'UPDATE orders SET status = ? WHERE id = ?',
            (new_status, order_id)
        )
        return cursor.rowcount > 0
```

---

## Несколько репозиториев в одной транзакции

Одно из главных преимуществ паттерна — все репозитории работают с одним соединением, значит все их операции можно объединить в транзакцию:

```python
import sqlite3
from repositories import UserRepository, ProductRepository, OrderRepository

with sqlite3.connect('shop.db') as connection:
    connection.row_factory = sqlite3.Row

    users   = UserRepository(connection)
    products = ProductRepository(connection)
    orders  = OrderRepository(connection)

    # Создаём пользователя
    user_id = users.create('Новый Клиент', 'client@mail.ru', 'Москва', '2024-06-25')

    # Проверяем наличие товара
    product = products.get_by_id(1)
    if product and product['stock'] > 0:

        # Создаём заказ
        order_id = orders.create(
            user_id=user_id,
            items=[{'product_id': 1, 'quantity': 1, 'price': product['price']}],
            created_at='2024-06-25'
        )

        # Уменьшаем остаток
        products.update_stock(1, product['stock'] - 1)

        print(f'Заказ #{order_id} создан для пользователя id={user_id}')

# При выходе из with — автоматический commit всех операций
# При исключении — автоматический rollback
```

Три репозитория, три таблицы — одна транзакция. Каждый репозиторий делает своё дело, а согласованность обеспечивается единым соединением.

---

## Структура файлов проекта

Разместим репозитории в отдельном файле:

```
project/
├── shop.db
├── repositories.py    ← все репозитории
├── seed.py            ← сидер из урока 12
└── main.py            ← точка входа
```

```python
# repositories.py
import sqlite3


class UserRepository:
    def __init__(self, connection):
        self.connection = connection
    # ... методы


class ProductRepository:
    def __init__(self, connection):
        self.connection = connection
    # ... методы


class OrderRepository:
    def __init__(self, connection):
        self.connection = connection
    # ... методы
```

```python
# main.py
import sqlite3
from repositories import UserRepository, ProductRepository, OrderRepository

DB_PATH = 'shop.db'

def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection

def main():
    with get_connection() as connection:
        users    = UserRepository(connection)
        products = ProductRepository(connection)
        orders   = OrderRepository(connection)

        print(f'Пользователей: {len(users.get_all())}')
        print(f'Товаров:       {len(products.get_all())}')
        print(f'Заказов:       {len(orders.get_all())}')

if __name__ == '__main__':
    main()
```

`main.py` не содержит ни одной SQL-строки. Слой данных полностью изолирован в `repositories.py`.

---

## Связь с ООП

Что именно из ООП применяется здесь:

**Инкапсуляция** — `self.connection` скрыт внутри класса. Вызывающий код не знает и не должен знать как именно репозиторий работает с соединением.

**Единственная ответственность** — каждый класс отвечает только за свою сущность. `UserRepository` никогда не лезет в таблицу `products`.

**Единый интерфейс** — все репозитории имеют одинаковый набор методов: `get_all`, `get_by_id`, `create`, `update_*`, `delete`. Это соглашение которое делает код предсказуемым.

**Замена реализации** — если завтра нужно перейти с SQLite на PostgreSQL, меняется только содержимое методов. Вызывающий код (`main.py`) не затрагивается вообще. Это прямое следствие инкапсуляции.

---

## Что дальше

Паттерн Repository — это то на что опираются ORM-фреймворки. Django ORM, SQLAlchemy — они реализуют ту же идею, только автоматически. Когда в следующих модулях вы увидите `User.objects.all()` или `session.query(User).filter_by(city='Москва')` — узнаете знакомую концепцию. Разница только в том что ORM генерирует SQL сам, а не требует писать его руками.

---

## Вопросы

**1.** В чём главное архитектурное отличие репозитория от набора функций из прошлого урока?
**2.** Почему принцип "один репозиторий — одна сущность" важен?
**3.** Как репозитории разных сущностей участвуют в одной транзакции?
**4.** Почему `self.connection` не закрывается внутри методов репозитория?
**5.** Что из принципов ООП реализуется в паттерне Repository?
**6.** Чем `users.get_by_id(5)` лучше чем `get_user_by_id(connection, 5)` с точки зрения читаемости?
**7.** Метод `OrderRepository.create()` вставляет данные в две таблицы. Нужно ли внутри него управлять транзакцией?
**8.** Как изменится `main.py` если таблицу `users` переименовать в `customers`?
**9.** Можно ли создать два экземпляра `UserRepository` с разными соединениями в одном скрипте?

---

## Задачи

### **Задача 1.** 

Создайте класс `CategoryRepository` с методами `get_all()` и `get_by_id(category_id)`. Создайте экземпляр, вызовите оба метода и выведите результаты.

---

### **Задача 2.** 

Добавьте в `CategoryRepository` метод `create(name)` который создаёт категорию и возвращает её `id`. Добавьте метод `delete(category_id)` который возвращает `True` при успехе.

---

### **Задача 3.** 

Создайте полный `UserRepository` со всеми методами из урока. Выполните полный CRUD-цикл: создать пользователя, получить по `id`, обновить город, удалить.

---

### **Задача 4.** 

Создайте `ProductRepository` с методами `get_all()`, `get_by_id()`, `create()`, `update_stock()`, `delete()`. Добавьте метод `get_low_stock(threshold)` который возвращает товары с остатком ниже порога.

---

### **Задача 5.** 

Используя `UserRepository` и `ProductRepository` вместе, напишите скрипт который выводит: количество пользователей из Москвы и список товаров дешевле 5000 рублей. Оба репозитория должны использовать одно соединение.

---

### **Задача 6.** 

Создайте `OrderRepository` с методами `get_all()` и `get_by_status(status)`. Метод `get_by_status` должен возвращать заказы с именами пользователей через JOIN.

---

### **Задача 7.** 

Создайте файл `repositories.py` с тремя классами: `UserRepository`, `ProductRepository`, `OrderRepository`. В `main.py` импортируйте все три, создайте с одним соединением и выведите статистику: кол-во пользователей, товаров, заказов.

---

### **Задача 8.** 

Используя все три репозитория и одно соединение, выполните следующую цепочку операций в одной транзакции: создайте пользователя, создайте для него заказ с одной позицией, уменьшите остаток товара на 1. После `commit` проверьте что все три изменения зафиксированы.

---

[Предыдущий урок](lesson13.md) | [Следующий урок](lesson15.md)