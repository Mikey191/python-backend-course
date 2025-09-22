# Модуль 1 · Урок 6. Сортировка и ограничение выборки

## **Цель урока:**

- Научиться использовать оператор `WHERE` в связке с `AND`, `OR`, `NOT`.
- Освоить различную сортировку с помощью `ORDER BY`.
- Использовать `LIMIT` и `OFFSET` для ограничения количества строк.

# 1) Теория.

## Продолжаем работать с таблицей `products`

Напоминаю схему, с которой мы работаем:

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

Каждая строка — это товар: название, краткое описание, количество на складе, статус (`'yes'`/`'no'`) и рейтинг (вещественное число). Во всех примерах ниже будем оперировать этими полями.

---

## Генерация данных (пример)

Для иллюстраций используйте такой набор строк:

```sql
INSERT INTO products (title, description, count, status, rating) VALUES
('Red Shirt',     'Cotton 100',      10, 'yes', 4.7),
('Blue Jeans',    'Denim slim fit',   5, 'yes', 4.3),
('Black Jacket',  'Leather',          2, 'no',  4.9),
('White Sneakers','Sport shoes',     15, 'yes', 4.6),
('Green Hat',     'Wool',             8, 'yes', 3.9),
('Yellow T-shirt','Casual wear',     12, 'yes', 4.1),
('Gray Socks',    'Comfort pack',     20, 'yes', 3.5),
('Brown Belt',    'Leather',          3, 'no',  4.0),
('Purple Scarf',  'Silk',             6, 'yes', 4.8),
('Orange Hoodie', 'Sport style',      7, 'yes', 4.2);
```

Эти данные дают разнообразие: разные `count`, `rating`, `status`, тексты описаний — есть где применить `LIKE`/`REGEXP`, сортировку и лимиты.

---

## `WHERE` + `AND` — детально

`AND` соединяет два (и более) логических условия и возвращает `TRUE` только если **все** условия истинны.

### Синтаксис:

```sql
SELECT * FROM products
WHERE condition1 AND condition2 AND ...;
```

### Пример:

«Выбрать товары в наличии и с рейтингом выше 4.5»

```sql
SELECT * FROM products
WHERE status = 'yes' AND rating > 4.5;
```

### Нюансы и советы:

- `AND` имеет **более высокий приоритет** чем `OR`. Это означает, что выражение `A OR B AND C` интерпретируется как `A OR (B AND C)`. Если вы хотели `(A OR B) AND C`, нужны скобки. (Подробнее — операторная приоритетность ниже.)
- Сравнения могут вернуть `NULL` (например, `description = NULL` — неверно). Для проверки `NULL` используйте `IS NULL`.
- Когда сочетаете `AND` с множеством условий, подумайте о порядке: лучше ставить самые селективные условия (те, что отбирают больше) первыми для читаемости; оптимизатор сам решит порядок выполнения, но читаемый код легче поддерживать.
- `AND` поддерживает любые булевы выражения: сравнения, `IN`, `LIKE`, `BETWEEN`, вложенные `EXISTS` и т. д.

---

## `WHERE` + `OR` — детально

`OR` возвращает `TRUE`, если хотя бы одно из условий истинно.

### Синтаксис:

```sql
SELECT * FROM products
WHERE condition1 OR condition2 OR ...;
```

### Пример:

«Выбрать товары либо с рейтингом > 4.5, либо с количеством > 10»

```sql
SELECT * FROM products
WHERE rating > 4.5 OR count > 10;
```

### Когда `OR` полезен:

- Поиск по нескольким альтернативным значениям (хотя для набора значений чаще удобнее `IN`).
- Комбинация разных критериев, не требующих соблюдения всех сразу.

### Нюансы и ловушки:

- Как уже сказано, `AND` имеет более высокий приоритет, чем `OR`. Поэтому выражение

  ```sql
  WHERE a = 1 OR b = 2 AND c = 3
  ```

  эквивалентно

  ```sql
  WHERE a = 1 OR (b = 2 AND c = 3)
  ```

  Если вы хотели `(a = 1 OR b = 2) AND c = 3`, обязательно используйте скобки:

  ```sql
  WHERE (a = 1 OR b = 2) AND c = 3;
  ```

