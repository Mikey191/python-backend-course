# Урок 12. Слаги в URL. get_absolute_url(). Django Debug Toolbar

## Проблема числовых ID в URL

Сейчас страница фильма выглядит так: `/films/1/`. Это работает, но не очень удобно — ни для пользователей, ни для поисковых систем. Сравни:

```
/films/1/
/films/krestnyj-otec/
```

Второй вариант — `slug` (слаг) — читаем, запоминаем и хорошо индексируется поисковиками. Мы уже добавили поле `slug` в модель `Film` в уроке 8, но до сих пор не использовали его по назначению.

---

## Что такое slug

Slug — это строка, состоящая только из латинских букв, цифр, дефисов и подчёркиваний. Она безопасна для использования в URL без дополнительного кодирования.

В модели мы уже описали поле:

```python
slug = models.SlugField(max_length=200, unique=True, blank=True)
```

`SlugField` — это, по сути, `CharField` с автоматической валидацией формата. На уровне базы данных он хранится как обычная строка.

### Автоматическая генерация слага

Стандартная функция `slugify()` из Django отлично работает с латиницей, но **не выполняет транслитерацию кириллицы**.

```python
from django.utils.text import slugify

slugify('The Godfather')
# 'the-godfather'

slugify('Крёстный отец')
# ''
```

Причина в том, что по умолчанию `slugify()` удаляет все символы, не входящие в ASCII.

Можно использовать параметр `allow_unicode=True`, тогда кириллица сохранится:

```python
slugify('Крёстный отец', allow_unicode=True)
# 'крёстный-отец'
```

Однако на практике чаще используют **латинские slug**, поскольку они лучше подходят для URL и не требуют кодирования национальных символов.

Для автоматической транслитерации удобно использовать библиотеку **python-slugify**.

---

Установим библиотеку:

```bash
pip install python-slugify
```

Она автоматически транслитерирует кириллицу в латиницу.

```python
from slugify import slugify

slugify('Крёстный отец')
# 'krestnyi-otets'

slugify('Иван Васильевич меняет профессию')
# 'ivan-vasilevich-meniaet-professiiu'
```

### Автогенерация в методе save()

Самый удобный способ — генерировать slug автоматически при сохранении, если он не указан явно. Переопределяем метод `save()` модели:

```python
# films/models.py
from slugify import slugify


class Film(models.Model):
    title = models.CharField(max_length=200, verbose_name='Название')
    year = models.PositiveIntegerField(verbose_name='Год выпуска')
    description = models.TextField(blank=True, verbose_name='Описание')
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=0.0)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    director = models.ForeignKey(
        Director, on_delete=models.SET_NULL, null=True, blank=True, related_name='films'
    )
    genres = models.ManyToManyField(Genre, blank=True, related_name='films')
    actors = models.ManyToManyField(Actor, blank=True, related_name='films')

    objects = FilmManager()

    class Meta:
        ordering = ['-year']
        verbose_name = 'Фильм'
        verbose_name_plural = 'Фильмы'

    def __str__(self):
        return f'{self.title} ({self.year})'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
```

Теперь при создании фильма без явного slug он сгенерируется автоматически:

```python
film = Film.objects.create(title='Крёстный отец', year=1972)
print(film.slug)
# 'krestnyi-otets'
```

### Почему именно `python-slugify`?

Для проекта с русскими названиями есть несколько способов решения генерации слага. Библиотека `pytils`, `django-slugify-unicode-cyrillic` или `python-slugify`.

Но сейчас `python-slugify` стала фактически стандартом для подобных задач.

Она поддерживает множество языков, умеет корректно транслитерировать кириллицу и не зависит от Django, поэтому пригодится и в других проектах (например, на FastAPI, Flask или обычном Python).

| Библиотека                      | Поддерживается       | Качество транслитерации | Использование                    |
| ------------------------------- | -------------------- | ----------------------- | -------------------------------- |
| **python-slugify**              | активно            | Отличное                | Очень популярна                  |
| pytils                          | редко обновляется | Хорошее                 | В основном старые Django-проекты |
| django-slugify-unicode-cyrillic | нишевая           | Хорошее                 | Практически не используется      |

---

---

## Метод get_absolute_url()

Сейчас, чтобы получить URL фильма, нужно помнить, какой маршрут за это отвечает, и вызывать `reverse()` каждый раз:

```python
reverse('films:film_detail', kwargs={'slug': film.slug})
```

