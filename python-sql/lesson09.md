# Модуль 2. Урок 9. Подзапросы и CTE. Объединение и логика в SQL

# 1) Подзапросы

## 1. Вводная часть — цель и мотив

Когда мы работаем с простой базой данных, нам обычно хватает прямых запросов с `SELECT`, `JOIN`, `WHERE`. Но по мере усложнения задач возникает потребность «вложить» один запрос внутрь другого.

Пример:

> Нужно вывести всех студентов, у которых **средний балл выше среднего по группе**.

В таком случае мы сначала должны посчитать средний балл по всей группе, а потом использовать это значение в условии. Согласись, неудобно делать это двумя отдельными запросами — хочется вложить один запрос внутрь другого.

Вот здесь и приходят на помощь **подзапросы (subqueries)** и **обобщённые табличные выражения (CTE)**. Они позволяют:

- делать запросы более читаемыми,
- разбивать сложные задачи на шаги,
- уменьшать дублирование кода,
- в некоторых случаях — оптимизировать работу базы.

---

## 2. Подзапросы — теория + примеры

### 2.1 Подзапросы в SELECT (скалярные)

Скалярный подзапрос возвращает одно значение. Его можно использовать как «виртуальное поле».

Пример:

```sql
SELECT
    name,
    (SELECT AVG(grade) FROM grades WHERE student_id = s.id) AS avg_grade
FROM students s;
```

Здесь для каждого студента в отдельном столбце показываем его средний балл.

> Важно: если подзапрос возвращает больше одной строки, будет ошибка. Поэтому такие подзапросы всегда должны гарантированно возвращать одно значение.

---

### 2.2 Подзапросы в WHERE

Используются для фильтрации данных на основе результата другого запроса.

**Однострочный подзапрос**:

```sql
SELECT name
FROM students
WHERE id = (SELECT student_id FROM grades ORDER BY grade DESC LIMIT 1);
```

→ Найти студента с максимальной оценкой.

**Многострочный подзапрос** (с `IN`):

```sql
SELECT name
FROM students
WHERE id IN (SELECT student_id FROM grades WHERE grade = 5);
```

→ Найти всех студентов, у которых есть «пятёрки».

---

### 2.3 Подзапросы в FROM (derived tables)

Мы можем временно рассматривать подзапрос как таблицу и использовать её в `FROM`.

Пример:

```sql
SELECT sub.subject_id, AVG(sub.grade) AS avg_grade
FROM (
    SELECT subject_id, grade FROM grades
) AS sub
GROUP BY sub.subject_id;
```

Это удобно, когда нужно сначала подготовить набор данных, а потом применять к нему агрегаты или фильтрацию.

---

### 2.4 Коррелированные подзапросы

Особый вид подзапросов, которые зависят от внешнего запроса.
Они выполняются **для каждой строки внешнего результата**. Это может быть медленно, но иногда без них не обойтись.

Пример:

```sql
SELECT s.name
FROM students s
WHERE 5 = (
    SELECT MAX(g.grade)
    FROM grades g
    WHERE g.student_id = s.id
);
```

→ Выбрать студентов, у которых максимальная оценка равна 5.
Здесь внутренний запрос зависит от `s.id`, то есть выполняется заново для каждого студента.

⚠️ Важно: коррелированные подзапросы часто менее производительны, чем `JOIN`, поэтому в реальной практике их стараются заменять.

---

## 3. Практика по подзапросам

Ниже 10 упражнений для закрепления.

---

### **Задание 1**

Вывести имя каждого студента и его средний балл.
_(подзапрос в SELECT)_

**Решение:**

```sql
SELECT
    s.name,
    (SELECT AVG(g.grade) FROM grades g WHERE g.student_id = s.id) AS avg_grade
FROM students s;
```

---

### **Задание 2**

Найти всех студентов, у которых есть хотя бы одна пятёрка.
_(подзапрос в WHERE, многострочный)_

**Решение:**

```sql
SELECT name
FROM students
WHERE id IN (SELECT student_id FROM grades WHERE grade = 5);
```

---

### **Задание 3**

Вывести студента с самой высокой оценкой в базе.
_(подзапрос в WHERE, однострочный)_

**Решение:**

```sql
SELECT name
FROM students
WHERE id = (SELECT student_id FROM grades ORDER BY grade DESC LIMIT 1);
```

