# Модуль 2. Урок 11. Flask + SQLite3 + HTML/CSS/JS.

## Как frontend и backend общаются между собой

Когда мы открываем сайт, нажимаем кнопку, заполняем форму или видим таблицу с данными — мы взаимодействуем с двумя важными частями приложения:
**клиентом (frontend)** и **сервером (backend)**.

Чтобы понять, как всё это работает, давай разберёмся с ключевыми понятиями, которые лежат в основе любого современного веб-приложения.

---

## 1. Что такое клиент и сервер

### Клиент

**Клиент** — это программа, которая отправляет запросы и отображает полученные результаты.
Обычно клиентом является **браузер**: Chrome, Firefox, Safari и т.д.
Когда пользователь открывает сайт, браузер выступает от его имени, посылая запросы серверу.

Пример:

Когда вы вводите в адресную строку `https://example.com`, ваш браузер отправляет **запрос на сервер** — "отдай мне эту страницу". Сервер отвечает — "вот HTML-файл, стили, скрипты".
Браузер получает эти файлы и показывает вам сайт.

### Сервер

**Сервер** — это программа, которая **принимает запросы от клиента и отправляет ответы**.
Сервер может быть написан на Python (Flask, Django), Node.js, Java, Go — неважно.
Главное, что он умеет слушать запросы и реагировать.

---

**Упрощённая схема:**

```
Пользователь → Браузер (клиент)
           ↓
       HTTP-запрос
           ↓
         Flask (сервер)
           ↓
       База данных (SQLite)
           ↓
       Ответ → Браузер
```

То есть клиент просит, сервер отвечает.
Клиент говорит: "Добавь новый предмет" или "Покажи список всех предметов",
а сервер выполняет действие и возвращает результат.

---

## 2. Что делает Flask

**Flask** — это лёгкий фреймворк для Python, который помогает создавать серверы.

**Он умеет**:

- **слушать входящие запросы** (например, `GET` и `POST`);
- **обрабатывать их** (например, сохранить данные в базу);
- **отправлять ответы клиенту**.

Можно сказать, `Flask` — это "секретарь", который принимает все входящие письма и передаёт их в нужный отдел, а потом возвращает ответ.

Пример (в общих чертах):

1. Клиент отправляет запрос на `/subjects`.
2. Flask принимает этот запрос.
3. Flask вызывает нужную функцию в коде Python.
4. Flask возвращает клиенту ответ (например, список предметов в виде JSON).

---

**Представь:**

- Flask — это мозг сервера.
- SQLite — это память.
- HTML/JS — это лицо и руки клиента.

---

## 3. Что такое HTTP-запросы

**HTTP (HyperText Transfer Protocol)** — это язык общения между клиентом и сервером.
Когда клиент хочет что-то сделать на сервере, он отправляет **HTTP-запрос**.

Основные типы запросов:

| Метод           | Назначение             | Пример                         |
| --------------- | ---------------------- | ------------------------------ |
| **GET**         | Получить данные        | Показать список всех предметов |
| **POST**        | Отправить новые данные | Добавить новый предмет         |
| **DELETE**      | Удалить данные         | Удалить предмет из списка      |
| **PUT / PATCH** | Изменить данные        | Переименовать предмет          |

Когда мы создаём форму на фронтенде, и она "отправляет" данные, — это **POST-запрос**.
Когда страница загружается и получает список данных — это **GET-запрос**.

---

**Пример общения:**

```
Клиент:  GET /subjects
Сервер:  [ "Математика", "История", "Информатика" ]

Клиент:  POST /subjects  { "name": "Физика" }
Сервер:  { "message": "Предмет добавлен" }
```

---

## 4. Что такое JSON

**JSON (JavaScript Object Notation)** — это способ хранить и передавать данные между клиентом и сервером.

Он очень похож на словари Python.

Пример JSON:

```json
{
  "name": "Математика",
  "hours": 120
}
```

Сервер может вернуть список предметов в JSON, а фронтенд (JavaScript) легко их обработает и покажет пользователю.
В Python такие данные превращаются в словари, в JavaScript — в объекты.

Почему это удобно:

- JSON лёгкий (только текст);
- одинаково понятен и для Python, и для JS;
- идеально подходит для обмена данными между frontend и backend.

