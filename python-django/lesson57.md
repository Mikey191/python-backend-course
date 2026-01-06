# Модуль 9. Урок 57. Классы `LoginView`, `LogoutView` и `AuthenticationForm`

В предыдущем уроке мы реализовали авторизацию пользователей с помощью **функционального представления**. Такой подход полезен для понимания внутренней логики Django, но на практике используется не всегда.

Django предоставляет **готовые классы представлений**, которые решают ту же задачу:

* обрабатывают форму входа;
* проверяют учетные данные;
* создают и удаляют сессии;
* обрабатывают ошибки.

В этом уроке мы научимся использовать эти классы, адаптировать их под проект **cinemahub** и понимать, когда они предпочтительнее ручной реализации.

---

## Зачем нужны стандартные классы авторизации

Функциональные представления дают гибкость, но имеют и недостатки:

* больше кода;
* выше вероятность ошибок;
* сложнее поддерживать проект.

Классы Django решают эти проблемы:

* логика авторизации уже реализована и протестирована;
* код становится короче и чище;
* поведение легко настраивается через переопределение атрибутов и методов.

---

## Основные классы, с которыми мы будем работать

В этом уроке мы разберём три ключевых компонента:

* **`LoginView`** — отвечает за вход пользователя;
* **`LogoutView`** — выполняет выход из системы;
* **`AuthenticationForm`** — стандартная форма аутентификации.

---

## Переход от функции к классу `LoginView`

Начнём с замены функции `login_user()` на класс-представление.

### Файл `users/views.py`

```python
from django.contrib.auth.views import LoginView
from django.contrib.auth.forms import AuthenticationForm

class LoginUser(LoginView):
    form_class = AuthenticationForm
    template_name = "users/login.html"
    extra_context = {
        "title": "Авторизация в Cinemahub"
    }
```

---

### Что здесь происходит

* `LoginView` уже содержит всю логику:

  * проверку данных;
  * вызов `authenticate()` и `login()`;
  * обработку ошибок.
* `form_class` — указываем, какую форму использовать.
* `template_name` — путь к HTML-шаблону.
* `extra_context` — дополнительные данные, доступные в шаблоне.

Мы **не пишем логику входа вручную**, а используем готовый механизм Django.

---

## Подключение маршрута

Теперь заменим маршрут входа на класс-представление.

### Файл `users/urls.py`

```python
from django.urls import path
from .views import LoginUser

app_name = "users"

urlpatterns = [
    path("login/", LoginUser.as_view(), name="login"),
]
```

---

## Проверка работы `LoginView`

1. Запустите сервер:

   ```bash
   python manage.py runserver
   ```
2. Перейдите по адресу:

   ```
   /users/login/
   ```
3. Введите корректные данные пользователя.

Если авторизация проходит успешно — значит `LoginView` работает корректно.

---

## Перенаправление после успешного входа

### Поведение по умолчанию

Если ничего не настраивать, Django попытается перенаправить пользователя на:

```
/accounts/profile/
```

Такого URL в проекте **cinemahub** нет, поэтому это приведёт к ошибке 404.

---

### Способ 1. Переопределение `get_success_url()`

#### Файл `users/views.py`

```python
from django.urls import reverse_lazy

class LoginUser(LoginView):
    form_class = AuthenticationForm
    template_name = "users/login.html"

    def get_success_url(self):
        return reverse_lazy("movies:movie_list")
```

Теперь после входа пользователь попадает на страницу со списком фильмов.

---

### Способ 2. Глобальная настройка в `settings.py`

```python
LOGIN_REDIRECT_URL = "movies:movie_list"
```

Этот способ удобен, если логика одинакова для всего проекта.

---

## Дополнительные настройки авторизации

В `settings.py` также часто используют:

```python
LOGIN_URL = "users:login"
LOGOUT_REDIRECT_URL = "movies:movie_list"
```

* `LOGIN_URL` — куда перенаправлять неавторизованных пользователей;
* `LOGOUT_REDIRECT_URL` — куда перенаправлять после выхода.

---

## Улучшение формы авторизации

### Что такое `AuthenticationForm`

`AuthenticationForm` — это стандартная форма Django, которая:

* проверяет логин и пароль;
* обрабатывает ошибки;
* передаёт сообщения об ошибках в шаблон.

---

### Улучшенное отображение ошибок

#### Файл `users/templates/users/login.html`

