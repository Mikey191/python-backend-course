# Модуль 7. Урок 44. Загрузка (upload) файлов на сервер в Django

Загрузка файлов — типичная веб-задача: постеры фильмов, трейлеры, документы, обложки, аватары. В Django есть простые и безопасные инструменты для приёма и хранения файлов. В этом уроке разберём:

* базовую HTML-форму для загрузки;
* как обрабатывать файлы в `views` (`request.FILES`);
* использовать Django-формы (`FileField`, `ImageField`);
* безопасное сохранение: `FileSystemStorage` / `default_storage` / уникальные имена;
* сохранение файлов через модель (`FileField` / `ImageField`);
* настройку `MEDIA_ROOT`/`MEDIA_URL` и обслуживание медиа в режиме разработки;
* типичные ошибки (и как их фиксить);
* практические задания с решениями.

---

## 0. Что нужно предусмотреть заранее

1. Для работы с изображениями требуется библиотека **Pillow**. Установите:

```
pip install Pillow
```

2. В `settings.py` добавьте (если ещё нет):

```python
import os
BASE_DIR = Path(__file__).resolve().parent.parent

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'
```

3. В режиме разработки подключите выдачу медиа в `urls.py` проекта (обычно `project/urls.py`):

```python
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # ... ваши маршруты ...
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

Теперь загруженные файлы будут доступны по `http://127.0.0.1:8000/media/...` в режиме разработки.

---

## 1. Базовая HTML-форма для загрузки файлов

**Важно:** форма, отправляющая файлы, должна иметь `enctype="multipart/form-data"`; без этого файлов в `request.FILES` не будет.

### Шаблон — `templates/movies/upload_basic.html`

```html
<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <title>Загрузка файла — cinemahub</title>
</head>
<body>
  <h1>Загрузка файла (базовая)</h1>

  <form action="" method="post" enctype="multipart/form-data">
    {% csrf_token %}
    <p><input type="file" name="file_upload"></p>
    <p><button type="submit">Загрузить</button></p>
  </form>

  {% if saved %}
    <p>Файл сохранён: {{ saved }}</p>
  {% endif %}
</body>
</html>
```

### Представление — `movies/views.py` (базовый способ, ручное сохранение)

```python
import os
from django.conf import settings
from django.shortcuts import render

def upload_basic_view(request):
    saved = None

    if request.method == "POST":
        uploaded_file = request.FILES.get('file_upload')
        if uploaded_file:
            # убедимся, что папка media/uploads существует
            upload_dir = os.path.join(settings.MEDIA_ROOT, 'uploads')
            os.makedirs(upload_dir, exist_ok=True)

            file_path = os.path.join(upload_dir, uploaded_file.name)
            with open(file_path, 'wb+') as dest:
                for chunk in uploaded_file.chunks():
                    dest.write(chunk)

            # путь, который можно показать пользователю
            saved = f"{settings.MEDIA_URL}uploads/{uploaded_file.name}"
        else:
            saved = "Файл не выбран"

    return render(request, 'movies/upload_basic.html', {'saved': saved})
```

**Проверка:** зайдите на страницу, выберите файл и загрузите. В папке `media/uploads` должен появиться файл, и вы увидите ссылку `/media/uploads/<имя>`.

---

## 2. Почему лучше использовать Django-формы и storage

Ручное открытие и запись файлов работает, но у Django есть встроенные механизмы:

* `forms.FileField` / `forms.ImageField` — автоматическая валидация;
* `django.core.files.storage.FileSystemStorage` (или `default_storage`) — абстракция хранилища, обеспечивает корректную работу путей и замену/переименование;
* `form.is_valid()` — проверит, что файл выбран и соответствует типу (для `ImageField`).

Используем их.

---

## 3. Загрузка через Django-форму

### Форма — `movies/forms.py`

```python
from django import forms

class UploadFileForm(forms.Form):
    file = forms.FileField(label="Файл")
```

(Если нужен только image: `file = forms.ImageField(label="Изображение")` — проверит формат.)

### Представление — `movies/views.py`

```python
from django.shortcuts import render
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from .forms import UploadFileForm

import uuid
import os

def upload_with_form_view(request):
    saved_url = None

    if request.method == "POST":
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            f = form.cleaned_data['file']
            # создаём уникальное имя
            name, ext = os.path.splitext(f.name)
            unique_name = f"{name}_{uuid.uuid4().hex}{ext}"
            path = f"uploads/{unique_name}"

            # default_storage.save вернёт путь, по которому сохранён файл
            saved_path = default_storage.save(path, ContentFile(f.read()))
            saved_url = default_storage.url(saved_path)
    else:
        form = UploadFileForm()

    return render(request, 'movies/upload_form.html', {'form': form, 'saved_url': saved_url})
```

