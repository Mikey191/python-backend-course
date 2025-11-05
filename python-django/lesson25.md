# Модуль 4. Урок 25. Добавление тегов на сайт

В прошлом уроке мы познакомились с типом связи **Many-to-Many** и научились связывать фильмы с жанрами.

Теперь мы реализуем ещё один похожий, но чуть более “живой” пример — **теги**.

Теги — это ключевые слова, по которым пользователь может быстро найти нужные материалы.

В нашем случае — фильмы. Например:

* Теги могут быть такими: *«Оскароносные»*, *«Новинки 2025»*, *«Классика»*.
* Один фильм может иметь несколько тегов.
* Один тег может быть связан с множеством фильмов.

---

## Цель урока

В этом уроке мы:

1. Создадим модель `Tag` для хранения тегов.
2. Настроим связь Many-to-Many между фильмами и тегами.
3. Сделаем страницу, где отображаются фильмы по выбранному тегу.
4. Добавим список тегов в сайт (например, в сайдбар).
5. Проверим всё это в браузере.

---

## 1. Создаём модель тегов

Откроем файл `movies/models.py` и добавим модель `Tag`:

```python
from django.db import models
from django.urls import reverse

class Tag(models.Model):
    name = models.CharField(max_length=100, db_index=True)
    slug = models.SlugField(max_length=255, unique=True, db_index=True)

    def get_absolute_url(self):
        return reverse('tag', kwargs={'tag_slug': self.slug})

    def __str__(self):
        return self.name
```

**Разберём подробнее:**

* `name` — название тега, которое будет отображаться пользователям.
* `slug` — короткое имя для URL (например, `"oscars"`).
* `get_absolute_url()` — специальный метод, возвращающий ссылку на страницу этого тега.
  Он пригодится в шаблонах, чтобы удобно формировать ссылки вида `/tag/oscars/`.

---

## 2. Добавляем связь с фильмами

Теперь свяжем фильмы и теги через `ManyToManyField`.

В модель `Movie` добавим новое поле:

```python
class Movie(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    release_year = models.PositiveIntegerField()
    description = models.TextField(blank=True)
    tags = models.ManyToManyField('Tag', blank=True, related_name='movies')

    def __str__(self):
        return self.title
```

После этого создаём и применяем миграции:

```bash
python manage.py makemigrations
python manage.py migrate
```

Теперь в базе появятся:

* таблица `movies_tag` — для тегов;
* промежуточная таблица `movies_movie_tags` — для связи фильмов и тегов.

---

## 3. Настраиваем маршрут для тегов

Теперь нам нужно сделать страницу, на которой будут отображаться фильмы с определённым тегом.

Откроем `movies/urls.py` и добавим новый маршрут:

```python
from django.urls import path
from . import views

urlpatterns = [
    # другие маршруты
    path('tag/<slug:tag_slug>/', views.show_tag_movies, name='tag'),
]
```

---

## 4. Создаём представление для тегов

Добавим в `movies/views.py` новое представление:

```python
from django.shortcuts import render, get_object_or_404
from .models import Movie, Tag

def show_tag_movies(request, tag_slug):
    tag = get_object_or_404(Tag, slug=tag_slug)
    movies = tag.movies.all()  # все фильмы с этим тегом

    context = {
        'title': f'Фильмы по тегу: {tag.name}',
        'tag': tag,
        'movies': movies,
    }
    return render(request, 'movies/tag_movies.html', context)
```

**Что делает этот код:**

* Находит тег по `slug`.
* Получает все фильмы, связанные с этим тегом (`tag.movies.all()` — благодаря `related_name='movies'`).
* Передаёт данные в шаблон для отображения.

---

## 5. Создаём шаблон для фильмов по тегу

Создадим новый файл `movies/templates/movies/tag_movies.html`:

```html
{% extends 'base.html' %}

{% block content %}
<h2>{{ title }}</h2>

{% if movies %}
  <ul>
  {% for movie in movies %}
    <li>
      <a href="{% url 'movie_detail' movie.slug %}">{{ movie.title }}</a>
    </li>
  {% endfor %}
  </ul>
{% else %}
  <p>Пока нет фильмов с этим тегом.</p>
{% endif %}
{% endblock %}
```

