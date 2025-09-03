# Модуль 1 · Урок 3. Работа с SQLite через Python (sqlite3).

## **Цель урока:**

- Понять базовый цикл работы с SQLite в Python: импорт, путь, подключение, курсор, сырой `CREATE TABLE`, вставки (`execute` / `executemany`), `commit`, закрытие, простые SELECT-запросы и способы чтения результатов (`fetchall`, `fetchone`, `fetchmany`).
- Посмотреть, как `with` упрощает те же шаги.

---

## 1) Импорт необходимых модулей

**Зачем:** нам нужны стандартный модуль `sqlite3` и `Path` из `pathlib` для аккуратной работы с путями.

```python
import sqlite3
from pathlib import Path
```

**Пояснение:**

- `sqlite3` — встроенный модуль Python для работы с SQLite.
- `Path` — удобный объект для путей; безопаснее, чем строковые пути (кросс-платформенно).

---

## 2) Создание константы «путь к файлу»

**Зачем:** чтобы знать, где будет лежать файл базы данных (`db.sqlite3`).

```python
DB_FILE = Path("db.sqlite3")       # относительный путь — файл в папке проекта
print("БД будет создана по пути:", DB_FILE.resolve())
```

**Пояснение:**

- `DB_FILE.resolve()` покажет абсолютный путь — удобно понимать, какой файл вы открываете.
- При первом подключении SQLite сам создаст файл, если его нет.

---

## 3) Создание соединения (пока без `with`)

**Зачем:** соединение (Connection) — основной объект для работы с БД.

```python
# Подключаемся к базе (создаст db.sqlite3, если его нет)
conn = sqlite3.connect(str(DB_FILE))
print("Соединение открыто:", conn)
```

**Пояснение:**

- `sqlite3.connect()` возвращает объект `Connection`.
- Здесь мы передаём `str(DB_FILE)` для совместимости с разными версиями Python.
- По умолчанию автосохранения (autocommit) нет — нужно вызывать `conn.commit()` после изменений.

---

## 4) Создание курсора

**Зачем:** через курсор (`Cursor`) выполняются SQL-запросы и читаются результаты.

```python
cursor = conn.cursor()
print("Курсор создан:", cursor)
```

**Пояснение:**

- `cursor` позволяет вызывать `execute`, `executemany`, `fetchone` и т.д.

---

## 5) Сырой SQL: CREATE TABLE (через `execute`)

**Задача:** создать простую таблицу `users` с четырьмя полями.

```python
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    age INTEGER,
    email TEXT
);
""")
print("Таблица users создана (если не была создана).")
```

**Пояснение:**

- `CREATE TABLE IF NOT EXISTS` — безопасная команда: если таблицы нет — создаст, если есть — не будет ошибки.
- `AUTOINCREMENT` — необязательно, но ясно показывает новичку, что `id` автоматически увеличивается. (В SQLite `INTEGER PRIMARY KEY` обычно уже даёт автоинкремент поведение; `AUTOINCREMENT` — опционально.)

---

## 6) Вставка данных: `execute` vs `executemany`

**Зачем:** показать разницу между одиночной вставкой и вставкой множества строк.

### Вариант A — одиночная вставка (`execute`)

```python
cursor.execute("INSERT INTO users (name, age, email) VALUES (?, ?, ?);",
               ("Иван Иванов", 28, "ivan@example.com"))
print("Вставлена одна строка (execute).")
```

**Пояснение:**

- `?` — плейсхолдер. **Никогда** не подставляйте строки напрямую через f-строки — это небезопасно (SQL-инъекция) и шатко при наличии кавычек в данных.

### Вариант B — массовая вставка (`executemany`)

```python
rows = [
    ("Мария Петрова", 34, "maria@example.com"),
    ("Chen Li", 22, None),   # None -> NULL
    ("Amina Yusuf", 40, "amina@example.com"),
]
cursor.executemany("INSERT INTO users (name, age, email) VALUES (?, ?, ?);", rows)
print("Вставлено несколько строк (executemany).")
```

**Пояснение:**

- `executemany` эффективнее, если нужно вставить много строк.
- `None` в Python превращается в `NULL` в SQLite.

---

## 7) COMMIT (сохранение изменений)

**Зачем:** без `commit()` изменения не сохранятся в файле базы (если вы не используете `with`).

```python
conn.commit()
print("Изменения сохранены (conn.commit()).")
```

**Пояснение:**

- `commit()` фиксирует текущую транзакцию. Если пропустить — вставки/обновления могут быть потеряны при закрытии соединения.

