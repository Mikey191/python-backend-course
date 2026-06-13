# Модуль 9. Урок 66. Разрешения и группы (Permissions & Groups)

В предыдущих уроках мы научились регистрировать пользователей, авторизовывать их, работать с профилем и ограничивать доступ по признаку «авторизован / не авторизован».
Однако в реальных проектах этого недостаточно.

В проекте **cinemahub** у нас могут быть разные типы пользователей:

* обычные пользователи, которые только смотрят каталог фильмов;
* модераторы, которые могут добавлять и редактировать фильмы;
* администраторы, которые управляют всеми сущностями проекта.

Для решения этой задачи в Django существует мощный и гибкий механизм **разрешений (permissions)** и **групп (groups)**.

Цель этого урока — научиться:

* понимать, как Django работает с разрешениями;
* ограничивать доступ к представлениям;
* проверять разрешения в шаблонах;
* использовать группы для управления доступом;
* работать с разрешениями программно;
* диагностировать типичные ошибки.

---

## 1. Где в Django находятся разрешения

Откроем админ-панель проекта:

```
http://127.0.0.1:8000/admin/
```

Перейдём в раздел **Users → Users** и откроем любого пользователя на редактирование.

Мы увидим два важных поля:

* **Groups** — группы, к которым принадлежит пользователь
* **User permissions** — индивидуальные разрешения пользователя

Важно понимать:
Django **всегда** проверяет разрешения пользователя, объединяя:

* личные разрешения пользователя;
* разрешения всех групп, в которые он входит.

---

## 2. Стандартные разрешения Django

Для **каждой модели** Django автоматически создаёт четыре базовых разрешения:

| Разрешение | Назначение         |
| ---------- | ------------------ |
| `add`      | Добавление записей |
| `change`   | Изменение записей  |
| `delete`   | Удаление записей   |
| `view`     | Просмотр записей   |

### Пример для модели Movie

Модель `Movie` находится в приложении `movies`, поэтому Django создаёт следующие разрешения:

* `movies.add_movie`
* `movies.change_movie`
* `movies.delete_movie`
* `movies.view_movie`

Общий формат имени разрешения:

```
<app_label>.<action>_<modelname>
```

---

## 3. Ограничение доступа к CBV (Class-Based Views)

Предположим, в проекте есть представление для добавления фильма.

**Файл:** `movies/views.py`

```python
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.views.generic import CreateView
from .models import Movie

class MovieCreateView(PermissionRequiredMixin, CreateView):
    model = Movie
    fields = ['title', 'description', 'year', 'category', 'is_published']
    template_name = 'movies/movie_form.html'
    success_url = '/'

    permission_required = 'movies.add_movie'
```

### Что происходит

* Django проверяет наличие разрешения `movies.add_movie`
* Если разрешение есть — страница открывается
* Если нет:

  * авторизованный пользователь получает **403 Forbidden**
  * неавторизованный пользователь будет перенаправлен на страницу входа

---

## 4. Проверка результата в браузере

1. Зайдите под пользователем **без разрешения**
2. Перейдите на страницу добавления фильма
3. Вы увидите ошибку **403**

Теперь:

1. Зайдите в админку
2. Назначьте пользователю разрешение `add movie`
3. Обновите страницу

Страница станет доступной.

---

## 5. Ограничение доступа для FBV (Function-Based Views)

Если используется представление-функция, применяется декоратор `@permission_required`.

**Файл:** `movies/views.py`

```python
from django.contrib.auth.decorators import permission_required
from django.http import HttpResponse

@permission_required('movies.view_movie', raise_exception=True)
def movie_contacts(request):
    return HttpResponse("Контакты кинопортала Cinemahub")
```

### Параметр `raise_exception=True`

* если `True` → ошибка **403**
* если `False` (по умолчанию) → редирект на страницу логина

---

## 6. Проверка разрешений в шаблонах

Django автоматически передаёт объект `perms` во все шаблоны.

### Пример: кнопка редактирования фильма

