# Модуль 3. Урок 17. Методы выбора записей из таблиц. Fields Lookups

В этом уроке мы научимся извлекать данные из базы с помощью **ORM-запросов** и познакомимся с мощным инструментом Django — **fields lookups**, который позволяет гибко фильтровать данные: искать по частичному совпадению, диапазонам, условиям, исключениям и т.д.

## Что такое ORM еще раз

**ORM (Object Relational Mapping)** — это механизм Django, который позволяет работать с базой данных **не через SQL-запросы**, а через **Python-код**.
Вы описываете таблицы в виде **моделей**, а Django сам превращает ваши вызовы в SQL-запросы.

**Пример:**
Вместо SQL-запроса:

```sql
SELECT * FROM movies_movie WHERE year = 2020;
```

в Django вы пишете:

```python
Movie.objects.filter(year=2020)
```

---

## Менеджер записей `objects`

Каждая модель Django имеет специальный атрибут `objects` — это **менеджер записей**, который управляет выборкой данных.

```python
Movie.objects
```

Через него мы будем выполнять все операции: создавать, искать, фильтровать и удалять записи.

---

## Подготовка среды

Перед началом работы запустите интерактивную оболочку Django:

```bash
python manage.py shell_plus --print-sql
```

Флаг `--print-sql` позволяет видеть SQL-запросы, которые Django выполняет под капотом.

Это поможет понять, как ORM превращает Python-запросы в SQL.

---

## Создание записей

Начнем с примера. Пусть у нас есть модель `Movie` в приложении `movies`:

```python
class Movie(models.Model):
    title = models.CharField(max_length=100)
    year = models.PositiveIntegerField()
    is_published = models.BooleanField(default=True)

    def __str__(self):
        return self.title
```

Создадим несколько фильмов прямо из shell:

```python
Movie.objects.create(title='Inception', year=2010)
Movie.objects.create(title='Avatar', year=2009)
Movie.objects.create(title='Interstellar', year=2014)
Movie.objects.create(title='Oppenheimer', year=2023, is_published=False)
```

Проверим, что всё сохранилось:

```python
Movie.objects.all()
```

Результат:

```bash
<QuerySet [<Movie: Inception>, <Movie: Avatar>, <Movie: Interstellar>, <Movie: Oppenheimer>]>
```

---

## Выбор всех записей — `all()`

Метод `all()` возвращает **все записи** таблицы:

```python
Movie.objects.all()
```

Вы можете обратиться к элементам по индексу:

```python
m = Movie.objects.all()[0]
print(m.title, m.year)
```

Или получить срез:

```python
movies = Movie.objects.all()[:2]
for m in movies:
    print(m.title)
```

---

## Фильтрация записей — `filter()`

Чтобы выбрать записи по условию, используется метод `filter()`.

```python
Movie.objects.filter(title='Inception')
```

Это превращается в SQL-запрос:

```sql
SELECT * FROM movies_movie WHERE title = 'Inception';
```

Если совпадений нет — возвращается пустой `QuerySet`.

---

## Что такое Lookup (поля поиска)

**Lookups** — это специальные суффиксы, которые позволяют уточнить, **как именно сравнивать значения** в запросах.

С их помощью можно делать запросы вроде:

- "где год больше 2010",
- "где название содержит слово",
- "где id входит в список значений".

Синтаксис:

```
<имя_поля>__<lookup>=<значение>
```

Обратите внимание на двойное подчеркивание `__`, которое разделяет имя поля и сам **lookup**.

---

## Примеры использования Lookups

### 1. Точное совпадение (`exact`)

```python
Movie.objects.filter(title__exact='Avatar')
```

SQL:

```sql
SELECT * FROM movies_movie WHERE title = 'Avatar';
```

---

### 2. Сравнение по числовым полям (`gt`, `gte`, `lt`, `lte`)

```python
Movie.objects.filter(year__gte=2010)
```

