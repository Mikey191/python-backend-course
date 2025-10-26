# Модуль 3. Урок 14. Что такое БД, SQL и ORM. Создание первой модели

В предыдущих уроках мы работали с шаблонами и HTML-страницами. Теперь настало время сделать наш сайт «живым» — добавить в него данные.
В реальном проекте фильмы, жанры, пользователи и рецензии хранятся не в коде, а в базе данных. Django умеет работать с базами очень удобно — с помощью технологии **ORM**.

---

## 1. Что такое база данных (БД)

**База данных** — это место, где хранятся структурированные данные: списки фильмов, пользователей, комментариев, жанров и т. д.

Например, если бы мы хранили данные о фильмах вручную, это выглядело бы примерно так:

| id  | Название      | Год  | Рейтинг | Жанр       |
| --- | ------------- | ---- | ------- | ---------- |
| 1   | 1+1           | 2011 | 8.9     | Драма      |
| 2   | Матрица       | 1999 | 8.5     | Фантастика |
| 3   | Крестный отец | 1972 | 8.6     | Криминал   |

В Django за хранение таких данных отвечает **СУБД (система управления базами данных)**.

По умолчанию используется простая и быстрая база — **SQLite**, которая хранится прямо в файле проекта (`db.sqlite3`).

---

## 2. SQL и ORM — в чём разница?

Чтобы работать с базой данных напрямую, нужно знать язык **SQL** — специальный язык запросов.

Например, чтобы выбрать все фильмы, написали бы:

```sql
SELECT * FROM movies;
```

Но Django предлагает более удобный способ — **ORM (Object Relational Mapping)**.

С помощью **ORM** мы обращаемся к базе не через SQL, а через Python-код:

```python
Movie.objects.all()
```

Под капотом ORM сам переведёт этот вызов в SQL-запрос, выполнит его и вернёт результат в виде объектов Python.

Так мы получаем мощь SQL, но в привычной и безопасной форме.

---

## 3. Проверяем настройки базы данных

Открой файл `settings.py` и найди раздел `DATABASES`:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

Здесь указано, что **Django будет использовать SQLite**.

Позже мы сможем заменить её, например, на PostgreSQL — и при этом **весь код останется тем же**.

Это одно из главных преимуществ ORM.

---

## 4. Создаём первую модель

**Модель** — это класс Python, который описывает структуру таблицы в базе данных.

Например, в нашем проекте **cinemahub** создадим модель `Movie`, чтобы хранить информацию о фильмах.

Открой файл `movies/models.py` и добавь следующий код:

```python
from django.db import models

class Movie(models.Model):
    title = models.CharField(max_length=255, verbose_name="Название")
    description = models.TextField(blank=True, verbose_name="Описание")
    year = models.IntegerField(verbose_name="Год выпуска")
    rating = models.FloatField(verbose_name="Рейтинг")
    time_create = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    time_update = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    is_published = models.BooleanField(default=True, verbose_name="Опубликовано")

    def __str__(self):
        return self.title
```

---

## 5. Разбор полей модели

- **`title`** — название фильма. Ограничение в 255 символов.
- **`description`** — описание фильма, может быть пустым (`blank=True`).
- **`year`** — год выхода фильма (целое число).
- **`rating`** — оценка фильма с плавающей точкой.
- **`time_create`** — дата и время создания записи (добавляется автоматически).
- **`time_update`** — дата последнего изменения.
- **`is_published`** — булево поле: опубликован фильм или нет.
- **`__str__`** — метод, который задаёт, как объект будет отображаться в интерфейсе (например, в админке).

---

## 6. Применяем модель: миграции

Django не создаёт таблицы в базе данных автоматически.

Чтобы модель появилась в SQLite, нужно создать и применить **миграции**:

```bash
python manage.py makemigrations
python manage.py migrate
```

Первая команда создаёт файл с описанием изменений, а вторая — применяет их к базе.

После выполнения этих команд появится таблица `movies_movie` с нужными полями.

---

## 7. Проверяем работу модели

Чтобы убедиться, что всё работает, запусти сервер:

```bash
python manage.py runserver
```

Теперь открой **Django shell** — интерактивную консоль для работы с ORM:

```bash
python manage.py shell
```

Попробуй создать первый фильм:

```python
from movies.models import Movie
m = Movie(title="1+1", year=2011, rating=8.9, description="Душевная история дружбы")
m.save()
```

Проверим, что фильм добавился:

```python
Movie.objects.all()
```

Ты должен увидеть что-то вроде:

```
<QuerySet [<Movie: 1+1>]>
```

Поздравляю — ты только что создал первую запись в базе данных через ORM Django!

---

## 8. Проверяем через браузер

1. Перейди в `/admin/` (если у тебя уже есть суперпользователь).
2. Зарегистрируй модель в `movies/admin.py`:

   ```python
   from django.contrib import admin
   from .models import Movie

   admin.site.register(Movie)
   ```

3. Обнови страницу — ты увидишь новую секцию **Movies**.
4. Добавь несколько фильмов и убедись, что они сохраняются в базу.
5. Если осталась старая модель Movie в файле `views.py`, ее нужно закомментировать или удалить.

