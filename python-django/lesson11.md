# Урок 11. Продвинутый ORM: Q, F, annotate(), агрегаты, группировка

## Зачем нужны дополнительные инструменты

Базовых методов `filter()`, `exclude()`, `order_by()` достаточно для большинства задач. Но есть три ситуации, где их не хватает:

- нужно составное условие с `OR`, а не только `AND` — для этого `Q`
- нужно сравнить два поля одной записи между собой — для этого `F`
- нужно посчитать агрегат (сумму, среднее, количество) — для этого функции агрегации и `annotate()`

> **Связь с прошлым курсом.** В модуле 1 прошлого курса мы писали `GROUP BY`, `COUNT()`, `AVG()` напрямую в SQL. Всё, что разберём в этом уроке, — это ORM-обёртка над теми же конструкциями. Если синтаксис Django покажется запутанным — мысленно переводи его в SQL, который мы уже знаем.

---

## Класс Q — составные условия

Обычная цепочка `filter(a=1, b=2)` или `filter(a=1).filter(b=2)` работает как `AND`. Но что если нужно `OR`?

Мы уже использовали `Q` в задаче из урока 9 — теперь разберём подробно.

`Q` — это объект, представляющий условие SQL-запроса. Он нужен тогда, когда простого `filter()` недостаточно: для операций `OR`, `NOT`, сложной логики и динамической сборки запросов. 

Django использует `Q`, потому что объекты безопаснее, переносимее между СУБД и позволяют **программно конструировать SQL без написания самого SQL**.

### Базовый синтаксис

```python
from django.db.models import Q

# Фильмы 1972 ИЛИ 1994 года
Film.objects.filter(Q(year=1972) | Q(year=1994))

# Фильмы с рейтингом выше 8 ИЛИ года после 2020
Film.objects.filter(Q(rating__gt=8.0) | Q(year__gt=2020))
```

### Операторы Q

| Оператор | Значение | Пример |
|---|---|---|
| `&` | AND | `Q(year__gt=2000) & Q(rating__gt=8)` |
| `\|` | OR | `Q(year=1972) \| Q(year=1994)` |
| `~` | NOT | `~Q(genres__name='Комедия')` |

```python
# AND через & — то же самое, что filter(year__gt=2000, rating__gt=8)
Film.objects.filter(Q(year__gt=2000) & Q(rating__gt=8))

# NOT — все фильмы, кроме комедий
Film.objects.filter(~Q(genres__name='Комедия'))

# Комбинация: (драма ИЛИ криминал) И рейтинг выше 8
Film.objects.filter(
    (Q(genres__name='Драма') | Q(genres__name='Криминал')) & Q(rating__gt=8)
)
```

### Q вместе с обычными аргументами

`Q`-объекты можно комбинировать с обычными именованными аргументами в одном вызове — но `Q` всегда должен идти первым:

```python
# Правильно: Q-объекты перед обычными аргументами
Film.objects.filter(Q(year=1972) | Q(year=1994), rating__gt=5)

# Неправильно: обычные аргументы перед Q — SyntaxError
Film.objects.filter(rating__gt=5, Q(year=1972) | Q(year=1994))
```

### Применение в нашем проекте — улучшаем поиск

В уроке 9 мы написали метод `search()` с `Q`. Расширим его — поиск теперь учитывает и режиссёра:

```python
# films/models.py
class FilmManager(models.Manager):

    def search(self, query):
        """Поиск по названию, описанию и имени режиссёра."""
        return self.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(director__name__icontains=query)
        ).distinct()
```

`.distinct()` добавлен на случай, если фильтрация через связанную таблицу `director` создаст дубликаты при JOIN.

---

## Класс F — сравнение полей внутри записи

`F` позволяет ссылаться на значение поля прямо в запросе — без загрузки объекта в Python. Это нужно в двух случаях: сравнение двух полей одной записи и атомарное обновление значения.

`F()` позволяет ссылаться на значение поля прямо внутри SQL-запроса. Чаще всего он используется для безопасного изменения **счетчиков**, **остатков товаров**, **балансов** и других данных, где новое значение **зависит от текущего значения в базе**. 

*Без `F()` такие операции подвержены **состояниям гонки** и требуют лишних запросов к базе данных.*

### Сравнение полей

Представим, что в модели `Film` есть поля `rating` (рейтинг критиков) и `audience_rating` (рейтинг зрителей):

```python
from django.db.models import F

# Фильмы, где зрительский рейтинг выше критического
Film.objects.filter(audience_rating__gt=F('rating'))
```