- Широкое использование `OR` может мешать использованию индексов в планах выполнения и снижать производительность: в сложных запросах лучше протестировать планы или рефакторить `OR` в `UNION` (в некоторых случаях).

---

## `WHERE` + `NOT` — детально

`NOT` инвертирует логическое значение условия: `NOT TRUE → FALSE`, `NOT FALSE → TRUE`, `NOT UNKNOWN → UNKNOWN` (см. про NULL/трёхзначную логику ниже).

### Синтаксис:

```sql
SELECT * FROM products
WHERE NOT condition;
```

### Пример:

«Выбрать товары, которые **не** в наличии»

```sql
SELECT * FROM products
WHERE NOT status = 'yes';
-- или явный вариант:
WHERE status != 'yes' OR status IS NULL
```

### Нюансы:

- `NOT` имеет более высокий приоритет, чем `AND` и `OR` — поэтому `NOT a = 1 AND b = 2` обычно читают как `(NOT a = 1) AND b = 2`. В практике часто ставят скобки для ясности.
- `NOT` + `IN`: `NOT status IN ('yes', 'no')` эквивалентно `status NOT IN ('yes','no')`. Но будьте осторожны с `NULL` в списке — логика `IN/NOT IN` при наличии `NULL` может быть хитрой; стандартно лучше явно обрабатывать `NULL`. Документация SQLite описывает матрицу поведения `IN/NOT IN`.

---

## Что такое сортировка и где применяется

**Сортировка** — это процесс упорядочивания данных по определённому критерию, например, по возрастанию или убыванию значений одного или нескольких столбцов. В SQL для сортировки используется оператор `ORDER BY`.

**Сортировка применяется в следующих случаях:**

- При выводе данных пользователю: Чтобы результаты были удобны для восприятия, например, список товаров по цене или алфавиту.
- Для аналитики и отчетности: Часто требуется видеть данные в определённом порядке для анализа, например, топ-10 продаж или последние транзакции.
- Для поиска и фильтрации: Сортировка облегчает поиск нужной информации, например, самых новых или самых старых записей.

---

## 7. `ORDER BY` + `ASC` / `DESC` — подробности и примеры

`ORDER BY` управляет порядком возвращаемых строк. По умолчанию SQL не гарантирует порядок без `ORDER BY`. В реальных приложениях сортировка нужна для:

- выдачи «лучших» результатов сверху (например, топ-5 по рейтингу);
- упорядочивания списков в интерфейсе (по алфавиту, цене и т. д.);
- детерминирования вывода перед применением `LIMIT` (иначе `LIMIT` даст «любой» набор строк).

**Важно:** если используете `LIMIT` для выбора «первых N», всегда указывайте `ORDER BY`, чтобы результат был детерминирован.

### Синтаксис простой:

```sql
SELECT * FROM products
ORDER BY rating ASC;   -- по возрастанию (по умолчанию)
SELECT * FROM products
ORDER BY rating DESC;  -- по убыванию
```

### Множественная сортировка (tie-breakers)

Можно сортировать по нескольким колонкам — первая колонка первична, в случае равенства применяется вторая:

```sql
SELECT * FROM products
ORDER BY status ASC, rating DESC;
-- сначала все строки упорядочены по status; внутри одного status — по рейтингу убыванию
```

### Сортировка по выражению / функции

Можно сортировать по вычисляемому выражению:

```sql
SELECT *, LENGTH(title) AS title_len FROM products
ORDER BY title_len DESC;
-- или прямо:
SELECT * FROM products ORDER BY LENGTH(title) DESC;
```

### Коллаторы и регистрозависимость

- По умолчанию сортировка строк зависит от коллации (в SQLite по умолчанию — BINARY, которое чувствительно к регистру). Чтобы получить нечувствительную сортировку по строке, используйте `COLLATE NOCASE` или приводите к одному регистру (`ORDER BY LOWER(title)`).

_Коллация (Collation) — это набор правил, определяющих, как сравниваются и сортируются символьные данные в базе данных._

```sql
SELECT * FROM products ORDER BY title COLLATE NOCASE ASC;
```

### `NULL` при сортировке

- По умолчанию в SQLite `NULL` считается «меньше» любых значений, поэтому `ORDER BY col ASC` поместит строки с `NULL` первыми, а `ORDER BY col DESC` — последними. В более новых версиях SQLite можно указать `ASC NULLS LAST` / `DESC NULLS FIRST` — см. документацию. Это поведение специфично для СУБД; в других СУБД дефолт может отличаться.

