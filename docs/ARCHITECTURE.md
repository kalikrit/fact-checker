# Архитектура

Структура проекта, ответственности модулей, карта зависимостей.
Основа для контрактов и реализации.

Версия: 1.0
Дата: 2026-09-25

---

## Общая картина

Два приложения: **backend** (Python) и **frontend** (Vue). Общаются
через REST API.

```
┌─────────────────────────────────────────┐
│  FRONTEND (Vue 3)                       │
│  UI · ввод · прогресс · результат       │
└────────────────┬────────────────────────┘
                 │ REST API (HTTP + JSON)
                 ▼
┌─────────────────────────────────────────┐
│  BACKEND (FastAPI)                      │
│                                          │
│  ┌────────────────────────────────────┐ │
│  │  api/ — routes, DTO, валидация     │ │
│  └──────────────┬─────────────────────┘ │
│                 │                        │
│  ┌──────────────▼─────────────────────┐ │
│  │  pipeline/ — оркестратор шагов     │ │
│  └──────────────┬─────────────────────┘ │
│                 │                        │
│  ┌──────────────▼─────────────────────┐ │
│  │  domain/ — чистая логика           │ │
│  │  (ноль зависимостей от FastAPI,    │ │
│  │   requests, LLM, БД)               │ │
│  └──────────────┬─────────────────────┘ │
│                 │                        │
│  ┌──────────────▼─────────────────────┐ │
│  │  infrastructure/ — внешний мир     │ │
│  │  LLM · search · DB · cache         │ │
│  └────────────────────────────────────┘ │
└─────────────────────────────────────────┘
                 │
                 ▼
    ┌────────────┬────────────┬──────────┐
    │ GigaChat   │ DuckDuckGo │  SQLite  │
    │ (Cloud.ru) │ + Wikipedia│          │
    └────────────┴────────────┴──────────┘
```

**Правило зависимостей:** стрелки идут **только сверху вниз**.
Никогда наоборот.

---

## Backend: структура

```
backend/
├── app/
│   ├── main.py                  ← точка входа FastAPI
│   │
│   ├── api/                     ← HTTP-слой
│   │   ├── __init__.py
│   │   ├── routes.py            ← эндпоинты
│   │   ├── schemas.py           ← Pydantic DTO
│   │   └── dependencies.py      ← DI-провайдеры
│   │
│   ├── pipeline/                ← оркестратор
│   │   ├── __init__.py
│   │   ├── orchestrator.py      ← главный класс Pipeline
│   │   ├── steps.py             ← описания шагов
│   │   └── errors.py            ← классификация ошибок
│   │
│   ├── domain/                  ← чистая логика
│   │   ├── __init__.py
│   │   ├── models.py            ← сущности
│   │   ├── enums.py             ← перечисления
│   │   ├── extractor.py         ← extractClaims
│   │   ├── plausibility.py      ← assessPlausibility
│   │   ├── query_builder.py     ← buildQueries
│   │   ├── source_rater.py      ← rateSource
│   │   ├── evidence_finder.py   ← findEvidence
│   │   ├── verdict_maker.py     ← decideVerdict
│   │   ├── attribute_checker.py ← checkAttribute
│   │   ├── aggregator.py        ← aggregateVerdict
│   │   ├── confidence.py        ← calculateConfidence
│   │   └── ports.py             ← интерфейсы (LLMPort, SearchPort)
│   │
│   ├── infrastructure/          ← внешний мир
│   │   ├── __init__.py
│   │   ├── llm/
│   │   │   ├── client.py        ← общий интерфейс LLMClient
│   │   │   ├── gigachat.py      ← реализация GigaChat
│   │   │   └── prompts.py       ← все промпты
│   │   ├── search/
│   │   │   ├── client.py        ← общий интерфейс SearchClient
│   │   │   ├── duckduckgo.py
│   │   │   └── wikipedia.py
│   │   ├── fetching/
│   │   │   └── page_fetcher.py  ← скачивание и парсинг HTML
│   │   ├── storage/
│   │   │   ├── db.py            ← подключение SQLite
│   │   │   ├── models.py        ← ORM-модели (отдельно от домена)
│   │   │   └── repositories.py  ← save/get tasks
│   │   └── cache/
│   │       ├── cache.py         ← общий интерфейс
│   │       └── sqlite_cache.py  ← реализация
│   │
│   └── config.py                ← настройки (env, константы)
│
├── tests/
│   ├── domain/
│   │   ├── test_extractor.py
│   │   ├── test_plausibility.py
│   │   ├── test_verdict_maker.py
│   │   └── ...
│   ├── pipeline/
│   │   └── test_orchestrator.py
│   └── api/
│       └── test_routes.py
│
├── data/                        ← SQLite, кэш (в .gitignore)
├── requirements.txt
├── pyproject.toml
└── README.md
```

