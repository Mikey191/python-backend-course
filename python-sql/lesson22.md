# Урок 22. Что такое ORM и зачем он нужен

## С чего начинается усталость от raw SQL

Вспомните репозитории которые мы писали в Модуле 2. Для каждой сущности — отдельный класс, в каждом методе — строка SQL. Когда сущностей три-четыре, это терпимо. Когда их двадцать — начинается боль.

Посмотрим на типичный репозиторий для пользователей из реального проекта:

```python
class UserRepository:

    def get_by_id(self, user_id):
        cursor = self.connection.cursor()
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        return cursor.fetchone()

    def get_by_email(self, email):
        cursor = self.connection.cursor()
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        return cursor.fetchone()

    def get_active_users(self):
        cursor = self.connection.cursor()
        cursor.execute('SELECT * FROM users WHERE is_active = 1 ORDER BY name')
        return cursor.fetchall()

    def create(self, name, email, city, created_at):
        cursor = self.connection.cursor()
        cursor.execute(
            'INSERT INTO users (name, email, city, created_at) VALUES (?, ?, ?, ?)',
            (name, email, city, created_at)
        )
        return cursor.lastrowid

    def update_city(self, user_id, new_city):
        cursor = self.connection.cursor()
        cursor.execute(
            'UPDATE users SET city = ? WHERE id = ?',
            (new_city, user_id)
        )
        return cursor.rowcount > 0

    def delete(self, user_id):
        cursor = self.connection.cursor()
        cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
        return cursor.rowcount > 0
```

И точно такой же класс — для товаров, заказов, категорий, отзывов, адресов доставки... Паттерн один и тот же, только имена таблиц и столбцов меняются. Это называется **boilerplate** — шаблонный код который приходится писать снова и снова.

---

## Проблемы raw SQL в большом проекте

### 1. Рефакторинг схемы — боль

Представьте: в таблице `users` нужно переименовать поле `city` в `city_name`. Это изменение в одной строке SQL-миграции. Но теперь нужно найти и обновить **каждое** упоминание строки `'city'` во всём проекте:

```python
# Нужно найти и заменить в каждом файле:
'SELECT name, city FROM users'
'INSERT INTO users (name, email, city) VALUES'
'UPDATE users SET city = ?'
```

В большом проекте таких мест могут быть десятки. Пропустили одно — получили баг который проявится только в продакшне.

### 2. Строки не проверяются на этапе написания кода

SQL — это строки. Python не знает что внутри:

```python
# Python не видит опечатку — узнаем только в рантайме
cursor.execute('SELECT * FROM uers WHERE id = ?', (user_id,))
#                          ^^^^  опечатка

# Python не видит что столбца нет — узнаем только в рантайме
cursor.execute('SELECT nonexistent_column FROM users')
```

IDE не подскажет, линтер не поймает. Ошибки в SQL-строках живут до момента выполнения.

### 3. Результаты — кортежи или словари без типов

```python
row = cursor.fetchone()
print(row['price'])   # float? str? Depends on what's in DB
```

Нет автодополнения. Нет проверки типов. Разработчик должен держать схему в голове.

### 4. Связанные данные требуют ручной сборки

Получить пользователя с его заказами и позициями каждого заказа:

```python
cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
user = dict(cursor.fetchone())

cursor.execute('SELECT * FROM orders WHERE user_id = ?', (user_id,))
orders = cursor.fetchall()

user['orders'] = []
for order in orders:
    order = dict(order)
    cursor.execute('SELECT * FROM order_items WHERE order_id = ?', (order['id'],))
    order['items'] = [dict(item) for item in cursor.fetchall()]
    user['orders'].append(order)
```

Три уровня вложенности — три запроса вручную, три уровня вложенного кода. В реальных приложениях таких уровней может быть пять-шесть.

---

## Что такое ORM

