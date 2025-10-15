# Модуль 4. Урок 11. CSS Grid

## 1. Что такое Grid и зачем он нужен

**CSS Grid** — это система для построения двухмерных макетов: она управляет **рядами и колонками одновременно**. Grid даёт удобные и декларативные инструменты для создания страниц, панелей, карточных сеток и сложных шаблонов, где нужно явно управлять и колонками, и строками.

### Главное отличие Grid vs Flex

- **Flexbox** — идеален для одномерной компоновки: одна строка _или_ одна колонка. Отлично подходит для выравнивания компонентов внутри строки/колонки (навигация, групповая кнопка, внутренняя компоновка карточки).
- **Grid** — предназначен для двухмерной раскладки: вы задаёте колонки **и** ряды и располагаете элементы по сетке. Grid удобен для глобальной структуры страницы (макет страницы, дашборд, галерея карточек).

**Правило практики:** используйте Grid для общей структуры (layout), а Flex — внутри компонентов (item-level alignment).

---

## 2. Базовая терминология

- **Grid container** — элемент с `display: grid;` (контейнер-сетка).
- **Grid item** — прямые дочерние элементы grid-контейнера.
- **Track** — одна колонка или одна строка (column track / row track).
- **Grid line** — линии сетки, между которыми располагаются элементы (номеруются).
- **Grid cell** — пересечение одной колонки и одной строки (ячейка).
- **Grid area** — объединённые соседние ячейки (область) — удобно именовать.
- **Explicit grid** — строки/колонки, которые вы явно задали (`grid-template-*`).
- **Implicit grid** — строки/колонки, которые создаются автоматически, если элементов больше, чем явно задано.
- **Fraction (`fr`)** — специальная единица Grid для долей свободного пространства.

---

## 3. Простейший рабочий пример (готовая разметка + стили)

Скопируй и открой файл в браузере — это минимальная сетка с 3 колонками и `gap`. Каждый элемент — grid-item.

### `grid-basic.html`

```html
<!DOCTYPE html>
<html lang="ru">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width,initial-scale=1" />
    <title>Grid — базовый пример</title>
    <style>
      body {
        font-family: Arial, sans-serif;
        margin: 20px;
        background: #f4f6f8;
        color: #111;
      }
      .grid {
        display: grid; /* делаем контейнер grid */
        grid-template-columns: 1fr 1fr 1fr; /* 3 колонки одинаковой ширины */
        gap: 16px; /* расстояние между ячейками */
        max-width: 1000px;
        margin: 0 auto;
      }
      .card {
        background: white;
        padding: 16px;
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
        min-height: 120px;
      }
    </style>
  </head>
  <body>
    <h1>Grid — базовая сетка</h1>
    <p>3 колонки одинаковой ширины.</p>

    <div class="grid">
      <div class="card">Элемент 1</div>
      <div class="card">Элемент 2</div>
      <div class="card">Элемент 3</div>
      <div class="card">Элемент 4</div>
      <div class="card">Элемент 5</div>
      <div class="card">Элемент 6</div>
    </div>
  </body>
</html>
```

---

## 4. Колонки и ряды: `grid-template-columns` / `grid-template-rows`

Эти свойства задают **явную сетку**: сколько колонок/рядов и их размеры.

### Синтаксис и примеры

1. **Фиксированные размеры**

   ```css
   grid-template-columns: 200px 200px 200px; /* три колонки по 200px */
   ```

   Используется, когда нужно точное значение колонок (напр., боковая панель фиксированной ширины).

2. **Процент/auto**

   ```css
   grid-template-columns: 20% auto 30%;
   ```

   Процентные значения указывают долю контейнера, `auto` подстраивается под содержимое.

3. **`fr` — фракции**

   ```css
   grid-template-columns: 1fr 2fr 1fr;
   ```

   `1fr 2fr 1fr` — свободное пространство делится в пропорциях 1:2:1. Очень удобно вместо процента.