---

**Пример потока:**

```
[HTML/JS] → POST JSON → [Flask] → SQLite
[Flask] → GET JSON → [JS] → визуализация
```

---

## 5. Как браузер общается с сервером

Когда вы нажимаете кнопку "Добавить", браузер делает следующее:

1. Формирует HTTP-запрос (например, `POST /api/subjects`).
2. Добавляет данные (в виде JSON).
3. Отправляет их на сервер.
4. Flask принимает запрос, сохраняет данные в базу.
5. Flask отправляет ответ (например, "добавлено успешно").
6. Браузер получает этот ответ и обновляет интерфейс (например, показывает новый предмет в списке).

---

**Схема взаимодействия:**

```
+-------------------------+
|  HTML + JS (клиент)     |
|-------------------------|
|  fetch('/api/subjects') |
+---------↓---------------+
          |
     Flask сервер
          |
     SQLite база
```

---

## Итог

- **Клиент** — отправляет запросы и показывает пользователю результат.
- **Сервер (Flask)** — принимает запросы, работает с базой данных, возвращает ответ.
- **HTTP** — язык общения между ними.
- **JSON** — формат, в котором передаются данные.
- **Браузер** — посредник, который визуализирует то, что приходит от сервера.

---

# Введение в backend-часть

## 1. Структура проекта (рекомендуемая)

```
backend/
├── app.py            # Flask приложение, маршруты API
├── core.py           # Database class — инициализация БД, execute и т.п.
├── repository.py     # StudentsRepository — CRUD для студентов
├── seed_info.py      # Скрипт для заполнения БД тестовыми данными
└── subjects.db       # (появится после init) SQLite-файл
```

---

## 2. Схема базы данных

- `groups`:

  - `id` INTEGER PRIMARY KEY AUTOINCREMENT
  - `name` TEXT NOT NULL UNIQUE

- `students`:

  - `id` INTEGER PRIMARY KEY AUTOINCREMENT
  - `name` TEXT NOT NULL
  - `phone` TEXT NULL
  - `group_id` INTEGER NULL — FK на `groups.id`
  - (возможно `created_at`, `updated_at` — опционально)

Связь: `students.group_id` → `groups.id`. Всё максимально просто и наглядно.

---

## 3. core.py — класс для работы с БД

**Задача**: инкапсулировать работу с `sqlite3`, создать БД/таблицы (init_db), дать универсальный `execute()` с несколькими режимами (fetchall, fetchone, execute/commit), и возвращать строки в виде dict (ключи — имена колонок).

```python
# core.py
import sqlite3
from typing import Any, List, Optional, Dict, Tuple

DB_FILE = "subjects.db"

class Database:
    def __init__(self, db_file: str = DB_FILE):
        self.db_file = db_file

    def init_db(self):
        """Создать таблицы, если их нет."""
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute("""
            CREATE TABLE IF NOT EXISTS groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            );
            """)
            cur.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT,
                group_id INTEGER,
                FOREIGN KEY(group_id) REFERENCES groups(id) ON DELETE SET NULL
            );
            """)
            conn.commit()

    def _get_conn(self):
        """Возвращает новое соединение. Используем sqlite3.Row для dict-подобных строк."""
        conn = sqlite3.connect(self.db_file, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def execute(self, sql: str, params: Optional[Tuple[Any, ...]] = None,
                fetchone: bool = False, fetchall: bool = False, commit: bool = False) -> Any:
        """
        Удобный универсальный метод для выполнения SQL.
        - sql: SQL строка с placeholders ?.
        - params: tuple параметров.
        - fetchone/fetchall: какой результат вернуть.
        - commit: делать ли commit (для INSERT/UPDATE/DELETE).

        Возвращает:
         - если fetchall: list[dict]
         - если fetchone: dict or None
         - иначе: cursor.lastrowid (если commit) или None
        """
        params = params or tuple()
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute(sql, params)
            result = None
            if commit:
                conn.commit()
                result = cur.lastrowid
            if fetchone:
                row = cur.fetchone()
                result = dict(row) if row else None
            if fetchall:
                rows = cur.fetchall()
                result = [dict(r) for r in rows]
            return result
```

