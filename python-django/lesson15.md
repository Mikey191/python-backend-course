# Урок 15. Настройка формы редактирования. Inline-модели. Внешний вид админки

## Последний рубеж настройки админки

Мы настроили список объектов — колонки, поиск, фильтры, действия. Осталась форма редактирования отдельной записи. По умолчанию Django показывает все поля модели подряд, без группировки. Сегодня приводим эту форму в порядок и добавляем возможность редактировать связанные модели прямо на той же странице.

---

## fields и fieldsets — структура формы

### fields — простой контроль набора и порядка полей

`fields` определяет, какие поля показывать в форме и в каком порядке:

```python
# films/admin.py
@admin.register(Film)
class FilmAdmin(admin.ModelAdmin):
    list_display = ('title', 'year', 'rating_badge', 'director', 'genre_list')
    fields = ('title', 'slug', 'year', 'director', 'genres', 'actors', 'description', 'rating')
```

Без явного указания `fields` Django показывает все редактируемые поля модели в порядке их объявления в классе.

### fieldsets — группировка полей с заголовками

`fieldsets` — более мощный инструмент: разбивает форму на визуальные секции с заголовками, можно сворачивать группы и задавать дополнительные CSS-классы:

```python
@admin.register(Film)
class FilmAdmin(admin.ModelAdmin):
    list_display = ('title', 'year', 'rating_badge', 'director', 'genre_list')

    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'slug', 'year', 'description')
        }),
        ('Участники', {
            'fields': ('director', 'genres', 'actors')
        }),
        ('Рейтинг', {
            'fields': ('rating',),
            'classes': ('collapse',),
        }),
    )
```

Структура `fieldsets` — это список кортежей. Первый элемент кортежа — заголовок секции (или `None` без заголовка), второй — словарь с настройками: `fields` обязателен, `classes` — опциональный список CSS-классов.

Класс `'collapse'` сворачивает секцию по умолчанию — пользователь должен кликнуть, чтобы её развернуть. Удобно для редко используемых полей.

> **Важно:** `fields` и `fieldsets` взаимоисключающие — указывается либо одно, либо другое, не оба одновременно.

---

## readonly_fields — поля только для просмотра

Некоторые поля не должны редактироваться вручную — например, `created_at` со значением `auto_now_add=True`. Django технически не даст его редактировать в форме, но по умолчанию такое поле просто не показывается. Если нужно показать его, но без возможности изменить — используем `readonly_fields`:

```python
@admin.register(Film)
class FilmAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'slug', 'year', 'description')
        }),
        ('Участники', {
            'fields': ('director', 'genres', 'actors')
        }),
        ('Системная информация', {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )
    readonly_fields = ('created_at',)
```

`readonly_fields` также принимает методы — это удобно для отображения вычисляемых значений прямо в форме редактирования:

```python
@admin.register(Film)
class FilmAdmin(admin.ModelAdmin):
    readonly_fields = ('created_at', 'views_summary')

    @admin.display(description='Статистика просмотров')
    def views_summary(self, obj):
        if hasattr(obj, 'stats'):
            return f'{obj.stats.views_count} просмотров, {obj.stats.likes_count} лайков'
        return 'Статистика не собрана'
```

---

## prepopulated_fields — автозаполнение slug в форме

В уроке 12 мы настроили автогенерацию slug на уровне модели через `save()`. Это работает, но администратор не видит slug до сохранения формы. `prepopulated_fields` решает это на уровне интерфейса — slug заполняется JavaScript'ом прямо в браузере, по мере того как печатается название:

```python
@admin.register(Film)
class FilmAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('title',)}
```

Теперь при создании нового фильма поле `slug` автоматически предлагает значение, как только администратор начинает печатать в поле `title` — без перезагрузки страницы. Наша логика в `save()` остаётся как защитный механизм на случай прямого создания объекта через код или API, минуя форму админки.

---

## autocomplete_fields — удобный выбор связанных объектов

В прошлом уроке мы упоминали проблему: если справочник (например, режиссёров) большой, обычный выпадающий список в форме становится неудобным — он рендерит все объекты сразу. `autocomplete_fields` заменяет выпадающий список на поле с поиском, которое подгружает варианты по мере набора текста через AJAX:

```python
@admin.register(Film)
class FilmAdmin(admin.ModelAdmin):
    autocomplete_fields = ('director', 'genres', 'actors')
```

Чтобы `autocomplete_fields` заработал, модель, на которую ссылается поле, должна иметь свой `ModelAdmin` с заполненным `search_fields` — Django использует его для поиска. У нас это уже сделано в прошлом уроке для `Director`, `Genre` и `Actor`.

```python
@admin.register(Director)
class DirectorAdmin(admin.ModelAdmin):
    search_fields = ('name',)  # обязательно для работы autocomplete_fields
```

Без `search_fields` на связанной модели Django выбросит ошибку при старте сервера — это явное и понятное сообщение, а не тихий сбой.

---

## Inline-модели — редактирование связанных объектов на одной странице

Inline — это механизм, который позволяет редактировать связанные объекты прямо на странице родительской модели, без перехода на отдельную форму.

Для нашего проекта хороший пример — модель `FilmStats`, связанная с `Film` через `OneToOneField` (мы создали её в уроке 10). Логично редактировать статистику прямо на странице фильма, а не искать её отдельно в разделе «Film stats».

### TabularInline — компактная табличная форма

```python
# films/admin.py
class FilmStatsInline(admin.TabularInline):
    model = FilmStats
    extra = 0  # не показывать пустые формы для добавления новых записей


@admin.register(Film)
class FilmAdmin(admin.ModelAdmin):
    list_display = ('title', 'year', 'rating_badge', 'director', 'genre_list')
    inlines = [FilmStatsInline]
```

`extra` определяет количество пустых форм для добавления новых записей, показываемых по умолчанию. Для `OneToOneField` логично поставить `0` или `1` — у фильма может быть только одна запись статистики.

### StackedInline — развёрнутая форма

`StackedInline` показывает каждое поле на отдельной строке, а не в виде компактной таблицы — подходит, когда полей много и таблица была бы слишком тесной:

```python
class FilmStatsInline(admin.StackedInline):
    model = FilmStats
    extra = 0
```

Выбор между `TabularInline` и `StackedInline` — вопрос удобства: мало полей и нужна компактность — табличный вид; много полей или они длинные — развёрнутый.

### Inline для ManyToMany — через промежуточную модель

Стандартный `ManyToManyField` (как `genres` и `actors`) Django admin показывает как обычный multiple-select виджет в форме — для этого inline не нужен. Inline для M2M требуется только тогда, когда связь имеет дополнительные поля через параметр `through`, который мы кратко упоминали в уроке 10. Для нашего текущего проекта это не нужно, но важно знать о существовании такого паттерна — он часто встречается в более сложных моделях данных.

---

## Внешний вид: site_header, site_title, index_title

Можно изменить заголовки и название самой админ-панели — это настраивается не в `admin.py` приложения, а в корневом `urls.py` или в отдельном модуле конфигурации:

```python
# filmsite/urls.py
from django.contrib import admin

admin.site.site_header = 'Управление каталогом фильмов'
admin.site.site_title = 'Админка — Сайт фильмов'
admin.site.index_title = 'Панель администратора'

urlpatterns = [
    path('admin/', admin.site.urls),
    # ...
]
```

- `site_header` — заголовок наверху каждой страницы админки
- `site_title` — заголовок вкладки браузера (`<title>`)
- `index_title` — заголовок главной страницы админки

### Кастомизация через собственный CSS

Для более глубокой кастомизации внешнего вида (цвета, логотип) Django позволяет переопределить шаблоны админки или подключить собственный CSS через `Media`-класс:

```python
@admin.register(Film)
class FilmAdmin(admin.ModelAdmin):
    class Media:
        css = {
            'all': ('films/css/admin_custom.css',)
        }
```

Файл ищется по тем же правилам, что обычные статические файлы приложения — `films/static/films/css/admin_custom.css`. Глубокая кастомизация внешнего вида — отдельная большая тема, выходящая за рамки базового курса; для большинства проектов перечисленных настроек более чем достаточно.

---

## Подводные камни

### prepopulated_fields работает только в форме, не при программном создании