---

## 8. `LIMIT` — зачем нужен и примеры

`LIMIT` ограничивает количество строк, возвращаемых запросом.

### Примеры:

- Показать первые 3 товара по рейтингу:

```sql
SELECT * FROM products
ORDER BY rating DESC
LIMIT 3;
```

- Использовать параметр (в приложении):

```sql
SELECT * FROM products ORDER BY rating DESC LIMIT ?;
-- передать число вместо ?
```

### Нюансы:

- Без `ORDER BY` `LIMIT` даст «произвольные» строки — результат зависит от плана выполнения и не гарантирован детерминирован. Всегда используйте `ORDER BY`, если ожидаете именно «первые N по критерию».
- Для пагинации (многостраничный вывод) `LIMIT` часто комбинируют с `OFFSET`. Однако для больших смещений (`OFFSET 100000`) производительность падает, так как СУБД всё равно выбирает и пропускает строки. Для масштабных систем рекомендуют keyset (seek) pagination (см. ниже).

---

## 9. `OFFSET` — зачем нужен и примеры

`OFFSET` пропускает указанное количество строк и начинает выдачу с указанной позиции.

### Пример:

«Показать 3 записи, начиная со второй (т.е. пропустить первую)»

```sql
SELECT * FROM products
ORDER BY rating DESC
LIMIT 3 OFFSET 1;
```

Это полезно для реализации постраничного вывода:

- Страница 1: `LIMIT 10 OFFSET 0`
- Страница 2: `LIMIT 10 OFFSET 10`
- и т.д.

### Производительность и альтернативы:

- `OFFSET` работает, но неэффективен на больших страницах, т.к. СУБД должна просчитать и пропустить `OFFSET` строк.
- Для больших таблиц используйте keyset (seek) pagination: сохраняете последний ключ (например, `(rating, id)`) и в следующем запросе делаете `WHERE (rating, id) < (?, ?)` + `ORDER BY rating DESC, id DESC LIMIT 10`. Это экономит отработку и эффективно использует индексы.

---

## 10. Тонкости логики выражений и NULL (трёхзначная логика)

### Трёхзначная логика

SQL использует три значения булевой логики: `TRUE`, `FALSE`, `UNKNOWN` (когда участвует `NULL`). В `WHERE` выбираются только строки, где условие истинно (`TRUE`). Если выражение возвращает `UNKNOWN` (например, `col = NULL`), строка **не попадёт** в результат.

Примеры:

- `description = NULL` → всегда `UNKNOWN` (не использовать).
- `description IS NULL` → корректно вернёт `TRUE` для строк с `NULL`.

### Сочетание логических операторов с NULL

- `NULL` в условиях делает результат `UNKNOWN`, поэтому комбинации с `AND/OR/NOT` могут дать неожиданные результаты. Всегда проверяйте `IS NULL` отдельно, если пустые значения важны.

---

## 11. Приоритет операторов (коротко, но важно)

Порядок вычисления логических операторов (в большинстве СУБД и в SQLite) — от **высокого к низкому**:

1. `NOT`
2. `AND`
3. `OR`

Это значит, что `NOT a AND b OR c` интерпретируется как `((NOT a) AND b) OR c`. Чтобы избежать двусмысленности используйте **скобки**. Официальная документация SQLite и общие рекомендации подчёркивают важность явных скобок в сложных выражениях.

---

## 12. Примеры «связок» с пройденными темами (комбинирование)

Ниже — краткие примеры, как объединять те, что уже изучили (DISTINCT, LENGTH, LIKE, BETWEEN, IS NULL) с ORDER/LIMIT/OFFSET:

- **Уникальные статусы пользователей только для товаров с рейтингом > 4.0**:

  ```sql
  SELECT DISTINCT status FROM products
  WHERE rating > 4.0
  ORDER BY status;
  ```

- **Показать 5 самых «длинных» названий товаров**:

  ```sql
  SELECT title, LENGTH(title) AS len
  FROM products
  ORDER BY len DESC
  LIMIT 5;
  ```

