# 🔥 Создаём четыре связанные сущности для практики

В этом модуле нам нужны данные, которые позволят тренировать фильтрацию, связи, агрегации, аннотации и оптимизацию запросов.

Мы создаём 4 сущности:

### 1. **Movie** — основной фильм

### 2. **Genre** — жанры (многие-ко-многим)

### 3. **Director** — режиссёры (один-ко-многим)

### 4. **Review** — отзывы пользователей о фильмах (один-ко-многим)

Эти модели дают нам полный набор кейсов:

* OneToMany
* ManyToMany
* Backward relations
* RelatedManager
* Prefetch / select_related
* Агрегации по связанным таблицам

---

# 1. Модели (models.py)

```python
from django.db import models
from django.utils.text import slugify


class Genre(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Director(models.Model):
    full_name = models.CharField(max_length=255)
    birth_year = models.IntegerField()
    country = models.CharField(max_length=100)
    slug = models.SlugField(max_length=255, unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.full_name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.full_name


class Movie(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    year = models.IntegerField()
    rating = models.FloatField(default=0.0)
    is_published = models.BooleanField(default=False)
    budget = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True)

    director = models.ForeignKey(
        Director, on_delete=models.SET_NULL, null=True, related_name="movies"
    )
    genres = models.ManyToManyField(Genre, related_name="movies")

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class Review(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name="reviews")
    author = models.CharField(max_length=100)
    text = models.TextField()
    rating = models.IntegerField()  # 1..10
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.author} — {self.movie.title}"
```

---

# 2. Генерация фейковых данных (management/commands/generate_cinema_data.py)

Файл:
`core/management/commands/generate_cinema_data.py`

```python
from django.core.management.base import BaseCommand
from faker import Faker
import random

from movies.models import Genre, Director, Movie, Review
from django.utils.text import slugify


class Command(BaseCommand):
    help = "Generate fake cinema data"

    def handle(self, *args, **kwargs):
        fake = Faker()

        # 1. Genres
        genres_list = []
        for name in ["Action", "Drama", "Comedy", "Fantasy", "Horror"]:
            g = Genre.objects.create(name=name, slug=slugify(name))
            genres_list.append(g)

        # 2. Directors
        directors = []
        for _ in range(5):
            fullname = fake.name()
            d = Director.objects.create(
                full_name=fullname,
                birth_year=random.randint(1950, 1995),
                country=fake.country(),
                slug=slugify(fullname),
            )
            directors.append(d)

        # 3. Movies
        movies = []
        for _ in range(10):
            title = fake.sentence(nb_words=3).replace(".", "")
            m = Movie.objects.create(
                title=title,
                description=fake.text(),
                year=random.randint(1980, 2024),
                rating=round(random.uniform(1.0, 9.8), 1),
                is_published=random.choice([True, False]),
                budget=random.randint(3_000_000, 200_000_000),
                slug=slugify(title),
                director=random.choice(directors),
            )
            m.genres.add(*random.sample(genres_list, k=random.randint(1, 3)))
            movies.append(m)

        # 4. Reviews
        for movie in movies:
            for _ in range(random.randint(1, 5)):
                Review.objects.create(
                    movie=movie,
                    author=fake.first_name(),
                    text=fake.text(),
                    rating=random.randint(1, 10),
                )

        self.stdout.write(self.style.SUCCESS("Cinema data generated!"))
```

Запуск:

```bash
python manage.py generate_cinema_data
```

---

# 3. Пример работы через Django shell

Открываем:

```bash
python manage.py shell
```

### ➤ Создать жанр

```python
from movies.models import Genre
from django.utils.text import slugify

g = Genre.objects.create(name="Thriller", slug=slugify("Thriller"))
```

### ➤ Создать режиссёра

```python
from movies.models import Director

d = Director.objects.create(
    full_name="James Nolan",
    birth_year=1978,
    country="USA",
    slug="james-nolan"
)
```

### ➤ Создать фильм

```python
from movies.models import Movie

m = Movie.objects.create(
    title="Dark Waves",
    description="Psychological thriller on the ocean.",
    year=2021,
    rating=8.8,
    is_published=True,
    budget=85000000,
    director=d,
    slug="dark-waves"
)
m.genres.add(g)
```

### ➤ Добавить отзыв

```python
from movies.models import Review

Review.objects.create(
    movie=m,
    author="Alex",
    text="Amazing film!",
    rating=9
)
```

---

# 4. Готовые данные (5 записей для каждой сущности)

Студент может **просто скопировать и вставить** эти записи в Django shell.

---

## ✅ 5 жанров

```python
from movies.models import Genre
Genre.objects.bulk_create([
    Genre(name="Action", slug="action"),
    Genre(name="Comedy", slug="comedy"),
    Genre(name="Drama", slug="drama"),
    Genre(name="Fantasy", slug="fantasy"),
    Genre(name="Sci-Fi", slug="sci-fi"),
])
```

---

## ✅ 5 режиссёров

```python
from movies.models import Director
Director.objects.bulk_create([
    Director(full_name="Christopher Nolan", birth_year=1970, country="UK", slug="christopher-nolan"),
    Director(full_name="Quentin Tarantino", birth_year=1963, country="USA", slug="quentin-tarantino"),
    Director(full_name="Denis Villeneuve", birth_year=1967, country="Canada", slug="denis-villeneuve"),
    Director(full_name="Ridley Scott", birth_year=1937, country="UK", slug="ridley-scott"),
    Director(full_name="Patty Jenkins", birth_year=1971, country="USA", slug="patty-jenkins"),
])
```

---

## ✅ 5 фильмов

После вставки — не забудьте привязать жанры вручную (пример ниже).

```python
from movies.models import Movie, Director
from django.utils.text import slugify

d1 = Director.objects.first()
d2 = Director.objects.last()

Movie.objects.create(title="Iron Horizon", year=2020, description="...", budget=100000000, rating=7.8, is_published=True, director=d1, slug="iron-horizon")
Movie.objects.create(title="Silent Dream", year=2019, description="...", budget=25000000, rating=6.9, is_published=True, director=d2, slug="silent-dream")
Movie.objects.create(title="Frozen Night", year=2022, description="...", budget=50000000, rating=8.2, is_published=False, director=d1, slug="frozen-night")
Movie.objects.create(title="Golden Path", year=2018, description="...", budget=70000000, rating=7.1, is_published=True, director=d1, slug="golden-path")
Movie.objects.create(title="Shadow River", year=2023, description="...", budget=40000000, rating=8.9, is_published=True, director=d2, slug="shadow-river")
```

Привязка жанров:

```python
from movies.models import Movie, Genre

m = Movie.objects.get(slug="iron-horizon")
m.genres.add(Genre.objects.get(slug="action"))

m = Movie.objects.get(slug="shadow-river")
m.genres.add(Genre.objects.get(slug="fantasy"), Genre.objects.get(slug="drama"))
```

---

## ✅ 5 отзывов

```python
from movies.models import Movie, Review

movie = Movie.objects.first()

Review.objects.bulk_create([
    Review(movie=movie, author="Anna", text="Great!", rating=9),
    Review(movie=movie, author="Max", text="Not bad", rating=7),
    Review(movie=movie, author="John", text="Could be better", rating=6),
    Review(movie=movie, author="Elena", text="Amazing visuals", rating=10),
    Review(movie=movie, author="Leo", text="Weak story", rating=5),
])
```

---