# Модуль 8. Урок 49. Класс `DetailView` в Django

## Введение: для чего нужен `DetailView`

`DetailView` — это обобщённое (generic) class-based view, которое отвечает за показ _одного_ объекта: страницы с детальной информацией о фильме, профиле актёра, странице жанра и т. п. В проекте **cinemahub** такие страницы встречаются постоянно: просмотр конкретного `Movie`, просмотр `DirectorProfile` или `ActorProfile`.

`DetailView` инкапсулирует типичную логику: получение одного объекта по `pk` или `slug`, проверка существования (404), передача объекта в шаблон. Наша задача — научиться корректно настраивать его под разные маршруты и требования (например, показывать только опубликованные фильмы).

---

## 1. Базовый пример: просмотр одного фильма

### 1.1. Что делает `DetailView` по умолчанию

При минимальной конфигурации `DetailView` требует одну из следующих вещей:

- указать `model`, и тогда будет использована выборка `model.objects.all()`;
- указать `queryset` — конкретную QuerySet;
- либо переопределить `get_object()` для кастомной логики.

По умолчанию `DetailView` ищет объект по `pk` (если в URL есть параметр `pk`) или по `slug` (если в URL есть параметр `slug`). Результат будет передан в шаблон под именем `object` и под названием модели в нижнем регистре (например, `movie`).

---

### 1.2. Простая реализация: `ShowMovieView`

**Файл:** `movies/views.py`

```python
from django.views.generic import DetailView
from .models import Movie

class ShowMovieView(DetailView):
    model = Movie
    template_name = 'movies/movie_detail.html'
    context_object_name = 'movie'  # удобное имя для шаблона
```

**Файл:** `movies/urls.py`

```python
from django.urls import path
from .views import ShowMovieView

urlpatterns = [
    path('movie/<int:pk>/', ShowMovieView.as_view(), name='movie_detail'),
]
```

**Простой шаблон:** `movies/templates/movies/movie_detail.html`

```html
<h1>{{ movie.title }}</h1>
<p>{{ movie.year }}</p>
<div>{{ movie.description }}</div>
```

Проверка в браузере:
`http://127.0.0.1:8000/movies/movie/1/` — должна открыться страница фильма с `pk=1`.

---

## 2. Использование `slug` в URL

Часто URL удобнее делать человекочитаемым — на основе slug. Тогда маршрут может выглядеть так:

**Файл:** `movies/urls.py`

```python
path('movie/<slug:movie_slug>/', ShowMovieView.as_view(), name='movie_detail')
```

Если вы используете имя параметра, отличное от `slug`, нужно сообщить `DetailView`, какой параметр использовать.

---

### 2.1. Связь имени параметра URL и `DetailView`

По умолчанию `DetailView` ищет `slug` в `self.kwargs['slug']`. Если в маршруте используется `movie_slug`, установите:

```python
class ShowMovieView(DetailView):
    model = Movie
    template_name = 'movies/movie_detail.html'
    context_object_name = 'movie'
    slug_url_kwarg = 'movie_slug'
```

Альтернатива — привести маршрут к `'<slug:slug>/'` и тогда специального указания не потребуется. Однако использование понятных имен параметров (`movie_slug`) улучшает читаемость URL-конфигурации.

---

## 3. Переименование объекта в шаблоне

`DetailView` по умолчанию кладёт объект в контекст под именем `object` и в виде имени модели в нижнем регистре (`movie`). Если вы хотите узнать или использовать собственное имя — задайте `context_object_name`, как показано выше. Это упрощает шаблоны и делает их более явными.

---

## 4. Показать только опубликованные фильмы — переопределяем `get_object`

В `cinemahub` нам обычно нужно показывать только `Movie` с `is_published=True`. Чтобы избежать случайного доступа к неопубликованным объектам (или чтобы корректно возвращать 404), лучше переопределить `get_object`.

**Файл:** `movies/views.py`

