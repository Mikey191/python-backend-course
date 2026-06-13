# Модуль 6. Урок 37. Настройка формы редактирования записей в админ-панели Django

## Введение

На предыдущих уроках мы научились:

* выводить список записей в админ-панели,
* управлять отображением колонок,
* настраивать поиск и фильтры,
* добавлять собственные фильтры.

Теперь мы переходим к очень важной части работы администратора — **настройке формы редактирования записи**.
Именно эта форма открывается, когда администратор нажимает «Добавить» или «Изменить» запись в админ-панели.

Сегодня мы:

* разберём, как управлять полями формы,
* научимся скрывать поля,
* делать их только для чтения,
* автоматически заполнять `slug`,
* улучшать работу с полями Many-to-Many,
* обработаем типичные ошибки и посмотрим, как их исправлять.

---

## 1. Напоминание структуры моделей проекта *cinemahub*

Перед началом работы напомним структуру данных, которая используется в этом модуле курса.

Файлы находятся в приложении `movies`.

---

### **movies/models.py**

```python
from django.db import models
from django.utils.text import slugify

class Genre(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Actor(models.Model):
    name = models.CharField(max_length=120)
    slug = models.SlugField(unique=True)
    bio = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Movie(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    year = models.PositiveIntegerField()
    genre = models.ForeignKey(Genre, on_delete=models.PROTECT)
    actors = models.ManyToManyField(Actor, blank=True)
    is_published = models.BooleanField(default=True)

    def __str__(self):
        return self.title
```

---

Теперь мы будем настраивать админ-панель, опираясь именно на эту структуру.

---

## 2. Как Django формирует форму редактирования записи

По умолчанию Django:

* показывает все редактируемые поля модели,
* упорядочивает их в том порядке, в котором они объявлены в модели,
* делает все поля доступными для редактирования,
* отображает поля Many-to-Many в виде списка, где нужно зажимать **Ctrl**.

Мы можем изменить любое поведение с помощью параметров в классе `ModelAdmin`.

Для этого создаём файл:

```
movies/admin.py
```

Там будем указывать настройки.

---

## 3. Настройка списка отображаемых полей (`fields`)

Иногда администратору не нужны все поля модели.
Например, мы можем временно скрыть `is_published`, чтобы администратор не менял публикацию, или показывать поля в другом порядке.

### Пример

`movies/admin.py`:

```python
from django.contrib import admin
from .models import Movie, Genre, Actor

@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    fields = ['title', 'slug', 'description', 'year', 'genre']
```

Теперь при открытии фильма мы увидим только эти поля и именно в таком порядке.

---

### Проверка в браузере

1. Перейдите в админ-панель
   `http://127.0.0.1:8000/admin/movies/movie/`
2. Откройте любой фильм или создайте новый.
3. Убедитесь, что поля `actors` и `is_published` исчезли.

---

## 4. Почему могут появляться ошибки при сохранении записи

Предположим, мы попытались создать новый фильм, но не включили в форму обязательное поле `genre`:

```python
fields = ['title', 'slug', 'description', 'year']
```

При сохранении появится ошибка:

```
This field is required.
```

Django сообщает: поле **genre** обязательно, но его нет в форме.

---

### Как исправить

Просто добавляем поле:

```python
fields = ['title', 'slug', 'description', 'year', 'genre']
```

Теперь запись сохраняется корректно.

---

## 5. Исключение полей с `exclude`

Иногда удобнее **убрать** ненужные поля, чем перечислять нужные.

```python
@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    exclude = ['is_published']
```

Теперь поле `is_published` не отображается, а другие появятся автоматически.

> ⚠ Важно: нельзя одновременно использовать `fields` и `exclude`. Django выбросит ошибку.

---

## 6. Поля только для чтения: `readonly_fields`

Это полезно когда:

* поле не должно вручную редактироваться,
* оно вычисляется автоматически,
* администратор не должен его менять.

Например, поле `slug`.

```python
@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    fields = ['title', 'slug', 'description', 'year', 'genre']
    readonly_fields = ['slug']
```

Теперь `slug` виден, но изменить его нельзя.

---

## 7. Автоматическое заполнение поля `slug`

Существует два подхода:

---

### Вариант 1. Автогенерация slug в модели (универсальный)

Изменяем модель `Movie`.

`movies/models.py`:

```python
def save(self, *args, **kwargs):
    if not self.slug:
        self.slug = slugify(self.title)
    super().save(*args, **kwargs)
```

