# Модуль 1 · Урок 4. Базовый синтаксис SQL и простые выборки

## **Цель урока:**

- Изучить операторы `SELECT`, `DISTINCT`
- Изучить встроенные функции `LENGTH`, `UPPER`, `LOWER`, `ABS`
- Разобрать, что такое **литералы** и **алиасы**.

## 1) Теория

### **Подготовка таблицы `customers`**

- Создадим таблицу в `SQLiteStudio` с помощью запроса:

  ```sql
  CREATE TABLE IF NOT EXISTS customers (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          name TEXT,
          email TEXT,
          city TEXT,
          age INTEGER,
          balance REAL
      );
  ```

- Заполним таблицу некоторыми данными:

  ```sql
  INSERT INTO customers (name, email, city, age, balance)
  VALUES
      ("Иван Иванов",     "ivan@example.com",  "Moscow",   28,  -150.0),
      ("Мария Петрова",   "maria@MAIL.com",    "Moscow",   34,   320.5),
      ("Chen Li",         "chen@example.com",  "Beijing",  22,     0.0),
      ("Amina Yusuf",     "AMINA@ExAmple.nl",  "Amsterdam",40,  -50.0),
      ("John O'Connor",   "john.o@example.org","Dublin",   31,   10.0),
      ("Sakura Tanaka",   "sakura@example.jp", "Tokyo",    26,  100.0);
  ```

### **SELECT, литералы, алиасы**

`SELECT` — это основной оператор для получения и анализа данных в SQL.

Он используется для выборки данных из одной или нескольких таблиц базы данных. Он позволяет извлекать строки и столбцы, соответствующие заданным условиям, и формировать результирующий набор данных (результат запроса).

- **Базовая форма `SELECT`:**

  ```sql
  SELECT столбец1, столбец2, ...
  FROM имя_таблицы;
  ```

  Пример:

  ```sql
  SELECT name, email
  FROM customers;
  ```

- **Литералы (константы в запросе):**

  Литерал — это константа (фиксированное значение), которая выводится в каждом ряду результата. «Искусственные» столбцы — строки в кавычках или числа:

  ```sql
  SELECT name, email, 'ACTIVE' AS status, 2025 AS year
  FROM customers;
  ```

  Здесь `'ACTIVE'` и `2025` — литералы (константы), появятся одинаковыми значениями во всех строках.

- **Алиасы (псевдонимы столбцов):**

  Алиасы упрощают чтение и позволяют переименовать столбец в выводе:

  ```sql
  SELECT name AS customer_name,
         email AS email_address
  FROM customers;
  ```

  `AS` можно опустить:

  ```sql
  SELECT name customer_name, email email_address FROM customers;
  ```

  Если **алиас** содержит пробелы, заключайте его в кавычки:

  ```sql
  SELECT name AS "Full Name" FROM customers;
  ```

- **Выражения в `SELECT`:**
  Можно строить выражения:

  ```sql
  SELECT name,
         age + 1     AS age_next_year,  -- числовое выражение
         name || ' <' || email || '>' AS mailing_label  -- конкатенация текстов в SQLite
  FROM customers;
  ```

---

### **DISTINCT**

Оператор `DISTINCT` используется для **удаления дубликатов из результата запроса `SELECT`**. Он позволяет выбрать только уникальные (неповторяющиеся) значения в указанных столбцах.

- **Один столбец:**

  ```sql
  SELECT DISTINCT city
  FROM customers;
  ```

  Вернёт каждое уникальное значение `city` один раз.

- **Несколько столбцов:**

  ```sql
  SELECT DISTINCT city, email
  FROM customers;
  ```

  Уникальность будет проверяться по **паре** `(city, email)`.

---

### **Простые встроенные функции: `LENGTH`, `UPPER`, `LOWER`, `ABS`**

- `LENGTH(текст)` — длина строки (в символах для TEXT).

  ```sql
  SELECT name, LENGTH(name) AS name_len
  FROM customers;
  ```

- `UPPER(текст)` — в верхний регистр:

  ```sql
  SELECT name, UPPER(city) AS city_upper
  FROM customers;
  ```