---

## Backend: ответственности модулей

### `api/` — HTTP-слой

**Ответственность:** принять HTTP-запрос, провалидировать, вернуть
ответ.

**Что делает:**
- `POST /api/check` — создать задачу.
- `GET /api/check/{id}` — статус и результат.
- Валидация через Pydantic.
- Маппинг доменных объектов ↔ Pydantic DTO.
- DI: передача `Pipeline`, `Repository` в роуты.

**Не делает:**
- Не содержит логики пайплайна.
- Не общается с LLM или поиском.
- Не знает про домен глубже, чем DTO.

**Зависимости:** `pipeline`, `infrastructure.storage`,
`domain.enums` (для типов).

---

### `pipeline/` — оркестратор

**Ответственность:** управляет **порядком** шагов и состоянием
задачи.

**Что делает:**
- `Pipeline.run(task_id, inputText)` — главный метод.
- Вызывает шаги по порядку: extract → plausibility → search →
  rate → evidence → verdict → (условно) attributes → aggregate.
- Обновляет прогресс в БД.
- Обрабатывает ошибки: retry для transient, fail для permanent.
- Формирует финальный `FactCheckResult`.
- Работает **асинхронно** (в фоне).

**Не делает:**
- Не содержит алгоритмов шагов — только вызовы domain-функций.
- Не знает деталей LLM/поиска — работает через порты.

**Зависимости:** `domain.*`, `infrastructure.*`,
`infrastructure.storage`.

**Почему отдельный модуль:** единственное место, где определён
порядок шагов. Завтра добавим «проверку изображений» — правим
только здесь.

---

### `domain/` — чистая логика

**Ответственность:** правила фактчекинга. Ноль зависимостей от
FastAPI, LLM, БД, сети.

**Что делает:**
- `models.py` — сущности (`Claim`, `Source`, `MainCheck`,
  `FactCheckResult`, ...).
- `enums.py` — `Verdict`, `Plausibility`, `ClaimType`,
  `AttributeSignal`.
- `extractor.py` — разбивает текст на main + attributes + opinions.
- `plausibility.py` — оценка правдоподобности (промпт + парсинг).
- `query_builder.py` — формирование поисковых запросов (RU + EN).
- `source_rater.py` — whitelist доменов.
- `evidence_finder.py` — извлечение цитат.
- `verdict_maker.py` — **матрица вердиктов** (главное правило).
- `attribute_checker.py` — проверка одного атрибута.
- `aggregator.py` — финальная агрегация с учётом сигналов.
- `confidence.py` — расчёт уверенности.

**Не делает:**
- Не вызывает LLM напрямую.
- Не ходит в сеть.
- Не знает про БД.
- Не знает про HTTP.

**Зависимости:** только `domain.models`, `domain.enums`,
`domain.ports`.

**Почему отдельный слой:** тестируется **без LLM, без сети, без БД**.
LLM-вызовы передаются через **порты** (`ports.py`).

**Как работают порты:**

```python
# domain/ports.py
class LLMPort(Protocol):
    def complete(self, prompt: str) -> str: ...

class SearchPort(Protocol):
    def search(self, query: str) -> list[SearchResult]: ...
```