---

### **Задание 4**

Показать список предметов и количество оценок по каждому.
Сначала вынести оценки в подзапрос, потом сгруппировать.
_(подзапрос в FROM)_

**Решение:**

```sql
SELECT sub.subject_id, COUNT(*) AS grade_count
FROM (
    SELECT subject_id FROM grades
) AS sub
GROUP BY sub.subject_id;
```

---

### **Задание 5**

Найти студентов, у которых средний балл выше среднего по всей группе.
_(коррелированный подзапрос)_

**Решение:**

```sql
SELECT s.name
FROM students s
WHERE (SELECT AVG(g.grade) FROM grades g WHERE g.student_id = s.id)
      > (SELECT AVG(grade) FROM grades);
```

---

### **Задание 6**

Вывести название предметов, у которых средний балл равен 5.
_(подзапрос в FROM + GROUP BY)_

**Решение:**

```sql
SELECT subj.title
FROM subjects subj
WHERE subj.id IN (
    SELECT subject_id
    FROM grades
    GROUP BY subject_id
    HAVING AVG(grade) = 5
);
```

---

### **Задание 7**

Найти студентов, которые сдавали больше предметов, чем среднее количество по группе.
_(подзапрос в WHERE + агрегаты)_

**Решение:**

```sql
SELECT s.name
FROM students s
WHERE (
    SELECT COUNT(DISTINCT subject_id)
    FROM grades g
    WHERE g.student_id = s.id
) > (
    SELECT AVG(cnt)
    FROM (
        SELECT COUNT(DISTINCT subject_id) AS cnt
        FROM grades
        GROUP BY student_id
    )
);
```

---

### **Задание 8**

Показать имена преподавателей и количество студентов, сдававших их предмет.
_(подзапрос в SELECT)_

**Решение:**

```sql
SELECT t.name,
       (SELECT COUNT(DISTINCT g.student_id)
        FROM grades g
        WHERE g.subject_id = t.subject_id) AS student_count
FROM teachers t;
```

---

### **Задание 9**

Найти студентов, у которых все оценки выше 3.
_(коррелированный подзапрос с ALL)_

**Решение:**

```sql
SELECT s.name
FROM students s
WHERE 3 < ALL (
    SELECT g.grade
    FROM grades g
    WHERE g.student_id = s.id
);
```

---

### **Задание 10**

Найти предметы, которые сдавали больше всего студентов.
_(подзапрос в FROM)_

**Решение:**

```sql
SELECT subj.title
FROM subjects subj
WHERE subj.id IN (
    SELECT subject_id
    FROM grades
    GROUP BY subject_id
    HAVING COUNT(DISTINCT student_id) = (
        SELECT MAX(cnt)
        FROM (
            SELECT COUNT(DISTINCT student_id) AS cnt
            FROM grades
            GROUP BY subject_id
        )
    )
);
```

---

Отлично — продолжаем лекцию. Ниже — развёрнутый теоретический блок по CTE, UNION и условной логике (CASE / IFNULL / COALESCE) с понятными, «прикладными» примерами на вашей схеме (students/subjects/grades/teachers). В каждом разделе — краткая теория, наглядные примеры и набор практических упражнений с готовыми решениями и пояснениями.

---

# 2) CTE, UNION и условная логика

## 4. CTE (`WITH`) — теория и преимущества

### Что такое CTE (Common Table Expression)

`CTE` — это именованный временный результат запроса, который определяется перед основным `SELECT` с помощью конструкции `WITH`. По сути, CTE — это способ вынести промежуточный запрос в отдельное, читаемое, переиспользуемое имя.

Общий синтаксис:

```sql
WITH cte_name AS (
    -- любой корректный SELECT
    SELECT ...
)
SELECT ...
FROM cte_name
JOIN ...
```

Можно определять несколько CTE подряд:

```sql
WITH a AS (...), b AS (...)
SELECT ...
FROM a JOIN b ON ...
```

### Зачем использовать CTE — преимущества

- **Читаемость.** Сложную логику разбивают на логические шаги: «сначала вычисли это → потом то».
- **Переиспользование внутри запроса.** Один и тот же промежуточный результат можно использовать несколько раз (в пределах одного запроса).
- **Разделение вычислений.** Легче проверять и отлаживать каждый шаг отдельно.
- **Подготовка данных для рекурсии.** Рекурсивные CTE (`WITH RECURSIVE`) удобны для работы с иерархиями и генерации последовательностей.
- **Замена derived tables.** Иногда CTE читаются лучше, чем вложенные подзапросы в `FROM`.

