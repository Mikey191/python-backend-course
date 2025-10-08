# Модуль 2. Урок 10. Модификация данных. CRUD

## Введение: «Зачем CRUD»

**CRUD** — это фундаментальная модель работы с данными в любых приложениях. Это не просто набор слов — `Create`, `Read`, `Update`, `Delete` — это набор действий, которые можно выполнять над любой сущностью: пользователем, заказом, статьёй, студентом. Понимание CRUD даёт вам инструмент думать о данных последовательно и системно: какие операции нужны, какие ограничения и проверки надо поставить, и как строить интерфейсы (CLI, HTTP, GUI), которые с этими операциями работают.

Почему это важно именно сейчас:

- Любое приложение, где есть данные, рано или поздно реализует CRUD. Если вы умеете грамотно отделять реализацию CRUD от бизнес-логики, ваш код становится проще, надёжнее и легче тестируется.
- CRUD — это та часть, которую вы будете повторять в разных проектах: регистрация пользователей, управление товарами, обработка заявок, ведение журналов. Освоив CRUD хорошо, вы получаете универсальный навык.
- На базе CRUD строятся более сложные операции: отчёты, пересчёты, миграции данных. Но сначала — нужно уметь делать базовые операции правильно.

Этот урок даёт практическое понимание CRUD: что это такое, зачем это нужно, как формально выглядят запросы и простые функции-обёртки в Python. В дальнейшем мы возьмём те же операции и встроим их в небольшое приложение: три сущности — студенты, предметы, группы — и терминальный интерфейс для работы с ними.

---

# Что такое CRUD

**CRUD** — это аббревиатура из четырёх фундаментальных действий над **сущностью** в базе данных:

- **C — Create (создать)**: добавить новую запись в таблицу.
- **R — Read (прочитать)**: получить одну или несколько записей (просмотр/поиск).
- **U — Update (обновить)**: изменить существующую запись.
- **D — Delete (удалить)**: удалить запись.

Ниже дано чёткое описание каждой операции, понятные примеры SQL и простая реализация в Python (sqlite3). Этот текст можно использовать как справочник: прочитал — скопировал — применил.

---

**Create — создать запись**

**Описание**: `Create` добавляет новую запись в таблицу. Всегда указывайте те поля, которые обязательны по схеме таблицы, и перед вставкой валидируйте вход (например: email корректен, имя не пустое). При выполнении вставки важно обрабатывать ошибки уникальности и нарушения ограничений, чтобы приложение не упало необработанным исключением.

SQL-пример (добавление студента):

```sql
INSERT INTO students (first_name, last_name, email, subject_id, group_id)
VALUES ('Анна', 'Иванова', 'anna@example.com', 1, 2);
```

Простой пример на Python (sqlite3):

```python
import sqlite3

def create_student(conn, first_name, last_name, email, subject_id=None, group_id=None):
    sql = """
    INSERT INTO students (first_name, last_name, email, subject_id, group_id)
    VALUES (?, ?, ?, ?, ?)
    """
    cur = conn.cursor()
    cur.execute(sql, (first_name, last_name, email, subject_id, group_id))
    return cur.lastrowid
```

Пояснение: функция принимает подключение `conn` (объект sqlite3.Connection), выполняет INSERT и возвращает `id` созданной записи.

---

**Read — прочитать данные**

**Описание**: `Read` возвращает запись(и). Чтение делят на два случая: получить одну запись по идентификатору (`get_by_id`) и получить список/набор записей по фильтрам (`list`/`search`). Для списков полезны сортировка и лимиты.

SQL-примеры:

Одну запись по id:

```sql
SELECT id, first_name, last_name, email, subject_id, group_id
FROM students
WHERE id = 42;
```

Список студентов с именем предмета (JOIN):

```sql
SELECT s.id, s.first_name || ' ' || s.last_name AS full_name, subj.name AS subject, g.name AS group_name
FROM students s
LEFT JOIN subjects subj ON s.subject_id = subj.id
LEFT JOIN groups g ON s.group_id = g.id
ORDER BY s.last_name, s.first_name;
```

Python-обёртка для получения одной записи:

```python
def get_student(conn, student_id):
    sql = "SELECT * FROM students WHERE id = ?"
    cur = conn.cursor()
    cur.execute(sql, (student_id,))
    return cur.fetchone()  # вернёт sqlite3.Row или None
```

---

**Update — изменить существующую запись**

**Описание**: `Update` меняет одно или несколько полей у уже существующей строки. Практика: обновляйте только те поля, которые переданы, чтобы не перезаписывать поля ненужными значениями. При обновлении полезно возвращать, сколько строк пострадало (affected rows), чтобы понять, была ли запись найдена.

SQL-пример (обновить email и группу):

```sql
UPDATE students
SET email = 'anna.new@example.com', group_id = 3
WHERE id = 42;
```

Python-реализация (упрощённая, обновляет конкретные поля):

