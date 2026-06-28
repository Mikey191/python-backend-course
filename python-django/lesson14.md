# Урок 14. Поиск, фильтры, пользовательские поля и действия в админ-панели Django

## От базового списка к рабочему инструменту

В прошлом уроке мы настроили отображение списка — колонки, редактирование прямо из таблицы. Но при большом каталоге фильмов нужно быстро находить нужные записи и выполнять массовые операции. Сегодня добавляем поиск, фильтры, вычисляемые колонки и собственные действия.

---

## search_fields — поиск по записям

`search_fields` добавляет строку поиска над списком объектов:

```python
# films/admin.py
@admin.register(Film)
class FilmAdmin(admin.ModelAdmin):
    list_display = ('title', 'year', 'rating', 'director')
    list_display_links = ('title',)
    list_editable = ('rating',)
    search_fields = ('title', 'description')
```

Django выполняет поиск по принципу `icontains` для каждого указанного поля, объединяя условия через `OR` — введённая строка ищется и в названии, и в описании одновременно.

### Поиск по связанным моделям

Через `__` можно искать и в полях связанных моделей — это та же нотация Field Lookups, что мы изучали в уроке 9:

```python
search_fields = ('title', 'description', 'director__name')
```

Теперь поиск «Коппола» в админке найдёт все фильмы этого режиссёра, даже если слово не встречается в названии или описании самого фильма.

### Точный поиск по полю

Префикс `^` ищет только совпадения с начала строки (`startswith` вместо `icontains`), а `=` — точное совпадение:

```python
search_fields = ('^title', 'description')
```

---

## list_filter — боковая панель фильтров

`list_filter` добавляет панель справа от списка с готовыми фильтрами по значению поля:

```python
@admin.register(Film)
class FilmAdmin(admin.ModelAdmin):
    list_display = ('title', 'year', 'rating', 'director')
    search_fields = ('title', 'description', 'director__name')
    list_filter = ('year', 'genres')
```

Для `ForeignKey` и `ManyToManyField` Django автоматически строит список всех связанных объектов с возможностью выбрать один или несколько. Для `BooleanField` — фильтр «Да / Нет / Все». Для `DateField` и `DateTimeField` — готовые интервалы: сегодня, последние 7 дней, этот месяц, этот год.

### Фильтр по диапазону дат

Если в модель добавить `DateField` (например, `release_date`), `list_filter` сразу предложит готовый виджет с интервалами:

```python
list_filter = ('year', 'genres', 'created_at')
```

---

## Вычисляемые колонки

В прошлом уроке мы оставили вопрос открытым: `genres` как ManyToManyField нельзя поставить в `list_display` напрямую. Решение — написать метод, который возвращает строковое представление коллекции.

### Метод на классе ModelAdmin

```python
@admin.register(Film)
class FilmAdmin(admin.ModelAdmin):
    list_display = ('title', 'year', 'rating', 'director', 'genre_list')
    search_fields = ('title', 'description', 'director__name')
    list_filter = ('year', 'genres')

    @admin.display(description='Жанры')
    def genre_list(self, obj):
        return ', '.join(genre.name for genre in obj.genres.all())
```

Декоратор `@admin.display(description='Жанры')` задаёт человекочитаемое имя заголовка колонки — без него Django покажет техническое имя метода `genre_list`.

Метод принимает `obj` — это конкретный объект `Film` из текущей строки списка. Внутри можно обращаться к любым полям и связям объекта, как в обычном Python-коде.

### Метод можно определить и на самой модели

Если вычисляемое значение нужно не только в админке, но и в шаблонах — логичнее определить метод на модели, а не на `ModelAdmin`:

```python
# films/models.py
class Film(models.Model):
    # ... поля ...

    def genre_list(self):
        return ', '.join(genre.name for genre in self.genres.all())
    genre_list.short_description = 'Жанры'
```

```python
# films/admin.py
@admin.register(Film)
class FilmAdmin(admin.ModelAdmin):
    list_display = ('title', 'year', 'rating', 'director', 'genre_list')
```