---

## 9. Выводим фильмы на страницу

Чтобы убедиться, что данные работают и через шаблоны, изменим представление `index` в `movies/views.py`:

```python
from django.shortcuts import render
from .models import Movie

def index(request):
    movies = Movie.objects.all()
    return render(request, 'movies/index.html', {"movies": movies})
```

Теперь в шаблоне `movies/index.html` можно вывести фильмы:

```django
<h2>Список фильмов</h2>
<ul>
  {% for m in movies %}
    <li>{{ m.title }} ({{ m.year }}) — рейтинг: {{ m.rating }}</li>
  {% empty %}
    <li>Пока фильмов нет 😢</li>
  {% endfor %}
</ul>
```

Перезагрузи страницу — и ты увидишь список фильмов, хранящихся в базе данных!

---

## 10. Типы полей в Django ORM

Django предоставляет богатый набор типов полей, которые позволяют гибко описывать любые данные.

### 1. Числовые поля

Используются для хранения числовых значений:

- `IntegerField()` — обычное целое число.
- `PositiveIntegerField()` — только положительные значения.
- `BigIntegerField()` — большое целое число (например, для счётчиков просмотров).
- `FloatField()` — число с плавающей точкой, например, рейтинг фильма.
- `DecimalField(max_digits=10, decimal_places=2)` — десятичное число с фиксированной точностью (удобно для цен и бюджетов).

💡 _Пример:_

```python
rating = models.FloatField(default=0)
budget = models.DecimalField(max_digits=12, decimal_places=2)
```

---

### 2. Поля для дат и времени

- `DateField()` — дата без времени (например, дата премьеры).
- `TimeField()` — время без даты.
- `DateTimeField()` — дата и время вместе.

Дополнительные параметры:

- `auto_now_add=True` — значение устанавливается при создании записи.
- `auto_now=True` — обновляется при каждом сохранении.

💡 _Пример:_

```python
release_date = models.DateField()
time_create = models.DateTimeField(auto_now_add=True)
```

---

### 3. Логические поля

- `BooleanField()` — принимает `True` или `False`.
- `BooleanField(null=True)` — допускает значение `None`.

💡 _Пример:_

```python
is_published = models.BooleanField(default=True)
```

---

### 4. Поля для связей между моделями

Используются, чтобы соединять данные разных таблиц:

- `ForeignKey(Model, on_delete=models.CASCADE)` — связь «один ко многим». Например, один жанр — много фильмов.
- `OneToOneField(Model, on_delete=models.CASCADE)` — связь «один к одному». Например, фильм и его расширенная карточка.
- `ManyToManyField(Model)` — связь «многие ко многим». Например, фильм и актёры.

💡 _Пример:_

```python
genre = models.ForeignKey('Genre', on_delete=models.CASCADE)
actors = models.ManyToManyField('Actor')
```

---

### 5. Поля для файлов и изображений

- `FileField(upload_to='uploads/')` — позволяет загружать файлы.
- `ImageField(upload_to='images/')` — используется для изображений (требует Pillow).

💡 _Пример:_

```python
poster = models.ImageField(upload_to='posters/')
```

---

### 6. JSON-поле

Позволяет хранить данные в формате JSON (список, словарь и т.п.):

```python
extra_info = models.JSONField(default=dict)
```

Полезно для гибких структур, например, хранения дополнительной информации о фильме.

---

### 7. Специальные и уникальные поля

- `SlugField(unique=True)` — короткий URL-идентификатор (например, `the-dark-knight`).
- `UUIDField(default=uuid.uuid4, unique=True)` — уникальный идентификатор записи.
- `EmailField()` — для e-mail адресов.
- `URLField()` — для ссылок.

💡 _Пример:_

```python
slug = models.SlugField(unique=True)
trailer_url = models.URLField(blank=True)
```

---

## Как выбрать подходящий тип поля

| Задача                 | Тип поля                                           |
| ---------------------- | -------------------------------------------------- |
| Короткий текст         | `CharField(max_length=...)`                        |
| Длинный текст          | `TextField()`                                      |
| Дата или время         | `DateTimeField()` / `DateField()`                  |
| Число                  | `IntegerField()`, `FloatField()`, `DecimalField()` |
| Да/Нет                 | `BooleanField()`                                   |
| Изображение            | `ImageField()`                                     |
| Связь с другой моделью | `ForeignKey`, `OneToOneField`, `ManyToManyField`   |

---

## Вопросы

1. Что делает ORM и почему она упрощает работу с базами данных?
2. Чем ORM отличается от SQL-запросов?
3. Где в Django настраивается подключение к базе данных?
4. Как создать новую таблицу (модель) в Django?
5. Для чего нужны команды `makemigrations` и `migrate`?
6. Что делает метод `__str__` в модели?
7. Как добавить новую запись в базу через ORM?
8. Как проверить список всех фильмов в Django shell?
9. Что делает параметр `auto_now_add=True`?
10. Как вывести объекты модели на страницу через шаблон?

---

[Предыдущий урок](lesson13.md) | [Следующий урок](lesson15.md)
