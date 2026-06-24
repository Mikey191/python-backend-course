# Модуль 9. Урок 62. Изменение пароля пользователя в Django

## PasswordChangeView и PasswordChangeDoneView

На предыдущих шагах мы реализовали регистрацию, авторизацию и профиль пользователя в проекте **Cinemahub**.
Логичным продолжением является возможность **самостоятельно менять пароль**, не привлекая администратора.

В этом уроке мы:

* разберём встроенный механизм Django для смены пароля;
* научимся кастомизировать форму и шаблоны;
* аккуратно встроим функциональность в существующий профиль пользователя;
* проверим работу в браузере и обсудим типичные ошибки.

---

## Зачем Django выделяет смену пароля в отдельный механизм

Смена пароля — **критически важная операция**, поэтому Django:

* требует, чтобы пользователь был **авторизован**;
* обязательно проверяет **старый пароль**;
* автоматически хэширует новый пароль;
* обновляет сессию пользователя, чтобы не разлогинивать его.

Поэтому Django предоставляет **готовые классы представлений**, которые безопаснее и надёжнее писать заново.

---

## Встроенные классы Django для смены пароля

В Django есть два ключевых класса:

* **`PasswordChangeView`**
  Отвечает за:

  * отображение формы;
  * проверку старого пароля;
  * валидацию нового пароля;
  * сохранение изменений.

* **`PasswordChangeDoneView`**
  Отображает страницу успешного изменения пароля.

Наша задача — **подключить их и адаптировать под проект Cinemahub**.

---

## Шаг 1. Подготовка маршрутов

Начнём с маршрутов, чтобы понимать структуру переходов.

### Файл: `users/urls.py`

```python
from django.urls import path
from django.contrib.auth.views import PasswordChangeDoneView
from .views import UserPasswordChange

app_name = "users"

urlpatterns = [
    path("password-change/", UserPasswordChange.as_view(), name="password_change"),
    path(
        "password-change/done/",
        PasswordChangeDoneView.as_view(
            template_name="users/password_change_done.html"
        ),
        name="password_change_done",
    ),
]
```

**Что важно понять:**

* Django ожидает, что после смены пароля будет маршрут `password_change_done`.
* Мы сразу указываем кастомный шаблон, чтобы интерфейс не выбивался из Cinemahub.

---

## Шаг 2. Кастомная форма смены пароля

По умолчанию Django использует `PasswordChangeForm`.
Она полностью рабочая, но **визуально не совпадает** с нашими формами регистрации и профиля.

Поэтому мы создадим обёртку над ней.

### Файл: `users/forms.py`

```python
from django import forms
from django.contrib.auth.forms import PasswordChangeForm

class UserPasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(
        label="Текущий пароль",
        widget=forms.PasswordInput(attrs={"class": "form-input"}),
    )
    new_password1 = forms.CharField(
        label="Новый пароль",
        widget=forms.PasswordInput(attrs={"class": "form-input"}),
    )
    new_password2 = forms.CharField(
        label="Подтверждение нового пароля",
        widget=forms.PasswordInput(attrs={"class": "form-input"}),
    )
```

**Ключевой момент:**
Мы **не переопределяем логику**, а только внешний вид.
Вся проверка надёжности пароля остаётся внутри Django.

---

## Шаг 3. Представление смены пароля

Теперь создадим собственное представление, которое:

* использует нашу форму;
* отображает наш шаблон;
* корректно перенаправляет пользователя после успеха.

### Файл: `users/views.py`

```python
from django.contrib.auth.views import PasswordChangeView
from django.urls import reverse_lazy
from .forms import UserPasswordChangeForm

class UserPasswordChange(PasswordChangeView):
    form_class = UserPasswordChangeForm
    template_name = "users/password_change_form.html"
    success_url = reverse_lazy("users:password_change_done")
    extra_context = {"title": "Изменение пароля"}
```

**Почему `reverse_lazy`, а не `reverse`:**

* URL разрешается только в момент выполнения запроса;
* это безопаснее для классовых представлений.

---

## Шаг 4. Шаблон формы смены пароля

Создадим шаблон формы.
Он **не привязан к Movie напрямую**, но логически встроен в пользовательский раздел Cinemahub.

### Файл: `users/templates/users/password_change_form.html`

```html
{% extends "base.html" %}

{% block content %}
<h1>{{ title }}</h1>

<form method="post">
  {% csrf_token %}

  <div class="form-error">{{ form.non_field_errors }}</div>

  {% for field in form %}
    <p>
      <label for="{{ field.id_for_label }}">{{ field.label }}:</label>
      {{ field }}
    </p>
    <div class="form-error">{{ field.errors }}</div>
  {% endfor %}

  <button type="submit">Сменить пароль</button>
</form>
{% endblock %}
```

---

## Шаг 5. Шаблон успешной смены пароля

После успешного изменения пароля пользователь должен **понять, что всё прошло корректно**.

### Файл: `users/templates/users/password_change_done.html`

```html
{% extends "base.html" %}

{% block content %}
<h1>Пароль изменён</h1>

<p>
  Пароль вашего аккаунта в Cinemahub успешно обновлён.
</p>

<p>
  <a href="{% url 'users:profile' %}">Вернуться в профиль</a>
</p>
{% endblock %}
```

---

## Шаг 6. Добавление ссылки в профиль пользователя

Теперь свяжем смену пароля с профилем.

### Файл: `users/templates/users/profile.html`

```html
<hr />
<p>
  <a href="{% url 'users:password_change' %}">
    Сменить пароль
  </a>
</p>
```

---

## Проверка результата в браузере

1. Авторизуйся под любым пользователем.
2. Перейди в **Профиль**.
3. Нажми **«Сменить пароль»**.
4. Проверь:

   * ввод старого пароля;
   * ввод нового пароля;
   * сообщения об ошибках;
   * переход на страницу успеха.
5. Разлогинься и войди с новым паролем.

Если всё работает — механизм реализован корректно.

---

## Типичные ошибки и причины

### 1. `NoReverseMatch: password_change_done`

Причина:

* маршрут не объявлен;
* неверное имя namespace.

### 2. Форма открывается, но пароль не меняется

Причина:

* пользователь не авторизован;
* используется `PasswordResetForm` вместо `PasswordChangeForm`.

### 3. После смены пароля пользователь разлогинивается

Причина:

* используется самописная логика вместо `PasswordChangeView`.

---

## Практические задания

Реализовать смену пароля в вашем проекте.

---

## Вопросы

1. Почему для смены пароля используется отдельное представление?
2. Чем `PasswordChangeForm` отличается от `PasswordResetForm`?
3. Зачем нужен `PasswordChangeDoneView`?
4. Почему нельзя просто изменить поле `password` у пользователя?
5. Где происходит проверка старого пароля?
6. Почему Django не разлогинивает пользователя после смены пароля?
7. Как изменить внешний вид формы, не ломая логику?
8. Где задаётся шаблон успешной смены пароля?

---

[Предыдущий урок](lesson61.md) | [Следующий урок](lesson63.md)