Домен зависит от **интерфейсов**, не от реализаций. Это DIP.

---

### `infrastructure/` — внешний мир

**Ответственность:** изолировать общение с LLM, поиском, БД, кэшем.

**Подмодули:**

#### `llm/`
- `client.py` — абстрактный `LLMClient` (соответствует `LLMPort`).
- `gigachat.py` — реализация через GigaChat API.
- `prompts.py` — **все промпты в одном месте**.

#### `search/`
- `client.py` — абстрактный `SearchClient`.
- `duckduckgo.py` — реализация.
- `wikipedia.py` — реализация.

#### `fetching/`
- `page_fetcher.py` — скачивает URL, извлекает текст
  (BeautifulSoup + trafilatura).

#### `storage/`
- `db.py` — подключение к SQLite.
- `models.py` — ORM-модели (**отдельно** от доменных!).
- `repositories.py` — методы `save_task`, `get_task`,
  `update_status`.

#### `cache/`
- `cache.py` — абстрактный `Cache`.
- `sqlite_cache.py` — реализация.

**Не делает:**
- Не содержит бизнес-правил.
- Не знает про пайплайн.

**Зависимости:** `domain.ports` (реализует интерфейсы), внешние
библиотеки (`requests`, `duckduckgo-search`, `sqlalchemy`).

---

### `config.py`

**Ответственность:** централизованные настройки.

- Читает `.env`.
- Валидирует обязательные переменные.
- Предоставляет типизированный доступ: `config.gigachat_api_key`,
  `config.database_url`.

---

## Frontend: структура

```
frontend/
├── src/
│   ├── main.ts                  ← точка входа
│   ├── App.vue                  ← корневой компонент
│   │
│   ├── api/                     ← клиент к backend
│   │   ├── client.ts            ← базовый HTTP-клиент
│   │   ├── check.ts             ← createCheck, getCheck
│   │   └── types.ts             ← DTO
│   │
│   ├── composables/             ← логика UI
│   │   ├── useCheck.ts          ← отправка, polling, состояние
│   │   └── useHistory.ts        ← (post-MVP)
│   │
│   ├── components/              ← UI-компоненты
│   │   ├── InputPanel.vue       ← ввод текста
│   │   ├── ProgressPanel.vue    ← прогресс-бар
│   │   ├── ResultPanel.vue      ← результат
│   │   ├── VerdictBadge.vue     ← вердикт (цвет + иконка)
│   │   ├── MainCheckCard.vue    ← одна проверка
│   │   ├── SourceList.vue       ← список источников
│   │   ├── AttributeList.vue    ← проверенные атрибуты
│   │   └── Disclaimer.vue       ← дисклеймер
│   │
│   ├── types/
│   │   └── ui.ts                ← типы UI
│   │
│   └── styles/
│       └── main.scss            ← общие стили
│
├── public/
├── index.html
├── vite.config.ts
├── tsconfig.json
└── package.json
```

---

## Frontend: ответственности

### `api/` — клиент к backend

**Ответственность:** HTTP-запросы, типы.

**Что делает:**
- `createCheck(text)` → `{ task_id }`.
- `getCheck(id)` → `{ status, result?, error? }`.
- Типы DTO.

**Не делает:**
- Не содержит логики UI.
- Не хранит состояние.

---

### `composables/` — логика UI

**Ответственность:** состояние и действия.

**`useCheck.ts`:**
- Хранит `inputText`, `taskId`, `status`, `progress`, `result`,
  `error`.
- `submit()` — отправляет текст.
- `poll()` — опрашивает сервер каждые 2 сек.
- Останавливает polling при `completed` / `failed`.

---

### `components/` — UI

**Ответственность:** отображение и ввод.

**Все компоненты тупые:**
- Получают данные через `props`.
- Эмитят события через `emits`.
- Не ходят в API.
- Не содержат логики проверки.