4. **repeat() — краткая запись**

   ```css
   grid-template-columns: repeat(3, 1fr); /* то же, что 1fr 1fr 1fr */
   ```

5. **mix: fixed + fr**

   ```css
   grid-template-columns: 240px 1fr 1fr; /* левый aside фиксирован, право гибкие */
   ```

6. **rows — строки**

   ```css
   grid-template-rows: 80px auto 60px; /* шапка 80px, контент — гибкий, футер 60px */
   ```

### Как это выглядит визуально

Добавим пример, где `aside` фиксирован, а контент гибко делится:

```html
<!-- Вставлять внутрь тела страницы -->
<div
  style="display:grid; grid-template-columns:240px 1fr; gap:16px; max-width:1000px; margin:20px auto;"
>
  <aside style="background:#fff;padding:12px;border-radius:8px;">
    Aside (240px)
  </aside>
  <main style="background:#fff;padding:12px;border-radius:8px;">
    Main (1fr)
  </main>
</div>
```

---

## 5. Практические мини-примеры (копировать и пробовать)

### Пример A — 4 колонки одинаковой ширины

```css
.grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}
```

### Пример B — фиксированный sidebar + 2 гибких колонки

```css
.grid {
  display: grid;
  grid-template-columns: 200px 1fr 1fr;
  gap: 16px;
}
```

### Пример C — сетка с явными строками

```css
.grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  grid-template-rows: 80px 1fr 80px; /* header, content, footer */
}
```

---

## 6. Единицы измерения в Grid: `fr`, `px`, `%`, `minmax()` и `auto`

### Краткая шпаргалка (что делает каждая)

- `px` — фиксированная величина в пикселях. Используйте когда нужна точная ширина (sidebar, колонки с фикс.контентом).
- `%` — процент от контейнера. Хорошо для относительных ширин, но зависит от padding/margin родителя.
- `fr` — дробная единица. Делит **свободное пространство** контейнера после вычета фиксированных треков. Отлично для гибкой сетки.
- `minmax(min, max)` — задаёт диапазон: трек не станет меньше `min` и не больше `max`. Очень полезно для адаптивных сеток.
- `auto` — размер по содержимому (или по заданной ширине элемента). Полезно, когда нужно подстроиться под контент.

### Когда что предпочесть — рекомендации

- Sidebar / колонки управления: `px` (фиксированная ширина) или `minmax(200px, 1fr)` (минимум — 200px, дальше гибко).
- Главный контент: `1fr` (или `2fr`/`3fr`) — чтобы занять оставшееся место.
- Карточная сетка (адаптивная): `repeat(auto-fill, minmax(200px, 1fr))` — карточки минимум 200px и делятся оставшееся место.
- Проценты — редко нужны внутри grid, чаще используются в старых макетах; `fr` обычно лучше читается и надёжнее.
- `auto` — когда важно, чтобы колонка подстраивалась по содержимому (например, кнопки, короткие метки).

---

### Пример: сравнение `fr` / `%` / `px` / `minmax`

Скопируй и открой в браузере — три небольших примера, каждый показывает разное поведение.

