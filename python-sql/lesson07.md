# Модуль 1 · Урок 7. Группировка и агрегаты.

## **Цель урока:**

- Разобрать групповые и агрегатные функции.
- Научится группировать данные.
- Познакомится с некоторыми «ловушками» при использовании HAVING.

# 1) Теория

## 1. Зачем нужны агрегаты и группировка (кратко)

**Агрегаты** позволяют **сводить множество строк к одному значению**: посчитать сумму, среднее, максимум и т.д.
**Группировка** (`GROUP BY`) нужна, когда нужно вычислить агрегаты не по всей таблице целиком, а разбить строки на группы по какому-то признаку и получить агрегат по каждой группе.

**Реальные задачи:**

- Подсчитать, сколько товаров каждого статуса — сколько строк с `status = 'yes'`, сколько — `status = 'no'`.
- Посчитать средний рейтинг товаров **в наличии** (для оценки качества ассортимента).
- Вывести минимальную и максимальную цену в каждой категории, чтобы понять ценовой диапазон по категориям.

Эти примеры соответствуют: «группировка по полю → агрегат по группе».

---

## 2. `GROUP BY`

### Что такое группировка

`GROUP BY` объединяет строки с одинаковыми значениями в указанных столбцах в одну группу. После этого можно применять агрегатные функции к каждой группе — например, `COUNT`, `AVG`, `SUM` и т.д.

### Главное правило (стандарт SQL)

В `SELECT` разрешено:

- агрегатные выражения (например, `COUNT(*)`, `SUM(price)`, `AVG(rating)`), и
- те столбцы/выражения, которые **включены в `GROUP BY`**.

Иначе — поведение не определено (в стандарте SQL это ошибка). На практике некоторые СУБД позволяют включать в `SELECT` столбцы не в `GROUP BY` — результат при этом может быть неопределён (SQLite допускает, но результат произволен). **Рекомендация:** всегда указывайте в `GROUP BY` все неагрегированные поля, которые вы хотите видеть в `SELECT`.

### Базовые примеры

- **Подсчитать количество товаров по статусам**:

```sql
SELECT status, COUNT(*) AS cnt
FROM products
GROUP BY status;
```

- **Средний рейтинг по каждой категории**:

```sql
SELECT category, AVG(rating) AS avg_rating
FROM products
GROUP BY category;
```

- **Количество товаров в каждой категории и суммарный запас (count суммируем)**:

```sql
SELECT category, COUNT(*) AS product_count, SUM(count) AS total_stock
FROM products
GROUP BY category;
```

### Группировка по нескольким колонкам

Иногда нужно более детально разбить группы:

```sql
SELECT category, status, COUNT(*) AS cnt
FROM products
GROUP BY category, status;
```

Здесь группы — пары (category, status).

### Группировка по выражению (computed group)

Можно группировать по выражению, не только по столбцу:

```sql
-- Группировка по первому символу названия
SELECT SUBSTR(title, 1, 1) AS first_char, COUNT(*) AS cnt
FROM products
GROUP BY first_char;
```

---

## 3. Агрегатные функции: `COUNT`, `SUM`, `AVG`, `MIN`, `MAX`

### Общие свойства агрегатов

- **Игнорируют `NULL`** (за исключением `COUNT(*)` — он считает строки, даже если некоторые поля NULL).
- Возвращают `NULL`, если в группе нет ненулевых значений для соответствующего столбца (например, `AVG` над пустой группой даст `NULL`).
- Многие агрегаты поддерживают `DISTINCT`, например `COUNT(DISTINCT column)` — считает количество различных значений.

### `COUNT`

- `COUNT(*)` — количество строк в группе (включая те, где все поля NULL).
- `COUNT(column)` — количество ненулевых значений в колонке в группе.
- `COUNT(DISTINCT column)` — количество уникальных ненулевых значений.

**Примеры:**

```sql
-- Количество строк в каждой категории:
SELECT category, COUNT(*) FROM products GROUP BY category;

-- Сколько разных описаний (не NULL) в каждой категории:
SELECT category, COUNT(DISTINCT description) FROM products GROUP BY category;
```

### `SUM`

Сумма значений числового столбца (NULL игнорируются).

```sql
-- Суммарный запас по категориям:
SELECT category, SUM(count) AS total_stock FROM products GROUP BY category;
```

### `AVG`

Среднее арифметическое по числовому столбцу (NULL игнорируются).

