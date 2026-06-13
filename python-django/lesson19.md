# Модуль 3. Урок 19. Слаги (slug) в URL-адресах и метод get_absolute_url()

Когда пользователь открывает страницу фильма на сайте, в адресной строке браузера мы обычно видим не что-то вроде:

```
https://cinemahub.com/movies/23/
```

а более понятный и "человеческий" адрес:

```
https://cinemahub.com/movies/interstellar/
```

Вот этот последний фрагмент (`interstellar`) и называется **slug** — короткое, уникальное, читаемое название для URL.

Оно обычно формируется из латинских букв, цифр и дефисов, и помогает пользователям (и поисковым системам) лучше понимать, что находится на странице.

---

## Что такое Slug и зачем он нужен

Slug — это строка, которая служит **уникальным идентификатором записи в URL**.
Он похож на `id`, но при этом более дружелюбен к пользователю. Например:

| Запись       | URL с ID      | URL со slug             |
| ------------ | ------------- | ----------------------- |
| Интерстеллар | `/movies/23/` | `/movies/interstellar/` |
| Начало       | `/movies/24/` | `/movies/inception/`    |

Таким образом, slug — это часть SEO и удобства навигации.

---

## Добавляем slug в модель

Откроем модель `Movie` в `models.py` и добавим новое поле `slug`:

```python
from django.db import models

class Movie(models.Model):
    title = models.CharField(max_length=255, verbose_name="Название")
    slug = models.SlugField(max_length=255, db_index=True, blank=True, default='', verbose_name="URL")
    description = models.TextField(blank=True, verbose_name="Описание")
    release_year = models.IntegerField(default=2000, verbose_name="Год выпуска")

    def __str__(self):
        return self.title
```

Теперь выполним миграции, чтобы Django добавил это поле в базу данных:

```bash
python manage.py makemigrations
python manage.py migrate
```

---

## Заполняем slug для существующих фильмов

Если фильмы уже есть в базе данных, им нужно выдать временные slug.
Откроем интерактивную оболочку Django:

```bash
python manage.py shell
```

и выполним:

```python
from movies.models import Movie

for movie in Movie.objects.all():
    movie.slug = f"movie-{movie.pk}"
    movie.save()
```

Теперь у всех фильмов появится уникальный slug вроде `movie-1`, `movie-2` и т.д.

После этого можно **запретить пустые значения** и **установить уникальность**, чтобы в будущем нельзя было создать два одинаковых slug:

```python
slug = models.SlugField(max_length=255, db_index=True, unique=True, verbose_name="URL")
```

И снова применяем миграции:

```bash
python manage.py makemigrations
python manage.py migrate
```

---

## Делаем страницы фильмов доступными по slug

Теперь давайте настроим так, чтобы фильм открывался по адресу `/movies/interstellar/`, а не `/movies/23/`.

Откроем файл `movies/urls.py` и добавим маршрут:

```python
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='home'),
    path('movie/<slug:movie_slug>/', views.show_movie, name='movie'),
]
```

Здесь `<slug:movie_slug>` — это динамическая часть URL, в которую Django будет подставлять значение `slug` конкретного фильма.

Теперь обновим `views.py`:

```python
from django.shortcuts import render, get_object_or_404
from .models import Movie

def show_movie(request, movie_slug):
    movie = get_object_or_404(Movie, slug=movie_slug)
    return render(request, 'movies/movie_detail.html', {'movie': movie})
```

Теперь можно открыть в браузере:

```
http://127.0.0.1:8000/movie/interstellar/
```

и увидеть страницу фильма.

---

## Метод get_absolute_url()

Когда мы работаем с шаблонами, нам часто нужно создавать ссылки на конкретный объект.

Например, в списке фильмов (`index.html`) мы хотим сделать кнопку «Подробнее»:

```html
<a href="/movie/interstellar/">Подробнее</a>
```

Но если в будущем мы изменим маршруты, нам придется переписывать все ссылки.
Чтобы избежать этого, Django предлагает **метод `get_absolute_url()`**.

Добавим его в нашу модель `Movie`:

```python
from django.urls import reverse

class Movie(models.Model):
    title = models.CharField(max_length=255, verbose_name="Название")
    slug = models.SlugField(max_length=255, db_index=True, unique=True, verbose_name="URL")
    description = models.TextField(blank=True, verbose_name="Описание")
    release_year = models.IntegerField(default=2000, verbose_name="Год выпуска")

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('movie', kwargs={'movie_slug': self.slug})
```

Теперь Django сам подставит нужный URL, когда мы вызовем этот метод.

---

## Пример использования в шаблоне

В шаблоне `index.html`, где мы отображаем список фильмов, теперь можно использовать:

```html
{% for movie in movies %}
  <h2>{{ movie.title }}</h2>
  <p>{{ movie.description|truncatewords:20 }}</p>
  <a href="{{ movie.get_absolute_url }}">Подробнее</a>
{% endfor %}
```

Django автоматически построит правильный адрес для каждого фильма.

Если вы поменяете структуру маршрутов в `urls.py`, всё продолжит работать без изменений в шаблонах.

---

## Проверяем в браузере

1. Перейдите на главную страницу `/movies/`.
2. Кликните на ссылку **"Подробнее"**.
3. Проверьте, что открывается страница конкретного фильма.
4. Попробуйте вручную ввести адрес `/movie/interstellar/` — убедитесь, что Django находит нужный фильм.

---

## Почему get_absolute_url() так важен

Метод `get_absolute_url()` — это стандарт Django.

Его используют не только в шаблонах, но и во встроенных механизмах, например, в админке или при сериализации объектов.

Он позволяет централизованно управлять URL — если вы когда-нибудь решите поменять структуру маршрутов, всё продолжит работать.

Это мощный инструмент, который делает код **устойчивым к изменениям** и **удобным для расширения**.

---

## Практические задания

1. **Добавьте slug** в модель `Genre`, чтобы жанры фильмов также открывались по URL вида `/genre/drama/`.
2. **Создайте шаблон** `genre_detail.html`, который отображает все фильмы этого жанра.
3. **Добавьте метод `get_absolute_url()`** в модель `Genre`.
4. **Проверьте**, что при клике на жанр в списке фильмов вы переходите на его страницу.
5. **Измените slug** одного из фильмов вручную через shell и убедитесь, что ссылка на фильм автоматически обновилась.
6. **Попробуйте ввести несуществующий slug** в адресной строке — посмотрите, как работает `get_object_or_404`.

---

## Вопросы для самопроверки

1. Что такое slug и зачем он используется в Django?
2. Почему slug должен быть уникальным?
3. Как добавить slug в модель и сделать его обязательным?
4. Что делает метод `get_absolute_url()`?
5. Почему в `get_absolute_url()` мы используем функцию `reverse()`?
6. Как в шаблоне получить ссылку на конкретный объект модели?
7. Что произойдет, если вызвать `get_object_or_404()` с несуществующим slug?
8. Чем slug лучше числового ID в URL?
9. Можно ли изменить slug после создания записи? Что произойдет со старыми ссылками?
10. Почему важно централизованно управлять URL через `get_absolute_url()`?

---

[Предыдущий урок](lesson18.md) | [Следующий урок](lesson20.md)