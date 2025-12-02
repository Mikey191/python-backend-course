# Модуль 7. Урок 46. Отображение загруженных изображений в HTML-документе и админ-панели

Когда мы научились загружать файлы в Django с помощью форм и моделей, следующий логичный шаг — научиться правильно _отображать_ эти файлы. На этом уроке мы сосредоточимся именно на работе с загруженными изображениями: покажем их в шаблонах, выведем миниатюры в админ-панели и разберём важные настройки проекта, без которых изображения просто не будут доступны пользователю.

---

## 1. Почему изображения не отображаются сами по себе?

Когда вы загружаете изображение в Django через `ImageField`, оно сохраняется в папку, указанную параметром `upload_to`. Например:

```python
poster = models.ImageField(upload_to="posters/%Y/%m/%d/")
```

Django отлично сохраняет файл… но _не раздаёт его пользователям автоматически_. Это принципиальная позиция: Django ― это веб-фреймворк, а не сервер файлов.

Значит, нам нужно:

1. Подготовить модель и данные.
2. Настроить отдачу **MEDIA-файлов**.
3. Научиться выводить изображения в HTML.
4. Научиться отображать миниатюры изображений в админ-панели.

Этим мы и займёмся.

---

## 2. Исходная модель проекта cinemahub

Для примеров возьмём модель фильма `Movie` (файл `cinemahub/models.py`):

```python
from django.db import models

class Movie(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    poster = models.ImageField(
        upload_to="posters/%Y/%m/%d/",
        blank=True,
        null=True,
        verbose_name="Постер"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
```

Поле `poster` — это наше изображение.

Если вы еще не сделали миграции:

```bash
python manage.py makemigrations
python manage.py migrate
```

---

## 3. Настройка MEDIA — обязательное условие отображения изображений

В файле **settings.py** добавьте:

```python
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
```

Здесь:

- `MEDIA_URL` — URL-префикс, по которому будет загружаться изображение
  (например: `/media/posters/2025/01/15/file.jpg`)
- `MEDIA_ROOT` — папка, где Django сохраняет изображения.

Теперь добавим раздачу медиа-файлов в `urls.py` (файл проекта, не приложения):

```python
# config/urls.py — главный urls.py проекта

from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include

urlpatterns = [
    path('', include('cinemahub.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

**Важно:** без этого шага никакие изображения не будут доступны браузеру.

---

## 4. Проверяем, что Django "видит" загруженные файлы

Запустите сервер:

```bash
python manage.py runserver
```

Загрузите в админке постер к любому фильму.

Теперь в shell можно посмотреть содержимое:

```bash
python manage.py shell
```

```python
from cinemahub.models import Movie
m = Movie.objects.first()

print(m.poster)       # путь внутри MEDIA_ROOT
print(m.poster.url)   # URL вида "/media/posters/2025/...jpg"
```

Если `.url` принимает значение — значит Django понимает путь к файлу.

---

## 5. Отображение изображений в HTML-шаблоне фильма

Допустим, у нас есть страница просмотра фильма:
`cinemahub/templates/cinemahub/movie_detail.html`.

Хотим вывести изображение, но только если оно есть:

```html
{% if movie.poster %}
<img src="{{ movie.poster.url }}" alt="Постер фильма" class="movie-poster" />
{% endif %}
```

Проверка `{% if movie.poster %}` обязательна — если изображения нет, Django выдаст ошибку.

### Проверяем результат:

1. Переходим в браузер на страницу фильма.
2. Открываем инструменты разработчика → вкладка **Network**.
3. Если изображение не грузится — ищем ошибку 404 по адресу `/media/...`.

Возможные ошибки и решения:

| Ошибка                      | Причина                       | Решение                                                  |
| --------------------------- | ----------------------------- | -------------------------------------------------------- |
| 404 Not Found               | Django не раздаёт MEDIA файлы | Проверьте настройки `MEDIA_URL` и `static()` в `urls.py` |
| net::ERR_FILE_NOT_FOUND     | Папка `media` не существует   | Создайте её в проекте                                    |
| Изображение не отображается | В шаблоне не добавлен `.url`  | Использовать `{{ movie.poster.url }}`                    |

---

## 6. Вывод изображений в списке фильмов

В шаблоне списка фильмов `cinemahub/movie_list.html`:

```html
{% for m in movies %}
<div class="movie-item">
  {% if m.poster %}
  <img src="{{ m.poster.url }}" alt="Постер" class="thumb" />
  {% endif %}
  <h3>{{ m.title }}</h3>