- **Поиск (LIKE) и сортировка (без учёта регистра)**:

  ```sql
  SELECT * FROM products
  WHERE LOWER(description) LIKE '%sport%'
  ORDER BY LOWER(title) ASC;
  ```

- **Pagination (стр. 3, 10 записей на страницу)**:

  ```sql
  SELECT * FROM products
  ORDER BY rating DESC, id DESC
  LIMIT 10 OFFSET 20;  -- третья страница (0-based)
  ```

- **Keyset pagination (рекомендуется при больших данных)**:

  ```sql
  -- допустим, у вас уже была последняя строчка с rating=4.1, id=45
  SELECT * FROM products
  WHERE (rating < 4.1) OR (rating = 4.1 AND id < 45)
  ORDER BY rating DESC, id DESC
  LIMIT 10;
  ```

---

# 2) Практика

## Шаг 1 — напоминание о таблице и данных

**Таблица:**

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

**Набор данных (пример для загрузки в БД один раз, можно поместить в `seed.py`):**

```sql
INSERT INTO products (title, description, count, status, rating) VALUES
('Red Shirt',     'Cotton 100',      10, 'yes', 4.7),
('Blue Jeans',    'Denim slim fit',   5, None, 4.3),
('Black Jacket',  'Leather',          2, 'no',  4.9),
('White Sneakers','Sport shoes',     15, 'yes', 4.6),
('Green Hat',     'Wool',             8, None, 3.9),
('Yellow T-shirt','Casual wear',     12, 'yes', 4.1),
('Gray Socks',    'Comfort pack',     20, 'yes', 3.5),
('Brown Belt',    'Leather',          3, 'no',  4.0),
('Purple Scarf',  'Silk',             6, 'yes', 4.8),
('Orange Hoodie', 'Sport style',      7, 'yes', 4.2);
```

---

## Шаг 2 — небольшое напоминание о проекте

Структура проекта:

```
project/
  core.py            # ваш класс Database (подключение, exec_read, exec_write, REGEXP)
  seed.py            # (опционально) скрипт для заполнения таблицы products
  logic_sorting.py   # здесь будут функции-практики по ORDER/LIMIT/OFFSET и логическим операторам
  main.py            # меню; подключает функции из logic_sorting.py и вызывает их
```

В `core.py` у вас уже определён класс `Database`. Все функции ниже используют `db.exec_read(sql, params)` для получения результатов.

---

## Шаг 3 — создаём новый модуль для логики

Создайте файл `logic_sorting.py`. В начале подключите класс:

```python
# logic_sorting.py
from core import Database
```

Функции будут принимать `db: Database` (объект), параметры фильтрации и возвращать результат `db.exec_read(...)`.

---

## Шаг 4 — Задание: `WHERE + AND`

### Задание

Найти товары, которые **в наличии** (`status = 'yes'`) **и** имеют **рейтинг > 4.5** и **count > 5**.
(Реально: «показать хорошо оцениваемые товары, которые действительно в наличии и которых достаточно на складе».)

### Логика решения

Комбинируем три условия с `AND`. Параметризуем пороги (`min_rating`, `min_count`) — так функция универсальна.

### Функция (пример)

```python
def products_in_stock_and_popular(db: Database, min_rating: float = 4.5, min_count: int = 5):
    """
    Возвращает товары, где status='yes' AND rating > min_rating AND count > min_count.
    """
    sql = """
    SELECT id, title, description, count, status, rating
    FROM products
    WHERE status = ? AND rating > ? AND count > ?;
    """
    return db.exec_read(sql, ('yes', min_rating, min_count))
```

**Пояснение:** порядок условий в `AND` не меняет логику, но для читаемости ставим сначала простые сравнения. Используем плейсхолдеры `?`.

---

## Шаг 5 — Задание: `WHERE + OR`

### Задание

Выбрать товары, которые **либо** имеют **рейтинг >= 4.8**, **либо** на складе **более 15 штук**, **либо** в описании есть слово `'Leather'`.
(Реальная задача: отобрать товары, которые можно либо рекламировать (высокий рейтинг), либо продвигать массово (много на складе), либо выделить по VIP-категории по материалу.)

### Логика решения

Объединим условия через `OR`. Поскольку `OR` может сочетаться с `AND` в других запросах, всегда добавляйте скобки, если сочетаете несколько видов логики.

