# Модуль 5. Урок 31. Группировка записей в Django ORM

В предыдущем уроке мы научились работать с агрегирующими функциями — считать, суммировать, вычислять средние значения.

Теперь мы сделаем следующий шаг и научимся **группировать записи**: собирать данные по категориям, жанрам, годам и любым другим признакам.

Группировка — это один из важнейших инструментов аналитики. Она лежит в основе:

- статистики,
- дашбордов,
- аналитических отчетов,
- страниц каталога,
- фильтров и витрин данных.

В Django за группировку отвечает связка:

```
values() + annotate()
```

Причём порядок важен: сначала определяется, **по каким полям группировать**, а затем — **какие агрегаты вычислять для каждой группы**.

---

## 1. Для чего нужна группировка в Django ORM?

Представьте задачи:

- Посчитать, сколько фильмов относится к каждому жанру.
- Узнать, сколько фильмов выпущено в каждый год.
- Посчитать количество фильмов у каждого режиссёра.
- Понять, какие теги используются чаще остальных.

Все эти задачи не требуют получения всех фильмов — группировка происходит прямо в базе данных.

---

## 2. Базовый принцип группировки

Предположим, у нас есть модели:

```python
class Genre(models.Model):
    name = models.CharField(max_length=100)

class Movie(models.Model):
    title = models.CharField(max_length=200)
    year = models.IntegerField()
    genre = models.ForeignKey(Genre, on_delete=models.SET_NULL, null=True)
    rating = models.FloatField()
```

### Посчитаем количество фильмов в каждом жанре

```python
from django.db.models import Count

Movie.objects.values("genre__name").annotate(total=Count("id"))
```

**Что происходит?**

1. `values("genre__name")` — группируем по жанрам.
2. `annotate(total=Count("id"))` — для каждой группы считаем фильмы.

SQL, который построит Django:

```sql
SELECT genre.name, COUNT(movie.id)
FROM movie
LEFT JOIN genre ON movie.genre_id = genre.id
GROUP BY genre.name;
```

Результат будет выглядеть так:

```python
[
    {"genre__name": "Комедия", "total": 12},
    {"genre__name": "Драма", "total": 8},
    {"genre__name": "Боевик", "total": 5},
]
```

---

## 3. Почему порядок важен: values() → annotate()

Неправильно:

```python
Movie.objects.annotate(total=Count("id")).values("genre__name")
```

Почему ошибка?

Потому что:

- сначала будет выполнена аннотация по всей таблице,
- а группировка произойдёт позже,
- что приведёт к неверному результату (одно число вместо групп).

Правильно:

```python
Movie.objects.values("genre__name").annotate(total=Count("id"))
```

Запомните правило:

> **Группировка — это values()**

> **Аналитика по группам — это annotate()**

---

## 4. Задаем собственное имя агрегатного поля

По умолчанию Django назовёт поле:

```
id__count
```

Но лучше задавать имя явно:

```python
Movie.objects.values("genre__name").annotate(total=Count("id"))
```

Или ещё лучше:

```python
Movie.objects.values("genre__name").annotate(
    movies_count=Count("id")
)
```

Так читается намного понятнее.

---

## 5. Фильтрация сгруппированных данных

Иногда нам нужны не все группы, а только те, которые удовлетворяют условиям.

### Найдём жанры, у которых есть хотя бы один фильм

```python
Genre.objects.annotate(total=Count("movie")).filter(total__gt=0)
```

Django сам понимает, что:

- таблица `movie` ссылается на `genre`,
- связь называется `movie_set` (или `movie` при related_name),
- группировка идёт по жанрам.

---

### Найдём года, в которых выпустили больше 3 фильмов

```python
Movie.objects.values("year").annotate(
    total=Count("id")
).filter(total__gt=3)
```

Результат:

```python
[
    {"year": 2019, "total": 7},
    {"year": 2021, "total": 4}
]
```

---

## 6. Проверка через браузер

Создадим временную вьюшку:

```python
def genre_stats(request):
    data = Movie.objects.values("genre__name").annotate(
        total=Count("id")
    )

    return HttpResponse(str(list(data)))
```

Открываем в браузере:

```
[{'genre__name': 'Комедия', 'total': 12},
 {'genre__name': 'Драма', 'total': 8},
 {'genre__name': 'Боевик', 'total': 5}]
```

Если видите ошибку:

- Проверьте, есть ли жанры.
- Проверьте, заполнены ли фильмы.
- Проверьте, что миграции применены.

---

## 7. Использование функций БД в annotate()

Кроме Count(), можно использовать:

- Avg
- Sum
- Max
- Min
- Length
- Upper, Lower
- ExtractYear и другие функции дат

Например:

### Вычислить длину названия фильма

```python
from django.db.models.functions import Length

Movie.objects.annotate(name_len=Length("title"))
```

### Узнать средний рейтинг по жанрам

```python
Movie.objects.values("genre__name").annotate(
    avg_rating=Avg("rating")
)
```

### Узнать самый старый фильм каждого жанра

```python
Movie.objects.values("genre__name").annotate(
    oldest=Min("year")
)
```

---

## 8. Частые ошибки и их исправление

### 1. Ошибка «FieldError: Cannot resolve keyword …»

Вы указали неправильное имя поля.

Например:

```python
Movie.objects.values("genres__name")
```

А правильное:

```python
Movie.objects.values("genre__name")
```

### 2. Ошибка при использовании annotate() перед values()

```python
Movie.objects.annotate(total=Count("id")).values("genre__name")
```

Решение:

```python
Movie.objects.values("genre__name").annotate(total=Count("id"))
```

### 3. Неиспользование related_name

Если у модели обратная связь называется `movie_set`, а вы пишете:

```python
Genre.objects.annotate(total=Count("movies"))
```

Будет ошибка.
Используйте:

```python
Genre.objects.annotate(total=Count("movie"))
```

или задайте related_name:

```python
genre = models.ForeignKey(..., related_name="movies")
```

---

## Практические задания

### **Задание 1.**

Сгруппируйте фильмы по году выпуска и подсчитайте количество фильмов в каждом году.

---

### **Задание 2.**

Сделайте группировку по жанрам и вычислите для каждого жанра:

- количество фильмов,
- средний рейтинг,
- минимальный год выпуска.

Используйте annotate().

---

### **Задание 3.**

Найдите только те жанры, у которых есть фильмы.

Используйте Genre.objects.annotate().

---

### **Задание 4.**

Получите список:

```
{"year": ..., "avg_rating": ...}
```

для каждого года, где средняя оценка выше 7.

---

### **Задание 5.**

Во временной вьюшке выведите список жанров вместе с количеством фильмов.

Проверьте работу в браузере.

---

### **Задание 6.**

Аннотируйте каждому фильму длину названия и отсортируйте по этому значению.

---

## Вопросы

1. Что делает связка values() + annotate()?
2. Почему порядок values() → annotate() важен?
3. Что происходит, если использовать annotate() до values()?
4. Как получить количество фильмов в каждом жанре?
5. Как фильтровать сгруппированные данные?
6. Что делает функция Length()?
7. Как сгруппировать фильмы по году?
8. Как работает related_name при группировке?
9. Что вернёт запрос: `Movie.objects.values("genre__name").annotate(avg=Avg("rating"))`?
10. Почему группировка выполняется на уровне базы данных, а не Python?

---

[Предыдущий урок](lesson30.md) | [Следующий урок](lesson32.md)
