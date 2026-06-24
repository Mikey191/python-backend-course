# Урок 7. Статические файлы. Пользовательские теги (simple_tag, inclusion_tag)

## Статические файлы

До этого момента наш сайт возвращает только HTML без какого-либо оформления. В реальном приложении к страницам подключаются CSS, JavaScript и изображения — всё это называется **статическими файлами**: они не генерируются динамически, а отдаются браузеру как есть.

Django разделяет два типа файлов, которые легко перепутать:

- **Статические файлы** (`static`) — CSS, JS, иконки, шрифты. Часть исходного кода проекта, не меняются в процессе работы сайта.
- **Медиафайлы** (`media`) — файлы, загруженные пользователями: постеры фильмов, аватары. Появляются в процессе работы сайта. Разберём их в модуле 5, когда дойдём до форм с загрузкой файлов.

---

## Настройка статических файлов

Откроем `settings.py` и проверим настройки:

```python
# filmsite/settings.py

# URL-префикс для статических файлов в браузере
STATIC_URL = '/static/'

# Папки, где Django ищет статические файлы помимо папок приложений
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Папка, куда collectstatic собирает все файлы для продакшна
# (используется при деплое — модуль 9)
STATIC_ROOT = BASE_DIR / 'staticfiles'
```

`django.contrib.staticfiles` уже включён в `INSTALLED_APPS` по умолчанию — он отвечает за обслуживание статических файлов в режиме разработки.

---

## Структура папок

Статические файлы можно хранить двумя способами, которые Django объединяет автоматически:

```
filmsite/
├── static/                        ← общие файлы проекта
│   └── css/
│       └── base.css
└── films/
    └── static/
        └── films/                 ← файлы приложения (та же логика, что с шаблонами)
            ├── css/
            │   └── films.css
            └── img/
                └── logo.png
```

Поддиректория с именем приложения внутри `films/static/` — по той же причине, что и в шаблонах: защита от конфликтов имён между приложениями.

---

## Тег {% load %} и {% static %}

Чтобы использовать статические файлы в шаблоне, нужно сначала загрузить библиотеку тегов командой `{% load static %}`, а затем получить URL файла через тег `{% static %}`:

```html
{% load static %}
<!DOCTYPE html>
<html lang="ru">
<head>
    <link rel="stylesheet" href="{% static 'css/base.css' %}">
</head>
```

`{% static 'css/base.css' %}` преобразуется в `/static/css/base.css` — абсолютный URL, по которому браузер запросит файл.

Добавим `{% load static %}` в базовый шаблон. Важно: `{% load %}` работает только в том шаблоне, где написан — дочерние шаблоны не наследуют загруженные библиотеки:

```html
<!-- templates/base.html -->
{% load static %}
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Сайт фильмов{% endblock %}</title>
    <link rel="stylesheet" href="{% static 'css/base.css' %}">
    {% block extra_css %}{% endblock %}
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

    {% block extra_js %}{% endblock %}
</body>
</html>
```

Добавили два новых блока: `extra_css` и `extra_js` — для страниц, которым нужны дополнительные стили или скрипты. Дочерний шаблон может их заполнить через `{{ block.super }}`, не затрагивая базовые файлы.

Создадим базовый CSS-файл `static/css/base.css`:

```css
* {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}

body {
    font-family: Arial, sans-serif;
    max-width: 960px;
    margin: 0 auto;
    padding: 20px;
    color: #333;
}

nav {
    padding: 12px 0;
    border-bottom: 1px solid #ddd;
    margin-bottom: 24px;
}

nav a {
    color: #333;
    text-decoration: none;
    margin-right: 12px;
}

nav a:hover {
    text-decoration: underline;
}

footer {
    margin-top: 40px;
    padding-top: 16px;
    border-top: 1px solid #ddd;
    color: #999;
    font-size: 14px;
}
```

---

## Пользовательские теги шаблонов

DTL намеренно ограничен — в шаблонах нельзя вызывать произвольные Python-функции. Но иногда нужна логика, которая не покрывается стандартными фильтрами и тегами. Для этого Django позволяет создавать **собственные теги шаблонов**.

### Структура templatetags

Пользовательские теги хранятся в специальной директории `templatetags` внутри приложения:

```
films/
├── templatetags/
│   ├── __init__.py          ← обязательно, делает папку пакетом
│   └── film_tags.py         ← наши теги
├── models.py
└── views.py
```

Имя файла (`film_tags.py`) — это имя библиотеки, которую нужно загрузить в шаблоне: `{% load film_tags %}`.

---

## simple_tag

`simple_tag` — самый простой тип пользовательского тега. Это Python-функция, которая принимает аргументы и возвращает значение, подставляемое в шаблон.

### Пример: текущий год для футера

Хардкодить год в футере — плохая практика: раз в год придётся вручную обновлять шаблон. Сделаем тег, который возвращает текущий год автоматически:

```python
# films/templatetags/film_tags.py
from django import template
import datetime

register = template.Library()


@register.simple_tag
def current_year():
    return datetime.date.today().year
```

Объект `register` — это точка входа для регистрации тегов и фильтров. Декоратор `@register.simple_tag` регистрирует функцию как тег.

Использование в шаблоне:

```html
<!-- templates/base.html -->
{% load film_tags %}

...

<footer>
    <p>© {% current_year %} Сайт фильмов</p>
</footer>
```

### Пример: тег с аргументами

`simple_tag` может принимать аргументы — позиционные и именованные:

```python
@register.simple_tag
def film_url(film_id, anchor=''):
    """Возвращает URL страницы фильма, опционально с якорем."""
    from django.urls import reverse
    url = reverse('films:film_detail', kwargs={'film_id': film_id})
    return f'{url}#{anchor}' if anchor else url
```

```html
<a href="{% film_url film.id 'reviews' %}">Рецензии на {{ film.title }}</a>
```

### Сохранение результата в переменную

Результат `simple_tag` можно сохранить в переменную контекста через `as`:

```python
@register.simple_tag
def get_top_films(count=3):
    """Возвращает список фильмов с наивысшим рейтингом."""
    # Сейчас — заглушка, в модуле 3 подключим QuerySet
    films = [
        {'id': 1, 'title': 'Крёстный отец', 'year': 1972},
        {'id': 3, 'title': 'Побег из Шоушенка', 'year': 1994},
    ]
    return films[:count]
```

```html
{% get_top_films 2 as top_films %}
{% for film in top_films %}
    <p>{{ film.title }}</p>
{% endfor %}
```

---

## inclusion_tag

`inclusion_tag` — более мощный тип тега. Он не просто возвращает значение, а рендерит отдельный шаблон и вставляет результат в страницу.

Это идеальный инструмент для повторяющихся блоков с собственной логикой: виджет последних фильмов на боковой панели, блок навигации с активным пунктом, мини-форма поиска.

### Пример: виджет последних фильмов

Создадим виджет, который будет показывать несколько последних фильмов — его можно вставить в любой шаблон сайта:

```python
# films/templatetags/film_tags.py
from django import template
import datetime

register = template.Library()


@register.simple_tag
def current_year():
    return datetime.date.today().year


@register.inclusion_tag('films/includes/latest_films.html')
def latest_films(count=3):
    """Рендерит виджет с последними добавленными фильмами."""
    # Заглушка — в модуле 3 заменим на запрос к БД
    films = [
        {'id': 1, 'title': 'Крёстный отец', 'year': 1972},
        {'id': 2, 'title': 'Список Шиндлера', 'year': 1993},
        {'id': 3, 'title': 'Побег из Шоушенка', 'year': 1994},
    ]
    return {'films': films[:count]}
```

Обрати внимание: `inclusion_tag` возвращает **словарь** — это контекст для шаблона виджета.

Создаём шаблон виджета `films/templates/films/includes/latest_films.html`:

```html
{% load film_tags %}

<div class="latest-films">
    <h3>Последние добавленные</h3>
    <ul>
    {% for film in films %}
        <li><a href="{% url 'films:film_detail' film_id=film.id %}">{{ film.title }}</a></li>
    {% empty %}
        <li>Фильмов пока нет.</li>
    {% endfor %}
    </ul>
</div>
```

Используем виджет в базовом шаблоне:

```html
<!-- templates/base.html -->
{% load static %}
{% load film_tags %}

...

<aside>
    {% latest_films 3 %}
</aside>
```

### Передача request в inclusion_tag

