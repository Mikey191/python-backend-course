# Модуль 1 · Урок 5. Фильтрация данных

## **Цель урока:**

- Научиться отбирать только те строки, которые нужны, с помощью WHERE.
- Освоить операторы сравнения (=, >, <, >=, <=, !=).
- Использовать IS NULL, BETWEEN, IN для фильтрации.
- Применять шаблонный поиск с LIKE и Ознакомиться с расширенным поиском через REGEXP в SQLite.

## 1) Теория

### **Что такое фильтрация. Для чего она нужна?**

**Фильтрация** — это процесс отбора только тех строк из таблицы, которые соответствуют определённым условиям.

- Представь, что у тебя есть список из 1000 товаров, но нужно найти только те, у которых **рейтинг больше 4.5** или которые **есть в наличии**.
- Именно для этого и используется **WHERE** и другие операторы — чтобы отсеять лишнее и оставить только нужное.

**Ключевая идея:**
SQL всегда работает с целыми таблицами, а фильтрация позволяет выделить «кусочек» таблицы, подходящий под условия.

---

### **Схема БД**

Мы будем работать с таблицей **products**. Она хранит список товаров:

| Поле          | Тип     | Описание                                             |
| ------------- | ------- | ---------------------------------------------------- |
| `id`          | INTEGER | Уникальный идентификатор (PRIMARY KEY AUTOINCREMENT) |
| `count`       | INTEGER | Количество товара на складе                          |
| `status`      | TEXT    | Есть ли в наличии (`'yes'` / `'no'`)                 |
| `description` | TEXT    | Краткое описание товара (2–3 слова)                  |
| `rating`      | REAL    | Рейтинг товара (например, 4.5)                       |

---

### **Создание БД и таблицы**

```sql
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    count INTEGER,
    status TEXT,
    description TEXT,
    rating REAL
);
```

---

### **Заполнение фейковыми данными**

```sql
INSERT INTO products (count, status, description, rating) VALUES
(10, 'yes', 'Red Shirt', 4.7),
(0, 'no', 'Blue Jeans', 4.1),
(25, 'yes', 'Black Shoes', 3.9),
(3, 'yes', 'Green Hat', 4.8),
(0, 'no', 'Yellow Jacket', 2.5),
(15, 'yes', 'White Socks', 4.3),
(7, 'yes', 'Gray Scarf', 3.5),
(0, 'no', 'Brown Belt', 4.0),
(12, 'yes', 'Pink Dress', 4.9),
(1, 'no', 'Orange Gloves', 3.2);
```

Теперь у нас есть таблица с 10 товарами.

---

### **Оператор WHERE**

Оператор **WHERE** используется для фильтрации строк.

Пример: товары, которые есть в наличии.

```sql
SELECT * FROM products
WHERE status = 'yes';
```

---

### **Операторы сравнения**

Операторы сравнения позволяют сравнивать значения:

- `=` — равно
- `!=` или `<>` — не равно
- `>` — больше
- `<` — меньше
- `>=` — больше или равно
- `<=` — меньше или равно

**Примеры:**

1. Все товары, у которых рейтинг выше 4.5:

```sql
SELECT * FROM products
WHERE rating > 4.5;
```

2. Все товары, у которых количество равно 0 (закончились):

```sql
SELECT * FROM products
WHERE count = 0;
```

---

### **Что такое NULL**

**NULL** в SQL — это специальное значение «пусто», «неизвестно».
Важно:

- NULL **не равно нулю (0)**.
- NULL **не равно пустой строке ("")**.
- NULL — это отдельное состояние, означающее, что значения просто нет.

Чтобы проверить NULL, используют `IS NULL` или `IS NOT NULL`.

**IS NULL** проверяет, что значение действительно является **NULL** (отсутствует). Проверка `= NULL` **всегда возвращает FALSE**, поэтому **её использовать нельзя**.

Пример: найти товары без описания.

```sql
SELECT * FROM products
WHERE description IS NULL;
```

---

### **Оператор BETWEEN**

**BETWEEN** позволяет отбирать значения в диапазоне.

Пример: товары с рейтингом от 4.0 до 4.8:

```sql
SELECT * FROM products
WHERE rating BETWEEN 4.0 AND 4.8;
```

---

### **Оператор IN**

**IN** проверяет, входит ли значение в набор.

Пример: товары со статусами `'yes'` или `'no'`:

```sql
SELECT * FROM products
WHERE status IN ('yes', 'no');
```