**ORM** (Object-Relational Mapping, объектно-реляционное отображение) — это слой который отображает таблицы базы данных на классы Python, а строки таблиц — на объекты этих классов.

Вместо того чтобы писать SQL вручную — вы описываете данные как классы, а ORM сам генерирует нужный SQL.

```python
# Вы описываете класс
class User(Base):
    __tablename__ = 'users'
    id    = Column(Integer, primary_key=True)
    name  = Column(String, nullable=False)
    email = Column(String, unique=True)
    city  = Column(String)

# ORM сам создаёт таблицу, сам пишет SELECT/INSERT/UPDATE/DELETE
```

Этот класс — одновременно и схема таблицы, и тип данных, и инструмент для запросов.

Важно понимать, что большинство ORM работают по одним и тем же принципам: таблицы представляются классами, записи — объектами, а SQL-запросы заменяются методами и выражениями языка Python. Поэтому, изучив SQLAlchemy, вы освоите не только конкретную библиотеку, но и сам подход к работе с ORM. 

В дальнейшем переход на Django ORM будет достаточно простым — потребуется лишь изучить особенности синтаксиса и API. Например, запрос `session.query(User).filter(User.city == 'Москва')` в SQLAlchemy по смыслу полностью соответствует `User.objects.filter(city='Москва')` в Django. Именно поэтому понимание SQLAlchemy помогает воспринимать Django ORM как понятный инструмент, а не как набор магических методов.

---

## Сравнение: raw sqlite3 vs SQLAlchemy ORM

Посмотрим на одну и ту же задачу в двух подходах.

### Задача: получить пользователя по id

```python
# --- Raw sqlite3 ---
def get_user_by_id(connection, user_id):
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    row = cursor.fetchone()
    return dict(row) if row else None

# Использование
user = get_user_by_id(connection, 5)
if user:
    print(user['name'])   # словарь, нет автодополнения
```

```python
# --- SQLAlchemy ORM ---
def get_user_by_id(session, user_id):
    return session.get(User, user_id)

# Использование
user = get_user_by_id(session, 5)
if user:
    print(user.name)   # объект с атрибутами, есть автодополнение
```

### Задача: создать пользователя

```python
# --- Raw sqlite3 ---
def create_user(connection, name, email, city, created_at):
    cursor = connection.cursor()
    cursor.execute(
        'INSERT INTO users (name, email, city, created_at) VALUES (?, ?, ?, ?)',
        (name, email, city, created_at)
    )
    return cursor.lastrowid
```

```python
# --- SQLAlchemy ORM ---
def create_user(session, name, email, city, created_at):
    user = User(name=name, email=email, city=city, created_at=created_at)
    session.add(user)
    session.flush()   # получаем id не закрывая транзакцию
    return user       # объект уже содержит id
```

### Задача: пользователи из Москвы

```python
# --- Raw sqlite3 ---
cursor.execute(
    'SELECT * FROM users WHERE city = ? ORDER BY name',
    ('Москва',)
)
rows = cursor.fetchall()
```

```python
# --- SQLAlchemy ORM ---
users = session.query(User)\
    .filter(User.city == 'Москва')\
    .order_by(User.name)\
    .all()
```

### Задача: пользователь с заказами

```python
# --- Raw sqlite3 — три запроса вручную ---
cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
user = dict(cursor.fetchone())

cursor.execute('SELECT * FROM orders WHERE user_id = ?', (user_id,))
user['orders'] = [dict(row) for row in cursor.fetchall()]
```

```python
# --- SQLAlchemy ORM — связи описаны в модели ---
class User(Base):
    __tablename__ = 'users'
    id     = Column(Integer, primary_key=True)
    name   = Column(String)
    orders = relationship('Order', back_populates='user')  # связь

# Получить пользователя с заказами
user = session.get(User, user_id)
print(user.orders)   # ORM сам выполнит нужный запрос
```

### Итог сравнения

