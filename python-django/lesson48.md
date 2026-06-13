# Модуль 8. Урок 48. Класс ListView в Django

## Введение: зачем нам ListView

В предыдущем уроке мы познакомились с фундаментом системы Class-Based Views — классами `View` и `TemplateView`. Теперь мы переходим к следующему важному этапу — изучению классов обобщённых представлений (Generic Class-Based Views).

Одним из самых часто используемых классов в Django является **ListView**. Он предназначен для отображения списков объектов — фильмов, актёров, режиссёров, жанров и любых других сущностей.

В проекте **cinemahub** списки объектов встречаются повсюду: на главной странице выводятся последние опубликованные фильмы, в каталогах — жанры, подборки, участники съёмочной группы. Такие представления легко создавать вручную, но при этом возникает множество повторяющихся фрагментов кода:

* Получение списка объектов модели
* Подготовка контекста
* Создание структуры пагинации
* Проверка пустого результата

`ListView` делает всё это за нас. Наша задача — лишь правильно настроить этот класс.

---

## 1. Создание простого ListView

### 1.1. Подключение класса

Класс `ListView` находится в модуле `django.views.generic.list`. Чтобы использовать его, импортируем:

**Файл:** `movies/views.py`

```python
from django.views.generic import ListView
```

---

### 1.2. Первый пример: вывод всех фильмов

Создадим представление, которое показывает список всех опубликованных фильмов в проекте.

**Файл:** `movies/views.py`

```python
from django.views.generic import ListView
from .models import Movie

class MoviesListView(ListView):
    model = Movie
```

Если запустить сервер и попытаться открыть это представление (его мы подключим позже), то Django попытается автоматически найти шаблон с именем:

```
movies/movie_list.html
```

Появление ошибки `TemplateDoesNotExist` на этом этапе — абсолютно нормальное поведение. Django использует строгие правила именования, чтобы не заставлять разработчика писать одинаковую конфигурацию вручную.

---

### 1.3. Создаём шаблон

Создадим минимальный шаблон, чтобы убедиться, что всё работает.

**Файл:** `movies/templates/movies/movie_list.html`

```html
<h1>Список фильмов</h1>

<ul>
    {% for movie in object_list %}
        <li>{{ movie.title }} ({{ movie.year }})</li>
    {% empty %}
        <li>Фильмов пока нет.</li>
    {% endfor %}
</ul>
```

Обратите внимание — `ListView` передаёт список объектов в шаблон под названием **object_list**. Это стандартное имя, которое мы можем заменить, если это необходимо.

---

### 1.4. Подключаем маршрут

**Файл:** `movies/urls.py`

```python
from django.urls import path
from .views import MoviesListView

urlpatterns = [
    path('all/', MoviesListView.as_view(), name='movies_all'),
]
```

Теперь открываем в браузере:

```
http://127.0.0.1:8000/movies/all/
```

Ожидаемый результат:

* если в базе уже есть фильмы — будет показан список;
* если фильмов нет — увидим сообщение их отсутствии.

Если видите ошибку:

```
TemplateDoesNotExist: movies/movie_list.html
```

— значит шаблон не находится по пути `movies/templates/movies/movie_list.html`.

---

## 2. Использование собственного шаблона

В cinemahub разные страницы могут использовать общие элементы оформления, поэтому иногда нужно явно указать шаблон.

Добавим параметр `template_name`:

**Файл:** `movies/views.py`

```python
class MoviesListView(ListView):
    model = Movie
    template_name = 'movies/index.html'
```

Теперь Django будет использовать `movies/index.html` вместо шаблона по умолчанию.

Чтобы данные отображались, в шаблоне должен использоваться `object_list` или другое имя, которое мы зададим.

---

## 3. Переименование переменной object_list

Чтобы передавать данные под удобным именем, используем атрибут `context_object_name`.

**Файл:** `movies/views.py`