Без `F` пришлось бы загрузить все объекты в Python и сравнивать в цикле — намного медленнее и не масштабируется.

### Атомарное обновление

Это самое частое применение `F` на практике. Вспомним модель `FilmStats` из урока 10 со счётчиком просмотров:

```python
# Опасно при конкурентном доступе (race condition)
stats = FilmStats.objects.get(film_id=1)
stats.views_count = stats.views_count + 1
stats.save()
```

Проблема: между чтением значения и записью могут произойти другие обновления — реальные одновременные запросы от двух пользователей могут привести к потере одного из увеличений счётчика.

```python
# Атомарно — вычисление происходит на стороне БД одним запросом
from django.db.models import F

FilmStats.objects.filter(film_id=1).update(views_count=F('views_count') + 1)
```

Такой `UPDATE` выполняется как единая операция на уровне базы данных: `UPDATE films_filmstats SET views_count = views_count + 1 WHERE film_id = 1`. Конкурентные запросы не теряют инкременты.

### Применение в представлении

Добавим инкремент просмотров в `film_detail`:

```python
# films/views.py
from django.db.models import F

def film_detail(request, film_id):
    film = get_object_or_404(
        Film.objects.select_related('director').prefetch_related('genres', 'actors'),
        id=film_id
    )

    # Атомарно увеличиваем счётчик просмотров, если статистика существует
    FilmStats.objects.filter(film=film).update(views_count=F('views_count') + 1)

    return render(request, 'films/film_detail.html', {'film': film})
```

---

## Агрегирующие функции

Агрегирующие функции вычисляют итоговое значение по набору записей: сумму, среднее, минимум, максимум, количество.

```python
from django.db.models import Avg, Count, Max, Min, Sum
```

### aggregate() — агрегат по всему QuerySet

```python
# Средний рейтинг всех фильмов
Film.objects.aggregate(Avg('rating'))
# {'rating__avg': Decimal('8.13')}

# Несколько агрегатов сразу, с понятными именами
Film.objects.aggregate(
    средний_рейтинг=Avg('rating'),
    максимальный_рейтинг=Max('rating'),
    минимальный_рейтинг=Min('rating'),
    всего_фильмов=Count('id')
)
# {'средний_рейтинг': Decimal('8.13'), 'максимальный_рейтинг': Decimal('9.30'), ...}
```

**SQL-эквивалент**:

```sql
-- Средний рейтинг
SELECT AVG(rating)
FROM films_film;
```

```sql
-- Несколько агрегатов сразу
SELECT
    AVG(rating) AS средний_рейтинг,
    MAX(rating) AS максимальный_рейтинг,
    MIN(rating) AS минимальный_рейтинг,
    COUNT(id) AS всего_фильмов
FROM films_film;
```

`aggregate()` возвращает словарь с одним набором значений по всему QuerySet — не привязан к отдельным объектам.

### annotate() — агрегат для каждого объекта

`annotate()` решает другую задачу: добавляет вычисленное значение к каждому объекту в QuerySet. Это аналог `GROUP BY` с агрегатом в SQL.

```python
from django.db.models import Count

# Количество фильмов у каждого режиссёра
directors = Director.objects.annotate(film_count=Count('films'))

for director in directors:
    print(f'{director.name}: {director.film_count} фильмов')
```

**SQL-эквивалент**:

```sql
SELECT director.*, COUNT(film.id) as film_count
FROM films_director director
LEFT JOIN films_film film ON film.director_id = director.id
GROUP BY director.id
```

`annotate()` буквально и есть `GROUP BY` — Django группирует по полю, к которому применяется метод (`Director`), и считает агрегат по связанной таблице.

### Сортировка по аннотированному полю

Результат `annotate()` можно использовать в `order_by()` и `filter()`:

```python
# Режиссёры, отсортированные по количеству фильмов (больше — выше)
directors = Director.objects.annotate(film_count=Count('films')).order_by('-film_count')
```

**SQL-эквивалент**:

```sql
SELECT director.*, COUNT(film.id) as film_count
FROM films_director director
LEFT JOIN films_film film ON film.director_id = director.id
GROUP BY director.id
ORDER BY film_count DESC;
```

---

```python
# Только режиссёры с более чем 2 фильмами
prolific_directors = Director.objects.annotate(
    film_count=Count('films')
).filter(film_count__gt=2)
```

**SQL-эквивалент**:

```sql
SELECT director.*, COUNT(film.id) as film_count
FROM films_director director
LEFT JOIN films_film film ON film.director_id = director.id
GROUP BY director.id
HAVING COUNT(film.id) > 2;
```