```html
<!DOCTYPE html>
<html lang="ru">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width,initial-scale=1" />
    <title>Grid — единицы измерения</title>
    <style>
      body {
        font-family: Arial, sans-serif;
        padding: 20px;
        background: #f5f6f8;
        color: #111;
      }
      section {
        background: #fff;
        padding: 12px;
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
        margin-bottom: 20px;
      }
      .grid {
        display: grid;
        gap: 12px;
        margin-top: 12px;
      }
      .cell {
        background: #e9f2ff;
        padding: 16px;
        border-radius: 6px;
        text-align: center;
        min-height: 80px;
      }
      h2 {
        margin: 0;
      }
    </style>
  </head>
  <body>
    <section>
      <h2>1) fr — гибкие доли</h2>
      <p>
        grid-template-columns: <code>1fr 2fr 1fr</code> — вторая колонка в 2
        раза шире.
      </p>
      <div class="grid" style="grid-template-columns:1fr 2fr 1fr;">
        <div class="cell">1fr</div>
        <div class="cell">2fr</div>
        <div class="cell">1fr</div>
      </div>
    </section>

    <section>
      <h2>2) px и % — фикс и процент</h2>
      <p>grid-template-columns: <code>200px 50% auto</code></p>
      <div class="grid" style="grid-template-columns:200px 50% auto;">
        <div class="cell">200px</div>
        <div class="cell">50%</div>
        <div class="cell">auto</div>
      </div>
    </section>

    <section>
      <h2>3) minmax() — минимум/максимум</h2>
      <p>
        grid-template-columns:
        <code>minmax(150px, 1fr) minmax(150px, 2fr)</code>
      </p>
      <div
        class="grid"
        style="grid-template-columns: minmax(150px,1fr) minmax(150px,2fr);"
      >
        <div class="cell">minmax(150px,1fr)</div>
        <div class="cell">minmax(150px,2fr)</div>
      </div>
    </section>
  </body>
</html>
```

**Что посмотреть:** изменяй ширину окна браузера — увидишь, как каждый трек реагирует по-разному.

---

## 7. `repeat()` и `repeat(auto-fill / auto-fit, ...)`

### Что это делает

- `repeat(n, value)` — сокращённая запись вместо повторения `value` n раз. Удобно и компактно.
- `repeat(auto-fill, minmax(...))` и `repeat(auto-fit, minmax(...))` — мощный приём для адаптивных сеток карточек:

  - `auto-fill` создаёт столько колонок указанной min ширины, _сколько помещается_; если остаётся место, оно будет пустым или заполнено колонками.
  - `auto-fit` похож, но «подгоняет» колонки под содержимое; при достаточном месте колонки «растягиваются» чтобы заполнить строку; поведение очень близко и в большинстве случаев взаимозаменяемо, но есть тонкости по тому, как заполняются пустые колонки при большом пространстве.

> Примечание: `auto-fill/fit` чаще используются в адаптивных макетах.

### Пример использования (карточки)

```html
<!DOCTYPE html>
<html lang="ru">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width,initial-scale=1" />
    <title>repeat(auto-fill) demo</title>
    <style>
      body {
        font-family: Arial, sans-serif;
        padding: 20px;
        background: #fafafa;
      }
      .grid {
        display: grid;
        gap: 12px;
        margin-top: 12px;
        grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
      }
      .card {
        background: #fff;
        padding: 12px;
        border-radius: 8px;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.06);
        min-height: 120px;
      }
    </style>
  </head>
  <body>
    <h2>repeat(auto-fill, minmax(180px, 1fr))</h2>
    <p>Изменяйте ширину окна — карточки сами перестраиваются в строки.</p>

    <div class="grid">
      <div class="card">Карточка 1</div>
      <div class="card">Карточка 2</div>
      <div class="card">Карточка 3</div>
      <div class="card">Карточка 4</div>
      <div class="card">Карточка 5</div>
      <div class="card">Карточка 6</div>
      <div class="card">Карточка 7</div>
    </div>
  </body>
</html>
```

**Совет:** использовать `minmax(150px, 1fr)` или `180px` в зависимости от желаемого минимума карточки.

---

## 8. Размещение элементов: `grid-column`, `grid-row`, `span`

### Что это делает

- `grid-column: start / end` — задаёт с какими линиями колонки элемент должен совпадать (линии нумеруются от 1).
- `grid-column: span N` — элемент занимает N колонок, начиная с его текущей позиции.
- Аналогично для `grid-row`.

### Синтаксис:

- `grid-column: 1 / 3;` — занимает с линии 1 до линии 3 (то есть **2 колонки**).
- `grid-column: 2 / span 2;` — начинает на линии 2 и занимает ещё 2 колонки.
- `grid-column: span 3;` — занимает 3 колонки, начиная с места в сетке, где он окажется по порядку.