### Функция (пример)

```python
def products_high_rating_or_many_or_material(db: Database, rating_thr: float = 4.8, many_threshold: int = 15, material_keyword: str = "Leather"):
    """
    Возвращает товары, где rating >= rating_thr OR count > many_threshold OR description LIKE '%material_keyword%'.
    """
    sql = """
    SELECT id, title, description, count, status, rating
    FROM products
    WHERE rating >= ? OR count > ? OR (description LIKE ?);
    """
    return db.exec_read(sql, (rating_thr, many_threshold, f"%{material_keyword}%"))
```

**Пояснение:** используем `LIKE` для поиска по описанию. Скобки вокруг `description LIKE ?` делают структуру очевидной.

---

## Шаг 6 — Задание: `WHERE + NOT`

### Задание

Показать товары, которые **не** доступны — т.е. **не** (`status = 'yes'` **и** count > 0). Другими словами: товары с `status != 'yes'` или `count = 0` или `description IS NULL` (если хотим исключить товары без описания из списка доступных).

### Логика решения

Используем `NOT` над составным условием, либо явную альтернативу с `OR`. Покажем оба варианта.

### Функция (вариант A — с `NOT`)

```python
def products_not_available(db: Database):
    """
    Возвращает товары, которые НЕ (status='yes' AND count > 0).
    """
    sql = """
    SELECT id, title, description, count, status, rating
    FROM products
    WHERE NOT (status = 'yes' AND count > 0);
    """
    return db.exec_read(sql)
```

### Функция (вариант B — эквивалент с OR и явной проверкой NULL)

```python
def products_not_available_explicit(db: Database):
    sql = """
    SELECT id, title, description, count, status, rating
    FROM products
    WHERE status != 'yes' OR count = 0 OR description IS NULL;
    """
    return db.exec_read(sql)
```

**Пояснение:** `NOT (A AND B)` эквивалентно `(NOT A) OR (NOT B)` (де Моргана). Выберите вариант, который для студентов более понятен.

---

## Шаг 7 — Задание: `ORDER BY`

### Задание

Сформировать отчёт: вывести поля `title`, `rating`, `count`, отсортированные сначала по **rating DESC**, затем по **count DESC** — т.е. сначала самые "качественные", среди равных — те, которых больше на складе.

### Логика решения

`ORDER BY rating DESC, count DESC`. Если нужно — добавить `LIMIT`.

### Функция

```python
def products_ordered_by_rating_and_stock(db: Database, limit: int | None = None):
    """
    Возвращает товары, отсортированные по rating DESC, count DESC.
    Если limit указан — ограничивает результат.
    """
    base_sql = """
    SELECT id, title, rating, count
    FROM products
    ORDER BY rating DESC, count DESC
    """
    if limit:
        base_sql += " LIMIT ?"
        return db.exec_read(base_sql, (limit,))
    return db.exec_read(base_sql)
```

**Пояснение:** сортировка по нескольким полям — частый паттерн в отчётах. При равных рейтингах вторичный ключ (count) разрешает порядок.

---

## Шаг 8 — Задание: `LIMIT`

### Задание

Вывести **топ-3** товара по длине названия (самые длинные `title`) — это пример «прикладной» аналитики: показать товары с длинными именами (может пригодиться для UI-корректировок).

### Логика решения

Используем `LENGTH(title)` вычисляемое выражение, сортируем `ORDER BY LENGTH(title) DESC`, затем `LIMIT 3`.

### Функция

```python
def top_n_long_titles(db: Database, n: int = 3):
    """
    Возвращает top n товаров по длине названия (LENGTH(title) DESC).
    """
    sql = """
    SELECT id, title, LENGTH(title) AS title_len, rating, count
    FROM products
    ORDER BY title_len DESC
    LIMIT ?;
    """
    return db.exec_read(sql, (n,))
```

**Пояснение:** `LIMIT` здесь ограничивает размер результата. Без `ORDER BY` `LIMIT` давал бы любое первые N строк — поэтому сортировка обязательна для детерминированного результата.

---

## Шаг 9 — Задание: `OFFSET` (пагинация)

### Задание

Реализовать функцию «страница» — возвращать товары для заданной страницы `page` и размера страницы `page_size`, сортируя по `rating DESC, id DESC`. Например, `page=1, page_size=4` — первые 4; `page=2` — 5–8.

