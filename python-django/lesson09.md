# Урок 9. CRUD через Django ORM. Field Lookups. Пользовательский менеджер модели

## Django shell — интерактивная работа с ORM

Прежде чем писать код в представлениях, удобно проверять ORM-запросы в интерактивной оболочке. Django предоставляет расширенную версию Python shell, в которой уже настроено окружение проекта:

```bash
python manage.py shell
```

Все примеры этого урока можно запускать прямо в shell. Начнём с импорта модели:

```python
from films.models import Film, Genre
```

---

## Manager и QuerySet

Прежде чем разбирать CRUD, важно понять два ключевых объекта Django ORM.

**Manager** — это точка входа для работы с таблицей через ORM. По умолчанию Django создаёт менеджер с именем `objects` для каждой модели. Через него мы и делаем все запросы:

```python
Film.objects   # это менеджер
```

**QuerySet** — это ленивый запрос к базе данных. Большинство методов менеджера возвращают QuerySet, а не список объектов. SQL выполняется только в момент обращения к данным: при итерации, срезе или явном приведении к списку.

```python
qs = Film.objects.filter(year__gt=2000)  # SQL ещё не выполнен
films = list(qs)                          # вот здесь выполнился SELECT
```

Это важно понимать при отладке: напечатать QuerySet в shell — это тоже момент выполнения запроса.

> **Связь с прошлым курсом.** В модуле 4 прошлого курса мы писали классы-репозитории, которые инкапсулировали SQL-запросы к базе. Manager в Django — это встроенный репозиторий: он уже прикреплён к каждой модели и предоставляет стандартный набор методов. Пользовательский менеджер, который мы разберём в конце урока, — это и есть расширение этого репозитория.

---

## CREATE — создание записей

### Способ 1: create()

Самый короткий способ — метод `create()`, который создаёт объект и сразу сохраняет его в БД:

```python
film = Film.objects.create(
    title='Крёстный отец',
    year=1972,
    description='История семьи Корлеоне.',
    rating=9.2,
    slug='krestnyj-otec'
)
```

### Способ 2: save()

Создаём объект вручную и явно вызываем `save()`:

```python
film = Film(
    title='Список Шиндлера',
    year=1993,
    rating=8.9,
    slug='spisok-shindlera'
)
film.save()  # только здесь выполняется INSERT
```

Этот способ полезен, когда нужно дополнительно обработать объект перед сохранением.

### Способ 3: get_or_create()

Создаёт запись, если её нет, или возвращает существующую. Возвращает кортеж `(объект, создан)`:

```python
film, created = Film.objects.get_or_create(
    slug='pobeg-iz-shoushenko',
    defaults={
        'title': 'Побег из Шоушенка',
        'year': 1994,
        'rating': 9.3,
    }
)
print(created)  # True — если создан, False — если уже существовал
```

Поля в `defaults` используются только при создании. Поиск идёт по полям вне `defaults` — в данном случае по `slug`.

---

## READ — чтение записей

### Все записи

```python
films = Film.objects.all()
# SELECT * FROM films_film ORDER BY -year (с учётом Meta.ordering)
```

### Один объект по условию: get()

```python
film = Film.objects.get(id=1)
film = Film.objects.get(slug='krestnyj-otec')
```

`get()` возвращает ровно один объект. Если запись не найдена — выбрасывает `Film.DoesNotExist`. Если найдено больше одной — `Film.MultipleObjectsReturned`. Поэтому `get()` используют только с уникальными полями.

### Фильтрация: filter() и exclude()

```python
# Фильмы после 2000 года
films = Film.objects.filter(year__gt=2000)

# Фильмы с рейтингом выше 8
high_rated = Film.objects.filter(rating__gte=8.0)

# Все фильмы кроме драм (исключение)
not_drama = Film.objects.exclude(genres__name='Драма')
```

`filter()` возвращает QuerySet с объектами, удовлетворяющими условию. `exclude()` — инверсия: возвращает объекты, не удовлетворяющие условию.

### Сортировка: order_by()