**Пояснения:**

- `check_same_thread=False` — позволяет использовать соединение в разных потоках; мы создаём новое соединение в `_get_conn()` каждый раз, это безопасно.
- `row_factory = sqlite3.Row` + приведение в `dict(row)` — удобно возвращать JSON-серии.
- `execute()` универсален: используем флаги `fetchall`/`fetchone`/`commit`.

---

## 4. repository.py — `StudentsRepository` (CRUD для студентов)

**Задача**: обернуть SQL в методы высокого уровня (репозиторий), чтобы Flask-логику держать чистой.

```python
# repository.py
from typing import List, Optional, Dict, Any
from core import Database

class StudentsRepository:
    def __init__(self, db: Database):
        self.db = db

    def get_all(self) -> List[Dict[str, Any]]:
        sql = """
        SELECT s.id, s.name, s.phone, s.group_id, g.name as group_name
        FROM students s
        LEFT JOIN groups g ON s.group_id = g.id
        ORDER BY s.id;
        """
        return self.db.execute(sql, fetchall=True)

    def get_by_id(self, student_id: int) -> Optional[Dict[str, Any]]:
        sql = """
        SELECT s.id, s.name, s.phone, s.group_id, g.name as group_name
        FROM students s
        LEFT JOIN groups g ON s.group_id = g.id
        WHERE s.id = ?;
        """
        return self.db.execute(sql, params=(student_id,), fetchone=True)

    def create(self, name: str, phone: Optional[str] = None, group_id: Optional[int] = None) -> int:
        sql = "INSERT INTO students (name, phone, group_id) VALUES (?, ?, ?);"
        lastrowid = self.db.execute(sql, params=(name, phone, group_id), commit=True)
        return lastrowid

    def update(self, student_id: int, data: Dict[str, Any]) -> bool:
        # data может содержать name, phone, group_id
        fields = []
        params = []
        for key in ('name', 'phone', 'group_id'):
            if key in data:
                fields.append(f"{key} = ?")
                params.append(data[key])
        if not fields:
            return False
        params.append(student_id)
        sql = f"UPDATE students SET {', '.join(fields)} WHERE id = ?;"
        self.db.execute(sql, params=tuple(params), commit=True)
        return True

    def delete(self, student_id: int) -> bool:
        sql = "DELETE FROM students WHERE id = ?;"
        self.db.execute(sql, params=(student_id,), commit=True)
        return True
```

**Пояснения:**

- `get_all()` возвращает список студентов с именем группы (`group_name`) — полезно для фронтенда.
- `create()` возвращает `lastrowid`, что удобно при создании.
- `update()` строит динамический SET из переданных полей.
- `delete()` — простой.

---

## 5. seed_info.py — наполнение тестовыми данными

Нужен для быстрого заполнения БД примерами. Если установлен `faker`, используем его; иначе — несколько хардкод-примеров.

```python
# seed_info.py
from core import Database

try:
    from faker import Faker
    fake = Faker()
except Exception:
    fake = None

def seed(db: Database, groups_count: int = 3, students_per_group: int = 4):
    db.init_db()
    # Добавляем группы (если уже есть — IGNORE)
    groups = []
    for i in range(groups_count):
        name = fake.bs().title() if fake else f"Group {i+1}"
        try:
            db.execute("INSERT INTO groups (name) VALUES (?);", params=(name,), commit=True)
        except Exception:
            pass
    # Получим все группы
    groups = db.execute("SELECT id, name FROM groups;", fetchall=True)
    if not groups:
        # если по каким-то причинам группы не создались — создадим базовые
        for i in range(3):
            db.execute("INSERT INTO groups (name) VALUES (?);", params=(f"Group {i+1}",), commit=True)
        groups = db.execute("SELECT id, name FROM groups;", fetchall=True)

    # Добавляем студентов
    for g in groups:
        for j in range(students_per_group):
            name = fake.name() if fake else f"Student {g['id']}-{j+1}"
            phone = fake.phone_number() if fake else None
            db.execute("INSERT INTO students (name, phone, group_id) VALUES (?, ?, ?);",
                       params=(name, phone, g['id']), commit=True)

if __name__ == "__main__":
    db = Database()
    seed(db)
    print("Seed completed.")
```