```python
def update_student_email_and_group(conn, student_id, email=None, group_id=None):
    parts = []
    params = []
    if email is not None:
        parts.append("email = ?")
        params.append(email)
    if group_id is not None:
        parts.append("group_id = ?")
        params.append(group_id)
    if not parts:
        return 0  # ничего обновлять не нужно
    sql = f"UPDATE students SET {', '.join(parts)} WHERE id = ?"
    params.append(student_id)
    cur = conn.cursor()
    cur.execute(sql, tuple(params))
    return cur.rowcount  # число обновлённых строк
```

---

**Delete — удалить запись**

**Описание**: `Delete` удаляет строку из таблицы. Удаление имеет побочные эффекты, если есть связи (FOREIGN KEY). Поэтому при проектировании схемы важно заранее решить: удаление родителя должно удалять детей (CASCADE), обнулять ссылку (SET NULL) или запрещаться (RESTRICT/NO ACTION).

SQL-пример:

```sql
DELETE FROM students WHERE id = 42;
```

Python:

```python
def delete_student(conn, student_id):
    sql = "DELETE FROM students WHERE id = ?"
    cur = conn.cursor()
    cur.execute(sql, (student_id,))
    return cur.rowcount
```

---

**Примеры из реальных приложений (как CRUD выглядит «в жизни»)**

1. **Регистрация и профиль пользователя**

   - Create: регистрация — `INSERT users (...)`.
   - Read: показать профиль — `SELECT * FROM users WHERE id = ?`.
   - Update: пользователь меняет email/пароль — `UPDATE users SET email = ? WHERE id = ?`.
   - Delete: удалить аккаунт — либо `DELETE` в БД, либо «мягкое» удаление `UPDATE users SET is_active = 0`.

2. **Каталог товаров (e-commerce)**

   - Create: админ добавляет товар в каталог — `INSERT products (...)`.
   - Read: страница товара — `SELECT ... FROM products WHERE id = ?`, список товаров — `SELECT ... ORDER BY price`.
   - Update: смена цены или наличия — `UPDATE products SET price = ?, stock = ?`.
   - Delete: удалить «устаревший» товар — чаще делают soft-delete.

3. **Система учёта (наш учебный пример)**

   - Create: создать студента/предмет/группу.
   - Read: показать список студентов, профиль студента с названием предмета и группой (JOIN).
   - Update: перевести студента в другую группу или сменить основной предмет.
   - Delete: удалить предмет — поведение зависит от `ON DELETE`: либо у студентов `subject_id` станет NULL, либо студенты будут удалены (если настроен CASCADE).

---

Короткая памятка (что важно помнить при работе с CRUD)

- Всегда проверяйте входные данные перед `INSERT`/`UPDATE`: обязательные поля, формат (email), допустимые значения.
- Обрабатывайте ошибки ограничений (UNIQUE/NOT NULL/FOREIGN KEY): база выдаст исключение — приложению нужно поймать и вернуть понятную пользователю ошибку.
- При `Read` используйте JOIN, когда нужно показать связанные данные (например, название предмета вместо `subject_id`).
- Для `Update` удобнее принимать только изменяемые поля и строить `SET` динамически.
- Для `Delete` заранее решайте политику каскада и последствия для связанных таблиц.

---

# Что такое API и почему CRUD — ключевая часть API

## Что такое API — простыми словами

**API (Application Programming Interface)** — это формальный договор между частями программы: набор правил и интерфейсов, по которым одна часть системы обращается к другой. API описывает _что_ можно попросить сделать и _что_ в ответ придёт, но не диктует _как_ это реализовано внутри.

API может быть:

- **внешним** — например, HTTP-API сервера, которым пользуется мобильное приложение;
- **внутренним** — модули внутри одного приложения, у которых есть чётко оформленные функции/классы (например, слой доступа к данным).

В обоих случаях **API — это контракт**: входные параметры, ожидаемый результат, и поведение при ошибках. Если контракт соблюдён, разные части системы могут развиваться независимо.

---

## Почему `CRUD` — основа (и самая важная часть) API

Большинство ресурсов в приложениях — это сущности: пользователи, заказы, студенты, предметы. Для каждой сущности почти всегда нужен один и тот же минимальный набор операций:

- **Create** — создать новый ресурс;
- **Read** — получить ресурс(ы);
- **Update** — изменить ресурс;
- **Delete** — удалить ресурс.

Эти четыре операции формируют **ядро API**. Остальные функции — валидация, бизнес-правила и отчёты — строятся поверх CRUD. Поэтому, проектируя API, первым делом определяют CRUD-контракт для каждой сущности: что можно создать, что можно прочитать, что можно обновить и что можно удалить.

---

## Уровни API в приложении

Хорошая архитектура разделяет ответственность на уровни. Это делает код понятным, облегчает изменение реализации и упрощает тестирование.

Последовательность уровней (снизу вверх):

### 1. DB (connection) — низкоуровневый слой

**Назначение:** открывает и закрывает соединение с базой данных, выполняет сырые SQL-запросы и возвращает результаты.

**Что здесь делают:** `execute`, `executemany`, `executescript`, `fetchone`, `fetchall`, установка PRAGMA (в SQLite).

**Почему отдельно:** абстрагирует детали СУБД; при смене СУБД меняем только этот слой.

**Пример интерфейса:**