#### Плюсы:

* работает везде: админка, API, тесты, shell;
* защищает от пустого slug.

#### Минусы:

* может не понравиться, если slug должен заполняться вручную.

---

### Вариант 2. Автозаполнение slug в админ-панели (`prepopulated_fields`)

Это работает только на странице добавления записи.

`movies/admin.py`:

```python
@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("title",)}
```

Django автоматически подставляет slug при вводе заголовка.

`prepopulated_fields` выдаст ошибку, если одновременно поле будет `readonly_fields`
---

### Проверка

1. Открываем добавление нового фильма.
2. Печатаем название.
3. Смотрим, как поле slug заполняется автоматически.

---

## 8. Улучшение работы с множественным выбором (`ManyToManyField`)

По умолчанию Django показывает поле `actors` в виде списка, где нужно выделять элементы с Ctrl.
Это неудобно при большом количестве актёров.

Есть два варианта улучшения:

---

### Горизонтальный фильтр (`filter_horizontal`)

```python
class MovieAdmin(admin.ModelAdmin):
    fields = ['title', 'slug', 'description', 'year', 'genre', 'actors']
    filter_horizontal = ['actors']
```

Теперь у администратора появится:

* левый список — доступные актёры,
* правый список — выбранные,
* кнопки добавления/удаления.

---

### Вертикальный фильтр (`filter_vertical`)

```python
filter_vertical = ['actors']
```

То же самое, но блоки располагаются вертикально.

---

#### Проверка

1. Перейдите в редактирование фильма.
2. Найдите поле «actors».
3. Убедитесь, что интерфейс стал удобнее.

---

## 9. Частые ошибки при настройке формы и как их исправлять

### ❌ Ошибка: «Both 'fields' and 'exclude' are specified»

Причина: указаны одновременно `fields` и `exclude`.

✔ Решение: оставить только одно.

---

### ❌ Ошибка: «This field is required»

Причина: обязательное поле не включено в форму.

✔ Решение: добавить его в `fields` или убрать из `exclude`.

---

### ❌ Slug не заполняется автоматически

Причина: не указан `prepopulated_fields`.

✔ Решение: добавить

```python
prepopulated_fields = {"slug": ("title",)}
```

---

## 10. Полная итоговая версия `admin.py` после всех настроек

```python
from django.contrib import admin
from .models import Movie, Genre, Actor


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    fields = ['title', 'slug', 'description', 'year', 'genre', 'actors']
    readonly_fields = ['slug']
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ['actors']


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    search_fields = ['name']


@admin.register(Actor)
class ActorAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
```

---

## Практические задания

1. Убрать поле из формы. Сделайте так, чтобы поле `is_published` не отображалось при редактировании фильма.

2. Сделать поле `year` только для чтения. Сделайте поле `year` доступным только для просмотра.

3. Добавить автозаполнение slug у актёра. Используйте `prepopulated_fields`.

4. Улучшить интерфейс выбора актёров. Поменяйте отображение поля `ManyToMany` на удобный фильтр.

5. Изменить порядок полей в форме фильма. Порядок должен быть: title, year, genre, description, slug.

### Сравнить решение

1. Убрать поле из формы.

```python
class MovieAdmin(admin.ModelAdmin):
    exclude = ['is_published']
```

2. Сделать поле `year` только для чтения.

```python
readonly_fields = ['year']
```

3. Добавить автозаполнение slug у актёра.

```python
class ActorAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
```

4. Улучшить интерфейс выбора актёров.

```python
filter_horizontal = ['actors']
```

5. Изменить порядок полей в форме фильма.

```python
fields = ['title', 'year', 'genre', 'description', 'slug']
```

---

## Вопросы

1. Для чего используется атрибут `fields` в классе ModelAdmin?
2. Почему нельзя использовать `fields` и `exclude` одновременно?
3. Что делает атрибут `readonly_fields`?
4. В каких случаях стоит использовать автозаполнение slug?
5. Чем `prepopulated_fields` отличается от ручного автогенератора slug в модели?
6. Как улучшить интерфейс для выбора значений Many-to-Many?
7. Почему может появиться ошибка «This field is required»?
8. Где Django берёт порядок полей формы, если `fields` не указан?
9. Как сделать поле видимым, но не редактируемым?
10. Для чего назначают `filter_vertical` или `filter_horizontal`?

---

[Предыдущий урок](lesson36.md) | [Следующий урок](lesson38.md)