# Урок 6. Наследование шаблонов (extends) и тег include

## Проблема дублирования

Посмотри на шаблоны, которые мы создали в прошлых уроках. В каждом из них повторяется одно и то же:

```html
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>...</title>
</head>
<body>
    <nav>
        <a href="{% url 'index' %}">Главная</a> |
        <a href="{% url 'film_list' %}">Каталог</a> |
        <a href="{% url 'about' %}">О сайте</a>
    </nav>
    ...
</body>
</html>
```

Навигация, структура HTML, подключение стилей — это одинаково на каждой странице. Если нужно добавить пункт в меню или изменить структуру — придётся редактировать каждый файл отдельно.

Django решает это через **наследование шаблонов**: один базовый шаблон определяет общую структуру страницы, дочерние шаблоны наследуют её и заполняют только изменяемые части.

---

## Базовый шаблон

Создадим базовый шаблон в общей папке проекта — `templates/base.html`:

```html
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Сайт фильмов{% endblock %}</title>
</head>
<body>

    <header>
        <nav>
            <a href="{% url 'index' %}">Главная</a> |
            <a href="{% url 'film_list' %}">Каталог</a> |
            <a href="{% url 'about' %}">О сайте</a>
        </nav>
    </header>

    <main>
        {% block content %}{% endblock %}
    </main>

    <footer>
        <p>© 2024 Сайт фильмов</p>
    </footer>

</body>
</html>
```

Ключевая конструкция — **`{% block %}`**:

```html
{% block имя_блока %}
    содержимое по умолчанию (необязательно)
{% endblock %}
```

Блок — это именованная область, которую дочерний шаблон может переопределить. Блоков может быть сколько угодно. В нашем базовом шаблоне их два:

- `title` — заголовок вкладки браузера, с дефолтным текстом `Сайт фильмов`
- `content` — основное содержимое страницы, пустое по умолчанию

---

## Дочерние шаблоны

Дочерний шаблон начинается с тега `{% extends %}` и содержит только те блоки, которые нужно переопределить:

```html
{% extends 'base.html' %}

{% block title %}Каталог фильмов{% endblock %}

{% block content %}
    <h1>Каталог фильмов</h1>
    <p>Здесь будет список фильмов.</p>
{% endblock %}
```

Правила наследования:

- `{% extends %}` должен быть **первой строкой** шаблона — до любого HTML и пробелов
- Всё, что написано вне блоков в дочернем шаблоне — игнорируется
- Если блок не переопределён — используется содержимое из базового шаблона

Перепишем все шаблоны приложения.

### index.html

```html
<!-- films/templates/films/index.html -->
{% extends 'base.html' %}

{% block title %}Главная — Сайт фильмов{% endblock %}

{% block content %}
    <h1>{{ title }}</h1>
    <p>Добро пожаловать на сайт фильмов!</p>
    <a href="{% url 'film_list' %}">Перейти к каталогу →</a>
{% endblock %}
```

### film_list.html

```html
<!-- films/templates/films/film_list.html -->
{% extends 'base.html' %}

{% block title %}Каталог фильмов{% endblock %}

{% block content %}
    <h1>Каталог фильмов</h1>

    {% for film in films %}
        <p>
            {{ forloop.counter }}.
            <a href="{% url 'film_detail' film_id=film.id %}">{{ film.title }}</a>
            ({{ film.year }})
            <br>
            {{ film.description|default:"Нет описания"|truncatechars:80 }}
        </p>
    {% empty %}
        <p>В каталоге пока нет фильмов.</p>
    {% endfor %}
{% endblock %}
```

### film_detail.html

```html
<!-- films/templates/films/film_detail.html -->
{% extends 'base.html' %}

{% block title %}{{ film.title }} — Сайт фильмов{% endblock %}

{% block content %}
    <h1>{{ film.title }}</h1>
    <p>Год выпуска: {{ film.year }}</p>
    <p>{{ film.description|default:"Описание отсутствует." }}</p>
    <a href="{% url 'film_list' %}">← Назад к каталогу</a>
{% endblock %}
```

Посмотри, насколько чище стали шаблоны. Вся HTML-обвязка живёт в одном месте — `base.html`.

---

## Переменная block.super

