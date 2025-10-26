# Модуль 2. Урок 13. Пользовательские теги шаблонов. Декораторы `simple_tag` и `inclusion_tag`

На предыдущих уроках мы научились работать с шаблонами, наследованием и статическими файлами.
Теперь представь, что в проекте нужно **многократно повторять один и тот же элемент интерфейса** — например, список жанров, меню навигации или рейтинг фильма.
Конечно, можно было бы просто вставлять одинаковый HTML в разные шаблоны, но это нарушает принцип **DRY (Don’t Repeat Yourself)**.

Django предлагает для этого мощный инструмент — **пользовательские теги шаблонов**.
Они позволяют **встраивать динамический контент в шаблоны** и **делать код компактным и переиспользуемым**.

---

## Что такое пользовательские теги?

Пользовательские теги — это **наши собственные шаблонные команды Django**, которые мы создаём вручную.
Они могут:

- возвращать данные (тег `simple_tag`);
- возвращать отрендеренный HTML-шаблон (тег `inclusion_tag`).

В нашем проекте `cinemahub` мы сделаем пример с **жанрами фильмов**.

---

## Цель урока

Мы создадим два пользовательских тега:

1. `get_genres` — вернёт список жанров (используя `simple_tag`).
2. `show_genres` — выведет список жанров через отдельный шаблон (используя `inclusion_tag`).

---

## Подготовка данных

Начнём с чего-то простого.
Откроем файл `movies/views.py` и создадим временные данные (эмулируем таблицу жанров):

```python
genres_db = [
    {'id': 1, 'name': 'Боевики'},
    {'id': 2, 'name': 'Драмы'},
    {'id': 3, 'name': 'Комедии'},
    {'id': 4, 'name': 'Фантастика'},
]
```

> 💡 Позже, когда мы подключим базу данных, эти данные будут загружаться из модели.

---

## Шаг 1. Создаём пакет для тегов

Django ищет пользовательские теги в **специальной папке `templatetags`** внутри приложения.

Создадим структуру:

```
movies/
│── templatetags/
│   ├── __init__.py
│   └── movie_tags.py
```

Файл `__init__.py` может быть пустым — он просто сообщает Python, что это пакет.

---

## Шаг 2. Создаём `simple_tag`

В файле `movie_tags.py` напишем наш первый пользовательский тег:

```python
from django import template
import movies.views as views

register = template.Library()

@register.simple_tag()
def get_genres():
    """Возвращает список жанров"""
    return views.genres_db
```

---

### Как работает `simple_tag`?

Тег `simple_tag` просто выполняет функцию и возвращает результат.
Мы можем сохранить этот результат в переменную и использовать в шаблоне.

---

## Шаг 3. Используем тег в шаблоне

Откроем шаблон `base.html` и подключим наши теги:

```django
{% load movie_tags %}
```

Теперь можно использовать тег в любом месте:

```django
{% get_genres as genres %}
<ul class="genres-list">
  {% for g in genres %}
    <li><a href="#">{{ g.name }}</a></li>
  {% endfor %}
</ul>
```

> Здесь мы сохраняем результат в переменную `genres`, чтобы потом вывести её в цикле.

---

## Проверим в браузере

Запускаем сервер:

```bash
python manage.py runserver
```

Переходим на страницу `/` — в шапке (или где вы разместили код) должен появиться список жанров:

```
Боевики | Драмы | Комедии | Фантастика
```

Если всё работает — поздравляю! Вы только что создали свой первый шаблонный тег Django 🎉

---

## Переименование тега

Иногда название функции не совпадает с тем, как вы хотите вызывать тег в шаблоне.
Можно задать имя вручную:

```python
@register.simple_tag(name='getcategories')
def get_genres():
    return views.genres_db
```

Теперь в шаблоне нужно писать:

```django
{% getcategories as genres %}
```

---

## Шаг 4. Создаём `inclusion_tag`

Тег `inclusion_tag` отличается от `simple_tag` тем, что он не просто возвращает данные, а **рендерит отдельный шаблон**.
Это удобно, когда нужно вставить готовый HTML-фрагмент (например, меню, рейтинг или карточку фильма).

