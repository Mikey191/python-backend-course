# Модуль 8. Урок 50. Класс FormView в Django

## Введение

Работа с HTML-формами — важная часть любого веб-приложения. До этого момента мы уже создавали формы вручную, использовали функции-представления и класс `View`, переопределяли методы `get()` и `post()`, передавали данные в шаблоны и обрабатывали результаты отправки форм.

Но Django предоставляет гораздо более удобный инструмент для работы с формами — **класс FormView**. Это полноценный класс-представление, ориентированный именно на задачу «показать форму → обработать отправку → вернуть результат».

Этот урок посвящён глубокому разбору `FormView`, пониманию его механизма работы, частых ошибок и практическому применению в проекте **cinemahub**.

Мы будем работать на примере формы добавления нового фильма в каталог. Это не финальная реализация функционала (позже в практике мы будем делать всё по-настоящему), но идеальный учебный контекст, чтобы сосредоточиться на механике `FormView`.

---

## 1. Зачем нужен FormView

Когда мы создаём форму через обычный `View`, нам приходится вручную писать:

- получение формы на GET-запрос
- обработку данных на POST-запрос
- проверку формы
- сохранение данных (если это форма, связанная с моделью)
- редирект после успешной отправки
- повторный рендеринг формы при ошибках

Это большой объём шаблонного кода, который приходится писать снова и снова.

`FormView` решает эту проблему:

- самостоятельно рендерит форму
- проверяет её валидность
- вызывает методы, которые мы можем переопределить — только там, где нужно
- выполняет редирект
- автоматически передаёт форму в контекст

При этом `FormView` не навязывает логику сохранения — она остаётся под контролем разработчика, что важно, например, когда нужно выполнить сложную бизнес-логику перед сохранением.

---

## 2. Создаём форму для добавления фильма

Пусть у нас есть задача: создать форму, через которую можно добавить новый фильм в каталог. Для урока нам не нужно использовать все поля модели `Movie`, достаточно нескольких.

### 2.1. Модель фильма (фрагмент)

Файл: **movies/models.py**

```python
class Movie(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    year = models.PositiveIntegerField()
    is_published = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
```

В этом уроке мы используем только часть полей, чтобы сфокусироваться на `FormView`.

---

### 2.2. Создаём форму

Файл: **movies/forms.py**

```python
from django import forms
from .models import Movie

class MovieCreateForm(forms.ModelForm):
    class Meta:
        model = Movie
        fields = ['title', 'description', 'year', 'is_published']
```

`ModelForm` сам выполнит всю необходимую валидацию — нам не нужно переписывать её вручную.

---

## 3. Создаём класс-представление на основе FormView

Теперь создадим класс, который будет отображать и обрабатывать форму.

Файл: **movies/views.py**

```python
from django.views.generic.edit import FormView
from django.urls import reverse_lazy

from .forms import MovieCreateForm

class MovieCreateView(FormView):
    template_name = 'movies/create_movie.html'
    form_class = MovieCreateForm
    success_url = reverse_lazy('movies:list')
```

Разберём:

- **template_name** — путь к шаблону, который будет использоваться для формы.
- **form_class** — класс формы, которая будет рендериться.
- **success_url** — куда перенаправить пользователя после успешного заполнения.

### Важный момент: почему reverse_lazy

`reverse_lazy()` откладывает вычисление URL до момента фактического вызова.
Это важно, потому что в момент загрузки `views.py` маршруты ещё не загружены.

Если использовать `reverse()`, можно получить ошибку:

```
django.core.exceptions.ImproperlyConfigured: The included URLconf ... does not appear to have any patterns in it.
```

`reverse_lazy` решает эту проблему.

---

## 4. Добавляем логику сохранения

По умолчанию `FormView` **ничего не сохраняет**. Он только проверяет форму.

Поэтому мы должны переопределить метод:

```python
def form_valid(self, form):
    form.save()
    return super().form_valid(form)
```

Дописываем в наш класс:

```python
class MovieCreateView(FormView):
    template_name = 'movies/create_movie.html'
    form_class = MovieCreateForm
    success_url = reverse_lazy('movies:list')

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)
```

Теперь после успешной отправки формы фильм действительно будет создан.

---

## 5. Передаём дополнительные данные в шаблон: extra_context

Иногда нам нужно пробросить заголовок, меню или любую другую информацию.

`FormView` позволяет сделать это без переопределения `get_context_data()`:

```python
extra_context = {
    'title': 'Добавление фильма',
}
```

Итоговая версия:

```python
class MovieCreateView(FormView):
    template_name = 'movies/create_movie.html'
    form_class = MovieCreateForm
    success_url = reverse_lazy('movies:list') # можно заменить на любую другую страницу, например index
    extra_context = {
        'title': 'Добавление фильма'
    }

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)
```