(Здесь результат совпадает со всеми товарами, но на реальных данных может быть несколько статусов, например `preorder`, `archived` и т.д.).

---

### **Оператор LIKE**

**LIKE** нужен для поиска по шаблону.
Символы:

- `%` — любое количество любых символов
- `_` — ровно один любой символ

Пример: товары, описание которых содержит слово `"Shirt"`:

```sql
SELECT * FROM products
WHERE description LIKE '%Shirt%';
```

Пример: товары, описание которых начинается с `"B"`:

```sql
SELECT * FROM products
WHERE description LIKE 'B%';
```

---

### **Оператор REGEXP**

**REGEXP** — это поиск по **регулярным выражениям**.
Регулярные выражения (regex) — специальный язык шаблонов для поиска текста. Их часто используют программисты для проверки строк (например, «это email?»).

⚠ В SQLite **REGEXP нет по умолчанию**. Его можно подключить вручную через Python или расширения. В MySQL и PostgreSQL поддержка есть «из коробки».

Пример (если REGEXP подключен): товары, описание которых состоит только из букв:

```sql
SELECT * FROM products
WHERE description REGEXP '^[A-Za-z ]+$';
```

---

### **LIKE и REGEXP не конкуренты**

В SQL (и конкретно в SQLite) используется **упрощённый синтаксис шаблонов**, не такой мощный как регулярные выражения. Основные элементы:

- `%` — заменяет **любое количество символов** (даже 0).

  ```sql
  -- Найдёт все названия, которые начинаются на 'Sh'
  SELECT * FROM products WHERE title LIKE 'Sh%';
  ```

- `_` — заменяет **ровно один символ**.

  ```sql
  -- Найдёт 'Shirt' и 'Short', но не 'Shampoo'
  SELECT * FROM products WHERE title LIKE 'Sh_rt';
  ```