> Замечание по производительности: поведение CTE зависит от СУБД. В некоторых СУБД CTE _материализуются_ (вычисляются один раз и сохраняются во временной структуре), в других — оптимизатор может «встраивать» CTE в план выполнения. Поэтому при оптимизации запросов стоит смотреть план выполнения. Для обучающих примеров эта деталь не мешает, но при работе с большими объёмами — проверьте поведение вашей СУБД.

### Рекурсивные CTE (кратко)

Для задач с иерархиями или когда нужно сгенерировать последовательность используют `WITH RECURSIVE`:

Пример генерации чисел:

```sql
WITH RECURSIVE nums(n) AS (
  SELECT 1
  UNION ALL
  SELECT n+1 FROM nums WHERE n < 10
)
SELECT n FROM nums;
```

Рекурсивные CTE имеют «якорную» часть (начало) и рекурсивную часть (повторяющуюся). Используются для обхода деревьев, вычисления путей, генерации временных рядов и т.п.

---

## 5. Практика с CTE — задания и решения

### CTE-Задание 1

**Задача:** посчитать средний балл по каждому студенту и вывести `student_id`, `name`, `avg_grade`, отсортировать по среднему по убыванию.
**Решение (CTE):**

```sql
WITH student_avg AS (
    SELECT student_id, AVG(grade) AS avg_grade
    FROM grades
    GROUP BY student_id
)
SELECT s.id AS student_id, s.name, sa.avg_grade
FROM student_avg sa
JOIN students s ON s.id = sa.student_id
ORDER BY sa.avg_grade DESC;
```

**Пояснение:** CTE `student_avg` делает агрегирование отдельно; основной `SELECT` присоединяет названия студентов. Такой приём делает код читабельным и переиспользуемым.

---

### CTE-Задание 2

**Задача:** вывести топ-5 студентов по среднему баллу (name + avg), используя CTE.
**Решение:**

```sql
WITH student_avg AS (
    SELECT student_id, AVG(grade) AS avg_grade
    FROM grades
    GROUP BY student_id
)
SELECT s.name, sa.avg_grade
FROM student_avg sa
JOIN students s ON s.id = sa.student_id
ORDER BY sa.avg_grade DESC
LIMIT 5;
```

**Пояснение:** то же, что и предыдущая задача, но с `LIMIT` — часто встречающийся кейс.

---

### CTE-Задание 3

**Задача:** составить отчёт по предметам: `subject_id`, `subject_title`, `avg_grade`, `count_students` (число уникальных студентов, сдававших предмет).
**Решение:**

```sql
WITH subj_stats AS (
    SELECT subject_id,
           AVG(grade) AS avg_grade,
           COUNT(DISTINCT student_id) AS student_count
    FROM grades
    GROUP BY subject_id
)
SELECT sub.id AS subject_id, sub.title, ss.avg_grade, ss.student_count
FROM subj_stats ss
LEFT JOIN subjects sub ON sub.id = ss.subject_id
ORDER BY ss.avg_grade DESC;
```

**Пояснение:** CTE вычисляет агрегаты, основной запрос добавляет заголовки предметов.

---

### CTE-Задание 4 (комбинированное)

**Задача:** найти предметы, где средний балл выше среднего по всем предметам (global average).
**Решение:**

```sql
WITH subj_avg AS (
    SELECT subject_id, AVG(grade) AS avg_grade
    FROM grades
    GROUP BY subject_id
), global_avg AS (
    SELECT AVG(grade) AS overall FROM grades
)
SELECT sa.subject_id, sub.title, sa.avg_grade
FROM subj_avg sa, global_avg g
JOIN subjects sub ON sub.id = sa.subject_id
WHERE sa.avg_grade > g.overall;
```

**Пояснение:** CTE `global_avg` вычисляет одно число (среднее по всем оценкам). CTE `subj_avg` — по предметам. Основной `SELECT` сравнивает.

---

### CTE-Задание 5 (рекурсивный пример — генерируем числа)

**Задача:** с помощью рекурсивного CTE сгенерируйте числа от 1 до 10 и выведите их.
**Решение:**

