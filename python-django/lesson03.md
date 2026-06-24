# Урок 3. GET и POST-запросы. Обработка ошибок. Redirect и reverse

## GET и POST: в чём разница

В прошлом курсе мы разбирали HTTP подробно — методы, статус-коды, структуру запроса и ответа. Здесь не будем повторять теорию, а сразу посмотрим, как это выглядит в Django.

Два метода, с которыми работает большинство веб-приложений:

- **GET** — запрос данных. Параметры передаются в строке URL: `/films/?genre=drama&year=2020`. Ничего не меняет на сервере.
- **POST** — отправка данных. Параметры передаются в теле запроса, не видны в URL. Используется для создания и изменения данных: отправка формы, добавление записи.

В Django оба метода приходят в одно и то же представление. Чтобы обработать их по-разному, проверяем `request.method`:

```python
from django.http import HttpResponse


def add_film(request):
    if request.method == 'POST':
        # данные из формы — в request.POST
        title = request.POST.get('title')
        return HttpResponse(f'Фильм «{title}» добавлен.')
    
    # GET-запрос — показываем форму
    return HttpResponse('Здесь будет форма добавления фильма.')
```

Сейчас мы возвращаем простой текст вместо HTML-формы — шаблоны и настоящие формы появятся в модулях 2 и 5. Но логика ветвления по `request.method` остаётся именно такой.

### Чтение параметров GET-запроса

Параметры из строки запроса доступны через `request.GET`:

```python
def film_list(request):
    genre = request.GET.get('genre', '')      # ?genre=drama
    year = request.GET.get('year', '')        # ?year=2020
    
    response_text = f'Жанр: {genre}, год: {year}' if genre or year else 'Все фильмы'
    return HttpResponse(response_text)
```

Запрос `/films/?genre=drama&year=2020` вернёт: `Жанр: drama, год: 2020`.

Используем `.get()` с дефолтным значением, а не обращение по ключу напрямую — если параметра нет в запросе, `request.GET['genre']` выбросит `KeyError`.

---

## Обработка ошибок

### get_object_or_404

Самая частая ошибка в работе с данными — запрос несуществующей записи. Пользователь заходит на `/films/999/`, а фильма с таким id нет.

Сейчас у нас ещё нет базы данных, поэтому покажем на примере со словарём — структура будет точно такой же, когда появятся модели:

```python
from django.http import HttpResponse, Http404


# Временная замена БД — словарь с фильмами
FILMS = {
    1: 'Крёстный отец',
    2: 'Список Шиндлера',
    3: 'Побег из Шоушенка',
}


def film_detail(request, film_id):
    if film_id not in FILMS:
        raise Http404(f'Фильм с id={film_id} не найден')
    
    return HttpResponse(f'Фильм: {FILMS[film_id]}')
```

Исключение `Http404` — это сигнал Django вернуть ответ `404 Not Found`. В режиме разработки (`DEBUG = True`) Django покажет подробную отладочную страницу. В продакшне — стандартную страницу 404, которую можно кастомизировать.

Когда в модуле 3 мы подключим базу данных, Django даст нам готовый инструмент — `get_object_or_404()`. Он делает то же самое, но короче:

```python
# Так это будет выглядеть с моделями (модуль 3):
from django.shortcuts import get_object_or_404
from .models import Film

def film_detail(request, film_id):
    film = get_object_or_404(Film, id=film_id)
    return HttpResponse(f'Фильм: {film.title}')
```

Запомни эту функцию — она появится в каждом представлении, которое работает с конкретной записью.

### Пользовательские обработчики ошибок

По умолчанию Django показывает стандартные страницы для ошибок `404` и `500`. Их можно заменить собственными — для этого достаточно создать шаблоны с именами `404.html` и `500.html` в корневой папке шаблонов. Это сделаем в модуле 2, когда займёмся шаблонами.

Но есть и программный способ — переопределить обработчики в корневом `urls.py`:

```python
# filmsite/urls.py
from django.contrib import admin
from django.urls import path, include

from films import views as film_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('films.urls')),
]

# Пользовательские обработчики ошибок
handler404 = film_views.page_not_found
handler500 = film_views.server_error
```

```python
# films/views.py
def page_not_found(request, exception):
    return HttpResponse('Страница не найдена. Вернитесь на главную.', status=404)


def server_error(request):
    return HttpResponse('Произошла ошибка сервера. Мы уже работаем над этим.', status=500)
```

*Обрати внимание: `handler404` принимает два аргумента — `request` и `exception`, а `handler500` — только `request`.*

*Пользовательские обработчики `handler404` и `handler500` работают только при `DEBUG=False`. В режиме разработки (`DEBUG=True`) Django показывает собственные отладочные страницы ошибок.*

*Если вы решили проверить работу переопределенных обработчиков, замените вот эти две настройки в `settings.py`:*

```python
DEBUG = False
ALLOWED_HOSTS = ['127.0.0.1', 'localhost']
```

---

## Redirect: перенаправление

Перенаправление — это ответ сервера, который говорит браузеру: «перейди по другому адресу». Используется, например, после отправки формы: пользователь отправил данные через POST, сервер сохранил их и перенаправляет на страницу с результатом.

Это стандартный паттерн веб-разработки — **Post/Redirect/Get (PRG)**. Без него при обновлении страницы браузер повторно отправит POST-запрос, и данные запишутся дважды.

```python
from django.http import HttpResponse, Http404
from django.shortcuts import redirect


def add_film(request):
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        
        if not title:
            return HttpResponse('Название фильма не может быть пустым.', status=400)
        
        # Здесь будет сохранение в БД (модуль 3)
        # После сохранения — перенаправляем на список фильмов
        return redirect('/films/')
    
    return HttpResponse('Здесь будет форма добавления фильма.')
```