---

### Создаём шаблон списка жанров

Создадим файл `movies/templates/movies/includes/genres_list.html`:

```django
<ul class="genres-list">
  {% for g in genres %}
    <li><a href="#">{{ g.name }}</a></li>
  {% endfor %}
</ul>
```

---

### Добавляем новый тег в `movie_tags.py`

```python
@register.inclusion_tag('movies/includes/genres_list.html')
def show_genres():
    """Рендерит шаблон со списком жанров"""
    return {"genres": views.genres_db}
```

---

Теперь мы можем использовать тег прямо в `base.html`:

```django
{% load movie_tags %}
...
{% show_genres %}
```

Django подставит отрендеренный шаблон `genres_list.html` и выведет список жанров.

---

## Шаг 5. Финальная сборка шаблонов

**Напомним структуру проекта**:
```
movies/
│── templates/
│   ├── base.html
│   ├── movies/
│   │   ├── index.html
│   │   ├── about.html
│   │   ├── includes/
│   │   │   ├── nav.html
│   │   │   ├── index_content.html
│   │   │   ├── genres_list.html
```

### **Изменим базовый шаблон `base.html`**

Этот шаблон будет основой для всех остальных.
Он подключает статику, загружает CSS и включает общие блоки сайта.

```django
{% load static %}
{% load movies_tags %}

<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>Cinemahub — фильмы и жанры</title>
    <link rel="stylesheet" href="{% static 'movies/css/styles.css' %}">
</head>
<body>
    <header>
        <h1><a href="{% url 'home' %}">🎬 Cinemahub</a></h1>
        {% include 'movies/includes/nav.html' %}
    </header>

    <main class="container">
        <aside class="sidebar">
            <h3>Жанры</h3>
            {% show_genres selected_genre %}
        </aside>

        <section class="content">
            {% block content %}{% endblock %}
        </section>
    </main>

    <footer>
        <p>&copy; 2025 Cinemahub</p>
    </footer>

    <script src="{% static 'movies/js/main.js' %}"></script>
</body>
</html>
```

---

### Создаём шаблоны страниц

**Главная страница со списком фильмов `index.html`**.

```django
{% extends 'base.html' %}

{% block content %}
{% include 'movies/includes/index_content.html' %}
{% endblock %}
```

---

**Страница “О проекте” `about.html`**.

```django
{% extends 'base.html' %}

{% block content %}
<h2>О проекте</h2>
<p>Проект <strong>Cinemahub</strong> создан для изучения Django и представляет собой учебный портал о фильмах и жанрах. Здесь вы сможете практиковаться с шаблонами, статикой и пользовательскими тегами.</p>
{% endblock %}
```

---

### Навигация и контентные блоки

**Меню сайта `includes/nav.html`**.

```django
<nav>
    <ul>
        <li><a href="{% url 'home' %}">Главная</a></li>
        <li><a href="{% url 'about' %}">О проекте</a></li>
    </ul>
</nav>
```

---

**Временный контент на главной `includes/index_content.html`**.

```django
{% load static %}

<h2>Добро пожаловать в Cinemahub!</h2>
<p>Здесь скоро появится каталог фильмов, поиск и фильтрация по жанрам. Пока мы учимся подключать шаблоны и статику.</p>
<img src="{% static 'movies/images/poster_sample.jpg' %}" alt="Movie Poster">
```

---

### Подключаем пользовательские теги

Для красоты добавим возможность подсвечивать выбранный жанр.

**Изменим тег**:

```python
@register.inclusion_tag('movies/includes/genres_list.html')
def show_genres(selected_genre=0):
    """Рендерит список жанров с выделением активного"""
    return {"genres": views.genres_db, "selected_genre": selected_genre}
```

### **Шаблон `genres_list.html`**

```django
<ul class="genres-list">
  {% for g in genres %}
    {% if g.id == selected_genre %}
      <li class="active">{{ g.name }}</li>
    {% else %}
      <li><a href="{% url 'genre' g.id %}">{{ g.name }}</a></li>
    {% endif %}
  {% endfor %}
</ul>
```

---