**Инструкция:** чтобы использовать faker, `pip install faker`. Но сидер работает и без него.

---

## 6. app.py — Flask приложение и маршруты

Важные концепции перед кодом:

- **Flask** — маршрутизатор: связывает URL и функцию (view).
- Для API мы принимаем и возвращаем JSON.
- **Методы**: `GET`, `POST`, `PUT`, `DELETE` соответствуют CRUD.
- Мы должны возвращать корректные HTTP-коды: `200 OK`, `201 Created`, `404 Not Found`, `400 Bad Request`, `204 No Content` и т.п.
- Для фронтенда, который будет работать из другого origin, нужен **CORS**. Рекомендация: `pip install flask-cors` и использовать `CORS(app)`.

Пример кода:

```python
# app.py
from flask import Flask, jsonify, request, abort
from flask_cors import CORS
from core import Database
from repository import StudentsRepository

app = Flask(__name__)
CORS(app)  # Разрешаем CORS, удобно при разработке фронтенда локально

db = Database()
db.init_db()
students_repo = StudentsRepository(db)

@app.route("/students", methods=["GET"])
def list_students():
    students = students_repo.get_all()
    return jsonify(students), 200

@app.route("/students", methods=["POST"])
def create_student():
    if not request.is_json:
        return jsonify({"error": "Expected JSON"}), 400
    data = request.get_json()
    name = data.get("name")
    if not name:
        return jsonify({"error": "Field 'name' is required"}), 400
    phone = data.get("phone")
    group_id = data.get("group_id")
    new_id = students_repo.create(name=name, phone=phone, group_id=group_id)
    student = students_repo.get_by_id(new_id)
    return jsonify(student), 201

@app.route("/students/<int:student_id>", methods=["GET"])
def get_student(student_id):
    student = students_repo.get_by_id(student_id)
    if not student:
        return jsonify({"error": "Not Found"}), 404
    return jsonify(student), 200

@app.route("/students/<int:student_id>", methods=["PUT", "POST"])
def update_student(student_id):
    if not request.is_json:
        return jsonify({"error": "Expected JSON"}), 400
    data = request.get_json()
    updated = students_repo.update(student_id, data)
    if not updated:
        return jsonify({"error": "No fields to update or student not found"}), 400
    student = students_repo.get_by_id(student_id)
    if not student:
        return jsonify({"error": "Not Found"}), 404
    return jsonify(student), 200

@app.route("/students/<int:student_id>", methods=["DELETE"])
def delete_student(student_id):
    student = students_repo.get_by_id(student_id)
    if not student:
        return jsonify({"error": "Not Found"}), 404
    students_repo.delete(student_id)
    return '', 204  # No Content

if __name__ == "__main__":
    app.run(debug=True)
```

**Примечания:**

- Возвращаемые объекты — JSON словари/списки: удобно для фронтенда.
- При удалении возвращаем `204 No Content`.

---

## 7. Примеры запросов (curl)

- Получить список:

```bash
curl http://127.0.0.1:5000/students
```

- Создать студента:

```bash
curl -X POST http://127.0.0.1:5000/students \
  -H "Content-Type: application/json" \
  -d '{"name": "Иван Иванов", "phone": "+7-999-111-22-33", "group_id": 1}'
```

- Получить одного:

```bash
curl http://127.0.0.1:5000/students/1
```

- Обновить:

```bash
curl -X PUT http://127.0.0.1:5000/students/1 \
  -H "Content-Type: application/json" \
  -d '{"phone":"12345"}'
```

- Удалить:

```bash
curl -X DELETE http://127.0.0.1:5000/students/1
```

---

## 8. Советы по запуску и зависимостям

1. Создайте виртуальное окружение:

```bash
python -m venv venv
source venv/bin/activate   # Unix
venv\Scripts\activate      # Windows
```

2. Установите нужные пакеты:

```bash
pip install flask flask-cors
# необязательно: pip install faker
```

3. Запустите сидер (опционально):

```bash
python seed_info.py
```

4. Запустите приложение:

```bash
python app.py
```

---