```html
{% if perms.movies.change_movie %}
    <a href="{% url 'movies:movie_edit' movie.pk %}">
        Редактировать фильм
    </a>
{% endif %}
```

Если у пользователя нет разрешения — ссылка просто **не будет отображаться**.

Это особенно важно:

* для UX
* для безопасности
* для предотвращения ошибок доступа

---

## 7. Группы пользователей (Groups)

Когда пользователей становится много, назначать разрешения вручную неудобно.
В этом случае используются **группы**.

### Пример групп в Cinemahub

| Группа      | Назначение              |
| ----------- | ----------------------- |
| `moderator` | Управление фильмами     |
| `editor`    | Редактирование описаний |
| `admin`     | Полный доступ           |

### Создание группы

1. Админка → **Groups**
2. Создать группу `moderator`
3. Назначить ей:

   * `add_movie`
   * `change_movie`
   * `view_movie`

Теперь достаточно добавить пользователя в группу — и он автоматически получит все права.

---

## 8. Работа с группами и разрешениями через Django Shell

Откроем shell:

```bash
python manage.py shell
```

### Добавление пользователя в группу

```python
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model

User = get_user_model()
user = User.objects.get(username='user1')

group = Group.objects.get(name='moderator')
user.groups.add(group)
```

### Проверка разрешений

```python
user.has_perm('movies.add_movie')     # True
user.has_perm('movies.delete_movie')  # False
```

---

## 9. Управление разрешениями напрямую

```python
user.user_permissions.add(permission)
user.user_permissions.remove(permission)
user.user_permissions.clear()
```

Добавление по объекту:

```python
from django.contrib.auth.models import Permission

perm = Permission.objects.get(codename='change_movie')
user.user_permissions.add(perm)
```

---

## 10. Создание пользовательских разрешений

Иногда стандартных разрешений недостаточно.

### Пример: разрешение на публикацию фильмов

**Файл:** `movies/models.py`

```python
class Movie(models.Model):
    ...
    class Meta:
        permissions = [
            ("can_publish_movie", "Can publish movie"),
        ]
```

После `makemigrations` и `migrate` разрешение появится в админке.

Проверка:

```python
user.has_perm('movies.can_publish_movie')
```

---

## 11. Где в проекте всё это хранится

* `users/models.py` — связи пользователя с группами и правами
* `movies/models.py` — кастомные разрешения
* `movies/views.py` — `PermissionRequiredMixin`
* `movies/templates/` — `perms`
* `admin.py` — назначение прав
* `manage.py shell` — отладка

---

## 12. Типичные ошибки и их причины

### Ошибка 403 при наличии прав

* пользователь не перелогинился
* кэш сессии не обновился

### Разрешение не появляется

* не выполнены `makemigrations` / `migrate`
* ошибка в `Meta.permissions`

### Ошибка `PermissionDenied`

* отсутствует `raise_exception=True`
* неверное имя разрешения

---

## Практические задания

### Задание 1

Ограничьте доступ к редактированию фильма так, чтобы только пользователи с разрешением `change_movie` могли открывать страницу. Использовать `PermissionRequiredMixin` с `movies.change_movie`.

---

### Задание 2

Создайте группу `editor`, которая может только редактировать и просматривать фильмы.Назначить `change_movie` и `view_movie`, добавить пользователя в группу.

---

### Задание 3

Скройте кнопку удаления фильма, если у пользователя нет соответствующего разрешения. Использовать `perms.movies.delete_movie` в шаблоне.

---

# Вопросы для самопроверки

1. Какие стандартные разрешения создаёт Django?
2. Чем отличаются группы от индивидуальных разрешений?
3. Как проверить разрешение пользователя в коде?
4. Как ограничить доступ к CBV?
5. Что делает `raise_exception=True`?
6. Где хранятся кастомные разрешения?
7. Почему пользователь может не получить доступ сразу?
8. Как проверить разрешения в шаблоне?

---

[Предыдущий урок](lesson65.md) | [Следующий урок](lesson67.md)