- `gt` — больше чем
- `gte` — больше или равно
- `lt` — меньше чем
- `lte` — меньше или равно

---

### 3. Частичное совпадение (`contains`, `icontains`)

с учетом регистра:

```python
Movie.objects.filter(title__contains='ter')
```

или без учета регистра:

```python
Movie.objects.filter(title__icontains='TER')
```

> ⚠️ SQLite может некорректно работать с `icontains` для кириллических символов.

---

### 4. Вхождение в список (`in`)

```python
Movie.objects.filter(year__in=[2009, 2010, 2014])
```

SQL:

```sql
SELECT * FROM movies_movie WHERE year IN (2009, 2010, 2014);
```

---

### 5. Проверка на `NULL` (`isnull`)

```python
Movie.objects.filter(year__isnull=True)
```

---

### 6. Комбинирование условий (`AND`, `OR`)

По умолчанию `filter()` объединяет условия с помощью `AND`:

```python
Movie.objects.filter(year__gte=2010, is_published=True)
```

Если нужно `OR`, используется `Q()` (О нем подробно будем говорить дальше по курсу):

```python
from django.db.models import Q
Movie.objects.filter(Q(year__lte=2010) | Q(is_published=False))
```

---

## Исключение записей — `exclude()`

Метод `exclude()` возвращает все записи, **кроме** тех, что соответствуют условию:

```python
Movie.objects.exclude(year__lt=2010)
```

Это эквивалент SQL:

```sql
SELECT * FROM movies_movie WHERE year >= 2010;
```

---

## Получение одной записи — `get()`

Метод `get()` возвращает **одну конкретную запись**.

Если записей больше одной или ни одной — выбрасывается ошибка.

```python
movie = Movie.objects.get(pk=2)
print(movie.title)
```

---

## Проверка результата в браузере

После экспериментов в shell, можно вывести данные в шаблон.

Например, создайте во `views.py` функцию:

```python
from django.shortcuts import render
from .models import Movie

def movies_list(request):
    movies = Movie.objects.filter(year__gte=2010)
    return render(request, 'movies/movies_list.html', {'movies': movies})
```

Шаблон `movies_list.html`:

```html
<h2>Фильмы после 2010 года</h2>
<ul>
  {% for m in movies %}
  <li>{{ m.title }} ({{ m.year }})</li>
  {% endfor %}
</ul>
```

Теперь проверьте в браузере — фильтр сработал, и вы видите только нужные фильмы.

---

## Практические задания

### **Задание 1. Простая выборка**

Выведите все фильмы, которые **вышли после 2012 года**.
Подсказка: используйте `filter(year__gt=2012)`.

---

### **Задание 2. Фильтрация по подстроке**

Выведите все фильмы, в названии которых встречается слово "in".

---

### **Задание 3. Исключение**

Отобразите все фильмы, **кроме** тех, у которых `is_published=False`.

---

### **Задание 4. Комбинированный фильтр**

Выведите фильмы, которые вышли **после 2010 года** и при этом **опубликованы**.

---

### **Задание 5. Проверка на наличие**

Создайте один фильм с `year=None`.
Затем выведите все фильмы, у которых поле `year` не заполнено (`isnull=True`).

---

### **Задание 6. Фильтрация по списку**

Отобразите все фильмы, год выхода которых — один из `[2009, 2010, 2014]`.

---

## Вопросы

1. Что такое менеджер `objects` в модели Django?
2. Чем отличается `filter()` от `get()`?
3. Что делает lookup `icontains`?
4. Как объединить условия фильтрации с помощью `OR`?
5. Как выбрать все записи, кроме определенных?
6. Как проверить, что поле не заполнено (`NULL`)?
7. Что произойдет, если `get()` вернет несколько записей?
8. Для чего используется двойное подчеркивание в lookups?
9. Как вывести только первые три записи из таблицы?
10. Как проверить результат работы фильтра в браузере?

---

[Предыдущий урок](lesson16.md) | [Следующий урок](lesson18.md)