Отлично!
Теперь мы переходим к завершающему этапу нашего проекта — **созданию фронтенд-части**, которая будет взаимодействовать с Flask-бэкендом через HTTP-запросы.
Эта часть позволит наглядно увидеть, **как браузер (frontend) общается с сервером (backend)**, как передаются данные и как отображаются результаты на экране.

---

# Введение в frontend-часть

## 1. Зачем нам нужен CORS (Cross-Origin Resource Sharing)

Когда мы запускаем **Flask-сервер** на одном порту (например `http://127.0.0.1:5000`), а **фронтенд-страницу** открываем через **Live Server** (например `http://127.0.0.1:5500`), браузер воспринимает это как **разные источники (origin)**.

> Origin = Протокол + Домен + Порт
> Пример:
> `http://127.0.0.1:5000` ≠ `http://127.0.0.1:5500`

По умолчанию браузер **блокирует такие запросы** ради безопасности (механизм называется _Same-Origin Policy_).

Чтобы разрешить браузеру выполнять запросы между этими источниками, нужно подключить **CORS (Cross-Origin Resource Sharing)**.
Flask предоставляет простое решение с помощью расширения `flask-cors`.

### Подключаем CORS:

В файле `app.py`:

```python
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Разрешаем фронтенду делать запросы
```

Теперь наш браузер сможет спокойно отправлять запросы с фронта на наш Flask-сервер.

---

## 2. Почему мы используем `Live Server`

Когда вы открываете HTML-файл двойным кликом (`file:///C:/.../index.html`), страница не запускается как настоящий веб-сайт.
У неё **нет сервера**, а значит — нельзя делать сетевые запросы, потому что JavaScript не знает, к какому источнику они относятся.

**Live Server** (расширение для VSCode) решает эту проблему:

- Запускает встроенный мини-сервер на вашем компьютере (например `http://127.0.0.1:5500`).
- Позволяет работать с JS-запросами.
- Автоматически обновляет страницу при изменениях.

> 💡 Иными словами, Live Server превращает вашу локальную папку с HTML и JS в «мини-веб-сайт».

---

## 3. Как фронтенд общается с Flask через HTTP-запросы

Теперь создадим структуру для фронтенда:

```
frontend/
│
├── index.html
├── style.css
└── script.js
```

---

## 4. index.html — структура интерфейса

Создадим простой, но понятный интерфейс с несколькими зонами:

- Просмотр всех студентов
- Добавление нового студента
- Поиск одного студента
- Управление каждым студентом (изменение, удаление)

```html
<!DOCTYPE html>
<html lang="ru">
  <head>
    <meta charset="UTF-8" />
    <title>Управление студентами</title>
    <link rel="stylesheet" href="style.css" />
  </head>
  <body>
    <h1>📚 Управление студентами</h1>

    <section id="all-students">
      <h2>Все студенты</h2>
      <button id="load-students">Загрузить студентов</button>
      <div id="students-list"></div>
    </section>

    <section id="add-student">
      <h2>Добавить нового студента</h2>
      <form id="add-form">
        <input type="text" id="new-name" placeholder="Имя" required />
        <input type="text" id="new-phone" placeholder="Телефон" required />
        <input type="number" id="new-group" placeholder="ID группы" required />
        <button type="submit">Добавить</button>
      </form>
      <p id="add-message"></p>
    </section>

    <section id="one-student">
      <h2>Найти студента по ID</h2>
      <input type="number" id="student-id" placeholder="Введите ID" />
      <button id="find-student">Найти</button>
      <div id="student-info"></div>
    </section>

    <script src="script.js"></script>
  </body>
</html>
```

---

## 5. style.css — базовая стилизация

Чтобы интерфейс выглядел симпатично, добавим минимальную стилизацию:

```css
body {
  font-family: Arial, sans-serif;
  margin: 20px auto;
  max-width: 800px;
  background: #f7f9fc;
  color: #333;
}

h1 {
  text-align: center;
  color: #2c3e50;
}

section {
  background: white;
  border-radius: 10px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
  padding: 20px;
  margin-bottom: 20px;
}

button {
  background: #3498db;
  color: white;
  border: none;
  padding: 8px 12px;
  border-radius: 6px;
  cursor: pointer;
}

button:hover {
  background: #2980b9;
}

input {
  margin: 5px;
  padding: 6px;
  border: 1px solid #ccc;
  border-radius: 4px;
}

.student-item {
  background: #eef6ff;
  border-radius: 8px;
  padding: 10px;
  margin: 8px 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
```

