# 🔥 Дополнительный раздел перед практикой

## Создание модели и подготовка фейковых данных для выполнения практических заданий

Перед тем как переходить к практической части урока, нам нужно:

1. Создать модель, которая будет использоваться в заданиях.
2. Подготовить набор тестовых (фейковых) данных.
3. Понять, как эти данные можно добавить в базу через Django shell.

Этот раздел формирует основу, на которой студент будет работать во всех упражнениях — фильтрации, выборке полей, агрегациях, аннотациях и других ORM-конструкциях.

---

# 1. Создаём модель **Movie**

Модель должна быть максимально удобной для тренировок, поэтому мы включим в неё разные типы:

* **CharField** — текстовые названия
* **TextField** — описание
* **IntegerField** — численные данные
* **FloatField** — рейтинг
* **BooleanField** — признак опубликованности
* **DateField / DateTimeField** — даты
* **SlugField**
* **ForeignKey / ManyToManyField** (если будут нужны в модуле)

> В этом уроке для упрощения делаем модель без связей. Связи идут в следующем модуле.

### 📌 Пример модели `Movie` (models.py)

```python
from django.db import models
from django.utils.text import slugify

class Movie(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    year = models.IntegerField()
    rating = models.FloatField(default=0.0)
    is_published = models.BooleanField(default=False)
    budget = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
```

---

# 2. Подготовка фейковых данных

Данные создадим с помощью Faker.
Набор полей будет полноценно покрывать практические задачи:

* названия фильмов
* описания
* случайные годы (1980–2024)
* случайные рейтинги
* случайные бюджеты
* published / not published
* корректный slug
* даты создания

### 📌 Скрипт для генерации данных (например, в **movies/management/commands/generate_movies.py**)

```python
from django.core.management.base import BaseCommand
from faker import Faker
import random
from movies.models import Movie
from django.utils.text import slugify

class Command(BaseCommand):
    help = "Generate fake movies data"

    def handle(self, *args, **kwargs):
        fake = Faker()

        for _ in range(50):
            title = fake.sentence(nb_words=3).replace(".", "")
            Movie.objects.create(
                title=title,
                description=fake.text(),
                year=random.randint(1980, 2024),
                rating=round(random.uniform(1.0, 9.9), 1),
                is_published=random.choice([True, False]),
                budget=random.randint(1_000_000, 200_000_000),
                slug=slugify(title),
                created_at=fake.date_time_between(start_date="-5y", end_date="now"),
            )

        self.stdout.write(self.style.SUCCESS("Fake movies created!"))
```

Запуск:

```bash
python manage.py generate_movies
```

---

# 3. Пример добавления таких данных через **Django shell**

Этот блок демонстрирует студенту, как вручную работать с ORM, создавать записи, сохранять их и извлекать.

Открываем shell:

```bash
python manage.py shell
```

### ➤ Создадим одну запись вручную

```python
from movies.models import Movie
from django.utils.text import slugify
from datetime import datetime

movie = Movie.objects.create(
    title="The Silent Forest",
    description="Mystery thriller about a forgotten place.",
    year=2022,
    rating=8.4,
    is_published=True,
    budget=45000000,
    slug=slugify("The Silent Forest"),
    created_at=datetime(2023, 5, 17, 14, 30)
)

movie
```

### ➤ Создадим несколько записей в цикле

```python
from faker import Faker
import random
from movies.models import Movie
from django.utils.text import slugify

fake = Faker()

for _ in range(5):
    title = fake.sentence(nb_words=3).replace(".", "")
    Movie.objects.create(
        title=title,
        description=fake.text(),
        year=random.randint(1980, 2024),
        rating=round(random.uniform(1.0, 10.0), 1),
        is_published=random.choice([True, False]),
        budget=random.randint(2_000_000, 100_000_000),
        slug=slugify(title),
        created_at=fake.date_time_between(start_date="-2y", end_date="now"),
    )
```

### ➤ Проверим, что записи появились

```python
Movie.objects.count()
```

---

# 🎯 Короткая инструкция: что чаще всего генерируют через Faker

Ниже — **только самые используемые методы**, которых достаточно в 90% учебных проектов.

## 👤 Люди (режиссёры, актёры, авторы)

```python
fake.name()
fake.first_name()
fake.last_name()
fake.job()            # профессия
```

## 📝 Текст (описания, слоганы, рецензии)

```python
fake.sentence()       # короткое описание
fake.paragraph()      # несколько предложений
fake.text(max_nb_chars=200)
```

## ⭐ Числа (рейтинги, возраст, бюджет)

```python
fake.random_int(min=0, max=100)
fake.pyfloat(positive=True)
```

## 📅 Даты (дата релиза, рождения)

```python
fake.date()
fake.date_time_between(start_date="-10y", end_date="now")
```

## 🌐 Интернет (email, ссылки, username)

```python
fake.email()
fake.url()
fake.user_name()
```

## 🏷️ Теги, ключевые слова

```python
fake.word()
fake.words(nb=3)
```

## 🗺 Адреса (если понадобятся)

```python
fake.city()
fake.country()
```

---

# 📌 Где использовать Faker в Django?

* **management-команды** для заполнения БД
* **тесты** (factories, fixtures)
* **скрипты генерации** мок-данных
* **seed для dev-окружения**
* **демо-проекты** и учебные курсы

---

# 🔧 Создание собственного провайдера (важный блок)

Если нужно генерировать «жанры», «названия фильмов», «киностудии» — создаём свой провайдер.

### 1. Создаём провайдер

```python
from faker.providers import BaseProvider

class MovieProvider(BaseProvider):
    def movie_genre(self):
        genres = ["Action", "Drama", "Comedy", "Sci-Fi", "Horror"]
        return self.random_element(genres)

    def movie_title(self):
        prefixes = ["Dark", "Silent", "Lost", "Golden"]
        nouns = ["Empire", "Storm", "Horizon", "Dream"]
        return f"{self.random_element(prefixes)} {self.random_element(nouns)}"
```

### 2. Подключаем в коде

```python
from faker import Faker
fake = Faker()
fake.add_provider(MovieProvider)
```

### 3. Используем

```python
fake.movie_genre()
fake.movie_title()
```

---

# 🎉 Итоговая компактная шпаргалка

### **Основные методы Faker**

| Категория   | Методы                                           |
| ----------- | ------------------------------------------------ |
| 👤 Люди     | `name()`, `first_name()`, `last_name()`, `job()` |
| 📝 Текст    | `sentence()`, `paragraph()`, `text()`            |
| ⭐ Числа     | `random_int()`, `pyfloat()`                      |
| 📅 Даты     | `date()`, `date_time_between()`                  |
| 🌐 Интернет | `email()`, `url()`, `user_name()`                |
| 🏷️ Теги    | `word()`, `words()`                              |

### **Обязательно знать**

📌 Можно создавать **свои провайдеры** (genre, movie_title, company_name).
📌 Faker часто используется в **seed-командах**, **тестах**, **dev-данных**.
📌 Можно указать локаль:

```python
fake = Faker("ru_RU")
```

---