```python
class DB:
    def execute(self, sql: str, params: tuple = ()) -> int: ...
    def fetchone(self, sql: str, params: tuple = ()) -> Row|None: ...
    def fetchall(self, sql: str, params: tuple = ()) -> list[Row]: ...
```

---

### 2. Repository (или Data Access Layer) — CRUD

**Назначение:** реализует CRUD-операции для конкретных сущностей. Репозиторий переводит вызовы в SQL и возвращает удобные объекты (Row, dict, DTO).

**Что здесь делают:** `create_student(...)`, `get_student(id)`, `list_students(filters)`, `update_student(id, fields)`, `delete_student(id)`.

**Почему отдельно:** репозиторий стандартизирует работу с данными, инкапсулирует SQL и даёт единое место для оптимизаций (индексы, запросы).
**Пример функций:**

```python
class StudentRepo:
    def create(self, first_name, last_name, email, subject_id=None, group_id=None) -> int: ...
    def get(self, student_id) -> dict | None: ...
    def update(self, student_id, **fields) -> int: ...
    def delete(self, student_id) -> int: ...
    def list(self, filters: dict = None) -> list[dict]: ...
```

**Примечание:** репозиторий не должен реализовывать сложную бизнес-логику — только доступ к данным и базовые проверки (например, проверка существования).

---

### 3. Service (бизнес-слой)

**Назначение:** реализует правила предметной области, комбинирует несколько CRUD-операций, выполняет валидацию и принимает решения. Именно сюда помещают сценарии **«перевести студента в другую группу»**, **«зарегистрировать студента и поставить его в группу по умолчанию»**, **«создать предмет и оповестить преподавателя»** и т.п.

**Почему отдельно:** service-слой — единственное место, где живёт логика приложения; интерфейс и репозитории становятся простыми и переиспользуемыми.

**Пример (сигнатуры):**

```python
class StudentService:
    def transfer_group(self, student_id: int, new_group_id: int) -> None: ...
    def enroll_student(self, data: dict) -> int: ...
```

**Что делает `transfer_group`:**

- проверяет, что студент существует (через репозиторий),
- проверяет, что целевая группа существует,
- выполняет обновление (через репозиторий) и возвращает результат или бросает понятную ошибку.

---

### 4. Interface (CLI / HTTP / GUI)

**Назначение:** пользовательский слой, принимает ввод (с консоли или по HTTP), валидирует формат, вызывает сервисы и форматирует ответ. Интерфейс работает с сервисами, а не со слоями ниже напрямую.

**Почему отдельно:** позволяет менять способ взаимодействия (CLI → Web → REST API) без изменения бизнес-логики.

**Пример CLI-вызова:**

```python
# main.py
actions = {
  "1": ("Create student", lambda: cli_create_student()),
  ...
}
# cli_create_student собирает данные, вызывает student_service.enroll_student(...)
```

---

## Примеры: как это выглядит на практике

Ниже — пошаговый пример вызова «создать студента и тут же показать профиль», проходящий через все уровни.

1. **Interface (CLI):**

   - пользователь вводит имя и email → вызывается `student_service.enroll_student(data)`

2. **Service (`StudentService.enroll_student`):**

   - валидирует формат email, проверяет бизнес-правила (например, группа доступна),
   - вызывает `StudentRepo.create(...)`,
   - возвращает `student_id`.

3. **Repository (`StudentRepo.create`):**

   - формирует SQL `INSERT` и вызывает `DB.execute(sql, params)`,
   - получает `lastrowid` и возвращает его.

4. **DB:**

   - выполняет запрос, коммитит транзакцию и возвращает результат.

Такое разделение делает код предсказуемым и простым для сопровождения.

---

## Преимущества разделения на уровни

1. **Чистота кода и SOLID.** Каждый слой решает свою задачу — легче читать и понимать.
2. **Замена деталей без трений.** Хотите перейти с SQLite на Postgres — меняете `DB` и, возможно, небольшие SQL-шаблоны в репозитории; `service` и `interface` остаются без изменений.
3. **Повторное использование.** Одна и та же бизнес-логика доступна через CLI и через HTTP, потому что оба слоя используют сервисы.
4. **Тестируемость.** Можно мокировать `DB` или `Repo` и тестировать `Service` отдельно (в будущем, когда будете писать тесты).
5. **Ясные границы ответственности.** Ошибки легче локализовать: если некорректный SQL — смотреть в `Repo/DB`; если бизнес-правила нарушены — смотреть в `Service`; если неверный ввод — смотреть в `Interface`.

---

## Рекомендации по интерфейсам функций и обработке ошибок

- **Единообразие возвращаемых типов.** Репозитории лучше возвращают словари (`dict`) или `sqlite3.Row`, а не сырые кортежи.
- **Ясные исключения.** Создавать собственные типы ошибок (например, `NotFoundError`, `ValidationError`, `ConflictError`) и пробрасывать их вверх — тогда интерфейс может красиво форматировать сообщения для пользователя.
- **Минимальная валидация на уровне репозитория.** Репозиторий проверяет только технические требования (например, не отправляет `NULL` в поле `NOT NULL`), основные проверки — в `Service`.
- **Логирование.** Логируйте ошибки и, при отладке, сам SQL (в dev режиме) в `DB`.