```python
from django.shortcuts import get_object_or_404

class ShowMovieView(DetailView):
    model = Movie
    template_name = 'movies/movie_detail.html'
    context_object_name = 'movie'
    slug_url_kwarg = 'movie_slug'  # если используете movie_slug в URL

    def get_object(self, queryset=None):
        slug = self.kwargs.get(self.slug_url_kwarg)
        queryset = queryset or self.get_queryset()
        # Фильтруем по is_published и ищем по slug
        return get_object_or_404(queryset.filter(is_published=True), slug=slug)
```

Обратите внимание:

- `get_queryset()` можно использовать, чтобы задать базовую выборку (например, `Movie.objects.select_related('director')`), тогда `get_object` будет работать быстрее.
- `get_object_or_404` — удобный способ вернуть 404 при отсутствии объекта.

**Альтернативный вариант**: установить `queryset = Movie.objects.filter(is_published=True)` в классе — тогда достаточно стандартного поведения `DetailView` (но при использовании `slug_url_kwarg` всё ещё нужно указать имя параметра, если оно нестандартное).

---

## 5. Доступ к дополнительным данным: `get_context_data`

Если странице детального просмотра нужно добавить дополнительные данные (связанные объекты, рекомендации, list похожих фильмов), используйте `get_context_data`.

**Пример:** вывести список ближайших по дате добавления 3-х фильмов и связанные теги:

```python
class ShowMovieView(DetailView):
    model = Movie
    template_name = 'movies/movie_detail.html'
    context_object_name = 'movie'
    slug_url_kwarg = 'movie_slug'

    def get_object(self, queryset=None):
        slug = self.kwargs.get(self.slug_url_kwarg)
        queryset = queryset or self.get_queryset()
        return get_object_or_404(queryset.filter(is_published=True), slug=slug)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        movie = context['movie']
        context['related_movies'] = Movie.objects.filter(
            genres__in=movie.genres.all(),
            is_published=True
        ).exclude(pk=movie.pk).distinct()[:3]
        context['title'] = movie.title
        return context
```

Проверяйте производительность: при получении связанных данных используйте `select_related` / `prefetch_related`, если нужно уменьшить число SQL-запросов.

---

## 6. Обработка ошибок и распространённые проблемы

Ниже — список распространённых ошибок при работе с `DetailView` и способы их исправления.

**Ошибка:** `AttributeError: 'ShowMovieView' object has no attribute 'slug_url_kwarg'`
**Причина:** неправильно использовано имя параметра в URL и в коде.
**Решение:** либо изменить маршрут на `'<slug:slug>/'`, либо задать `slug_url_kwarg = 'movie_slug'`.

---

**Ошибка:** `Http404` при доступе к валидному объекту
**Причина 1:** ваш `get_object()` или `queryset` фильтруют по `is_published=True`, а объект не опубликован.
**Причина 2:** неверный slug/pk в URL.
**Решение:** проверить данные в БД, временно убрать фильтр `is_published` для отладки, убедиться в корректности URL.

---

**Ошибка:** шаблон не видит переменную `movie` (или `object`)
**Причина:** вы использовали другое имя контекста или забыли задать `context_object_name`. По умолчанию доступно `object` и `movie` (имя модели).
**Решение:** либо используйте `{{ object }}`, либо установите `context_object_name = 'movie'`.

---

**Ошибка:** N+1 (много запросов при получении связанных полей)
**Причина:** в шаблоне обращаетесь к `movie.director` или `movie.genres.all()` без предварительного `select_related`/`prefetch_related`.
**Решение:** override `get_queryset()` или задать `queryset = Movie.objects.select_related('director').prefetch_related('genres', 'tags')`.

---

# 7. Проверка в браузере и отладка

1. Пропишите маршрут, как показано выше.
2. Убедитесь, что в базе есть подходящий `Movie` (опубликованный, с нужным slug или pk).
3. Откройте URL:

   - для pk: `http://127.0.0.1:8000/movies/movie/1/`
   - для slug: `http://127.0.0.1:8000/movies/movie/inception-2010/`

4. Если видите 404 — проверьте: существует ли объект в БД, опубликован ли он, совпадает ли slug.
5. Для отладки временно поставьте в `get_object` `print()` или используйте Django Debug Toolbar, чтобы увидеть SQL-запросы и убедиться, что связанные поля подгружаются эффективно.

