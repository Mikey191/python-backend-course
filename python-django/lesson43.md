# Модуль 7. Урок 43. Формы, связанные с моделями в Django (ModelForm)

Работа с обычными формами (`forms.Form`) — отличный способ понять, как Django принимает и валидирует данные. Но в реальных проектах очень часто данные формы должны сохраняться в базу данных. Например:

- форма добавления фильма,
- форма добавления актёра,
- форма редактирования жанра,
- форма добавления рецензии.

Если создавать такие формы вручную, каждый раз повторится одно и то же:

1. объявить поля формы,
2. проверить валидность,
3. вручную создать объект модели через `Model.objects.create()`,
4. обрабатывать уникальность, ограничения, ошибки.

Django решает эту проблему одним мощным инструментом — **ModelForm**.

---

## **Что такое ModelForm?**

`ModelForm` — это класс формы, который автоматически генерирует поля на основе модели.

Он:

- создаёт форму на основе модели;
- автоматически выполняет все её проверки;
- сам знает, как сохранить данные через `form.save()`;
- экономит огромное количество времени и кода.

---

## **Где создаём форму?**

Как и раньше — в файле:

```
cinemahub/forms.py
```

Если файла ещё нет — создаём.

---

## 1. Создаём форму, связанную с моделью

Предположим, у нас есть модель фильма:

### **`cinemahub/models.py`**

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

    def __str__(self):
        return self.title
```

---

### Теперь создаём форму для добавления фильма

#### **`cinemahub/forms.py`**

```python
from django import forms
from .models import Movie, Genre


class MovieForm(forms.ModelForm):
    class Meta:
        model = Movie
        fields = [
            "title",
            "slug",
            "description",
            "year",
            "is_published",
            "genre",
        ]
```

---

### Объяснение

- `model = Movie` говорит Django, с какой моделью связана форма.
- `fields` определяет, какие поля нужно вывести.
- Django автоматически создаст:

  - поля ввода текста,
  - textarea,
  - checkbox,
  - списки выбора,
  - валидаторы уникальности,
  - валидатор пустых значений,
  - типы значений (например, год должен быть числом).

То есть то, что раньше нужно было писать вручную, теперь работает «из коробки».

---

## 2. Настройка отображения формы

Обычно формы нужно немного «причесать»: добавить CSS-классы, изменить размеры полей, задать метки.

Для этого внутри `Meta` используется ключ `widgets`.

### **`cinemahub/forms.py`**

```python
class MovieForm(forms.ModelForm):
    class Meta:
        model = Movie
        fields = ["title", "slug", "description", "year", "is_published", "genre"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-input"}),
            "description": forms.Textarea(attrs={"rows": 5, "cols": 60}),
        }
        labels = {
            "slug": "URL фильма",
            "year": "Год выхода",
        }
```

---

## 3. Добавляем empty_label для полей выбора

Поле `genre` — это ForeignKey. Django отобразит его как `<select>`. Но иногда хочется добавить вариант «Выберите жанр».

Тогда переопределяем поле:

```python
genre = forms.ModelChoiceField(
    queryset=Genre.objects.all(),
    empty_label="Жанр не выбран",
    label="Жанр",
)
```

Поле при этом нужно вынести _наружу_ класса Meta.

---

## 4. Используем форму в представлении

Создадим страницу добавления фильма.

---

### **`cinemahub/views.py`**

```python
from django.shortcuts import render, redirect
from .forms import MovieForm


def add_movie(request):
    if request.method == "POST":
        form = MovieForm(request.POST)
        if form.is_valid():
            form.save()       # <-- самое важное!
            return redirect("home")
    else:
        form = MovieForm()

    return render(request, "cinemahub/add_movie.html", {"form": form})
```

---

### Что происходит при `form.save()`?

1. Django создаёт объект Movie.
2. Переносит в него данные формы.
3. Валидирует уникальность `slug`.
4. Сохраняет объект в базу.

`ModelForm` делает всю работу за нас.

---

## 5. Создаём шаблон для формы

### **`cinemahub/templates/cinemahub/add_movie.html`**

```html
<h1>Добавить фильм</h1>

<form method="post">
  {% csrf_token %} {{ form.as_p }}

  <button type="submit">Сохранить</button>
