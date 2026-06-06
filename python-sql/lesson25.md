# Урок 25. Миграции — Alembic

## Почему миграции необходимы

Представьте: вы написали приложение, задеплоили его на сервер, база данных заполнена реальными данными пользователей. Через месяц приходит задача — добавить в таблицу `products` новый столбец `description`.

Что происходит без миграций:

```python
# Вы обновили модель
class Product(Base):
    __tablename__ = 'products'
    id          = Column(Integer, primary_key=True)
    name        = Column(String)
    price       = Column(Float)
    description = Column(Text)    # ← добавили
```

Но в реальной базе данных на сервере столбца `description` нет. Приложение падает с ошибкой при первом же запросе к этому полю. Можно запустить `Base.metadata.create_all(engine)` — но он создаёт только **новые** таблицы, существующие не трогает. Значит `description` не появится.

Без миграций есть только плохие варианты:
- Написать `ALTER TABLE products ADD COLUMN description TEXT` вручную прямо на боевом сервере — риск ошибки, нет истории изменений
- Удалить базу и создать заново — потеря всех данных

**Миграция** — это файл с инструкциями как перейти от одной версии схемы к другой (и как откатиться назад). История миграций — это полная летопись эволюции вашей базы данных.

---

## Что такое Alembic

**Alembic** — инструмент миграций для SQLAlchemy. Он:
- Сравнивает текущее состояние моделей с состоянием базы данных
- Автоматически генерирует файлы миграций
- Применяет миграции к базе данных
- Умеет откатывать изменения

Установка:

```bash
pip install alembic
```

---

## Структура проекта перед началом

Для урока будем работать с проектом интернет-магазина. Предположим такую структуру:

```
shop/
├── models.py       ← SQLAlchemy-модели (из Урока 24)
├── database.py     ← create_engine
└── main.py
```

```python
# database.py
from sqlalchemy import create_engine

DATABASE_URL = 'sqlite:///shop.db'
engine = create_engine(DATABASE_URL)
```

```python
# models.py
from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class Category(Base):
    __tablename__ = 'categories'
    id   = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    products = relationship('Product', back_populates='category')


class Product(Base):
    __tablename__ = 'products'
    id          = Column(Integer, primary_key=True, autoincrement=True)
    name        = Column(String(200), nullable=False)
    price       = Column(Float,       nullable=False)
    stock       = Column(Integer,     nullable=False, default=0)
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=False)
    category    = relationship('Category', back_populates='products')
```

---

## Шаг 1. Инициализация Alembic

В папке проекта выполните:

```bash
alembic init alembic
```

Это создаёт папку `alembic/` со служебными файлами:

```
shop/
├── alembic/
│   ├── env.py            ← главный конфиг — здесь подключают модели
│   ├── script.py.mako    ← шаблон для файлов миграций
│   └── versions/         ← сюда будут попадать файлы миграций
│       └── (пусто)
├── alembic.ini           ← конфиг Alembic (строка подключения к БД)
├── models.py
├── database.py
└── main.py
```

---

## Шаг 2. Настройка alembic.ini

Откройте `alembic.ini` и найдите строку:

```ini
sqlalchemy.url = driver://user:pass@localhost/dbname
```

Замените на путь к вашей базе данных:

```ini
sqlalchemy.url = sqlite:///shop.db
```

Для PostgreSQL это выглядело бы как:
```ini
sqlalchemy.url = postgresql://user:password@localhost/shop
```

---

## Шаг 3. Настройка env.py

Откройте `alembic/env.py`. Это самый важный файл — он соединяет Alembic с вашими моделями.

Найдите строку:
```python
target_metadata = None
```

Замените её двумя строками:
```python
from models import Base
target_metadata = Base.metadata
```

`target_metadata` — это метаданные ваших моделей. Alembic будет сравнивать их с реальной схемой базы данных чтобы понять что изменилось.

Полный блок в `env.py` после правки выглядит примерно так:

```python
# alembic/env.py (ключевые части)
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# --- Добавляем импорт наших моделей ---
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from models import Base
# --- конец добавленного ---

config = context.config
fileConfig(config.config_file_name)

target_metadata = Base.metadata   # ← вот эта строка
```

`sys.path.insert` — нужен чтобы Python нашёл `models.py` в папке проекта при запуске из папки `alembic/`.

---

## Шаг 4. Первая миграция — создание таблиц