```sql
-- Средний рейтинг по категориям:
SELECT category, AVG(rating) AS avg_rating FROM products GROUP BY category;
```

### `MIN` / `MAX`

Минимум и максимум. Работают и для чисел, и для строк (строки — лексикографически).

```sql
-- Минимальная и максимальная цена по категориям:
SELECT category, MIN(price) AS min_price, MAX(price) AS max_price
FROM products
GROUP BY category;
```

### Особые случаи и советы

- `SUM` по столбцу, где все значения `NULL`, вернёт `NULL`.
- `AVG` возвращает `NULL`, если нет ненулевых значений.
- `MIN`/`MAX` для текстовых полей возвращают лексикографически минимальное/максимальное значение.
- Часто полезно комбинировать `COUNT` и `SUM` для метрик: `COUNT(*)` (сколько записей) и `SUM(count)` (сколько единиц на складе).

---

## 4. `HAVING`

### Для чего нужен `HAVING`

- `WHERE` фильтрует **строки** **до** группировки (отбирает какие строки попадут в группы).
- `HAVING` фильтрует **группы** **после** группировки — это единственный способ отфильтровать группы по агрегатам (например, оставить только группы, где `COUNT(*) > 3` или `AVG(rating) >= 4.5`).

### Примеры использования HAVING

- **Оставить только категории, где более 2 товаров**:

```sql
SELECT category, COUNT(*) AS cnt
FROM products
GROUP BY category
HAVING COUNT(*) > 2;
```

- **Категории со средней ценой >= 50**:

```sql
SELECT category, AVG(price) AS avg_price
FROM products
GROUP BY category
HAVING AVG(price) >= 50.0;
```

### Почему `HAVING` нужен (когда `WHERE` не подойдёт)

`WHERE` не может использовать агрегатные функции, потому что агрегирование ещё не произошло до `WHERE`. Например, **нельзя** написать\*\*:\*\*

```sql
-- ❌ НЕРАБОЧИЙ запрос (нельзя использовать AVG в WHERE)
SELECT category, AVG(rating) FROM products
WHERE AVG(rating) > 4.5  -- недопустимо
GROUP BY category;
```

Правильный вариант — `HAVING`:

```sql
SELECT category, AVG(rating) FROM products
GROUP BY category
HAVING AVG(rating) > 4.5;
```

### Пример «пустая выборка» из-за WHERE vs HAVING

Иногда можно ожидать некий результат, но из-за неправильного места фильтра получить пустой результат:

- Если вы сначала примените `WHERE`, то строки, вырезанные `WHERE`, **не попадут в группы**, и затем `HAVING` не сможет «вернуть» их. Например:

```sql
-- предположим, что мы сначала отфильтруем все товары с price < 100,
-- после группировки может не остаться групп, удовлетворяющих HAVING
SELECT category, AVG(price)
FROM products
WHERE price < 100    -- отрезали возможные дорогие записи
GROUP BY category
HAVING AVG(price) > 150;  -- ожидание «категории со средней ценой > 150» — но где взять данные,
                          -- если мы в WHERE вырезали все цены >= 100?
```

В этом примере `WHERE` удалит дорогие товары и затем `HAVING AVG(price) > 150` даст пустой результат, потому что в группах уже нет дорогих значений. **Итого:** порядок обработки имеет значение.

### Смешанный пример: WHERE + GROUP BY + HAVING

Часто полезно сначала сузить строки `WHERE`, а затем уже отфильтровать группы `HAVING`:

```sql
SELECT category, COUNT(*) AS cnt, AVG(rating) AS avg_rating
FROM products
WHERE status = 'yes'         -- только товары в наличии
GROUP BY category
HAVING AVG(rating) >= 4.5    -- только категории с хорошим средним рейтингом
ORDER BY avg_rating DESC;
```

---

## 5. Логический порядок выполнения (важно для понимания WHERE vs HAVING)

Логический порядок обработки основных частей запроса примерно такой (упрощённо):

1. `FROM` (и JOIN) — формирование начального множества строк.
2. `WHERE` — фильтрация строк (до группировки).
3. `GROUP BY` — объединение строк в группы.
4. `HAVING` — фильтрация групп (по агрегатам или выражениям над группой).
5. `SELECT` — вычисление итоговых выражений/агрегатов/алиасов.
6. `ORDER BY` — сортировка результирующих строк.
7. `LIMIT` — ограничение числа возвращаемых строк.