---

## 6. script.js — логика взаимодействия

Теперь добавим JavaScript-код, который:

- будет отправлять запросы к Flask-бэкенду;
- получать и отображать данные;
- создавать и удалять студентов;
- редактировать данные без перезагрузки страницы.

```javascript
const API_URL = "http://127.0.0.1:5000/students";

// ===== ЗАГРУЗИТЬ ВСЕХ СТУДЕНТОВ =====
document.getElementById("load-students").addEventListener("click", async () => {
  const response = await fetch(API_URL);
  const students = await response.json();
  const container = document.getElementById("students-list");
  container.innerHTML = "";

  students.forEach((student) => {
    const div = document.createElement("div");
    div.className = "student-item";
    div.innerHTML = `
      <span><b>${student.id}</b>. ${student.name} — ${student.phone} (Группа ${student.group_id})</span>
      <div>
        <button onclick="editStudent(${student.id})">✏️</button>
        <button onclick="deleteStudent(${student.id})">🗑️</button>
      </div>
    `;
    container.appendChild(div);
  });
});

// ===== УДАЛЕНИЕ СТУДЕНТА =====
async function deleteStudent(id) {
  if (!confirm("Удалить этого студента?")) return;
  await fetch(`${API_URL}/${id}`, { method: "DELETE" });
  alert("Студент удалён");
}

// ===== ДОБАВИТЬ НОВОГО СТУДЕНТА =====
document.getElementById("add-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const name = document.getElementById("new-name").value;
  const phone = document.getElementById("new-phone").value;
  const group_id = document.getElementById("new-group").value;

  const response = await fetch(API_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, phone, group_id }),
  });

  const data = await response.json();
  document.getElementById("add-message").innerText = data.message || "Ошибка";
});

// ===== ПОИСК ОДНОГО СТУДЕНТА =====
document.getElementById("find-student").addEventListener("click", async () => {
  const id = document.getElementById("student-id").value;
  const response = await fetch(`${API_URL}/${id}`);
  const student = await response.json();
  const info = document.getElementById("student-info");
  info.innerHTML = `<p>${student.name} (${student.phone}), Группа ${student.group_id}</p>`;
});

// ===== РЕДАКТИРОВАНИЕ СТУДЕНТА =====
async function editStudent(id) {
  const container = document.getElementById("students-list");
  const form = document.createElement("div");
  form.innerHTML = `
    <input type="text" id="edit-name-${id}" placeholder="Новое имя">
    <input type="text" id="edit-phone-${id}" placeholder="Новый телефон">
    <button onclick="saveEdit(${id})">💾 Сохранить</button>
  `;
  container.appendChild(form);
}

async function saveEdit(id) {
  const name = document.getElementById(`edit-name-${id}`).value;
  const phone = document.getElementById(`edit-phone-${id}`).value;
  await fetch(`${API_URL}/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, phone }),
  });
  alert("Изменения сохранены!");
}
```

---

## 7. Итог

- **CORS** — разрешает фронтенду делать запросы к другому серверу.
- **Live Server** — локальный сервер, на котором мы запускаем наш фронтенд.
- **fetch()** — инструмент JavaScript для работы с HTTP-запросами.
- **DOM-манипуляции** — мы динамически создаём и изменяем HTML-элементы через JS.
- **Интеграция фронта и бэка** — браузер отправляет запрос → Flask получает → обращается к SQLite → возвращает ответ → JS показывает его на странице.

---

# Запуск всего проекта и подведение итогов:

## **1. Запуск backend**

Перейди в папку `backend/` и запусти сервер Flask:

```bash
python app.py
```

После запуска ты должен увидеть сообщение:

```
 * Running on http://127.0.0.1:5000