Иногда нужно не заменить содержимое блока, а **дополнить** его. Для этого используется `{{ block.super }}` — он вставляет содержимое блока из родительского шаблона:

```html
{% extends 'base.html' %}

{% block title %}{{ block.super }} — Каталог{% endblock %}
```

Если в `base.html` блок `title` содержит `Сайт фильмов`, результат будет: `Сайт фильмов — Каталог`.

Это полезно для блоков со скриптами или стилями — добавить что-то к базовому набору, не удаляя его:

```html
{% block extra_css %}
    {{ block.super }}
    <link rel="stylesheet" href="...film-detail-styles.css">
{% endblock %}
```

---

## Многоуровневое наследование

Наследование может быть многоуровневым. Например, для раздела администрирования можно создать промежуточный шаблон:

```
base.html
└── base_films.html      ← добавляет боковую панель с жанрами
    ├── film_list.html
    └── film_detail.html
```

```html
<!-- films/templates/films/base_films.html -->
{% extends 'base.html' %}

{% block content %}
    <div class="layout">
        <aside>
            <h3>Жанры</h3>
            <ul>
                <li><a href="#">Драма</a></li>
                <li><a href="#">Комедия</a></li>
                <li><a href="#">Триллер</a></li>
            </ul>
        </aside>
        <div class="main-content">
            {% block main_content %}{% endblock %}
        </div>
    </div>
{% endblock %}
```

```html
<!-- films/templates/films/film_list.html -->
{% extends 'films/base_films.html' %}

{% block title %}Каталог фильмов{% endblock %}

{% block main_content %}
    <h1>Каталог фильмов</h1>
    ...
{% endblock %}
```

Глубокую вложенность без необходимости делать не стоит — три уровня это обычно предел разумного.

---

## Тег include

Тег `{% include %}` решает другую задачу: он вставляет один шаблон внутрь другого. В отличие от наследования — это не структурный механизм, а способ переиспользовать небольшие повторяющиеся фрагменты.

Хороший кандидат для `{% include %}` — карточка фильма. Сейчас она выводится в одном месте, но когда появятся страница режиссёра и страница поиска, одна и та же карточка понадобится в нескольких шаблонах.

Создадим фрагмент `films/templates/films/includes/film_card.html`:

```html
<!-- films/templates/films/includes/film_card.html -->
<div class="film-card">
    <h3>
        <a href="{% url 'film_detail' film_id=film.id %}">{{ film.title }}</a>
    </h3>
    <p>Год: {{ film.year }}</p>
    <p>{{ film.description|default:"Нет описания"|truncatechars:80 }}</p>
</div>
```

Подключаем в `film_list.html`:

```html
{% extends 'base.html' %}

{% block title %}Каталог фильмов{% endblock %}

{% block content %}
    <h1>Каталог фильмов</h1>

    {% for film in films %}
        {% include 'films/includes/film_card.html' %}
    {% empty %}
        <p>В каталоге пока нет фильмов.</p>
    {% endfor %}
{% endblock %}
```

Переменная `film` из цикла доступна внутри включаемого шаблона автоматически — он видит весь контекст родительского шаблона.

### Передача дополнительных переменных в include

Можно передать дополнительные переменные через `with`:

```html
{% include 'films/includes/film_card.html' with show_description=False %}
```

```html
<!-- film_card.html -->
<div class="film-card">
    <h3><a href="{% url 'film_detail' film_id=film.id %}">{{ film.title }}</a></h3>
    <p>Год: {{ film.year }}</p>
    {% if show_description %}
        <p>{{ film.description|default:"Нет описания" }}</p>
    {% endif %}
</div>
```

Чтобы включаемый шаблон видел **только** переданные переменные и не имел доступа к контексту родителя — добавь `only`:

```html
{% include 'films/includes/film_card.html' with film=film only %}
```

---

## Пространства имён маршрутов

В уроке 5 мы упоминали, что тег `{% url %}` может вести себя непредсказуемо, если в разных приложениях есть маршруты с одинаковыми именами. Сейчас — самое время это исправить.

Добавляем `app_name` в файл маршрутов приложения:

```python
# films/urls.py
from django.urls import path
from . import views

app_name = 'films'  # <- пространство имён

urlpatterns = [
    path('', views.index, name='index'),
    path('about/', views.about, name='about'),
    path('films/', views.film_list, name='film_list'),
    path('films/<int:film_id>/', views.film_detail, name='film_detail'),
    path('films/add/', views.add_film, name='add_film'),
    path('films/search/', views.search_film, name='search_film'),
    path('directors/<int:director_id>/', views.director_detail, name='director_detail'),
]
```

Теперь в шаблонах и в Python-коде к маршрутам обращаемся через `приложение:имя`:

```html
<!-- В шаблонах -->
<a href="{% url 'films:index' %}">Главная</a>
<a href="{% url 'films:film_detail' film_id=film.id %}">{{ film.title }}</a>
```

```python
# В представлениях
from django.urls import reverse
reverse('films:film_list')
redirect('films:film_list')
```

Обновим `base.html` с учётом пространства имён:

```html
<!-- templates/base.html -->
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Сайт фильмов{% endblock %}</title>
</head>
<body>

    <header>
        <nav>
            <a href="{% url 'films:index' %}">Главная</a> |
            <a href="{% url 'films:film_list' %}">Каталог</a> |
            <a href="{% url 'films:about' %}">О сайте</a>
        </nav>
    </header>

    <main>
        {% block content %}{% endblock %}
    </main>

    <footer>
        <p>© 2024 Сайт фильмов</p>
    </footer>

</body>
</html>
```

---

## Подводные камни

### extends должен быть первой строкой

Любой символ до `{% extends %}` — включая пустую строку или пробел — вызовет ошибку или непредсказуемое поведение:

```html
<!-- Пробел или пустая строка перед extends -->

{% extends 'base.html' %}

<!-- Правильно — extends первой строкой, без отступов -->
{% extends 'base.html' %}
```

### Контент вне блоков игнорируется

В дочернем шаблоне весь HTML вне блоков просто не попадёт в итоговую страницу. Это частая ошибка, когда переносят шаблон на наследование:

```html
{% extends 'base.html' %}

<p>Этот текст никогда не появится на странице.</p>  <!-- вне блока -->

{% block content %}
    <p>А этот появится.</p>  <!-- внутри блока -->
{% endblock %}
```

### include и производительность

Каждый `{% include %}` — это загрузка и рендеринг отдельного файла. Если включать шаблоны внутри цикла с сотнями элементов, это заметно замедлит страницу. В таких случаях лучше вынести содержимое карточки прямо в цикл или использовать кэширование (модуль 8).

---

## Итоговая структура шаблонов

```
filmsite/
├── templates/
│   └── base.html                          ← общий макет проекта
└── films/
    └── templates/
        └── films/
            ├── index.html                 ← наследует base.html
            ├── about.html                 ← наследует base.html
            ├── film_list.html             ← наследует base.html
            ├── film_detail.html           ← наследует base.html
            └── includes/
                └── film_card.html         ← переиспользуемый фрагмент
```

---

## Вопросы

1. В чём принципиальная разница между `{% extends %}` и `{% include %}`?
2. Что произойдёт, если в дочернем шаблоне написать HTML вне блоков `{% block %}`?
3. Для чего нужен `{{ block.super }}` и в каком случае он полезен?
4. Зачем нужен `app_name` в `urls.py`? Что изменится в синтаксисе тега `{% url %}`?
5. Включаемый шаблон через `{% include %}` — имеет ли он доступ к переменным контекста родительского шаблона?

---

## Практическая задача

**Тип: переведи**

Сейчас все шаблоны проекта дублируют HTML-структуру страницы. Переведи их на систему наследования.

**Требования:**

1. Создай базовый шаблон `templates/base.html` с блоками `title` и `content`. Добавь в него навигацию с тремя ссылками: главная, каталог, о сайте — используй `{% url %}` с пространством имён `films:`
2. Добавь `app_name = 'films'` в `films/urls.py`
3. Переведи шаблоны `index.html`, `film_list.html`, `film_detail.html`, `about.html` на наследование от `base.html`
4. Вынеси карточку фильма (название-ссылка, год, обрезанное описание) в отдельный фрагмент `films/includes/film_card.html` и подключи его в `film_list.html` через `{% include %}`

После выполнения задания все страницы должны выглядеть так же, как раньше, но HTML-структура теперь определяется в одном файле.

---

[Предыдущий урок](lesson05.md) | [Следующий урок](lesson07.md)