### Примеры

#### HTML/CSS демо: разные способы span / start-end

```html
<!DOCTYPE html>
<html lang="ru">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width,initial-scale=1" />
    <title>grid-column / span demo</title>
    <style>
      body {
        font-family: Arial, sans-serif;
        padding: 20px;
        background: #f8fafc;
      }
      .grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 12px;
      }
      .box {
        background: #fff;
        padding: 12px;
        border-radius: 8px;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.06);
      }
      .a {
        grid-column: 1 / 3;
      } /* занимает колонки 1 и 2 */
      .b {
        grid-column: 3 / span 2;
      } /* начинается на 3 и span 2 (3 и 4) */
      .c {
        grid-column: span 2;
      } /* занимает 2 колонки в месте в потоке */
    </style>
  </head>
  <body>
    <h2>Размещение элементов: start/end и span</h2>
    <div class="grid">
      <div class="box a">.a — grid-column: 1 / 3</div>
      <div class="box b">.b — grid-column: 3 / span 2</div>
      <div class="box c">.c — grid-column: span 2</div>
      <div class="box">обычная</div>
      <div class="box">обычная</div>
    </div>
  </body>
</html>
```

---

## Практические упражнения (быстро и понятно)

1. **Сделай 3-колоночную сетку** (`repeat(3, 1fr)`) и создай блок, который занимает **две** колонки (используй `grid-column: span 2;`).
   Проверь, что при уменьшении ширины браузера поведение остаётся корректным.

2. **Сделай layout с sidebar**: `grid-template-columns: 200px 1fr 1fr;`
   Вставь карточку, которая занимает вторую и третью колонки: `grid-column: 2 / 4;`.

3. **Адаптивная карточная сетка:** используй `repeat(auto-fill, minmax(180px, 1fr))` и добавь 8 карточек — проверь перестройку при изменении ширины.

4. **Смешай fixed + fr + minmax:**
   `grid-template-columns: 240px minmax(200px, 2fr) 1fr;` — посмотри, как ведёт себя средняя колонка.

---

## 9. Grid gaps и выравнивания

`gap` и связанные с ним свойства управляют **пространством между ячейками** сетки. Свойства выравнивания (`align-*` / `justify-*`) управляют тем, **как содержимое ячеек и сама сетка располагаются** внутри контейнера. Вместе они дают полный контроль над визуальной компоновкой карточек, их выравниванием и поведением при разной высоте/ширине.

---

### 1. `gap`, `row-gap`, `column-gap`

**Что делают**

- `gap` — задаёт расстояние между строками и колонками (универсально).
- `row-gap` — только вертикальный промежуток между строками.
- `column-gap` — только горизонтальный промежуток между колонками.

**Почему `gap` лучше, чем `margin` между элементами**

- `gap` не требует «убирать» внешние отступы у крайних элементов.
- `gap` работает прямо на контейнере (`display:grid` / `display:flex`) и корректно учитывает систему размещения.

---

### Пример 1 — базовая сетка карточек с gap

Скопируй этот пример в файл и открой в браузере — увидишь, как `gap` влияет на сетку.

