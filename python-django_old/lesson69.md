# Модуль 10. Урок 69. Настройка Django, Gunicorn и Nginx для отображения страниц сайта

На предыдущих занятиях мы сделали всю «черновую» работу:

* развернули сервер;
* подключились к нему по SSH;
* перенесли код проекта **cinemahub**;
* установили зависимости;
* (опционально) подготовили базу данных.

Теперь мы подошли к самому важному моменту — **настройке связки Django → Gunicorn → Nginx**, благодаря которой страницы сайта станут доступны по доменному имени в браузере.

---

## Шаг 1. Подготовка Django-проекта к работе на сервере

Начинаем с настройки Django.
Все изменения мы будем вносить в файл:

```
cinemahub/settings.py
```

(путь указывайте относительно корня проекта, где лежит `manage.py`).

---

### Подключение модуля os

В самом начале файла `settings.py` добавьте импорт:

```python
import os
```

Он понадобится для работы с путями и статическими файлами.

---

### Настройка ALLOWED_HOSTS

По умолчанию Django **блокирует все внешние запросы**.
Это защита от случайного запуска проекта в продакшене.

Найдите в `settings.py` переменную `ALLOWED_HOSTS` и укажите ваш домен:

```python
ALLOWED_HOSTS = [
    'cinemahub.ru',
    'www.cinemahub.ru',
]
```

Если этого не сделать, при открытии сайта вы получите ошибку **DisallowedHost**.

---

### INTERNAL_IPS

Если в файле есть строка:

```python
INTERNAL_IPS = ["127.0.0.1"]
```

— закомментируйте её, так как она используется для отладки.

---

## Шаг 2. Настройка базы данных (ДВА ВАРИАНТА)

Здесь мы делаем важную методическую развилку.

---

### Вариант 1. PostgreSQL (если вы его используете)

В `settings.py` настройка будет выглядеть так:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'cinemahub_db',
        'USER': 'cinemahub_user',
        'PASSWORD': 'strong_password_here',
        'HOST': 'localhost',
        'PORT': '',
    }
}
```

Этот вариант актуален, если вы **осознанно решили перейти на PostgreSQL**.

---

### Вариант 2. SQLite (рекомендуется для текущего курса)

Если студенты **работали только с SQLite**, то **ничего менять не нужно**.

Оставляем стандартную конфигурацию:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

> В этом случае база данных — это файл `db.sqlite3` внутри проекта.

> Django работает с ним **точно так же**, как локально.

---

## Шаг 3. Настройка статических файлов

В `settings.py` добавьте:

```python
STATIC_ROOT = os.path.join(BASE_DIR, 'static/')
```

А если есть переменная `STATICFILES_DIRS`, **закомментируйте её**:

```python
# STATICFILES_DIRS = [...]
```

Почему так:

* в продакшене все статические файлы должны лежать **в одном месте**;
* Nginx будет забирать их напрямую, без Django.

---

## Шаг 4. Миграции и сбор статических файлов

Теперь применяем изменения.

Из корня проекта выполняем:

```bash
python3 manage.py makemigrations
python3 manage.py migrate
```

Затем собираем статику:

```bash
python3 manage.py collectstatic
```

Django спросит подтверждение — вводим `yes`.

---

### Проверка №1 (важная)

Проверьте, что в проекте появилась папка:

```
static/
```

И внутри неё — CSS, JS и другие файлы.

---

## Шаг 5. Временный запуск Django-сервера

Откроем порт 8000:

```bash
sudo ufw allow 8000
```

Запускаем Django:

```bash
python3 manage.py runserver 0.0.0.0:8000
```

Теперь в браузере открываем:

```
http://ваш_домен:8000
```

---

### Проверка №2

* сайт **открывается**;
* пока может быть пустая главная страница;
* это нормально — сервер доступен, Django работает.

⚠️ Это **тестовый сервер**, он не предназначен для продакшена.

Останавливаем его: `Ctrl + C`.

---

## Шаг 6. Перенос данных (если нужно)

Если вы хотите перенести данные (фильмы, пользователей):

На локальном компьютере:

```bash
python manage.py dumpdata --indent=2 -o db.json
```

Загружаем `db.json` на сервер и выполняем:

```bash
python3 manage.py loaddata db.json
```

После этого:

* появятся записи `movies`;
* появится суперпользователь.

---

## Шаг 7. Переключение Django в боевой режим

В `settings.py`:

```python
DEBUG = False
```

⚠️ Это обязательный шаг перед продакшеном.

---

## Шаг 8. Тестирование Gunicorn

Находясь в виртуальном окружении, выполняем:

```bash
gunicorn --bind 0.0.0.0:8000 cinemahub.wsgi
```

_*Если ваше основное приложение (внутри которого файл `settings.py`) называется, к примеру `core`, то вызвать нужно будет `core.wsgi`_

В браузере снова открываем:

```
http://ваш_домен:8000
```

---

### Проверка №3

* сайт работает;
* **стили не загружаются** — это ожидаемо;
* Gunicorn работает корректно.

Останавливаем сервер (`Ctrl + C`) и выходим из окружения:

```bash
deactivate
```

---

## Шаг 9. Настройка Gunicorn как systemd-сервиса

Создаём файл сервиса:

```bash
sudo vim /etc/systemd/system/gunicorn.service
```

Содержимое файла:

```ini
[Unit]
Description=gunicorn daemon for cinemahub
After=network.target

[Service]
User=root
Group=www-data
WorkingDirectory=/var/www/cinemahub
ExecStart=/var/www/cinemahub/venv/bin/gunicorn \
    --workers 3 \
    --bind unix:/var/www/cinemahub/cinemahub.sock \
    cinemahub.wsgi:application
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

_*Что бы сохранить файл в `vim` нужно написать команду `:wq` и нажать `enter`_

_*Если ваше основное приложение (внутри которого файл `settings.py`) называется, к примеру `core`, то в файле нужно будет прописать `core.wsgi:application` вместо `cinemahub.wsgi:application`_

Запускаем сервис:

```bash
sudo systemctl enable --now gunicorn
sudo systemctl status gunicorn
```

---

### Проверка №4

* статус **active (running)**;
* в каталоге проекта появился файл:

  ```
  cinemahub.sock
  ```

---

## Шаг 10. Настройка Nginx

Создаём конфигурацию:

```bash
sudo vim /etc/nginx/sites-available/cinemahub

или

sudo nano /etc/nginx/sites-available/cinemahub
```

Содержимое:

```nginx
server {
    listen 80;
    server_name cinemahub.ru *.cinemahub.ru;

    location = /favicon.ico { access_log off; log_not_found off; }
    location /static/ { root /var/www/cinemahub; }
    location /media/ { root /var/www/cinemahub; }

    location / {
        include proxy_params;
        proxy_pass http://unix:/var/www/cinemahub/cinemahub.sock;
    }
}
```

Активируем конфигурацию:

```bash
sudo ln -s /etc/nginx/sites-available/cinemahub /etc/nginx/sites-enabled
```

Проверяем:

```bash
sudo nginx -t
sudo systemctl restart nginx
sudo systemctl restart gunicorn
```

---

## Шаг 11. Firewall и финальная проверка

Закрываем порт 8000:

```bash
sudo ufw delete allow 8000
sudo ufw allow 'Nginx Full'
```

Открываем в браузере:

```
http://cinemahub.ru
```

---

### Если не загружаются стили

Устанавливаем права:

```bash
sudo chmod 755 /var/www/cinemahub/static
sudo chmod 755 /var/www/cinemahub/media
```

---

[Предыдущий урок](lesson68.md) | [Следующий урок](lesson70.md)