---

# Ограничения в SQL

## Введение — зачем нужны ограничения в схеме

Ограничения (constraints) — это **правила, которые мы записываем в схеме базы данных**, чтобы гарантирова­ть корректность данных независимо от ошибок в приложении.
Они помогают базе автоматически:

- **защищать от дубликатов** (например, два пользователя с одним email);
- **поддерживать целостность связей** между таблицами (чтобы не появлялись «висящие» ссылки);
- **обеспечивать корректность значений** (например, оценка должна быть в диапазоне 0–100);
- **уменьшать количество багов в приложении**, поскольку часть валидации выполняется на уровне БД.

Разумное сочетание валидации в приложении + ограничений в схеме — почти всегда лучший выбор.

---

## Основные виды ограничений и их смысл

### PRIMARY KEY

`PRIMARY KEY` — уникальный идентификатор строки.

- Обычно используется `INTEGER PRIMARY KEY AUTOINCREMENT` (в SQLite) для автоинкрементного id.
- В таблице может быть **только один** PRIMARY KEY; он по сути задаёт уникальность и not-null для указанного столбца (или набора столбцов).

**Пример:**

```sql
CREATE TABLE subjects (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL
);
```

---

### UNIQUE

`UNIQUE` гарантирует, что значения в столбце (или группе столбцов) **не будут повторяться**.
Полезно для email, имен с уникальным требованием и т.п.

**Пример (одиночный столбец):**

```sql
CREATE TABLE students (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  email TEXT NOT NULL UNIQUE
);
```

**Пример (составной уникальный индекс):**

```sql
CREATE TABLE enrollment (
  student_id INTEGER,
  subject_id INTEGER,
  PRIMARY KEY (student_id, subject_id)  -- не даст дубликатов пар
);
```

---

### NOT NULL

`NOT NULL` запрещает поле со значением `NULL`.
Применяется к обязательным полям (имя, фамилия, email и т.п.).

**Пример:**

```sql
CREATE TABLE groups (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL
);
```

---

### CHECK

`CHECK` позволяет задать произвольное булево-условие на значения столбца. Полезно для ограничения диапазонов или списка допустимых значений.
Обратите внимание: в разных СУБД поведение `CHECK` может отличаться, но в SQLite он поддерживается.

**Примеры:**

- ограничить роль в `group_members`:

```sql
role TEXT NOT NULL DEFAULT 'member' CHECK (role IN ('member', 'leader', 'assistant'))
```

- проверка диапазона:

```sql
grade REAL CHECK (grade >= 0 AND grade <= 100)
```

---

### DEFAULT

`DEFAULT` задаёт значение по умолчанию, если при вставке значение не передано.
**Пример:**

```sql
created_at TEXT DEFAULT CURRENT_TIMESTAMP
```

---

### FOREIGN KEY + ON DELETE / ON UPDATE

`FOREIGN KEY` связывает столбец с ключом в другой таблице — это основной инструмент для ссылочной целостности.
Очень важно явно задать поведение при удалении/обновлении родительской записи через `ON DELETE` / `ON UPDATE`.

**Типичные опции:**

- `ON DELETE CASCADE` — при удалении родителя удаляются все связанные записи-дети.

  - Удобно для связей «жёсткого владения».

- `ON DELETE SET NULL` — при удалении родителя у дочерних записей поле внешнего ключа становится `NULL`.

  - Удобно, когда не хотим терять дочерние строки (например, студенты остаются в базе, даже если предмет удалён).

- `ON DELETE RESTRICT` / `NO ACTION` — запрещает удаление родителя, если есть дочерние записи.

  - Полезно, если удаление родителя должно быть явным и сопровождаемым дополнительной логикой.

**Пример:**

```sql
CREATE TABLE students (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  first_name TEXT NOT NULL,
  last_name TEXT NOT NULL,
  email TEXT NOT NULL UNIQUE,
  subject_id INTEGER,
  group_id INTEGER,
  FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE SET NULL,
  FOREIGN KEY (group_id) REFERENCES groups(id) ON DELETE SET NULL
);
```

**Важно для SQLite:** необходимо включать проверку внешних ключей:

```sql
PRAGMA foreign_keys = ON;
```

Если `PRAGMA foreign_keys` выключен, SQLite **игнорирует** FK-ограничения!

---

## Примеры: как ограничения работают на практике

### 1) Защита от дубликата email

Если `email` помечен как `UNIQUE`, попытка вставить другой студент с тем же email приведёт к ошибке (в Python — `sqlite3.IntegrityError`). Это предотвращает неудобные состояния в приложении и избавляет от дополнительной синхронизации.

**SQL:**

```sql
INSERT INTO students (first_name, last_name, email) VALUES ('Иван', 'Иванов', 'ivan@example.com');
-- Повторная попытка вставки с тем же email вызовет ошибку UNIQUE constraint.
```

### 2) Целостность ссылок — удаление предмета

