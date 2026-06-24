# Урок 4. Введение в DTL. render() и передача данных в шаблон

## Что такое шаблон и зачем он нужен

В предыдущих трёх уроках все наши представления возвращали `HttpResponse` с текстовой строкой. Это работает, но в реальном приложении страница — это HTML-документ с разметкой, стилями, изображениями. Собирать такой документ конкатенацией строк в Python-коде — это нечитаемо и неудобно.

Шаблон решает эту проблему: HTML живёт в отдельном файле, а Python-код только передаёт в него данные. Это прямое следствие архитектуры MTV — **Template** отвечает за представление данных, **View** — за логику.

Django использует собственный язык шаблонов — **DTL (Django Template Language)**. Он намеренно ограничен: в шаблонах нельзя писать произвольный Python-код. Это не недостаток, а осознанное решение — логика должна быть в представлениях, а не в HTML.

---

## Настройка шаблонов

Django ищет шаблоны по путям, которые указаны в `settings.py`. Откроем его и найдём раздел `TEMPLATES`:

```python
# filmsite/settings.py
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],   # <- добавляем эту строку
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]
```

Две ключевые настройки:

- `'DIRS': [BASE_DIR / 'templates']` — папка для общих шаблонов проекта (навигация, базовый макет). Мы её добавили.
- `'APP_DIRS': True` — Django также ищет шаблоны внутри каждого приложения в папке `templates/`. Это уже включено по умолчанию.

### Структура папок для шаблонов

Мы будем держать шаблоны приложения внутри самого приложения — это удобнее при масштабировании проекта:

```
filmsite/
├── filmsite/
│   └── settings.py
├── films/
│   ├── templates/
│   │   └── films/          # <- поддиректория с именем приложения
│   │       ├── index.html
│   │       ├── film_list.html
│   │       └── film_detail.html
│   ├── views.py
│   └── urls.py
└── templates/              # <- общие шаблоны проекта (появятся в уроке 6)
```

Поддиректория `films/` внутри `templates/` — это важная деталь. Без неё Django может перепутать шаблоны разных приложений, если у них одинаковые имена файлов. Обращение к шаблону выглядит так: `'films/index.html'`, а не просто `'index.html'`.

---

## Функция render()

До этого мы возвращали `HttpResponse('строка')`. Теперь используем `render()` — она загружает шаблон, подставляет данные и возвращает готовый `HttpResponse`:

```python
from django.shortcuts import render

def index(request):
    return render(request, 'films/index.html')
```

`render()` принимает три аргумента:

| Аргумент | Обязательный | Что это |
|---|---|---|
| `request` | да | Объект запроса — всегда первым |
| `'films/index.html'` | да | Путь к шаблону относительно папки `templates/` |
| `context` | нет | Словарь с данными для шаблона |

Третий аргумент — **контекст** — это и есть механизм передачи данных из представления в шаблон.

---

## Создаём первые шаблоны

### Главная страница

Создаём файл `films/templates/films/index.html`:

```html
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>Сайт фильмов</title>
</head>
<body>
    <h1>Добро пожаловать на сайт фильмов!</h1>
    <p>Здесь собраны лучшие фильмы всех времён.</p>
    <a href="/films/">Перейти к каталогу</a>
</body>
</html>
```

Обновляем представление:

```python
# films/views.py
from django.shortcuts import render


def index(request):
    return render(request, 'films/index.html')
```

---

## Передача данных в шаблон

Шаблон без данных — это статическая HTML-страница. Чтобы страница была динамической, передаём данные через словарь контекста.

### Передача одного значения

```python
def index(request):
    context = {
        'title': 'Лучшие фильмы всех времён',
    }
    return render(request, 'films/index.html', context)
```

В шаблоне обращаемся к переменной через двойные фигурные скобки:

```html
<h1>{{ title }}</h1>
```

Django подставит значение переменной `title` из контекста.

### Передача списка

Сейчас у нас ещё нет базы данных, поэтому используем список словарей — такая же структура будет возвращаться из QuerySet в модуле 3:

```python
def film_list(request):
    films = [
        {'id': 1, 'title': 'Крёстный отец', 'year': 1972},
        {'id': 2, 'title': 'Список Шиндлера', 'year': 1993},
        {'id': 3, 'title': 'Побег из Шоушенка', 'year': 1994},
    ]
    context = {
        'films': films,
        'total': len(films),
    }
    return render(request, 'films/film_list.html', context)
```

Шаблон `films/templates/films/film_list.html`:

```html
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>Каталог фильмов</title>
</head>
<body>
    <h1>Каталог фильмов</h1>
    <p>Всего фильмов: {{ total }}</p>

    <ul>
        {% for film in films %}
            <li>{{ film.title }} ({{ film.year }})</li>
        {% endfor %}
    </ul>
</body>
</html>
```

Здесь мы впервые видим два синтаксических элемента DTL:

