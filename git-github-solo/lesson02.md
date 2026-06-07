# Урок 2. GitHub: работа с нескольких компьютеров

## Введение

В прошлом уроке Боб научился работать с Git локально. Вся история проекта хранится на его рабочем компьютере, цикл `dev → test → main` работает хорошо.

Но сегодня вечером Боб уходит домой — и хочет продолжить работу там. Копировать проект на флешку? Отправить себе архив по почте? Оба варианта плохие: история коммитов потеряется, ветки не сохранятся, и уже завтра непонятно какая версия актуальная.

Решение — **GitHub**. Это облачный сервис, который хранит Git-репозиторий в интернете. Теперь история проекта живёт не только на одном компьютере, а на удалённом сервере — и доступна с любой машины.

> **Git и GitHub — это разные вещи.** Git — программа на твоём компьютере. GitHub — сайт в интернете, который хранит репозитории. Есть и другие похожие сервисы: GitLab, Bitbucket — принцип тот же.

---

## Регистрация на GitHub

Переходи на [github.com](https://github.com) и регистрируйся. После регистрации у тебя будет аккаунт — например, `github.com/bob`.

---

## SSH-ключи: как компьютер «представляется» GitHub

Когда Боб отправляет изменения на GitHub, сервис должен убедиться что это действительно Боб, а не кто-то другой. Для этого используются **SSH-ключи**.

SSH-ключ — это пара файлов:
- **Приватный ключ** — хранится только на твоём компьютере, никому не показываешь
- **Публичный ключ** — добавляешь на GitHub

Когда ты подключаешься к GitHub, он проверяет: есть ли у тебя приватный ключ, который соответствует публичному? Если да — ты прошёл аутентификацию.

### Что такое SSH и зачем он нужен?

GitHub должен понимать, кто именно пытается отправить изменения в репозиторий. Для этого необходимо пройти аутентификацию — подтвердить свою личность.

Существует два основных способа аутентификации при работе с удалёнными репозиториями:

* **HTTPS**
* **SSH**

### HTTPS

При использовании HTTPS адрес репозитория выглядит так:

```text
https://github.com/user/project.git
```

GitHub проверяет пользователя с помощью специального токена доступа (Personal Access Token, PAT).

Раньше использовались обычные пароли, но сейчас GitHub требует использовать токены.

### SSH

При использовании SSH адрес репозитория выглядит так:

```text
git@github.com:user/project.git
```

Вместо токена используются специальные криптографические ключи.

Пользователь один раз создаёт пару ключей:

* приватный ключ остаётся на компьютере;
* публичный ключ добавляется в настройки GitHub.

После этого GitHub сможет автоматически подтверждать личность пользователя без ввода токена при каждой операции.

---

> *SSH и HTTPS не меняют работу Git и не влияют на репозиторий. Они отличаются только способом подключения и аутентификации между вашим компьютером и сервером GitHub. Все команды Git (`clone`, `pull`, `push`, `fetch`) работают одинаково в обоих случаях. Различается лишь адрес удалённого репозитория и механизм подтверждения личности пользователя.*

### Шаг 1. Проверить, есть ли уже ключи

```bash
ls ~/.ssh
```

Если видишь файлы `id_rsa` и `id_rsa.pub` (или `id_ed25519` и `id_ed25519.pub`) — ключи уже есть, можно пропустить генерацию.

#### Что находится в папке ~/.ssh?

Папка:

```text
~/.ssh
```

является стандартным местом хранения настроек и ключей SSH.

Если SSH уже использовался на компьютере ранее, в ней могут находиться файлы:

```text
~/.ssh/
├── id_ed25519
├── id_ed25519.pub
├── known_hosts
```

**id_ed25519**

Приватный ключ.

Этот файл используется для подтверждения вашей личности при подключении к удалённым сервисам.

Никогда не передавайте этот файл другим людям и не загружайте его в репозитории.

**id_ed25519.pub**

Публичный ключ.

Этот файл можно безопасно отправлять на GitHub, GitLab и другие сервисы.

Именно его мы будем добавлять в настройки GitHub.

**known_hosts**

Список серверов, к которым компьютер уже подключался через SSH.

Этот файл помогает SSH обнаруживать попытки подмены удалённого сервера.

Если файлов `id_ed25519` и `id_ed25519.pub` нет, значит SSH-ключи ещё не создавались и их необходимо сгенерировать.

---

### Шаг 2. Сгенерировать новый ключ

```bash
ssh-keygen -t ed25519 -C "bob@example.com"
```

Терминал задаст вопросы:

```
Enter file in which to save the key (~/.ssh/id_ed25519): 
```
Нажми Enter — сохранится в папку по умолчанию.

```
Enter passphrase (empty for no passphrase):
```
Можно оставить пустым (просто Enter). Passphrase добавляет дополнительную защиту, но тогда нужно вводить пароль при каждом подключении.

**Разберём команду по частям**:

```bash
ssh-keygen -t ed25519 -C "bob@example.com"
```

`ssh-keygen`: Утилита для создания SSH-ключей. Она генерирует криптографическую пару ключей: приватный ключ и публичный ключ.

`-t ed25519`: Параметр `-t` задаёт тип ключа. В данном случае используется алгоритм `ed25519`. Это современный алгоритм, который рекомендуется использовать для SSH. Существуют и другие алгоритмы, однако для новых проектов обычно рекомендуется именно `ed25519`.

`-C "bob@example.com"`: Параметр `-C` означает комментарий (comment). Он не участвует в шифровании и нужен только для удобства идентификации ключа. Комментарий будет отображаться в конце публичного ключа.

После успешной генерации обычно появляются два файла:

```text
id_ed25519
id_ed25519.pub
```

Это одна ключевая пара:

| Файл           | Назначение     |
| -------------- | -------------- |
| id_ed25519     | Приватный ключ |
| id_ed25519.pub | Публичный ключ |

*Приватный ключ остаётся только на компьютере пользователя.*

*Публичный ключ можно передавать сервисам, которым необходимо подтверждать вашу личность.*

### Шаг 3. Скопировать публичный ключ

**Mac / Linux / Git Bash на Windows:**

```bash
cat ~/.ssh/id_ed25519.pub
```

Скопируй весь вывод — это и есть публичный ключ. Выглядит примерно так:

```
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAI... bob@example.com
```

**Windows (альтернативный способ):**

```bash
clip < ~/.ssh/id_ed25519.pub
```

Ключ сразу скопируется в буфер обмена.

### Шаг 4. Добавить ключ на GitHub

1. Открой [github.com/settings/keys](https://github.com/settings/keys)
2. Нажми **New SSH key**
3. В поле **Title** напиши что-то понятное: `Work laptop` или `MacBook Bob`
4. В поле **Key** вставь скопированный публичный ключ
5. Нажми **Add SSH key**

### Шаг 5. Проверить подключение

```bash
ssh -T git@github.com
```

Если всё настроено правильно:

```
Hi bob! You've successfully authenticated, but GitHub does not provide shell access.
```

> **Почему SSH, а не HTTPS?** GitHub поддерживает оба варианта. HTTPS проще настроить, но требует вводить токен при каждой операции (или хранить его в менеджере паролей). SSH настраивается один раз и потом работает без лишних действий.

---

## Создаём репозиторий на GitHub

Боб заходит на GitHub и создаёт новый репозиторий:

1. Нажимает **New repository** (кнопка `+` в правом верхнем углу)
2. Название: `tasks-api`
3. Описание: `Simple REST API for task management`
4. Видимость: **Private** — пока проект только для Боба
5. **Важно:** галочки "Add README", "Add .gitignore", "Choose a license" — **не ставить**. У нас уже есть локальный репозиторий с историей, лишние файлы создадут конфликт
6. Нажимает **Create repository**

GitHub показывает страницу с инструкциями. Нам нужна секция **"…or push an existing repository from the command line"**.

---

## Подключаем локальный репозиторий к GitHub

Боб возвращается в терминал. Он находится в папке проекта `tasks-api`.

### git remote — связываем репозитории

```bash
git remote add origin git@github.com:bob/tasks-api.git
```

Разберём команду:
- `git remote add` — добавить удалённый репозиторий
- `origin` — стандартное имя для основного удалённого репозитория (просто соглашение, можно назвать иначе)
- `git@github.com:bob/tasks-api.git` — SSH-адрес репозитория на GitHub

Проверяем:

```bash
git remote -v
```

```
origin  git@github.com:bob/tasks-api.git (fetch)
origin  git@github.com:bob/tasks-api.git (push)
```

Хорошо. Локальный репозиторий знает куда отправлять изменения.

### git push — отправляем историю на GitHub

```bash
git push -u origin main
```

```
Enumerating objects: 12, done.
Counting objects: 100% (12/12), done.
Delta compression using up to 8 threads
Compressing objects: 100% (8/8), done.
Writing objects: 100% (12/12), 1.24 KiB | 1.24 MiB/s, done.
Total 12 (delta 1), reused 0 (delta 0), pack-reused 0
To git@github.com:bob/tasks-api.git
 * [new branch]      main -> main
branch 'main' set up to track remote branch 'main' from 'origin'.
```

Флаг `-u` (upstream) — устанавливает связь между локальной веткой и удалённой. После этого первого `push` с флагом `-u`, в дальнейшем достаточно писать просто `git push`.

Теперь отправим остальные ветки:

```bash
git push -u origin dev
git push -u origin test
```

Открываем GitHub — репозиторий там, со всеми коммитами и ветками.

---

## Боб идёт домой

Рабочий день закончен. Боб выключает рабочий компьютер и едет домой.

Дома у него другой компьютер. Git установлен. SSH-ключ для домашнего компьютера нужно настроить отдельно — точно так же как мы делали выше, только в конце назвать ключ как-нибудь понятно: `Home desktop`.

> **Каждый компьютер — свой SSH-ключ.** На GitHub можно добавить сколько угодно ключей. Это нормально и правильно: если потеряешь ноутбук, удалишь только его ключ — остальные продолжат работать.

### git clone — клонируем репозиторий

На домашнем компьютере проекта ещё нет. Боб клонирует его с GitHub:

```bash
cd ~/Documents
git clone git@github.com:bob/tasks-api.git
cd tasks-api
```

`git clone` скачивает весь репозиторий: все файлы, все коммиты, все ветки.

Проверим:

```bash
git log --oneline
```

```
f2c9a84 (HEAD -> main, origin/main, origin/dev, origin/test) feat: add filtering by done status in GET /tasks
e4a1c03 feat: add GET /tasks/{id} endpoint
c8b3d72 feat: add PUT and DELETE endpoints for tasks
b7d2e91 feat: add Task model and basic CRUD endpoints
a3f8c12 init: project setup with requirements and gitignore
```

Вся история здесь. Но есть нюанс: `git clone` автоматически создаёт только ветку `main` как локальную. Ветки `dev` и `test` существуют как удалённые (`origin/dev`, `origin/test`), но локально их нет.

Создаём локальные ветки, связанные с удалёнными:

```bash
git checkout -b dev origin/dev
git checkout -b test origin/test
```

```
branch 'dev' set up to track remote branch 'dev' from 'origin'.
Switched to a new branch 'dev'
```

Теперь всё готово. Боб переключается на `dev` и продолжает работу:

```bash
git checkout dev
```

---

## Работа дома: новый цикл dev → test → main

Боб решает добавить поиск задачи по названию. Он уже в ветке `dev`.

Обновляет `app/main.py` — добавляет параметр `search` в GET /tasks:

```python
@app.get("/tasks")
def get_tasks(done: Optional[bool] = None, search: Optional[str] = None):
    result = tasks

    if done is not None:
        result = [task for task in result if task.done == done]

    if search is not None:
        result = [task for task in result if search.lower() in task.title.lower()]

    return result
```

```bash
git add app/main.py
git commit -m "feat: add search by title in GET /tasks"
```

Отправляет ветку `dev` на GitHub:

```bash
git push
```

```
Enumerating objects: 5, done.
...
To git@github.com:bob/tasks-api.git
   f2c9a84..a91e3c7  dev -> dev
```

Проверяет — переносит в `test`, затем в `main`:

```bash
git checkout test
git merge dev
git push

git checkout main
git merge test
git push
```

Всё. Домашний компьютер отправил изменения на GitHub. Завтра рабочий компьютер сможет их получить.

---

## Утро: возвращаемся на работу

Боб приходит на работу. Первое что нужно сделать — **получить изменения с GitHub**, которые он делал дома.

### git pull — получаем изменения

```bash
git checkout dev
git pull
```

```
remote: Enumerating objects: 5, done.
remote: Counting objects: 100% (5/5), done.
...
Updating f2c9a84..a91e3c7
Fast-forward
 app/main.py | 6 +++++-
 1 file changed, 5 insertions(+), 1 deletion(-)
```

`git pull` делает две вещи сразу:
1. Скачивает новые коммиты с GitHub (`git fetch`)
2. Применяет их к текущей ветке (`git merge`)

Обновляем остальные ветки:

```bash
git checkout test
git pull

git checkout main
git pull

git checkout dev
```

Хорошая привычка — делать `git pull` в начале каждого рабочего дня и перед тем как начинаешь новую задачу.

---

## Конфликт: что бывает когда забыл сделать pull

Боб — человек. Однажды он забывает сделать `git pull` перед началом работы.

Вот как это происходит:

**Вечером дома** Боб меняет `app/models.py` — добавляет поле `priority`:

```python
class Task(BaseModel):
    id: Optional[int] = None
    title: str
    description: Optional[str] = None
    done: bool = False
    priority: int = 0  # 0 - обычная, 1 - важная, 2 - срочная
```

```bash
git add app/models.py
git commit -m "feat: add priority field to Task model"
git checkout test && git merge dev && git push
git checkout main && git merge test && git push
git checkout dev && git push
```

**Утром на работе** Боб садится за компьютер. Забывает сделать `git pull`. Открывает `app/models.py` и тоже редактирует его — добавляет поле `due_date`:

```python
class Task(BaseModel):
    id: Optional[int] = None
    title: str
    description: Optional[str] = None
    done: bool = False
    due_date: Optional[str] = None  # Срок выполнения
```

```bash
git add app/models.py
git commit -m "feat: add due_date field to Task model"
```

Теперь Боб пытается отправить изменения:

```bash
git push
```

```
To git@github.com:bob/tasks-api.git
 ! [rejected]        dev -> dev (non-fast-forward)
error: failed to push some refs to 'git@github.com:bob/tasks-api.git'
hint: Updates were rejected because the remote contains work that you do
hint: not have locally. Integrate the remote changes (e.g.
hint: 'git pull ...') before pushing again.
```

Git отказывает. Причина: на GitHub в ветке `dev` есть коммит (`priority`), которого нет на рабочем компьютере. Если бы Git просто перезаписал — домашний коммит потерялся бы.

### Решаем конфликт

Боб делает `git pull`:

```bash
git pull
```

```
Auto-merging app/models.py
CONFLICT (content): Merge conflict in app/models.py
Automatic merge failed; fix conflicts then commit the result.
```

Git не смог объединить изменения автоматически — оба коммита меняли одну и ту же строку в одном файле. Это **конфликт**.

Открываем `app/models.py` — там маркеры конфликта:

```python
class Task(BaseModel):
    id: Optional[int] = None
    title: str
    description: Optional[str] = None
    done: bool = False
<<<<<<< HEAD
    due_date: Optional[str] = None  # Срок выполнения
=======
    priority: int = 0  # 0 - обычная, 1 - важная, 2 - срочная
>>>>>>> origin/dev
```

Читаем маркеры:
- `<<<<<<< HEAD` — твои локальные изменения (рабочий компьютер)
- `=======` — разделитель
- `>>>>>>> origin/dev` — изменения с GitHub (домашний компьютер)

Боб хочет оставить **оба поля** — они не противоречат друг другу. Редактирует файл вручную, удаляя маркеры:

```python
class Task(BaseModel):
    id: Optional[int] = None
    title: str
    description: Optional[str] = None
    done: bool = False
    due_date: Optional[str] = None  # Срок выполнения
    priority: int = 0  # 0 - обычная, 1 - важная, 2 - срочная
```

Сохраняет файл. Добавляет в staging и завершает merge:

```bash
git add app/models.py
git commit -m "merge: combine due_date and priority fields in Task model"
```

```
[dev 3d8f1a2] merge: combine due_date and priority fields in Task model
```

Теперь можно отправить:

```bash
git push
```

```
To git@github.com:bob/tasks-api.git
   a91e3c7..3d8f1a2  dev -> dev
```

Конфликт разрешён. История сохранена.

### Как избежать конфликтов

Конфликт произошёл потому что Боб редактировал один и тот же файл на двух компьютерах без синхронизации. Простое правило:

> **Первое действие в начале работы — `git pull`.**

Выработай привычку: открыл проект → сделал `git pull`. Большинство конфликтов исчезнет само собой.

---

## Итоговый рабочий процесс Боба

После двух уроков у Боба сложился чёткий ритм. Вот как выглядит его рабочий день:

### Начало работы (любой компьютер)

```bash
git checkout dev
git pull
```

### В процессе разработки

```bash
# Пишешь код...

git add .
git commit -m "feat: описание что сделал"

# Пишешь ещё...

git add .
git commit -m "fix: описание что исправил"
```

### Когда задача готова

```bash
# Переносим в test
git checkout test
git pull
git merge dev
git push

# Проверяем, запускаем проект, смотрим что всё работает

# Переносим в main
git checkout main
git pull
git merge test
git push

# Возвращаемся в dev для следующей задачи
git checkout dev
git push
```

### Конец дня (перед тем как закрыть компьютер)

Убедись что все коммиты отправлены:

```bash
git status
git push
```

---

## Полезные команды для работы с GitHub

| Команда | Что делает |
|---------|-----------|
| `git remote add origin URL` | Подключить удалённый репозиторий |
| `git remote -v` | Посмотреть подключённые репозитории |
| `git push` | Отправить коммиты на GitHub |
| `git push -u origin ветка` | Первый push новой ветки |
| `git pull` | Получить и применить изменения с GitHub |
| `git fetch` | Только скачать изменения, не применять |
| `git clone URL` | Клонировать репозиторий |
| `git status` | Проверить состояние (в т.ч. отставание от remote) |

### git fetch vs git pull

`git pull` = `git fetch` + `git merge`. 

Иногда полезно использовать `git fetch` отдельно — чтобы посмотреть что изменилось на GitHub, прежде чем применять изменения:

```bash
git fetch
git log HEAD..origin/dev --oneline   # что есть на GitHub, но нет локально
git pull                              # теперь применяем
```

---

## Итог урока

Боб подключил проект к GitHub и научился работать с нескольких компьютеров:

1. Сгенерировал SSH-ключи на каждом компьютере и добавил их на GitHub
2. Создал удалённый репозиторий и отправил туда локальную историю
3. Склонировал проект на домашний компьютер и продолжил работу
4. Освоил цикл `dev → test → main` с `push` и `pull` на каждом шаге
5. Попал в конфликт — и разрешил его вручную
6. Выработал привычку начинать день с `git pull`

---

## Что дальше

Пока Боб работает один. Но проект растёт, и он задумывается: а что если подключить к работе ещё одного разработчика? Или отдать часть задач на аутсорс?

В следующем уроке разберём как устроена командная работа на GitHub: защита веток, Pull Request, и как открыть доступ к репозиторию для другого человека.

---

[Предыдущий урок](lesson01.md) | [Следующий урок](lesson03.md)