Если мы используем `ON DELETE SET NULL` для `subject_id`, удаление предмета не удалит студентов, а только обнулит их `subject_id`. Если использовать `ON DELETE CASCADE`, при удалении предмета удалятся и все студенты, у которых этот предмет был основным — это опасное поведение, но иногда желаемое (например, удаление временных сущностей).

**Показательный SQL:**

```sql
-- удаляем subject с id = 2
DELETE FROM subjects WHERE id = 2;
-- при ON DELETE SET NULL: у студентов subject_id станет NULL
-- при ON DELETE CASCADE: студенты с subject_id=2 будут удалены
```

---

## Обработка ошибок ограничений в Python (sqlite3)

Когда БД обнаруживает нарушение ограничения, она выбрасывает ошибку. В sqlite3 это `sqlite3.IntegrityError`. На уровне приложения стоит ловить такие ошибки и превращать их в понятные сообщения пользователю.

**Пример:**

```python
import sqlite3

def create_student(conn, first_name, last_name, email, subject_id=None, group_id=None):
    sql = """
    INSERT INTO students (first_name, last_name, email, subject_id, group_id)
    VALUES (?, ?, ?, ?, ?)
    """
    try:
        cur = conn.cursor()
        cur.execute(sql, (first_name, last_name, email, subject_id, group_id))
        conn.commit()
        return cur.lastrowid
    except sqlite3.IntegrityError as e:
        # простая обработка: различаем по тексту ошибки (можно делать по коду в других СУБД)
        msg = str(e).lower()
        if 'unique' in msg and 'email' in msg:
            raise ValueError("Пользователь с таким email уже существует")
        else:
            raise
```

**Рекомендация:** не показывать сырой текст ошибки БД пользователю — формируйте читабельные сообщения.

---

## CHECK в SQLite — нюансы и примеры использования

`CHECK` — мощный инструмент, но в SQLite есть нюансы:

- SQLite поддерживает `CHECK`, но поведение может отличаться в старых версиях. Обычно всё работает.
- `CHECK` проверяется при `INSERT` и `UPDATE`.
- `CHECK` удобно использовать для простых правил (диапазоны, перечисления), но не для сложной логики, зависящей от других таблиц.

**Пример — роль участника группы:**

```sql
CREATE TABLE group_members (
  group_id INTEGER NOT NULL,
  student_id INTEGER NOT NULL,
  role TEXT NOT NULL DEFAULT 'member' CHECK(role IN ('member','leader','assistant')),
  PRIMARY KEY (group_id, student_id),
  FOREIGN KEY (group_id) REFERENCES groups(id) ON DELETE CASCADE,
  FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
);
```

---

## Практические DDL-примеры (готовые для запуска)

Ниже — компактная схема для проекта с тремя сущностями. Можно скопировать и выполнить в SQLiteStudio или из Python (через `executescript`).

```sql
PRAGMA foreign_keys = ON;

-- groups
CREATE TABLE IF NOT EXISTS groups (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL UNIQUE
);

-- subjects
CREATE TABLE IF NOT EXISTS subjects (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL UNIQUE,
  CHECK (length(name) > 0)
);

-- students
CREATE TABLE IF NOT EXISTS students (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  first_name TEXT NOT NULL,
  last_name TEXT NOT NULL,
  email TEXT NOT NULL UNIQUE,
  subject_id INTEGER,
  group_id INTEGER,
  FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE SET NULL,
  FOREIGN KEY (group_id) REFERENCES groups(id) ON DELETE SET NULL,
  CHECK (length(first_name) > 0 AND length(last_name) > 0)
);
```

---

## Рекомендации по проектированию ограничений — практические правила

1. **Думайте о правильной семантике `ON DELETE`.**

   - Если дочерняя сущность бессмысленна без родителя — используйте `CASCADE`.
   - Если дочерняя сущность важна сама по себе (например, студенты) — чаще `SET NULL` или `RESTRICT`.

2. **UNIQUE на уровне БД, а не только в коде.**

   - Даже если вы проверяете уникальность в коде, гонки и параллельные запросы могут привести к дублям; только ограничение в БД делает это гарантийно.

3. **NOT NULL для обязательных полей.**

   - Не доверяйте только UI — делайте `NOT NULL` там, где поле обязательно.

4. **CHECK для простых инвариантов.**

   - Ограничивайте наборы значений и диапазоны чисел через `CHECK`.

5. **DEFAULT для удобства.**

   - Полезно для полей роли, статуса и т. п.

6. **Логика + ограничения.**

   - Не пытайтесь поместить всю бизнес-логику в `CHECK` или триггеры — делайте основные проверки в `Service`, а базовую целостность — в схеме.

---

# Практика: Создание приложения CRUD

Теперь, когда мы разобрались с концепцией CRUD, API и ограничениями данных, самое время применить всё на практике.

Мы создадим простое, но хорошо структурированное приложение на **Python + SQLite**, которое будет реализовывать CRUD-операции для трёх сущностей — **студенты**, **группы** и **предметы**, а также небольшую бизнес-логику: перевод студента из одной группы в другую.

Наша цель — не просто заставить приложение «работать», а научиться правильно **разделять логику**: где хранить SQL-запросы, где реализовывать бизнес-операции, и как организовать простой интерфейс взаимодействия.