- `{{ переменная }}` — **вывод значения**
- `{% тег %}` — **логика**: циклы, условия, включения

Тег `{% for %}` разберём подробнее в следующем уроке. Сейчас важно понять главное: данные из контекста доступны в шаблоне по имени ключа словаря.

### Передача объекта

Если в контексте словарь или объект — обращаемся к его атрибутам через точку:

```python
def film_detail(request, film_id):
    # Временная заглушка вместо БД
    film = {'id': film_id, 'title': 'Крёстный отец', 'year': 1972, 'description': 'Классика мирового кино.'}
    context = {
        'film': film,
    }
    return render(request, 'films/film_detail.html', context)
```

```html
<!-- films/templates/films/film_detail.html -->
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>{{ film.title }}</title>
</head>
<body>
    <h1>{{ film.title }}</h1>
    <p>Год выпуска: {{ film.year }}</p>
    <p>{{ film.description }}</p>
    <a href="/films/">← Назад к каталогу</a>
</body>
</html>
```

Точечная нотация `{{ film.title }}` работает одинаково для словарей (`film['title']`), объектов (`film.title`) и даже индексов списков (`films.0`). Django пробует все варианты по порядку.

---

## Как DTL обрабатывает переменные

Несколько важных деталей о поведении DTL:

**Несуществующая переменная** не вызывает ошибку — Django просто подставит пустую строку. Это защищает от падений шаблона, но может скрывать опечатки. В режиме разработки полезно включить `string_if_invalid` в настройках:

```python
# settings.py — только для разработки
TEMPLATES = [
    {
        ...
        'OPTIONS': {
            'string_if_invalid': '[MISSING: %s]',  # покажет имя пропущенной переменной
        },
    },
]
```

**Автоэкранирование** — DTL автоматически экранирует HTML-символы в переменных. Если передать строку `'<script>alert(1)</script>'`, в шаблоне она отобразится как безопасный текст, а не выполнится как код. Это защита от XSS-атак.

---

## Подводные камни

### Шаблон не найден

Если Django не может найти шаблон, он выбросит `TemplateDoesNotExist`. Чаще всего это означает одно из трёх:

```
# 1. Опечатка в пути
render(request, 'film_list.html')         # нет поддиректории приложения
render(request, 'films/film_list.html')   

# 2. Неправильная структура папок
films/templates/film_list.html            
films/templates/films/film_list.html      

# 3. APP_DIRS = False в settings.py — Django не смотрит внутрь приложений
```

### Контекст — это всегда словарь

```python
# Частая ошибка новичков — передать не словарь
return render(request, 'films/index.html', title)

# Правильно — обязательно словарь
return render(request, 'films/index.html', {'title': title})
```

---

## Итоговый код урока

```python
# films/views.py
from django.shortcuts import render, get_object_or_404
from django.http import Http404


FILMS = [
    {'id': 1, 'title': 'Крёстный отец', 'year': 1972, 'description': 'Классика мирового кино.'},
    {'id': 2, 'title': 'Список Шиндлера', 'year': 1993, 'description': 'История Оскара Шиндлера.'},
    {'id': 3, 'title': 'Побег из Шоушенка', 'year': 1994, 'description': 'История о надежде и свободе.'},
]


def index(request):
    context = {
        'title': 'Лучшие фильмы всех времён',
    }
    return render(request, 'films/index.html', context)


def film_list(request):
    context = {
        'films': FILMS,
        'total': len(FILMS),
    }
    return render(request, 'films/film_list.html', context)


def film_detail(request, film_id):
    film = next((f for f in FILMS if f['id'] == film_id), None)
    if film is None:
        raise Http404('Фильм не найден')
    return render(request, 'films/film_detail.html', {'film': film})
```

---

## Вопросы

1. Чем `render()` отличается от `HttpResponse()`? Когда использовать каждый из них?
2. Что такое контекст (передаётся третьим аргументом в `render()`) в Django-шаблоне? Какой тип данных он принимает?
3. Как в DTL обратиться к атрибуту объекта? Работает ли это одинаково для словарей и объектов?
4. Что произойдёт, если в шаблоне обратиться к переменной, которой нет в контексте?
5. Зачем создавать поддиректорию с именем приложения внутри `templates/`? Что будет, если этого не делать?

---

## Практическая задача

**Тип: расширь проект**

Добавь страницу «О сайте» с HTML-шаблоном.

**Требования:**

1. Создай шаблон `films/templates/films/about.html`
2. Шаблон должен содержать заголовок и два абзаца текста о сайте
3. В представлении `about` передай в шаблон контекст с двумя переменными:
   - `title` — заголовок страницы (например, `'О нашем сайте'`)
   - `film_count` — количество фильмов в каталоге (возьми `len(FILMS)`)
4. В шаблоне выведи обе переменные
5. Страница должна открываться по адресу `/about/`

---

[Предыдущий урок](lesson03.md) | [Следующий урок](lesson05.md)