| | Raw SQL | ORM |
|---|---|---|
| Написание запросов | Вручную, строки | Автоматически из объектов |
| Проверка ошибок | Только в рантайме | Частично на этапе написания |
| Автодополнение IDE | Нет | Да — атрибуты объекта |
| Рефакторинг схемы | Менять везде в коде | Только в модели |
| Связанные данные | Ручные JOIN или N+1 запросов | Через `relationship` |
| Контроль SQL | Полный | Ограниченный |
| Порог вхождения | Низкий — только SQL | Выше — нужно знать ORM |

---

## Что ORM прячет — и почему это важно понимать

ORM — это абстракция. Абстракция упрощает работу, но прячет детали. Иногда спрятанные детали становятся проблемой.

### Проблема N+1 запросов

Это классическая ловушка ORM о которой нужно знать до того как столкнуться с ней в продакшне.

Представьте: нужно вывести список из 100 пользователей и для каждого — количество заказов.

```python
# Выглядит невинно
users = session.query(User).all()   # 1 запрос — получить всех пользователей

for user in users:
    print(f'{user.name}: {len(user.orders)} заказов')
    # user.orders — ORM идёт в БД за заказами ЭТОГО пользователя
    # Это происходит для КАЖДОГО пользователя в цикле!
```

Итог: 1 запрос за пользователями + 100 запросов за заказами = **101 запрос** вместо одного.

В raw SQL эта задача решается одним запросом:

```sql
SELECT u.name, COUNT(o.id) AS order_count
FROM users AS u
LEFT JOIN orders AS o ON u.id = o.user_id
GROUP BY u.id
```

ORM тоже умеет делать это эффективно — через `joinedload` или `subqueryload`. Но разработчик должен **явно** указать что загружать вместе. Без этого ORM по умолчанию выбирает ленивую загрузку и создаёт N+1 проблему.

Подробнее об оптимизации запросов в ORM мы разберём в Уроке 24 когда будем работать с SQLAlchemy ORM напрямую.

---

## Когда ORM — плохой выбор

Это честный вопрос. ORM не универсальный инструмент — у него есть ситуации когда он мешает больше чем помогает.

### 1. Сложная аналитика и агрегация

Представьте запрос который нужен бизнесу: "Топ-10 категорий по выручке за последние 30 дней среди пользователей из Москвы зарегистрированных в этом году, исключая заказы со статусом 'cancelled'".

```sql
-- Этот запрос понятен и прямолинеен
SELECT
    c.name,
    SUM(oi.quantity * oi.price_at_time) AS revenue
FROM order_items AS oi
INNER JOIN orders    AS o  ON oi.order_id    = o.id
INNER JOIN users     AS u  ON o.user_id      = u.id
INNER JOIN products  AS p  ON oi.product_id  = p.id
INNER JOIN categories AS c ON p.category_id  = c.id
WHERE
    o.status != 'cancelled'
    AND u.city = 'Москва'
    AND u.created_at >= '2024-01-01'
    AND o.created_at >= date('now', '-30 days')
GROUP BY c.id, c.name
ORDER BY revenue DESC
LIMIT 10;
```

Попытка написать это через ORM даёт громоздкую цепочку `.join().filter().group_by().order_by()`. SQL здесь выразительнее, короче и понятнее. Опытные разработчики в таких случаях пишут raw SQL даже внутри ORM-проекта — SQLAlchemy это позволяет.

### 2. Высоконагруженные системы с критичной производительностью

ORM добавляет слой обработки между кодом и базой данных. При тысячах запросов в секунду этот overhead становится заметным. Системы где каждая миллисекунда важна (биржевые торги, real-time игры, телеметрия) часто работают с raw SQL или специализированными инструментами.

### 3. Специфичные возможности конкретной СУБД

PostgreSQL умеет многое чего нет в стандартном SQL: JSONB-поля, полнотекстовый поиск, оконные функции с особым синтаксисом, `COPY` для массовой загрузки данных. ORM абстрагирует от конкретной СУБД — это хорошо для переносимости, но плохо если нужна именно PostgreSQL-специфика. Придётся писать raw SQL внутри ORM.

