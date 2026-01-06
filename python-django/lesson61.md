# Модуль 9. Урок 61. Авторизация через email. Профайл пользователя

К этому моменту в проекте **cinemahub** уже реализованы:

* регистрация пользователей;
* авторизация через `LoginView`;
* защита представлений с помощью `login_required` и `LoginRequiredMixin`.

Однако всё это пока опирается на стандартную модель поведения Django — **вход по username и паролю**.
На практике же пользователю гораздо привычнее и удобнее использовать **email** как логин.

В этом уроке мы решим сразу две важные задачи:

1. Реализуем **авторизацию по email**.
2. Создадим **страницу профиля пользователя**, где он сможет редактировать свои данные.

---

## Как Django аутентифицирует пользователя по умолчанию

По умолчанию Django использует механизм аутентификации через backend
`django.contrib.auth.backends.ModelBackend`.

Он:

* ищет пользователя по полю `username`;
* проверяет пароль;
* возвращает объект пользователя или `None`.

В `settings.py` это можно увидеть (или явно указать):

```python
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]
```

Важно понимать:
**Django допускает использование нескольких backend’ов одновременно**.
Это означает, что мы можем:

* добавить собственный способ входа;
* при этом не ломать стандартный механизм.

---

## Идея авторизации через email

Мы хотим, чтобы пользователь мог:

* вводить email и пароль;
* при этом Django находил пользователя по `email`, а не по `username`.

Для этого мы создадим **собственный backend аутентификации**, который:

* будет искать пользователя по email;
* проверять пароль стандартным способом;
* возвращать пользователя, если данные верны.

---

## Создание собственного backend аутентификации

Создадим файл:

**`users/authentication.py`**

```python
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model
```

```python
class EmailAuthBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        user_model = get_user_model()
        try:
            user = user_model.objects.get(email=username)  # из input username теперь сможем получать email
            if user.check_password(password):
                return user
            return None
        except (user_model.DoesNotExist, user_model.MultipleObjectsReturned):
            return None
```

### Что здесь происходит

* `authenticate()` — ключевой метод любого backend’а.
* Мы:

  * получаем модель пользователя через `get_user_model()`;
  * ищем пользователя по `email`;
  * проверяем пароль через `check_password()`.

Если что-то пошло не так — возвращаем `None`, и Django попробует следующий backend.

---

## Реализация метода get_user

Django использует метод `get_user()` для:

* восстановления пользователя из сессии;
* работы `request.user`.

Добавим его в тот же класс:

```python
    def get_user(self, user_id):
        user_model = get_user_model()
        try:
            return user_model.objects.get(pk=user_id)
        except user_model.DoesNotExist:
            return None
```

---

## Подключение backend’а в settings.py

Теперь сообщим Django, что у нас появился новый способ аутентификации.

**Файл:** `settings.py`

```python
AUTHENTICATION_BACKENDS = [
    'users.authentication.EmailAuthBackend',
    'django.contrib.auth.backends.ModelBackend',
]
```

Важно:

* порядок имеет значение;
* сначала Django попытается аутентифицировать по email;
* если не получится — по username.

---

## Проверка авторизации через email

1. Запустите сервер.
2. Перейдите на страницу входа.
3. Введите **email** и пароль.
4. Убедитесь, что вход выполнен успешно.

Если вход не работает:

* проверьте, что email уникален;
* убедитесь, что форма входа действительно передаёт `email`, а не `username`.
* убедитесь, что в `EmailAuthBackend` в поле `email` присваивается значение из поля `username`.

---

## Зачем нужен профиль пользователя

После регистрации и входа пользователь ожидает:

* увидеть свои данные;
* иметь возможность их изменить.

Для этого мы создадим страницу **профиля пользователя**.

---

## Шаблон профиля пользователя

**Файл:** `users/templates/users/profile.html`