- `LOWER(текст)` — в нижний регистр:

  ```sql
  SELECT email, LOWER(email) AS email_lower
  FROM customers;
  ```

- `ABS(число)` — модуль числа:

  ```sql
  SELECT name, balance, ABS(balance) AS balance_abs
  FROM customers;
  ```

- **Комбинирование:**

  ```sql
  SELECT DISTINCT UPPER(city) AS city_upper
  FROM customers;
  ```

  ```sql
  SELECT name,
      LENGTH(UPPER(name)) AS name_len_upper
  FROM customers;
  ```

## 2) Практика

### **Структура проекта на python:**

```
lesson04_sql_basics/
├─ db.sqlite3              # файл с БД, создастся автоматически
├─ main.py                 # запуск и простое меню
├─ core.py                 # подключение к БД, инициализация, общие утилиты
└─ logic.py                # логика урока: реализация задач по темам
```

### Модуль `core.py`

Этот модуль отвечает за всё **взаимодействие программы с базой данных**. Чтобы код был аккуратным и понятным, мы **вынесем работу с БД в отдельный файл**.

#### Шаг 1. Подключаем нужные библиотеки

Мы будем использовать:

- **sqlite3** — стандартная библиотека Python для работы с SQLite.
- **pathlib** — модуль для работы с путями (чтобы было удобно работать с файлами на разных ОС).

```python
# core.py
import sqlite3
from pathlib import Path
```

> Почему используем `pathlib`, а не просто строки (`"db.sqlite3"`)?

- На Windows и Linux пути к файлам пишутся по-разному (`\` и `/`).
- `Path` автоматически приведёт путь к правильному виду.
- Код станет кроссплатформенным и более читаемым.

---

#### Шаг 2. Константа для пути к файлу базы

Обычно **путь к файлу базы данных уносят в отдельную константу**, чтобы:

- легко было менять местоположение файла;
- всегда знать, где именно хранится БД.

```python
DB_PATH = Path("db.sqlite3")
```

> Здесь мы "говорим": база данных лежит в файле `db.sqlite3` в корне проекта. Если файла нет — SQLite его создаст автоматически.

#### Шаг 3. Функция подключения к базе

Чтобы каждый раз не писать одну и ту же команду, мы сделаем отдельную функцию:

```python
def get_connection() -> sqlite3.Connection:
    """Создаёт и возвращает подключение к базе данных."""
    return sqlite3.connect(str(DB_PATH))
```

- Функция возвращает **объект соединения** (`Connection`).
- Мы используем `str(DB_PATH)`, потому что `sqlite3.connect` работает со строками, а не с `Path`.

Теперь в любом месте проекта можно будет написать:

```python
conn = get_connection()
```

и получить соединение.

---

#### Шаг 4. Инициализация базы и создание таблицы

При первом запуске у нас базы может не быть. Поэтому:

- создаём таблицу `customers`, если её ещё нет;
- если таблица пустая — наполняем её тестовыми данными.

```python
def init_db() -> None:
    """Создаём таблицу customers и наполняем данными, если пусто."""
    with get_connection() as conn:   # создаём подключение
        cur = conn.cursor()          # создаём курсор для запросов

        # 1. Создаём таблицу, если её нет
        cur.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            city TEXT,
            age INTEGER,
            balance REAL
        );
        """)

        # 2. Проверяем: есть ли уже данные?
        cur.execute("SELECT COUNT(*) FROM customers;")
        count = cur.fetchone()[0]

        # 3. Если пусто — добавляем тестовые данные
        if count == 0:
            rows = [
                ("Иван Иванов",     "ivan@example.com",  "Moscow",   28,  -150.0),
                ("Мария Петрова",   "maria@MAIL.com",    "Moscow",   34,   320.5),
                ("Chen Li",         "chen@example.com",  "Beijing",  22,     0.0),
                ("Amina Yusuf",     "AMINA@ExAmple.nl",  "Amsterdam",40,  -50.0),
                ("John O'Connor",   "john.o@example.org","Dublin",   31,   10.0),
                ("Sakura Tanaka",   "sakura@example.jp", "Tokyo",    26,  100.0),
            ]
            cur.executemany("""
                INSERT INTO customers (name, email, city, age, balance)
                VALUES (?, ?, ?, ?, ?);
            """, rows)

        conn.commit()  # сохраняем изменения
```

> Объяснение:

- `CREATE TABLE IF NOT EXISTS` — создаёт таблицу только если её нет.
- `SELECT COUNT(*)` — узнаём количество строк.
- `executemany` — позволяет вставить сразу несколько строк за один вызов.

---

#### Шаг 5. Универсальная функция выборки

Чтобы не **повторять один и тот же код** (открыть соединение → выполнить запрос → забрать данные → закрыть соединение), сделаем одну функцию для выборок:

```python
def fetch_all(sql: str, params: tuple = ()):
    """Выполняет SELECT-запрос и возвращает все строки."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(sql, params)
        return cur.fetchall()
