# Урок 10. Связи между моделями: ForeignKey, ManyToMany, OneToOne — теория + ORM-команды для всех типов

## Почему одной таблицы недостаточно

До этого момента у нас две таблицы: `Film` и `Genre`. Они существуют независимо — жанр нельзя «прикрепить» к фильму. В реальном приложении данные всегда связаны: у фильма есть режиссёр, жанры, актёры. У пользователя — профиль.

В реляционных базах данных связи между таблицами — это фундамент. Мы уже работали с JOIN в первом модуле прошлого курса. Django ORM делает то же самое, но описывает связи на уровне Python-классов, а SQL генерирует сам.

Три типа связей, которые мы разберём в этом уроке:

| Тип | Пример | Поле Django |
|---|---|---|
| Many-to-One | Фильм → Режиссёр (у фильма один режиссёр, у режиссёра много фильмов) | `ForeignKey` |
| Many-to-Many | Фильм ↔ Жанры (у фильма много жанров, жанр у многих фильмов) | `ManyToManyField` |
| One-to-One | Пользователь ↔ Профиль (один к одному) | `OneToOneField` |

---

## Many-to-One: ForeignKey

### Теория

Many-to-One — самая распространённая связь. У фильма один режиссёр, но у режиссёра может быть много фильмов. В базе данных это реализуется через внешний ключ: в таблице `films_film` появляется колонка `director_id`, которая хранит `id` записи из таблицы `films_director`.

### Добавляем модели Director и Film с ForeignKey

```python
# films/models.py
from django.db import models


class Director(models.Model):
    name = models.CharField(max_length=200, verbose_name='Имя')
    bio = models.TextField(blank=True, verbose_name='Биография')
    photo = models.ImageField(
        upload_to='directors/',
        blank=True,
        verbose_name='Фото'
    )

    class Meta:
        ordering = ['name']
        verbose_name = 'Режиссёр'
        verbose_name_plural = 'Режиссёры'

    def __str__(self):
        return self.name


class Genre(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name='Название')
    slug = models.SlugField(max_length=100, unique=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Жанр'
        verbose_name_plural = 'Жанры'

    def __str__(self):
        return self.name


class FilmManager(models.Manager):

    def high_rated(self):
        return self.filter(rating__gte=8.0)

    def by_year(self, year):
        return self.filter(year=year)

    def recent(self, count=5):
        return self.order_by('-created_at')[:count]

    def search(self, query):
        return self.filter(
            models.Q(title__icontains=query) |
            models.Q(description__icontains=query)
        )


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

    # Many-to-One: у фильма один режиссёр
    director = models.ForeignKey(
        Director,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='films',
        verbose_name='Режиссёр'
    )

    objects = FilmManager()

    class Meta:
        ordering = ['-year']
        verbose_name = 'Фильм'
        verbose_name_plural = 'Фильмы'

    def __str__(self):
        return f'{self.title} ({self.year})'
```

> **Важно:** 
> 
> Для работы поля `ImageField`(Модель `Director` - поле `photo`) Django использует стороннюю библиотеку **Pillow** (обработчик изображений для Python). 
> 
> Если библиотека не установлена, при запуске проекта или выполнении миграций может возникнуть ошибка.
> 
> Для исправления ошибки установите **Pillow**:
>
> ```bash
> pip install pillow
> ```

### Параметры ForeignKey

**`on_delete`** — обязательный параметр. Определяет, что произойдёт с фильмами, если режиссёр будет удалён:

| Значение | Поведение |
|---|---|
| `CASCADE` | Удалить все связанные фильмы вместе с режиссёром |
| `SET_NULL` | Поставить `NULL` в поле `director` (требует `null=True`) |
| `SET_DEFAULT` | Поставить значение по умолчанию |
| `PROTECT` | Запретить удаление режиссёра, пока есть связанные фильмы |
| `DO_NOTHING` | Ничего не делать (опасно — нарушает целостность БД) |

Для нашего проекта выбираем `SET_NULL` — удаление режиссёра не должно удалять фильмы.

**`related_name='films'`** — имя обратной связи. Через него можно получить все фильмы режиссёра: `director.films.all()`. Если не указать, Django создаст имя автоматически: `director.film_set.all()`.

### ORM-команды для ForeignKey

