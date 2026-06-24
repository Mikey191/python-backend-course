# Урок 8. Модели Django. Миграции

## Что мы уже знаем и что добавит Django

В прошлом курсе мы работали с базами данных напрямую: писали SQL-запросы, создавали таблицы через `CREATE TABLE`, подключались через `sqlite3`. Потом познакомились с SQLAlchemy — там уже появилась идея описывать структуру таблиц через Python-классы.

Django ORM работает по той же идее, но глубже интегрирован во фреймворк. Три главных отличия от того, что мы делали раньше:

- **Модель = таблица.** Python-класс описывает структуру таблицы. Django сам генерирует SQL и создаёт таблицу в базе.
- **Миграции.** Изменил класс — Django видит разницу и создаёт файл миграции, который обновит схему БД. Не нужно писать `ALTER TABLE` вручную.
- **ORM-запросы вместо SQL.** Вместо строк `SELECT * FROM films WHERE year > 2000` пишем `Film.objects.filter(year__gt=2000)`. SQL генерируется автоматически.

Сегодня разберём первые два пункта: как описывать модели и как работают миграции.

---

## Первая модель

Модель — это класс, унаследованный от `django.db.models.Model`. Каждый атрибут класса — это поле таблицы:

```python
# films/models.py
from django.db import models


class Film(models.Model):
    title = models.CharField(max_length=200)
    year = models.PositiveIntegerField()
    description = models.TextField(blank=True)
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.title} ({self.year})'
```

Разберём каждую строку.

### Поле id

Мы не объявили поле `id` — Django создаёт его автоматически для каждой модели:

```python
id = models.AutoField(primary_key=True)
```

Это целочисленный первичный ключ с автоинкрементом. Если нужен другой тип PK — можно переопределить, добавив `primary_key=True` к любому другому полю.

### Типы полей

Django предоставляет широкий набор типов полей. Основные, которые нам понадобятся в курсе:

| Поле | SQL-тип | Назначение |
|---|---|---|
| `CharField(max_length=N)` | `VARCHAR(N)` | Короткая строка — название, имя |
| `TextField()` | `TEXT` | Длинный текст — описание, биография |
| `IntegerField()` | `INTEGER` | Целое число |
| `PositiveIntegerField()` | `INTEGER` | Целое положительное число |
| `DecimalField(max_digits, decimal_places)` | `DECIMAL` | Число с фиксированной точностью — рейтинг, цена |
| `BooleanField()` | `BOOLEAN` | True/False |
| `DateField()` | `DATE` | Дата |
| `DateTimeField()` | `DATETIME` | Дата и время |
| `ImageField()` | `VARCHAR` | Путь к изображению (подробнее в модуле 5) |
| `SlugField()` | `VARCHAR` | URL-совместимая строка |

### Параметры полей

Параметры управляют поведением поля на уровне базы данных и на уровне валидации:

| Параметр | Значение по умолчанию | Что делает |
|---|---|---|
| `null=True` | `False` | Разрешает `NULL` в базе данных |
| `blank=True` | `False` | Разрешает пустое значение при валидации форм |
| `default=значение` | — | Значение по умолчанию |
| `unique=True` | `False` | Уникальность значения в колонке |
| `db_index=True` | `False` | Создать индекс для ускорения поиска |
| `verbose_name='...'` | имя поля | Человекочитаемое имя для админки |
| `choices=[(val, label)]` | — | Ограничить допустимые значения списком |

> **Частая путаница:** `null` и `blank` — разные вещи. `null=True` означает, что в базе данных поле может хранить значение `NULL`. `blank=True` означает, что при валидации Django-формы поле может быть пустым. Для строковых полей (`CharField`, `TextField`) принято использовать только `blank=True` — Django хранит пустую строку `''` вместо `NULL`. Для нестроковых (`IntegerField`, `DateField`) — `null=True, blank=True`.

### Метод __str__

`__str__` определяет строковое представление объекта — оно используется в административной панели, в оболочке Django и при отладке:

