# Модуль 4. Урок 23. ORM-команды для связи Many-to-One

В прошлом уроке мы познакомились с тем, как в Django создаётся связь **«многие к одному» (Many-to-One)** с помощью `ForeignKey`.

Теперь пришло время научиться **работать с этими связями через ORM**, получать связанные объекты, фильтровать их и строить удобные выборки данных.

Мы будем работать в контексте проекта **Cinemahub**, где у нас уже есть две модели:

```python
from django.db import models

class Category(models.Model):
    name = models.CharField(max_length=100, db_index=True)
    slug = models.SlugField(max_length=255, unique=True, db_index=True)

    def __str__(self):
        return self.name


class Movie(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    release_year = models.PositiveIntegerField()
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='movies')

    def __str__(self):
        return self.title
```

Каждый фильм (`Movie`) относится к определённой категории (`Category`). Например:

* фильм *«Inception»* — к категории *«Science Fiction»*,
* фильм *«The Godfather»* — к категории *«Crime»*.

---

## Работа с ORM через shell

Для начала откроем интерактивную консоль Django:

```bash
python manage.py shell
```

Теперь можно работать напрямую с моделями.

### 1. Получаем фильм по ID

```python
m = Movie.objects.get(pk=1)
```

Теперь объект `m` — это один конкретный фильм.

Можно проверить его поля:

```python
m.title
m.release_year
m.category_id
```

`category_id` — это значение внешнего ключа, то есть ID категории, к которой относится фильм.

### 2. Доступ к связанным объектам

Чтобы получить сам объект категории, можно обратиться к атрибуту `category`:

```python
m.category.name
```

Это вызовет **дополнительный SQL-запрос** и вернёт имя категории.

Если в проекте включено логирование SQL-запросов, вы увидите, что ORM выполняет запрос `SELECT ... FROM category WHERE id = ...`.

---

## Обратная связь — от категории к фильмам

Django автоматически создаёт связь и в обратную сторону.

Теперь мы можем узнать, **какие фильмы принадлежат конкретной категории**.

### 1. Пример без `related_name`

Если бы в модели `Movie` не было параметра `related_name`, то обращение выглядело бы так:

```python
c = Category.objects.get(pk=1)
c.movie_set.all()
```

Это стандартное имя, которое Django создаёт автоматически:
**`<имя_модели>_set`** (в нашем случае — `movie_set`).

### 2. Пример с `related_name`

Но мы добавили в модель `Movie` параметр `related_name='movies'`, поэтому теперь можем писать более удобно:

```python
c.movies.all()
```

Здесь `c` — это категория, а `c.movies` — связанный набор фильмов.

### 3. Фильтрация связанных записей

Можно фильтровать связанные фильмы, например:

```python
c.movies.filter(release_year__gte=2020)
```

Это вернёт все фильмы данной категории, выпущенные после 2020 года.

---

## Фильтрация по внешнему ключу

Часто нужно отобрать фильмы, принадлежащие к определённой категории.

### 1. По ID категории

```python
Movie.objects.filter(category_id=1)
```

### 2. По объекту категории

```python
c = Category.objects.get(name='Science Fiction')
Movie.objects.filter(category=c)
```

### 3. По нескольким категориям

```python
Movie.objects.filter(category__in=[1, 2])
```

или

```python
cats = Category.objects.filter(name__in=['Science Fiction', 'Drama'])
Movie.objects.filter(category__in=cats)
```

---

## Фильтрация по полям связанных моделей

Django позволяет фильтровать не только по текущей модели, но и по полям связанных.

### Примеры:

1. Фильмы по `slug` категории:

   ```python
   Movie.objects.filter(category__slug='drama')
   ```

2. Фильмы по имени категории:

   ```python
   Movie.objects.filter(category__name='Science Fiction')
   ```

3. По части названия категории:

   ```python
   Movie.objects.filter(category__name__icontains='fiction')
   ```

4. И наоборот — получить категории, в которых есть фильмы, соответствующие определённому условию:

   ```python
   Category.objects.filter(movies__title__icontains='star').distinct()
   ```

Метод `.distinct()` нужен, чтобы исключить дубликаты, ведь в одной категории может быть несколько фильмов с похожими названиями.

---

## Отображение фильмов по категориям в Django