- В некоторых СУБД (MySQL, PostgreSQL) можно задавать **escape-символ** (например, `\`), чтобы искать сами `%` или `_`, но в SQLite чаще это не требуется.

То есть `LIKE` — это по сути "миниконструктор шаблонов" с двумя спецсимволами.

- `REGEXP` — это **полноценные регулярные выражения**. С их помощью можно искать гораздо более сложные шаблоны (цифры, буквы, группы, повторы, классы символов и т. д.).

#### **Схема применения**

- Если нужен **простой поиск** (начинается на..., заканчивается на..., содержит...), → используй `LIKE`.
- Если нужен **сложный шаблон** (например, "в начале цифра, потом слово", "не менее 2 подряд идущих заглавных букв"), → используй `REGEXP`.

#### **Итог:**

`LIKE` и `REGEXP` это **два уровня детализации**. `LIKE` проще и быстрее, `REGEXP` мощнее, но сложнее.

## 2) Практика

### Шаг 1. Структура таблицы `products`

**Схема (колонки):**

- `id` — `INTEGER PRIMARY KEY AUTOINCREMENT`
- `title` — `TEXT` (название товара, 1–3 слова)
- `description` — `TEXT` или `NULL` (краткое описание, иногда пусто)
- `count` — `INTEGER` (кол-во на складе; 0 допустим)
- `status` — `TEXT` (значения будем использовать `'yes'`/`'no'`; у нулевого `count` ставим `'no'`)
- `rating` — `REAL` (например, 3.8, 4.5)

**Сырой SQL на создание:**

```sql
CREATE TABLE IF NOT EXISTS products (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT,
  description TEXT,
  count INTEGER,
  status TEXT,
  rating REAL
);
```

---

### Шаг 2. Подготовка тестовых данных (10+ записей)

Требования к данным:

- есть товары с `description = NULL`;
- есть `count = 0` (и тогда `status = 'no'`);
- описания максимум из 3 слов;
- в некоторых описаниях присутствуют цифры (для задач с REGEXP/LIKE);
- рейтинги разные (в диапазоне, например, 2.5–5.0).

**Набор данных (для последующей вставки):**

```python
# Положим этот список в main.py (для единоразового заполнения) или в отдельный setup-скрипт:
SAMPLE_PRODUCTS = [
    ("Red Shirt",         "Cotton 100",     10, "yes", 4.7),  # описание с цифрами
    ("Blue Jeans",        "Denim",           0,  "no",  4.1),
    ("Black Shoes",       "Leather",        25, "yes", 3.9),
    ("Green Hat",         None,              3, "yes", 4.8),  # NULL в description
    ("Yellow Jacket",     "Rain proof",      0,  "no",  2.5),
    ("White Socks",       "Pack 3",         15, "yes", 4.3),  # цифра в описании
    ("Gray Scarf",        "Wool 80",         7, "yes", 3.5),  # цифра в описании
    ("Brown Belt",        "Genuine",         0,  "no",  4.0),
    ("Pink Dress",        "Silk",           12, "yes", 4.9),
    ("Orange Gloves",     "Winter",          1, "no",  3.2),
]
```

> Примечание: мы храним `status` как `'yes'/'no'`. Это удобно для заданий с `IN` и предсказуемо для фильтрации.

---

### Шаг 3. Создаём проект (3 модуля)

Структура каталога:

```
project/
  core.py
  logic.py
  main.py
```

- `core.py` — минимальный класс `Database` (подключение, регистрация `REGEXP`, методы для запросов, создание таблицы).
- `logic.py` — **функции**, каждая решает конкретную задачу SQL-фильтрации.
- `main.py` — меню, маппинг «номер → функция», вывод результатов, однократное заполнение таблицы тестовыми данными.

---

### Шаг 4. `core.py`: импорт, путь, каркас класса

#### **Импорты и константа пути к файлу БД**

```python
# core.py (фрагмент 1)
import sqlite3
from pathlib import Path
import re  # понадобится для регистрации REGEXP

DB_PATH = Path("shop.db")  # единая БД для урока
```

**Почему так:**

- `sqlite3` — стандартный драйвер SQLite в Python.
- `Path` — удобная, кроссплатформенная работа с путями.
- `re` — используем, чтобы зарегистрировать кастомную функцию `REGEXP` (в SQLite она не встроена по умолчанию).

#### **Класс `Database`: инициализация и подключение**

```python
# core.py (фрагмент 2)
class Database:
    def __init__(self, db_path: Path = DB_PATH):
        # создаём соединение один раз и используем повторно
        self.db_path = Path(db_path)
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row  # удобный доступ к колонкам по имени
        self._register_regexp()  # сразу подключаем REGEXP
```

**Комментарий:** один объект `Database` → одно соединение. `sqlite3.Row` позволяет печатать строки как `dict(row)`.

#### **`REGEXP`: статический метод и регистрация**

```python
# core.py (фрагмент 3)
class Database:
    # ... __init__ как выше ...

    @staticmethod
    def _regexp(pattern: str, value: str) -> int:
        """Возвращает 1, если regex 'pattern' находит совпадение в 'value', иначе 0."""
        if value is None:
            return 0
        try:
            return 1 if re.search(pattern, value) else 0
        except re.error:
            return 0

    def _register_regexp(self) -> None:
        # регистрируем SQL-функцию REGEXP с 2 параметрами
        self.conn.create_function("REGEXP", 2, self._regexp)
```

**Важно:** В «чистом» SQLite оператора `REGEXP` нет — мы его регистрируем сами, чтобы можно было писать `WHERE description REGEXP '^\d+$'`.

#### **Универсальные методы: изменения (commit) и выборка (fetchall)**

```python
# core.py (фрагмент 4)
class Database:
    # ... как выше ...

    def exec_write(self, sql: str, params: tuple | list[tuple] | None = None) -> None:
        """
        Для INSERT/UPDATE/DELETE/DDL.
        Если передан список кортежей params -> используем executemany.
        Иначе -> execute.
        """
        cur = self.conn.cursor()
        if params is None:
            cur.execute(sql)
        elif isinstance(params, list):
            cur.executemany(sql, params)
        else:
            cur.execute(sql, params)
        self.conn.commit()

    def exec_read(self, sql: str, params: tuple = ()) -> list[sqlite3.Row]:
        """Для SELECT-запросов: возвращаем все строки."""
        cur = self.conn.cursor()
        cur.execute(sql, params)
        return cur.fetchall()
```

**Зачем два метода:**

- `exec_write` — для запросов, меняющих данные или структуру (и commit).
- `exec_read` — для запросов выборки (SELECT), возвращаем список строк.

#### **Метод создания таблицы**

```python
# core.py (фрагмент 5)
class Database:
    # ... как выше ...

    def create_products_table(self) -> None:
        sql = """
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            description TEXT,
            count INTEGER,
            status TEXT,
            rating REAL
        );
        """
        self.exec_write(sql)
```

> На этом `core.py` готов: у нас есть подключение, REGEXP, методы на чтение/запись и создание таблицы.

---

### Шаг 5. `logic.py`: функции-задания

**Общее правило:** каждая функция принимает объект `db: Database`, выполняет запрос и возвращает список строк (`list[sqlite3.Row]`).
Печать/форматирование — в `main.py`.

В начале файла — импорт:

```python
# logic.py (фрагмент 1)
from core import Database
```

Дальше — задачи по темам:

#### **WHERE**

**Задание А:** «Вывести товары, у которых `count > 5`»

```python
# logic.py (фрагмент 2)
def products_count_gt(db: Database, n: int = 5):
    sql = "SELECT * FROM products WHERE count > ?;"
    return db.exec_read(sql, (n,))
```

**Задание Б:** «Вывести товары, которые в наличии (`status = 'yes'`)»

```python
def products_in_stock(db: Database):
    sql = "SELECT * FROM products WHERE status = 'yes';"
    return db.exec_read(sql)
```

#### **Операторы сравнения**

**Задание А:** «Товары с рейтингом выше 4.5»

```python
def products_rating_gt(db: Database, threshold: float = 4.5):
    sql = "SELECT * FROM products WHERE rating > ?;"
    return db.exec_read(sql, (threshold,))
```

**Задание Б:** «Товары с `count < 3` (мало на складе)»

```python
def products_low_stock(db: Database, limit: int = 3):
    sql = "SELECT * FROM products WHERE count < ?;"
    return db.exec_read(sql, (limit,))
```

#### **NULL / NOT NULL**

**Задание А:** «Найти товары без описания (`description IS NULL`)»

```python
def products_without_description(db: Database):
    sql = "SELECT * FROM products WHERE description IS NULL;"
    return db.exec_read(sql)
```

**Задание Б:** «Найти товары, у которых описание задано (`IS NOT NULL`)»

```python
def products_with_description(db: Database):
    sql = "SELECT * FROM products WHERE description IS NOT NULL;"
    return db.exec_read(sql)
```

#### **BETWEEN**

**Задание:** «Товары с `rating` между 3.5 и 5.0»

```python
def products_rating_between(db: Database, low: float = 3.5, high: float = 5.0):
    sql = "SELECT * FROM products WHERE rating BETWEEN ? AND ?;"
    return db.exec_read(sql, (low, high))
```

#### **IN**

**Задание:** «Товары со статусом в наборе (например `'yes'` или `'no'`)»

```python
def products_status_in(db: Database, statuses: list[str] = None):
    if statuses is None:
        statuses = ["yes", "no"]
    placeholders = ",".join(["?"] * len(statuses))
    sql = f"SELECT * FROM products WHERE status IN ({placeholders});"
    return db.exec_read(sql, tuple(statuses))
```

#### **LIKE (поиск по шаблону)**

**Задание:** «Найти товары, в описании которых содержится слово `'Shirt'`»

```python
def products_description_like(db: Database, keyword: str = "Shirt"):
    # по умолчанию регистрозависимо; для независимого — LOWER(description) LIKE LOWER(?)
    sql = "SELECT * FROM products WHERE description LIKE ?;"
    return db.exec_read(sql, (f"%{keyword}%",))
```

#### **REGEXP**

**Задание:** «Найти товары, где `description` содержит цифры»

```python
def products_description_has_digits(db: Database):
    sql = r"SELECT * FROM products WHERE description REGEXP ?;"
    return db.exec_read(sql, (r"\d+",))
```

#### **Комбинированные задания**

**Задание А:** «Показать уникальные статусы (`DISTINCT`) только для товаров с рейтингом `> 4.0`»

```python
def distinct_status_for_high_rating(db: Database, threshold: float = 4.0):
    sql = "SELECT DISTINCT status FROM products WHERE rating > ?;"
    return db.exec_read(sql, (threshold,))
```

**Задание Б:** «Вывести `title`, `description` и литерал `'HOT'` (как `tag`) для товаров с рейтингом `> 4.5`»

```python
def hot_products(db: Database, threshold: float = 4.5):
    sql = "SELECT title, description, 'HOT' AS tag FROM products WHERE rating > ?;"
    return db.exec_read(sql, (threshold,))
```

> Подсказка: сюда же можно добавить алиасы (`AS alias_name`) или объединение полей, если хочешь расширить практику.

---

### Шаг 6. `main.py`: меню, маппинг, заполнение данными

В `main.py` мы:

1. создаём объект `Database`,
2. создаём таблицу `products`,
3. **один раз** заполняем тестовыми данными (если таблица пустая),
4. объявляем **маппинг меню** номер → функция,
5. запускаем цикл выбора, печатаем результаты, ждём Enter для продолжения.

#### **Импорты и подготовка данных**

```python
# main.py (фрагмент 1)
from core import Database
import logic

# Тестовые данные из шага 2:
SAMPLE_PRODUCTS = [
    ("Red Shirt",     "Cotton 100", 10, "yes", 4.7),
    ("Blue Jeans",    "Denim",       0, "no",  4.1),
    ("Black Shoes",   "Leather",    25, "yes", 3.9),
    ("Green Hat",     None,          3, "yes", 4.8),
    ("Yellow Jacket", "Rain proof",  0, "no",  2.5),
    ("White Socks",   "Pack 3",     15, "yes", 4.3),
    ("Gray Scarf",    "Wool 80",     7, "yes", 3.5),
    ("Brown Belt",    "Genuine",     0, "no",  4.0),
    ("Pink Dress",    "Silk",       12, "yes", 4.9),
    ("Orange Gloves", "Winter",      1, "no",  3.2),
]
```

#### **Инициализация БД (создание таблицы и единоразовая загрузка данных)**

```python
# main.py (фрагмент 2)
def init_data(db: Database):
    db.create_products_table()
    # есть ли данные?
    exists = db.exec_read("SELECT id FROM products LIMIT 1;")
    if not exists:
        db.exec_write(
            "INSERT INTO products (title, description, count, status, rating) VALUES (?, ?, ?, ?, ?);",
            SAMPLE_PRODUCTS  # список кортежей -> executemany
        )
```

#### **Маппинг меню «номер → функция»**

```python
# main.py (фрагмент 3)
def print_rows(rows):
    if not rows:
        print("Ничего не найдено.")
        return
    for r in rows:
        # r — sqlite3.Row, удобно привести к dict для читабельной печати
        print(dict(r))

def build_menu(db: Database):
    return {
        "1": ("WHERE: count > 5",                 lambda: logic.products_count_gt(db, 5)),
        "2": ("WHERE: status = 'yes'",            lambda: logic.products_in_stock(db)),
        "3": ("Сравнение: rating > 4.5",         lambda: logic.products_rating_gt(db, 4.5)),
        "4": ("Сравнение: count < 3",            lambda: logic.products_low_stock(db, 3)),
        "5": ("NULL: description IS NULL",       lambda: logic.products_without_description(db)),
        "6": ("NOT NULL: description IS NOT NULL", lambda: logic.products_with_description(db)),
        "7": ("BETWEEN: rating 3.5–5.0",         lambda: logic.products_rating_between(db, 3.5, 5.0)),
        "8": ("IN: status IN ('yes','no')",      lambda: logic.products_status_in(db, ["yes","no"])),
        "9": ("LIKE: description contains 'Shirt'", lambda: logic.products_description_like(db, "Shirt")),
        "10":("REGEXP: description has digits",  lambda: logic.products_description_has_digits(db)),
        "11":("DISTINCT+WHERE: statuses for rating>4.0", lambda: logic.distinct_status_for_high_rating(db, 4.0)),
        "12":("Литерал 'HOT' для rating>4.5",    lambda: logic.hot_products(db, 4.5)),
        "0": ("Выход",                            None),
    }
```

#### **Основной цикл и «Нажмите Enter, чтобы продолжить»**

```python
# main.py (фрагмент 4)
def main():
    db = Database()
    init_data(db)

    menu = build_menu(db)
    while True:
        print("\n=== Меню фильтрации (products) ===")
        for key, (title, _) in menu.items():
            print(f"{key}) {title}")
        choice = input("Выберите пункт: ").strip()

        if choice == "0":
            print("Пока!")
            break

        item = menu.get(choice)
        if not item:
            print("Неверный выбор.")
            continue

        _, action = item
        rows = action()  # вызываем функцию из logic.py
        print_rows(rows)
        input("\nНажмите Enter, чтобы продолжить...")

if __name__ == "__main__":
    main()
```

---

## 3) Вопросы

1. **Что делает оператор `WHERE` и зачем он нужен в SQL-запросах?**
2. **Какой результат даст запрос:**

   ```sql
   SELECT * FROM products WHERE count > 10;
   ```

3. **Чем отличается оператор `=` от оператора `!=` при фильтрации данных?**
4. **Для чего используется выражение `IS NULL` и чем оно отличается от проверки `= NULL`?**
5. **Напиши SQL-запрос, который выберет товары с рейтингом от 3.5 до 5.0 включительно.**
6. **Что делает шаблон `%` в операторе `LIKE`? Приведи пример поиска всех товаров, название которых оканчивается на `'shirt'`.**
7. **Что делает символ `_` (нижнее подчёркивание) в `LIKE` и чем он отличается от `%`?**
8. **Что позволяет делать оператор `REGEXP` в SQLite? Приведи пример поиска товаров, в описании которых встречаются цифры.**

---

## 4) Домашнее задание

### 1. Структура проекта

Проект должен состоять из следующих файлов:

- **core.py** – класс для взаимодействия с БД.
- **seed.py** – отдельный модуль для создания таблицы и заполнения её тестовыми данными.
- **logic.py** – функции с запросами для выполнения заданий.
- **main.py** – меню для запуска программы и выбора заданий.

---

### 2. Структура таблицы в БД

Таблица `users` должна иметь поля:

- `id` – целое число, первичный ключ.
- `login` – логин пользователя (текст).
- `password` – пароль (текст).
- `email` – почта (текст).
- `phone` – телефон (текст, может быть `NULL`).
- `level` – уровень пользователя (целое число от 1 до 5).

---

## 3. Данные для заполнения

Добавьте **10 пользователей**. Данные должны быть разнообразными:

- У некоторых пользователей `phone = NULL`.
- Уровни (`level`) должны быть разными (от 1 до 5).
- В `email` и `login` должны быть такие, чтобы можно было протестировать `LIKE` и `REGEXP` (например, логин с цифрой, email с определённым словом).

Пример (можно менять):

```text
1, "alex1", "pass123", "alex@example.com", "1234567890", 3
2, "maria", "qwerty", "maria@gmail.com", NULL, 5
3, "john_doe", "111111", "john@mail.com", "9876543210", 2
4, "kate2025", "passkate", "kate@mail.com", NULL, 1
5, "mike", "mypass", "mike@shop.com", "5551234", 4
6, "linda", "linpass", "linda2024@gmail.com", NULL, 2
7, "bob77", "passbob", "bob@example.com", "999000111", 3
8, "sara", "sarapass", "sara@mail.ru", NULL, 1
9, "test123", "testpass", "test123@mail.com", "111222333", 5
10, "eva", "evapass", "eva2025@gmail.com", "333444555", 4
```

---

## 4. Класс для работы с БД (core.py)

Класс `Database` должен содержать:

- подключение к SQLite (`sqlite3.connect`),
- метод `execute_query(query, params=())` – для вставки/обновления с `commit`,
- метод `fetch_all(query, params=())` – для получения данных (`fetchall`),
- регистрацию функции `REGEXP` (для поиска с регулярками).

---

## 5. Заполнение БД (seed.py)

Отдельный cкрипт для заполнения БД:

1. Создания таблицы `users`.
2. Заполнения её тестовыми данными (10 пользователей).

---

## 6. Логика SQL-запросов (logic.py)

Реализовать **10 функций** для следующих заданий:

1. **WHERE + сравнение**

   - Найти пользователей, у которых `level > 3`.
   - Найти пользователей, у которых `id < 5`.

2. **Операторы сравнения**

   - Пользователи с `level = 5`.
   - Пользователи, у которых `id != 1`.

3. **NULL / NOT NULL**

   - Найти пользователей без телефона (`phone IS NULL`).
   - Найти пользователей с телефоном (`phone IS NOT NULL`).

4. **BETWEEN**

   - Найти пользователей, у которых `level BETWEEN 2 AND 4`.

5. **IN**

   - Найти пользователей с уровнем `IN (1, 3, 5)`.

6. **LIKE**

   - Найти пользователей, у которых `login` начинается на `'a'`.
   - Найти пользователей, у которых `email` содержит `'gmail'`.

7. **REGEXP**

   - Найти пользователей, у которых `login` содержит цифры.
   - Найти пользователей, у которых `email` оканчивается на `.ru` или `.com`.

---

## 7. Главный модуль (main.py)

- Вывод меню (список заданий).
- Маппинг: номер → функция.
- Ожидание нажатия Enter перед возвратом в меню.
- Возможность выхода из программы.
- Запуск скрипта с заполнением БД.

---

[Предыдущий урок](lesson04.md) | [Следующий урок](lesson06.md)