```

> Теперь можно будет написать:

```python
rows = fetch_all("SELECT * FROM customers WHERE age > ?", (30,))
print(rows)
```

и получить список строк из базы.

---

#### Итог по `core.py`

Теперь у нас есть модуль, который:

- хранит путь к базе (`DB_PATH`);
- умеет создавать соединения (`get_connection`);
- инициализирует таблицу и тестовые данные (`init_db`);
- позволяет выполнять простые выборки (`fetch_all`).

---

### Модуль `logic.py`

В этом модуле мы сделаем реализацию "сырых" запросов к БД. К каждому заданию будет отдельная функция.

#### Задание 1.

**Вывести список всех клиентов (id, имя и email).**

```python
def show_select_basics():
    print("\n[SELECT] Базовый выбор колонок:")
    rows = fetch_all("SELECT id, name, email FROM customers;")
    for r in rows:
        print(r)
```

**Пояснение:**

- `SELECT id, name, email` — выбираем только нужные колонки, а не все данные.
- Так студенты видят, что не всегда нужно использовать `SELECT *`.
- В Python мы перебираем результат построчно.

---

#### Задание 2.

**Вывести имя и email клиентов, но:**

- назвать поле `name → customer_name`
- назвать поле `email → email_address`
- добавить колонку с литералом `'ACTIVE'`
- добавить колонку с годом (например, `2025`)

```python
def show_aliases_and_literals():
    print("\n[SELECT + Алиасы + Литералы] Переименование и добавление констант:")
    rows = fetch_all("""
        SELECT
            name AS customer_name,
            email AS email_address,
            'ACTIVE' AS status,
            2025 AS year
        FROM customers;
    """)
    for r in rows:
        print(r)
```

**Пояснение:**

- `AS` позволяет давать **алиасы** (понятные имена колонок).
- `'ACTIVE' AS status` — это **литерал** (строка-константа).
- Такие колонки полезны, если мы хотим «пометить» данные или объединять таблицы.

---

#### Задание 3.

**Сделать «почтовую метку» в формате: `Имя <email>`**

```python
def show_mailing_label():
    print("\n[SELECT + выражения] Почтовая метка (name <email>):")
    rows = fetch_all("""
        SELECT
            name,
            email,
            name || ' <' || email || '>' AS mailing_label
        FROM customers;
    """)
    for r in rows:
        print(r)
```

**Пояснение:**

- В SQLite строки объединяются оператором `||`.
- Мы создаём новый столбец `mailing_label`.
- Результат будет выглядеть так: `Иван Иванов <ivan@test.com>`.

---

#### Задание 4.

**Вывести список уникальных городов, где живут клиенты.**

```python
def show_distinct_cities():
    print("\n[DISTINCT] Уникальные города клиентов:")
    rows = fetch_all("SELECT DISTINCT city FROM customers;")
    for (city,) in rows:
        print(city)
