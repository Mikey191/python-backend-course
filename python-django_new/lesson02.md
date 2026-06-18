# Урок 2. Маршрутизация и функции представления. Динамические URL и конвертеры

## Как Django обрабатывает запрос

В прошлом уроке мы написали первое представление и подключили его к маршруту. Сейчас разберём эту механику подробнее — она будет работать одинаково во всех последующих уроках.

Когда браузер отправляет запрос на `/films/`, Django делает следующее:

1. Берёт путь из URL — всё, что идёт после домена
2. Идёт в корневой `urls.py` и перебирает список `urlpatterns` сверху вниз
3. Находит первое совпадение и передаёт запрос в соответствующее представление
4. Представление возвращает ответ — Django отдаёт его браузеру

Если ни один маршрут не совпал — Django возвращает ответ `404 Not Found`.

---

## Функции представления

Функция представления (FBV — Function Based View) — это обычная Python-функция, которая:

- принимает объект `request` первым аргументом
- возвращает объект `HttpResponse` (или его наследника)

```python
from django.http import HttpResponse

def index(request):
    return HttpResponse('Главная страница')
```

Объект `request` содержит всю информацию о входящем запросе. Самые нужные атрибуты сейчас:

| Атрибут | Что содержит |
|---|---|
| `request.method` | Метод запроса: `'GET'` или `'POST'` |
| `request.GET` | Параметры из строки запроса (`?page=2`) |
| `request.POST` | Данные из тела POST-запроса |
| `request.user` | Текущий пользователь (разберём в модуле 7) |

`request.GET` — это словарь (точнее, `QueryDict`) с параметрами из строки запроса. Значение можно получить как `request.GET.get('page')` или `request.GET['page']`. Первый вариант безопаснее: если параметра нет, вернёт `None`, а не выбросит исключение.

> **Связь с прошлым курсом.** В FastAPI параметры запроса описывались через аргументы функции с аннотациями типов, и фреймворк парсил их автоматически. В Django всё то же самое лежит в `request.GET` и `request.POST` — просто в виде словарей, без автоматической валидации. Валидацию мы добавим в модуле 5, когда дойдём до форм.

---

## Статические маршруты

Статический маршрут — это фиксированная строка пути. Мы уже писали такие в первом уроке:

```python
# films/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('about/', views.about, name='about'),
    path('films/', views.film_list, name='film_list'),
]
```

Функция `path()` принимает три аргумента:

- **маршрут** — строка пути, без ведущего слеша
- **представление** — функция, которая обработает запрос
- **name** — имя маршрута для обращения к нему из кода и шаблонов (разберём подробнее в модуле 2)

Добавим в проект список фильмов. Сначала — заглушку, без базы данных:

```python
# films/views.py
from django.http import HttpResponse


def index(request):
    return HttpResponse('Добро пожаловать на сайт фильмов!')


def about(request):
    return HttpResponse('Сайт-каталог фильмов. Здесь собраны лучшие фильмы всех времён.')


def film_list(request):
    return HttpResponse('Список фильмов — скоро здесь будет каталог.')
```

---

## Динамические URL

Страница со списком фильмов — это статический маршрут: один URL, одна страница. Но нам нужна и страница отдельного фильма: `/films/1/`, `/films/2/`, `/films/42/`. Создавать отдельный маршрут для каждого фильма невозможно — их сотни.

Решение — динамический URL с параметром:

```python
# films/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('about/', views.about, name='about'),
    path('films/', views.film_list, name='film_list'),
    path('films/<int:film_id>/', views.film_detail, name='film_detail'),
]
```

Угловые скобки `<int:film_id>` — это захват параметра из URL. Django извлечёт число из пути и передаст его в представление как аргумент `film_id`.

Представление должно принять этот аргумент явно:

```python
def film_detail(request, film_id):
    return HttpResponse(f'Страница фильма с id={film_id}')
```

Теперь запрос на `/films/7/` вызовет `film_detail(request, film_id=7)`.

---

## Конвертеры типов

Часть `int:` перед именем параметра — это конвертер. Он делает две вещи одновременно: проверяет, что значение в URL подходит под тип, и преобразует строку в нужный Python-тип.

Встроенные конвертеры:

| Конвертер | Что принимает | Python-тип |
|---|---|---|
| `int` | Целое положительное число | `int` |
| `str` | Любая строка без слеша (по умолчанию) | `str` |
| `slug` | Строка из букв, цифр, дефисов и подчёркиваний | `str` |
| `uuid` | UUID в стандартном формате | `uuid.UUID` |
| `path` | Любая строка, включая слеши | `str` |

