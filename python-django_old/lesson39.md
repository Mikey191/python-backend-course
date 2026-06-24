# Модуль 7. Урок 39. Что такое HTML-формы. Отправка данных по GET и POST-запросам

Формы — один из ключевых механизмов веб-разработки.
Через формы пользователи взаимодействуют с сайтом: ищут фильмы, добавляют данные, оставляют комментарии, фильтруют списки, отправляют сообщения и выполняют множество других действий.

В этом уроке мы впервые погрузимся в базовый фундамент работы HTML-форм, научимся отправлять данные на сервер методами **GET** и **POST**, обрабатывать эти данные в Django и выводить результат в браузере.

Все примеры будут связаны с проектом **cinemahub** и моделью **Movie**.

---

## 1. Что такое HTML-форма и зачем она нужна

HTML-форма — это специальная разметка, которая позволяет пользователю вводить данные и отправлять их на сервер.

Например:

- Ввести название фильма и выполнить поиск.
- Добавить описание фильма.
- Выбрать год выпуска фильма.
- Отправить текстовый запрос на сервер.

Все формы создаются с помощью тега:

```html
<form></form>
```

А внутри формы размещаются элементы:

- `<input>` — поля для ввода текста, числа, даты и др.
- `<textarea>` — многострочное текстовое поле.
- `<select>` — список с вариантами выбора.
- `<button>` — кнопка отправки формы.

---

## 2. Первая форма в проекте cinemahub

### Пример: Поиск фильма по названию (метод GET)

Создадим простую страницу поиска.
Форма будет отправлять данные методом **GET**, поэтому параметры появятся в URL.

### 2.1 Создаём шаблон поиска

Файл: **templates/search_movie.html**

```html
<!DOCTYPE html>
<html lang="ru">
  <head>
    <meta charset="UTF-8" />
    <title>Поиск фильма</title>
  </head>
  <body>
    <h1>Поиск фильма</h1>

    <form action="" method="get">
      <label for="title">Название фильма:</label>
      <input type="text" id="title" name="title" />

      <button type="submit">Искать</button>
    </form>

    {% if movies %}
    <h2>Результаты поиска:</h2>
    <ul>
      {% for movie in movies %}
      <li>{{ movie.title }} ({{ movie.year }})</li>
      {% endfor %}
    </ul>
    {% endif %}
  </body>
</html>
```

Что происходит?

- `method="get"` — данные будут добавлены в URL.
- При отправке формы URL станет таким:

```
http://localhost:8000/search?title=matrix
```

- Мы выводим список фильмов, если он передан в контекст.

---

### 2.2 Создаём представление для обработки поиска

Файл: **views.py**

```python
from django.shortcuts import render
from movies.models import Movie

def search_movie_view(request):
    title_query = request.GET.get('title')  # достаём параметр из URL
    movies = None

    if title_query:
        movies = Movie.objects.filter(title__icontains=title_query)

    return render(request, 'search_movie.html', {'movies': movies})
```

Пояснения:

- `request.GET` используется для получения данных, отправленных методом GET.
- `title__icontains` — ищем фильмы, содержащие введённый текст.
- Если пользователь ещё ничего не отправил → список пустой.

---

### 2.3 Добавляем маршрут

Файл: **urls.py**

```python
from django.urls import path
from .views import search_movie_view

urlpatterns = [
    path('search/', search_movie_view, name='search-movie'),
]
```

---

### 2.4 Проверяем в браузере

Открываем:

```
http://localhost:8000/search/
```

Вводим «matrix» → нажимаем «Искать».

Если модель Movie содержит такие фильмы — они появятся на странице.

❗ Частая ошибка:
**Пустая страница без ошибок** → скорее всего, забыли передать контекст `{'movies': movies}`.

---

## 3. Метод POST — передача данных в теле запроса

Метод POST используется, когда:

- Данные не должны появляться в URL
- Мы создаём/изменяем данные
- Мы отправляем большие тексты (описание фильма)

Пример: создадим простейшую учебную форму добавления фильма.

---

## 4. Создание фильма (POST-запрос)

В реальном проекте мы будем использовать Django Forms и ModelForm,
но сейчас важно понять базовые механизмы «сырая HTML-форма → Django view».

---

### 4.1 Создаём шаблон формы создания фильма

Файл: **templates/add_movie.html**

```html
<!DOCTYPE html>
<html lang="ru">
  <head>
    <meta charset="UTF-8" />
    <title>Добавить фильм</title>
  </head>
  <body>
    <h1>Добавление фильма</h1>

    <form action="" method="post">
      {% csrf_token %}

      <label for="title">Название фильма:</label>
      <input type="text" id="title" name="title" required />

      <label for="year">Год выхода:</label>
      <input
        type="number"
        id="year"
        name="year"
        min="1900"
        max="2100"
        required
      />

      <label for="description">Описание фильма:</label>
      <textarea id="description" name="description"></textarea>

      <button type="submit">Добавить</button>
    </form>

    {% if message %}
    <p>{{ message }}</p>
    {% endif %}
  </body>
</html>
```