### Логика решения

`OFFSET = (page - 1) * page_size`, `LIMIT = page_size`, и обязательно `ORDER BY` для детерминированности.

### Функция (пагинация)

```python
def products_page(db: Database, page: int = 1, page_size: int = 4):
    """
    Возвращает конкретную страницу товаров, отсортированных по rating DESC, id DESC.
    page — 1-based.
    """
    if page < 1:
        page = 1
    offset = (page - 1) * page_size
    sql = """
    SELECT id, title, rating, count
    FROM products
    ORDER BY rating DESC, id DESC
    LIMIT ? OFFSET ?;
    """
    return db.exec_read(sql, (page_size, offset))
```

**Пояснение:** такой подход — простая пагинация. Для больших БД обсудите keyset pagination как альтернативу (описали в теории).

---

## Дополнительно — несколько реалистичных комбинированных запросов (отчёты)

### A. «Отчёт: уникальные статусы для товаров с rating > 4.0»

```python
def distinct_status_for_high_rating(db: Database, threshold: float = 4.0):
    sql = "SELECT DISTINCT status FROM products WHERE rating > ? ORDER BY status;"
    return db.exec_read(sql, (threshold,))
```

### B. «Маркировка горячих товаров»: `title`, `description`, литерал `'HOT'` для rating > 4.5

```python
def hot_products_tagged(db: Database, threshold: float = 4.5):
    sql = "SELECT title, description, 'HOT' AS tag FROM products WHERE rating > ? ORDER BY rating DESC;"
    return db.exec_read(sql, (threshold,))
```

### C. «Поиск + сортировка + лимит» — найти товары с `LIKE '%Sport%'`, отсортировать по `rating DESC` и взять первые 5

```python
def sport_products_top5(db: Database):
    sql = """
    SELECT id, title, description, rating
    FROM products
    WHERE description LIKE ?
    ORDER BY rating DESC
    LIMIT 5;
    """
    return db.exec_read(sql, ("%Sport%",))
```

**Пояснение:** такие комбинированные запросы ближе к реальным отчётам.

---

## Шаг 10 — интеграция в `main.py`

В `main.py` создайте экземпляр `db = Database()` и подключите меню, где номера маппируются на функции из `logic_sorting.py`. Пример формата маппинга (коротко):

```python
menu = {
    "1": ("in_stock_and_popular", lambda: logic.products_in_stock_and_popular(db)),
    "2": ("high_or_many_or_material", lambda: logic.products_high_rating_or_many_or_material(db)),
    "3": ("not_available", lambda: logic.products_not_available(db)),
    "4": ("ordered_by_rating_stock", lambda: logic.products_ordered_by_rating_and_stock(db, limit=10)),
    "5": ("top_long_titles", lambda: logic.top_n_long_titles(db, 3)),
    "6": ("page", lambda: logic.products_page(db, page=2, page_size=4)),
    # ...
}
```

После вызова функции печатайте результат удобно, например:

```python
rows = action()
if rows:
    for r in rows:
        print(dict(r))   # sqlite3.Row -> dict for readable output
else:
    print("Ничего не найдено.")
input("Нажмите Enter чтобы продолжить...")
```

---

# Вопросы

1. В чём разница между `AND` и `OR` в SQL?
2. Как работает оператор `NOT`? Приведите пример.
3. Для чего нужен `ORDER BY` и какие у него бывают направления сортировки?
4. Как отсортировать товары сначала по статусу, а затем по рейтингу?
5. Для чего нужны `LIMIT` и `OFFSET`?
6. Приведите пример запроса: вывести 5 самых популярных товаров (по рейтингу).
7. Как получить «вторую страницу» товаров по 3 записи на страницу?
8. Чем отличается `NULL` от нуля или пустой строки?
9. Как с помощью `LIKE` найти товары, у которых описание начинается на слово «Red»?
10. Зачем может пригодиться `DISTINCT` вместе с `WHERE` или `ORDER BY`?

---

# Домашнее задание

## Задание 1 — Базовый проект

Цель: собрать минимальную рабочую структуру и реализовать простые запросы для тренировки фильтрации и сортировки.

### Файлы, которые нужно создать

