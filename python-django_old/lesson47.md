# Модуль 8. Урок 47. Введение в CBV (Class Based Views). Классы View и TemplateView

## Введение: зачем Django нужны классы представлений

В предыдущих модулях мы работали с представлениями, написанными в виде функций (`FBV — Function-Based Views`). Такой подход прост и хорошо подходит для небольших задач, однако в реальных проектах, особенно таких как **cinemahub**, функциональные представления очень быстро начинают «расти» и усложняться:

* в них накапливается логика обработки разных типов запросов: `GET`, `POST`, `PUT`, `DELETE`;
* появляются повторяющиеся фрагменты кода, которые сложно поддерживать;
* одни и те же элементы интерфейса (например, формы или фильтры) приходится подключать вручную в каждом представлении.

Чтобы снизить количество дублирования кода и сделать архитектуру более предсказуемой, Django предлагает альтернативу — **классы представлений (CBV, Class-Based Views)**.

Использование CBV позволяет:

* представлять каждое представление как отдельный класс со строгой структурой;
* переопределять только нужные методы;
* применять наследование и `mixins`, тем самым уменьшая повторяемость кода;
* улучшить читаемость проекта и упростить его поддержку.

В этом уроке мы познакомимся с основой всей системы CBV — классом **View**, а также рассмотрим самый простой, но очень полезный класс **TemplateView**.

---

## 1. Базовый класс View

### 1.1. Концепция класса View

Классическое функциональное представление выглядит так:

```python
def movie_list(request):
    ...
```

Мы сами внутри функции определяем, что делать при `GET`, `POST` и других типах запросов.

В CBV та же логика разделяется на методы класса:

* **get()** — обработка GET-запроса
* **post()** — обработка POST-запроса
* **put()** — обработка PUT-запроса
* **delete()** — обработка DELETE-запроса

Django автоматически перенаправляет запрос в нужный метод, если он определён.

Таким образом структура становится предсказуемой: всё, что касается GET — в одном методе, всё, что касается POST — в другом.

---

### 1.2. Создание простого класса-представления

Создадим пример класса, который будет выводить форму добавления фильма (в учебных целях мы создадим временную форму).

### Шаг 1. Создадим простую форму

**Файл:** `movies/forms.py`

```python
from django import forms

class AddMovieForm(forms.Form):
    title = forms.CharField(max_length=255)
    year = forms.IntegerField(min_value=1895, max_value=2050)
```

Эта форма пока не связана с моделью. Модель `Movie` мы подключим позже, в следующих уроках.

---

## 1.3. Создаём класс-представление

**Файл:** `movies/views.py`

```python
from django.views import View
from django.shortcuts import render, redirect
from .forms import AddMovieForm

class AddMovieView(View):
    def get(self, request):
        form = AddMovieForm()
        return render(request, 'movies/add_movie.html', {
            'title': 'Добавление фильма',
            'form': form,
        })

    def post(self, request):
        form = AddMovieForm(request.POST)
        if form.is_valid():
            # В этом уроке мы не сохраняем данные в БД, чтобы не отвлекаться
            print("Форма прошла валидацию:", form.cleaned_data)
            return redirect('movies:add_movie')
        return render(request, 'movies/add_movie.html', {
            'title': 'Добавление фильма',
            'form': form,
        })
```

### Что здесь происходит?

* При GET-запросе (например, при открытии страницы в браузере) вызывается `get()`.
* При POST (например, при отправке формы) вызывается `post()`.
* Логика обработки чётко разделена.
* Шаблон один и тот же, но поведение различается.

---

## 1.4. Подключаем маршрут

**Файл:** `movies/urls.py`

```python
from django.urls import path
from .views import AddMovieView

app_name = 'movies'

urlpatterns = [
    path('add/', AddMovieView.as_view(), name='add_movie'),
]
```

Здесь важно: **во всех CBV вызывается метод `as_view()`**.
Он создаёт функцию, которую Django может использовать как представление.

---

## 1.5. Создаём простой шаблон для формы