---

## 1. Схема базы данных

Мы будем работать с тремя таблицами: **students**, **groups** и **subjects**.
В таблицах используются ограничения, которые обеспечивают уникальность и целостность данных.

```sql
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS subjects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    group_id INTEGER,
    subject_id INTEGER,
    FOREIGN KEY (group_id) REFERENCES groups(id) ON DELETE SET NULL,
    FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE SET NULL
);
```

🔹 Здесь:

- Каждый студент принадлежит одной группе и может изучать один предмет.
- Если удалить группу или предмет, студенты не удаляются, а просто теряют связь (`SET NULL`).
- Email студента уникален.
- Все поля имени обязательны (`NOT NULL`).

---

## 2. Структура проекта

Приложение будет состоять из нескольких файлов, каждый из которых отвечает за свою часть логики.

```
crud_app/
│
├── core.py         # класс для взаимодействия с базой данных (создание, подключение, выполнение запросов)
├── repository.py   # CRUD-операции (Create, Read, Update, Delete)
├── logic.py        # бизнес-логика (например, перевод студента в другую группу)
├── interface.py    # терминальный интерфейс (меню и обработка действий)
└── main.py         # точка входа в программу
```

Такое разделение помогает проекту быть гибким:

- если нужно заменить SQLite на PostgreSQL — достаточно адаптировать `core.py`;
- если изменится бизнес-логика — меняем `logic.py`, не затрагивая интерфейс.

---

## 3. Реализация `core.py` — базовый класс для взаимодействия с БД

```python
# core.py
import sqlite3

class Database:
    def __init__(self, db_name="students.db"):
        self.db_name = db_name
        self.conn = sqlite3.connect(self.db_name)
        self.conn.execute("PRAGMA foreign_keys = ON;")

    def executescript(self, script: str):
        """Выполнение SQL-скрипта (для создания таблиц)"""
        with self.conn:
            self.conn.executescript(script)

    def execute(self, query, params=(), fetchone=False, fetchall=False, commit=False):
        """Универсальный метод для запросов"""
        cur = self.conn.cursor()
        cur.execute(query, params)
        if commit:
            self.conn.commit()
        if fetchone:
            return cur.fetchone()
        if fetchall:
            return cur.fetchall()

    def close(self):
        self.conn.close()
```

Этот класс инкапсулирует всю работу с базой: подключение, выполнение запросов и коммит транзакций.
Мы избегаем дублирования кода и обеспечиваем централизованное управление соединением.

---

## 4. Реализация `repository.py` — CRUD для всех сущностей

В этом модуле определим класс `Repository`, который содержит все операции для студентов, групп и предметов.
Каждый метод соответствует одной CRUD-операции.

```python
# repository.py
from core import Database

class Repository:
    def __init__(self, db: Database):
        self.db = db

    # ---------- ГРУППЫ ----------
    def create_group(self, name):
        query = "INSERT INTO groups (name) VALUES (?)"
        self.db.execute(query, (name,), commit=True)

    def get_all_groups(self):
        return self.db.execute("SELECT * FROM groups", fetchall=True)

    def update_group(self, group_id, new_name):
        self.db.execute("UPDATE groups SET name = ? WHERE id = ?", (new_name, group_id), commit=True)

    def delete_group(self, group_id):
        self.db.execute("DELETE FROM groups WHERE id = ?", (group_id,), commit=True)

    # ---------- ПРЕДМЕТЫ ----------
    def create_subject(self, name):
        self.db.execute("INSERT INTO subjects (name) VALUES (?)", (name,), commit=True)

    def get_all_subjects(self):
        return self.db.execute("SELECT * FROM subjects", fetchall=True)

    def update_subject(self, subject_id, new_name):
        self.db.execute("UPDATE subjects SET name = ? WHERE id = ?", (new_name, subject_id), commit=True)

    def delete_subject(self, subject_id):
        self.db.execute("DELETE FROM subjects WHERE id = ?", (subject_id,), commit=True)

    # ---------- СТУДЕНТЫ ----------
    def create_student(self, first_name, last_name, email, group_id=None, subject_id=None):
        query = """
        INSERT INTO students (first_name, last_name, email, group_id, subject_id)
        VALUES (?, ?, ?, ?, ?)
        """
        self.db.execute(query, (first_name, last_name, email, group_id, subject_id), commit=True)

    def get_all_students(self):
        return self.db.execute("""
        SELECT s.id, s.first_name, s.last_name, s.email, g.name as group_name, sub.name as subject_name
        FROM students s
        LEFT JOIN groups g ON s.group_id = g.id
        LEFT JOIN subjects sub ON s.subject_id = sub.id
        """, fetchall=True)

    def update_student_email(self, student_id, new_email):
        self.db.execute("UPDATE students SET email = ? WHERE id = ?", (new_email, student_id), commit=True)

    def delete_student(self, student_id):
        self.db.execute("DELETE FROM students WHERE id = ?", (student_id,), commit=True)
```

Здесь мы видим классический CRUD:

- **Create** — вставка новых записей.
- **Read** — чтение данных (с JOIN для удобного отображения).
- **Update** — изменение значений.
- **Delete** — удаление.