</div>
{% endfor %}
```

---

## 7. Миниатюры изображений в админ-панели

По умолчанию админ-панель не показывает изображения — только текстовые пути.

Мы добавим миниатюры.

Откройте файл **cinemahub/admin.py**:

```python
from django.contrib import admin
from django.utils.safestring import mark_safe
from .models import Movie
```

Добавим метод отображения:

```python
@admin.display(description="Постер")
def movie_poster(self, movie: Movie):
    if movie.poster:
        return mark_safe(f"<img src='{movie.poster.url}' width='60' />")
    return "—"
```

Теперь подключим в админ-класс:

```python
@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ("title", "movie_poster", "created_at")
    readonly_fields = ("movie_poster",)
    fields = ("title", "description", "poster", "movie_poster")
```

### Проверяем результат:

1. Заходим в админ-панель.
2. Открываем раздел фильмов.
3. Видим маленькие миниатюры в списке.
4. Заходим в карточку фильма — mini-preview там тоже отображается.

Если миниатюра не отображается:

- проверьте `MEDIA_URL`
- проверьте, что файл действительно лежит в `media/...`
- убедитесь, что `movie.poster.url` существует

---

## 8. Итоговая схема файлов проекта

```
cinemahub/
    models.py
    admin.py
    views.py
    forms.py
    templates/cinemahub/
        movie_list.html
        movie_detail.html
media/
    posters/...
config/
    settings.py
    urls.py
```

---

## Практика

1. Вывести изображение только если оно больше 0 байт. Создайте условие в шаблоне `movie_detail.html`: не выводить изображение, если файл пустой.

---

2. Добавить рамку к изображению в списке фильмов. Создайте CSS-класс `poster-frame` и примените его к изображениям, но только если они есть.

---

3. Добавить в админку отображение размера файла. Добавьте в `MovieAdmin` отдельное поле “Размер файла”. Пример вывода: `"150 KB"`.

---

## Сравнить решение

1. Вывести изображение только если оно больше 0 байт

```html
{% if movie.poster and movie.poster.size > 0 %}
<img src="{{ movie.poster.url }}" alt="Постер" />
{% endif %}
```

---

2. Добавить рамку к изображению в списке фильмов

HTML:

```html
{% if m.poster %}
<img src="{{ m.poster.url }}" class="poster-frame" />
{% endif %}
```

CSS:

```css
.poster-frame {
  border: 2px solid #ccc;
  padding: 4px;
}
```

---

3. Добавить в админку отображение размера файла.

`admin.py`:

```python
@admin.display(description="Размер файла")
def poster_size(self, movie: Movie):
    if movie.poster:
        size = movie.poster.size
        kb = round(size / 1024)
        return f"{kb} KB"
    return "—"


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ("title", "movie_poster", "poster_size", "created_at")
```

---

## Вопросы

1. Почему изображения не отображаются в Django без настройки MEDIA?
2. Что делает параметр `upload_to` в `ImageField`?
3. Почему важно использовать `<img src="{{ movie.poster.url }}">`, а не просто `{{ movie.poster }}`?
4. Зачем добавлять проверку `{% if movie.poster %}`?
5. Как работает `static()` в `urls.py`?
6. Что делает функция `mark_safe()` и почему она нужна в admin?
7. Как вывести миниатюру изображения в admin-панели?
8. Где хранятся загруженные изображения в Django?
9. Почему в продакшене нельзя раздавать MEDIA-файлы через Django?
10. Что происходит, если удалить файл через файловую систему, но оставить запись в БД?

---

[Предыдущий урок](lesson45.md) | [Следующий урок](lesson47.md)