Примеры:

```python
urlpatterns = [
    # /films/42/  → film_id=42 (int)
    path('films/<int:film_id>/', views.film_detail, name='film_detail'),

    # /films/the-godfather/  → slug='the-godfather' (str)
    path('films/<slug:slug>/', views.film_by_slug, name='film_by_slug'),
]
```

Если URL не соответствует конвертеру — Django автоматически вернёт `404`. Например, запрос на `/films/abc/` при конвертере `int` не совпадёт с маршрутом вообще.

> Конвертер `slug` нам понадобится в модуле 3, когда мы добавим поле `SlugField` к модели `Film` и научим Django строить красивые URL вида `/films/the-godfather/` вместо `/films/42/`.

---

Если написать `<film_id>` без конвертера, Django применит `str` по умолчанию — параметр будет строкой. 

```python
urlpatterns = [
    path('films/<film_id>/', views.film_detail, name='film_detail'),
]
```

Запрос `/films/abc/` тоже совпадёт с маршрутом, и в представлении придётся вручную проверять и преобразовывать значение.

---

## Несколько параметров в одном маршруте

В URL можно захватывать несколько параметров одновременно. Пример — маршрут для фильмов, отфильтрованных по году:

```python
# /films/2024/3/  → фильмы 2024 года, страница 3
path('films/<int:year>/<int:page>/', views.films_by_year, name='films_by_year'),
```

```python
def films_by_year(request, year, page):
    return HttpResponse(f'Фильмы {year} года, страница {page}')
```

---

## Подводные камни

### Порядок маршрутов имеет значение

Django перебирает `urlpatterns` сверху вниз и останавливается на первом совпадении. Если поставить более общий маршрут раньше специфичного, специфичный никогда не сработает:

```python
# Неправильно: маршрут со строкой перехватит 'new' раньше, чем до него дойдёт очередь
urlpatterns = [
    path('films/<str:slug>/', views.film_by_slug),
    path('films/new/', views.film_create),   # сюда никогда не дойдёт
]

# Правильно: специфичные маршруты — выше
urlpatterns = [
    path('films/new/', views.film_create),
    path('films/<str:slug>/', views.film_by_slug),
]
```

### Слеш в конце URL

По умолчанию Django ожидает слеш в конце пути: `films/`, а не `films`. Если пользователь зайдёт на `/films` без слеша — Django автоматически перенаправит его на `/films/`. Это поведение регулируется настройкой `APPEND_SLASH = True` в `settings.py` и менять его без необходимости не стоит.

---

## Итоговый urls.py приложения

```python
# films/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('about/', views.about, name='about'),
    path('films/', views.film_list, name='film_list'),
    path('films/<int:film_id>/', views.film_detail, name='film_detail'),
]
```

```python
# films/views.py
from django.http import HttpResponse


def index(request):
    return HttpResponse('Добро пожаловать на сайт фильмов!')


def about(request):
    return HttpResponse('Сайт-каталог фильмов. Здесь собраны лучшие фильмы всех времён.')


def film_list(request):
    return HttpResponse('Список фильмов — скоро здесь будет каталог.')


def film_detail(request, film_id):
    return HttpResponse(f'Страница фильма с id={film_id}')
```

---

## Вопросы

1. Что произойдёт, если ни один маршрут в `urlpatterns` не совпадёт с запрошенным URL?
2. Зачем нужен конвертер типа в динамическом URL? Что будет, если написать `<film_id>` без конвертера?
3. Есть два маршрута: `path('films/<str:slug>/', ...)` и `path('films/new/', ...)`. Какой из них нужно поставить первым и почему?
4. Какой атрибут объекта `request` содержит параметры из строки запроса, например `?page=2`?
5. Чем конвертер `slug` отличается от `str`?

---

## Практическая задача

**Тип: расширь проект**

Добавь в проект страницу режиссёра.

**Требования:**

1. Представление называется `director_detail` и находится в `films/views.py`
2. Оно принимает `director_id` из URL как целое число
3. Доступно по адресу `/directors/<director_id>/`
4. Возвращает строку вида: `'Страница режиссёра с id=5'` (число подставляется из URL)
5. Маршрут имеет имя `director_detail`

Проверь, что:
- `/directors/1/` работает и возвращает правильный текст
- `/directors/abc/` возвращает 404

---

[Предыдущий урок](lesson01.md) | [Следующий урок](lesson03.md)