Django предоставляет соглашение для упрощения этого: метод `get_absolute_url()` на самой модели. Если он определён, объект сам знает свой URL:

```python
# films/models.py
from django.urls import reverse


class Film(models.Model):
    # ... поля ...

    def get_absolute_url(self):
        return reverse('films:film_detail', kwargs={'slug': self.slug})
```

Теперь в шаблонах и коде можно писать короче:

```html
<!-- Вместо {% url 'films:film_detail' slug=film.slug %} -->
<a href="{{ film.get_absolute_url }}">{{ film.title }}</a>
```

```python
# В представлениях
return redirect(film.get_absolute_url())
```

Преимущество в том, что логика построения URL хранится один раз — на самой модели, а не размазана по шаблонам и представлениям, которые должны знать имя маршрута и список нужных параметров.

> **Полезная деталь:** административная панель Django (модуль 4) автоматически использует `get_absolute_url()`, чтобы добавить кнопку «Просмотр на сайте» прямо в форме редактирования объекта.

---

## Меняем маршрут на slug

Обновляем `films/urls.py`, заменяя `<int:film_id>` на `<slug:slug>`:

```python
# films/urls.py
from django.urls import path
from . import views

app_name = 'films'

urlpatterns = [
    path('', views.index, name='index'),
    path('about/', views.about, name='about'),
    path('films/', views.film_list, name='film_list'),
    path('films/search/', views.search_film, name='search_film'),
    path('films/add/', views.add_film, name='add_film'),
    path('films/<slug:slug>/', views.film_detail, name='film_detail'),
    path('directors/<int:director_id>/', views.director_detail, name='director_detail'),
    path('stats/', views.catalog_stats, name='catalog_stats'),
]
```

И представление:

```python
# films/views.py
def film_detail(request, slug):
    film = get_object_or_404(
        Film.objects.select_related('director').prefetch_related('genres', 'actors'),
        slug=slug
    )

    FilmStats.objects.filter(film=film).update(views_count=F('views_count') + 1)

    return render(request, 'films/film_detail.html', {'film': film})
```

Обновляем все обращения к `film_detail` в шаблонах — теперь они используют `get_absolute_url()`:

```html
<!-- films/templates/films/includes/film_card.html -->
<div>
    <h3><a href="{{ film.get_absolute_url }}">{{ film.title }}</a></h3>
    <p>Год: {{ film.year }}</p>
    <p>{{ film.description|default:"Нет описания"|truncatechars:80 }}</p>
</div>
```

```html
<!-- films/templates/films/includes/latest_films.html -->
<div>
    <h3>Последние добавленные</h3>
    <ul>
    {% for film in films %}
        <li><a href="{{ film.get_absolute_url }}">{{ film.title }}</a></li>
    {% empty %}
        <li>Фильмов пока нет.</li>
    {% endfor %}
    </ul>
</div>
```

---

## Django Debug Toolbar

Мы несколько раз упоминали проблему N+1 и обещали увидеть её наглядно. Сейчас этот момент настал.

### Установка

```bash
pip install django-debug-toolbar
```

### Настройка

```python
# filmsite/settings.py
INSTALLED_APPS = [
    # ...
    'debug_toolbar',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',  # добавляем после Security
    'django.contrib.sessions.middleware.SessionMiddleware',
    # ... остальные middleware
]

INTERNAL_IPS = [
    '127.0.0.1',
]
```

Подключаем маршруты панели — только в режиме разработки:

```python
# filmsite/urls.py
from django.conf import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('films.urls')),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
    ]
```

Перезапускаем сервер и открываем любую страницу — справа появляется панель с вкладками: SQL, Templates, Cache, Static files и другие.

### Вкладка SQL — находим N+1

Откроем страницу каталога `/films/` без `prefetch_related` и посмотрим вкладку SQL:

```python
# Намеренно «плохая» версия — для демонстрации проблемы
def film_list(request):
    films = Film.objects.all()  # без select_related/prefetch_related
    return render(request, 'films/film_list.html', {'films': films})
```

Если шаблон `film_card.html` обращается к `film.genres.all()` для каждого фильма — Debug Toolbar покажет десятки похожих запросов вместо одного. Каждая строка в списке SQL-запросов — это отдельный JOIN, который можно было сделать один раз.

Теперь применим `prefetch_related` и сравним:

```python
def film_list(request):
    films = Film.objects.select_related('director').prefetch_related('genres', 'actors')
    return render(request, 'films/film_list.html', {'films': films})
```

