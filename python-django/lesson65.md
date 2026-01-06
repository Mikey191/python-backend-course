# Модуль 9. Урок 65. Расширение модели пользователя в Django (AbstractUser)

## Зачем расширять модель пользователя в Cinemahub

На предыдущих уроках мы реализовали регистрацию, авторизацию и восстановление пароля. На этом этапе в проекте **Cinemahub** уже существует полноценная система пользователей, но она пока использует стандартную модель `User`, предоставляемую Django.

Однако в реальных проектах почти всегда возникает необходимость хранить **дополнительную информацию о пользователе**:

* фотографию профиля;
* дату рождения;
* город;
* настройки профиля;
* служебные поля (например, роль пользователя в системе).

Даже в рамках Cinemahub это может быть полезно: в будущем пользователь может иметь собственный профиль, список избранных фильмов, историю просмотров, персональные рекомендации и т.д.

В этом уроке мы разберём, **какими способами Django позволяет расширять модель пользователя**, и подробно реализуем **наиболее универсальный и профессиональный подход — через `AbstractUser`**.

---

## Два подхода к расширению пользователя в Django

В Django существует **два официальных способа** расширить информацию о пользователе.

### Подход 1. Отдельная модель профиля (One-to-One)

Создаётся дополнительная модель, например `UserProfile`, связанная с `User` через `OneToOneField`.

**Идея:**
Основная модель `User` остаётся стандартной, а все дополнительные данные хранятся в отдельной таблице.

### Подход 2. Кастомная модель пользователя (`AbstractUser`)

Создаётся **собственная модель пользователя**, которая **полностью заменяет стандартную** и наследуется от `AbstractUser`.

---

## Сравнение подходов

| Подход             | Когда использовать                          | Плюсы                               | Минусы                        |
| ------------------ | ------------------------------------------- | ----------------------------------- | ----------------------------- |
| One-to-One профиль | Проект уже в production, нельзя менять User | Не затрагивает стандартную модель   | Дополнительные JOIN-запросы   |
| AbstractUser       | Новый проект или ранний этап                | Все данные в одной модели, гибкость | Нужно принять решение заранее |

### Почему в Cinemahub мы выбираем `AbstractUser`

Проект Cinemahub находится **на этапе активной разработки**, и мы уже контролируем систему авторизации. Это идеальный момент, чтобы:

* сразу определить структуру пользователя;
* избежать лишних связей;
* упростить дальнейшую работу с профилем.

Поэтому в рамках курса мы будем использовать **кастомную модель пользователя на базе `AbstractUser`**.

---

## Шаг 1. Создание кастомной модели пользователя

Создадим собственную модель пользователя в приложении `users`.

### Файл: `users/models.py`

```python
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    photo = models.ImageField(
        upload_to="users/%Y/%m/%d/",
        blank=True,
        null=True,
        verbose_name="Фото профиля"
    )
    date_birth = models.DateField(
        blank=True,
        null=True,
        verbose_name="Дата рождения"
    )
```

### Что мы сделали

* унаследовались от `AbstractUser`, сохранив:

  * `username`
  * `email`
  * `password`
  * `is_staff`, `is_active` и т.д.
* добавили собственные поля:

  * `photo` — для фотографии пользователя;
  * `date_birth` — дата рождения.

Таким образом, **вся информация о пользователе теперь хранится в одной модели**.

---

## Шаг 2. Подключение кастомной модели в Django

Теперь необходимо явно указать Django, что проект Cinemahub использует **нашу модель пользователя**, а не стандартную.

### Файл: `settings.py`

```python
AUTH_USER_MODEL = "users.User"
```

⚠️ **Важно:**
Эта настройка должна быть добавлена **до создания первых миграций**, иначе Django уже зафиксирует стандартную модель `User`.

---

## Шаг 3. Создание и применение миграций

После изменения модели создаём миграции.

```bash
python manage.py makemigrations
python manage.py migrate
```

### Возможная проблема

Если до этого проект уже использовал стандартного `User`, Django может выдать ошибки миграций.

В учебном проекте допустим «жёсткий сброс»:

```bash
rm -rf users/migrations/
rm db.sqlite3
python manage.py makemigrations
python manage.py migrate
```

В **production-проектах так делать нельзя**, но для обучения это допустимо и полезно для понимания механики.

---

## Шаг 4. Регистрация пользователя в админ-панели

Чтобы управлять пользователями через админку, зарегистрируем модель.

### Файл: `users/admin.py`

```python
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


admin.site.register(User, UserAdmin)
```

После этого:

1. запускаем сервер;
2. переходим в `/admin/`;
3. видим пользователей с нашими дополнительными полями.

---

## Шаг 5. Использование `get_user_model()` в проекте

После замены модели пользователя **никогда нельзя импортировать `User` напрямую**.

❌ Неправильно:

```python
from django.contrib.auth.models import User
```

✅ Правильно:

```python
from django.contrib.auth import get_user_model

User = get_user_model()
```

Это гарантирует, что Django всегда будет использовать актуальную модель пользователя, даже если она изменится.

---

## Шаг 6. Создание суперпользователя

Создадим администратора уже для новой модели:

```bash
python manage.py createsuperuser
```

Зайди в админку и убедись, что:

* пользователь создаётся корректно;
* дополнительные поля отображаются.

---

## Шаг 7. Работа с пользователем в формах

Добавим форму редактирования профиля пользователя.

### Файл: `users/forms.py`

```python
from django import forms
from django.contrib.auth import get_user_model
import datetime


class ProfileUserForm(forms.ModelForm):
    this_year = datetime.date.today().year

    date_birth = forms.DateField(
        widget=forms.SelectDateWidget(
            years=range(this_year - 100, this_year - 10)
        ),
        label="Дата рождения"
    )

    class Meta:
        model = get_user_model()
        fields = [
            "photo",
            "username",
            "email",
            "first_name",
            "last_name",
            "date_birth",
        ]
```

---

## Шаг 8. Отображение фотографии пользователя

Создадим простой шаблон профиля.

### Файл: `users/templates/users/profile.html`

```html
<form method="post" enctype="multipart/form-data">
  {% csrf_token %}

  {% if user.photo %}
    <p><img src="{{ user.photo.url }}" width="150"></p>
  {% else %}
    <p><img src="{{ default_image }}" width="150"></p>
  {% endif %}

  {{ form.as_p }}

  <button type="submit">Сохранить</button>
</form>
```

---

## Шаг 9. Настройка MEDIA и изображения по умолчанию

### Файл: `settings.py`

```python
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_USER_IMAGE = MEDIA_URL + "users/default.png"
```

### Файл: `users/views.py`

```python
from django.conf import settings

extra_context = {
    "title": "Профиль пользователя",
    "default_image": settings.DEFAULT_USER_IMAGE,
}
```

---

## Шаг 10. Добавление поля `photo` в админку

Модель пользователя уже содержит поле `photo`, но стандартный `UserAdmin` **не показывает его автоматически**.

### Кастомизация `UserAdmin`

Создадим собственный класс админки.

**Файл `users/admin.py`:**

```python
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("Дополнительная информация", {
            "fields": ("photo", "date_birth"),
        }),
    )
```

Что здесь происходит:

* мы **наследуемся от стандартного `UserAdmin`**;
* добавляем новый блок полей;
* поле `photo` появляется:

  * при создании пользователя;
  * при редактировании пользователя.

Теперь можно:

1. зайти в админку;
2. открыть пользователя;
3. загрузить фотографию;
4. сохранить изменения.

---

## Шаг 11. Добавление фотографии в форму регистрации

По умолчанию пользователь регистрируется **без фото**, но в Cinemahub логично разрешить загрузку аватара уже на этапе регистрации.

### Обновление формы регистрации

Предположим, у тебя уже есть форма `RegisterUserForm`, унаследованная от `UserCreationForm`.

**Файл `users/forms.py`:**

```python
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django import forms


class RegisterUserForm(UserCreationForm):
    photo = forms.ImageField(
        required=False,
        label="Фото профиля"
    )

    class Meta:
        model = get_user_model()
        fields = (
            "username",
            "email",
            "photo",
            "password1",
            "password2",
        )
```

Обрати внимание:

* `photo` добавлено **явно**;
* поле необязательное — пользователь может пропустить его.

---

Чтобы браузер корректно отправлял файл, форма **обязательно** должна использовать `multipart/form-data`.

### Файл: `users/templates/users/register.html`

```html
<form method="post" enctype="multipart/form-data">
  {% csrf_token %}
  
  {{ form.as_p }}

  <button type="submit">Зарегистрироваться</button>
</form>
```

---

## Шаг 12. Добавление фотографии в профиль пользователя

Форма профиля у тебя уже есть:

```python
class ProfileUser(LoginRequiredMixin, UpdateView):
    model = get_user_model()
    form_class = ProfileUserForm
```

Осталось убедиться, что:

### Форма поддерживает загрузку файлов

**Файл `users/forms.py`:**

```python
class ProfileUserForm(forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = (
            "photo",
            "username",
            "email",
            "first_name",
            "last_name",
            "date_birth",
        )
```

### Шаблон профиля

**Файл `users/templates/users/profile.html`:**

```html
<form method="post" enctype="multipart/form-data">
  {% csrf_token %}

  {% if user.photo %}
    <p><img src="{{ user.photo.url }}" width="150"></p>
  {% endif %}

  {{ form.as_p }}

  <button type="submit">Сохранить</button>
</form>
```

---

## Проверка результата

1. Перейди в админку.
2. Открой пользователя.
3. Загрузи фото и укажи дату рождения.
4. Сохрани изменения.
5. Перейди на страницу профиля.
6. Убедись, что:

   * фото отображается;
   * данные корректно сохраняются.

---

## Практические задания

Добавить все изменения в свой проект.

## Вопросы для самопроверки

1. В чём разница между `User` и `AbstractUser`?
2. Почему важно заранее выбирать способ расширения пользователя?
3. Когда лучше использовать One-to-One профиль?
4. Зачем нужен `get_user_model()`?
5. Что произойдёт, если изменить `AUTH_USER_MODEL` после миграций?
6. Где настраивается хранение загруженных файлов?
7. Почему `ImageField` требует `enctype="multipart/form-data"`?

---

[Предыдущий урок](lesson64.md) | [Следующий урок](lesson66.md)