---

## 6. Подключаем маршрут

Файл: **movies/urls.py**

```python
from django.urls import path
from .views import MovieCreateView

app_name = 'movies'

urlpatterns = [
    path('add/', MovieCreateView.as_view(), name='add'),
]
```

---

## 7. Создаём шаблон для формы

Файл: **movies/templates/movies/create_movie.html**

```html
{% extends 'base.html' %} {% block content %}
<h1>{{ title }}</h1>

<form method="post">
  {% csrf_token %} {{ form.as_p }}

  <button type="submit">Добавить фильм</button>
</form>
{% endblock %}
```

---

## 8. Проверяем результат в браузере

После всех изменений запускаем сервер:

```
python manage.py runserver
```

Переходим в браузере:

```
http://127.0.0.1:8000/movies/add/
```

Должно отобразиться:

- Заголовок
- Форма с полями title, description, year
- Кнопка отправки

Проверка:

1. Заполняем форму.
2. Отправляем.
3. Если всё корректно — происходит редирект на `movies:list`.
4. Если формы нет или ошибки — проверяем:

   - корректность шаблона
   - правильность названия формы (form, а не movie_form и т.п.)
   - что форма наследует ModelForm

---

## 9. Частые ошибки и как их исправить

### Ошибка 1: TemplateDoesNotExist

**Причина:** неправильный путь в `template_name`.
**Как исправить:** убедиться, что файл расположен по указанному пути.

---

### Ошибка 2: NoReverseMatch при загрузке сервером

**Причина:** используете `reverse()` вместо `reverse_lazy()`
**Исправление:** заменить на `reverse_lazy()`.

---

### Ошибка 3: Форма не сохраняет данные

**Причина:** забыли переопределить `form_valid()`.
**Исправление:** добавить `form.save()`.

---

### Ошибка 4: Форма в шаблоне не отображается

**Причина:** используете неправильное имя переменной в шаблоне.
FormView передает форму как **form**.

---

## Практические задания

### Задание 1

Создайте класс-представление, основанный на `FormView`, который выводит форму добавления жанра (`Genre`).

Форма должна запрашивать два поля:

- `name`
- `slug`

Маршрут должен находиться по адресу `/genres/add/`.
После успешной отправки пользователь должен перенаправляться на страницу списка жанров (`genres:list`).

---

### Задание 2

Сделайте форму добавления режиссёра (`Director`) через `FormView`.

Форма должна отображать только поле `name`.

В шаблон нужно передать дополнительный контекст:
`title = "Добавление режиссёра"`

---

### Задание 3

Создайте форму добавления актёра (`Actor`) и модифицируйте `form_valid()` так, чтобы перед сохранением поле `name` автоматически приводилось к title-case (`str.title()`).

---

## Сравнить решение

### Решение задания 1

**forms.py**

```python
class GenreCreateForm(forms.ModelForm):
    class Meta:
        model = Genre
        fields = ['name', 'slug']
```

**views.py**

```python
class GenreCreateView(FormView):
    template_name = 'genres/create_genre.html'
    form_class = GenreCreateForm
    success_url = reverse_lazy('genres:list')

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)
```

**urls.py**

```python
path('add/', GenreCreateView.as_view(), name='add'),
```

---

### Решение задания 2

```python
class DirectorCreateView(FormView):
    template_name = 'directors/create_director.html'
    form_class = DirectorCreateForm
    success_url = reverse_lazy('directors:list')
    extra_context = {'title': 'Добавление режиссёра'}

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)
```

---

### Решение задания 3

```python
def form_valid(self, form):
    actor = form.save(commit=False)
    actor.name = actor.name.title()
    actor.save()
    return super().form_valid(form)
```

---

# 11. Вопросы

1. Для чего предназначен класс `FormView`?
2. Почему нельзя использовать `reverse()` вместо `reverse_lazy()` при определении `success_url` в классе?
3. Какой метод нужно переопределить, чтобы форма сохраняла данные?
4. Как передать дополнительные переменные в шаблон без переопределения `get_context_data()`?
5. Как Django передает форму в контекст шаблона? Под каким именем?
6. Что произойдет, если в шаблоне обратиться не к `form`, а, например, к `movie_form`?
7. Можно ли использовать FormView с обычной `forms.Form`, а не ModelForm?
8. Что делает метод `form_valid()`?
9. Что произойдет при невалидной форме?
10. Какие ошибки чаще всего возникают при работе с FormView и как их исправлять?

---

[Предыдущий урок](lesson49.md) | [Следующий урок](lesson51.md)