---

## 5. Реализация бизнес-логики в `logic.py`

Теперь добавим немного «жизни» в приложение — операцию перевода студента в другую группу.

Эта операция требует целостности, поэтому мы выполняем её **в транзакции**.

```python
# logic.py
from core import Database

def transfer_student_to_group(db: Database, student_id: int, new_group_id: int):
    """Перевод студента в другую группу"""
    try:
        with db.conn:
            db.execute("UPDATE students SET group_id = ? WHERE id = ?", (new_group_id, student_id))
    except Exception as e:
        print(f"Ошибка при переводе: {e}")
```

Если перевод будет состоять из нескольких действий (например, обновить группу и добавить запись в журнал изменений), всё должно выполняться атомарно.
Благодаря `with db.conn:` — SQLite автоматически откатывает изменения, если произойдёт ошибка.

---

## 6. Реализация интерфейса — `interface.py`

Интерфейс будет простым: пользователь видит меню с номерами действий и выбирает нужное.
Мы будем использовать словарь, где ключ — это цифра, а значение — кортеж с описанием и функцией, которую нужно вызвать.

```python
# interface.py
from repository import Repository
from logic import transfer_student_to_group

def show_data(data):
    """Удобный вывод таблицы данных"""
    if not data:
        print("Нет данных для отображения.")
    else:
        for row in data:
            print(row)

def menu(repo: Repository):
    actions = {
        "1": ("Показать всех студентов", lambda: show_data(repo.get_all_students())),
        "2": ("Добавить студента", lambda: repo.create_student(
            input("Имя: "), input("Фамилия: "), input("Email: ")
        )),
        "3": ("Удалить студента", lambda: repo.delete_student(int(input("ID студента: ")))),
        "4": ("Показать все группы", lambda: show_data(repo.get_all_groups())),
        "5": ("Добавить группу", lambda: repo.create_group(input("Название группы: "))),
        "6": ("Перевести студента в другую группу", lambda: transfer_student_to_group(
            repo.db,
            int(input("ID студента: ")),
            int(input("ID новой группы: "))
        )),
        "0": ("Выход", lambda: exit())
    }

    while True:
        print("\n--- МЕНЮ ---")
        for key, (desc, _) in actions.items():
            print(f"{key}. {desc}")
        choice = input("Выберите действие: ")
        if choice in actions:
            actions[choice][1]()
        else:
            print("Неверный выбор, попробуйте снова.")
```

---

## 7. Точка входа в приложение — `main.py`

```python
# main.py
from core import Database
from repository import Repository
from interface import menu

CREATE_SCRIPT = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS subjects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    group_id INTEGER,
    subject_id INTEGER,
    FOREIGN KEY (group_id) REFERENCES groups(id) ON DELETE SET NULL,
    FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE SET NULL
);
"""

def main():
    db = Database()
    db.executescript(CREATE_SCRIPT)
    repo = Repository(db)
    menu(repo)
    db.close()

if __name__ == "__main__":
    main()
```

---

Отлично 👏
**Store App** — прекрасный выбор: понятная бизнес-модель, логичные связи, много возможностей для тренировки CRUD.
Ниже я подготовил **полноценный материал для самостоятельной практики**, который можно сразу вставить в курс.
Он написан в повествовательной, “учебной” форме — студенты смогут читать, понимать, планировать и выполнять шаги без необходимости дополнительного объяснения.

---

# Практика (Самостоятельно): «Store App — магазин товаров»

## Цель практики

Приложение должно уметь хранить список товаров, категорий и заказов, выполнять все CRUD-операции и обрабатывать простую бизнес-логику — оформление заказа с изменением количества товара на складе.

Что нужно использовать:

- создании таблиц с ограничениями (`UNIQUE`, `NOT NULL`, `CHECK`, `FOREIGN KEY`);
- реализации CRUD (Create, Read, Update, Delete);
- разделении логики приложения по уровням;
- работе с базой данных через Python и `sqlite3`.

---

## Схема базы данных

Создать три таблицы:

### 1. `categories` — категории товаров

Содержит список категорий, к которым относятся товары.

| Поле   | Тип     | Ограничения               | Описание                           |
| ------ | ------- | ------------------------- | ---------------------------------- |
| `id`   | INTEGER | PRIMARY KEY AUTOINCREMENT | Уникальный идентификатор категории |
| `name` | TEXT    | UNIQUE, NOT NULL          | Название категории                 |

**Пример:**
“Одежда”, “Электроника”, “Игрушки”

---

### 2. `products` — товары

Каждый товар принадлежит одной категории и имеет цену, количество на складе.

| Поле          | Тип     | Ограничения                                                            | Описание                        |
| ------------- | ------- | ---------------------------------------------------------------------- | ------------------------------- |
| `id`          | INTEGER | PRIMARY KEY AUTOINCREMENT                                              | Уникальный идентификатор товара |
| `name`        | TEXT    | UNIQUE, NOT NULL                                                       | Название товара                 |
| `price`       | REAL    | NOT NULL, CHECK(price >= 0)                                            | Цена                            |
| `quantity`    | INTEGER | NOT NULL, CHECK(quantity >= 0)                                         | Количество на складе            |
| `category_id` | INTEGER | FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL | Категория                       |