---

## Практические задания

### Задание 1 — Просмотр фильма по slug с фильтрацией публикации

**Требование:** реализуйте `DetailView`, которое принимает `movie_slug` в URL, показывает только `is_published=True` фильмы, передаёт объект в шаблон как `movie`. Назовите маршрут `movie_detail`.

---

### Задание 2 — Просмотр профиля режиссёра по `pk`, плюс список фильмов режиссёра

**Требование:** создайте `DirectorDetailView` на основе `DetailView`, который принимает `pk` режиссёра, передаёт объект как `director`, и в `context` добавляет `director_movies` — все опубликованные фильмы этого режиссёра.

---

### Задание 3 — DetailView с оптимизацией запросов

**Требование:** реализуйте `ShowMovieViewOptimized`, который выводит `movie` и его `genres` и `directors`, но при этом делает минимум SQL-запросов (используйте `select_related` и `prefetch_related`).

---

## Сравнить решение

### Решение задания 1

**Файл:** `movies/views.py`

```python
from django.views.generic import DetailView
from django.shortcuts import get_object_or_404
from .models import Movie

class ShowMovieView(DetailView):
    model = Movie
    template_name = 'movies/movie_detail.html'
    context_object_name = 'movie'
    slug_url_kwarg = 'movie_slug'

    def get_object(self, queryset=None):
        slug = self.kwargs.get(self.slug_url_kwarg)
        queryset = queryset or self.get_queryset()
        return get_object_or_404(queryset.filter(is_published=True), slug=slug)
```

**Файл:** `movies/urls.py`

```python
path('movie/<slug:movie_slug>/', ShowMovieView.as_view(), name='movie_detail')
```

### Решение задания 2

**Файл:** `directors/views.py` (или `movies/views.py` при объединении)

```python
from django.views.generic import DetailView
from django.shortcuts import get_object_or_404
from .models import Director, Movie

class DirectorDetailView(DetailView):
    model = Director
    template_name = 'directors/director_detail.html'
    context_object_name = 'director'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        director = context['director']
        context['director_movies'] = Movie.objects.filter(directors=director, is_published=True)
        return context
```

**Маршрут:**

```python
path('director/<int:pk>/', DirectorDetailView.as_view(), name='director_detail')
```

**Шаблон (фрагмент):**

```html
<h1>{{ director.name }}</h1>

<h2>Фильмы режиссёра</h2>
<ul>
  {% for m in director_movies %}
  <li>{{ m.title }} ({{ m.year }})</li>
  {% empty %}
  <li>Фильмов не найдено.</li>
  {% endfor %}
</ul>
```

### Решение задания 3

```python
class ShowMovieViewOptimized(DetailView):
    model = Movie
    template_name = 'movies/movie_detail.html'
    context_object_name = 'movie'
    slug_url_kwarg = 'movie_slug'

    def get_queryset(self):
        return Movie.objects.filter(is_published=True).select_related(
            # если у Movie есть FK на director, например primary_director
        ).prefetch_related('genres', 'tags', 'directors')
```

Если у `Movie` несколько режиссёров через M2M, `prefetch_related('directors')` предзагрузит их в два запроса.

# 9. Вопросы для самопроверки

1. По каким ключам `DetailView` пытается найти объект по умолчанию?
2. Как сообщить `DetailView`, что имя параметра slug в маршруте — `movie_slug`?
3. Как в шаблоне обращаться к объекту, если задан `context_object_name = 'movie'`?
4. Как показать только опубликованные фильмы с помощью `DetailView`?
5. Что вернёт `DetailView`, если объект не найден?
6. Как минимизировать число SQL-запросов при чтении связанных полей?
7. Где лучше формировать заголовок страницы — в `get_context_data` или в шаблоне?
8. Можно ли использовать `DetailView` для обработки POST-запроса (например, формы комментария)?
9. Что делает `context_object_name`?
10. Как получить параметр URL внутри метода класса `DetailView`?

---

[Предыдущий урок](lesson48.md) | [Следующий урок](lesson50.md)