```python
def __str__(self):
    return f'{self.title} ({self.year})'
```

Без `__str__` в админке объекты будут отображаться как `Film object (1)` — малоинформативно.

### Класс Meta

Внутри модели можно определить вложенный класс `Meta` для дополнительных настроек:

```python
class Film(models.Model):
    title = models.CharField(max_length=200)
    year = models.PositiveIntegerField()
    ...

    class Meta:
        ordering = ['-year']          # сортировка по умолчанию: новые сначала
        verbose_name = 'Фильм'        # имя в единственном числе для админки
        verbose_name_plural = 'Фильмы' # имя во множественном числе
        db_table = 'films'            # имя таблицы в БД (по умолчанию — films_film)
```

`ordering` особенно полезен: один раз задал — и все QuerySet по умолчанию будут возвращать записи в этом порядке.

---

## Миграции

Модель описана, но таблицы в базе данных пока нет. Миграции — это механизм синхронизации Python-кода с реальной схемой базы данных.

> **Связь с прошлым курсом.** В модуле 4 прошлого курса мы работали с Alembic — это миграционный инструмент для SQLAlchemy. Django Migrations решает ту же задачу, но встроен в фреймворк и работает значительно проще: не нужно настраивать отдельный инструмент, всё управляется через `manage.py`.

### Две команды

Работа с миграциями всегда состоит из двух шагов:

```bash
# Шаг 1: Django анализирует модели и создаёт файл миграции
python manage.py makemigrations

# Шаг 2: Django выполняет файл миграции — создаёт/изменяет таблицы в БД
python manage.py migrate
```

Запустим первую команду:

```bash
python manage.py makemigrations
```

```
Migrations for 'films':
  films/migrations/0001_initial.py
    - Create model Film
```

Django создал файл `films/migrations/0001_initial.py`. Заглянем в него:

```python
# films/migrations/0001_initial.py
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Film',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=200)),
                ('year', models.PositiveIntegerField()),
                ('description', models.TextField(blank=True)),
                ('rating', models.DecimalField(decimal_places=1, default=0.0, max_digits=3)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Фильм',
                'verbose_name_plural': 'Фильмы',
                'ordering': ['-year'],
            },
        ),
    ]
```

Это обычный Python-файл, который описывает операции над схемой базы данных. Его не нужно редактировать вручную — Django генерирует и применяет его сам.

Теперь применяем миграцию:

```bash
python manage.py migrate
```

```
Operations to perform:
  Apply all migrations: admin, auth, contenttypes, films, sessions
Running migrations:
  Applying contenttypes.0001_initial... OK
  Applying auth.0001_initial... OK
  ...
  Applying films.0001_initial... OK
```

Django применил как наши миграции, так и миграции встроенных приложений — `admin`, `auth` и других. Это то самое предупреждение про `unapplied migrations`, которое мы видели при первом запуске сервера в уроке 1.

### Что хранится в таблице django_migrations

Django ведёт учёт применённых миграций в специальной таблице `django_migrations`. Благодаря этому повторный `migrate` не применит уже выполненные миграции:

```bash
python manage.py migrate
# No migrations to apply.
```

### Изменение модели

Добавим в модель новое поле — `slug` для красивых URL (понадобится в уроке 12):

```python
class Film(models.Model):
    title = models.CharField(max_length=200)
    year = models.PositiveIntegerField()
    description = models.TextField(blank=True)
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=0.0)
    slug = models.SlugField(max_length=200, unique=True, blank=True)  # новое поле
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-year']
        verbose_name = 'Фильм'
        verbose_name_plural = 'Фильмы'

    def __str__(self):
        return f'{self.title} ({self.year})'
```

Снова запускаем `makemigrations`:

```bash
python manage.py makemigrations
```

```
Migrations for 'films':
  films/migrations/0002_film_slug.py
    - Add field slug to film
```

Django видит разницу между текущим состоянием модели и последней применённой миграцией и создаёт новый файл — `0002_film_slug.py`. Применяем:

