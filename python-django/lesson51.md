# Модуль 8. Урок 51. Классы CreateView и UpdateView в Django

## Введение

В предыдущем уроке мы подробно разобрали `FormView` — универсальный инструмент для отображения и обработки HTML-форм. Однако в реальных проектах Django большинство форм напрямую связано с моделями базы данных: мы либо **создаём новый объект**, либо **редактируем существующий**.

Для этих двух сценариев Django предоставляет специализированные классы:

- **CreateView** — для создания новых объектов;
- **UpdateView** — для редактирования уже существующих записей.

Они построены поверх `FormView`, но идут дальше:
Django автоматически связывает форму с моделью, управляет сохранением объекта и заполняет форму данными из базы.

В этом уроке мы разберём:

- чем `CreateView` отличается от `FormView`;
- когда использовать форму, а когда — `fields`;
- как работает `UpdateView`;
- как выбирать объект для редактирования по `pk` и `slug`;
- какие ошибки встречаются чаще всего и почему они возникают.

Все примеры будут построены на сущностях проекта **cinemahub**, в первую очередь — на модели `Movie`.

---

## 1. Общая идея CreateView и UpdateView

Оба класса решают одну и ту же задачу — работу с моделью через форму, но в разных режимах:

| Класс      | Назначение                         |
| ---------- | ---------------------------------- |
| CreateView | Создание новой записи              |
| UpdateView | Редактирование существующей записи |

Они автоматически:

- создают форму на основе модели;
- валидируют данные;
- сохраняют объект в базе;
- выполняют редирект после успеха;
- передают форму в шаблон под именем `form`.

По сути, `CreateView` и `UpdateView` — это **FormView + ModelForm + логика сохранения**, упакованные в один класс.

---

## 2. CreateView: создание фильма

Начнём с самого распространённого сценария — добавления нового фильма в каталог.

### 2.1. Использование CreateView с готовой формой

Предположим, у нас уже есть форма `MovieCreateForm`, созданная в предыдущем уроке.

Файл: **movies/views.py**

```python
from django.views.generic import CreateView
from django.urls import reverse_lazy

from .models import Movie
from .forms import MovieCreateForm
```

Создадим класс-представление:

```python
class MovieCreateView(CreateView):
    form_class = MovieCreateForm
    template_name = 'movies/movie_form.html'
    success_url = reverse_lazy('movies:list')
    extra_context = {
        'title': 'Добавление фильма'
    }
```

#### Что здесь происходит

- `CreateView` сам:

  - создаёт экземпляр формы;
  - проверяет данные;
  - сохраняет объект `Movie`;

- `form_class` указывает, какую форму использовать;
- `template_name` — шаблон для отображения;
- `success_url` — куда перенаправлять после успеха;
- `extra_context` — дополнительные данные в шаблон.

### Проверка результата

1. Запускаем сервер.
2. Переходим в браузере на `/movies/add/`.
3. Видим форму добавления фильма.
4. Заполняем данные и отправляем.
5. Новый фильм появляется в базе, происходит редирект.

Если результат именно такой — `CreateView` работает корректно.

---

## 3. CreateView без явного указания формы

Иногда отдельная форма не нужна. Django позволяет создать форму **на лету**, прямо на основе модели.

### 3.1. Использование model + fields

Файл: **movies/views.py**

```python
class MovieCreateView(CreateView):
    model = Movie
    template_name = 'movies/movie_form.html'
    success_url = reverse_lazy('movies:list')
    fields = ['title', 'description', 'year', 'is_published']
    extra_context = {
        'title': 'Добавление фильма'
    }
```

В этом случае Django:

- автоматически создаёт `ModelForm`;
- включает в форму только указанные поля;
- сам выполняет `save()`.

### Когда это удобно

- форма простая;
- нет дополнительной логики;
- не требуется кастомная валидация.

### Когда лучше использовать `form_class`

- нужна сложная валидация;
- требуется переопределять `clean_*`;
- используется `commit=False`;
- форма применяется в нескольких местах.

---

## 4. Частая ошибка: обязательные поля

Если в модели есть **обязательное поле**, а вы забыли указать его в `fields`, при отправке формы произойдёт ошибка.

Пример проблемы:

```python
fields = ['title', 'year']
```

Если `description` обязательное — форма будет невалидной.

**Вывод:**
CreateView не отменяет требований модели. Все ограничения модели продолжают действовать.

---

## 5. UpdateView: редактирование фильма

Теперь перейдём ко второй ключевой задаче — редактированию существующего фильма.

### 5.1. Базовый пример UpdateView