```html
{% extends 'base.html' %}

{% block content %}
<h1>{{ title }}</h1>

<form method="post">
  {% csrf_token %}

  <div class="form-error">
    {{ form.non_field_errors }}
  </div>

  {% for f in form %}
    <p>
      <label for="{{ f.id_for_label }}">{{ f.label }}:</label>
      {{ f }}
    </p>
    <div class="form-error">{{ f.errors }}</div>
  {% endfor %}

  <p>
    <button type="submit">Сохранить</button>
  </p>
</form>
{% endblock %}
```

---

## Форма профиля пользователя

**Файл:** `users/forms.py`

```python
from django import forms
from django.contrib.auth import get_user_model
```

```python
class ProfileUserForm(forms.ModelForm):
    email = forms.CharField(
        disabled=True,
        label='E-mail',
        widget=forms.TextInput(attrs={'class': 'form-input'})
    )

    class Meta:
        model = get_user_model()
        fields = ['email', 'first_name', 'last_name']
        labels = {
            'first_name': 'Имя',
            'last_name': 'Фамилия',
        }
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-input'}),
            'last_name': forms.TextInput(attrs={'class': 'form-input'}),
        }
```

### Почему email disabled

Email:

* используется как логин;
* участвует в аутентификации;
* изменение его без подтверждения — плохая практика.

---

## Представление профиля пользователя

Используем `UpdateView`, так как мы **редактируем существующий объект**.

**Файл:** `users/views.py`

```python
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import get_user_model
from django.urls import reverse_lazy
from django.views.generic import UpdateView
from .forms import ProfileUserForm
```

```python
class ProfileUser(LoginRequiredMixin, UpdateView):
    model = get_user_model()
    form_class = ProfileUserForm
    template_name = 'users/profile.html'
    extra_context = {'title': 'Профиль пользователя'}

    def get_success_url(self):
        return reverse_lazy('users:profile')

    def get_object(self, queryset=None):
        return self.request.user
```

### Ключевой момент

Метод `get_object()` гарантирует, что:

* пользователь может редактировать **только свой профиль**;
* никакие ID в URL не используются.

---

## Маршрут профиля

**Файл:** `users/urls.py`

```python
from django.urls import path
from .views import ProfileUser

app_name = 'users'

urlpatterns = [
    path('profile/', ProfileUser.as_view(), name='profile'),
]
```

---

## Ссылка на профиль в base.html

**Файл:** `templates/base.html`

```html
<li class="last">
  <a href="{% url 'users:profile' %}">{{ user.email }}</a> |
  <a href="{% url 'users:logout' %}">Выйти</a>
</li>
```

---

## Проверка результата

1. Авторизуйтесь через email.
2. Перейдите в профиль.
3. Измените имя или фамилию.
4. Сохраните изменения.
5. Обновите страницу — данные должны сохраниться.

---

## Типичные ошибки

**Ошибка:** форма не открывается
**Причина:** отсутствует `LoginRequiredMixin`

**Ошибка:** редактируется не тот пользователь
**Причина:** не переопределён `get_object()`

**Ошибка:** email можно изменить
**Причина:** забыли `disabled=True`

---

## Практические задания

## Задание 1

Добавьте в профиль отображение даты регистрации пользователя `date_joined`. Пользователь может только видеть ее.

---

## Задание 2

Измените отображение имени пользователя в меню на `first_name`.

---

## Сравнить решение

### Решение задания 1

```python
fields = ['email', 'first_name', 'last_name', 'date_joined']
```

и

```python
date_joined = forms.DateTimeField(disabled=True, label='Дата регистрации')
```

---

### Решение задания 2

```html
{{ user.first_name|default:user.email }}
```

---

## Вопросы

1. Зачем Django поддерживает несколько backend’ов аутентификации?
2. Где происходит проверка пароля при входе?
3. Почему важно реализовать `get_user()`?
4. В чём разница между `CreateView` и `UpdateView`?
5. Почему email лучше не разрешать менять?
6. Что делает `LoginRequiredMixin`?
7. Как Django понимает, какого пользователя редактировать?
8. Почему профиль нельзя реализовать через `DetailView`?

---

[Предыдущий урок](lesson60.md) | [Следующий урок](lesson62.md)