```

**Пояснение:**

- `DISTINCT` убирает дубликаты.
- Если без него, то «Moscow» повторится несколько раз.
- В Python `(city,)` — это распаковка одной колонки.

---

#### Задание 5.

**Вывести имена клиентов и длину каждого имени. Отсортировать по длине.**

```python
def show_length_of_names():
    print("\n[LENGTH] Длина имён:")
    rows = fetch_all("""
        SELECT name, LENGTH(name) AS name_len
        FROM customers
        ORDER BY name_len DESC, name;
    """)
    for r in rows:
        print(r)
```

**Пояснение:**

- `LENGTH(name)` возвращает количество символов.
- `AS name_len` — даём понятное имя колонке.
- Сортировка по длине (`DESC` — от большего к меньшему).

---

#### Задание 6.

**Вывести города клиентов, а рядом — те же города, но заглавными буквами.**

```python
def show_upper_cities():
    print("\n[UPPER] Города в верхнем регистре:")
    rows = fetch_all("SELECT city, UPPER(city) AS city_upper FROM customers;")
    for r in rows:
        print(r)
```

**Пояснение:**

- `UPPER(city)` переводит текст в верхний регистр.
- Это часто нужно, чтобы сравнивать данные без учёта регистра.

---

#### Задание 7.

**Вывести email клиентов в нижнем регистре.**

```python
def show_lower_emails():
    print("\n[LOWER] Email в нижнем регистре (нормализация):")
    rows = fetch_all("SELECT email, LOWER(email) AS email_lower FROM customers;")
    for r in rows:
        print(r)
```

**Пояснение:**

- `LOWER(email)` переводит в нижний регистр.
- В реальных проектах так «нормализуют» email перед хранением или поиском.

---

#### Задание 8.

**Вывести баланс клиентов и его абсолютное значение.**

```python
def show_abs_balances():
    print("\n[ABS] Балансы и их модуль (полезно для долгов):")
    rows = fetch_all("""
        SELECT name, balance, ABS(balance) AS balance_abs
        FROM customers;
    """)
    for r in rows:
        print(r)
```

**Пояснение:**

- `ABS(balance)` возвращает модуль числа.
- Отрицательные балансы (долги) становятся положительными.
- Это удобно для аналитики (например, общая сумма долгов).

---

#### Задание 9.

**Вывести имя клиента и длину имени, но сначала привести имя к верхнему регистру.**

```python
def show_name_length_on_upper():
    print("\n[UPPER + LENGTH] Длина имени после приведения к верхнему регистру:")
    rows = fetch_all("""
        SELECT name, LENGTH(UPPER(name)) AS len_upper
        FROM customers
        ORDER BY len_upper DESC;
    """)
    for r in rows:
        print(r)
```

**Пояснение:**

- Функции можно **вкладывать** друг в друга.
- `UPPER(name)` → `LENGTH(...)` — сначала переводим в верхний регистр, потом считаем длину.
- В нашем случае длина имени не изменится (кроме спецсимволов в некоторых языках). Но студенты поймут принцип **комбинации функций**.

---

### Файл `main.py` для запуска приложения

#### Шаг 1. Импорты

Подключить инициализацию БД и «набор упражнений» (функции из `logic.py`):

- `core.init_db()` гарантирует, что таблица и демо-данные готовы;
- `logic` — это место, где лежат наши учебные задания.

```python
from core import init_db
import logic
```

---

#### Шаг 2. Лёгкая инициализация БД в начале работы

При первом запуске **создать таблицу** и **наполнить её тестовыми данными**.

```python
def main():
    init_db()  # создаём таблицу и тестовые данные при первом запуске
    # ... здесь позже добавим меню ...
```

---

#### Шаг 3. Текстовое меню

Нужно дать пользователю список упражнений и обработать выбор.

Реализуем меню с помощью маппинга «номер → функция»

```python
MENU = {
    "1": ("SELECT базовый", logic.show_select_basics),
    "2": ("SELECT + алиасы + литералы", logic.show_aliases_and_literals),
    "3": ("SELECT: почтовая метка (конкатенация)", logic.show_mailing_label),
    "4": ("DISTINCT: уникальные города", logic.show_distinct_cities),
    "5": ("LENGTH: длина имён", logic.show_length_of_names),
    "6": ("UPPER: города в верхнем регистре", logic.show_upper_cities),
    "7": ("LOWER: email в нижнем регистре", logic.show_lower_emails),
    "8": ("ABS: модуль баланса", logic.show_abs_balances),
    "9": ("UPPER + LENGTH: длина имени после UPPER", logic.show_name_length_on_upper),
}