```sql
WITH RECURSIVE nums(n) AS (
    SELECT 1
    UNION ALL
    SELECT n+1 FROM nums WHERE n < 10
)
SELECT n FROM nums;
```

**Пояснение:** полезный шаблон — рекурсивный CTE для генерации последовательности (иногда используется для "создания" дат, чисел страниц и т. п.).

---

### CTE-Задание 6 (ранжирование без оконных функций)

**Задача:** посчитать средний балл студентов и присвоить каждому ранг (1 — лучший, 2 — следующий и т.д.) без использования оконных функций (используя CTE + подзапрос).
**Решение:**

```sql
WITH student_avg AS (
  SELECT student_id, AVG(grade) AS avg_grade
  FROM grades
  GROUP BY student_id
)
SELECT s.name, sa.avg_grade,
       (SELECT COUNT(*) + 1
        FROM student_avg sa2
        WHERE sa2.avg_grade > sa.avg_grade) AS rank
FROM student_avg sa
JOIN students s ON s.id = sa.student_id
ORDER BY sa.avg_grade DESC;
```

**Пояснение:** для каждого студента считаем, сколько студентов имеют средний строго выше — это «плюс 1» даёт место в ранге. CTE упрощает выражение.

---

## 6. Объединение запросов: `UNION` vs `UNION ALL`

### Теория

- **`UNION`** объединяет результаты двух (и более) SELECT запросов и **удаляет дубликаты** (повторяющиеся строки).
- **`UNION ALL`** объединяет результаты **без удаления дублей** — быстрее, потому что не выполняется операция удаления дубликатов.

**Требования:** у объединяемых SELECT запросов должно совпадать число столбцов и совместимые типы данных (порядок тоже важен).

### Когда использовать

- `UNION` — когда вам нужен уникальный набор значений (например, список имен из двух таблиц без повторов).
- `UNION ALL` — когда нужны все строки (включая повторы), либо когда явно знаете, что дубликатов нет и хотите повысить производительность.

### Примеры

1. Собрать все имена (студенты + преподаватели) без дублей:

```sql
SELECT name FROM students
UNION
SELECT name FROM teachers;
```

2. То же самое, но с меткой источника, и не удаляя дубликаты:

```sql
SELECT name, 'student' AS who FROM students
UNION ALL
SELECT name, 'teacher' AS who FROM teachers;
```

### Практика (`UNION` / `UNION ALL`) — задания и решения

---

#### U-Задание 1

**Задача:** получить список всех имён (students + teachers) **без дублей** и отсортировать по имени.
**Решение:**

```sql
SELECT name FROM students
UNION
SELECT name FROM teachers
ORDER BY name;
```

**Пояснение:** `UNION` убирает повторы.

---

#### U-Задание 2

**Задача:** получить список всех имён с пометкой источника (`who`) и показать, сколько всего строк получилось (с учётом дублей).
**Решение:**

```sql
SELECT name, 'student' AS who FROM students
UNION ALL
SELECT name, 'teacher' AS who FROM teachers;
```

**Пояснение:** `UNION ALL` сохраняет возможные совпадения имени (например, если человек одновременно преподаватель и студент).

---

## 7. Условная логика: `CASE`, `IFNULL`, `COALESCE`

### `CASE` — условные выражения

`CASE` даёт возможность писать ветвления прямо в `SELECT` (или `ORDER BY`, `HAVING` и пр.). Две формы:

**1) Простая форма (по значению):**

```sql
CASE column
  WHEN value1 THEN result1
  WHEN value2 THEN result2
  ELSE default
END
```

**2) Искусственная / поисковая форма (условия):**

```sql
CASE
  WHEN condition1 THEN result1
  WHEN condition2 THEN result2
  ELSE default
END
```

**Примеры использования:**

- категоризация оценок (`excellent`, `good`, `satisfactory`, `poor`);
- вычисление флажка (`is_top := CASE WHEN avg_grade >= 4.5 THEN 1 ELSE 0 END`).

### `IFNULL(expr, alt)` и `COALESCE(...)`

- `IFNULL(a, b)` — SQLite-функция: если `a IS NULL`, вернуть `b`, иначе — `a`.
- `COALESCE(a, b, c, ...)` — возвращает первый аргумент, который не `NULL`. Удобно для нескольких запасных значений.

