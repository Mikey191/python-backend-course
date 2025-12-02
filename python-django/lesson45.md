# Модуль 7. Урок 45. Загрузка файлов с использованием моделей в Django

Загрузка файлов через простую форму полезна для демонстрации, но в реальных приложениях файлы обычно являются свойством объекта: постер фильма, трейлер, сцены и т. д. В этом уроке мы научимся связывать файлы с моделями и использовать возможности Django для безопасного и удобного хранения, валидации и отображения файлов.

Мы разберём:

- модель с `FileField`/`ImageField`
- миграции
- `ModelForm` для загрузки файлов
- `request.FILES` и `form.save()` для сохранения
- `upload_to`, callable и шаблонизаторы (`%Y/%m/%d`)
- как избежать перезаписи и обеспечить понятные пути
- отображение загруженных файлов в шаблонах и админке
- типичные ошибки и как их исправлять
- практические задания с решениями

---

## 0. Подготовка (если ещё не сделано)

1. Установите Pillow (нужен для `ImageField`):

```bash
pip install Pillow
```

2. В `settings.py` убедитесь, что есть:

```python
import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MEDIA_ROOT = os.path.join(BASE_DIR, "media")
MEDIA_URL = "/media/"
```

3. В корневом `urls.py` (только при `DEBUG = True`) подключите отдачу медиа:

```python
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # ... ваши маршруты ...
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

---

## 1. Модель для хранения файлов: пример с постером фильма

Добавим в модель `Movie` поле `poster`, которое будет хранить изображение-постер.

### Файл: `cinemahub/models.py`

```python
from django.db import models

