# Урок 13. Подключение и регистрация моделей. Базовая настройка списка

## Что такое админ-панель и почему это важно

Все три прошлых модуля мы работали без полноценного интерфейса для управления данными — фильмы создавались через shell, через `create()` в коде. Это нормально для разработки, но неудобно для повседневной работы с контентом.

Django поставляется с готовой административной панелью — это полноценный CRUD-интерфейс для любой модели, который не нужно писать руками. Достаточно зарегистрировать модель — и Django сам генерирует страницы списка, формы создания и редактирования, валидацию.

> Мы уже видели админку мельком в уроке 1 — маршрут `admin/` подключён в `urls.py` с самого начала проекта, потому что `django.contrib.admin` входит в `INSTALLED_APPS` по умолчанию. Сегодня превращаем эту пустую панель в рабочий инструмент.

---

## Создание суперпользователя

Чтобы зайти в админку, нужна учётная запись с правами администратора:

```bash
python manage.py createsuperuser
```

Django спросит логин, email и пароль:

```
Имя пользователя: admin
Адрес электронной почты: admin@example.com
Password: 
Password (again): 
Superuser created successfully.
```

Открываем `http://127.0.0.1:8000/admin/` и входим под этими данными. Пока в панели видны только встроенные модели — `Users` и `Groups` (из `django.contrib.auth`). Наших фильмов там нет — потому что мы их ещё не зарегистрировали.

---

## Регистрация моделей

Самый простой способ — зарегистрировать модель в `admin.py` приложения:

```python
# films/admin.py
from django.contrib import admin
from .models import Film, Genre, Director, Actor, FilmStats


admin.site.register(Film)
admin.site.register(Genre)
admin.site.register(Director)
admin.site.register(Actor)
admin.site.register(FilmStats)
```

Перезагружаем страницу `/admin/` — теперь видим раздел «Films» со всеми пятью моделями. Можно сразу зайти, создать, отредактировать и удалить запись — без единой строчки HTML или представления.

Это и есть главная ценность админки: она экономит огромное количество времени на рутинных CRUD-интерфейсах, которые иначе пришлось бы писать вручную через формы и CBV (этим мы займёмся в модулях 5–6, но уже для пользовательской части сайта, а не для администрирования).

---

## ModelAdmin — настройка через класс

Прямая регистрация (`admin.site.register(Film)`) даёт стандартный вид без какой-либо настройки. Чтобы управлять отображением — какие поля показывать в списке, как искать, как сортировать — используется класс `ModelAdmin`.

```python
# films/admin.py
from django.contrib import admin
from .models import Film, Genre, Director, Actor, FilmStats


@admin.register(Film)
class FilmAdmin(admin.ModelAdmin):
    list_display = ('title', 'year', 'rating', 'director')


admin.site.register(Genre)
admin.site.register(Director)
admin.site.register(Actor)
admin.site.register(FilmStats)
```

Декоратор `@admin.register(Film)` — это альтернативный синтаксис для `admin.site.register(Film, FilmAdmin)`. Оба варианта эквивалентны, но декоратор компактнее и используется чаще в современном коде.

### list_display — колонки в списке

По умолчанию список объектов в админке показывает только результат `__str__()`. `list_display` задаёт, какие поля выводить отдельными колонками:

```python
class FilmAdmin(admin.ModelAdmin):
    list_display = ('title', 'year', 'rating', 'director')
```

Теперь страница списка фильмов выглядит как таблица: название, год, рейтинг, режиссёр — каждое в своей колонке, с возможностью сортировки по клику на заголовок.

### list_display_links — какие поля кликабельны

По умолчанию ссылка на редактирование стоит на первом поле из `list_display`. Можно явно указать, какие поля должны быть ссылками:

```python
class FilmAdmin(admin.ModelAdmin):
    list_display = ('title', 'year', 'rating', 'director')
    list_display_links = ('title',)
```

### list_editable — редактирование прямо из списка

Поля, перечисленные в `list_editable`, становятся редактируемыми прямо в табличном виде — без перехода на страницу отдельной записи:

```python
class FilmAdmin(admin.ModelAdmin):
    list_display = ('title', 'year', 'rating', 'director')
    list_display_links = ('title',)
    list_editable = ('rating',)
```

> Важное ограничение: поле в `list_editable` не может одновременно быть в `list_display_links` — Django не разрешит сделать ссылку одновременно редактируемым полем.

### Настраиваем все модели

Применим то же самое к остальным моделям:

```python
@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')


@admin.register(Director)
class DirectorAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(Actor)
class ActorAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(FilmStats)
class FilmStatsAdmin(admin.ModelAdmin):
    list_display = ('film', 'views_count', 'likes_count')
```

---

## list_per_page — пагинация в админке

По умолчанию Django показывает 100 объектов на странице списка. Для большого каталога это можно изменить:

```python
class FilmAdmin(admin.ModelAdmin):
    list_display = ('title', 'year', 'rating', 'director')
    list_per_page = 20
```

---

## empty_value_display — отображение пустых значений

Если у фильма не указан режиссёр (помним, что в уроке 10 мы сделали `director` опциональным через `null=True`), в колонке по умолчанию будет пустая ячейка. Можно задать понятную заглушку:

```python
class FilmAdmin(admin.ModelAdmin):
    list_display = ('title', 'year', 'rating', 'director')
    empty_value_display = '— не указано —'
```

---

## Связь get_absolute_url() с админкой

В прошлом уроке мы добавили `get_absolute_url()` к моделям `Film` и `Director`. Сейчас этот метод раскрывает себя: на странице редактирования объекта в админке автоматически появляется кнопка «Просмотреть на сайте», которая ведёт прямо на страницу фильма на нашем сайте. Никакой дополнительной настройки для этого не нужно — Django проверяет наличие метода `get_absolute_url()` на модели и сам добавляет кнопку.

---

## Подводные камни

### list_display и методы без полей модели

`list_display` принимает не только имена полей, но и имена методов модели (без аргументов, кроме `self`) и методы самого `ModelAdmin`. Это пригодится уже в следующем уроке для вычисляемых колонок — сейчас просто держим это в уме.

```python
# Допустимо — count_views — метод модели Film
class FilmAdmin(admin.ModelAdmin):
    list_display = ('title', 'year', 'count_views')
```

### ManyToManyField нельзя добавить в list_display напрямую

Попытка добавить `genres` (ManyToManyField) в `list_display` вызовет ошибку:

```python
# Ошибка: FieldDoesNotExist / NotRelationField для M2M в list_display
list_display = ('title', 'genres')
```

Причина — `list_display` ожидает одно скалярное значение на ячейку, а M2M-связь это коллекция. Решение — написать метод, который возвращает строку со списком жанров через запятую. Подробно разберём это в следующем уроке.

### Изменения в admin.py требуют перезапуска сервера не всегда

Django в режиме разработки (`runserver`) автоматически подхватывает изменения в `admin.py`, как и в любом другом `.py`-файле — благодаря `StatReloader`. Если изменения не применились — проверь, не упал ли сервер с ошибкой импорта (например, опечатка в имени поля).

### Повторная регистрация модели

Каждая модель может быть зарегистрирована в административной панели **только один раз**. Во время регистрации Django сохраняет информацию о том, какой класс `ModelAdmin` должен использоваться для этой модели.

Повторная регистрация модели почти никогда не используют для собственных моделей. Она бывает нужна в ситуациях, когда модель **уже зарегистрирована где-то еще**, а разработчик хочет заменить ее настройки.

Классический пример — встроенная модель пользователя Django. Она уже зарегистрирована самим Django, поэтому повторная регистрация приведет к ошибке.

Правильный способ повторной регистрации - использовать `admin.site.unregister`:

```python
from django.contrib import admin
from django.contrib.auth.models import User


admin.site.unregister(User)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email']
```

---

## Итоговый admin.py

```python
# films/admin.py
from django.contrib import admin
from .models import Film, Genre, Director, Actor, FilmStats


@admin.register(Film)
class FilmAdmin(admin.ModelAdmin):
    list_display = ('title', 'year', 'rating', 'director')
    list_display_links = ('title',)
    list_editable = ('rating',)
    list_per_page = 20
    empty_value_display = '— не указано —'


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')


@admin.register(Director)
class DirectorAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(Actor)
class ActorAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(FilmStats)
class FilmStatsAdmin(admin.ModelAdmin):
    list_display = ('film', 'views_count', 'likes_count')
```

---

## Вопросы для проверки

1. Чем `admin.site.register(Film)` отличается от регистрации через `@admin.register(Film)` с классом `FilmAdmin`?
2. Что делает `list_display_links` и почему его нельзя использовать одновременно с `list_editable` на одном поле?
3. Почему ManyToManyField нельзя напрямую добавить в `list_display`?
4. Что нужно сделать, чтобы на странице редактирования объекта в админке появилась кнопка «Просмотреть на сайте»?
5. Что произойдёт, если зарегистрировать модель дважды — например, через `admin.site.register()` и через `@admin.register()` одновременно?

---

## Практическая задача

**Тип: расширь проект**

Настрой отображение модели `Genre` и `Director` в админке так, чтобы работать с ними было удобнее.

**Требования:**

1. Для `GenreAdmin`: добавь `list_editable` для поля `slug`, чтобы его можно было быстро менять прямо из списка (помни про ограничение с `list_display_links`)
2. Для `DirectorAdmin`: добавь в `list_display` поле `slug`, а также задай `empty_value_display = '— нет данных —'`
3. Для обеих моделей задай `list_per_page = 15`

---

[Предыдущий урок](lesson12.md) | [Следующий урок](lesson14.md)