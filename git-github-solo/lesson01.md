# Урок 1. Git: локальная работа с проектом

## Введение

Представь ситуацию: ты пишешь проект несколько недель. В какой-то момент добавляешь новую функцию — и что-то ломается. Ты не помнишь что именно менял. Откатиться некуда. Резервной копии нет.

Именно для таких ситуаций существует **Git** — система контроля версий. Она запоминает каждое изменение в проекте: что изменилось, когда и зачем. В любой момент можно вернуться к рабочей версии, посмотреть историю изменений или работать над несколькими задачами параллельно — не боясь сломать то, что уже работает.

В этом уроке мы познакомимся с Git на примере **Боба** — разработчика, который начинает новый проект и хочет с самого начала организовать работу правильно.

---

## Что такое Git

Git — это программа, которая работает локально на твоём компьютере и отслеживает изменения в файлах проекта.

Несколько ключевых моментов:

- Git не требует интернета для базовой работы — всё хранится на твоём компьютере
- Git работает с любыми текстовыми файлами: Python, SQL, Markdown, конфиги
- Git не следит за бинарными файлами (картинки, видео, `.exe`) — для этого есть другие инструменты
- Git не занимается синхронизацией между компьютерами сам по себе — для этого используют GitHub (рассмотрим в следующем уроке)

---

## Установка Git

### Windows

