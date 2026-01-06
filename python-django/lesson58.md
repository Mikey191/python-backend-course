# Модуль 9. Урок 58. Декоратор `login_required` и класс `LoginRequiredMixin`

## Зачем вообще ограничивать доступ

На текущем этапе проекта _cinemahub_ мы уже умеем:

- отображать список фильмов;
- просматривать детальную страницу фильма;
- работать с категориями, жанрами, актёрами и режиссёрами.

Однако есть важный момент:
**не все действия в приложении должны быть доступны анонимным пользователям**.

Например:

- добавление фильма;
- редактирование описания;
- публикация (`is_published=True`);
- доступ к служебным страницам проекта.

Именно здесь появляется необходимость **ограничивать доступ** и пускать на страницу **только авторизованных пользователей**.

Django предоставляет для этого два основных инструмента:

- декоратор `login_required` — для функциональных представлений;
- миксин `LoginRequiredMixin` — для представлений на основе классов.

---

## Ограничение доступа к функциональным представлениям (`login_required`)

### Базовый пример

Создадим простую страницу, доступную **только авторизованным пользователям**.
Например, страницу «Мои фильмы», где в будущем пользователь будет видеть фильмы, добавленные им лично.

**Файл:** `movies/views.py`

```python
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

@login_required
def my_movies(request):
    return HttpResponse("Страница доступна только авторизованным пользователям")
```

Здесь происходит следующее:

- Django проверяет `request.user.is_authenticated`;
- если пользователь **авторизован** — функция выполняется;
- если **нет** — Django автоматически перенаправляет его на страницу входа.

---

### Проверка результата в браузере

1. Запустите сервер:

   ```bash
   python manage.py runserver
   ```

2. Откройте страницу `http://127.0.0.1:8000/movies/my/`
3. Если вы **не авторизованы**, произойдёт редирект на адрес вида:

   ```
   /accounts/login/?next=/movies/my/
   ```

Параметр `next` — ключевой момент.
Он говорит Django: _«после успешного входа верни пользователя туда, куда он изначально хотел попасть»_.

---

## Настройка `LOGIN_URL`

Если в проекте **нет URL `/accounts/login/`**, пользователь попадёт на несуществующую страницу (404).

Чтобы этого избежать, необходимо явно указать Django, **где находится форма входа**.

**Файл:** `settings.py`

```python
LOGIN_URL = 'users:login'
```

> Здесь `users:login` — это именованный URL формы входа.

Теперь:

- Django будет корректно перенаправлять пользователя;
- параметр `next` будет добавляться автоматически;
- после входа пользователь вернётся на защищённую страницу.

---

## Переопределение `login_url` прямо в декораторе

Иногда нужно задать страницу входа **локально**, не меняя глобальные настройки.

```python
@login_required(login_url='/admin/')
def my_movies(request):
    return HttpResponse("Только для авторизованных")
```

Приоритет:

1. `login_url` в декораторе
2. `LOGIN_URL` в `settings.py`

---

## Ограничение доступа в class-based views (`LoginRequiredMixin`)

В проекте _cinemahub_ мы активно используем **представления на основе классов**, поэтому основной инструмент здесь — `LoginRequiredMixin`.

---

### Пример: добавление фильма

Создадим страницу добавления фильма, доступную только после входа.

**Файл:** `movies/views.py`

```python
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView
from .models import Movie

class MovieCreateView(LoginRequiredMixin, CreateView):
    model = Movie
    fields = ['title', 'description', 'year', 'category']
    template_name = 'movies/movie_form.html'
    success_url = '/'
```

Важно:

- `LoginRequiredMixin` **всегда указывается первым**;
- если пользователь не авторизован — Django выполнит редирект.

---

### Проверка результата

1. Выйдите из аккаунта
2. Попробуйте открыть страницу добавления фильма
3. Django автоматически перенаправит вас на страницу входа

После авторизации вы вернётесь на форму добавления фильма.