Функция `redirect()` принимает URL в виде строки и возвращает ответ с кодом `302 Found`.

Передавать URL жёстко закодированной строкой — плохая практика. Если маршрут изменится, нужно будет искать все вхождения этой строки по всему проекту. Для этого существует `reverse()`.

---

## reverse: строим URL по имени маршрута

Функция `reverse()` принимает имя маршрута и возвращает соответствующий URL:

```python
from django.urls import reverse

reverse('film_list')   # вернёт '/films/'
reverse('index')       # вернёт '/'
```

Если маршрут динамический и требует параметров, передаём их через `kwargs`:

```python
reverse('film_detail', kwargs={'film_id': 7})   # вернёт '/films/7/'
```

Теперь перепишем `redirect()` с использованием `reverse()`:

```python
from django.shortcuts import redirect
from django.urls import reverse


def add_film(request):
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        
        if not title:
            return HttpResponse('Название фильма не может быть пустым.', status=400)
        
        # Перенаправляем по имени маршрута, а не по жёсткой строке
        return redirect(reverse('film_list'))
    
    return HttpResponse('Здесь будет форма добавления фильма.')
```

На практике `redirect()` умеет принимать имя маршрута напрямую, без явного вызова `reverse()`:

```python
return redirect('film_list')              # статический маршрут
return redirect('film_detail', film_id=7) # динамический маршрут
```

Это просто синтаксический сахар — внутри Django всё равно вызывает `reverse()`. Но явный `reverse()` пригодится, когда нужно получить URL не для редиректа, а для других целей — например, передать в шаблон или в JSON-ответ.

---

## Подводные камни

### redirect() после POST — обязательно

Если представление обработало POST-запрос и вернуло `HttpResponse` напрямую — при обновлении страницы браузер предложит повторно отправить данные. Это приводит к дублированию записей в базе. Всегда используй паттерн PRG: после POST делай `redirect()`.

### reverse() вне контекста запроса

`reverse()` можно вызывать в представлениях и шаблонах, но не на уровне модуля — в момент импорта маршруты могут быть ещё не загружены:

```python
# Не работает — вызывается при импорте модуля, до загрузки маршрутов
from django.urls import reverse
FILM_LIST_URL = reverse('film_list')

# Правильно — вызывается внутри функции, когда маршруты уже загружены
def some_view(request):
    url = reverse('film_list')
    return redirect(url)
```

### NoReverseMatch

Если передать в `reverse()` несуществующее имя маршрута или забыть передать обязательный параметр — Django выбросит исключение `NoReverseMatch`. Это частая ошибка при переименовании маршрутов:

```python
# В urls.py переименовали 'film_list' в 'films'
# В views.py забыли обновить:
reverse('film_list')   # NoReverseMatch
reverse('films')       # Перенаправление получилось
```

---

## Итоговый код урока

```python
# films/views.py
from django.http import HttpResponse, Http404
from django.shortcuts import redirect
from django.urls import reverse


FILMS = {
    1: 'Крёстный отец',
    2: 'Список Шиндлера',
    3: 'Побег из Шоушенка',
}


def index(request):
    return HttpResponse('Добро пожаловать на сайт фильмов!')


def about(request):
    return HttpResponse('Сайт-каталог фильмов. Здесь собраны лучшие фильмы всех времён.')


def film_list(request):
    genre = request.GET.get('genre', '')
    year = request.GET.get('year', '')
    response_text = f'Жанр: {genre}, год: {year}' if genre or year else 'Все фильмы'
    return HttpResponse(response_text)


def film_detail(request, film_id):
    if film_id not in FILMS:
        raise Http404(f'Фильм с id={film_id} не найден')
    return HttpResponse(f'Фильм: {FILMS[film_id]}')


def add_film(request):
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        if not title:
            return HttpResponse('Название фильма не может быть пустым.', status=400)
        return redirect(reverse('film_list'))
    return HttpResponse('Здесь будет форма добавления фильма.')


def page_not_found(request, exception):
    return HttpResponse('Страница не найдена.', status=404)


def server_error(request):
    return HttpResponse('Произошла ошибка сервера.', status=500)
```

```python
# films/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('about/', views.about, name='about'),
    path('films/', views.film_list, name='film_list'),
    path('films/<int:film_id>/', views.film_detail, name='film_detail'),
    path('films/add/', views.add_film, name='add_film'),
    path('directors/<int:director_id>/', views.director_detail, name='director_detail'),
]
```

---

## Вопросы

1. Чем отличается GET от POST? В каких случаях используется каждый из них?
2. Что такое паттерн Post/Redirect/Get и зачем он нужен?
3. В чём преимущество `reverse()` перед жёстко заданной строкой URL?
4. Как передать параметры в `reverse()` для динамического маршрута?
5. Что произойдёт, если вызвать `raise Http404` внутри представления?

---

## Практическая задача

**Тип: допиши код**

Тебе дано представление `search_film`. Оно должно:

1. Принимать поисковый запрос из параметра `q` в строке URL (`/films/search/?q=крёстный`)
2. Если параметр `q` пустой или отсутствует — возвращать ответ `'Введите название фильма для поиска.'` со статусом `400`
3. Если параметр есть — возвращать строку вида `'Результаты поиска по запросу: крёстный'`
4. Маршрут доступен по адресу `/films/search/` с именем `search_film`

Допиши пропущенные части:

```python
# films/views.py
def search_film(request):
    query = ___________________________
    
    if not query:
        return ___________________________
    
    return HttpResponse(f'Результаты поиска по запросу: {query}')
```

```python
# films/urls.py — добавь маршрут
urlpatterns = [
    ...
    ___________________________
]
```

---

[Предыдущий урок](lesson02.md) | [Следующий урок](lesson04.md)