Количество запросов падает с «количество фильмов + 1» до 3 запросов суммарно — независимо от того, сколько фильмов в каталоге.

### Другие полезные вкладки

| Вкладка | Что показывает |
|---|---|
| **SQL** | Список всех SQL-запросов, их время выполнения, дублирующиеся запросы (подсвечиваются) |
| **Templates** | Какие шаблоны использовались и какой контекст в них передан |
| **Time** | Время выполнения представления по этапам |
| **Static files** | Список загруженных статических файлов |

---

## Подводные камни

### Дублирующиеся слаги

`unique=True` защищает от дублей на уровне базы данных, но если два фильма имеют одинаковое название — `slugify()` сгенерирует одинаковый slug, и второй `save()` упадёт с ошибкой целостности. Решение — добавлять уникальный суффикс при коллизии:

```python
def save(self, *args, **kwargs):
    if not self.slug:
        base_slug = slugify(self.title)
        slug = base_slug
        counter = 1
        while Film.objects.filter(slug=slug).exclude(pk=self.pk).exists():
            slug = f'{base_slug}-{counter}'
            counter += 1
        self.slug = slug
    super().save(*args, **kwargs)
```

### Debug Toolbar нельзя оставлять в продакшне

Панель показывает SQL-запросы, структуру шаблонов и внутренние детали приложения — серьёзная утечка информации, если показать её обычным пользователям. Условие `if settings.DEBUG` в `urls.py` — обязательное, не опциональное.

### get_absolute_url() и смена slug

Если slug меняется (например, при редактировании названия фильма), все ранее сохранённые ссылки на старый URL перестают работать. На продакшн-сайтах эту проблему решают через редиректы со старого slug на новый — для учебного проекта пока не критично, но важно знать о такой ловушке.

---

## Итоговая модель Film

```python
# films/models.py
from django.db import models
from django.db.models import Q
from django.urls import reverse
from slugify import slugify


class FilmManager(models.Manager):

    def high_rated(self):
        return self.filter(rating__gte=8.0)

    def by_year(self, year):
        return self.filter(year=year)

    def recent(self, count=5):
        return self.order_by('-created_at')[:count]

    def search(self, query):
        return self.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(director__name__icontains=query)
        ).distinct()


class Film(models.Model):
    title = models.CharField(max_length=200, verbose_name='Название')
    year = models.PositiveIntegerField(verbose_name='Год выпуска')
    description = models.TextField(blank=True, verbose_name='Описание')
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=0.0, verbose_name='Рейтинг')
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата добавления')

    director = models.ForeignKey(
        'Director', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='films', verbose_name='Режиссёр'
    )
    genres = models.ManyToManyField('Genre', blank=True, related_name='films', verbose_name='Жанры')
    actors = models.ManyToManyField('Actor', blank=True, related_name='films', verbose_name='Актёры')

    objects = FilmManager()

    class Meta:
        ordering = ['-year']
        verbose_name = 'Фильм'
        verbose_name_plural = 'Фильмы'

    def __str__(self):
        return f'{self.title} ({self.year})'

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while Film.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f'{base_slug}-{counter}'
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('films:film_detail', kwargs={'slug': self.slug})
```

---

## Вопросы для проверки

1. Зачем использовать slug в URL вместо числового id?
2. Зачем нужен метод `get_absolute_url()`, если можно вызвать `reverse()` напрямую?
3. Что показывает Django Debug Toolbar на вкладке SQL и как это помогает находить проблему N+1?
4. Почему нельзя оставлять Django Debug Toolbar включённым в продакшне?
5. Что произойдёт при попытке сохранить два фильма с одинаковым названием без явного slug? Как это исправить?

---

## Практическая задача

**Тип: расширь проект**

**Часть 1.** Сделай то же самое для модели `Director`, что мы сделали для `Film`:
- Добавь поле `slug` (`SlugField`, `unique=True`, `blank=True`)
- Переопредели `save()` для автогенерации slug с защитой от коллизий
- Добавь метод `get_absolute_url()`, который возвращает URL вида `/directors/<slug>/`

**Часть 2.** Обнови маршрут `directors/<int:director_id>/` на `directors/<slug:slug>/` и соответствующее представление `director_detail`.

**Часть 3.** Замени везде в шаблонах прямые вызовы `{% url 'films:director_detail' director_id=... %}` на `{{ director.get_absolute_url }}`.

После выполнения создай и примени миграцию.

---

[Предыдущий урок](lesson11.md) | [Следующий урок](lesson13.md)