1. Перейди на [git-scm.com](https://git-scm.com) и скачай установщик
2. Запусти установщик. На вопросе про редактор по умолчанию выбери **Nano** или **VS Code** — с Vim новичку будет сложно
3. Все остальные настройки оставь по умолчанию
4. После установки откроется программа **Git Bash** — это терминал, в котором мы будем работать

> **Важно для Windows:** мы будем работать в **Git Bash**, а не в стандартном `cmd` или PowerShell. Git Bash понимает Unix-команды и работает одинаково на Windows и Mac.

### Mac

На Mac Git часто уже установлен. Проверь:

```bash
git --version
```

Если Git не установлен, Mac предложит установить Command Line Tools — соглашайся. Либо установи через Homebrew:

```bash
brew install git
```

### Проверка установки

После установки открой терминал (Git Bash на Windows, Terminal на Mac) и выполни:

```bash
git --version
```

Ты должен увидеть что-то вроде:

```
git version 2.43.0
```

---

## Базовые команды терминала

Git управляется через терминал. Прежде чем идти дальше — несколько команд, без которых не обойтись:

| Команда | Что делает |
|---------|-----------|
| `pwd` | Показывает текущую папку (где ты сейчас находишься) |
| `ls` | Список файлов в текущей папке |
| `cd название_папки` | Войти в папку |
| `cd ..` | Выйти на уровень выше |
| `mkdir название` | Создать новую папку |

> **Windows (cmd/PowerShell):** вместо `ls` используй `dir`. В Git Bash работает и `ls`.

Пример навигации:

```bash
pwd
# /Users/bob

cd Documents
pwd
# /Users/bob/Documents

mkdir tasks-api
cd tasks-api
pwd
# /Users/bob/Documents/tasks-api
```

Эти команды нужны только для навигации. Всё остальное — уже Git.

---

## Настройка Git

Перед первым использованием Git нужно представиться — указать имя и email. Эти данные будут записываться в каждый коммит.

```bash
git config --global user.name "Bob"
git config --global user.email "bob@example.com"
```

Проверить настройки:

```bash
git config --list
```

Флаг `--global` означает что настройка применится ко всем проектам на этом компьютере. Сделать это нужно один раз.

---

## Проект Боба

Боб — Python-разработчик. Он хочет написать простой REST API для управления задачами. Проект небольшой: одна сущность `Task`, четыре маршрута. Боб уже работал с FastAPI, поэтому выбор фреймворка очевиден.

Боб понимает: проект будет развиваться. Он хочет с самого начала работать правильно — чтобы в истории коммитов было видно как проект рос, а не один коммит «всё сразу».

### Структура проекта

```
tasks-api/
├── app/
│   ├── __init__.py
│   ├── main.py
│   └── models.py
├── .gitignore
├── README.md
└── requirements.txt
```

---

## git init — начало истории

Боб создаёт папку проекта и инициализирует Git-репозиторий:

```bash
mkdir tasks-api
cd tasks-api
git init
```

Вывод:

```
Initialized empty Git repository in /Users/bob/Documents/tasks-api/.git/
```

Git создал скрытую папку `.git` — именно в ней хранится вся история проекта. Трогать её вручную не нужно.

Проверим статус:

```bash
git status
```

```
On branch main
No commits yet
nothing to commit (create/copy files and start working)
```

Репозиторий создан, но он пустой. Пора добавлять файлы.

---

## Первые файлы: .gitignore и requirements.txt

Боб не начинает сразу с кода. Сначала — файлы конфигурации. Это хорошая практика.

### .gitignore

`.gitignore` — файл, который говорит Git какие файлы **не нужно** отслеживать. В Python-проектах это:

- `__pycache__/` — кэш байткода Python
- `.venv/` или `venv/` — виртуальное окружение (у каждого разработчика своё)
- `.env` — файл с секретами (пароли, API-ключи)
- `.DS_Store` — служебный файл macOS
- `*.pyc` — скомпилированные файлы Python

Боб создаёт файл `.gitignore`:

```
# Python
__pycache__/
*.py[cod]
*.pyo
.venv/
venv/
env/

# Переменные окружения
.env
.env.local

# IDE
.vscode/
.idea/

# macOS
.DS_Store

# Логи
*.log
```

> **Почему .gitignore важен:** если случайно закоммитить `.env` с паролями и отправить на GitHub — это утечка данных. `.gitignore` защищает от таких ошибок.

### requirements.txt

```
fastapi==0.110.0
uvicorn==0.27.1
```

### Проверяем статус

```bash
git status
```

```
On branch main

No commits yet

Untracked files:
  (use "git add <file>..." to include in what will be committed)
        .gitignore
        requirements.txt

nothing added to commit but untracked files present (use "git add" to include in what will be committed)
```

Git видит новые файлы, но ещё не отслеживает их. Они в статусе `Untracked`.

---

## Как работает Git: три состояния

Прежде чем делать первый коммит — важно понять модель Git:

```
Рабочая директория  →  Staging area  →  История (репозиторий)
  (твои файлы)          (git add)         (git commit)
```

**Рабочая директория** — обычные файлы на диске. Ты их редактируешь.

**Staging area (индекс)** — промежуточная зона. Сюда ты добавляешь файлы командой `git add`, говоря Git: «эти изменения войдут в следующий коммит».

**История** — коммит зафиксирован командой `git commit`. Теперь это часть истории, к которой можно вернуться.

Зачем нужен staging area? Представь: ты за день изменил 10 файлов. Пять из них — новая функция, пять — исправление бага. Staging area позволяет сделать **два отдельных коммита** из одного дня работы — история будет чистой и понятной.

---

## git add и git commit — первый коммит

Боб добавляет файлы в staging area:

```bash
git add .gitignore
git add requirements.txt
```

Или всё сразу:

```bash
git add .
```

Проверяем:

```bash
git status
```

```
On branch main

No commits yet

Changes to be committed:
  (use "git rm --cached <file>..." to unstage)
        new file:   .gitignore
        new file:   requirements.txt
```

Теперь делаем коммит:

```bash
git commit -m "init: project setup with requirements and gitignore"
```

```
[main (root-commit) a3f8c12] init: project setup with requirements and gitignore
 2 files changed, 20 insertions(+)
 create mode 100644 .gitignore
 create mode 100644 requirements.txt
```

Первый коммит сделан. `a3f8c12` — это уникальный идентификатор коммита (хеш).

### Правила хороших коммит-сообщений

Коммит-сообщение — это запись в дневнике проекта. Через месяц ты скажешь спасибо себе за понятные сообщения.

Распространённый формат — **Conventional Commits**:

```
тип: краткое описание что сделано
```

| Тип | Когда использовать |
|-----|-------------------|
| `init` | Инициализация проекта |
| `feat` | Новая функция |
| `fix` | Исправление бага |
| `refactor` | Рефакторинг без изменения поведения |
| `docs` | Изменения в документации |
| `chore` | Обслуживание: обновление зависимостей, конфиги |

Примеры хороших сообщений:
```
feat: add GET /tasks endpoint
fix: handle empty task list response
docs: update README with API examples
```

Примеры плохих сообщений:
```
fix
changes
wip
asdfgh
```

---

## Пишем код проекта

Теперь Боб начинает писать сам проект. Он создаёт структуру папок:

```bash
mkdir app
```

### app/\_\_init\_\_.py

Пустой файл — нужен чтобы Python воспринимал папку как модуль:

```python
```

### app/models.py

```python
from pydantic import BaseModel
from typing import Optional


class Task(BaseModel):
    id: Optional[int] = None
    title: str
    description: Optional[str] = None
    done: bool = False
```

### app/main.py

```python
from fastapi import FastAPI, HTTPException
from app.models import Task

app = FastAPI()

# Временное хранилище задач (в памяти)
tasks: list[Task] = []
task_counter = 0


@app.get("/tasks")
def get_tasks():
    return tasks


@app.post("/tasks", status_code=201)
def create_task(task: Task):
    global task_counter
    task_counter += 1
    task.id = task_counter
    tasks.append(task)
    return task
```

### README.md

```markdown
# Tasks API

Простой REST API для управления задачами.

## Запуск

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Эндпоинты

- `GET /tasks` — список всех задач
- `POST /tasks` — создать задачу
```

Проверяем статус:

```bash
git status
```

```
On branch main
Untracked files:
  (use "git add <file>..." to include in what will be committed)
        README.md
        app/
```

Добавляем и коммитим:

```bash
git add .
git commit -m "feat: add Task model and basic CRUD endpoints"
```

---

## git log — смотрим историю

```bash
git log
```

```
commit b7d2e91 (HEAD -> main)
Author: Bob <bob@example.com>
Date:   Mon Jun 1 10:34:21 2026 +0300

    feat: add Task model and basic CRUD endpoints

commit a3f8c12
Author: Bob <bob@example.com>
Date:   Mon Jun 1 10:15:04 2026 +0300

    init: project setup with requirements and gitignore
```

Более компактный вывод:

```bash
git log --oneline
```

```
b7d2e91 (HEAD -> main) feat: add Task model and basic CRUD endpoints
a3f8c12 init: project setup with requirements and gitignore
```

`HEAD` — указатель на текущий коммит. Сейчас мы на ветке `main`, на последнем коммите.

---

## Ветки: зачем они нужны

Пока Боб работал прямо в ветке `main`. Для первоначальной настройки это нормально. Но теперь он хочет добавить новые эндпоинты — и делать это в `main` рискованно: если что-то сломается, `main` окажется в нерабочем состоянии.

Решение — **ветки**.

Ветка — это независимая линия разработки. Изменения в одной ветке не влияют на другие ветки, пока ты сам их не объединишь (merge).

### Модель веток Боба

Боб решает работать по следующей схеме:

```
main        ← стабильный код. Сюда попадает только проверенное
  ↑
test        ← тестирование перед выходом в main
  ↑
dev         ← активная разработка. Здесь Боб пишет новый код
```

Логика работы:
1. Пишешь новый код в `dev`
2. Переносишь в `test`, проверяешь что ничего не сломалось
3. Если всё хорошо — переносишь в `main`

Это называется **упрощённый Git Flow**. Он хорошо работает и для одного разработчика, и для небольшой команды.

---

## Создаём ветки

```bash
git branch dev
git branch test
```

Смотрим список веток:

```bash
git branch
```

```
  dev
* main
  test
```

Звёздочка `*` показывает текущую ветку. Боб всё ещё на `main`.

Переключаемся на `dev`:

```bash
git checkout dev
```

```
Switched to branch 'dev'
```

> **Современный способ:** вместо `git checkout` можно использовать `git switch dev` — команда появилась в Git 2.23 и делает то же самое, но с более понятным названием. В этом уроке используем `git checkout` — он встречается чаще в документации и примерах.

Создать ветку и сразу переключиться на неё можно одной командой:

```bash
git checkout -b feature/new-branch
```

---

## Работа в ветке dev

Боб в ветке `dev`. Теперь он добавляет новые эндпоинты — PUT и DELETE.

Обновляет `app/main.py`:

```python
from fastapi import FastAPI, HTTPException
from app.models import Task

app = FastAPI()

tasks: list[Task] = []
task_counter = 0


@app.get("/tasks")
def get_tasks():
    return tasks


@app.post("/tasks", status_code=201)
def create_task(task: Task):
    global task_counter
    task_counter += 1
    task.id = task_counter
    tasks.append(task)
    return task


@app.put("/tasks/{task_id}")
def update_task(task_id: int, updated: Task):
    for i, task in enumerate(tasks):
        if task.id == task_id:
            updated.id = task_id
            tasks[i] = updated
            return updated
    raise HTTPException(status_code=404, detail="Task not found")


@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    for i, task in enumerate(tasks):
        if task.id == task_id:
            tasks.pop(i)
            return
    raise HTTPException(status_code=404, detail="Task not found")
```

Коммитим:

```bash
git add app/main.py
git commit -m "feat: add PUT and DELETE endpoints for tasks"
```

Добавляет ещё один эндпоинт — получить задачу по ID:

```python
@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    for task in tasks:
        if task.id == task_id:
            return task
    raise HTTPException(status_code=404, detail="Task not found")
```

```bash
git add app/main.py
git commit -m "feat: add GET /tasks/{id} endpoint"
```

Смотрим историю в ветке `dev`:

```bash
git log --oneline
```

```
e4a1c03 (HEAD -> dev) feat: add GET /tasks/{id} endpoint
c8b3d72 feat: add PUT and DELETE endpoints for tasks
b7d2e91 (main, test) feat: add Task model and basic CRUD endpoints
a3f8c12 init: project setup with requirements and gitignore
```

Видно что `dev` ушла вперёд на 2 коммита. `main` и `test` пока на месте.

---

## git diff — смотрим изменения

Перед тем как переносить изменения, полезно посмотреть что именно изменилось.

Разница между текущей веткой и другой веткой:

```bash
git diff main
```

Разница между двумя конкретными ветками:

```bash
git diff main dev
```

Разница между staged изменениями и последним коммитом:

```bash
git diff --staged
```

---

## Переносим изменения в test

Боб доволен: оба коммита выглядят хорошо, код написан. Теперь он переключается на `test` и переносит туда изменения из `dev`:

```bash
git checkout test
git merge dev
```

```
Updating b7d2e91..e4a1c03
Fast-forward
 app/main.py | 22 ++++++++++++++++++++++
 1 file changed, 22 insertions(+)
```

`Fast-forward` означает: ветка `test` просто «догнала» `dev` — конфликтов нет, история линейная.

Проверяем:

```bash
git log --oneline
```

```
e4a1c03 (HEAD -> test, dev) feat: add GET /tasks/{id} endpoint
c8b3d72 feat: add PUT and DELETE endpoints for tasks
b7d2e91 (main) feat: add Task model and basic CRUD endpoints
a3f8c12 init: project setup with requirements and gitignore
```

Теперь `test` и `dev` смотрят на один и тот же коммит.

Боб запускает проект и проверяет что все эндпоинты работают:

```bash
uvicorn app.main:app --reload
```

Всё работает. Можно переносить в `main`.

---

## Переносим изменения в main

```bash
git checkout main
git merge test
```

```
Updating b7d2e91..e4a1c03
Fast-forward
 app/main.py | 22 ++++++++++++++++++++++
 1 file changed, 22 insertions(+)
```

Итоговая история:

```bash
git log --oneline
```

```
e4a1c03 (HEAD -> main, test, dev) feat: add GET /tasks/{id} endpoint
c8b3d72 feat: add PUT and DELETE endpoints for tasks
b7d2e91 feat: add Task model and basic CRUD endpoints
a3f8c12 init: project setup with requirements and gitignore
```

Все три ветки теперь на одном коммите. `main` содержит стабильный, проверенный код.

---

## Второй цикл разработки

Боб видит что хочет добавить фильтрацию задач по статусу. Он снова переключается на `dev` — главная ветка не трогается.

```bash
git checkout dev
```

Обновляет `app/main.py` — добавляет параметр `done` в GET /tasks:

```python
@app.get("/tasks")
def get_tasks(done: Optional[bool] = None):
    if done is None:
        return tasks
    return [task for task in tasks if task.done == done]
```

Добавляет импорт `Optional` из `typing` в начало файла (уже есть в models.py, но нужен и в main.py):

```python
from typing import Optional
```

```bash
git add app/main.py
git commit -m "feat: add filtering by done status in GET /tasks"
```

И снова цикл: `dev` → `test` → `main`:

```bash
git checkout test
git merge dev

# Проверяем, запускаем, всё работает

git checkout main
git merge test
```

```bash
git log --oneline
```

```
f2c9a84 (HEAD -> main, test, dev) feat: add filtering by done status in GET /tasks
e4a1c03 feat: add GET /tasks/{id} endpoint
c8b3d72 feat: add PUT and DELETE endpoints for tasks
b7d2e91 feat: add Task model and basic CRUD endpoints
a3f8c12 init: project setup with requirements and gitignore
```

Это и есть ритм работы Боба: новый код → dev → test → main. Цикл повторяется.

---

## Что делать если что-то пошло не так

### Отменить изменения в рабочей директории

Если ты изменил файл, но ещё не делал `git add`, и хочешь вернуть его к состоянию последнего коммита:

```bash
git checkout -- app/main.py
```

> **Осторожно:** эта команда безвозвратно удаляет несохранённые изменения.

### Убрать файл из staging area

Если сделал `git add`, но передумал включать файл в коммит:

```bash
git restore --staged app/main.py
```

### Посмотреть что было в прошлом коммите

```bash
git show a3f8c12
```

Или по относительной позиции (предыдущий коммит):

```bash
git show HEAD~1
```

### Вернуться к старому коммиту (безопасный способ)

Если хочешь посмотреть как выглядел проект в определённый момент — не удаляя новые коммиты:

```bash
git checkout a3f8c12
```

Чтобы вернуться обратно:

```bash
git checkout main
```

---

## Итог урока

Боб прошёл полный цикл локальной работы с Git:

1. Инициализировал репозиторий (`git init`)
2. Настроил `.gitignore` и `requirements.txt`
3. Делал осмысленные коммиты с понятными сообщениями
4. Создал три ветки: `main`, `test`, `dev`
5. Работал в `dev`, тестировал в `test`, фиксировал стабильный код в `main`
6. Повторил цикл несколько раз

### Команды урока

| Команда | Что делает |
|---------|-----------|
| `git init` | Инициализировать репозиторий |
| `git status` | Текущее состояние |
| `git add .` | Добавить все изменения в staging |
| `git add файл` | Добавить конкретный файл |
| `git commit -m "сообщение"` | Зафиксировать изменения |
| `git log` | История коммитов |
| `git log --oneline` | Краткая история |
| `git diff` | Посмотреть изменения |
| `git branch` | Список веток |
| `git branch имя` | Создать ветку |
| `git checkout имя` | Переключиться на ветку |
| `git checkout -b имя` | Создать ветку и переключиться |
| `git merge имя` | Влить ветку в текущую |
| `git show хеш` | Посмотреть коммит |

---

## Что дальше

Всё что мы делали — хранится только на компьютере Боба. Если компьютер сломается — история исчезнет. Кроме того, Боб хочет продолжать работу дома.

В следующем уроке мы подключим **GitHub** — удалённый репозиторий, который хранит историю проекта в облаке и позволяет работать с нескольких компьютеров.

---

[Следующий урок](lesson02.md)