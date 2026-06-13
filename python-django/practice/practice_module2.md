# 🎬 Финальная практика: создание стартового шаблона проекта **Cinemahub**

## 🎯 Цель практической работы

Создать первый полноценный прототип сайта **Cinemahub** — онлайн-каталога фильмов и сериалов.
Сайт пока не будет динамическим (без моделей и БД),
но будет иметь аккуратный интерфейс, навигацию, шаблоны, подключённую статику и базовую структуру Django-проекта.

---

## ⚙️ Шаг 1. Создание проекта и приложений

1. Создай новый проект:

   ```bash
   django-admin startproject cinemahub
   cd cinemahub
   ```

2. Создай приложение `movies`, где будут все страницы сайта:

   ```bash
   python manage.py startapp movies
   ```

3. В `settings.py` зарегистрируй приложение:

   ```python
   INSTALLED_APPS = [
       ...
       'movies',
   ]
   ```

4. Проверь, что проект запускается:

   ```bash
   python manage.py runserver
   ```

   Перейди по адресу [http://127.0.0.1:8000](http://127.0.0.1:8000) — должна открыться стартовая страница Django.

---

## 🧱 Шаг 2. Настраиваем структуру проекта

Сразу создадим базовую структуру каталогов и файлов.

```
cinemahub/
│── cinemahub/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
│── movies/
│   ├── templates/
│   │   └── movies/
│   │       ├── index.html
│   │       ├── movie_detail.html
│   │       └── includes/
│   │           ├── nav.html
│   │           ├── movie_card.html
│   │           ├── index_content.html
│   │           └── genres_list.html
│   │
│   ├── static/
│   │   └── movies/
│   │       ├── css/
│   │       │   └── style.css
│   │       └── images/
│   │           ├── 1.webp
│   │           ├── 2.webp
│   │           └── ... (все остальные постеры)
│   │
│   ├── templatetags/
│   │   ├── __init__.py
│   │   └── movies_tags.py
│   │
│   ├── views.py
│   ├── urls.py
│   └── ...
│
│── manage.py
```

---

## 🎨 Шаг 3. Настраиваем статику

В `settings.py` добавь внизу:

```python
STATIC_URL = '/static/'

STATICFILES_DIRS = [
    BASE_DIR / "movies" / "static"
]
```

Проверь, что в `INSTALLED_APPS` есть:

```python
'django.contrib.staticfiles',
```

---

## 🧭 Шаг 4. Маршруты проекта

В `cinemahub/urls.py`:

```python
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('movies.urls')),
]
```

В `movies/urls.py`:

```python
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='home'),
    path('movie/<int:movie_id>/', views.movie_detail, name='movie_detail'),
    path('genre/<int:genre_id>/', views.show_genre, name='show_genre'),
]
```

---

## 🎬 Шаг 5. Контент фильмов (пока вручную)

В `movies/views.py` создаём список фильмов:

```python
from django.shortcuts import render

movies_db = [
    {
        "id": 1,
        "title": "1+1",
        "group": "Художественный фильм",
        "img": "1.webp",
        "year": "2011",
        "description": "Пострадав в результате несчастного случая...",
        "genre": ["драма", "комедия"],
        "rating": 8.9
    },
    {
        "id": 2,
        "title": "Матрица",
        "group": "Художественный фильм",
        "img": "2.webp",
        "year": "1999",
        "description": "Жизнь Томаса Андерсона разделена на две части...",
        "genre": ["фантастика", "боевик"],
        "rating": 8.5
    },
    # ... остальные фильмы ...
]

def index(request):
    return render(request, "movies/index.html", {"movies": movies_db})

def movie_detail(request, movie_id):
    movie = next((m for m in movies_db if m["id"] == movie_id), None)
    return render(request, "movies/movie_detail.html", {"movie": movie})

def show_genre(request, genre_id):
    return render(request, "movies/index.html", {"selected_genre": genre_id})
```

---

## 🧩 Шаг 6. Создаём шаблоны

### `base.html`

Создай базовый шаблон с подключением статики:

```django
{% load static %}
{% load movies_tags %}
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>Cinemahub</title>
    <link rel="stylesheet" href="{% static 'movies/css/style.css' %}">
</head>
<body>
    <header>
        {% include 'movies/includes/nav.html' %}
    </header>

    <main>
        {% block content %}{% endblock %}
    </main>

    <footer>
        <p>© 2025 Cinemahub</p>
    </footer>
</body>
</html>
```

---

### `includes/nav.html`

```django
<nav class="navbar">
    <img src="{% static 'movies/images/logo.jpg' %}" alt="Cinemahub logo" class="logo">
    <ul>
        <li><a href="{% url 'home' %}">Главная</a></li>
        <li><a href="#">О проекте</a></li>
    </ul>
</nav>
```

---

### `index.html`

```django
{% extends 'base.html' %}
{% block content %}
<section class="movies-grid">
    {% include 'movies/includes/index_content.html' %}
</section>
{% endblock %}
```

---

### `includes/index_content.html`

```django
<div class="movie-container">
    {% for movie in movies %}
        {% include 'movies/includes/movie_card.html' %}
    {% endfor %}
</div>
```

---

### `includes/movie_card.html`

```django
<div class="movie-card">
    <a href="{% url 'movie_detail' movie.id %}">
        <img src="{% static 'movies/images/' %}{{ movie.img }}" alt="{{ movie.title }}">
    </a>
    <h3>{{ movie.title }} ({{ movie.year }})</h3>
    <p>{{ movie.group }}</p>
    <p class="rating">⭐ {{ movie.rating }}</p>
</div>
```

---

### `movie_detail.html`

```django
{% extends 'base.html' %}
{% block content %}
<div class="movie-detail">
    <img src="{% static 'movies/images/' %}{{ movie.img }}" alt="{{ movie.title }}">
    <div class="movie-info">
        <h1>{{ movie.title }}</h1>
        <p><b>Год:</b> {{ movie.year }}</p>
        <p><b>Жанры:</b> {{ movie.genre|join:", " }}</p>
        <p><b>Рейтинг:</b> ⭐ {{ movie.rating }}</p>
        <p>{{ movie.description }}</p>
    </div>
</div>
{% endblock %}
```

---

## 🎨 Шаг 7. Добавляем немного стилей

`movies/static/movies/css/style.css`:

```css
body {
    font-family: Arial, sans-serif;
    background: #111;
    color: #fff;
    margin: 0;
    padding: 0;
}

.navbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: #222;
    padding: 10px 40px;
}

.navbar ul {
    list-style: none;
    display: flex;
    gap: 20px;
}

.navbar a {
    color: #fff;
    text-decoration: none;
}

.logo {
    height: 40px;
}

.movie-container {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 20px;
    padding: 20px;
}

.movie-card {
    background: #1e1e1e;
    border-radius: 10px;
    overflow: hidden;
    text-align: center;
    transition: transform 0.2s;
}

.movie-card:hover {
    transform: scale(1.03);
}

.movie-card img {
    width: 100%;
    height: 320px;
    object-fit: cover;
}

.rating {
    color: gold;
}
```

---

## 🧠 Шаг 8. Проверяем результат

1. Запусти сервер:

   ```bash
   python manage.py runserver
   ```

2. Перейди на главную страницу `/` — должны отображаться карточки фильмов (4 в ряд).

3. Кликни на карточку — откроется страница с подробным описанием.

4. Проверь, что изображения и стили подгружаются корректно (без 404).

5. Всё! У тебя готов визуальный каркас будущего сайта Cinemahub 🎉

---

## 💡 Что мы закрепили

* Создание структуры проекта и приложения.
* Работа с шаблонами и наследованием.
* Подключение статики и изображений.
* Создание отдельных страниц (список и детальная).
* Использование include-шаблонов для переиспользования кода.

---

## 🧩 Вопросы для самопроверки

1. Что делает параметр `STATICFILES_DIRS`?
2. Для чего нужен тег `{% load static %}`?
3. В чем разница между `{% include %}` и `{% extends %}`?
4. Где нужно подключать пользовательские теги шаблонов?
5. Что произойдет, если не зарегистрировать приложение в `INSTALLED_APPS`?
6. Как проверить, что изображение из статики подключилось корректно?

---

Хочешь, я добавлю к этой практике **мини-задания для самостоятельной доработки**, чтобы студенты могли чуть-чуть улучшить сайт (например, добавить фильтры по жанрам или страницу "О проекте")?


