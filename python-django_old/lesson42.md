# Модуль 7. Урок 42. Валидация полей формы. Создание пользовательского валидатора

## Введение

Когда пользователь отправляет форму — это всегда риск. Он может:

- ошибиться в данных,
- случайно отправить пустые поля,
- ввести неправильный формат,
- попытаться подставить вредоносный текст.

Django защищает нас: все поля формы проходят строгую **валидацию**, прежде чем попасть в базу данных.
Задача этого урока — научиться использовать разные виды валидации:

## 1. Валидация полей формы: первые шаги

Создадим простую форму добавления фильма для приложения `movies`.

Файл: **movies/forms.py**

```python
from django import forms

class MovieForm(forms.Form):
    title = forms.CharField(
        max_length=100,
        min_length=2,
        label="Название фильма",
        widget=forms.TextInput(attrs={'class': 'form-input'}),
    )
```

### Что здесь происходит?

- `max_length=100` — ограничивает длину на уровне Django и HTML.
- `min_length=2` — минимальное количество символов.
- `widget` отвечает за отображение, но он не влияет на валидацию — проверка всё равно происходит на сервере.

### Проверка в браузере

Создадим временный шаблон формы:

Файл: **templates/movies/add_movie.html**

```html
<h1>Добавить фильм</h1>
<form method="post">
  {% csrf_token %} {{ form.as_p }}
  <button type="submit">Сохранить</button>
</form>
```

Файл: **movies/views.py**

```python
from django.shortcuts import render
from .forms import MovieForm

def add_movie(request):
    if request.method == "POST":
        form = MovieForm(request.POST)
        if form.is_valid():
            return render(request, "movies/add_movie.html", {
                "form": MovieForm(),
                "message": "Фильм успешно добавлен!"
            })
    else:
        form = MovieForm()

    return render(request, "movies/add_movie.html", {"form": form})
```

Файл: **movies/urls.py**

```python
from django.urls import path
from .views import add_movie

urlpatterns = [
    path("add/", add_movie, name="add_movie"),
]
```

### Как проверить?