```html
<h1>{{ title }}</h1>

<form method="post">
    {% csrf_token %}

    {% if form.non_field_errors %}
        <div class="form-error">
            {{ form.non_field_errors }}
        </div>
    {% endif %}

    {% for field in form %}
        <p>
            {{ field.label_tag }}<br>
            {{ field }}
            {{ field.errors }}
        </p>
    {% endfor %}

    <button type="submit">Войти</button>
</form>
```

Теперь ошибки входа будут отображаться пользователю корректно.

---

## Расширение `AuthenticationForm`

Иногда нужно изменить внешний вид формы, не переписывая логику.

### Файл `users/forms.py`

```python
from django.contrib.auth.forms import AuthenticationForm
from django import forms

class LoginUserForm(AuthenticationForm):
    username = forms.CharField(
        label="Логин",
        widget=forms.TextInput(attrs={"class": "form-input"})
    )
    password = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput(attrs={"class": "form-input"})
    )
```

И подключаем её в `LoginView`:

```python
class LoginUser(LoginView):
    form_class = LoginUserForm
    template_name = "users/login.html"
```

---

## Параметр `next`

Django автоматически поддерживает параметр `next`.

Пример URL:

```
/users/login/?next=/movies/add/
```

После успешного входа пользователь будет перенаправлён на `/movies/add/`.

Чтобы это работало, добавьте в шаблон:

```html
<input type="hidden" name="next" value="{{ next }}">
```

---

## Класс `LogoutView`

Теперь заменим функцию выхода стандартным классом.

### Файл `users/urls.py`

```python
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path("logout/", LogoutView.as_view(), name="logout"),
]
```

`LogoutView`:

* удаляет данные сессии;
* делает пользователя анонимным;
* перенаправляет на `LOGOUT_REDIRECT_URL`.

---

## Проверка выхода из системы

1. Авторизуйтесь.
2. Перейдите по адресу:

   ```
   /users/logout/
   ```
3. Проверьте, что:

   * пользователь вышел из системы;
   * повторный вход в защищённые страницы требует авторизации.

---

## Логика отображения пользователя в базовом шаблоне.

```html
<header>
  {% if request.user.is_authenticated %}
    <p>Привет, {{ request.user.username }}!</p>
    <form action="{% url 'users:logout' %}" method="post" style="display:inline;">
        {% csrf_token %}
        <button type="submit">Выйти</button>
    </form>
  {% else %}
    <a href="{% url 'users:login' %}">Войти</a> |
  {% endif %}
  <h1><a href="{% url 'movies:index' %}">Кино-проекты</a></h1>
  <nav>
    <!-- Общие блоки тегов/жанров/режиссёров можно сюда включать -->
  </nav>
</header>
```

## Типичные ошибки и их причины

### После входа ошибка 404

Причина — не настроен `LOGIN_REDIRECT_URL` или `get_success_url()`.

---

### Форма не отображается

Причины:

* неверный путь к шаблону;
* ошибка в `template_name`.

---

### `LogoutView` не работает

Причина — отсутствует `django.contrib.auth` в `INSTALLED_APPS`.

---

### Ошибка 405 после выхода с использованием LogoutView

Ошибка HTTP 405 (Method Not Allowed) возникает потому, что стандартный класс LogoutView из Django по умолчанию принимает только HTTP метод `POST` для выхода из профиля, а не `GET-запрос`.

## Практические задания

### Задание 1

Измените заголовок страницы входа на
**«Вход для администраторов Cinemahub»**.

---

### Задание 2

Сделайте так, чтобы после выхода пользователь перенаправлялся на страницу списка фильмов (За это отвечает параметр в settings.py `LOGOUT_REDIRECT_URL`).

---

### Задание 3

Переопределите `get_success_url()`, чтобы пользователь всегда попадал на первый опубликованный фильм.

---

## Сравнить решение

### Решение задания 1

```python
extra_context = {"title": "Вход для администраторов Cinemahub"}
```

### Решение задания 2

```python
LOGOUT_REDIRECT_URL = "movies:movie_list"
```

### Решение задания 3

```python
from movies.models import Movie

def get_success_url(self):
    movie = Movie.objects.filter(is_published=True).first()
    return movie.get_absolute_url()
```

---

## Вопросы для самопроверки

1. Чем `LoginView` лучше функционального представления?
2. Где Django хранит логику проверки пароля?
3. Что делает `AuthenticationForm`?
4. Зачем нужен параметр `next`?
5. Как изменить URL после входа?
6. Когда лучше использовать `LOGIN_REDIRECT_URL`?
7. Что делает `LogoutView`?
8. Можно ли использовать собственную форму с `LoginView`?
9. Где обрабатываются ошибки авторизации?

---

[Предыдущий урок](lesson56.md) | [Следующий урок](lesson58.md)