Теперь попросим Alembic сравнить наши модели с базой данных и сгенерировать миграцию:

```bash
alembic revision --autogenerate -m "create initial tables"
```

- `--autogenerate` — автоматически определить что изменилось
- `-m "..."` — сообщение миграции (как commit message в Git)

Alembic создаст файл в `alembic/versions/`:

```
alembic/versions/
└── 3a8f2c1d9e45_create_initial_tables.py
```

Имя файла содержит уникальный хэш — это **revision ID**. Посмотрим что внутри:

```python
# alembic/versions/3a8f2c1d9e45_create_initial_tables.py

"""create initial tables

Revision ID: 3a8f2c1d9e45
Revises:
Create Date: 2024-06-25 10:00:00
"""

from alembic import op
import sqlalchemy as sa

# Идентификатор этой миграции
revision = '3a8f2c1d9e45'
# Идентификатор предыдущей миграции (None — это первая)
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Применить миграцию — что делаем при переходе вперёд."""
    op.create_table(
        'categories',
        sa.Column('id',   sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_table(
        'products',
        sa.Column('id',          sa.Integer(), nullable=False),
        sa.Column('name',        sa.String(length=200), nullable=False),
        sa.Column('price',       sa.Float(), nullable=False),
        sa.Column('stock',       sa.Integer(), nullable=False),
        sa.Column('category_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id']),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    """Откатить миграцию — что делаем при возврате назад."""
    op.drop_table('products')    # в обратном порядке — зависимые первыми
    op.drop_table('categories')
```

Каждый файл миграции содержит две функции:
- `upgrade()` — что сделать при применении миграции
- `downgrade()` — как откатить изменения

Это и есть двусторонность миграций — можно двигаться вперёд и назад.

> **Важно:** всегда просматривайте автогенерированные миграции перед применением. Alembic умный, но не идеальный — иногда он не замечает некоторые изменения (переименование столбцов, изменение значений по умолчанию). Автогенерация — это помощник, не замена внимательности.

---

## Шаг 5. Применение миграции

```bash
alembic upgrade head
```

- `upgrade` — применить миграции
- `head` — до самой последней

В консоли увидите:

```
INFO  [alembic.runtime.migration] Context impl SQLiteImpl.
INFO  [alembic.runtime.migration] Will assume non-transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade  -> 3a8f2c1d9e45, create initial tables
```

Таблицы созданы. Alembic также создаёт в базе данных служебную таблицу `alembic_version` которая хранит хэш последней применённой миграции:

```sql
SELECT * FROM alembic_version;
-- version_num
-- 3a8f2c1d9e45
```

Это позволяет Alembic всегда знать на какой версии находится база данных.

---

## Шаг 6. Изменение схемы — вторая миграция

Пришла задача: добавить в `products` столбец `description`. Меняем модель:

```python
# models.py
class Product(Base):
    __tablename__ = 'products'
    id          = Column(Integer, primary_key=True, autoincrement=True)
    name        = Column(String(200), nullable=False)
    price       = Column(Float,       nullable=False)
    stock       = Column(Integer,     nullable=False, default=0)
    description = Column(String(500), nullable=True)   # ← добавили
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=False)
    category    = relationship('Category', back_populates='products')
```

Генерируем новую миграцию:

```bash
alembic revision --autogenerate -m "add description to products"
```

Alembic сравнивает модели с текущим состоянием базы и видит новый столбец:

```python
# alembic/versions/7b4e1f2a8c33_add_description_to_products.py

revision = '7b4e1f2a8c33'
down_revision = '3a8f2c1d9e45'   # ← предыдущая миграция

def upgrade() -> None:
    op.add_column(
        'products',
        sa.Column('description', sa.String(length=500), nullable=True)
    )

def downgrade() -> None:
    op.drop_column('products', 'description')
```

`down_revision = '3a8f2c1d9e45'` — цепочка. Каждая миграция знает свою предыдущую. Это и есть история изменений.

Применяем:

```bash
alembic upgrade head
```

```
INFO  Running upgrade 3a8f2c1d9e45 -> 7b4e1f2a8c33, add description to products
```

Столбец добавлен в существующую таблицу. Данные в таблице сохранены.

---

## Откат миграции

Нужно вернуться на шаг назад:

```bash
alembic downgrade -1
```

`-1` — откатить одну миграцию. Alembic вызовет `downgrade()` последней применённой миграции:

```
INFO  Running downgrade 7b4e1f2a8c33 -> 3a8f2c1d9e45, add description to products
```

Столбец `description` удалён. База вернулась к состоянию после первой миграции.

Другие варианты отката:

```bash
alembic downgrade -2         # откатить две миграции
alembic downgrade base       # откатить все миграции (пустая база)
alembic upgrade +1           # применить одну следующую
alembic upgrade 3a8f2c1d9e45 # перейти к конкретной миграции по хэшу
```

---

## Просмотр истории и текущего состояния

```bash
# История всех миграций
alembic history

# Текущая версия базы данных
alembic current
```

Вывод `alembic history`:

```
7b4e1f2a8c33 -> (head), add description to products
3a8f2c1d9e45 -> 7b4e1f2a8c33, create initial tables
<base> -> 3a8f2c1d9e45
```

Стрелки показывают цепочку: `base → первая миграция → вторая (head)`.

---

## Миграции и командная работа

Миграции хранятся в папке `alembic/versions/` — их нужно добавлять в Git вместе с кодом. Это и есть история изменений схемы:

```bash
git add alembic/versions/
git commit -m "add migration: add description to products"
```

Когда коллега получает ваши изменения:

```bash
git pull
alembic upgrade head   # применить все новые миграции
```

Его локальная база мгновенно приходит в актуальное состояние.

---

## Типичные ошибки новичков

### 1. Забыть добавить `target_metadata`

Если `target_metadata = None` в `env.py` — Alembic не знает о ваших моделях и сгенерирует пустую миграцию.

### 2. Запустить `create_all` вместо миграций

```python
Base.metadata.create_all(engine)   # создаёт таблицы, но не трогает существующие
```

`create_all` — для начального создания или для тестов. В продакшне — только через Alembic.

### 3. Не проверить автогенерированную миграцию

Alembic не отслеживает переименование столбцов — он видит удаление одного и создание другого. Это потеря данных. Нужно вручную заменить:

```python
# Что Alembic сгенерирует (НЕВЕРНО — удалит данные):
op.drop_column('products', 'old_name')
op.add_column('products', sa.Column('new_name', sa.String()))

# Что нужно написать вручную (ВЕРНО — данные сохранятся):
op.alter_column('products', 'old_name', new_column_name='new_name')
```

### 4. Применять миграции в неправильном порядке

Алembic отслеживает порядок через `down_revision`. Но если два разработчика создали миграции параллельно — возникнет конфликт веток. Это продвинутый сценарий, в учебных проектах не встречается.

### 5. Нельзя редактировать уже применённые файлы миграций

Применённые файлы миграций редактировать **нельзя** — это сломает историю. Alembic сопоставляет файлы миграций с записями в `alembic_version` по хэшам. Если изменить применённый файл — Alembic может запутаться в состоянии базы. 

**Если нужно исправить ошибку в применённой миграции — создаётся новая миграция которая исправляет её последствия**.

---

## Полный рабочий процесс

```
1. Изменить модель в models.py
        ↓
2. alembic revision --autogenerate -m "описание"
        ↓
3. Проверить сгенерированный файл в alembic/versions/
        ↓
4. alembic upgrade head
        ↓
5. git add alembic/versions/ && git commit
```

Это и есть стандартный цикл работы с миграциями в любом Python веб-проекте.

---

В конце материала мы рассмотрим два конкретных вопроса, которые возникают почти в каждом проекте.

1. Добавить столбец который может быть NULL
2. Добавить столбец который не может быть NULL