Теперь давайте добавим отображение фильмов по категориям в приложении.

Мы сделаем это пошагово.

---

### 1. Настраиваем маршруты (`urls.py`)

В файле `cinemahub/urls.py` добавим маршрут для категории:

```python
from django.urls import path
from . import views

urlpatterns = [
    path('category/<slug:cat_slug>/', views.show_category, name='category'),
]
```

Теперь URL вроде `/category/drama/` будет показывать фильмы из категории «Драма».

---

### 2. Обновляем представление (`views.py`)

Создадим функцию `show_category`:

```python
from django.shortcuts import render, get_object_or_404
from .models import Movie, Category

def show_category(request, cat_slug):
    category = get_object_or_404(Category, slug=cat_slug)
    movies = Movie.objects.filter(category=category)
    return render(request, 'movies/category_list.html', {
        'category': category,
        'movies': movies,
    })
```

Здесь мы:

1. Получаем объект категории по `slug`.
2. Извлекаем все фильмы, связанные с этой категорией.
3. Передаём их в шаблон.

---

### 3. Создаём шаблон `category_list.html`

```html
<h1>Фильмы категории: {{ category.name }}</h1>

<ul>
  {% for movie in movies %}
    <li>
      <strong>{{ movie.title }}</strong> ({{ movie.release_year }})
    </li>
  {% empty %}
    <li>В этой категории пока нет фильмов.</li>
  {% endfor %}
</ul>
```

Проверяем в браузере:

Переходим по адресу `http://127.0.0.1:8000/category/drama/` — видим список фильмов этой категории.

---

### 4. Добавляем метод `get_absolute_url()` в модель `Category`

Чтобы генерировать ссылки автоматически, добавим метод:

```python
from django.urls import reverse

class Category(models.Model):
    name = models.CharField(max_length=100, db_index=True)
    slug = models.SlugField(max_length=255, unique=True, db_index=True)

    def get_absolute_url(self):
        return reverse('category', kwargs={'cat_slug': self.slug})
```

Теперь в шаблонах можно ссылаться на категорию так:

```html
<a href="{{ category.get_absolute_url }}">{{ category.name }}</a>
```

---

## Проверка результата

1. Создайте несколько категорий в админке:

   * «Драма»
   * «Научная фантастика»
   * «Комедия»

2. Добавьте несколько фильмов и назначьте им категории.

3. Перейдите в браузере по адресу:

   ```
   /category/drama/
   /category/science-fiction/
   ```

   Убедитесь, что фильтры работают корректно.

4. Измените `related_name` в `Movie` и убедитесь, что можно обращаться к фильмам через `category.movies.all()`.

---

## Возможные ошибки

* **`DoesNotExist`** — если указанный объект не найден. Решается заменой `.get()` на `get_object_or_404()`.
* **`ProtectedError`** — при попытке удалить категорию, если используется `on_delete=PROTECT`.
* **`IntegrityError`** — если добавляете фильм без категории, а поле не допускает `null=True`.

---

## Практические задания

1. Создайте 3 категории фильмов и 6 фильмов, по 2 на каждую категорию.
   Попробуйте получить все фильмы одной категории через `category.movies.all()`.

2. Напишите запрос, который найдёт все фильмы, вышедшие после 2015 года в категории «Драма».

3. Получите все категории, в которых есть хотя бы один фильм с названием, содержащим слово “Love”.

4. Измените `related_name` и проверьте, как меняется способ обращения к связанным данным.

5. В шаблоне выведите список категорий и добавьте ссылки на каждую через `get_absolute_url()`.

---

## Вопросы

1. Что такое связь «многие к одному» (Many-to-One)?
2. Чем `category_id` отличается от `category`?
3. Для чего нужен параметр `related_name` в `ForeignKey`?
4. Что делает метод `.distinct()`?
5. Как получить все фильмы категории без использования SQL?
6. Как можно фильтровать объекты по полям связанных моделей?
7. Почему может возникнуть ошибка `ProtectedError`?
8. Зачем нужен метод `get_absolute_url()`?
9. Что делает `get_object_or_404()` и почему он удобнее, чем `.get()`?
10. Что произойдёт, если удалить категорию при `on_delete=CASCADE`?

---

[Предыдущий урок](lesson22.md) | [Следующий урок](lesson24.md)