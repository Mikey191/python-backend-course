# Модуль 9. Урок 59. Регистрация пользователей через функции представления

## Зачем нужна собственная регистрация

К этому моменту в проекте **cinemahub** мы уже научились:

- авторизовывать пользователей;
- ограничивать доступ к страницам;
- связывать фильмы с их авторами.

Однако если пользователь **не может создать аккаунт**, весь этот функционал теряет практический смысл.
Да, Django предоставляет готовую модель пользователя и даже встроенные представления, но в реальных проектах почти всегда требуется **собственная логика регистрации**:

- дополнительные поля;
- проверка email;
- контроль паролей;
- кастомные шаблоны.

В этом уроке мы реализуем **полный цикл регистрации пользователя** через **функцию представления**, чтобы глубже понять, как работает механизм аутентификации Django.

---

## Общая схема регистрации

Процесс регистрации в Django почти всегда состоит из четырёх шагов:

1. Пользователь открывает страницу регистрации
2. Django отображает HTML-форму
3. Пользователь отправляет данные
4. Сервер:

   - валидирует данные;
   - создаёт пользователя;
   - хэширует пароль;
   - сохраняет пользователя в базе

Мы реализуем каждый шаг вручную, не скрывая детали.

---

## Шаблон страницы регистрации

Начнём с шаблона. Он почти идентичен форме входа, но это **нормально** — пользователю важна визуальная целостность интерфейса.

**Файл:** `users/templates/users/register.html`

```html
{% extends 'base.html' %} {% block content %}
<h1>Регистрация в Cinemahub</h1>

<form method="post">
  {% csrf_token %}
  <input type="hidden" name="next" value="{{ next }}" />
  {{ form.as_p }}
  <p>
    <button type="submit">Зарегистрироваться</button>
  </p>
</form>

{% endblock %}
```

Что здесь важно:

- `{% csrf_token %}` — обязательная защита от CSRF-атак;
- `form.as_p` — быстрый способ вывести поля формы;
- скрытое поле `next` — задел на будущее (после регистрации можно делать редирект).

---

## Создание формы регистрации

Теперь опишем форму, которая будет:

- создавать пользователя;
- проверять пароли;
- контролировать email.

**Файл:** `users/forms.py`

```python
from django import forms
from django.contrib.auth import get_user_model

User = get_user_model()

class RegisterUserForm(forms.ModelForm):
    username = forms.CharField(label="Логин")
    password = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput
    )
    password2 = forms.CharField(
        label="Повтор пароля",
        widget=forms.PasswordInput
    )

    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'first_name',
            'last_name',
            'password',
            'password2'
        ]
        labels = {
            'email': 'E-mail',
            'first_name': 'Имя',
            'last_name': 'Фамилия',
        }
```

### Почему используется `get_user_model()`

Это принципиально важный момент:

- сегодня используется стандартный `User`;
- завтра — кастомная модель пользователя;
- код **не придётся переписывать**.

---

## Проверка данных формы

### Проверка совпадения паролей

Если этого не сделать, пользователь может зарегистрироваться с опечаткой в пароле.

Добавим кастомную валидацию.

**Файл:** `users/forms.py`

```python
    def clean_password2(self):
        cd = self.cleaned_data
        if cd['password'] != cd['password2']:
            raise forms.ValidationError("Пароли не совпадают")
        return cd['password2']
```

---

### Проверка уникальности email

По умолчанию Django **не запрещает** повторяющиеся email.

Добавим эту проверку вручную.

```python
    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Пользователь с таким E-mail уже существует")
        return email
```

---

## Функция представления регистрации

Теперь объединим форму и шаблон в полноценную логику.

**Файл:** `users/views.py`

```python
from django.shortcuts import render
from django.contrib.auth import login
from .forms import RegisterUserForm

def register(request):
    if request.method == 'POST':
        form = RegisterUserForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            return render(request, 'users/register_done.html')
    else:
        form = RegisterUserForm()

    return render(request, 'users/register.html', {'form': form})
```

### Что здесь происходит

1. При `GET`:

   - создаётся пустая форма;
   - отображается шаблон.

2. При `POST`:

   - данные валидируются;
   - пользователь создаётся **без сохранения**;
   - пароль хэшируется через `set_password()`;
   - пользователь сохраняется в базе.

---

## Почему нельзя сохранять пароль напрямую

❌ **Нельзя**:

```python
user.password = form.cleaned_data['password']
```

✔ **Нужно**:

```python
user.set_password(...)
```

Причина:

- Django хранит **хэши**, а не пароли;
- без `set_password()` пользователь не сможет войти.

---

## Шаблон успешной регистрации

**Файл:** `users/templates/users/register_done.html`

```html
{% extends 'base.html' %} {% block content %}
<h1>Регистрация завершена</h1>

<p>
  Вы успешно зарегистрировались на Cinemahub. Теперь вы можете
  <a href="{% url 'users:login' %}">войти в систему</a>.
</p>

{% endblock %}
```

---

## Маршруты приложения users

**Файл:** `users/urls.py`

```python
from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView

app_name = 'users'

urlpatterns = [
    path('login/', views.LoginUser.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('register/', views.register, name='register'),
]
```

---

## Добавление ссылки в базовый шаблон

**Файл:** `templates/base.html`

```html
<header>
  {% if request.user.is_authenticated %}
    <p>Привет, {{ request.user.username }}!</p>
    <a href="{% url 'users:logout' %}">Выйти</a>
  {% else %}
    <a href="{% url 'users:login' %}">Войти</a> |

    <a href="{% url 'users:register' %}">Регистрация</a>

  {% endif %}
  <h1><a href="{% url 'movies:index' %}">Кино-проекты</a></h1>
  <nav>
    <!-- Общие блоки тегов/жанров/режиссёров можно сюда включать -->
  </nav>
</header>
```

---

## Проверка результата в браузере

1. Запустите сервер
2. Перейдите по ссылке «Регистрация»
3. Попробуйте:

   - разные пароли;
   - одинаковые email;
   - корректную регистрацию

4. Проверьте:

   - пользователь появился в админке;
   - пароль не отображается в явном виде;
   - вход работает корректно.

---

## Типичные ошибки и их причины

**Ошибка:** пользователь создаётся, но не может войти
**Причина:** не использован `set_password()`

**Ошибка:** форма всегда невалидна
**Причина:** забыли `password2` в `fields`

**Ошибка:** email дублируется
**Причина:** нет `clean_email()`

---

## Практические задания

### Задание 1

Добавьте поле `email` обязательным для заполнения.

---

### Задание 2

Сделайте автоматический вход пользователя сразу после регистрации.

---

### Задание 3

Добавьте вывод имени пользователя в шаблон успешной регистрации.

---

## Сравнить решение

### Решение задания 1

```python
email = forms.EmailField(label="E-mail", required=True)
```

---

### Решение задания 2

```python
from django.contrib.auth import login

login(request, user)
```

---

### Решение задания 3

```html
<p>Добро пожаловать, {{ user.username }}!</p>
```

(передать `user` в контекст)

---

# Вопросы

1. Зачем использовать `get_user_model()`?
2. Почему нельзя сохранять пароль напрямую?
3. Где выполняется валидация формы?
4. Чем отличается `GET` от `POST` в представлении?
5. Зачем нужен `commit=False`?
6. Где лучше проверять совпадение паролей?
7. Что произойдёт без `csrf_token`?
8. Как проверить регистрацию без тестов?

---

[Предыдущий урок](lesson58.md) | [Следующий урок](lesson60.md)