**Файл:** `movies/templates/movies/add_movie.html`

```html
<h1>{{ title }}</h1>

<form method="post">
    {% csrf_token %}
    {{ form.as_p }}
    <button type="submit">Сохранить</button>
</form>
```

---

## 1.6. Проверяем результат

После запуска сервера:

* открываем в браузере:
  `http://127.0.0.1:8000/movies/add/`

Ожидаем:

1. Отобразится форма с полями `title` и `year`.
2. При отправке формы без значений появится сообщение об ошибке.
3. Если значения корректные, сервер выведет их в консоли и перенаправит обратно.

Если вы видите ошибку типа:

* *TemplateDoesNotExist* — неверный путь к шаблону
* *ImportError* — неправильно указали путь в urls.py
* *AttributeError: type object 'AddMovieView' has no attribute 'as_view'* — забыли вызвать `as_view()` в маршруте

---

## 2. TemplateView — самый простой способ вывести шаблон

### 2.1. Когда использовать TemplateView

TemplateView используется, когда:

* нужно вывести статическую страницу (например, "О проекте"),
* передать в шаблон фиксированные данные,
* логика представления минимальна.

В отличие от `View`, TemplateView уже реализует метод `get()` и возвращает готовый рендер.

---

### 2.2. Создаём простую главную страницу проекта cinemahub

Предположим, на главной странице мы хотим показать приветствие и список последних фильмов.

### Шаг 1. Создаём представление

**Файл:** `movies/views.py`

```python
from django.views.generic import TemplateView
from .models import Movie

class MoviesHomeView(TemplateView):
    template_name = 'movies/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Cinemahub — каталог фильмов'
        context['last_movies'] = Movie.objects.filter(is_published=True).order_by('-created_at')[:5]
        return context
```

### Разбор

* `template_name` — путь к шаблону.
* `get_context_data()` — метод, в который мы добавляем динамические данные.

В этот метод:

* всегда нужно вызывать `super()`,
* всегда возвращать `context`.

---

### 2.3. Подключаем маршрут

**Файл:** `movies/urls.py`

```python
from .views import MoviesHomeView

urlpatterns = [
    path('', MoviesHomeView.as_view(), name='home'),
]
```

---

### 2.4. Создаём шаблон главной страницы

**Файл:** `movies/templates/movies/home.html`

```html
<h1>{{ title }}</h1>

<h2>Последние добавленные фильмы</h2>

<ul>
    {% for movie in last_movies %}
        <li>{{ movie.title }} ({{ movie.year }})</li>
    {% empty %}
        <li>Фильмов пока нет.</li>
    {% endfor %}
</ul>
```

---

### 2.5. Проверяем

Открываем:

```
http://127.0.0.1:8000/movies/
```

Ожидаем увидеть:

* заголовок,
* список последних пяти опубликованных фильмов.

Если получаете *ObjectDoesNotExist*, то, возможно, у моделей нет данных или неправильно указаны имена полей.

---

## 3. Частые ошибки при работе с CBV

### 3.1. Ошибка: забыли вызвать as_view()

```
TypeError: AddMovieView() missing 1 required positional argument: 'request'
```

Решение:
в `urls.py` всегда нужно писать:

```python
AddMovieView.as_view()
```

---

### 3.2. Ошибка: неверный путь к шаблону

```
TemplateDoesNotExist: movies/home.html
```

Проверьте:

* правильность пути,
* имя папки `templates/movies/`,
* регистр имени файла.

---

### 3.3. Ошибка: используете переменные, которых нет в контексте

Например, забыли добавить `title` в `context`.

Исправление:
добавить в `get_context_data()`.

---

### 3.4. Ошибка в маршрутизации

Если видна ошибка:

```
ImportError: cannot import name MoviesHomeView
```

Проверьте:

* правильный путь в import,
* что класс находится в `movies/views.py`,
* что файл сохранён.

---

## 4. Практические задания

Ниже — задания, которые требуют применения CBV, но не копируют примеры из урока. Решения приведены после заданий.