```html
<!DOCTYPE html>
<html lang="ru">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width,initial-scale=1" />
    <title>Grid — gap и выравнивание (пример 1)</title>
    <style>
      body {
        font-family: Arial, sans-serif;
        padding: 20px;
        background: #f7f8fb;
        color: #111;
      }
      h2 {
        margin: 0 0 8px 0;
      }
      .demo {
        margin-bottom: 28px;
      }

      .grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 20px; /* <-- общий gap между строками и колонками */
        background: #fff;
        padding: 16px;
        border-radius: 8px;
      }

      .card {
        background: #ffffff;
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
        overflow: hidden;
        display: flex;
        flex-direction: column;
      }

      .cover {
        height: 140px;
        background: #dbeafe;
        display: block;
      }
      .body {
        padding: 12px;
        flex: 1;
        display: flex;
        flex-direction: column;
      }
      .title {
        font-weight: bold;
        margin-bottom: 8px;
      }
      .desc {
        flex: 1;
        color: #333;
        margin-bottom: 12px;
      }
      .meta {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 8px;
      }
      .btn {
        padding: 6px 10px;
        border: none;
        background: #2563eb;
        color: white;
        border-radius: 6px;
        cursor: pointer;
      }
    </style>
  </head>
  <body>
    <section class="demo">
      <h2>Пример: gap (20px)</h2>
      <p>grid-template-columns: repeat(3, 1fr); gap: 20px;</p>

      <div class="grid">
        <article class="card">
          <img
            class="cover"
            src="https://picsum.photos/seed/p1/600/400"
            alt=""
          />
          <div class="body">
            <div class="title">Карточка 1</div>
            <div class="desc">
              Короткое описание карточки для демонстрации высоты.
            </div>
            <div class="meta">
              <div>€49</div>
              <button class="btn">Открыть</button>
            </div>
          </div>
        </article>

        <article class="card">
          <img
            class="cover"
            src="https://picsum.photos/seed/p2/600/400"
            alt=""
          />
          <div class="body">
            <div class="title">Карточка 2</div>
            <div class="desc">
              Более длинное описание, чтобы увидеть, как карточки ведут себя при
              разной высоте контента. Тут текста явно больше.
            </div>
            <div class="meta">
              <div>€79</div>
              <button class="btn">Открыть</button>
            </div>
          </div>
        </article>

        <article class="card">
          <img
            class="cover"
            src="https://picsum.photos/seed/p3/600/400"
            alt=""
          />
          <div class="body">
            <div class="title">Карточка 3</div>
            <div class="desc">Описание.</div>
            <div class="meta">
              <div>€29</div>
              <button class="btn">Открыть</button>
            </div>
          </div>
        </article>
      </div>
    </section>
  </body>
</html>
```

---

## 10. Выравнивания в Grid: понятия и где применяются

- `align-items` — выравнивание содержимого **каждой ячейки** по вертикали (вдоль cross axis).
- `justify-items` — выравнивание содержимого **каждой ячейки** по горизонтали (вдоль main axis).
- `align-content` — выравнивание **всей сетки** внутри контейнера по вертикали, когда сетка меньше контейнера (есть свободное пространство).
- `justify-content` — выравнивание **всей сетки** внутри контейнера по горизонтали.
- `place-items` = сокращение для `align-items` + `justify-items`.
- `place-content` = сокращение для `align-content` + `justify-content`.

**Ключевое отличие:** `*-items` управляют тем, как **_внутри каждой ячейки_** позиционируется содержимое; `*-content` управляют тем, как **_вся сетка как блок_** располагается внутри контейнера, если между сеткой и контейнером осталось свободное место.

---

### Пример 2 — `align-items` и `justify-items` (видно на карточках с разной высотой контента)

