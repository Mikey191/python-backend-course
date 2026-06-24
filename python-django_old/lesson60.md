# Модуль 9. Урок 60. Класс UserCreationForm

## Зачем нам UserCreationForm, если регистрация уже работает

В прошлом уроке мы реализовали регистрацию пользователей **через функцию представления**. Это было сделано осознанно:
важно понять, **как именно Django создаёт пользователя**, где происходит валидация и почему пароль нельзя сохранять напрямую.

Однако Django — это фреймворк, ориентированный на **повторное использование готовых решений**.
Для регистрации пользователей в нём уже существует специальный класс формы — **`UserCreationForm`**.

Задача этого урока:

* перейти от ручной реализации к более идиоматичному Django-подходу;
* разобраться, **что именно делает `UserCreationForm`**;
* переписать регистрацию, используя **классовое представление (`CreateView`)**;
* сохранить возможность расширять форму под нужды проекта *cinemahub*.

---

## Что такое UserCreationForm

`UserCreationForm` — это встроенная форма Django, которая:

* создаёт нового пользователя;
* автоматически добавляет поля `password1` и `password2`;
* проверяет совпадение паролей;
* использует `set_password()` внутри себя.

Проще говоря, она решает **80% задач регистрации**, которые мы писали вручную в прошлом уроке.

Но:

* она не знает ничего о нашем интерфейсе;
* не проверяет уникальность email;
* не учитывает стиль проекта.

Поэтому мы **наследуемся** от неё и дорабатываем под себя.

---

## Определение формы регистрации на основе UserCreationForm

Начнём с формы.

**Файл:** `users/forms.py`

```python
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model

User = get_user_model()
```

Теперь создадим кастомную форму регистрации.

```python
class RegisterUserForm(UserCreationForm):
    username = forms.CharField(
        label='Логин',
        widget=forms.TextInput(attrs={'class': 'form-input'})
    )
    password1 = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={'class': 'form-input'})
    )
    password2 = forms.CharField(
        label='Повтор пароля',
        widget=forms.PasswordInput(attrs={'class': 'form-input'})
    )

    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'first_name',
            'last_name',
            'password1',
            'password2'
        ]
        labels = {
            'email': 'E-mail',
            'first_name': 'Имя',
            'last_name': 'Фамилия',
        }
        widgets = {
            'email': forms.TextInput(attrs={'class': 'form-input'}),
            'first_name': forms.TextInput(attrs={'class': 'form-input'}),
            'last_name': forms.TextInput(attrs={'class': 'form-input'}),
        }
```

---

## Что мы получили автоматически

Благодаря `UserCreationForm` Django **сам**:

* проверяет, что пароли совпадают;
* проверяет минимальную сложность пароля;
* хэширует пароль;
* создаёт пользователя корректным способом.

Нам **больше не нужен**:

* `clean_password2`;
* ручной вызов `set_password()`.

Это ключевое отличие от прошлого урока.

---

## Добавление проверки уникальности email

По умолчанию Django:

* не требует уникальный email;
* не валидирует его уникальность.

Для проекта **cinemahub** это нежелательно, поэтому добавим проверку.

**Файл:** `users/forms.py`

```python
    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(
                "Пользователь с таким E-mail уже существует"
            )
        return email
```

---

## Обновление шаблона регистрации

Теперь форма стала сложнее, и нам важно:

* видеть ошибки валидации;
* отображать ошибки каждого поля отдельно.

**Файл:** `users/templates/users/register.html`

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
    <button type="submit">Регистрация</button>
  </p>
</form>

{% endblock %}
```

---

## Переход к классовому представлению

Теперь мы можем отказаться от функции `register()` и перейти к **классовому представлению**.

Это логичный шаг:

* форма уже готова;
* Django умеет работать с ней автоматически.

---

## Создание представления RegisterUser

**Файл:** `users/views.py`

```python
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView
from .forms import RegisterUserForm
```

```python
class RegisterUser(CreateView):
    form_class = RegisterUserForm
    template_name = 'users/register.html'
    success_url = reverse_lazy('users:login')
    extra_context = {'title': 'Регистрация'}
```

---

## Разбор ключевых элементов

### CreateView

`CreateView`:

* отображает форму;
* обрабатывает `POST`;
* сохраняет объект в базу;
* перенаправляет при успехе.

В нашем случае объект — **пользователь**.

---

### success_url

```python
success_url = reverse_lazy('users:login')
```

После успешной регистрации пользователь:

* попадает на страницу входа;
* может сразу авторизоваться.

---

### extra_context

```python
extra_context = {'title': 'Регистрация'}
```

Позволяет передавать данные в шаблон **без переопределения методов**.

---

## Настройка маршрута

Обновим маршруты.

**Файл:** `users/urls.py`

```python
from django.urls import path
from .views import RegisterUser

app_name = 'users'

urlpatterns = [
    path('register/', RegisterUser.as_view(), name='register'),
]
```

---

## Проверка результата в браузере

1. Перейдите на страницу `/users/register/`
2. Попробуйте:

   * несовпадающие пароли;
   * слабый пароль;
   * повторяющийся email;
3. Убедитесь, что:

   * ошибки отображаются корректно;
   * пользователь создаётся;
   * пароль хранится в хэшированном виде;
   * вход работает.

---

## Типичные ошибки и причины

**Ошибка:** пароли не совпадают, но форма «валидна»
**Причина:** используется `ModelForm`, а не `UserCreationForm`

**Ошибка:** пользователь создаётся, но не может войти
**Причина:** попытка переопределить `save()` без вызова `super()`

**Ошибка:** email дублируется
**Причина:** отсутствует `clean_email()`

---

## Практические задания

### Задание 1

Сделайте поле `email` обязательным для заполнения.

---

### Задание 2

Измените перенаправление после регистрации на главную страницу со списком фильмов.

---

### Задание 3

Добавьте в шаблон подсказку о требованиях к паролю.

---

## Сравнить решение

### Решение задания 1

```python
email = forms.EmailField(
    label='E-mail',
    required=True,
    widget=forms.TextInput(attrs={'class': 'form-input'})
)
```

---

### Решение задания 2

```python
success_url = reverse_lazy('movies:movie_list')
```

---

### Решение задания 3

```html
<p class="help-text">
  Пароль должен содержать минимум 8 символов
</p>
```

---

## Вопросы

1. Чем `UserCreationForm` отличается от `ModelForm`?
2. Где происходит хэширование пароля?
3. Почему не нужно вручную проверять совпадение паролей?
4. Зачем использовать `reverse_lazy`, а не `reverse`?
5. Что делает `CreateView` автоматически?
6. Где лучше валидировать email?
7. Какие ошибки обрабатываются на уровне формы?
8. В каком месте проще изменить внешний вид формы?

---

[Предыдущий урок](lesson59.md) | [Следующий урок](lesson61.md)