Это объясняет, почему `WHERE` не видит агрегаты, а `HAVING` — видит.

---

## 6. Полезные примеры (сырые запросы)

Ниже — коллекция запросов, которые хорошо показывают разные сценарии:

- **Общее количество товаров**:

```sql
SELECT COUNT(*) AS total_products FROM products;
```

- **Суммарный запас (сколько единиц всего на складе)**:

```sql
SELECT SUM(count) AS total_stock FROM products;
```

- **Средний рейтинг по всем товарам**:

```sql
SELECT AVG(rating) AS avg_rating FROM products;
```

- **Минимальная и максимальная цена в таблице**:

```sql
SELECT MIN(price) AS min_price, MAX(price) AS max_price FROM products;
```

- **Количество товаров по категориям**:

```sql
SELECT category, COUNT(*) AS cnt
FROM products
GROUP BY category;
```

- **Сколько единиц на складе в каждой категории**:

```sql
SELECT category, SUM(count) AS total_stock
FROM products
GROUP BY category;
```

- **Средний рейтинг и количество товаров в каждой категории, но только для категорий с >= 3 товаров**:

```sql
SELECT category, COUNT(*) AS cnt, AVG(rating) AS avg_rating
FROM products
GROUP BY category
HAVING COUNT(*) >= 3;
```

- **Категории, где средняя цена > 50**:

```sql
SELECT category, AVG(price) AS avg_price
FROM products
GROUP BY category
HAVING AVG(price) > 50;
```

- **Уникальные комбинации `category + status` и количество в каждой**:

```sql
SELECT category, status, COUNT(*) AS cnt
FROM products
GROUP BY category, status
ORDER BY category, status;
```

### Примеры из «будущего»

- **Группировка по «корзинам» рейтинга (белтеты) — пример GROUP BY с CASE**:

```sql
SELECT
  CASE
    WHEN rating >= 4.5 THEN 'high'
    WHEN rating >= 3.5 THEN 'medium'
    ELSE 'low'
  END AS rating_bucket,
  COUNT(*) AS cnt,
  AVG(price) AS avg_price
FROM products
GROUP BY rating_bucket;
```

- **Группировка по первому символу названия (пример с выражением)**:

```sql
SELECT SUBSTR(title,1,1) AS first_letter, COUNT(*) AS cnt
FROM products
GROUP BY first_letter
ORDER BY first_letter;
```

- **DISTINCT внутри агрегата**:

```sql
-- Сколько разных описаний в каждой категории
SELECT category, COUNT(DISTINCT description) AS distinct_descriptions
FROM products
GROUP BY category;
```

---

## 7. Частые ошибки и рекомендации (best practices)

1. **Не пытайтесь использовать агрегаты в `WHERE`.** Для условий по агрегатам используйте `HAVING`.
2. **Старайтесь фильтровать как можно раньше (`WHERE`),** чтобы уменьшить объём данных для группировки — это обычно быстрее.
3. **Чётко указывайте поля в `GROUP BY`.** Стандарт SQL требует, чтобы все неагрегированные поля в `SELECT` были в `GROUP BY`. Некоторые СУБД позволяют не делать этого — но результат может быть непредсказуем.
4. **Понимайте поведение `NULL`:** агрегаты игнорируют `NULL` (кроме `COUNT(*)`). Планируйте обработку `NULL`, если это важно.
5. **Для «топ-N по группе» используйте оконные функции (если доступны)** — это следующий уровень. Но в простых случаях можно сделать подзапрос + `ROW_NUMBER()` или комбинацию `JOIN`. (Окна — за пределами текущего урока.)
6. **Используйте `COUNT(DISTINCT ...)` аккуратно:** для больших наборов DISTINCT может быть дорогим по ресурсам.
7. **Порядок операций важен:** если результат пуст — проверьте сначала `WHERE` (не убиваете ли вы строки до группировки), потом `HAVING` (невыполнение агрегатного условия).

---

# 2) Практика

## Расширим таблицу `products`

```sql
DROP TABLE IF EXISTS products;

CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT,
    price REAL,
    quantity INTEGER,
    supplier TEXT,
    rating REAL,
    created_at TEXT
);
```

### Новые столбцы:

- `supplier` — поставщик (строка).
- `rating` — рейтинг товара (от 1.0 до 5.0, может быть `NULL`).
- `created_at` — дата добавления товара (строка в формате `YYYY-MM-DD`).

---

## Добавим тестовые данные

```sql
INSERT INTO products (name, category, price, quantity, supplier, rating, created_at) VALUES
('iPhone 14', 'Electronics', 1200, 10, 'Apple', 4.8, '2023-05-10'),
('MacBook Air', 'Electronics', 1500, 5, 'Apple', 4.7, '2023-06-12'),
('Galaxy S22', 'Electronics', 1100, 7, 'Samsung', 4.5, '2023-07-01'),
('Galaxy Tab S8', 'Electronics', 900, 12, 'Samsung', 4.2, '2023-07-15'),
('ThinkPad X1', 'Electronics', 1700, 3, 'Lenovo', 4.6, '2023-08-01'),
('Yoga Slim 7', 'Electronics', 1300, 8, 'Lenovo', 4.3, '2023-08-10'),
('Office Chair', 'Furniture', 200, 20, 'Ikea', 4.1, '2023-06-20'),
('Dining Table', 'Furniture', 600, 2, 'Ikea', 4.4, '2023-07-02'),
('Lamp', 'Furniture', 50, 15, 'Ikea', NULL, '2023-07-05'),
('Desk', 'Furniture', 400, 7, 'Ikea', 3.9, '2023-07-22'),
('T-shirt', 'Clothes', 25, 50, 'Zara', 4.0, '2023-06-01'),
('Jeans', 'Clothes', 60, 30, 'Zara', 3.8, '2023-06-15'),
('Jacket', 'Clothes', 120, 10, 'Zara', 4.5, '2023-07-01'),
('Sneakers', 'Clothes', 90, 25, 'Nike', 4.6, '2023-06-25'),
('Cap', 'Clothes', 20, 40, 'Nike', NULL, '2023-07-05'),
('Monitor', 'Electronics', 300, 15, 'Samsung', 4.2, '2023-07-28'),
('Mouse', 'Electronics', 40, 30, 'Logitech', 4.0, '2023-08-05'),
('Keyboard', 'Electronics', 70, 25, 'Logitech', 4.1, '2023-08-06'),
('Smartwatch', 'Electronics', 400, 12, 'Apple', 4.4, '2023-08-08'),
('Headphones', 'Electronics', 250, 18, 'Sony', 4.5, '2023-07-18');
```

---

## 3. Задания

### Базовые задания

**Задание 1.**
Выведите количество товаров в каждой категории (`GROUP BY category`).

**Ожидание:**
3 строки: Electronics, Furniture, Clothes.

---

**Задание 2.**
Посчитайте среднюю цену товаров для каждого поставщика (`AVG(price)`).

**Ожидание:**
Apple, Samsung, Lenovo, Ikea, Zara, Nike, Logitech, Sony.

---

**Задание 3.**
Найдите максимальный рейтинг товара в каждой категории (`MAX(rating)`).

---

**Задание 4.**
Посчитайте общее количество товаров (`SUM(quantity)`) у каждого поставщика.

---

### Средний уровень

**Задание 5.**
Выведите только те категории, где количество товаров больше 4 (`HAVING COUNT(*) > 4`).

---

**Задание 6.**
Найдите поставщиков, у которых средняя цена товара выше 500 (`HAVING AVG(price) > 500`).

---

**Задание 7.**
Для каждой категории выведите минимальную и максимальную цену товара.

---

### Сложные задания

**Задание 8.**
Найдите категории, где суммарное количество товаров превышает 100.

---

**Задание 9.**
Выведите поставщиков, у которых средний рейтинг товаров выше 4.3, но количество товаров не меньше 3.

---

**Задание 10.**
Найдите топ-3 категории по средней цене товара (сортировка `ORDER BY AVG(price) DESC LIMIT 3`).

---

**Задание 11.**
Определите, сколько товаров было добавлено в каждом месяце (`strftime('%m', created_at)`).

---

**Задание 12.**
Выведите поставщика с самым дорогим товаром в каждой категории.

---

## 4. Решения заданий в функциях

```python
def task_1_count_by_category(db: Database):
    """
    Задание 1.
    Выведите количество товаров в каждой категории.
    """
    sql = """
    SELECT category, COUNT(*) AS product_count
    FROM products
    GROUP BY category;
    """
    rows = db.exec_read(sql)
    for row in rows:
        print(dict(row))
    return rows
```