```html
<!DOCTYPE html>
<html lang="ru">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width,initial-scale=1" />
    <title>Grid — align-items / justify-items</title>
    <style>
      body {
        font-family: Arial;
        padding: 20px;
        background: #f6f7fb;
      }
      .demo {
        margin-bottom: 28px;
      }
      .grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 12px;
        padding: 12px;
        background: #fff;
        border-radius: 8px;
      }
      /* Вариант: выравнивание содержимого ячеек */
      .grid.align-center {
        align-items: center;
        justify-items: center;
      } /* содержимое каждой ячейки центрировано */
      .grid.align-start {
        align-items: start;
        justify-items: start;
      } /* содержимое с верхнего левого края ячейки */
      .grid.align-end {
        align-items: end;
        justify-items: end;
      } /* содержимое внизу вправо */
      .box {
        background: #eaf2ff;
        padding: 12px;
        border-radius: 8px;
        min-height: 120px;
      }
      .box p {
        margin: 0;
      }
    </style>
  </head>
  <body>
    <section class="demo">
      <h3>align-items: center; justify-items: center;</h3>
      <div class="grid align-center">
        <div class="box">
          <h4>Короткий</h4>
          <p>Текст</p>
        </div>
        <div class="box">
          <h4>Средний</h4>
          <p>Немного длиннее описание чтобы увидеть центрирование</p>
        </div>
        <div class="box">
          <h4>Длинный</h4>
          <p>
            Очень длинное описание. Lorem ipsum dolor sit amet, consectetur
            adipisicing elit.
          </p>
        </div>
      </div>
    </section>

    <section class="demo">
      <h3>align-items: start; justify-items: start;</h3>
      <div class="grid align-start">
        <div class="box">
          <h4>Короткий</h4>
          <p>Текст</p>
        </div>
        <div class="box">
          <h4>Средний</h4>
          <p>Немного длиннее</p>
        </div>
        <div class="box">
          <h4>Длинный</h4>
          <p>Длинный текст</p>
        </div>
      </div>
    </section>
  </body>
</html>
```

**Что видно:** при `align-items: center` содержимое каждой карточки (в пределах её ячейки) центрируется по вертикали; при `start` — прижато к верху.

---

### Пример 3 — `align-content` / `justify-content`

Эти свойства важны, когда **высота/ширина контейнера больше**, чем суммарный размер сетки — например, когда вы задали фиксированную высоту контейнера или вьюпорта.

```html
<!DOCTYPE html>
<html lang="ru">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width,initial-scale=1" />
    <title>Grid — align-content / justify-content</title>
    <style>
      body {
        font-family: Arial;
        margin: 0;
        background: #f3f4f7;
        padding: 20px;
      }
      .wrap {
        height: 420px;
        background: #fff;
        padding: 12px;
        border-radius: 8px;
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 10px;
      }
      /* Управление всей сеткой внутри .wrap */
      .wrap.top {
        align-content: start;
        justify-content: center;
      }
      .wrap.center {
        align-content: center;
        justify-content: center;
      }
      .wrap.space {
        align-content: space-between;
        justify-content: space-around;
      }
      .item {
        background: #e9f3ff;
        padding: 12px;
        border-radius: 6px;
        min-height: 80px;
      }
    </style>
  </head>
  <body>
    <h3>align-content / justify-content — позиция всей сетки в контейнере</h3>
    <p>
      Контейнер имеет фиксированную высоту — смотрите, как сетка смещается
      внутри.
    </p>

    <div class="wrap top">
      <div class="item">1</div>
      <div class="item">2</div>
      <div class="item">3</div>
      <div class="item">4</div>
      <div class="item">5</div>
      <div class="item">6</div>
    </div>

    <hr style="margin:18px 0;" />

    <div class="wrap center">
      <div class="item">1</div>
      <div class="item">2</div>
      <div class="item">3</div>
      <div class="item">4</div>
      <div class="item">5</div>
      <div class="item">6</div>
    </div>

    <hr style="margin:18px 0;" />

    <div class="wrap space">
      <div class="item">1</div>
      <div class="item">2</div>
      <div class="item">3</div>
      <div class="item">4</div>
      <div class="item">5</div>
      <div class="item">6</div>
    </div>
  </body>
</html>
```

**Пояснение:**

- `align-content: center` — вертикально центрирует всю сетку внутри контейнера;
- `justify-content: space-around` — по горизонтали распределяет ряды/колонки с отступами.

---

### Набор простых упражнений (быстро проверить понимание)