### Шаблон — `templates/movies/upload_form.html`

```html
<h1>Загрузка через Django Form</h1>

<form method="post" enctype="multipart/form-data">
  {% csrf_token %}
  {{ form.as_p }}
  <button type="submit">Загрузить</button>
</form>

{% if saved_url %}
  <p>Файл сохранён: <a href="{{ saved_url }}">{{ saved_url }}</a></p>
{% endif %}
```

**Пояснение:** `default_storage` использует `MEDIA_ROOT`/`MEDIA_URL`. `ContentFile(f.read())` — читаем содержимое в память; можно использовать `f` напрямую (для больших файлов лучше работать через `chunks()` и `FileSystemStorage`).

---

## 4. Уникальные имена и избегание перезаписи

Мы использовали `uuid` для генерации уникального имени. Альтернативы:

* `django.utils.text.get_valid_filename` + `uuid` для чистого имени;
* `FileSystemStorage.get_available_name(name)` — если имя занято, функция вернёт свободное имя.

Пример с `FileSystemStorage`:

```python
from django.core.files.storage import FileSystemStorage

fs = FileSystemStorage(location=settings.MEDIA_ROOT + '/uploads')

filename = fs.save(unique_name, f)  # f — объект файла
file_url = fs.url(filename)
```

---

## 5. Хранение файлов в модели (рекомендуется для сущностей типа Movie)

Часто файлы — атрибут модели (постер фильма). Тогда используется `FileField`/`ImageField` в модели и `ModelForm` для сохранения.

### Модель — `cinemahub/models.py`

```python
from django.db import models

def movie_poster_path(instance, filename):
    # сохраняем в media/posters/movie_<id>/<filename>
    return f"posters/movie_{instance.id}/{filename}"

class Movie(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    poster = models.ImageField(upload_to='posters/%Y/%m/%d/', blank=True, null=True)
    # или с функцией:
    # poster = models.ImageField(upload_to=movie_poster_path, blank=True, null=True)
    # остальные поля...
```

`upload_to` задаёт путь внутри `MEDIA_ROOT`. Можно использовать шаблоны (`%Y`, `%m`, `%d`) или callable функции.

### ModelForm — `cinemahub/forms.py`

```python
from django import forms
from .models import Movie

class MovieWithPosterForm(forms.ModelForm):
    class Meta:
        model = Movie
        fields = ['title', 'slug', 'poster', 'year', 'genre', 'is_published']
```

### Представление — `cinemahub/views.py`

```python
def add_movie_with_poster(request):
    if request.method == 'POST':
        form = MovieWithPosterForm(request.POST, request.FILES)
        if form.is_valid():
            movie = form.save()
            return redirect('movie_detail', pk=movie.pk)
    else:
        form = MovieWithPosterForm()

    return render(request, 'cinemahub/add_movie_with_poster.html', {'form': form})
```

### Шаблон — `templates/cinemahub/add_movie_with_poster.html`

```html
<h1>Добавить фильм с постером</h1>

<form method="post" enctype="multipart/form-data">
  {% csrf_token %}
  {{ form.as_p }}
  <button type="submit">Сохранить фильм</button>
</form>
```

**Проверка:** после сохранения в `MEDIA_ROOT/posters/...` появится файл и в админке/деталке можно отобразить `<img src="{{ movie.poster.url }}">`.

---

## 6. Отображение загруженных медиа в шаблонах (dev)

В шаблоне, когда у объекта есть `ImageField`:

```html
{% if movie.poster %}
  <img src="{{ movie.poster.url }}" alt="{{ movie.title }}" />
{% endif %}
```

Важно: в режиме разработки — мы уже подключили `static()` для `MEDIA_URL` в `urls.py` (см. начало урока). На проде отдавать медиа должен веб-сервер (nginx, s3 и т.п.).

---

## 7. Частые ошибки и способы исправить

### 1) Забыл `enctype="multipart/form-data"`

Симптом: `request.FILES` пуст, `form.is_valid()` для `FileField` — False или файл не передаётся.
Решение: добавьте `enctype`.

### 2) Неправильно настроен `MEDIA_ROOT` / `MEDIA_URL`

Симптом: файл сохраняется, но ссылка `{{ file.url }}` не работает — 404.
Решение: проверьте `settings.MEDIA_ROOT` и подключение `urlpatterns += static(...)` в режиме DEBUG.

### 3) Ошибка импорта Pillow / `OSError: cannot identify image file`

Симптом: сервер падает при загрузке изображения.
Решение: `pip install Pillow`.