---

### Задание 1

Создайте CBV, который:

1. отображает форму обратной связи с полями:

   * email
   * message
2. при GET показывает пустую форму;
3. при POST выводит очищенные данные (например, используя `print()`) и возвращает ту же страницу.

Используйте:

* класс `View`,
* форму `forms.Form`,
* шаблон по аналогии с уроком.

---

### Задание 2

Создайте `TemplateView`, который:

1. отображает страницу «О режиссёрах»;
2. в контекст добавляет список всех режиссёров (модель `Director`);
3. выводит их имена в шаблоне.

---

### Задание 3

Создайте CBV, который:

1. принимает GET-параметр `q`;
2. выводит список фильмов, в названии которых встречается эта строка;
3. если параметр отсутствует, список пустой.

Использовать только класс `View`.

---

## Сравнить решение

---

## Решение задания 1

**Файл:** `movies/forms.py`

```python
from django import forms

class ContactForm(forms.Form):
    email = forms.EmailField()
    message = forms.CharField(widget=forms.Textarea)
```

**Файл:** `movies/views.py`

```python
from django.views import View
from django.shortcuts import render
from .forms import ContactForm

class ContactView(View):
    def get(self, request):
        form = ContactForm()
        return render(request, 'movies/contact.html', {'form': form})

    def post(self, request):
        form = ContactForm(request.POST)
        if form.is_valid():
            print(form.cleaned_data)
        return render(request, 'movies/contact.html', {'form': form})
```

**Шаблон:** `movies/templates/movies/contact.html`

```html
<h1>Обратная связь</h1>

<form method="post">
    {% csrf_token %}
    {{ form.as_p }}
    <button type="submit">Отправить</button>
</form>
```

---

## Решение задания 2

**Файл:** `movies/views.py`

```python
from django.views.generic import TemplateView
from .models import Director

class DirectorsInfoView(TemplateView):
    template_name = 'movies/directors_info.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['directors'] = Director.objects.all()
        return context
```

**Шаблон:** `movies/templates/movies/directors_info.html`

```html
<h1>Список режиссёров</h1>

<ul>
    {% for director in directors %}
        <li>{{ director.name }}</li>
    {% empty %}
        <li>Пока нет режиссёров.</li>
    {% endfor %}
</ul>
```

---

## Решение задания 3

**Файл:** `movies/views.py`

```python
from django.views import View
from django.shortcuts import render
from .models import Movie

class MovieSearchView(View):
    def get(self, request):
        query = request.GET.get('q')
        movies = Movie.objects.filter(title__icontains=query) if query else []
        return render(request, 'movies/search.html', {
            'query': query,
            'movies': movies,
        })
```

**Шаблон:** `movies/templates/movies/search.html`

```html
<h1>Результаты поиска</h1>

{% if query %}
    <p>Вы искали: "{{ query }}"</p>
{% else %}
    <p>Введите строку поиска.</p>
{% endif %}

<ul>
    {% for movie in movies %}
        <li>{{ movie.title }}</li>
    {% empty %}
        {% if query %}
            <li>Ничего не найдено.</li>
        {% endif %}
    {% endfor %}
</ul>
```

---

# 5. Вопросы для самопроверки

1. Почему CBV лучше подходят для крупных проектов, чем FBV?
2. Какие методы обрабатывают GET- и POST-запросы в классе View?
3. Для чего нужен метод `as_view()`?
4. Чем TemplateView отличается от View?
5. В каком методе TemplateView добавляют данные в шаблон?
6. Что произойдёт, если забыть вызвать `super().get_context_data()`?
7. Что делает `context` в CBV и почему важно вернуть именно его?
8. Какие ошибки чаще всего возникают при работе с CBV и как их исправить?
9. Можно ли использовать TemplateView для обработки POST? Почему?
10. Как передать в CBV форму и обработать её валидность?

---

[Предыдущий урок](lesson46.md) | [Следующий урок](lesson48.md)