Иногда тегу нужен доступ к объекту запроса — например, чтобы знать текущего пользователя или отметить активный пункт навигации. Для этого добавляем `takes_context=True`:

```python
@register.inclusion_tag('films/includes/nav.html', takes_context=True)
def nav_menu(context):
    """Рендерит навигацию с выделением активного раздела."""
    request = context['request']
    return {
        'current_path': request.path,
    }
```

```html
<!-- films/templates/films/includes/nav.html -->
<nav>
    <a href="{% url 'films:index' %}"
       {% if current_path == '/' %}class="active"{% endif %}>
        Главная
    </a>
    <a href="{% url 'films:film_list' %}"
       {% if '/films/' in current_path %}class="active"{% endif %}>
        Каталог
    </a>
</nav>
```

---

## Подводные камни

### {% load %} не наследуется

Это самая частая ошибка при работе с тегами. Если `{% load film_tags %}` написан в `base.html`, дочерний шаблон всё равно должен загрузить библиотеку сам — если использует теги из неё:

```html
<!-- Не сработает — дочерний шаблон не наследует {% load %} из base.html -->
{% extends 'base.html' %}

{% block content %}
    {% current_year %}   {# TemplateSyntaxError #}
{% endblock %}

<!-- Правильно — загружаем библиотеку явно -->
{% extends 'base.html' %}
{% load film_tags %}

{% block content %}
    {% current_year %}
{% endblock %}
```

### __init__.py обязателен

Папка `templatetags` без файла `__init__.py` не будет распознана Django как Python-пакет — теги не загрузятся:

```
films/templatetags/
├── __init__.py   ← обязателен, может быть пустым
└── film_tags.py
```

### Статические файлы в продакшне

В режиме разработки (`DEBUG = True`) Django сам обслуживает статические файлы. В продакшне этого не происходит — нужно запустить команду `collectstatic`, которая собирает все статические файлы в папку `STATIC_ROOT`, откуда их раздаёт Nginx. Разберём это в модуле 9 при деплое.

---

## Итоговая структура проекта после урока

```
filmsite/
├── static/
│   └── css/
│       └── base.css
├── templates/
│   └── base.html
├── filmsite/
│   └── settings.py
└── films/
    ├── static/
    │   └── films/
    │       └── css/
    │           └── films.css
    ├── templates/
    │   └── films/
    │       ├── index.html
    │       ├── about.html
    │       ├── film_list.html
    │       ├── film_detail.html
    │       └── includes/
    │           ├── film_card.html
    │           └── latest_films.html
    ├── templatetags/
    │   ├── __init__.py
    │   └── film_tags.py
    └── views.py
```

---

## Вопросы

1. Чем статические файлы отличаются от медиафайлов в Django?
2. Почему `{% load static %}` нужно писать в каждом шаблоне, который использует статические файлы, — даже если базовый шаблон его уже загружает?
3. В чём разница между `simple_tag` и `inclusion_tag`?
4. Что вернёт `inclusion_tag` — строку или словарь? Почему?
5. Зачем нужен файл `__init__.py` в папке `templatetags`?

---

## Практическая задача

**Тип: расширь проект**

**Часть 1.** Подключи статические файлы к проекту:

1. Убедись, что в `settings.py` настроены `STATIC_URL` и `STATICFILES_DIRS`
2. Создай файл `static/css/base.css` с минимальными стилями на свой вкус (шрифт, отступы, оформление навигации)
3. Подключи его в `base.html` через `{% load static %}` и `{% static %}`

**Часть 2.** Создай пользовательский тег `film_tags`:

1. Создай папку `films/templatetags/` с файлами `__init__.py` и `film_tags.py`
2. Напиши `simple_tag` с именем `current_year`, который возвращает текущий год
3. Используй его в футере `base.html` вместо хардкода: `© {% current_year %} Сайт фильмов`
4. Напиши `inclusion_tag` с именем `latest_films`, который принимает аргумент `count` и рендерит шаблон `films/includes/latest_films.html` со списком фильмов из заглушки
5. Вставь `{% latest_films 3 %}` в `base.html` — например, перед закрывающим тегом `</body>`

---

[Предыдущий урок](lesson06.md) | [Следующий урок](lesson08.md)