1. Открываем:
   **[http://127.0.0.1:8000/movies/add/](http://127.0.0.1:8000/movies/add/)**
2. Вводим:

   - 1 символ → должна появиться ошибка.
   - более 100 символов → тоже ошибка.

3. Вводим корректное значение → сообщение “Фильм успешно добавлен!”

---

## 2. Кастомные сообщения об ошибках (`error_messages`)

Стандартные сообщения не всегда подходят:

- "Ensure this value has at least 2 characters" выглядит слишком технически.
- Иногда хочется подсказать пользователю что он сделал неправильно.

Обновим форму:

Файл: **movies/forms.py**

```python
class MovieForm(forms.Form):
    title = forms.CharField(
        max_length=100,
        min_length=2,
        label="Название фильма",
        widget=forms.TextInput(attrs={'class': 'form-input'}),
        error_messages={
            "required": "Название фильма обязательно.",
            "min_length": "Название должно быть длиннее 2 символов.",
            "max_length": "Название слишком длинное — максимум 100 символов.",
        }
    )
```

Теперь в браузере появятся **человекопонятные** сообщения.

---

## 3. Использование встроенных валидаторов (`validators=[]`)

Django предоставляет десятки готовых валидаторов.
Для примера — пусть у фильма есть поле `slug`:

Файл: **movies/forms.py**

```python
from django.core.validators import MinLengthValidator, MaxLengthValidator

class MovieForm(forms.Form):
    title = ...
    slug = forms.SlugField(
        label="URL фильма",
        validators=[
            MinLengthValidator(5, message="Минимум 5 символов."),
            MaxLengthValidator(50, message="Максимум 50 символов."),
        ]
    )
```

Попробуйте ввести в браузере:

- слишком короткий slug → ошибка,
- слишком длинный → ошибка,
- slug с пробелами → ошибка (SlugField их не допускает).

---

## 4. Создание пользовательского валидатора

Иногда встроенных ограничений мало.
Представим: название фильма должно содержать **только буквы, цифры, пробел и дефис** — ничего лишнего.

Для этого создадим валидатор:

Файл: **movies/validators.py**

```python
from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible

@deconstructible
class TitleValidator:
    ALLOWED = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 -"

    def __init__(self, message=None):
        self.message = message or "Название может содержать только буквы, цифры, пробел и дефис."

    def __call__(self, value):
        for char in value:
            if char not in self.ALLOWED:
                raise ValidationError(self.message)
```

### Подключаем валидатор в форму

Файл: **movies/forms.py**

```python
from .validators import TitleValidator

class MovieForm(forms.Form):
    title = forms.CharField(
        max_length=100,
        min_length=2,
        label="Название фильма",
        validators=[TitleValidator()],
    )
    slug = ...
```

### Проверяем

1. Вводим `Interstellar` → ок
2. Вводим `Интерстеллар` → ошибка (русские буквы запрещены)
3. Вводим `Spider-Man` → ок
4. Вводим `Avatar!!!` → ошибка

---

## 5. Валидация методом `clean_<field>()`

Если валидатор нужен только для одного поля — писать целый класс необязательно.

Файл: **movies/forms.py**

```python
class MovieForm(forms.Form):
    title = forms.CharField(max_length=100)
    slug = forms.SlugField()

    def clean_title(self):
        title = self.cleaned_data['title']
        if "  " in title:
            raise ValidationError("Название не должно содержать двойных пробелов.")
        return title
```

### Когда вызывается этот метод?

При вызове:

```python
form.is_valid()
```

---

## 6. Полный механизм валидации Django

Когда вызывается `form.is_valid()`, происходит следующее:

1. **Проверка типов данных** — что поле строка, число, slug и т.д.
2. **Проверка встроенных ограничений**
   (`min_length`, `max_length`, типы полей, обязательность)
3. **Запуск всех валидаторов** из списка `validators`
4. **Вызов методов `clean_<field>()`**
5. **Формирование `cleaned_data`**
   Если хотя бы одно нарушение — `is_valid()` возвращает False.

---

## 7. Частые ошибки и их причины

### ❌ Ошибка: «KeyError: 'title'»

Причина: поле не прошло валидацию → его нет в `cleaned_data`.

Решение:

```python
title = self.cleaned_data.get('title')
```

---

### ❌ Ошибка: «AttributeError: 'MovieForm' object has no attribute 'clean_title'»

Причина: название метода написано как `clean_Title` или `clean- title`.

Django вызывает только строго `clean_<имя_поля>`.

---

### ❌ Ошибка: валидатор не срабатывает

Причина: забыли добавить его в поле:

```python
validators=[MyValidator()]
```

---

## Практика

1. Создайте форму для добавления режиссёра (**DirectorForm**) с полем:

- `name` — строка от 3 до 50 символов
- Создайте кастомное сообщение об ошибке: «Имя режиссёра слишком короткое» (для min_length)

---

2. Добавьте в `DirectorForm` новое поле:

- `slug` — SlugField
- Создайте валидатор, который запрещает цифры в slug.

---

3. Добавьте метод `clean_name`, который запрещает двойные пробелы.

---

## Сравнить решение

1. Форма для добавление режиссёра с первым полем `name`

```python
class DirectorForm(forms.Form):
    name = forms.CharField(
        min_length=3,
        max_length=50,
        label="Имя режиссера",
        error_messages={
            "min_length": "Имя режиссёра слишком короткое.",
        }
    )
```

---

2. Добавить поле `slug`

**movies/validators.py**

```python
@deconstructible
class NoDigitsValidator:
    def __call__(self, value):
        for c in value:
            if c.isdigit():
                raise ValidationError("Slug не должен содержать цифры.")
```

**movies/forms.py**

```python
from .validators import NoDigitsValidator

class DirectorForm(forms.Form):
    name = ...
    slug = forms.SlugField(validators=[NoDigitsValidator()])
```

---

3. Добавьте метод `clean_name`.

```python
def clean_name(self):
    name = self.cleaned_data['name']
    if "  " in name:
        raise ValidationError("Имя не должно содержать двойных пробелов.")
    return name
```

---

## Вопросы

1. Что делает параметр `min_length` и где он срабатывает: в HTML, Django или обоих?
2. Как задать своё сообщение об ошибке для поля формы?
3. Что делает список `validators=`?
4. В чём разница между валидатором класса и методом `clean_<field>()`?
5. Зачем нужен декоратор `@deconstructible`?
6. Что такое `cleaned_data` и когда она формируется?
7. Почему может возникнуть ошибка `KeyError` при обращении к `cleaned_data`?
8. Когда вызывается метод `clean_title()`?
9. Может ли одно поле иметь несколько валидаторов?
10. Что произойдёт, если хотя бы один валидатор выбросит ValidationError?

---

[Предыдущий урок](lesson41.md) | [Следующий урок](lesson43.md)