### 4) Перезапись файлов с одинаковыми именами

Симптом: новый файл затирает старый.
Решение: генерируйте уникальные имена (`uuid`, `get_available_name`) или используйте папки по дате.

### 5) Слишком большие файлы

Симптом: память/время обработки растёт, возможен отказ.
Решение: ограничить размер на уровне формы (проверка в `clean_file`) или настроить сервер и Nginx; использовать `chunks()` при сохранении.

Пример проверки размера файла в форме:

```python
class UploadFileForm(forms.Form):
    file = forms.FileField()

    def clean_file(self):
        f = self.cleaned_data['file']
        max_mb = 5
        if f.size > max_mb * 1024 * 1024:
            raise forms.ValidationError(f"Максимальный размер файла — {max_mb}MB")
        return f
```

---

## 8. Тестирование: как проверять изменения в браузере

1. Убедитесь, что `DEBUG = True` и `MEDIA_ROOT` настроен.
2. Перейдите на страницу загрузки (`/movies/upload/` или ваш маршрут).
3. Попробуйте:

   * загрузить картинку — должно появиться сообщение со ссылкой (`/media/...`) и файл в `media/`;
   * загрузить большой файл > лимита — увидеть ошибку;
   * загрузить файл с тем же именем — убедиться, что используем unique naming;
   * в случае ModelForm — проверить, что поле `poster` заполнилось (`movie.poster.url`) и картинка отображается.

---

## Практика

1. Создайте страницу `/movies/upload-size/`, где пользователь загружает файл. Ограничьте размер до 2 MB. При успешной загрузке покажите ссылку.

---

2. Добавьте в модель `Movie` поле `poster = ImageField(...)`. Сделайте страницу создания фильма, где можно загрузить постер (ModelForm). Проверьте, что после создания постера можно вывести `<img src="{{ movie.poster.url }}">`.

---

3. Используя `FileSystemStorage`, сохраните загруженный файл в `media/uploads` и используйте `fs.get_available_name` или добавьте UUID. Покажите пользователю конечный URL.

---

## Сравнить решение

1. **Создайте страницу `/movies/upload-size/`. Ограничьте размер до 2 MB**.

`forms.py`

```python
class UploadFileForm(forms.Form):
    file = forms.FileField()

    def clean_file(self):
        f = self.cleaned_data['file']
        if f.size > 2 * 1024 * 1024:
            raise forms.ValidationError("Максимум 2MB")
        return f
```

`views.py`

```python
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import uuid, os

def upload_size_view(request):
    url = None
    if request.method == "POST":
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            f = form.cleaned_data['file']
            name, ext = os.path.splitext(f.name)
            unique_name = f"{name}_{uuid.uuid4().hex}{ext}"
            path = default_storage.save(f"uploads/{unique_name}", ContentFile(f.read()))
            url = default_storage.url(path)
    else:
        form = UploadFileForm()
    return render(request, 'movies/upload_size.html', {'form': form, 'url': url})
```

Шаблон похож на предыдущие.

---

2. **Добавьте в модель `Movie` поле `poster = ImageField(...)`**.

`models.py` — добавляем `poster = models.ImageField(upload_to='posters/%Y/%m/%d/', blank=True, null=True)`

`forms.py` — `MovieWithPosterForm` (ModelForm с полем poster).

`views.py` — `add_movie_with_poster` (как выше).

`templates` — `{{ form.as_p }}` + `enctype`.

Проверка: после сохранения открыть детальную страницу и вывести `movie.poster.url`.

---

3. **Уникальное имя с FileSystemStorage**

```python
from django.core.files.storage import FileSystemStorage
fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT,'uploads'), base_url=settings.MEDIA_URL+'uploads/')

uploaded = request.FILES['file']
name = fs.get_available_name(uploaded.name)
filename = fs.save(name, uploaded)
file_url = fs.url(filename)
```

---

## 10. Вопросы

1. Почему нужна `enctype="multipart/form-data"`?
2. Где хранятся загруженные файлы в проекте?
3. Чем `FileField` отличается от `ImageField`?
4. Как предотвратить перезапись файлов с одинаковыми именами?
5. Почему лучше использовать `default_storage` или `FileSystemStorage`, а не `open(...,'wb')`?
6. Как в форме ограничить максимальный размер загружаемого файла?
7. Что делать, если `ImageField` не принимает изображение?
8. Как отображать загруженное изображение в шаблоне?
9. Куда ставить `upload_to` и что он делает?
10. Как обрабатывать очень большие файлы?

---

[Предыдущий урок](lesson43.md) | [Следующий урок](lesson45.md)