---

```python
def task_2_avg_price_by_supplier(db: Database):
    """
    Задание 2.
    Посчитайте среднюю цену товаров для каждого поставщика.
    """
    sql = """
    SELECT supplier, AVG(price) AS avg_price
    FROM products
    GROUP BY supplier;
    """
    rows = db.exec_read(sql)
    for row in rows:
        print(dict(row))
    return rows
```

---

```python
def task_3_max_rating_by_category(db: Database):
    """
    Задание 3.
    Найдите максимальный рейтинг товара в каждой категории.
    """
    sql = """
    SELECT category, MAX(rating) AS max_rating
    FROM products
    GROUP BY category;
    """
    rows = db.exec_read(sql)
    for row in rows:
        print(dict(row))
    return rows
```

---

```python
def task_4_total_quantity_by_supplier(db: Database):
    """
    Задание 4.
    Посчитайте общее количество товаров у каждого поставщика.
    """
    sql = """
    SELECT supplier, SUM(quantity) AS total_quantity
    FROM products
    GROUP BY supplier;
    """
    rows = db.exec_read(sql)
    for row in rows:
        print(dict(row))
    return rows
```

---

```python
def task_5_categories_more_than_4_products(db: Database):
    """
    Задание 5.
    Выведите только те категории, где количество товаров больше 4.
    """
    sql = """
    SELECT category, COUNT(*) AS product_count
    FROM products
    GROUP BY category
    HAVING COUNT(*) > 4;
    """
    rows = db.exec_read(sql)
    for row in rows:
        print(dict(row))
    return rows
```

---

```python
def task_6_suppliers_avg_price_gt_500(db: Database):
    """
    Задание 6.
    Найдите поставщиков, у которых средняя цена товара выше 500.
    """
    sql = """
    SELECT supplier, AVG(price) AS avg_price
    FROM products
    GROUP BY supplier
    HAVING AVG(price) > 500;
    """
    rows = db.exec_read(sql)
    for row in rows:
        print(dict(row))
    return rows
```

---

```python
def task_7_min_max_price_by_category(db: Database):
    """
    Задание 7.
    Для каждой категории выведите минимальную и максимальную цену товара.
    """
    sql = """
    SELECT category, MIN(price) AS min_price, MAX(price) AS max_price
    FROM products
    GROUP BY category;
    """
    rows = db.exec_read(sql)
    for row in rows:
        print(dict(row))
    return rows
```

---

```python
def task_8_categories_total_quantity_gt_100(db: Database):
    """
    Задание 8.
    Найдите категории, где суммарное количество товаров превышает 100.
    """
    sql = """
    SELECT category, SUM(quantity) AS total_quantity
    FROM products
    GROUP BY category
    HAVING SUM(quantity) > 100;
    """
    rows = db.exec_read(sql)
    for row in rows:
        print(dict(row))
    return rows
```

---

```python
def task_9_suppliers_high_rating(db: Database):
    """
    Задание 9.
    Выведите поставщиков, у которых средний рейтинг выше 4.3,
    но количество товаров не меньше 3.
    """
    sql = """
    SELECT supplier, AVG(rating) AS avg_rating, COUNT(*) AS product_count
    FROM products
    GROUP BY supplier
    HAVING AVG(rating) > 4.3 AND COUNT(*) >= 3;
    """
    rows = db.exec_read(sql)
    for row in rows:
        print(dict(row))
    return rows
```

---

```python
def task_10_top3_categories_by_avg_price(db: Database):
    """
    Задание 10.
    Найдите топ-3 категории по средней цене товара.
    """
    sql = """
    SELECT category, AVG(price) AS avg_price
    FROM products
    GROUP BY category
    ORDER BY avg_price DESC
    LIMIT 3;
    """
    rows = db.exec_read(sql)
    for row in rows:
        print(dict(row))
    return rows
```

---

```python
def task_11_products_by_month(db: Database):
    """
    Задание 11.
    Определите, сколько товаров было добавлено в каждом месяце.
    """
    sql = """
    SELECT strftime('%Y-%m', created_at) AS month, COUNT(*) AS product_count
    FROM products
    GROUP BY month
    ORDER BY month;
    """
    rows = db.exec_read(sql)
    for row in rows:
        print(dict(row))
    return rows
```

---