Оба подхода рабочие. Правило простое: если значение нужно только в админке — пиши метод на `ModelAdmin`. Если нужно где-то ещё (шаблоны, API) — пиши на модели.

### Цветные индикаторы через format_html

Можно выводить не просто текст, а HTML — например, цветную метку для рейтинга:

```python
from django.utils.html import format_html


@admin.register(Film)
class FilmAdmin(admin.ModelAdmin):
    list_display = ('title', 'year', 'rating_badge', 'director', 'genre_list')

    @admin.display(description='Рейтинг')
    def rating_badge(self, obj):
        if obj.rating >= 8:
            color = 'green'
        elif obj.rating >= 5:
            color = 'orange'
        else:
            color = 'red'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.rating
        )
```

`format_html()` обязателен здесь — это безопасный способ вставить HTML с подстановкой значений, защищённый от XSS. Использовать обычное форматирование строк (`f-string`) для построения HTML в Django — небезопасно, потому что значения не экранируются.

---

## Пользовательские действия (actions)

Действия — это операции, которые применяются сразу к нескольким выбранным объектам в списке. Django предоставляет одно действие по умолчанию — массовое удаление. Добавим собственные.

### Простое действие: сброс рейтинга

```python
# films/admin.py
@admin.register(Film)
class FilmAdmin(admin.ModelAdmin):
    list_display = ('title', 'year', 'rating_badge', 'director', 'genre_list')
    actions = ['reset_rating']

    @admin.action(description='Сбросить рейтинг выбранных фильмов')
    def reset_rating(self, request, queryset):
        updated_count = queryset.update(rating=0.0)
        self.message_user(request, f'Рейтинг сброшен у {updated_count} фильмов.')
```

Разберём сигнатуру метода действия:

- `self` — экземпляр `FilmAdmin`
- `request` — объект запроса, как в обычном представлении
- `queryset` — QuerySet из выбранных в списке объектов

`queryset.update()` — тот самый метод массового обновления из урока 9. Использование `update()` здесь особенно уместно: операция применяется к множеству объектов одним SQL-запросом.

`self.message_user()` показывает уведомление администратору после выполнения действия — зелёное сообщение наверху страницы.

### Действие с условной логикой

```python
@admin.action(description='Отметить как высокорейтинговые (8.0+)')
def mark_high_rated(self, request, queryset):
    updated_count = queryset.filter(rating__lt=8.0).update(rating=8.0)
    if updated_count:
        self.message_user(request, f'Обновлено {updated_count} фильмов.')
    else:
        self.message_user(request, 'Все выбранные фильмы уже имели рейтинг 8.0+', level='warning')
```

`message_user()` принимает параметр `level` — `'info'`, `'success'`, `'warning'`, `'error'` — для разных цветов уведомления.

### Применение action в нашем проекте — массовая привязка жанра

Более практичный пример для нашего каталога: быстро присвоить выбранным фильмам жанр «Классика».

```python
@admin.action(description='Добавить жанр «Классика»')
def add_classic_genre(self, request, queryset):
    classic_genre, created = Genre.objects.get_or_create(
        name='Классика',
        defaults={'slug': 'klassika'}
    )
    for film in queryset:
        film.genres.add(classic_genre)
    self.message_user(request, f'Жанр «Классика» добавлен к {queryset.count()} фильмам.')
```

Здесь используем `get_or_create()` из урока 9 — гарантируем, что жанр существует, прежде чем привязывать его к фильмам.

Обрати внимание: для ManyToMany нельзя использовать `queryset.update()` — связь меняется через `film.genres.add()` для каждого объекта отдельно, поскольку это отдельная промежуточная таблица, а не колонка в самой модели `Film`.

---

## Подводные камни

### list_filter и производительность

Каждый фильтр в `list_filter` для `ForeignKey`/`ManyToManyField` выполняет отдельный запрос, чтобы построить список значений для боковой панели. Если связанных объектов очень много (тысячи режиссёров), это может замедлить страницу. Решение для больших справочников — `autocomplete_fields`, разберём в следующем уроке при настройке форм редактирования.