**Примеры:**

```sql
SELECT IFNULL(subjects.title, 'No subject') AS title_safe FROM subjects;
SELECT COALESCE(sub.title, 'No subject', 'Unknown') FROM subjects sub;
```

### Практика по условной логике — задания и решения

---

#### K-Задание 1 (CASE: метки оценок)

**Задача:** вывести `student_id`, `subject_id`, `grade`, а также текстовую метку `grade_label`:

- `>=5` → 'excellent'
- `>=4` → 'good'
- `>=3` → 'satisfactory'
- иначе → 'poor'

**Решение:**

```sql
SELECT student_id, subject_id, grade,
  CASE
    WHEN grade >= 5 THEN 'excellent'
    WHEN grade >= 4 THEN 'good'
    WHEN grade >= 3 THEN 'satisfactory'
    ELSE 'poor'
  END AS grade_label
FROM grades;
```

**Пояснение:** Хорошо подходит для отчётных представлений.

---

#### K-Задание 2 (IFNULL / COALESCE)

**Задача:** вывести список оценок вместе с названием предмета, если название отсутствует — показать `'Unknown subject'`.
**Решение:**

```sql
SELECT g.id, COALESCE(sub.title, 'Unknown subject') AS title, g.grade
FROM grades g
LEFT JOIN subjects sub ON sub.id = g.subject_id;
```

**Пояснение:** `COALESCE` защищает от NULL в `title` и делает вывод дружелюбным.

---

#### K-Задание 3 (CASE в ORDER BY)

**Задача:** отсортировать оценки так, чтобы сначала шли `excellent`, затем `good`, и т.д. (использовать CASE в `ORDER BY`).
**Решение:**

```sql
SELECT student_id, subject_id, grade,
  CASE
    WHEN grade >= 5 THEN 1
    WHEN grade >= 4 THEN 2
    WHEN grade >= 3 THEN 3
    ELSE 4
  END AS category_order
FROM grades
ORDER BY category_order, grade DESC;
```

**Пояснение:** сначала вычисляем числовой ранг категории, затем сортируем по нему.

---

## Рекомендации по использованию

- **CTE** отлично подходят для разбивки сложного запроса на логические шаги; используйте их для отчётов и подготовки данных. Рекурсивные CTE — отдельная тема (иерархии, генерация рядов).
- **UNION** убирает дубликаты; **UNION ALL** — быстрее и сохраняет все строки. Выбирайте в зависимости от нужды уникальности.
- **CASE** — главный инструмент для категоризации и условной логики в SQL; **COALESCE/IFNULL** — стандартный метод для обработки NULL.
- Всегда думайте о читаемости запроса: если сложная логика, лучше разложить на CTE — так проще отлаживать.
- При переходе от учебных данных к реальным объёмам обязательно изучите план выполнения запросов (EXPLAIN) — некоторые конструкции (особенно коррелированные подзапросы) могут быть медленными.

---

## Комбинированная практика

### **Задание 1. Использование CTE + агрегаты**

Найти студентов, у которых средний балл выше среднего по всей группе.
_Подсказка:_ в CTE вычисли общий средний балл, а потом сравнивай в основном запросе.

---

### **Задание 2. Подзапрос в SELECT + CASE**

Вывести список студентов и рядом в колонке `status` указать:

- `"Отличник"`, если средний балл ≥ 4.5
- `"Хорошист"`, если средний балл ≥ 3.5
- `"Троечник"`, иначе.
  _Подсказка:_ подзапрос в SELECT вычисляет средний балл, CASE превращает его в текст.

---

### **Задание 3. UNION**

Получить список всех имён из таблицы `students` и всех имён из таблицы `teachers` в одном списке (без повторов).
_Подсказка:_ `UNION` сам уберёт дубликаты.

---

### **Задание 4. UNION ALL + пометка источника**

Составить список всех имён из таблиц `students` и `teachers`, но добавить колонку `"role"`:

- `"student"` для студентов
- `"teacher"` для преподавателей.
  _Подсказка:_ использовать `UNION ALL` и добавить литерал в SELECT.

---

### **Задание 5. CTE + коррелированный подзапрос**

Для каждого предмета вывести средний балл и указать, выше ли он, чем средний балл по этому же предмету у всех студентов вместе.
_Подсказка:_ CTE считает средние, в основном запросе коррелированный подзапрос сравнивает.