```python
class MoviesListView(ListView):
    model = Movie
    template_name = 'movies/index.html'
    context_object_name = 'movies'
```

Теперь в шаблоне мы можем писать:

```html
{% for movie in movies %}
    ...
{% endfor %}
```

---

## 4. Передача дополнительных статичных данных

Иногда нужно передать вместе со списком фильмов дополнительные значения, например заголовок страницы.

Для статичных данных подходит `extra_context`:

```python
extra_context = {
    'title': 'Каталог фильмов'
}
```

Полная версия:

```python
class MoviesListView(ListView):
    model = Movie
    template_name = 'movies/index.html'
    context_object_name = 'movies'
    extra_context = {'title': 'Каталог фильмов'}
```

Но важно помнить: `extra_context` подходит только для неизменяемых значений. Если нужно передать динамические данные — используем `get_context_data`.

---

## 5. Динамические данные: переопределение get_context_data

Добавим в контекст, например, количество опубликованных фильмов.

**Файл:** `movies/views.py`

```python
class MoviesListView(ListView):
    model = Movie
    template_name = 'movies/index.html'
    context_object_name = 'movies'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['movies_count'] = Movie.objects.filter(is_published=True).count()
        context['title'] = 'Каталог фильмов'
        return context
```

Важно:

* обязательно вызываем `super().get_context_data(**kwargs)`
* не забываем вернуть `context`

Если забыть вызвать `super()`, список объектов не попадёт в шаблон.

---

## 6. Фильтрация списка: переопределение get_queryset

По умолчанию `ListView` выбирает все объекты модели. Но в проекте cinemahub большинство страниц работает только с опубликованными фильмами.

Создадим представление, которое показывает только опубликованные фильмы, отсортированные по дате создания (сначала новые):

```python
class MoviesListView(ListView):
    template_name = 'movies/index.html'
    context_object_name = 'movies'

    def get_queryset(self):
        return Movie.objects.filter(is_published=True).order_by('-created_at')
```

Теперь Django будет использовать результат этого метода вместо `Movie.objects.all()`.

---

## 7. ListView для жанров, режиссёров и других сущностей

Рассмотрим практический пример: вывод фильмов по жанру.

URL будет выглядеть так:

```
/movies/genre/<slug>/
```

---

### 7.1. Представление фильмов по жанру

**Файл:** `movies/views.py`

```python
class MoviesByGenreView(ListView):
    template_name = 'movies/genre_list.html'
    context_object_name = 'movies'
    allow_empty = False

    def get_queryset(self):
        return Movie.objects.filter(
            is_published=True,
            genres__slug=self.kwargs['genre_slug']
        ).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        genre = context['movies'][0].genres.all()[0]
        context['title'] = f'Фильмы жанра: {genre.name}'
        return context
```

### Объяснение:

* `allow_empty = False` — если жанр пуст, Django вернёт ошибку 404.
* `self.kwargs['genre_slug']` — берём slug из URL.
* в `get_context_data` берём первый найденный фильм и его первый жанр для формирования заголовка.

---

### 7.2. Подключаем маршрут

**Файл:** `movies/urls.py`

```python
path('genre/<slug:genre_slug>/', MoviesByGenreView.as_view(), name='movies_by_genre')
```

---

### 7.3. Шаблон списка фильмов жанра

**Файл:** `movies/templates/movies/genre_list.html`

```html
<h1>{{ title }}</h1>

<ul>
    {% for movie in movies %}
        <li>{{ movie.title }} ({{ movie.year }})</li>
    {% endfor %}
</ul>
```

---

## 8. Проверка работы и возможные ошибки

### Ошибка 1: TemplateDoesNotExist

Причины:

* неправильный путь к шаблону
* другая вложенность папок
* не тот файл указан в `template_name`

Проверка:

* убедитесь, что файл находится по пути, указанному в ошибке
* в проектах Django путь всегда идёт от папки `templates`