Файл: **movies/views.py**

```python
from django.views.generic import UpdateView

class MovieUpdateView(UpdateView):
    model = Movie
    fields = ['title', 'description', 'year', 'is_published']
    template_name = 'movies/movie_form.html'
    success_url = reverse_lazy('movies:list')
    extra_context = {
        'title': 'Редактирование фильма'
    }
```

`UpdateView`:

- находит объект в базе;
- подставляет его данные в форму;
- сохраняет изменения после отправки.

---

## 6. Как UpdateView находит объект

По умолчанию `UpdateView` ищет объект по **pk**.

### 6.1. Маршрут с pk

Файл: **movies/urls.py**

```python
path('edit/<int:pk>/', MovieUpdateView.as_view(), name='edit'),
```

Переход по адресу:

```
/movies/edit/1/
```

Откроет форму редактирования фильма с `id=1`.

---

### 6.2. Использование slug вместо pk

Для проектов вроде cinemahub это более естественный вариант.

Маршрут:

```python
path('edit/<slug:slug>/', MovieUpdateView.as_view(), name='edit'),
```

Если поле в модели называется `slug`, Django использует его автоматически.

Если имя другое — можно явно указать:

```python
slug_field = 'slug'
slug_url_kwarg = 'slug'
```

---

## 7. Проверка результата редактирования

1. Переходим по URL редактирования.
2. Форма уже заполнена данными фильма.
3. Меняем значения.
4. Отправляем форму.
5. Изменения сохраняются в базе.

Если форма пустая — ошибка в маршруте или параметрах поиска объекта.

---

## 8. Общий шаблон для CreateView и UpdateView

Большое преимущество этих классов — **один шаблон** для создания и редактирования.

Пример: **movies/templates/movies/movie_form.html**

```html
{% extends 'base.html' %} {% block content %}
<h1>{{ title }}</h1>

<form method="post">
  {% csrf_token %} {{ form.as_p }}

  <button type="submit">Сохранить</button>
</form>
{% endblock %}
```

Шаблон не знает, создаём мы объект или редактируем — логика полностью в представлении.

---

## 9. Частые ошибки и причины

### Ошибка 1. 404 при редактировании

**Причина:** объект с таким pk или slug не существует.
**Решение:** проверить данные в базе.

---

### Ошибка 2. Форма не заполняется

**Причина:** неверное имя параметра в URL.
**Решение:** `pk`, `slug_url_kwarg` должны совпадать.

---

### Ошибка 3. Данные не сохраняются

**Причина:** обязательное поле отсутствует в `fields`.
**Решение:** проверить модель.

---

### Ошибка 4. Неправильный редирект

**Причина:** ошибка в `success_url`.
**Решение:** проверить `reverse_lazy()` и namespace.

---

## Практические задания

### Задание 1

Создайте `CreateView` для добавления жанра (`Genre`) без отдельной формы, используя `fields`.

Поля:

- name
- slug

---

### Задание 2

Создайте `UpdateView` для редактирования режиссёра (`Director`) по `pk`.

---

### Задание 3

Создайте `UpdateView` для редактирования фильма по `slug`.

---

## Сравнить решение

### Решение задания 1

```python
class GenreCreateView(CreateView):
    model = Genre
    fields = ['name', 'slug']
    template_name = 'genres/genre_form.html'
    success_url = reverse_lazy('genres:list')
```

---

### Решение задания 2

```python
class DirectorUpdateView(UpdateView):
    model = Director
    fields = ['name', 'slug']
    template_name = 'directors/director_form.html'
    success_url = reverse_lazy('directors:list')
```

### Решение задания 3

```python
class MovieUpdateView(UpdateView):
    model = Movie
    fields = ['title', 'description', 'year', 'is_published']
    template_name = 'movies/movie_form.html'
    success_url = reverse_lazy('movies:list')
```

Маршрут:

```python
path('edit/<slug:slug>/', MovieUpdateView.as_view(), name='edit'),
```

---

## Вопросы

1. В чём основное отличие `CreateView` от `FormView`?
2. Когда лучше использовать `fields`, а когда `form_class`?
3. Как `UpdateView` находит объект для редактирования?
4. Что произойдёт, если обязательное поле не указано в `fields`?
5. Можно ли использовать один шаблон для CreateView и UpdateView?
6. Как изменить способ поиска объекта (pk → slug)?
7. Где происходит сохранение данных в CreateView?
8. Какой метод отвечает за редирект после успеха?

---

[Предыдущий урок](lesson50.md) | [Следующий урок](lesson52.md)