- `core.py` — класс `Database` (упрощённый).
- `seed.py` — скрипт для создания таблицы `products` и вставки `SAMPLE_PRODUCTS`.
- `logic.py` — функции-запросы (по пунктам ниже).
- `main.py` — простое меню, которое вызывает функции из `logic.py` по номеру (маппинг).

### Шаг 1. Реализовать класс `Database` (файл `core.py`)

**Требования к классу:**

- Инициализация: подключение к SQLite, хранение `self.conn`.
- Метод `exec_write(sql, params=None)` — выполнять изменения и `commit()`; поддерживает `executemany` если `params` — список кортежей.
- Метод `exec_read(sql, params=())` — выполнять `SELECT` и возвращать `fetchall()`.
- Метод `create_products_table()` — создаёт таблицу `products`.

### Шаг 2. Создать скрипт заполнения `seed.py`

**Задача:** создать таблицу и вставить `SAMPLE_PRODUCTS` (Список продуктов для заполнения).

**План:**

1. Импортировать `Database` и `SAMPLE_PRODUCTS`.
2. Создать объект `db = Database()`.
3. Вызвать `db.create_products_table()`.
4. Вставить данные (только если таблица пустая — можно предварительно сделать `SELECT COUNT(*)` и вставить данные только при `0`).

### Шаг 3. Логика запросов (`logic.py`) — простые задания

В `logic.py` реализовать функции, каждая возвращает `list` строк через `db.exec_read`.

1. **Показать все продукты**
2. **Товары в наличии (status = 'yes')**
3. **Товары с рейтингом > 4.5**
4. **Товары с count = 0 (нет на складе)**
5. **Товары с рейтингом BETWEEN 4.0 AND 4.8**
6. **Товары со статусом IN ('yes','no')**
7. **Поиск по описанию: LIKE '%Sport%'**
8. **Сортировка: top 5 по рейтингу**
9. **Уникальные статусы (DISTINCT)**
10. **Длина title (LENGTH) — показать title и его длину, отсортировать по длине**

### Шаг 4. `main.py` — простое меню

- Создайте `db = Database()` и импортируйте функции из `logic.py`.
- Сделайте словарь маппинга `"номер" -> (описание, функция_обёртка)`.
- В цикле выводите меню, получайте выбор, вызывайте `action()` (если нужно — запрашивайте дополнительные параметры) и печатайте результат.
- В конце каждой команды делайте `input("Нажмите Enter для продолжения...")`.

**Совет:** используйте `lambda` или `functools.partial`, чтобы откладывать вызов функций с аргументами.

## Задание 2 — Продвинутая практика

Цель: практиковать составные условия (AND/OR/NOT), скобки для приоритета, смешанные операторы (BETWEEN/IN/LIKE/IS NULL/IS NOT NULL), сортировку и пагинацию в рамках реальных сценариев.

### Общие подготовительные шаги (перед началом)

1. Убедитесь, что вы выполнили Задание 1 и `products` заполнена.
2. Используйте тот же `core.Database` и `db.exec_read` / `db.exec_write`.
3. Создайте файл `logic_complex.py`

### Логика запросов (`logic_complex.py`) - составные задания

1. Фильтр для «маркетинг-акций» — показывать товары, которые можно смело рекламировать и отгрузить сразу. Выбрать товары, где `status='yes'`, `rating >= 4.5` и `count >= 5`.
2. Альтернатива выбора по рейтингу или количеству, и последующая проверка на наличие такого товара. Выбрать товары, которые у которых rating > 4.8 или count >= 15, и проверить их статус `status='yes'` (Скобки в запросе увеличивают приоритет).
3. Товары с рейтингом между 4.0 и 4.8 и статусом "в наличии" (`yes`).
4. Выбрать товары, где статус в наборе `('yes','no')` и количество больше `0`, сортируя запрос по рейтингу по убыванию.
5. Найти товары, в описании которых есть слово `'Sport'` (регистр учитывать), и `rating > 4.0` — показать топ 3 по рейтингу.
6. Показать товары, у которых пустое описание (NULL) или описание начиналось с шаблона `'%Leather%'`, отсортировать данные по убыванию количества `ASC` (чтобы сначала мелкие партии).

---

[Предыдущий урок](lesson05.md) | [Следующий урок](lesson07.md)