class Genre(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Movie(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    year = models.PositiveIntegerField()
    is_published = models.BooleanField(default=True)
    genre = models.ForeignKey(Genre, on_delete=models.PROTECT)
    poster = models.ImageField(
        upload_to='posters/%Y/%m/%d/',  # файлы будут лежать в media/posters/YYYY/MM/DD/
        blank=True,
        null=True,
        verbose_name='Постер фильма'
    )

    def __str__(self):
        return self.title
```

**Пояснение:**

- `ImageField` проверит, что файл — изображение (используется Pillow).
- `upload_to='posters/%Y/%m/%d/'` — удобный способ организовать хранилище по дате.
- `blank=True, null=True` — постер необязателен.

После изменения модели — создайте миграции:

```bash
python manage.py makemigrations
python manage.py migrate
```

---

## 2. ModelForm для создания фильма с загрузкой постера

Лучше использовать `ModelForm` — он автоматически подготовит поле для `poster`.

### Файл: `cinemahub/forms.py`

```python
from django import forms
from .models import Movie, Genre

class MovieWithPosterForm(forms.ModelForm):
    class Meta:
        model = Movie
        fields = ['title', 'slug', 'description', 'year', 'is_published', 'genre', 'poster']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input'}),
            'description': forms.Textarea(attrs={'rows': 4}),
            'year': forms.NumberInput(attrs={'min': 1900, 'max': 2100}),
        }
```

**Замечание:** поле `poster` будет автоматически использовать `ClearableFileInput` — позволяющее загрузить файл и при редактировании очистить старый.

---

## 3. Представление для загрузки файла вместе с моделью

### Файл: `cinemahub/views.py`

```python
from django.shortcuts import render, redirect, get_object_or_404
from .forms import MovieWithPosterForm
from .models import Movie

def add_movie_with_poster(request):
    if request.method == 'POST':
        form = MovieWithPosterForm(request.POST, request.FILES)
        if form.is_valid():
            movie = form.save()  # Django сохранит модель и загрузит файл в MEDIA_ROOT/posters/...
            return redirect('movie_detail', pk=movie.pk)  # пример редиректа на детальную страницу
    else:
        form = MovieWithPosterForm()
    return render(request, 'cinemahub/add_movie_with_poster.html', {'form': form})
```

**Ключевой момент:** при создании формы, принимающей файлы, всегда передаём два аргумента: `request.POST` и `request.FILES`.

---

## 4. Шаблон загрузки (обязателен `enctype`)

### Файл: `templates/cinemahub/add_movie_with_poster.html`

```html
<!DOCTYPE html>
<html lang="ru">
  <head>
    <meta charset="utf-8" />
    <title>Добавить фильм с постером</title>
  </head>
  <body>
    <h1>Добавить фильм</h1>

    <form method="post" enctype="multipart/form-data">
      {% csrf_token %} {{ form.as_p }}
      <button type="submit">Сохранить</button>
    </form>
  </body>
</html>
```

---

## 5. Просмотр загруженного файла (детальная страница)

После сохранения объекта можно показывать постер:

### Файл: `cinemahub/views.py` (деталка)

```python
def movie_detail(request, pk):
    movie = get_object_or_404(Movie, pk=pk)
    return render(request, 'cinemahub/movie_detail.html', {'movie': movie})
```

### Шаблон: `templates/cinemahub/movie_detail.html`

```html
<h1>{{ movie.title }}</h1>

{% if movie.poster %}
<img
  src="{{ movie.poster.url }}"
  alt="{{ movie.title }}"
  style="max-width:300px;"
/>
{% else %}
<p>Постер отсутствует</p>
{% endif %}

<p>{{ movie.description }}</p>
```

**Проверка:** в режиме разработки убедитесь, что `MEDIA_URL` подключён в `urls.py` (см. начало урока), тогда картинка откроется по `http://127.0.0.1:8000/media/posters/...`.

---

## 6. Более гибкий `upload_to` — callable для уникальных путей

Иногда нужно подложить файл в папку с id объекта или с безопасным именем. Callable позволяет это сделать:

### В `models.py`

```python
import os
import uuid

def poster_upload_to(instance, filename):
    # файл пока ещё не сохранён, instance.id может быть None
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4().hex}.{ext}"
    return os.path.join('posters', str(instance.slug), filename)
```

```python
poster = models.ImageField(upload_to=poster_upload_to, blank=True, null=True)
```

**Плюсы:** уникальные имена, гибкая структура директорий.

---

## 7. Обновление постера (редактирование существующего фильма)

При редактировании `ModelForm` автоматически покажет поле `ClearableFileInput`, где студент может загрузить новый постер или отметить чекбокс «Удалить».

Представление для редактирования:

```python
def edit_movie(request, pk):
    movie = get_object_or_404(Movie, pk=pk)
    if request.method == 'POST':
        form = MovieWithPosterForm(request.POST, request.FILES, instance=movie)
        if form.is_valid():
            form.save()
            return redirect('movie_detail', pk=movie.pk)
    else:
        form = MovieWithPosterForm(instance=movie)
    return render(request, 'cinemahub/edit_movie.html', {'form': form, 'movie': movie})
```

---

## 8. Типичные ошибки и как их исправлять

### Ошибка 1 — забыли `enctype="multipart/form-data"`

Симптом: `request.FILES` пуст, `form.is_valid()` для `ImageField` — False или `poster` не сохраняется.
**Решение:** добавить `enctype="multipart/form-data"` в форму.

### Ошибка 2 — `ValueError: The 'poster' attribute has no file associated with it.`

Симптом: при попытке обратиться к `movie.poster.url` для объекта без постера.
**Решение:** проверять `if movie.poster:` перед выводом `movie.poster.url`.

### Ошибка 3 — Pillow не установлен или ошибка чтения изображения

Симптом: `OSError: cannot identify image file` или ошибка импорта.
**Решение:** `pip install Pillow`

### Ошибка 4 — перезапись файлов с одинаковыми именами

Симптом: новый файл затирает старый.
**Решение:** используйте уникальные имена (uuid) в `upload_to` или `FileSystemStorage.get_available_name`.

### Ошибка 5 — файл сохранён, но URL даёт 404

Симптом: файл в `media/` есть, но браузер отдаёт 404.
**Решение:** проверьте `MEDIA_ROOT`/`MEDIA_URL` и подключение `static()` в `urls.py` (только при `DEBUG=True`).

---

## 9. Безопасность и полезные дополнения

- **Проверяйте тип и размер** загружаемых файлов в `clean_<field>` формы.
- **Ограничивайте размер** (например, 5 MB) — см. пример в предыдущем уроке.
- **Сохраняйте оригинальные имена** в отдельном поле модели, если нужно помнить изначальное имя.
- **Используйте storage (S3, Azure, GCS)** в продакшене — `default_storage` абстрагирует логику сохранения.

---

## 10. Тестирование изменений в браузере

1. Запустите сервер: `python manage.py runserver`
2. Перейдите на страницу добавления фильма (например, `/movies/add/` или ваш маршрут).
3. Заполните поля и загрузите изображение (постер).
4. Отправьте форму.
5. Убедитесь, что:

   - вы попали на страницу деталей (или увидели сообщение об успехе);
   - файл появился в `media/posters/...`;
   - при просмотре детальной страницы изображение видно (`<img src="{{ movie.poster.url }}">`).

---

## Практика

1. Добавьте в `Movie` поле `trailer = models.FileField(upload_to='trailers/%Y/%m/%d/', blank=True, null=True)`. Создайте `ModelForm` и страницу для загрузки трейлера. После создания фильма убедитесь, что файл появился в `media/trailers/...` и вы можете получить к нему URL: `movie.trailer.url`.

---

2. Сделайте так, чтобы при загрузке постера имя файла заменялось на UUID (с сохранением расширения), и файлы сохранялись в `posters/<slug>/`.

---

3. Добавьте в `MovieWithPosterForm` проверку `clean_poster`, которая запрещает файлы больше 3MB.

---

## Сравнить решение

1. Форма добавления трейлера (видео) через модель

`models.py`:

```python
trailer = models.FileField(upload_to='trailers/%Y/%m/%d/', blank=True, null=True, verbose_name="Трейлер")
```

`forms.py`:

```python
class MovieWithTrailerForm(forms.ModelForm):
    class Meta:
        model = Movie
        fields = ['title','slug','year','genre','trailer']
```

`views.py`:

```python
def add_movie_trailer(request):
    if request.method == 'POST':
        form = MovieWithTrailerForm(request.POST, request.FILES)
        if form.is_valid():
            movie = form.save()
            return redirect('movie_detail', pk=movie.pk)
    else:
        form = MovieWithTrailerForm()
    return render(request, 'cinemahub/add_movie_trailer.html', {'form': form})
```

Шаблон: как раньше — `enctype="multipart/form-data"`.

---

2. Уникальные имена постеров через UUID

`models.py`:

```python
import os, uuid

def poster_upload_to(instance, filename):
    ext = os.path.splitext(filename)[1]
    name = f"{uuid.uuid4().hex}{ext}"
    return os.path.join('posters', instance.slug, name)

poster = models.ImageField(upload_to=poster_upload_to, blank=True, null=True)
```

Миграции, затем тест.

---

3. Валидация размера файла poster <= 3MB

`forms.py`:

```python
class MovieWithPosterForm(forms.ModelForm):
    class Meta:
        model = Movie
        fields = ['title', 'slug', 'poster', 'year', 'genre']

    def clean_poster(self):
        poster = self.cleaned_data.get('poster')
        if poster:
            max_mb = 3
            if poster.size > max_mb * 1024 * 1024:
                raise forms.ValidationError(f"Максимальный размер постера — {max_mb} MB")
        return poster
```

---

# Контрольные вопросы (с ответами включены в материал)

1. **Что делает `upload_to` у `FileField`/`ImageField`?**
2. **Почему нужно передавать `request.FILES` в форму?**
3. **Чем `ImageField` отличается от `FileField`?**
4. **Как предотвратить перезапись файлов с одинаковыми именами?**
5. **Что нужно добавить в `settings.py` для работы медиа?**
6. **Как проверить размер загруженного файла в форме?**
7. **Почему `form.save()` удобен в ModelForm?**
8. **Как отобразить загруженную картинку в шаблоне?**
9. **Что делать, если `poster.url` даёт 404?**
10. **Нужен ли Pillow для FileField?**

---

[Предыдущий урок](lesson44.md) | [Следующий урок](lesson46.md)