### search_fields и ManyToManyField

Поиск по `ManyToManyField` через `__` работает, но может создавать дублирующиеся строки в результатах поиска по той же причине, что и обычная фильтрация через M2M — JOIN с промежуточной таблицей умножает строки:

```python
search_fields = ('title', 'genres__name')
```

Django admin сам добавляет `distinct()` к результатам поиска, если в `search_fields` присутствует related-поле — это уже решено внутри Django, в отличие от собственных ORM-запросов, где `distinct()` нужно ставить вручную.

### Действия и большие QuerySet

Если действие применяется к тысячам объектов одновременно, цикл `for film in queryset` (как в примере с жанром «Классика») может быть медленным — каждая итерация это отдельная операция с промежуточной таблицей. Для действительно больших объёмов данных стоит рассмотреть `bulk_create()` для промежуточной модели напрямую, но для учебного проекта и большинства реальных кейсов этот уровень оптимизации избыточен.

---

## Итоговый admin.py

```python
# films/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import Film, Genre, Director, Actor, FilmStats


@admin.register(Film)
class FilmAdmin(admin.ModelAdmin):
    list_display = ('title', 'year', 'rating_badge', 'director', 'genre_list')
    list_display_links = ('title',)
    search_fields = ('title', 'description', 'director__name')
    list_filter = ('year', 'genres')
    list_per_page = 20
    empty_value_display = '— не указано —'
    actions = ['reset_rating', 'add_classic_genre']

    @admin.display(description='Рейтинг')
    def rating_badge(self, obj):
        if obj.rating >= 8:
            color = 'green'
        elif obj.rating >= 5:
            color = 'orange'
        else:
            color = 'red'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.rating
        )

    @admin.display(description='Жанры')
    def genre_list(self, obj):
        return ', '.join(genre.name for genre in obj.genres.all())

    @admin.action(description='Сбросить рейтинг выбранных фильмов')
    def reset_rating(self, request, queryset):
        updated_count = queryset.update(rating=0.0)
        self.message_user(request, f'Рейтинг сброшен у {updated_count} фильмов.')

    @admin.action(description='Добавить жанр «Классика»')
    def add_classic_genre(self, request, queryset):
        classic_genre, _ = Genre.objects.get_or_create(
            name='Классика', defaults={'slug': 'klassika'}
        )
        for film in queryset:
            film.genres.add(classic_genre)
        self.message_user(request, f'Жанр «Классика» добавлен к {queryset.count()} фильмам.')


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name',)


@admin.register(Director)
class DirectorAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name',)


@admin.register(Actor)
class ActorAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(FilmStats)
class FilmStatsAdmin(admin.ModelAdmin):
    list_display = ('film', 'views_count', 'likes_count')
```

---

## Вопросы для проверки

1. По какому принципу Django ищет совпадения в `search_fields`, если указано несколько полей?
2. Зачем использовать `format_html()` вместо обычной f-строки при построении HTML в методе `list_display`?
3. Какие три аргумента принимает метод пользовательского действия (`action`) и что содержит каждый из них?
4. Почему для обновления ManyToManyField внутри действия нельзя использовать `queryset.update()`, как для обычных полей?
5. Что произойдёт, если добавить `ManyToManyField` напрямую в `search_fields`? Нужно ли вручную добавлять `distinct()`?

---

## Практическая задача

**Тип: расширь проект**

Добавь в `DirectorAdmin` инструменты поиска и вычисляемую колонку.

**Требования:**

1. Добавь `search_fields` для поиска по имени режиссёра
2. Добавь вычисляемый метод `film_count`, который показывает количество фильмов режиссёра в каталоге (используй `obj.films.count()`), с описанием колонки `'Количество фильмов'`
3. Включи `film_count` в `list_display`
4. Добавь пользовательское действие `clear_bio`, которое очищает поле `bio` (биографию) у выбранных режиссёров, и выводит сообщение о количестве обновлённых записей

---

[Предыдущий урок](lesson13.md) | [Следующий урок](lesson15.md)