JavaScript-автозаполнение `prepopulated_fields` срабатывает только при создании объекта через форму в браузере. Если фильм создаётся в коде (`Film.objects.create(...)`) или через shell — slug всё равно генерируется через метод `save()`, который мы написали в уроке 12. Это разные механизмы для разных сценариев, и важно, чтобы оба работали независимо.

### Inline и on_delete

Если у `FilmStatsInline` установлен `extra = 0`, а статистика для фильма ещё не создана — секция будет показывать пустую форму для добавления одной записи. Это ожидаемое поведение для `OneToOneField`: Django не может показать несуществующий объект, но позволяет создать его сразу здесь же.

### autocomplete_fields без search_fields на связанной модели

Частая ошибка при добавлении `autocomplete_fields` — забыть, что связанная модель должна иметь собственную регистрацию в админке с `search_fields`. Без этого Django выбросит `ImproperlyConfigured` при старте сервера с понятным сообщением, какую модель нужно донастроить.

---

## Итоговый admin.py

```python
# films/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import Film, Genre, Director, Actor, FilmStats


class FilmStatsInline(admin.TabularInline):
    model = FilmStats
    extra = 0


@admin.register(Film)
class FilmAdmin(admin.ModelAdmin):
    list_display = ('title', 'year', 'rating_badge', 'director', 'genre_list')
    list_display_links = ('title',)
    search_fields = ('title', 'description', 'director__name')
    list_filter = ('year', 'genres')
    list_per_page = 20
    empty_value_display = '— не указано —'
    actions = ['reset_rating', 'add_classic_genre']

    prepopulated_fields = {'slug': ('title',)}
    autocomplete_fields = ('director', 'genres', 'actors')
    readonly_fields = ('created_at',)
    inlines = [FilmStatsInline]

    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'slug', 'year', 'description')
        }),
        ('Участники', {
            'fields': ('director', 'genres', 'actors')
        }),
        ('Рейтинг', {
            'fields': ('rating',),
            'classes': ('collapse',),
        }),
        ('Системная информация', {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )

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
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Director)
class DirectorAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'film_count')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    actions = ['clear_bio']

    @admin.display(description='Количество фильмов')
    def film_count(self, obj):
        return obj.films.count()

    @admin.action(description='Очистить биографию выбранных режиссёров')
    def clear_bio(self, request, queryset):
        updated_count = queryset.update(bio='')
        self.message_user(request, f'Биография очищена у {updated_count} режиссёров.')


@admin.register(Actor)
class ActorAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(FilmStats)
class FilmStatsAdmin(admin.ModelAdmin):
    list_display = ('film', 'views_count', 'likes_count')
```

```python
# filmsite/urls.py
from django.contrib import admin
from django.urls import path, include

admin.site.site_header = 'Управление каталогом фильмов'
admin.site.site_title = 'Админка — Сайт фильмов'
admin.site.index_title = 'Панель администратора'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('films.urls')),
]
```

---

## Вопросы

1. В чём разница между `fields` и `fieldsets`? Можно ли использовать оба одновременно?
2. Зачем нужен `prepopulated_fields`, если slug уже генерируется автоматически в методе `save()` модели?
3. Что должно быть настроено на связанной модели, чтобы `autocomplete_fields` сработал для поля, ссылающегося на неё?
4. Когда лучше использовать `TabularInline`, а когда `StackedInline`?
5. Почему модель, связанная через `ManyToManyField` без параметра `through`, не требует Inline для редактирования?

---

## Практическая задача

**Тип: расширь проект**

Настрой форму редактирования модели `Director`.

**Требования:**

1. Раздели форму на две секции через `fieldsets`: «Основная информация» (поля `name`, `slug`) и «Дополнительно» (поля `bio`, `photo`), вторую секцию сделай свёрнутой по умолчанию
2. Добавь `prepopulated_fields`, чтобы slug автоматически предлагался на основе поля `name` (это уже должно быть сделано из прошлого решения — проверь и перенеси в `fieldsets`, если нужно)
3. Добавь `readonly_fields` с методом `films_preview`, который показывает список названий всех фильмов режиссёра через запятую (можно переиспользовать логику, похожую на `genre_list` из `FilmAdmin`)
4. Включи `films_preview` в секцию «Дополнительно»

---

[Предыдущий урок](lesson14.md) | [Следующий урок](lesson16.md)