1. Создать grid с 3 колонками и `gap: 24px`. Сделать так, чтобы содержимое **каждой** ячейки было по центру (гориз.+верт.).
2. Сделать сетку карточек, где карточки имеют разные объёмы текста, но кнопки у всех карточек прижаты к низу (использовать внутренний `display:flex; flex-direction:column;` + `margin-top:auto` или `flex:1` у body).
3. Создать контейнер фиксированной высоты (например, 480px) и расположить внутри 6 элементов; применить `align-content: space-between` и `justify-content: center`. Посмотреть итог.
4. Сделать две соседние секции: в первой — `justify-items: start`, во второй — `justify-items: end`. Понаблюдать за горизонтальным позиционированием.

---

## 11. Grid Template Areas — именованные области в Grid

Grid Layout позволяет не только задавать количество строк и столбцов, но и **давать названия областям сетки**.
Это делает код **наглядным, читаемым** и упрощает позиционирование элементов — особенно при создании **сложных макетов страниц** (header, sidebar, main, footer и т.д.).

---

### Что такое `grid-template-areas`

Свойство **`grid-template-areas`** позволяет задать **шаблон размещения** элементов внутри сетки.
Вы создаете как бы **“карту” сетки**, где каждый участок имеет имя (area name).

### Пример структуры

```css
grid-template-areas:
  "header header"
  "sidebar main"
  "footer footer";
```

Такой шаблон создаёт:

- первую строку из двух ячеек под `header`,
- вторую строку с `sidebar` и `main`,
- третью строку с `footer`.

---

### Пример базовой страницы с именованными областями

Создадим простую структуру:

```html
<body>
  <header>HEADER</header>
  <aside>SIDEBAR</aside>
  <main>MAIN CONTENT</main>
  <footer>FOOTER</footer>
</body>
```

Теперь применим Grid к `<body>`:

```css
body {
  display: grid;
  grid-template-columns: 200px 1fr;
  grid-template-rows: 80px 1fr 60px;
  grid-template-areas:
    "header header"
    "sidebar main"
    "footer footer";
  height: 100vh;
  gap: 10px;
}

header {
  grid-area: header;
  background: #6c5ce7;
  color: white;
}
aside {
  grid-area: sidebar;
  background: #a29bfe;
  color: white;
}
main {
  grid-area: main;
  background: #dfe6e9;
  color: #2d3436;
}
footer {
  grid-area: footer;
  background: #636e72;
  color: white;
}
```

**Результат:**

- Header занимает всю верхнюю строку.
- Sidebar располагается слева, main — справа.
- Footer тянется по всей нижней строке.

---

### Правила именования областей

- Имя области — это любое слово (например, `"main"`, `"sidebar"`).
- Пустые ячейки можно обозначать точкой (`"."`).
- Все строки шаблона должны содержать **одинаковое количество “ячейчных имен”**.

Пример с пропуском области:

```css
grid-template-areas:
  "header header"
  "sidebar ."
  "footer footer";
```

Точка (`.`) означает пустую ячейку.

---

### Распределение областей по элементам

Чтобы элемент оказался в нужной области, ему присваивается свойство:

```css
.element {
  grid-area: имя-области;
}
```

Например:

```css
header {
  grid-area: header;
}
aside {
  grid-area: sidebar;
}
main {
  grid-area: main;
}
footer {
  grid-area: footer;
}
```

---

### Пример: Сетка внутри `main`

Теперь создадим шаблон **внутри `main`**, где будут карточки клиентов (например, для CRM-страницы):

```html
<main>
  <div class="filters">Фильтры</div>
  <div class="cards">Карточки</div>
  <div class="stats">Статистика</div>
</main>
```

```css
main {
  display: grid;
  grid-template-columns: 1fr 2fr;
  grid-template-rows: auto 200px;
  grid-template-areas:
    "filters cards"
    "stats cards";
  gap: 15px;
}

.filters {
  grid-area: filters;
  background: #fab1a0;
}
.cards {
  grid-area: cards;
  background: #ffeaa7;
}
.stats {
  grid-area: stats;
  background: #74b9ff;
}
```

**Что произойдет:**