```python
# По году (возрастание)
films = Film.objects.order_by('year')

# По году (убывание) — минус перед именем поля
films = Film.objects.order_by('-year')

# По нескольким полям
films = Film.objects.order_by('-rating', 'title')
```

`order_by()` переопределяет сортировку из `Meta.ordering`.

### Срез: первые N записей

```python
# Первые 5 фильмов
top5 = Film.objects.all()[:5]

# Записи с 5 по 10
page = Film.objects.all()[5:10]
```

Срез QuerySet транслируется в SQL-конструкцию `LIMIT / OFFSET`.

### Подсчёт и проверка существования

```python
# Количество записей
count = Film.objects.count()
count = Film.objects.filter(year__gt=2000).count()

# Проверка существования (быстрее чем count() > 0)
exists = Film.objects.filter(slug='krestnyj-otec').exists()
```

---

## Field Lookups — условия поиска

Field Lookups — это синтаксис для задания условий в `filter()`, `exclude()` и `get()`. Он выглядит как `поле__оператор`:

```python
Film.objects.filter(year__gt=2000)
#                   ^^^^  ^^
#                   поле  оператор (greater than)
```

> **Связь с прошлым курсом.** В SQL мы писали `WHERE year > 2000`, `WHERE title LIKE '%отец%'`. Field Lookups — это то же самое, но в Python-синтаксисе. Каждый lookup транслируется в соответствующую SQL-конструкцию.

### Числовые и строковые сравнения

| Lookup | SQL-эквивалент | Пример |
|---|---|---|
| `exact` (по умолчанию) | `= 'значение'` | `filter(year=1972)` |
| `gt` | `> значение` | `filter(year__gt=2000)` |
| `gte` | `>= значение` | `filter(rating__gte=8.0)` |
| `lt` | `< значение` | `filter(year__lt=1990)` |
| `lte` | `<= значение` | `filter(year__lte=2000)` |
| `in` | `IN (...)` | `filter(year__in=[1972, 1993, 1994])` |
| `range` | `BETWEEN ... AND ...` | `filter(year__range=(1990, 2000))` |

### Строковые lookups

| Lookup | SQL-эквивалент | Пример |
|---|---|---|
| `contains` | `LIKE '%значение%'` | `filter(title__contains='отец')` |
| `icontains` | `ILIKE '%значение%'` | `filter(title__icontains='отец')` |
| `startswith` | `LIKE 'значение%'` | `filter(title__startswith='Кр')` |
| `endswith` | `LIKE '%значение'` | `filter(title__endswith='ка')` |
| `istartswith` | без учёта регистра | `filter(title__istartswith='кр')` |

Префикс `i` означает case-insensitive (без учёта регистра). Для поиска по строкам почти всегда используют `icontains` вместо `contains`.

### Проверка на None

```python
# Фильмы без описания
Film.objects.filter(description__isnull=True)

# Фильмы с описанием
Film.objects.filter(description__isnull=False)
```

### Цепочки условий

Несколько вызовов `filter()` подряд работают как `AND`:

```python
# Фильмы с рейтингом выше 8 И годом после 1990
films = Film.objects.filter(rating__gte=8.0).filter(year__gt=1990)

# То же самое — через запятую внутри одного filter()
films = Film.objects.filter(rating__gte=8.0, year__gt=1990)
```

---

## UPDATE — обновление записей

### Обновление одного объекта

```python
film = Film.objects.get(id=1)
film.rating = 9.5
film.save()
```

`save()` по умолчанию обновляет все поля. Если нужно обновить только одно — используй `update_fields`, чтобы не перезаписывать лишнее:

```python
film.rating = 9.5
film.save(update_fields=['rating'])
# UPDATE films_film SET rating = 9.5 WHERE id = 1
```

### Массовое обновление: update()

```python
# Установить рейтинг 0 всем фильмам до 1950 года
Film.objects.filter(year__lt=1950).update(rating=0.0)
```

`update()` выполняет один SQL-запрос `UPDATE` и возвращает количество обновлённых строк. Это намного эффективнее, чем загружать все объекты и вызывать `save()` для каждого.

---

## DELETE — удаление записей

### Удаление одного объекта