---

## 8) Простые SELECT-запросы

**Задача:** сделать несколько простых выборок и показать разные методы чтения результатов.

### Запрос 1 — `SELECT *` и `fetchall()`

```python
cursor.execute("SELECT * FROM users;")
all_users = cursor.fetchall()   # список кортежей
print("\nРезультат SELECT * (fetchall):")
for row in all_users:
    print(row)   # row — кортеж: (id, name, age, email)
```

**Пояснение:**

- `fetchall()` возвращает все найденные строки как список кортежей. Удобно для небольших наборов.

### Запрос 2 — `SELECT ... WHERE` и `fetchone()`

```python
cursor.execute("SELECT id, name, age FROM users WHERE age >= ?;", (30,))
one = cursor.fetchone()   # первая строка результата или None
print("\nРезультат SELECT ... WHERE (fetchone):")
print(one)   # например: (2, 'Мария Петрова', 34)
```

**Пояснение:**

- `fetchone()` возвращает одну строку (первую) или `None`, если ничего не найдено.

### Запрос 3 — `fetchmany(n)` (пакетная выборка)

```python
cursor.execute("SELECT id, name FROM users ORDER BY id;")
batch = cursor.fetchmany(2)   # взять первые 2 строки
print("\nРезультат fetchmany(2):")
for r in batch:
    print(r)
```

**Пояснение:**

- `fetchmany(n)` удобно, если результат большой — можно читать партиями.

> Важно: после `fetchone()`/`fetchmany()` курсор «съедает» возвращаемые строки — если нужно снова получить те же данные, заново выполните `execute()`.

---

## 9) Закрытие курсора и соединения

**Зачем:** освобождаем ресурсы.

```python
cursor.close()
conn.close()
print("\nКурсор и соединение закрыты.")
```

**Пояснение:**

- Закрывать соединение и курсор — хорошая практика. На коротких скриптах интерпретатор всё равно закроет при завершении, но явное закрытие демонстрирует порядок действий.

---

## 10) Как тот же код выглядит с `with` (контекстным менеджером)

**Зачем:** показать более «питоновый» и безопасный вариант, который автоматически управляет транзакцией (`commit`/`rollback`) при выходе из блока.

```python
from pathlib import Path
import sqlite3

DB_FILE = Path("db.sqlite3")

# Вариант с with — короче и безопаснее по ошибкам
with sqlite3.connect(str(DB_FILE)) as conn2:
    cur2 = conn2.cursor()
    cur2.execute("CREATE TABLE IF NOT EXISTS demo (id INTEGER PRIMARY KEY, val TEXT);")
    cur2.execute("INSERT INTO demo (val) VALUES (?);", ("пример",))
    # при выходе из with Python автоматически выполнит commit (если не было исключения)
    # и закроет соединение
print("Секция с with выполнена — commit выполнен автоматически при нормальном выходе.")
```

**Пояснение:**

- `with sqlite3.connect(...) as conn:` — при выходе: если всё прошло OK — `commit()` выполнится, если было исключение — `rollback()`.
- `with` сокращает рутинный код и уменьшает шанс забыть `commit()`/`close()`.

---

## 11) Полезная таблица-справка (коротко)

| Операция           | Метод                                    | Возвращаемое / примечание             |
| ------------------ | ---------------------------------------- | ------------------------------------- |
| Подключиться       | `sqlite3.connect(path)`                  | `Connection`                          |
| Создать курсор     | `conn.cursor()`                          | `Cursor`                              |
| Выполнить один SQL | `cursor.execute(sql, params)`            | возвращает `Cursor`                   |
| Вставить много     | `cursor.executemany(sql, seq_of_params)` | эффективнее при множестве строк       |
| Считать все        | `cursor.fetchall()`                      | список кортежей                       |
| Считать одну       | `cursor.fetchone()`                      | один кортеж или `None`                |
| Считать n          | `cursor.fetchmany(n)`                    | список до n строк                     |
| Сохранить          | `conn.commit()`                          | фиксирует изменения                   |
| Откатить           | `conn.rollback()`                        | отменить изменения текущей транзакции |
| Закрыть курсор     | `cursor.close()`                         | освобождение ресурсов                 |
| Закрыть соединение | `conn.close()`                           | обязательно при завершении работы     |

---

## 12) Важные советы