### **Сравниваем Вьюшки проекта**

```python
...

genres_db = [
    {"id": 1, "name": "Боевики"},
    {"id": 2, "name": "Драмы"},
    {"id": 3, "name": "Комедии"},
    {"id": 4, "name": "Фантастика"},
]


def index(request):
    return render(request, 'movies/index.html', {"selected_genre": 0})

def show_genre(request, genre_id):
    return render(request, 'movies/index.html', {"selected_genre": genre_id})

def about(request):
    data = {
        "title": "О сайте",
        "menu": menu,
        "films": data_db,
    }
    return render(request, "movies/about.html", data)

...
```

### **Добавляем путь для genre**

```python
urlpatterns = [
    path('', views.index, name='home'),
    path('about/', views.about, name='about'),
    path('add_film/', views.add_film, name='add_film'),
    path('contact/', views.contact, name='contact'),
    path('login/', views.login, name='login'),
    path('film/<int:film_id>/', views.show_film, name='film'),

    path('genre/<int:genre_id>/', views.show_genre, name='genre'),
]
```

### **Добавляем стилизацию в `styles.css`**

```css
body {
    font-family: Arial, sans-serif;
    background-color: #f3f3f3;
    color: #333;
    margin: 0;
    padding: 0;
}

header {
    background-color: #242424;
    color: white;
    padding: 15px;
}

header a {
    color: white;
    text-decoration: none;
    margin-right: 10px;
}

.container {
    display: flex;
    gap: 20px;
    padding: 20px;
}

.sidebar {
    width: 25%;
    background-color: #fff;
    padding: 15px;
    border-radius: 8px;
}

.genres-list {
    list-style: none;
    padding: 0;
}

.genres-list li {
    margin-bottom: 8px;
}

.genres-list li.active {
    font-weight: bold;
    color: #d22;
}

.content {
    width: 75%;
    background-color: #fff;
    padding: 20px;
    border-radius: 8px;
}
```

### Проверяем результат

1. Убедись, что в `settings.py` прописано:

   ```python
   STATIC_URL = '/static/'
   STATICFILES_DIRS = [BASE_DIR / 'static']
   ```

2. Запусти сервер:

   ```bash
   python manage.py runserver
   ```

3. Перейди на:

   * `/` — откроется главная страница с постером.
   * `/about/` — страница о проекте.
   * `/genre/2/` — жанр “Комедии” подсветится в боковом меню.

4. Проверь консоль браузера — не должно быть ошибок загрузки статики.

---

## Практическое задание

1. Создай собственный тег `get_movies_count`, который возвращает количество фильмов в списке.
2. Создай тег `show_header`, который будет рендерить шаблон `includes/header.html` (через `inclusion_tag`).
3. Добавь параметр `username` в тег `show_header` и выведи приветствие на странице.
4. Проверь, что все пользовательские теги подключаются корректно.
5. Попробуй объединить `simple_tag` и `inclusion_tag`: передай данные из первого в шаблон второго.

---

## Резюме

- **`simple_tag`** — возвращает данные прямо в шаблон.
- **`inclusion_tag`** — возвращает готовый HTML-фрагмент из отдельного шаблона.
- Оба тега регистрируются через `@register`.
- Папка `templatetags` должна находиться внутри приложения.
- Пользовательские теги позволяют писать **чистые и переиспользуемые шаблоны**.

---

## Вопросы для самопроверки

1. Для чего нужны пользовательские теги в Django?
2. В чём разница между `simple_tag` и `inclusion_tag`?
3. Где должна находиться папка `templatetags`?
4. Зачем нужен декоратор `@register.simple_tag()`?
5. Можно ли передавать параметры в пользовательский тег?
6. Как вызвать тег и сохранить результат в переменную?
7. Что делает `inclusion_tag` при рендеринге страницы?
8. Как подсветить активный элемент списка с помощью параметра?
9. Что произойдёт, если забыть подключить `{% load movie_tags %}`?
10. Приведи пример, когда `inclusion_tag` предпочтительнее `simple_tag`.

---

[Предыдущий урок](lesson12.md) | [Следующий урок](lesson14.md)