---

## Указание `login_url` в классе

Аналогично декоратору:

```python
class MovieCreateView(LoginRequiredMixin, CreateView):
    login_url = '/admin/'
    ...
```

---

## Привязка фильма к пользователю (авторство)

Теперь логичный шаг — **сохранить информацию о том, кто добавил фильм**.

### Добавление поля `author` в модель Movie

**Файл:** `movies/models.py`

```python
from django.contrib.auth import get_user_model
from django.db import models

class Movie(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    year = models.PositiveIntegerField()
    category = models.ForeignKey('Category', on_delete=models.PROTECT)
    author = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True,
        related_name='movies'
    )
```

Почему так:

- `get_user_model()` — правильный способ работы с пользователем;
- `SET_NULL` — фильм не удалится, если пользователь будет удалён;
- `related_name='movies'` — удобный доступ `user.movies.all()`.

---

### Применение миграций

```bash
python manage.py makemigrations
python manage.py migrate
```

Проверьте:

- таблица `movies_movie` содержит поле `author_id`.

---

## Автоматическое назначение автора

Пользователь **не должен выбирать себя из списка**.
Автор назначается автоматически.

**Файл:** `movies/views.py`

```python
class MovieCreateView(LoginRequiredMixin, CreateView):
    model = Movie
    fields = ['title', 'description', 'year', 'category']
    template_name = 'movies/movie_form.html'
    success_url = '/'

    def form_valid(self, form):
        movie = form.save(commit=False)
        movie.author = self.request.user
        return super().form_valid(form)
```

Алгоритм:

1. Объект создаётся в памяти
2. Назначается текущий пользователь
3. Объект сохраняется в БД

---

### Возможная ошибка

**Ошибка:**
`NOT NULL constraint failed: movies_movie.author_id`

**Причина:**

- забыли `null=True` в модели;
- не назначили автора в `form_valid()`.

---

## Отображение автора в шаблоне

**Файл:** `templates/movies/movie_list.html`

```html
<p>
  {{ movie.title }} — добавлен пользователем: {{
  movie.author.username|default:"неизвестен" }}
</p>
```

---

## Проверка результата

1. Авторизуйтесь
2. Добавьте новый фильм
3. Убедитесь:

   - фильм сохранился;
   - автор отображается корректно;
   - анонимный пользователь не может добавить фильм.

---

## Практические задания

### Задание 1

Создайте страницу со списком **черновиков фильмов** (`is_published=False`), доступную только авторизованным пользователям.

---

## Задание 2

Ограничьте доступ к странице редактирования фильма с помощью `LoginRequiredMixin`.

---

## Задание 3

Сделайте так, чтобы пользователь видел **только свои фильмы** на странице «Мои фильмы».

---

## Сравнить решение

### Решение задания 1

```python
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import Movie

@login_required
def drafts(request):
    movies = Movie.objects.filter(is_published=False)
    return render(request, 'movies/drafts.html', {'movies': movies})
```

---

### Решение задания 2

```python
from django.views.generic import UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin

class MovieUpdateView(LoginRequiredMixin, UpdateView):
    model = Movie
    fields = ['title', 'description']
    template_name = 'movies/movie_form.html'
```

---

### Решение задания 3

```python
@login_required
def my_movies(request):
    movies = Movie.objects.filter(author=request.user)
    return render(request, 'movies/my_movies.html', {'movies': movies})
```

---

## Вопросы

1. Чем отличается `login_required` от `LoginRequiredMixin`?
2. Почему `LoginRequiredMixin` должен быть первым в списке наследования?
3. Что делает параметр `next`?
4. Где задаётся `LOGIN_URL`?
5. Зачем использовать `get_user_model()`?
6. В каком методе корректно назначать автора объекта?
7. Что произойдёт, если пользователь не авторизован?
8. Как проверить результат без тестов?

---

[Предыдущий урок](lesson57.md) | [Следующий урок](lesson59.md)