### 4. Массовые операции с данными

```python
# ORM: создать 10 000 записей
for item in large_dataset:
    obj = Product(name=item['name'], price=item['price'], ...)
    session.add(obj)
session.commit()
# ORM создаёт Python-объект для каждой строки — медленно при больших объёмах
```

```python
# Raw SQL: одна операция
cursor.executemany(
    'INSERT INTO products (name, price, ...) VALUES (?, ?, ...)',
    large_dataset
)
# Прямо в БД, без создания Python-объектов — значительно быстрее
```

SQLAlchemy ORM предоставляет `bulk_insert_mappings` для таких случаев, но это уже обход ORM-паттерна, а не его использование.

### 5. Когда команда лучше знает SQL чем ORM

Если в команде сильные SQL-разработчики и слабые знания конкретного ORM — raw SQL даст меньше ошибок и быстрее. ORM нужно изучать — это инвестиция которая окупается не сразу.

---

## Итог: как выбирать

```
Нужен ORM когда:
✓ Стандартные CRUD-операции составляют большинство запросов
✓ Команда хорошо знает выбранный ORM
✓ Важна переносимость между СУБД
✓ Нужна быстрая разработка

Нужен raw SQL когда:
✓ Сложная аналитика и нестандартные запросы
✓ Критична производительность каждого запроса
✓ Используются специфичные возможности СУБД
✓ Массовые операции с данными

На практике:
✓ ORM для основной работы
✓ Raw SQL для сложных запросов внутри ORM-проекта
✓ Знать оба подхода — обязательно
```

Именно поэтому мы изучали raw SQL два модуля прежде чем перейти к ORM. Разработчик который понимает SQL — использует ORM осознанно. Разработчик который знает только ORM — не понимает что происходит под капотом и не может решить проблему когда ORM не справляется.

---

## Вопросы

1. Что такое boilerplate-код и почему он проблема в большом проекте?
2. Почему опечатка в имени таблицы в SQL-строке не видна до запуска программы?
3. Чем объект SQLAlchemy ORM удобнее словаря из sqlite3.Row?
4. Что такое проблема N+1 запросов и почему она возникает в ORM?
5. В каком случае raw SQL внутри ORM-проекта лучше чем использование ORM?
6. Почему ORM не подходит для массовой вставки 100 000 строк?
7. Что означает "ORM абстрагирует от конкретной СУБД" и когда это минус?
8. Почему в этом курсе raw SQL изучался раньше ORM, а не наоборот?
9. Как Django ORM связан с тем что мы изучаем в этом модуле?
10. Команда решает переименовать поле `city` в `city_name`. Что проще: в проекте с raw SQL или с ORM?

---

## Задачи

### **Задача 1.** 

В репозитории из Модуля 2 (`UserRepository`) подсчитайте: сколько строк занимает шаблонный код (открытие курсора, выполнение запроса, получение результата) и сколько — уникальная логика (конкретный SQL). Запишите соотношение. Это и есть объём boilerplate.

---

### **Задача 2.** 

Напишите raw SQL запрос который за один вызов к базе получает: всех пользователей из Москвы, количество их заказов и суммарную потраченную сумму. Подумайте: как это выглядело бы если получать данные через три отдельных запроса в цикле (N+1 вариант)?

---

### **Задача 3.** 

Найдите в коде мини-проекта из Урока 20 (To-Do API) запрос который было бы сложнее всего переписать через ORM и объясните почему. Подсказка: ищите динамически строящийся WHERE.

---

### **Задача 4.** 

Опишите сценарий из реального приложения (не из курса) где вы бы выбрали raw SQL вместо ORM. Обоснуйте выбор используя критерии из урока.

---

[Предыдущий урок](lesson21.md) | [Следующий урок](lesson23.md)