**Исключение:** `App.vue` — использует `useCheck`, раздаёт данные
в компоненты.

---

## Карта зависимостей

### Backend

```
api/routes.py
  ├──→ pipeline/orchestrator.py
  ├──→ infrastructure/storage/repositories.py
  └──→ api/schemas.py

pipeline/orchestrator.py
  ├──→ domain/extractor.py
  ├──→ domain/plausibility.py
  ├──→ domain/query_builder.py
  ├──→ domain/source_rater.py
  ├──→ domain/evidence_finder.py
  ├──→ domain/verdict_maker.py
  ├──→ domain/attribute_checker.py
  ├──→ domain/aggregator.py
  ├──→ infrastructure/llm/client.py
  ├──→ infrastructure/search/client.py
  └──→ infrastructure/storage/repositories.py

domain/*.py
  ├──→ domain/models.py
  ├──→ domain/enums.py
  └──→ domain/ports.py

infrastructure/*.py
  ├──→ domain/ports.py
  └──→ внешние библиотеки
```

**Проверка границ:**
- `domain/` не импортирует `fastapi`, `requests`, `sqlalchemy`,
  `duckduckgo`. ✅
- `domain/` не импортирует `infrastructure/`, `pipeline/`, `api/`. ✅
- `pipeline/` не импортирует `api/`. ✅

### Frontend

```
App.vue
  ├──→ composables/useCheck.ts
  └──→ components/*.vue

composables/useCheck.ts
  └──→ api/check.ts

api/check.ts
  └──→ api/client.ts, api/types.ts

components/*.vue
  ├──→ vue
  └──→ types/ui.ts
```

**Проверка границ:**
- `components/` не импортируют `api/`. ✅
- `components/` не импортируют `composables/` (кроме `App.vue`). ✅
- `api/` не импортирует `composables/` или `components/`. ✅

---

## Соответствие доменной модели

Каждый доменный модуль реализует **свои операции** из `DOMAIN.md`:

| Модуль | Операции |
|---|---|
| `extractor.py` | `extractClaims`, `extractEntities` |
| `plausibility.py` | `assessPlausibility` |
| `query_builder.py` | `buildQueries` |
| `source_rater.py` | `rateSource` |
| `evidence_finder.py` | `findEvidence` |
| `verdict_maker.py` | `decideVerdict` |
| `attribute_checker.py` | `checkAttribute` |
| `aggregator.py` | `aggregateVerdict`, `applyAttributeSignals` |
| `confidence.py` | `calculateConfidence` |

Пайплайн их вызывает по очереди, передавая данные через доменные
объекты.

---

## Что НЕ создаём

- **`services/`** — не нужен, всё в `domain/` или `pipeline/`.
- **`utils/`** — пока нет утилит вне домена.
- **`common/`** — преждевременно.
- **`shared/`** — нет общего кода между backend и frontend.
- **Абстрактный `BaseRepository`** — YAGNI, у нас один репозиторий.
- **`middleware/`** — не нужен в MVP.
- **`websockets/`** — не нужен, у нас polling.

---

## Принятые решения

1. **Backend разбит на `api / pipeline / domain / infrastructure`.**
   Классическая clean architecture.
2. **`pipeline/` — отдельный модуль**, не часть `api/`. Пайплайн —
   это логика, а не HTTP.
3. **Порты (`domain/ports.py`) — нужны.** Домен не знает про
   GigaChat, только про интерфейс `LLMPort`. DIP.
4. **Frontend разбит на `api / composables / components`.**
5. **DTO синхронизация — вручную** для MVP. OpenAPI — если проект
   вырастет.
6. **Тесты:** `domain/` — полное покрытие, `pipeline/` —
   smoke-тесты.

---

## История изменений

### 2026-09-25 (v1.0)
- Первая версия архитектуры.
- Разбиение backend: `api / pipeline / domain / infrastructure`.
- Разбиение frontend: `api / composables / components`.
- Порты в домене (DIP).
- Ручная синхронизация DTO.