[Практические миграции](#практические-миграции)

---

## Вопросы

1. Почему `Base.metadata.create_all(engine)` не подходит для обновления существующей базы данных?
2. Что хранится в таблице `alembic_version` и зачем она нужна?
3. Что делают функции `upgrade()` и `downgrade()` в файле миграции?
4. Почему в `down_revision` каждой миграции хранится хэш предыдущей?
5. Что произойдёт если запустить `alembic upgrade head` на базе которая уже обновлена до последней версии?
6. Почему нужно проверять автогенерированные миграции перед применением?
7. Как `alembic downgrade -1` отличается от `alembic downgrade base`?
8. Почему файлы миграций нужно хранить в Git?
9. Что нужно исправить в автогенерированной миграции при переименовании столбца?
10. Можно ли редактировать уже применённые файлы миграций?

---

## Задачи

### **Задача 1.** 

Инициализируйте Alembic в папке проекта с моделями из Урока 24 (`Category`, `Product`). Настройте `alembic.ini` и `env.py`. Сгенерируйте и примените первую миграцию для создания таблиц.

---

### **Задача 2.** 

Добавьте в модель `Product` столбец `description: Column(String(500), nullable=True)`. Сгенерируйте миграцию и примените её. Проверьте через `alembic history` что цепочка миграций выстроена правильно.

---

### **Задача 3.** 

Откатите последнюю миграцию через `alembic downgrade -1`. Убедитесь что столбец `description` исчез (можно проверить через SQLiteStudio или Python). Примените миграцию снова через `alembic upgrade head`.

---

### **Задача 4.** 

Добавьте в проект новую модель `Tag` (id, name UNIQUE) и связь многие-ко-многим с `Product` через таблицу ассоциации `product_tags`. Сгенерируйте и примените миграцию. Убедитесь что Alembic правильно определил все три новые таблицы (или изменения).

---

### **Задача 5.** 

Проверьте поведение `alembic upgrade head` на уже актуальной базе — убедитесь что команда безопасна и не производит лишних изменений. Затем выполните `alembic downgrade base` и снова `alembic upgrade head` — база должна вернуться в полное актуальное состояние.

---

## Практические миграции

<details>
<summary>Раскрыть</summary>

## Что разбираем

В основном уроке мы научились базовому циклу: изменил модель → сгенерировал миграцию → применил. Но реальная работа ставит два конкретных вопроса которые возникают почти в каждом проекте:

1. **Добавить столбец который может быть NULL** — безопасная миграция, данные не затрагиваются
2. **Добавить столбец который не может быть NULL** — здесь есть ловушка, и нужно знать как её обойти

Разберём оба случая на живом проекте с реальными данными в базе.

---

## Проект для практики

Маленький рабочий FastAPI-проект с категориями и товарами. Структура минимальная — ровно столько чтобы API работал и в базе были данные.

```
shop/
├── main.py
├── database.py
├── models.py
├── seed.py
├── routers/
│   └── products.py
└── alembic/
    └── versions/
```

### models.py

```python
# models.py
from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class Category(Base):
    __tablename__ = 'categories'

    id   = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)

    products = relationship('Product', back_populates='category',
                            cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Category {self.name!r}>'


class Product(Base):
    __tablename__ = 'products'

    id          = Column(Integer, primary_key=True, autoincrement=True)
    name        = Column(String(200), nullable=False)
    price       = Column(Float,       nullable=False)
    stock       = Column(Integer,     nullable=False, default=0)
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=False)

    category = relationship('Category', back_populates='products')

    def __repr__(self):
        return f'<Product {self.name!r} price={self.price}>'
```

### database.py

```python
# database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from typing import Generator
from fastapi import Depends

DATABASE_URL = 'sqlite:///shop.db'

engine = create_engine(
    DATABASE_URL,
    connect_args={'check_same_thread': False}
)


def get_db() -> Generator:
    with Session(engine) as session:
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
```

### routers/products.py

```python
# routers/products.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select
from database import get_db
from models import Product

router = APIRouter()


@router.get('/')
def get_products(session: Session = Depends(get_db)):
    products = session.execute(select(Product)).scalars().all()
    return [
        {
            'id':    p.id,
            'name':  p.name,
            'price': p.price,
            'stock': p.stock,
        }
        for p in products
    ]


@router.get('/{product_id}')
def get_product(product_id: int, session: Session = Depends(get_db)):
    product = session.get(Product, product_id)
    if product is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail='Товар не найден')
    return {
        'id':    product.id,
        'name':  product.name,
        'price': product.price,
        'stock': product.stock,
    }
```

### main.py

```python
# main.py
from fastapi import FastAPI
from routers import products

app = FastAPI(title='Shop API — практика миграций')

app.include_router(products.router, prefix='/products', tags=['products'])


@app.get('/health')
def health():
    return {'status': 'ok'}
```

### seed.py

```python
# seed.py
# Заполняем базу данными — чтобы миграции были на живых данных,
# а не на пустой таблице.

from sqlalchemy.orm import Session
from database import engine
from models import Base, Category, Product


def seed():
    # Создаём таблицы (первый запуск)
    Base.metadata.create_all(engine)

    with Session(engine) as session:

        # Очищаем перед заполнением
        session.query(Product).delete()
        session.query(Category).delete()
        session.commit()

        # Категории
        electronics = Category(name='Электроника')
        books       = Category(name='Книги')
        periphery   = Category(name='Периферия')

        session.add_all([electronics, books, periphery])
        session.flush()   # нужны id для товаров

        # Товары
        products = [
            Product(name='Ноутбук Lenovo',      price=75000, stock=12, category_id=electronics.id),
            Product(name='Смартфон Samsung',     price=45000, stock=25, category_id=electronics.id),
            Product(name='Наушники Sony',        price=28000, stock=15, category_id=electronics.id),
            Product(name='Мышь Logitech',        price=5500,  stock=50, category_id=periphery.id),
            Product(name='Клавиатура Keychron',  price=8900,  stock=20, category_id=periphery.id),
            Product(name='Чистый код. Мартин',   price=1200,  stock=100, category_id=books.id),
            Product(name='Грокаем алгоритмы',    price=1100,  stock=90,  category_id=books.id),
        ]

        session.add_all(products)
        session.commit()

    print(f'Заполнено: 3 категории, {len(products)} товаров')


if __name__ == '__main__':
    seed()
```

### Запуск проекта

```bash
# 1. Инициализировать Alembic (если ещё не сделано)
alembic init alembic

# alembic.ini:
# sqlalchemy.url = sqlite:///shop.db

# alembic/env.py — добавить:
# import sys, os
# sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# from models import Base
# target_metadata = Base.metadata

# 2. Создать таблицы и заполнить данными
python seed.py

# 3. Зафиксировать начальное состояние в Alembic
alembic stamp head
# stamp head — говорит Alembic "считай что текущее состояние БД
# соответствует последней миграции" без выполнения SQL.
# Нужно когда таблицы уже созданы не через Alembic а через create_all.

# 4. Запустить API
uvicorn main:app --reload
```

> **Важно про `alembic stamp head`:** мы создали таблицы через `seed.py` используя `Base.metadata.create_all()`. Alembic об этом не знает — таблица `alembic_version` пустая. `stamp head` синхронизирует Alembic с реальностью: "да, база уже в актуальном состоянии". Без этого `alembic upgrade head` попытается создать таблицы заново и упадёт с ошибкой.

Убедитесь что API работает: `GET /products` должен вернуть 7 товаров.

---

## Ситуация 1. Добавить столбец который может быть NULL

**Задача:** добавить к товарам поле `description` — описание товара. Поле необязательное: у новых товаров будет описание, у старых — нет (NULL). Существующие данные не должны измениться.

Это **безопасная миграция** — NULL разрешён, поэтому все существующие строки просто получат NULL в новом столбце. Никаких дополнительных действий не нужно.

### Шаг 1. Добавить поле в модель

```python
# models.py — добавить в класс Product:
class Product(Base):
    __tablename__ = 'products'

    id          = Column(Integer, primary_key=True, autoincrement=True)
    name        = Column(String(200), nullable=False)
    price       = Column(Float,       nullable=False)
    stock       = Column(Integer,     nullable=False, default=0)
    description = Column(String(500), nullable=True)   # ← новое поле
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=False)

    category = relationship('Category', back_populates='products')
```

### Шаг 2. Сгенерировать миграцию

```bash
alembic revision --autogenerate -m "add description to products"
```

Alembic сравнил модель с текущей схемой и увидел новый столбец. Открываем сгенерированный файл — убеждаемся что там именно то что ожидали:

```python
def upgrade() -> None:
    op.add_column('products',
        sa.Column('description', sa.String(length=500), nullable=True)
    )

def downgrade() -> None:
    op.drop_column('products', 'description')
```

Всё корректно. `nullable=True` — существующие строки получат NULL.

### Шаг 3. Применить миграцию

```bash
alembic upgrade head
```

```
INFO  Running upgrade abc123 -> def456, add description to products
```

### Шаг 4. Проверить результат

```python
# check.py — быстрая проверка
from sqlalchemy.orm import Session
from sqlalchemy import select
from database import engine
from models import Product

with Session(engine) as session:
    products = session.execute(select(Product)).scalars().all()
    for p in products:
        print(f'{p.name}: description={p.description!r}')
```

```
Ноутбук Lenovo: description=None
Смартфон Samsung: description=None
Мышь Logitech: description=None
...
```

Все существующие товары получили `None` (NULL) в новом поле. Данные не потеряны, API продолжает работать.

### Шаг 5. Обновить роутер

Теперь можно добавить `description` в ответ:

```python
# routers/products.py — обновить get_product:
return {
    'id':          product.id,
    'name':        product.name,
    'price':       product.price,
    'stock':       product.stock,
    'description': product.description,   # ← добавили
}
```

**Итог:** безопасная миграция прошла без единой проблемы. Для nullable-полей это стандартная операция.

---

## Ситуация 2. Добавить столбец который не может быть NULL

**Задача:** добавить к товарам поле `sku` — артикул товара (уникальный код). Поле обязательное: каждый товар должен иметь артикул. `nullable=False`, `unique=True`.

Это **проблемная миграция**. Поймём почему.

### Почему это проблема

В базе уже есть 7 товаров. Если добавить столбец `sku NOT NULL` — база данных спросит: "а какое значение поставить в этот столбец для уже существующих строк?". Ответа нет — вы же не придумали артикулы заранее. База откажет с ошибкой.

Именно здесь автогенерированная миграция вас подведёт если вы её не проверите.

### Неправильный путь — что сделает Alembic

Добавим поле в модель наивно:

```python
# ПОКА НЕ ДЕЛАЙТЕ ТАК — смотрим что произойдёт
sku = Column(String(50), nullable=False, unique=True)
```

```bash
alembic revision --autogenerate -m "add sku to products"
```

Alembic сгенерирует:

```python
def upgrade() -> None:
    op.add_column('products',
        sa.Column('sku', sa.String(length=50), nullable=False)  # ← проблема здесь
    )
    op.create_unique_constraint('uq_products_sku', 'products', ['sku'])
```

Применяем:

```bash
alembic upgrade head
```

```
sqlalchemy.exc.OperationalError: (sqlite3.OperationalError)
Cannot add a NOT NULL column with default value NULL
```

Именно эта ошибка. SQLite (и другие СУБД) не могут добавить `NOT NULL` столбец к таблице с данными если нет значения по умолчанию для существующих строк.

### Правильный путь — трёхшаговая миграция

Стратегия: **сначала добавить столбец как nullable, заполнить данные, потом сделать NOT NULL**.

#### Шаг 1. Модель — добавить поле как nullable

```python
# models.py — временно nullable=True
class Product(Base):
    __tablename__ = 'products'

    id          = Column(Integer, primary_key=True, autoincrement=True)
    name        = Column(String(200), nullable=False)
    price       = Column(Float,       nullable=False)
    stock       = Column(Integer,     nullable=False, default=0)
    description = Column(String(500), nullable=True)
    sku         = Column(String(50),  nullable=True, unique=True)   # ← пока nullable
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=False)

    category = relationship('Category', back_populates='products')
```

#### Шаг 2. Сгенерировать миграцию — и отредактировать её

```bash
alembic revision --autogenerate -m "add sku to products"
```

Alembic сгенерирует добавление nullable-столбца. Открываем файл и **дописываем** заполнение данных вручную:

**Редактирование миграции для SQLite**:

Проблема при работе с SQLite: она умеет обрабатывать очень мало операций через `ALTER TABLE`.

SQLite не может:

* менять nullable
* менять тип столбца
* добавлять уникальные ограничения через ALTER TABLE
* удалять ограничения

SQLite не поддерживает:

* ALTER TABLE table_name ALTER COLUMN ...
* ALTER TABLE table_name DROP COLUMN ...
* ALTER TABLE table_name ADD CONSTRAINT ...

Миграции, которые отлично работают в PostgreSQL или MySQL, на SQLite часто ломаются.

Для корректной миграции нам нужно сделать обходной путь без использования не поддерживаемых операций с `ALTER TABLE`.

```python
def upgrade() -> None:
    # 1. Добавляем nullable-столбец
    op.add_column(
        'products',
        sa.Column('sku', sa.String(length=50), nullable=True)
    )

    # 2. Заполняем существующие записи
    op.execute("""
        UPDATE products
        SET sku = 'SKU-' || CAST(id AS TEXT)
        WHERE sku IS NULL
    """)

    # 3. Для SQLite изменение структуры через batch_alter_table
    with op.batch_alter_table('products') as batch_op:
        batch_op.alter_column(
            'sku',
            existing_type=sa.String(length=50),
            nullable=False
        )

        batch_op.create_unique_constraint(
            'uq_products_sku',
            ['sku']
        )


def downgrade() -> None:
    with op.batch_alter_table('products') as batch_op:
        batch_op.drop_constraint(
            'uq_products_sku',
            type_='unique'
        )

    op.drop_column('products', 'sku')
```

В режиме `batch_alter_table()` Alembic делает хитрый обходной путь:

* Создает временную таблицу с новой схемой.
* Копирует данные.
* Удаляет старую таблицу.
* Переименовывает новую.

То есть имитирует изменение структуры таблицы, которого SQLite сам делать не умеет.

**Рассмотрим вариант для Postgres**:

Тот же вариант миграции для Postgres будет выглядеть проще:

```python
def upgrade() -> None:
    # Шаг 2а: добавляем столбец как nullable
    op.add_column('products',
        sa.Column('sku', sa.String(length=50), nullable=True)
    )

    # Шаг 2б: заполняем существующие строки уникальными значениями
    # Используем op.execute для прямого SQL внутри миграции
    op.execute("""
        UPDATE products
        SET sku = 'SKU-' || CAST(id AS TEXT)
        WHERE sku IS NULL
    """)
    # Каждый товар получит артикул: SKU-1, SKU-2, SKU-3...
    # В реальном проекте здесь могла бы быть более сложная логика
    # или вы могли бы импортировать реальные артикулы из другой системы

    # Шаг 2в: теперь ставим NOT NULL — все строки уже заполнены
    op.alter_column('products', 'sku', nullable=False)

    # Шаг 2г: уникальный индекс
    op.create_unique_constraint('uq_products_sku', 'products', ['sku'])


def downgrade() -> None:
    op.drop_constraint('uq_products_sku', 'products', type_='unique')
    op.drop_column('products', 'sku')
```

#### Шаг 3. Обновить модель — убрать nullable

После того как миграция написана — обновляем модель в соответствии с финальным состоянием:

```python
# models.py — финальный вариант
sku = Column(String(50), nullable=False, unique=True)   # ← убрали nullable=True
```

#### Шаг 4. Применить миграцию

```bash
alembic upgrade head
```

```
INFO  Running upgrade def456 -> ghi789, add sku to products
```

#### Шаг 5. Проверить результат

```python
from sqlalchemy.orm import Session
from sqlalchemy import select
from database import engine
from models import Product

with Session(engine) as session:
    products = session.execute(select(Product)).scalars().all()
    for p in products:
        print(f'{p.name}: sku={p.sku!r}')
```

```
Ноутбук Lenovo:     sku='SKU-1'
Смартфон Samsung:   sku='SKU-2'
Наушники Sony:      sku='SKU-3'
Мышь Logitech:      sku='SKU-4'
Клавиатура Keychron: sku='SKU-5'
Чистый код. Мартин: sku='SKU-6'
Грокаем алгоритмы:  sku='SKU-7'
```

Все 7 существующих товаров получили уникальные артикулы. Новые товары при создании должны будут передать `sku` явно — иначе `NOT NULL` не пустит.

---

## Сравнение двух ситуаций

| | Ситуация 1: nullable | Ситуация 2: NOT NULL |
|---|---|---|
| Сложность миграции | Простая — Alembic сделает всё сам | Требует ручного дополнения |
| Риск потери данных | Нет | Нет, если сделать правильно |
| Как заполнить старые строки | Автоматически NULL | Вручную через `op.execute()` |
| Что проверять в сгенерированной миграции | Убедиться что `nullable=True` | Убедиться что нет `nullable=False` без заполнения |
| Типичная ошибка | — | Применить NOT NULL без заполнения → OperationalError |

---

## Главное правило

**Всегда открывайте сгенерированный файл миграции перед `alembic upgrade head`.**

Alembic — умный инструмент, но он не знает ваших данных. Он видит разницу в схеме и генерирует SQL. Что делать с существующими данными при изменении схемы — ваша ответственность. Миграция это не только `CREATE TABLE` и `ADD COLUMN` — иногда это и `UPDATE` для подготовки данных.

Именно поэтому файлы миграций хранятся в Git и ревьюятся как обычный код — в них может быть логика работы с данными которая так же важна как любой другой код проекта.

---

</details>

[Предыдущий урок](lesson24.md) | [Следующий урок](lesson26.md)