def main():
    init_db()
    while True:
        print("\n=== Урок 4: Базовый синтаксис SQL и простые выборки ===")
        for key, (title, _) in MENU.items():
            print(f"{key}) {title}")
        print("0) Выход")

        choice = input("Выберите пункт: ").strip()
        if choice == "0":
            print("Пока!")
            break

        item = MENU.get(choice)
        if item:
            _, func = item
            func()
        else:
            print("Неверный выбор. Попробуйте снова.")
```

> Такой подход автоматически держит **названия меню и функции синхронно**.

---

#### Шаг 4. «Охранная» конструкция запуска

Сделать так, чтобы `main()` запускался только когда мы запускаем файл напрямую. Если кто-то импортирует `main.py` как модуль, код не должен сам запускаться.

```python
if __name__ == "__main__":
    main()
```

## 3) Вопросы

1. Какой SQL-запрос вернёт все строки и все столбцы таблицы `customers`?
2. Зачем нужны псевдонимы (`AS`) в SQL? Приведите пример запроса с алиасом для столбца email (например: `contact_email` вместо `email`).
3. Что такое литерал в SQL-запросе? Приведите пример, когда мы добавляем столбец с названием `status` и фиксированным значением `'VIP'` (С помощью запроса нужно вывести столбец `first_name` и `status` из таблицы `customers`).
4. Чем отличается `SELECT city FROM customers;` от `SELECT DISTINCT city FROM customers;`?
5. Какой результат вернёт выражение `LENGTH('Python')`?
6. Напишите SQL-запрос, который выводит **_имя клиента_ в верхнем регистре** и **длину этого имени**.

## 4) Домашнее задание

Написать приложение для взаимодействия с базой данных SQLite. Приложение должно запускаться через консоль и предоставлять меню для выполнения различных действий.

---

### 1. Структура проекта

Ваш проект должен состоять из трёх модулей:

- **`core.py`** — работа с БД (подключение, инициализация таблицы, базовые функции).
- **`logic.py`** — функции, реализующие SQL-запросы.
- **`main.py`** — основной файл для запуска приложения с меню.

---

### 2. База данных

Создайте базу данных SQLite с одной таблицей `products`.

**Структура таблицы:**

- `id` — целое число, первичный ключ, автоинкремент.
- `title` — название продукта (TEXT).
- `price` — цена продукта (REAL).
- `count` — количество на складе (INTEGER).

---

### 3. Данные для заполнения таблицы

При первом запуске программы заполните таблицу тестовыми данными:

```sql
('Яблоко', 50.0, 100),
('Яблоко', 52.0, 80),
('Банан', 40.0, 120),
('Апельсин', 60.0, 60),
('Помидор', 70.0, 50),
('Огурец', 45.0, 90),
('Огурец', 44.0, 100),
('Сок яблочный', 120.0, 30),
('Сок апельсиновый', 130.0, 25),
('Сок яблочный', 115.0, 40),
('Хлеб', 35.0, 200),
('Хлеб', 34.0, 180);
```

---

### 4. Логика приложения

Реализуйте в приложении следующее функции:

1. **Вывести все продукты**

2. **Вывести название всех продуктов и поле `discount` со значением `'YES'`**

3. **Вывести названия уникальных продуктов**

---

### 5. Результат работы

После запуска программа должна выводить меню, ждать выбора пользователя и отображать результат SQL-запроса.
Пример вывода:

```
=== Меню ===
1) Все продукты
2) Названия + discount
3) Уникальные продукты
0) Выход
Выберите пункт: 3

Уникальные продукты:
Яблоко
Банан
Апельсин
Помидор
Огурец
Сок яблочный
Сок апельсиновый
Хлеб
```

---

[Предыдущий урок](lesson03.md) | [Следующий урок](lesson05.md)