---

### 3. `orders` — заказы

Хранит информацию о заказанных товарах.

| Поле          | Тип     | Ограничения                                                     | Описание                        |
| ------------- | ------- | --------------------------------------------------------------- | ------------------------------- |
| `id`          | INTEGER | PRIMARY KEY AUTOINCREMENT                                       | Уникальный идентификатор заказа |
| `product_id`  | INTEGER | NOT NULL, FOREIGN KEY REFERENCES products(id) ON DELETE CASCADE | Заказанный товар                |
| `quantity`    | INTEGER | NOT NULL, CHECK(quantity > 0)                                   | Количество единиц товара        |
| `total_price` | REAL    | NOT NULL                                                        | Итоговая сумма заказа           |

---

## Этапы выполнения практики

### Этап 1. Создание структуры проекта

Создай проект с тремя основными файлами:

```
store_app/
│
├── core.py         # Работа с базой данных
├── crud.py         # CRUD-операции для каждой сущности
├── main.py         # Основная точка входа и интерфейс
```

> 💡 Подсказка:
> можно добавить при желании модуль `logic.py` для бизнес-операций (например, оформления заказа).

---

### Этап 2. Реализация класса для работы с БД (`core.py`)

Создай класс `Database`, который будет:

- устанавливать соединение с SQLite;
- выполнять SQL-запросы (`execute`, `fetchall`, `fetchone`);
- создавать таблицы при запуске приложения (метод `create_tables()`).

> 💡 Подсказка:
> для создания таблиц можно использовать метод `executescript()`, чтобы выполнить несколько SQL-запросов сразу.

---

### Этап 3. Реализация CRUD для каждой сущности (`crud.py`)

Для каждой таблицы создай отдельный класс:

- `CategoryCRUD`
- `ProductCRUD`
- `OrderCRUD`

Каждый класс должен иметь методы:

- `create()` — добавление новой записи;
- `get_all()` — получение списка всех записей;
- `get_by_id()` — получение записи по id;
- `update()` — обновление полей записи;
- `delete()` — удаление записи.

> 💡 Подсказка:
>
> - Используй параметризованные запросы (`?`) при вставке и обновлении.
> - После каждой операции изменения не забывай вызывать `commit()`.

---

### Этап 4. Реализация бизнес-логики — «оформление заказа»

Создай функцию `make_order(product_id, quantity)`, которая должна:

1. Проверить, что товар существует и нужное количество есть на складе.
2. Вычислить сумму заказа (`total_price = price * quantity`).
3. Добавить запись в таблицу `orders`.
4. Уменьшить количество товара в таблице `products`.

> 💡 Подсказка:
> Все действия нужно выполнять в одной транзакции — если что-то не получится, изменения должны откатиться.
> Для этого можно использовать `with connection:` или вручную управлять `commit()` / `rollback()`.

---

### Этап 5. Реализация интерфейса (`main.py`)

Создай простое консольное меню для взаимодействия с пользователем.
Например, в виде словаря:

```python
menu = {
    "1": ("Добавить товар", lambda: ...),
    "2": ("Показать товары", lambda: ...),
    "3": ("Создать заказ", lambda: ...),
    "4": ("Удалить товар", lambda: ...),
    "0": ("Выход", exit)
}
```

Функция `main()` должна:

- отображать пункты меню;
- принимать ввод пользователя;
- вызывать соответствующую функцию из словаря.

> **Подсказка**:
> Для вывода таблиц с результатами можно написать вспомогательную функцию `show_data(rows, headers)`, чтобы красиво печатать данные.

---

### Этап 6. Проверка CRUD-операций

1. Добавь несколько категорий (например: “Одежда”, “Электроника”).
2. Добавь несколько товаров в каждую категорию.
3. Попробуй изменить цену и количество у товара.
4. Удали товар и проверь, что каскадные ограничения работают корректно.
5. Создай несколько заказов через бизнес-функцию и убедись, что количество товара на складе уменьшается.

---

# Вопросы:

1. Что означает аббревиатура **CRUD** и какие операции в неё входят?
2. Какую роль играет **CRUD** в любом API-приложении?
3. В чём разница между **API** и **базой данных**?
4. Назови и кратко опиши четыре основных ограничения в SQL, которые помогают поддерживать целостность данных.
5. Что делает выражение `FOREIGN KEY (...) REFERENCES ... ON DELETE CASCADE`?
6. Какую задачу решает уровень **Repository (CRUD)** в структуре приложения?
7. Почему важно разделять логику приложения на уровни (DB → CRUD → Business Logic → Interface)?
8. Что произойдёт, если при вставке записи нарушить ограничение `UNIQUE` или `NOT NULL`?
9. Какую задачу решает **бизнес-логика** в CRUD-приложении? Например, почему перевод студента в другую группу не является простым `UPDATE`.
10. Что делает функция `executescript()` в `sqlite3` и когда её удобно использовать?

---

[Предыдущий урок](lesson09.md) | [Следующий урок](lesson11.md)