```python
def task_12_most_expensive_supplier_per_category(db: Database):
    """
    Задание 12.
    Выведите поставщика с самым дорогим товаром в каждой категории.
    """
    sql = """
    SELECT p.category, p.supplier, MAX(p.price) AS max_price
    FROM products p
    GROUP BY p.category;
    """
    rows = db.exec_read(sql)
    for row in rows:
        print(dict(row))
    return rows
```

---

# Вопросы

1. Что делает оператор `GROUP BY`?
2. В чём разница между `WHERE` и `HAVING`?
3. Можно ли использовать в `SELECT` столбцы, которые не входят в `GROUP BY` и не являются агрегатными функциями?
4. Что возвращает `COUNT(*)`?
5. В чём разница между `AVG(price)` и `SUM(price) / COUNT(price)`?
6. Как найти максимальную цену среди всех товаров и минимальную цену в той же таблице?
7. Можно ли использовать агрегатные функции в `WHERE`?
8. Как посчитать средний рейтинг товаров для каждого поставщика?
9. Для чего может использоваться комбинация `GROUP BY` + `ORDER BY`?

---

# Домашнее задание

## 1. Подготовка

1. Убедитесь, что у вас есть таблица `products` с расширенными полями:

   ```sql
   CREATE TABLE IF NOT EXISTS products (
       id INTEGER PRIMARY KEY AUTOINCREMENT,
       title TEXT,
       description TEXT,
       category TEXT,
       supplier TEXT,
       price REAL,
       quantity INTEGER,
       status TEXT,
       rating REAL,
       created_at TEXT
   );
   ```

2. Данные можно заполнить любыми тестовыми значениями (10–15 записей). Важно, чтобы:

   - были повторяющиеся категории,
   - у некоторых товаров `description` или `rating` были `NULL`,
   - цены и количество были разные.

---

## 2. Задания

### Задание 1. Количество товаров по статусу

Выведите, сколько товаров находится в каждом статусе (`status`).
_Подсказка: используйте `GROUP BY status` и `COUNT(_)`.\*

---

### Задание 2. Средняя цена товаров по категориям

Найдите среднюю цену товаров в каждой категории.
_Подсказка: `AVG(price)`._

---

### Задание 3. Категории с дорогими товарами

Выведите категории, где минимальная цена товара больше 200.
_Подсказка: `MIN(price)` + `HAVING`._

---

### Задание 4. Поставщики и количество уникальных категорий

Для каждого поставщика (`supplier`) посчитайте, сколько разных категорий товаров он поставляет.
_Подсказка: используйте `COUNT(DISTINCT category)`._

---

### Задание 5. Категории с товарами без описания

Найдите категории, где есть хотя бы один товар с пустым описанием (`description IS NULL`).
_Подсказка: сначала `WHERE description IS NULL`, потом `GROUP BY category`._

---

### Задание 6. Поставщики и общая сумма товаров

Выведите поставщиков и общее количество их товаров (`SUM(quantity)`).
Отсортируйте результат по сумме от большего к меньшему.

---

### Задание 7. Рейтинг товаров по статусу

Для каждого статуса (`status`) выведите средний рейтинг товаров.
_Подсказка: `AVG(rating)`._

---

### Задание 8. Поставщики с дорогими товарами

Найдите поставщиков, у которых средняя цена товаров превышает 400.
_Подсказка: `HAVING AVG(price) > 400`._

---

### Задание 9. Категории с высоким средним рейтингом

Найдите категории, где средний рейтинг товаров выше 4.2, и при этом товаров не меньше 2.
_Подсказка: `HAVING AVG(rating) > 4.2 AND COUNT(_) >= 2`.\*

---

### Задание 10. Топ-3 поставщиков по общему количеству товаров

Выведите 3 поставщиков с наибольшим количеством товаров.
_Подсказка: `ORDER BY SUM(quantity) DESC LIMIT 3`._

---

### Задание 11. Количество товаров по месяцам

Определите, сколько товаров было добавлено в каждом месяце (`created_at`).
_Подсказка: используйте `strftime('%m', created_at)` и `GROUP BY`._

---

### Задание 12. Самый дорогой товар у каждого поставщика

Для каждого поставщика найдите название (`title`) и цену (`price`) его самого дорогого товара.
_Подсказка: `MAX(price)` + подзапрос или `JOIN`._

---

[Предыдущий урок](lesson06.md) | [Следующий урок](lesson08.md)