```python
film = Film.objects.get(id=1)
film.delete()
```

### Массовое удаление

```python
# Удалить все фильмы с рейтингом ниже 5
deleted_count, _ = Film.objects.filter(rating__lt=5.0).delete()
print(deleted_count)  # количество удалённых записей
```

`delete()` возвращает кортеж: количество удалённых объектов и словарь с детализацией по моделям (актуально при каскадном удалении связанных объектов, о чём подробнее в уроке 10).

---

## Обновляем представления — подключаем реальные данные

Теперь заменим заглушку из словаря на настоящие запросы к базе. Попутно видим, как QuerySet органично встраивается на место списка — шаблоны менять не нужно:

```python
# films/views.py
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.urls import reverse
from django.shortcuts import redirect

from .models import Film


def index(request):
    context = {
        'title': 'Лучшие фильмы всех времён',
    }
    return render(request, 'films/index.html', context)


def film_list(request):
    films = Film.objects.all()
    context = {
        'films': films,
    }
    return render(request, 'films/film_list.html', context)


def film_detail(request, film_id):
    film = get_object_or_404(Film, id=film_id)
    return render(request, 'films/film_detail.html', {'film': film})


def about(request):
    context = {
        'title': 'О нашем сайте',
        'film_count': Film.objects.count(),
    }
    return render(request, 'films/about.html', context)
```

`get_object_or_404()` — это именно та функция, которую мы анонсировали в уроке 3. Она делает `get()` и автоматически возвращает 404, если объект не найден. Больше не нужен словарь `FILMS` и ручная проверка `if film_id not in FILMS`.

---

## Пользовательский менеджер модели

Стандартный менеджер `objects` предоставляет все базовые методы. Но если одни и те же запросы повторяются в нескольких местах — логично вынести их в модель.

Пользовательский менеджер — это класс, унаследованный от `models.Manager`, в котором мы добавляем собственные методы:

```python
# films/models.py
from django.db import models


class FilmManager(models.Manager):

    def high_rated(self):
        """Фильмы с рейтингом 8.0 и выше."""
        return self.filter(rating__gte=8.0)

    def by_year(self, year):
        """Фильмы конкретного года."""
        return self.filter(year=year)

    def recent(self, count=5):
        """Последние добавленные фильмы."""
        return self.order_by('-created_at')[:count]
```

Подключаем менеджер к модели:

```python
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

    objects = FilmManager()  # заменяем стандартный менеджер

    class Meta:
        ordering = ['-year']
        verbose_name = 'Фильм'
        verbose_name_plural = 'Фильмы'

    def __str__(self):
        return f'{self.title} ({self.year})'
```

Теперь в представлениях и шаблонных тегах можно писать выразительно:

```python
# Вместо Film.objects.filter(rating__gte=8.0)
films = Film.objects.high_rated()

# Вместо Film.objects.filter(year=1972)
films = Film.objects.by_year(1972)

# Последние 3 добавленных фильма
latest = Film.objects.recent(3)
```

### Обновляем templatetag

Помнишь заглушку в `inclusion_tag` из урока 7? Теперь заменяем её на реальный запрос:

```python
# films/templatetags/film_tags.py
from django import template
from films.models import Film
import datetime

register = template.Library()


@register.simple_tag
def current_year():
    return datetime.date.today().year


@register.inclusion_tag('films/includes/latest_films.html')
def latest_films(count=3):
    films = Film.objects.recent(count)  # используем менеджер
    return {'films': films}
```

Шаблон `latest_films.html` не меняется — он уже ожидает список фильмов с полями `id` и `title`.

---

## Подводные камни

### get() и исключения

`get()` выбрасывает исключение при любом отклонении от «ровно один результат». Никогда не используй `get()` по неуникальному полю:

```python
# X - Если несколько фильмов с таким годом — MultipleObjectsReturned
film = Film.objects.get(year=1972)

# Правильно: По уникальному полю — безопасно
film = Film.objects.get(slug='krestnyj-otec')

# Правильно: Или через get_object_or_404 — автоматический 404 вместо исключения
film = get_object_or_404(Film, slug='krestnyj-otec')
```