```python
# Создание фильма с режиссёром
coppola = Director.objects.create(name='Фрэнсис Форд Коппола')
film = Film.objects.create(
    title='Крёстный отец',
    year=1972,
    slug='krestnyj-otec',
    director=coppola       # передаём объект
)

# Или через id
film = Film.objects.create(
    title='Крёстный отец',
    year=1972,
    slug='krestnyj-otec',
    director_id=coppola.id  # передаём id напрямую
)

# Получить режиссёра фильма (прямая связь)
film = Film.objects.get(slug='krestnyj-otec')
print(film.director)        # Фрэнсис Форд Коппола
print(film.director.name)   # Фрэнсис Форд Коппола

# Получить все фильмы режиссёра (обратная связь через related_name)
coppola = Director.objects.get(name='Фрэнсис Форд Коппола')
films = coppola.films.all()

# Фильтрация по связанной модели через __
films = Film.objects.filter(director__name='Фрэнсис Форд Коппола')
films = Film.objects.filter(director__name__icontains='коппола')
```

Двойное подчёркивание `__` работает не только для Field Lookups, но и для «перехода» по связи в другую таблицу. `director__name` означает: перейди в связанную таблицу `Director` и обратись к полю `name`. В SQL это транслируется в `JOIN`.

---

## Many-to-Many: ManyToManyField

### Теория

У фильма много жанров, и один жанр относится ко многим фильмам. В реляционной базе данных такая связь реализуется через **промежуточную таблицу** (junction table): `films_film_genres` с колонками `film_id` и `genre_id`.

Django создаёт эту таблицу автоматически — нам не нужно описывать её в коде.

### Добавляем Actor и ManyToManyField

```python
class Actor(models.Model):
    name = models.CharField(max_length=200, verbose_name='Имя')
    photo = models.ImageField(
        upload_to='actors/',
        blank=True,
        verbose_name='Фото'
    )

    class Meta:
        ordering = ['name']
        verbose_name = 'Актёр'
        verbose_name_plural = 'Актёры'

    def __str__(self):
        return self.name


class Film(models.Model):
    # ... предыдущие поля ...

    director = models.ForeignKey(
        Director,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='films',
        verbose_name='Режиссёр'
    )

    # Many-to-Many: у фильма много жанров
    genres = models.ManyToManyField(
        Genre,
        blank=True,
        related_name='films',
        verbose_name='Жанры'
    )

    # Many-to-Many: у фильма много актёров
    actors = models.ManyToManyField(
        Actor,
        blank=True,
        related_name='films',
        verbose_name='Актёры'
    )
```

Обрати внимание: у `ManyToManyField` нет параметра `on_delete` — при удалении фильма или жанра Django просто удаляет строки в промежуточной таблице, сами объекты остаются.

### ORM-команды для ManyToManyField

M2M-связь управляется через специальный менеджер, который доступен как атрибут поля:

```python
film = Film.objects.get(slug='krestnyj-otec')
drama = Genre.objects.get(name='Драма')
crime = Genre.objects.get(name='Криминал')

# Добавить жанры
film.genres.add(drama)
film.genres.add(drama, crime)          # несколько сразу

# Получить все жанры фильма
film.genres.all()

# Установить жанры — заменяет все текущие
film.genres.set([drama, crime])

# Удалить один жанр
film.genres.remove(drama)

# Очистить все жанры
film.genres.clear()

# Проверить наличие
film.genres.filter(name='Драма').exists()
```

Обратная сторона связи — через `related_name`:

```python
# Все фильмы жанра «Криминал»
crime = Genre.objects.get(name='Криминал')
crime.films.all()
```

Фильтрация через `__`:

```python
# Фильмы жанра «Драма»
Film.objects.filter(genres__name='Драма')

# Фильмы с актёром по имени (без учёта регистра)
Film.objects.filter(actors__name__icontains='пачино')

# Фильмы, у которых есть хотя бы один жанр
Film.objects.filter(genres__isnull=False).distinct()
```

`.distinct()` здесь важен: если у фильма несколько жанров, JOIN вернёт дублирующиеся строки, и без `distinct()` один фильм попадёт в результат несколько раз.

---

## One-to-One: OneToOneField

### Теория