```

Это означает, что твой сервер успешно работает и слушает запросы от клиента (фронтенда).
Теперь можешь проверить: открой в браузере [http://127.0.0.1:5000/students](http://127.0.0.1:5000/students)
— и ты должен увидеть JSON-список студентов.

---

## **2. Запуск frontend**

Перейди в папку `frontend/` и открой файл `index.html` **через Live Server** (в VS Code).
Для этого:

- нажми правой кнопкой на `index.html`;
- выбери пункт **“Open with Live Server”**.

В браузере откроется адрес вроде:

```
http://127.0.0.1:5500/frontend/index.html
```

Теперь обе части работают:

- **Flask** — на `http://127.0.0.1:5000`;
- **Frontend** — на `http://127.0.0.1:5500`.

---

## 3. Как работает взаимодействие фронта и бэка

1. **Пользователь нажимает кнопку** “Загрузить студентов”.
2. **JavaScript** вызывает функцию, которая делает `fetch()` запрос на адрес `http://127.0.0.1:5000/users`.
3. **Flask** получает этот запрос, обрабатывает его в маршруте `/users`, делает запрос к базе данных через `repository.py`, и возвращает **JSON-ответ**.
4. **JS получает ответ**, преобразует JSON в объект, создаёт новые HTML-элементы и **динамически добавляет** их на страницу.
5. При нажатии на кнопки ✏️ или 🗑️ выполняются POST/PUT/DELETE-запросы — и изменения сразу сохраняются в БД.

Таким образом, мы построили **реальный цикл взаимодействия браузера с сервером**:

> Клиент (фронт) → HTTP-запрос → Сервер (Flask) → SQLite → JSON-ответ → Отображение на странице.

---

## 4. Что мы узнали

Сегодня ты познакомился с ключевыми концепциями современного web-разработчика:

1. **Клиент–серверная архитектура** — как браузер общается с сервером.
2. **Flask** — лёгкий фреймворк для создания REST API.
3. **HTTP-запросы (GET, POST, PUT, DELETE)** — основные методы взаимодействия клиента и сервера.
4. **JSON** — универсальный формат передачи данных.
5. **CORS** — механизм, который позволяет фронтенду и бэкенду работать с разных портов.
6. **Live Server** — мини-сервер для тестирования фронтенда.
7. **JavaScript fetch()** — инструмент для отправки HTTP-запросов и работы с ответами.
8. **Работа с DOM** — как динамически создавать и обновлять HTML через JS.
9. **Интеграция фронта и бэка** — как объединить всё в один работающий проект.

---

## Вопросы

1. Что такое клиент и сервер? В чём их отличие?
2. Зачем нужен Flask и какие задачи он решает?
3. Что такое HTTP-запрос? Чем GET отличается от POST?
4. Почему мы используем JSON в обмене данными между фронтом и бэком?
5. Что делает механизм CORS и зачем он нужен?
6. Почему нельзя просто открыть HTML-файл напрямую через `file:///` для теста запросов?
7. Что делает метод `fetch()` в JavaScript?
8. В каком случае браузер выдаёт ошибку `Unexpected token '<'` при работе с JSON?
9. Как JavaScript создаёт и добавляет новые элементы на страницу?
10. Что произойдёт, если сервер Flask не запущен, но фронтенд попытается сделать запрос?

---

## Домашнее задание

### **Задание: реализовать похожий функционал для групп**

1. В файле `repository.py` добавь класс `GroupsRepository`, в котором реализуй методы:

   - получения всех групп,
   - создания новой группы,
   - получения одной группы по ID,
   - удаления группы.

2. Добавь в `app.py` маршруты:

   ```python
   /groups (GET, POST)
   /groups/<int:id> (GET, DELETE)
   ```

3. На фронтенде:

   - Создай новый блок для работы с группами (по аналогии с блоком студентов).
   - Добавь возможность добавления и удаления групп.

4. Добавь отображение студентов вместе с их группами в формате:

   ```text
   Группа 1:
     - Иван Иванов
     - Пётр Петров
     - Анна Смирнова

   Группа 2:
     - Алексей Сидоров
     - Ольга Кузнецова
   ```

   > Для этого можно сначала запросить все группы, затем для каждой группы — получить студентов, и с помощью JavaScript сгенерировать блоки `<div>` с заголовками и списками.

---

[Предыдущий урок](lesson10.md)

---

[К списку курсов](../README.md)