Здесь появляется важный SQL-оператор `HAVING`, который работает с агрегатными функциями после группировки.

### Практический пример — топ жанров

```python
# Жанры с количеством фильмов и средним рейтингом фильмов в этом жанре
genres = Genre.objects.annotate(
    film_count=Count('films'),
    avg_rating=Avg('films__rating')
).order_by('-film_count')

for genre in genres:
    print(f'{genre.name}: {genre.film_count} фильмов, средний рейтинг {genre.avg_rating}')
```

**SQL-эквивалент**:

```sql
SELECT
    genre.*,
    COUNT(film.id) AS film_count,
    AVG(film.rating) AS avg_rating
FROM films_genre genre
LEFT JOIN films_film_genres fg
    ON fg.genre_id = genre.id
LEFT JOIN films_film film
    ON film.id = fg.film_id
GROUP BY genre.id
ORDER BY film_count DESC;
```

Обрати внимание: Django автоматически строит JOIN через промежуточную таблицу ManyToMany.

---

## Value — вычисляемая константа в запросе

`Value` оборачивает обычное Python-значение, чтобы использовать его в выражении ORM наравне с полями модели. Применяется реже, чем `Q` и `F`, но полезен при построении вычисляемых полей:

```python
from django.db.models import Value
from django.db.models.functions import Concat

# Объединить название и год в одну строку через ORM, а не в Python
films = Film.objects.annotate(
    full_title=Concat('title', Value(' ('), 'year', Value(')'))
)
```

**SQL-эквивалент:**

```sql
SELECT
    *,
    CONCAT(title, ' (', year, ')') AS full_title
FROM films_film;
```

**Пример результата:**

```text
Список Шиндлера (1993)
Крёстный отец (1972)
Побег из Шоушенка (1994)
```

Это нужно, когда вычисление должно остаться внутри SQL-запроса — например, для последующей фильтрации или сортировки по результату.

---

## Группировка через values() + annotate()

Если нужна группировка не по объектам модели, а по произвольному полю — используем `values()` перед `annotate()`. Это меняет поведение `annotate()`: вместо агрегата для каждого объекта он сгруппирует записи по указанным полям.

```python
# Количество фильмов по годам
Film.objects.values('year').annotate(count=Count('id')).order_by('-year')

# [{'year': 1994, 'count': 1}, {'year': 1993, 'count': 1}, {'year': 1972, 'count': 1}]
```

**SQL-эквивалент:**

```sql
SELECT
    year,
    COUNT(id) AS count
FROM films_film
GROUP BY year
ORDER BY year DESC;
```

Здесь `values('year')` фактически становится аналогом SQL-конструкции:

```sql
GROUP BY year
```

Без `values()` перед `annotate()` группировка происходила бы по первичному ключу модели — то есть фактически её бы не было.

---

```python
# Средний рейтинг по годам
Film.objects.values('year').annotate(avg_rating=Avg('rating')).order_by('-avg_rating')
```

**SQL-эквивалент:**

```sql
SELECT
    year,
    AVG(rating) AS avg_rating
FROM films_film
GROUP BY year
ORDER BY avg_rating DESC;
```

Результат:

```python
[
    {'year': 1994, 'avg_rating': 9.3},
    {'year': 1972, 'avg_rating': 9.2},
    {'year': 1993, 'avg_rating': 8.9},
]
```

> **Важное отличие.** `values()` возвращает не объекты модели, а словари. Это значит — после `values()` нельзя обратиться к методам модели или `related_name`, только к данным, которые попали в словарь.

---

## Сравнение: aggregate() vs annotate() vs values()+annotate()

Сводим три похожих, но разных подхода:

| Метод | Что возвращает | Когда использовать |
|---|---|---|
| `aggregate()` | Один словарь со значением по всему QuerySet | Нужна общая статистика: средний рейтинг всех фильмов |
| `annotate()` | QuerySet объектов с добавленным полем | Нужно значение для каждого объекта: количество фильмов у каждого режиссёра |
| `values().annotate()` | QuerySet словарей, сгруппированных по указанному полю | Нужна группировка по произвольному критерию: количество фильмов по годам |

---

## Применяем в нашем проекте — страница статистики

Соберём всё изученное в одном представлении — простая страница со сводной статистикой каталога:

```python
# films/views.py
from django.db.models import Avg, Count, Max, Min

def catalog_stats(request):
    overall_stats = Film.objects.aggregate(
        total=Count('id'),
        avg_rating=Avg('rating'),
        max_rating=Max('rating'),
        min_rating=Min('rating'),
    )

    top_directors = Director.objects.annotate(
        film_count=Count('films')
    ).filter(film_count__gt=0).order_by('-film_count')[:5]

    films_by_year = Film.objects.values('year').annotate(
        count=Count('id')
    ).order_by('-year')

    context = {
        'overall_stats': overall_stats,
        'top_directors': top_directors,
        'films_by_year': films_by_year,
    }
    return render(request, 'films/catalog_stats.html', context)
```

```html
<!-- films/templates/films/catalog_stats.html -->
{% extends 'base.html' %}

{% block title %}Статистика каталога{% endblock %}

{% block content %}
    <h1>Статистика каталога</h1>

    <h2>Общая информация</h2>
    <p>Всего фильмов: {{ overall_stats.total }}</p>
    <p>Средний рейтинг: {{ overall_stats.avg_rating|floatformat:1 }}</p>
    <p>Максимальный рейтинг: {{ overall_stats.max_rating }}</p>

    <h2>Самые продуктивные режиссёры</h2>
    <ul>
        {% for director in top_directors %}
            <li>{{ director.name }} — {{ director.film_count }} фильмов</li>
        {% endfor %}
    </ul>

    <h2>Фильмы по годам</h2>
    <ul>
        {% for item in films_by_year %}
            <li>{{ item.year }}: {{ item.count }} фильмов</li>
        {% endfor %}
    </ul>
{% endblock %}
```

Не забываем добавить маршрут:

```python
# films/urls.py
path('stats/', views.catalog_stats, name='catalog_stats'),
```

---

## Подводные камни

### annotate() после filter() меняет смысл агрегата

Порядок `filter()` и `annotate()` имеет значение. Если фильтровать перед `annotate()`, агрегат считается только по отфильтрованным записям; если после — фильтр применяется к уже посчитанному значению:

```python
# Среднее по ВСЕМ фильмам режиссёра, потом фильтр по результату
Director.objects.annotate(avg_rating=Avg('films__rating')).filter(avg_rating__gt=8)

# Среднее ТОЛЬКО по фильмам после 2000 года (отдельная фильтрация связанных объектов)
Director.objects.filter(films__year__gt=2000).annotate(avg_rating=Avg('films__rating'))
```

Это частый источник багов — порядок вызовов даёт разный результат при, казалось бы, похожем синтаксисе.

### Двойной annotate() с Count даёт неверный результат

Если применить `Count()` к двум разным M2M-связям одновременно, JOIN-комбинаторика умножает строки, и числа окажутся завышенными:

```python
# Потенциально неверный результат — JOIN по genres и actors комбинируются
Film.objects.annotate(
    genre_count=Count('genres'),
    actor_count=Count('actors')
)
```

Решение — `distinct=True` внутри `Count()`:

```python
Film.objects.annotate(
    genre_count=Count('genres', distinct=True),
    actor_count=Count('actors', distinct=True)
)
```

### F() в Python-выражениях не работает

`F()` существует только внутри ORM-запросов. Нельзя использовать его как обычное Python-значение:

```python
# TypeError — F() не вычисляется в Python
new_count = F('views_count') + 1
print(new_count)

# Работает только внутри update() или filter()
FilmStats.objects.filter(film_id=1).update(views_count=F('views_count') + 1)
```

---

## Вопросы

1. В чём разница между `Q` и обычными именованными аргументами в `filter()`?
2. Зачем использовать `F()` при обновлении счётчика вместо обычного increment в Python?
3. Чем `aggregate()` отличается от `annotate()`?
4. Зачем перед `annotate()` иногда вызывают `values()`? Что меняется в поведении группировки?
5. Почему `Count()` на двух разных ManyToMany-связях одновременно может дать неверный результат?

---

## Практическая задача

**Тип: допиши код**

Дано представление, которое должно показывать пять режиссёров с самым высоким средним рейтингом их фильмов — но только тех, у кого есть хотя бы 2 фильма в каталоге. Допиши пропущенные части.

```python
from django.db.models import Avg, Count

def top_directors(request):
    directors = Director.objects.annotate(
        avg_rating=___________________,
        film_count=___________________
    ).filter(
        ___________________
    ).order_by(
        ___________________
    )[:5]

    context = {'directors': directors}
    return render(request, 'films/top_directors.html', context)
```

Шаблон уже готов и ожидает у каждого `director` атрибуты `name`, `avg_rating`, `film_count`.

---

[Предыдущий урок](lesson10.md) | [Следующий урок](lesson12.md)