**Здесь**:

* Мы отображаем список фильмов, связанных с тегом.
* Если фильмов нет — выводим сообщение об этом.

---

## 6. Добавляем список тегов в сайдбар

Чтобы пользователи могли видеть все доступные теги, создадим **шаблонный тег**.

---

### Шаг 1. Создаём модуль для шаблонных тегов

В папке `movies` создаём файл `movies_tags.py`:

```python
from django import template
from movies.models import Tag

register = template.Library()

@register.inclusion_tag('movies/list_tags.html')
def show_all_tags():
    return {"tags": Tag.objects.all()}
```

Этот тег будет возвращать список всех тегов для отображения в отдельном шаблоне.

---

### Шаг 2. Создаём шаблон списка тегов

Файл `movies/templates/movies/list_tags.html`:

```html
{% if tags %}
<div class="tags-block">
  <p><strong>Теги:</strong></p>
  <ul class="tags-list">
    {% for t in tags %}
      <li><a href="{{ t.get_absolute_url }}">{{ t.name }}</a></li>
    {% endfor %}
  </ul>
</div>
{% endif %}
```

---

### Шаг 3. Подключаем список тегов в `base.html`

Вставим вызов шаблонного тега в базовый шаблон (например, в сайдбар):

```html
{% load movies_tags %}

<aside>
  {% show_all_tags %}
</aside>
```

Теперь на каждой странице будет отображаться список всех тегов с ссылками.

---

## 7. Проверка в браузере

1. Перейдите в **панель администратора Django**.
2. Добавьте несколько тегов:

   * «Оскар»
   * «Новинки 2025»
   * «Топ IMDb»
3. Привяжите их к нескольким фильмам.
4. Откройте страницу любого фильма и убедитесь, что теги отображаются.
5. Нажмите на тег — должна открыться страница с фильтрами по этому тегу.

---

## Возможные ошибки

**Ошибка 1.**

```
TemplateSyntaxError: 'movies_tags' is not a registered tag library
```

Убедитесь, что файл `movies_tags.py` находится в папке приложения (`movies`)
и в шаблоне вы загрузили его с помощью `{% load movies_tags %}`.

---

**Ошибка 2.**

```
NoReverseMatch: Reverse for 'tag' not found
```

Проверьте, что маршрут `path('tag/<slug:tag_slug>/', ...)` действительно существует и у него указано имя `name='tag'`.

---

**Ошибка 3.**
Теги не отображаются на странице.
Проверьте, вызван ли шаблонный тег в `base.html`:

```html
{% show_all_tags %}
```

и что вы подключили `{% load movies_tags %}`.

---

## Практические задания

### Задание 1

Создайте 3 тега:

* "Классика"
* "Фильмы с Оскаром"
* "Новинки 2025"

Добавьте к фильму «Титаник» теги «Классика» и «Фильмы с Оскаром».
Откройте `/tag/klassika/` и проверьте, что фильм отображается.

---

### Задание 2

Создайте тег «Блокбастеры» и привяжите его сразу к нескольким фильмам.
Проверьте, что все эти фильмы отображаются при переходе по ссылке на тег.

---

### Задание 3

Добавьте новый тег в базу, но не привязывайте его ни к одному фильму.
Откройте страницу тега — что вы видите?

---

### Задание 4

Попробуйте удалить тег, который привязан к нескольким фильмам.
Проверьте, что произойдёт при удалении — фильмы не пропадут, просто связь удалится.

---

## Вопросы

1. Для чего используется связь Many-to-Many между фильмами и тегами?
2. Что делает метод `get_absolute_url()` в модели `Tag`?
3. Как получить все фильмы, связанные с конкретным тегом через ORM?
4. Почему для шаблонных тегов создаётся отдельный модуль?
5. Что делает декоратор `@register.inclusion_tag()`?
6. Что произойдёт, если тег не связан ни с одним фильмом?
7. Почему важно использовать `related_name` при Many-to-Many?
8. Как Django формирует URL при вызове `t.get_absolute_url`?
9. Что нужно сделать, если Django не находит наш шаблонный тег?
10. Чем шаблонный тег отличается от обычного вызова контекста?

---

[Предыдущий урок](lesson24.md) | [Следующий урок](lesson26.md)