### update() не вызывает save()

Метод `update()` выполняет SQL напрямую, минуя Python-объект. Это значит: не срабатывают сигналы Django, не обновляется `auto_now`, не вызывается кастомный `save()`:

```python
# Поле updated_at с auto_now=True НЕ обновится
Film.objects.filter(id=1).update(rating=9.5)

# Для обновления с вызовом save() — только через объект
film = Film.objects.get(id=1)
film.rating = 9.5
film.save()
```

`auto_now` — это специальный параметр полей `DateField` и `DateTimeField`, который автоматически записывает текущую дату/время при каждом сохранении объекта.

`update()` выполняет один SQL-запрос `UPDATE` напрямую, минуя Python-объекты. Это эффективно для массового обновления, но не вызывает кастомный `save()`, сигналы Django и не обновляет поля с `auto_now=True`. Загрузка объекта и `save()` работает через Python — медленнее при массовом обновлении, но поддерживает всю кастомную логику модели.

### Ленивость QuerySet и N+1

QuerySet ленивый — SQL выполняется при первом обращении к данным. Но если внутри цикла обращаться к связанным объектам (появятся в уроке 10), каждое обращение порождает новый запрос. Это классическая проблема N+1, которую мы разберём в уроке 11 с Django Debug Toolbar.

---

## Вопросы

1. В чём разница между `get()` и `filter()`? Когда использовать каждый?
2. Что такое Field Lookup и как он связан с SQL?
3. Чем отличается `Film.objects.filter(...).update(...)` от загрузки объекта и вызова `save()`?
4. Зачем нужен пользовательский менеджер? Чем он лучше, чем писать `filter()` в каждом представлении?
5. Почему QuerySet называют «ленивым»? Когда фактически выполняется SQL-запрос?

---

## Практическая задача

**Тип: расширь проект**

**Часть 1.** Добавь в `FilmManager` метод `search(query)`, который принимает строку и возвращает фильмы, в названии или описании которых встречается эта строка (без учёта регистра).

**Часть 2.** Используй этот метод в представлении `search_film` из урока 3 — вместо заглушки с текстом теперь оно должно возвращать реальные результаты поиска. Передай найденные фильмы в шаблон `films/search_results.html` и выведи их список. Если фильмов не найдено — покажи сообщение `'По запросу "..." ничего не найдено.'`

<details>
<summary><b>Пример решение</b></summary>

---

**films/models.py** — добавляем метод в менеджер:

```python
class FilmManager(models.Manager):

    def high_rated(self):
        return self.filter(rating__gte=8.0)

    def by_year(self, year):
        return self.filter(year=year)

    def recent(self, count=5):
        return self.order_by('-created_at')[:count]

    def search(self, query):
        """Поиск по названию и описанию без учёта регистра."""
        return self.filter(
            models.Q(title__icontains=query) |
            models.Q(description__icontains=query)
        )
```

> Обрати внимание: в методе `search()` используется `models.Q` — специальный класс для составных условий с оператором `OR` (`|`). Подробно разберём его в уроке 11.

**films/views.py** — обновляем представление:

```python
def search_film(request):
    query = request.GET.get('q', '').strip()

    if not query:
        return HttpResponse('Введите название фильма для поиска.', status=400)

    films = Film.objects.search(query)
    context = {
        'films': films,
        'query': query,
    }
    return render(request, 'films/search_results.html', context)
```

**films/templates/films/search_results.html:**

```html
{% extends 'base.html' %}

{% block title %}Поиск: {{ query }}{% endblock %}

{% block content %}
    <h1>Результаты поиска: «{{ query }}»</h1>

    {% for film in films %}
        {% include 'films/includes/film_card.html' %}
    {% empty %}
        <p>По запросу «{{ query }}» ничего не найдено.</p>
    {% endfor %}

    <a href="{% url 'films:film_list' %}">← К каталогу</a>
{% endblock %}
```

> Строка запроса: `http://127.0.0.1:8000/films/search/?q=Список Шиндлера`

</details>

---

[Предыдущий урок](lesson08.md) | [Следующий урок](lesson10.md)