Один объект связан ровно с одним другим объектом. В базе данных это ForeignKey с ограничением `UNIQUE`. Используется для расширения существующей модели без изменения самой модели.

Классический пример в Django — расширение встроенной модели `User`. Встроенная модель содержит только базовые поля: `username`, `email`, `password`. Для профиля пользователя (аватар, биография) создаётся отдельная модель с `OneToOneField` на `User`.

Эту связь мы реализуем полностью в модуле 7, когда дойдём до авторизации. Сейчас разберём механику на примере нашего проекта.

### Добавляем модель FilmStats

Представь, что мы хотим хранить статистику просмотров отдельно от основной модели — чтобы не раздувать таблицу `films_film`:

```python
class FilmStats(models.Model):
    film = models.OneToOneField(
        Film,
        on_delete=models.CASCADE,
        related_name='stats',
        verbose_name='Фильм'
    )
    views_count = models.PositiveIntegerField(default=0, verbose_name='Просмотры')
    likes_count = models.PositiveIntegerField(default=0, verbose_name='Лайки')

    class Meta:
        verbose_name = 'Статистика фильма'
        verbose_name_plural = 'Статистика фильмов'

    def __str__(self):
        return f'Статистика: {self.film.title}'
```

`on_delete=CASCADE` здесь логичен: если фильм удалён — статистика теряет смысл.

### ORM-команды для OneToOneField

```python
film = Film.objects.get(slug='krestnyj-otec')

# Создать статистику для фильма
stats = FilmStats.objects.create(film=film, views_count=1000)

# Получить статистику фильма (прямая связь)
print(film.stats.views_count)  # 1000

# Получить фильм по статистике (обратная связь)
stats = FilmStats.objects.get(film__slug='krestnyj-otec')
print(stats.film.title)        # Крёстный отец

# Обновить счётчик
film.stats.views_count += 1
film.stats.save()
```

Главное отличие от `ForeignKey`: обращение к связанному объекту через `film.stats` вернёт один объект, а не QuerySet. Если статистики нет — выбросит `RelatedObjectDoesNotExist`.

---

### ForeignKey отличается от OneToOneField на уровне базы данных

На уровне базы данных оба создают внешний ключ. Разница в ограничении: `OneToOneField` добавляет `UNIQUE` на колонку с внешним ключом, что гарантирует — каждому объекту соответствует ровно один связанный объект. 

`ForeignKey` без `unique=True` позволяет нескольким записям ссылаться на один и тот же объект (много-к-одному).

## select_related и prefetch_related

Работа со связями порождает классическую проблему N+1: если вывести список из 100 фильмов и для каждого обратиться к `film.director`, Django выполнит 101 запрос — один для списка и по одному для каждого режиссёра.

Django решает это двумя методами:

**`select_related`** — для связей ForeignKey и OneToOne. Делает один SQL-запрос с JOIN:

```python
# Без select_related: 1 + N запросов
films = Film.objects.all()
for film in films:
    print(film.director.name)  # каждый раз новый SELECT

# С select_related: 1 запрос с JOIN
films = Film.objects.select_related('director').all()
for film in films:
    print(film.director.name)  # данные уже загружены
```

**`prefetch_related`** — для связей ManyToMany и обратных ForeignKey. Делает отдельный запрос для каждой связи и соединяет результаты в Python:

```python
# Без prefetch_related: 1 + N запросов
films = Film.objects.all()
for film in films:
    print(film.genres.all())   # каждый раз новый SELECT

# С prefetch_related: 2 запроса суммарно
films = Film.objects.prefetch_related('genres', 'actors').all()
for film in films:
    print(film.genres.all())   # данные уже загружены
```

Можно комбинировать оба метода:

```python
films = Film.objects.select_related('director').prefetch_related('genres', 'actors')
```

Мы увидим реальный эффект от этих методов в уроке 12, когда подключим Django Debug Toolbar и сравним количество SQL-запросов.

---

## Создаём миграцию

После всех изменений в `models.py` создаём и применяем миграцию:

```bash
python manage.py makemigrations
python manage.py migrate
```

Django создаст таблицы `films_director`, `films_actor`, `films_filmstats`, а также промежуточные таблицы `films_film_genres` и `films_film_actors`.

---

## Обновляем представление film_detail

Теперь страница фильма может показывать режиссёра, жанры и актёров:

```python
# films/views.py
def film_detail(request, film_id):
    film = get_object_or_404(
        Film.objects.select_related('director').prefetch_related('genres', 'actors'),
        id=film_id
    )
    return render(request, 'films/film_detail.html', {'film': film})
```

```html
<!-- films/templates/films/film_detail.html -->
{% extends 'base.html' %}

{% block title %}{{ film.title }} — Сайт фильмов{% endblock %}

{% block content %}
    <h1>{{ film.title }}</h1>
    <p>Год выпуска: {{ film.year }}</p>

    {% if film.director %}
        <p>Режиссёр: {{ film.director.name }}</p>
    {% endif %}

    {% if film.genres.all %}
        <p>Жанры:
            {% for genre in film.genres.all %}
                {{ genre.name }}{% if not forloop.last %}, {% endif %}
            {% endfor %}
        </p>
    {% endif %}

    {% if film.actors.all %}
        <p>Актёры:
            {% for actor in film.actors.all %}
                {{ actor.name }}{% if not forloop.last %}, {% endif %}
            {% endfor %}
        </p>
    {% endif %}

    <p>{{ film.description|default:"Описание отсутствует." }}</p>

    {% if film.stats %}
        <p>Просмотров: {{ film.stats.views_count }}</p>
    {% endif %}

    <a href="{% url 'films:film_list' %}">← Назад к каталогу</a>
{% endblock %}
```

---

## Подводные камни

### NULL в ForeignKey

`ForeignKey` по умолчанию не допускает `NULL` — связь обязательна. Если добавляешь ForeignKey в уже существующую таблицу с данными без `null=True` — Django при `makemigrations` потребует значение по умолчанию для существующих строк. Всегда думай заранее: может ли фильм существовать без режиссёра?

```python
# Необязательная связь (режиссёр может быть не указан)
director = models.ForeignKey(Director, on_delete=models.SET_NULL, null=True, blank=True)

# Обязательная связь (режиссёр всегда должен быть указан)
director = models.ForeignKey(Director, on_delete=models.CASCADE)
```

### related_name при нескольких ForeignKey на одну модель

Если в одной модели два ForeignKey указывают на одну и ту же модель — Django не сможет автоматически создать обратные имена и выдаст ошибку. `related_name` становится обязательным:

```python
class Film(models.Model):
    director = models.ForeignKey(
        Person, on_delete=models.SET_NULL,
        null=True, related_name='directed_films'
    )
    screenwriter = models.ForeignKey(
        Person, on_delete=models.SET_NULL,
        null=True, related_name='written_films'
    )
```

### distinct() при фильтрации через M2M

Фильтрация через ManyToMany делает JOIN с промежуточной таблицей. Если у фильма несколько жанров и условие совпадает с несколькими из них — фильм попадёт в результат несколько раз:

```python
# Один фильм может появиться дважды
Film.objects.filter(genres__name__in=['Драма', 'Криминал'])

# distinct() убирает дубликаты
Film.objects.filter(genres__name__in=['Драма', 'Криминал']).distinct()
```

---

## Вопросы

1. Чем ForeignKey отличается от OneToOneField на уровне базы данных?
2. Нужно ли вручную создавать промежуточную таблицу для ManyToManyField?
3. Что такое `related_name` и что произойдёт, если его не указать?
4. В чём разница между `select_related` и `prefetch_related`? Когда использовать каждый?
5. Почему при фильтрации через ManyToMany иногда нужен `.distinct()`?

---

## Практическая задача

**Тип: расширь проект**

**Часть 1.** Добавь в `films/views.py` представление `director_detail`, которое показывает страницу режиссёра: имя, биографию и список его фильмов. Используй `select_related` и `prefetch_related` там, где это уместно.

**Часть 2.** Создай шаблон `films/templates/films/director_detail.html`, который наследует `base.html` и выводит информацию о режиссёре и список его фильмов через `{% include 'films/includes/film_card.html' %}`.

**Часть 3.** Убедись, что маршрут `directors/<int:director_id>/` с именем `director_detail` добавлен в `films/urls.py` (мы создавали его в уроке 2 — проверь, что он там есть).

---

[Предыдущий урок](lesson09.md) | [Следующий урок](lesson11.md)