Важно:

- `method="post"` — данные отправляются **в теле запроса**, не в URL.
- `{% csrf_token %}` — обязательная защита от CSRF-атак.
- Добавлена валидация в форме (`required`, `min/max`).

---

### 4.2 Создаём представление для обработки POST

Файл: **views.py**

```python
from django.shortcuts import render
from movies.models import Movie

def add_movie_view(request):
    message = ""

    if request.method == "POST":
        title = request.POST.get('title')
        year = request.POST.get('year')
        description = request.POST.get('description')

        # Простейшая проверка данных
        if not title or not year:
            message = "Заполните обязательные поля!"
        else:
            Movie.objects.create(
                title=title,
                year=year,
                description=description
            )
            message = "Фильм успешно добавлен!"

    return render(request, 'add_movie.html', {'message': message})
```

Разбор:

- `request.POST` — словарь данных, отправленных методом POST.
- Проверяем обязательные поля.
- Создаём запись в БД.
- Выводим сообщение.

---

### 4.3 Маршрут

Файл: **urls.py**

```python
path('add-movie/', add_movie_view, name='add-movie'),
```

---

### 4.4 Проверка в браузере

Переходим:

```
http://localhost:8000/add-movie/
```

Вводим данные → нажимаем «Добавить».

Если всё хорошо — получаем сообщение:
**«Фильм успешно добавлен!»**

Ошибка:
**“403 Forbidden (CSRF token missing)”** → вы забыли `{% csrf_token %}`.

---

## 5. GET-форма фильтрации (пример с годом выхода)

Файл: **templates/filter_year.html**

```html
<h1>Фильтрация фильмов по году</h1>

<form method="get">
  <label for="year">Год:</label>
  <input type="number" id="year" name="year" />

  <button type="submit">Фильтровать</button>
</form>

<ul>
  {% for movie in movies %}
  <li>{{ movie.title }} ({{ movie.year }})</li>
  {% endfor %}
</ul>
```

Файл: **views.py**

```python
def filter_by_year_view(request):
    year = request.GET.get('year')
    movies = Movie.objects.all()

    if year:
        movies = movies.filter(year=year)

    return render(request, 'filter_year.html', {'movies': movies})
```

---

## Практические задания

1. Создать форму, которая принимает название фильма и выводит длину строки.

---

2. Создать POST-форму, которая принимает описание фильма и выводит количество слов.

---

3. Создать GET-форму выбора минимального года фильма и вывести фильмы, выпущенные позже этого года.

---

## Сравнить решение

1. Форма с названием и длиной.

**Шаблон (templates/title_length.html)**

```html
<form method="get">
  <input type="text" name="title" />
  <button type="submit">Отправить</button>
</form>

{% if length %}
<p>Длина строки: {{ length }}</p>
{% endif %}
```

**View**

```python
def title_length_view(request):
    title = request.GET.get('title')
    length = len(title) if title else None
    return render(request, 'title_length.html', {'length': length})
```

---

2. Форма количества слов в описании.

**Шаблон**

```html
<form method="post">
  {% csrf_token %}
  <textarea name="text"></textarea>
  <button type="submit">Посчитать</button>
</form>

{% if count %}
<p>Количество слов: {{ count }}</p>
{% endif %}
```

**View**

```python
def count_words_view(request):
    count = None
    if request.method == "POST":
        text = request.POST.get('text', '')
        count = len(text.split())
    return render(request, 'count_words.html', {'count': count})
```

---

3. GET-форма для фильмов после определенного года.

**Решение (view)**

```python
def filter_from_year_view(request):
    year = request.GET.get('year')
    movies = Movie.objects.all()

    if year:
        movies = movies.filter(year__gte=year)

    return render(request, 'filter_from_year.html', {'movies': movies})
```

---

## Вопросы

1. Чем отличается GET от POST?
2. Где находятся данные, отправленные методом GET?
3. Где находятся данные, отправленные методом POST?
4. Зачем нужен CSRF-токен?
5. Можно ли отправить форму POST без CSRF-токена?
6. Через какой объект мы читаем GET-данные в Django?
7. Через какой объект мы читаем POST-данные в Django?
8. Что будет, если забыть передать контекст в render()?
9. Когда данные появляются в URL?
10. В каком случае стоит использовать POST?

---

[Предыдущий урок](lesson38.md) | [Следующий урок](lesson40.md)