</form>
```

---

## 6. Проверяем работу формы

Запускаем сервер:

```
python manage.py runserver
```

Переходим по адресу:

```
/add-movie/
```

Пробуем:

- оставить поля пустыми,
- ввести slug с пробелами,
- указать текст в поле `year`,
- указать уже существующий slug.

Каждая ошибка будет отображена автоматически — Django всё сделает сам.

---

## 7. Добавляем собственную валидацию

Допустим, мы хотим:

- ограничить максимальную длину названия (например, 50 символов)
- запретить использовать числа в названии фильма

Реализуем метод `clean_<поле>`:

### **`cinemahub/forms.py`**

```python
from django.core.exceptions import ValidationError

class MovieForm(forms.ModelForm):
    class Meta:
        model = Movie
        fields = ["title", "slug", "description", "year", "is_published", "genre"]

    def clean_title(self):
        title = self.cleaned_data["title"]

        if len(title) > 50:
            raise ValidationError("Название фильма не должно превышать 50 символов")

        if any(char.isdigit() for char in title):
            raise ValidationError("Название фильма не может содержать цифры")

        return title
```

---

## Возможные ошибки и как их исправить

### ❌ _Ошибка:_ «UNIQUE constraint failed: cinemahub_movie.slug»

**Причина:** пользователь ввёл slug, который уже существует.

**Решение:** Django автоматически отобразит ошибку под полем slug.

---

### ❌ _Ошибка:_ ValidationError при сохранении

Чаще всего происходит, если:

- неправильно написан метод clean_title
- забыто `return title`

---

### ❌ _Форма не отображает ошибки_

Проверьте шаблон: в нём должно быть либо `{{ form }}`, либо `{{ form.as_p }}`.

---

## Практика

1. Создать форму для добавления жанра. Создайте форму `GenreForm`, которая:

- связана с моделью Genre
- имеет одно поле `name`
- ограничивает длину имени жанра до 30 символов (через `clean_name`)
- добавляет CSS-класс `form-input`

Создайте представление `add_genre` и шаблон `add_genre.html`, в котором форма выводится через `{{ form.as_p }}`.

---

2. Проверка уникальности названия фильма. Создайте в форме MovieForm метод `clean_title`, который:

- запрещает вводить одинаковые названия разных фильмов (проверяет через Movie.objects.filter)

---

3. Стилизовать форму через widgets. Создайте форму `MovieFormMinimal`, в которой:

- выводятся только поля title и year
- поля получают CSS-класс `input-min`

---

## Сравнить решение

1. Создать форму для добавления жанра.

**`cinemahub/forms.py`**

```python
class GenreForm(forms.ModelForm):
    class Meta:
        model = Genre
        fields = ["name"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-input"}),
        }

    def clean_name(self):
        name = self.cleaned_data["name"]
        if len(name) > 30:
            raise ValidationError("Длина жанра не может превышать 30 символов")
        return name
```

**`cinemahub/views.py`**

```python
def add_genre(request):
    if request.method == "POST":
        form = GenreForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("home")
    else:
        form = GenreForm()

    return render(request, "cinemahub/add_genre.html", {"form": form})
```

**`add_genre.html`**

```html
<h1>Добавить жанр</h1>

<form method="post">
  {% csrf_token %} {{ form.as_p }}
  <button type="submit">Сохранить</button>
</form>
```

---

2. Проверка уникальности названия фильма.

```python
def clean_title(self):
    title = self.cleaned_data["title"]

    if Movie.objects.filter(title=title).exists():
        raise ValidationError("Фильм с таким названием уже существует")

    return title
```

---

3. Стилизовать форму через widgets.

```python
class MovieFormMinimal(forms.ModelForm):
    class Meta:
        model = Movie
        fields = ["title", "year"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "input-min"}),
            "year": forms.NumberInput(attrs={"class": "input-min"}),
        }
```

---

## Вопросы

1. Что такое ModelForm и в чём его отличие от обычной формы?
2. Где в Django указывается связь формы и модели?
3. Для чего используется класс Meta?
4. Что делает метод `form.save()`?
5. Где лучше размещать кастомные валидаторы для полей формы?
6. Когда применяется метод `clean_<имя_поля>`?
7. Что делает атрибут `widgets` в классе Meta?
8. Как добавить placeholder или CSS-класс к полю формы?
9. Как работает проверка уникальности slug?
10. Зачем нужен `empty_label` в `ModelChoiceField`?

---

[Предыдущий урок](lesson42.md) | [Следующий урок](lesson44.md)