---

### **Задание 6. CASE + IFNULL**

Вывести список всех студентов и их средний балл. Если у студента нет оценок, вместо `NULL` вывести `"Нет данных"`.
_Подсказка:_ `IFNULL(AVG(...), 'Нет данных')`.

---

### **Задание 7. Составная задача с CTE и UNION**

Найти:

1. Студентов, у которых средний балл ≥ 4.0.
2. Преподавателей, у которых предметы с средним баллом ≥ 4.0.
   Объединить эти два списка в один (`UNION ALL`), добавив колонку `"type"` = `student` / `teacher`.

---

## Для проверки комбинированной практики

**Задание 1:** Найти студентов, у которых средний балл выше среднего по всей группе.

```sql
WITH avg_all AS (SELECT AVG(grade) AS g FROM grades)
SELECT s.name, AVG(g.grade) AS avg_student
FROM students s
JOIN grades g ON s.id = g.student_id
GROUP BY s.id
HAVING avg_student > (SELECT g FROM avg_all);
```

---

**Задание 2:** Вывести студентов со статусом (Отличник/Хорошист/Троечник).

```sql
SELECT s.name,
        CASE
            WHEN (SELECT AVG(g.grade) FROM grades g WHERE g.student_id = s.id) >= 4.5 THEN 'Отличник'
            WHEN (SELECT AVG(g.grade) FROM grades g WHERE g.student_id = s.id) >= 3.5 THEN 'Хорошист'
            ELSE 'Троечник'
        END AS status
FROM students s;
```

---

**Задание 3:** Получить список имён студентов и преподавателей (без повторов).

```sql
SELECT name FROM students
UNION
SELECT name FROM teachers;
```

---

**Задание 4:** Список имён студентов и преподавателей с пометкой роли.

```sql
SELECT name, 'student' AS role FROM students
UNION ALL
SELECT name, 'teacher' AS role FROM teachers;
```

---

**Задание 5:** Средний балл по предметам + сравнение с общим средним.

```sql
WITH subj_avg AS (
    SELECT subject_id, AVG(grade) AS avg_subj
    FROM grades
    GROUP BY subject_id
)
SELECT sub.title, sa.avg_subj,
        CASE
            WHEN sa.avg_subj > (SELECT AVG(grade) FROM grades) THEN 'Выше общего среднего'
            ELSE 'Не выше'
        END AS comparison
FROM subj_avg sa
JOIN subjects sub ON sub.id = sa.subject_id;
```

---

**Задание 6:** Средний балл студентов, если нет оценок — вывести 'Нет данных'.

```sql
SELECT s.name, IFNULL(ROUND(AVG(g.grade), 2), 'Нет данных') AS avg_grade
FROM students s
LEFT JOIN grades g ON s.id = g.student_id
GROUP BY s.id;
```

---

**Задание 7:** Студенты со ср.баллом ≥ 4.0 и преподаватели, у которых предметы ≥ 4.0.

```sql
WITH good_students AS (
    SELECT s.name, 'student' AS type
    FROM students s
    JOIN grades g ON s.id = g.student_id
    GROUP BY s.id
    HAVING AVG(g.grade) >= 4.0
),
good_teachers AS (
    SELECT t.name, 'teacher' AS type
    FROM teachers t
    JOIN grades g ON t.subject_id = g.subject_id
    GROUP BY t.id
    HAVING AVG(g.grade) >= 4.0
)
SELECT * FROM good_students
UNION ALL
SELECT * FROM good_teachers;
```

---

# Вопросы
1. Что такое **подзапрос** и где он может использоваться в SQL?
2. Чем отличается **скалярный подзапрос** от подзапроса, возвращающего несколько строк?
3. Что такое **коррелированный подзапрос**?
4. Для чего используется ключевое слово **WITH (CTE)**?
5. В чём отличие между **UNION** и **UNION ALL**?
6. Как работает конструкция **CASE**?
7. В чём разница между **IFNULL** и **COALESCE**?
8. Можно ли использовать CTE рекурсивно? Для чего это нужно?
9. Почему иногда выгоднее использовать CTE вместо подзапросов?
10. Зачем в реальных проектах используют UNION?

---

[Предыдущий урок](lesson08.md) | [Следующий урок](lesson10.md)