```bash
python manage.py migrate
```

### Полезные команды для работы с миграциями

```bash
# Показать статус всех миграций (применены или нет)
python manage.py showmigrations

# Показать SQL, который выполнит миграция (без применения)
python manage.py sqlmigrate films 0001

# Откатить миграции до указанного состояния
python manage.py migrate films 0001
```

`sqlmigrate` — особенно полезная команда. Она показывает реальный SQL, который Django собирается выполнить. Хороший способ проверить, что именно произойдёт с базой:

```bash
python manage.py sqlmigrate films 0001
```

```sql
BEGIN;
CREATE TABLE "films_film" (
    "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
    "title" varchar(200) NOT NULL,
    "year" integer unsigned NOT NULL,
    "description" text NOT NULL,
    "rating" decimal NOT NULL,
    "created_at" datetime NOT NULL
);
COMMIT;
```

---

## Подводные камни

### makemigrations ≠ migrate

Частая ошибка: добавил поле в модель, запустил сервер — и удивляется, почему ничего не изменилось. Цепочка всегда такая:

```
Изменил models.py
    → makemigrations (создаёт файл миграции)
    → migrate (применяет файл к БД)
```

Пропуск любого шага означает, что модель и база данных рассинхронизированы. Django не применяет изменения модели автоматически.

### Файлы миграций — часть кода

Папка `migrations/` должна быть в системе контроля версий (Git). Это не временные файлы. Они описывают историю схемы базы данных и нужны для воспроизводимого развёртывания на другом компьютере или сервере.

### Добавление поля без default в непустую таблицу

Если таблица уже содержит данные, а новое поле не имеет значения по умолчанию и не допускает `NULL` — Django спросит при `makemigrations`:

```
It is impossible to add a non-nullable field 'country' to film
without specifying a default.
Please select a fix:
 1) Provide a one-off default now
 2) Quit and manually define a default value in models.py
```

Выбор 1 позволяет ввести временное значение прямо в терминале. Выбор 2 — вернуться в код и добавить `default=`. В продакшне всегда лучше второй вариант: явный `default` в коде понятен и воспроизводим.

---

## Итоговая модель

```python
# films/models.py
from django.db import models


class Film(models.Model):
    title = models.CharField(max_length=200, verbose_name='Название')
    year = models.PositiveIntegerField(verbose_name='Год выпуска')
    description = models.TextField(blank=True, verbose_name='Описание')
    rating = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        default=0.0,
        verbose_name='Рейтинг'
    )
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата добавления')

    class Meta:
        ordering = ['-year']
        verbose_name = 'Фильм'
        verbose_name_plural = 'Фильмы'

    def __str__(self):
        return f'{self.title} ({self.year})'
```

---

## Вопросы

1. Чем Django Migrations отличается от Alembic, с которым мы работали в прошлом курсе?
2. В чём разница между `null=True` и `blank=True`? Можно ли использовать только один из них?
3. Что произойдёт, если изменить модель, но не запустить `makemigrations` и `migrate`?
4. Зачем нужна команда `sqlmigrate` и когда её полезно использовать?
5. Нужно ли коммитить папку `migrations/` в Git? Почему?

---

## Практическая задача

**Тип: расширь проект**

Модель `Film` создана. Теперь добавь в проект модель `Genre`.

**Требования:**

1. Создай модель `Genre` в `films/models.py` со следующими полями:
   - `name` — название жанра, строка до 100 символов, уникальное
   - `slug` — SlugField, уникальный, до 100 символов
2. Добавь `__str__`, возвращающий название жанра
3. В классе `Meta` задай сортировку по полю `name` и человекочитаемые имена: `'Жанр'` и `'Жанры'`
4. Создай и примени миграцию
5. Проверь через `sqlmigrate`, какой SQL сгенерировал Django для создания таблицы `Genre`

---

[Предыдущий урок](lesson07.md) | [Следующий урок](lesson09.md)