- Всегда используйте плейсхолдеры (`?`) — безопасно и правильно при подстановке данных.
- `executemany` — для массовой вставки.
- `commit()` обязателен, если вы не используете `with`.
- Если вам нужно повторно прочитать те же данные — повторно вызовите `execute()` (курсоры не «перематываются»).
- При работе в учебных скриптах повторный запуск может добавить дубли — будьте к этому готовы (можно перед вставкой очистить таблицу `DELETE FROM users;` — опционально).

---

## 13) Полный пример файла `main.py` (собранный из шагов выше)

> Ниже — **полный последовательный скрипт**, который реализует все шаги: создание файла/таблицы, вставки (`execute` + `executemany`), пример трёх видов `SELECT` (`fetchall`, `fetchone`, `fetchmany`), закрытие, и небольшой пример с `with`.

```python
# main.py
# Пошаговый учебный пример работы с sqlite3 — без функций (для новичков)

import sqlite3
from pathlib import Path

# Шаг 1–2: путь к файлу БД
DB_FILE = Path("db.sqlite3")
print("БД будет создана по пути:", DB_FILE.resolve())

# Шаг 3: создать соединение
conn = sqlite3.connect(str(DB_FILE))
print("Соединение открыто:", conn)

# Шаг 4: создать курсор
cursor = conn.cursor()
print("Курсор создан:", cursor)

# Шаг 5: создать таблицу (execute)
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    age INTEGER,
    email TEXT
);
""")
print("Таблица users создана (если не была).")

# Шаг 6: вставка данных
#  - одиночная вставка (execute)
#  - массовая вставка (executemany)

# Одиночная вставка:
cursor.execute("INSERT INTO users (name, age, email) VALUES (?, ?, ?);",
               ("Иван Иванов", 28, "ivan@example.com"))
print("Вставлена 1 строка (execute).")

# Массовая вставка:
rows = [
    ("Мария Петрова", 34, "maria@example.com"),
    ("Chen Li", 22, None),
    ("Amina Yusuf", 40, "amina@example.com"),
]
cursor.executemany("INSERT INTO users (name, age, email) VALUES (?, ?, ?);", rows)
print("Вставлено несколько строк (executemany).")

# (Опционально) Если хотите, чтобы повторные запуски не дублировали данные,
# можно перед вставкой очистить таблицу:
# cursor.execute("DELETE FROM users;")
# Но в уроке мы пока не делаем этого автоматически.

# Шаг 7: сохранить изменения (commit)
conn.commit()
print("Изменения сохранены (conn.commit()).")

# Шаг 8: простые SELECT-запросы
# 1) SELECT * и fetchall()
cursor.execute("SELECT * FROM users;")
all_users = cursor.fetchall()
print("\nSELECT * (fetchall) — все строки:")
for row in all_users:
    print(row)

# 2) SELECT ... WHERE и fetchone()
cursor.execute("SELECT id, name, age FROM users WHERE age >= ?;", (30,))
one = cursor.fetchone()
print("\nSELECT ... WHERE (fetchone) — первая подходящая строка:")
print(one)

# 3) fetchmany(n)
cursor.execute("SELECT id, name FROM users ORDER BY id;")
batch = cursor.fetchmany(2)
print("\nfetchmany(2) — первые 2 строки (партией):")
for r in batch:
    print(r)

# Шаг 9: закрыть курсор и соединение
cursor.close()
conn.close()
print("\nКурсор и соединение закрыты.")

# Шаг 10: тот же код с with (пример)
```

```python
# Небольшой пример, как with упрощает commit/rollback:
with sqlite3.connect(str(DB_FILE)) as conn2:
    cur2 = conn2.cursor()
    cur2.execute("CREATE TABLE IF NOT EXISTS demo (id INTEGER PRIMARY KEY, val TEXT);")
    cur2.execute("INSERT INTO demo (val) VALUES (?);", ("пример",))
    # нет необходимости явно вызывать conn2.commit(): при нормальном выходе из with commit выполнится
print("Секция с with выполнена — commit выполнен автоматически при нормальном выходе.")
```

---

## 14) Домашнее задание

1. Импортируйте модуль для работы с SQLite
2. Импортируйте модуль для работы с путями файлов
3. Создайте константную переменную с названием файла Базы Данных `db.sqlite3`
4. Создайте соединение к БД и курсор для взаимодействия с ней
5. Создайте пустую таблицу `products` с помощью "сырого" запроса. Поля в таблице: `id`, `name`, `price`, `count`
6. Заполните таблицу 4 продуктами. В третьем продукте поле цены должно быть `NULL`
7. Выведите в консоль первые три продукта
8. Закройте соединение в конце программы

---

[Предыдущий урок](lesson02.md) | [Следующий урок](lesson04.md)