- `filters` займёт левую верхнюю ячейку,
- `cards` — правую колонку и растянется на две строки,
- `stats` — левую нижнюю ячейку.

---

### Почему это удобно

Использование `grid-template-areas` делает код:

- **визуально понятным** — сразу видно структуру страницы;
- **гибким** — можно легко менять расположение блоков, просто поменяв шаблон;
- **независимым от HTML-порядка** — блоки могут быть в любом месте в разметке.

---

### Мини-практика

Создай сетку страницы:

```
HEADER
SIDEBAR | MAIN
FOOTER
```

**Задание:**

1. Создай теги: `<header>`, `<aside>`, `<main>`, `<footer>`.
2. Задай контейнеру (`body` или `.grid-container`) 3 строки и 2 колонки.
3. Присвой каждой области имя и задай шаблон:

   ```
   "header header"
   "sidebar main"
   "footer footer"
   ```

4. Используй `gap: 10px` и задай разный фон каждому блоку.
5. Установи высоту контейнера `min-height: 100vh`.

## 12. Практическая работа: Страница фильмов

**Цель:**
Закрепить работу с **Grid Layout (grid-template-areas)** и **Flexbox**, создав полноценную страницу каталога фильмов.

---

### Задача

Создай веб-страницу, которая будет состоять из четырёх основных секций:

- **header** — шапка сайта
- **aside** — боковая панель с фильтрами
- **main** — основная часть с карточками фильмов
- **footer** — нижняя часть сайта

Вся страница должна быть выстроена с помощью **Grid Layout**, используя **grid-template-areas**.
Сетка должна иметь такую структуру:

```
header header
aside  main
footer footer
```

---

### Требования к разметке и стилям

#### 1. Общая сетка страницы

- Используй тег `body` или контейнер `div` для всей страницы.
- Настрой сетку с помощью **grid-template-areas**.
- Укажи сетку в 3 ряда: `header`, `aside + main`, `footer`.
- Задай пропорции колонок и рядов так, чтобы структура выглядела аккуратно (например: `grid-template-columns: 250px 1fr;`).

---

#### 2. Блок `header`

- Внутри `header` размести:

  - логотип (изображение),
  - название сайта (например, “MovieGrid”),
  - навигацию с пунктами: **Главная**, **Фильмы**, **Контакты**.

- Построй содержимое `header` с помощью **display: flex**.
- Распредели элементы по горизонтали с помощью **justify-content**.
- Навигацию (`nav`) также выстрой с помощью **display: flex**.

---

#### 3. Блок `aside`

- Размести внутри три пункта фильтра:

  - Фильмы
  - Сериалы
  - Мультики

- Используй **display: flex** и **flex-direction: column**, чтобы выстроить их вертикально.

---

#### 4. Блок `main`

- В `main` размести **6 карточек фильмов**.
- Каждая карточка должна содержать:

  - контейнер для изображения (`div > img`);
  - название фильма;
  - краткое описание;
  - ссылку “Смотреть”.

- Внутри карточки используй **display: flex** и **flex-direction: column**.
- Карточки фильмов должны быть выстроены в сетку (например, 3 колонки по 2 ряда).

---

#### 5. Блок `footer`

- Размести две части:

  - Контакты (например, “Связаться с нами”)
  - Копирайт (например, “© 2025 MovieGrid”)

- Используй **display: flex** и свойство **justify-content**, чтобы развести эти элементы по разным сторонам.

---

### Пример реализации

<img src='img/result-practice-grid.jpg' width='500px'>

---

### Картинки используемые в проекте

<img src='img/grid-1.webp' width='150px'>
<img src='img/grid-2.webp' width='150px'>
<img src='img/grid-3.webp' width='150px'>
<img src='img/grid-4.webp' width='150px'>
<img src='img/grid-5.webp' width='150px'>
<img src='img/grid-6.webp' width='150px'>

---

[Предыдущий урок](lesson10.md) | [Следующий урок](lesson12.md)