---

### Ошибка 2: 'movies' is empty when allow_empty = False

Причина:

* жанра с таким slug нет
* жанр есть, но фильмы отсутствуют

Решение:

* проверьте данные в БД
* временно поставьте `allow_empty = True` для отладки

---

### Ошибка 3: KeyError: 'genre_slug'

Причина:

* неправильное имя параметра в `path()`
* неправильное имя в `self.kwargs[]`

Должны совпадать:

```python
path('genre/<slug:genre_slug>/', ...)
self.kwargs['genre_slug']
```

---

## Практические задания

### Задание 1

Создайте ListView, которое выводит список всех актёров (`Actor`).
Отобразите:

* имя актёра,
* год рождения (если указан в ActorProfile),
* сортировку выполните по имени.

Название переменной контекста должно быть `actors`.
Шаблон — `actors/actor_list.html`.

---

### Задание 2

Создайте ListView, которое выводит список режиссёров (`Director`), у которых есть профиль (`DirectorProfile`).

В контекст добавьте:

* `title = "Режиссёры с профилями"`

Контекстная переменная — `directors`.

---

### Задание 3

Создайте ListView, которое выводит фильмы, выпущенные после года, указанного в URL:

```
/movies/year/<int:year>/
```

Контекстное имя — `movies`.
Шаблон любой (например, `movies/by_year.html`).

---

## Сравнить решение

### Решение задания 1

**Файл:** `actors/views.py`

```python
from django.views.generic import ListView
from .models import Actor

class ActorsListView(ListView):
    model = Actor
    template_name = 'actors/actor_list.html'
    context_object_name = 'actors'

    def get_queryset(self):
        return Actor.objects.all().order_by('name')
```

**Файл:** `actors/templates/actors/actor_list.html`

```html
<h1>Список актёров</h1>

<ul>
    {% for actor in actors %}
        <li>
            {{ actor.name }}
            {% if actor.actorprofile %}
                — {{ actor.actorprofile.birthday.year }}
            {% endif %}
        </li>
    {% empty %}
        <li>Актёров пока нет.</li>
    {% endfor %}
</ul>
```

---

### Решение задания 2

**Файл:** `directors/views.py`

```python
from django.views.generic import ListView
from .models import Director

class DirectorsWithProfileView(ListView):
    template_name = 'directors/with_profile.html'
    context_object_name = 'directors'

    def get_queryset(self):
        return Director.objects.filter(directorprofile__isnull=False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Режиссёры с профилями"
        return context
```

**Файл:** `directors/templates/directors/with_profile.html`

```html
<h1>{{ title }}</h1>

<ul>
    {% for director in directors %}
        <li>{{ director.name }}</li>
    {% endfor %}
</ul>
```

---

### Решение задания 3

**Файл:** `movies/views.py`

```python
class MoviesByYearView(ListView):
    template_name = 'movies/by_year.html'
    context_object_name = 'movies'

    def get_queryset(self):
        year = self.kwargs['year']
        return Movie.objects.filter(year__gt=year, is_published=True).order_by('year')
```

---

## Вопросы

1. Как Django определяет имя шаблона по умолчанию для ListView?
2. Какое имя переменной используется для списка объектов, если не указано `context_object_name`?
3. В каких случаях стоит использовать `extra_context`, а в каких — `get_context_data`?
4. Что произойдёт, если забыть вызвать `super().get_context_data()`?
5. Как получить переменную из URL внутри ListView?
6. Зачем используется параметр `allow_empty`?
7. Чем отличается `get_queryset` от `model = ...`?
8. Что нужно сделать, если Django выдаёт `TemplateDoesNotExist`?
9. Можно ли передавать динамические данные через `extra_context`? Почему?
10. Что вернёт `ListView`, если фильтр вернул пустой список и `allow_empty = False`?

---

[Предыдущий урок](lesson47.md) | [Следующий урок](lesson49.md)