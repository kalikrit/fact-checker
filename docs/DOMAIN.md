# Доменная модель

Сущности, поля, связи и операции Fact Checker. Словарь предметной
области. Ещё не код — только то, **что есть в мире задачи**.

Версия: 1.0
Дата: 2026-09-25

---

## Принципы

1. **Сущность описывает «что», а не «как».** Если это про реализацию —
   в инфраструктуру.
2. **Поле объясняется одной фразой на языке бизнеса.** Если нельзя —
   поля не должно быть.
3. **Типы — enum, а не boolean.** Категории важнее бинарности.
4. **Результат — массив `MainCheck`.** Один запрос → 1–3 проверки,
   каждая со своим вердиктом.

---

## Сущности

### 1. `CheckTask` — задача проверки

Описывает **один запрос пользователя** на проверку текста.

| Поле | Тип | Смысл |
|---|---|---|
| `id` | `string` | UUID задачи |
| `inputText` | `string` | Исходный текст (до 1000 символов) |
| `status` | `TaskStatus` | `pending` / `running` / `completed` / `failed` |
| `progress` | `TaskProgress \| null` | Текущий шаг и процент |
| `createdAt` | `number` | Момент создания (ms) |
| `startedAt` | `number \| null` | Момент старта обработки |
| `finishedAt` | `number \| null` | Момент завершения |
| `result` | `FactCheckResult \| null` | Результат (когда `completed`) |
| `error` | `TaskError \| null` | Ошибка (когда `failed`) |

**Замечания:**
- `id` — генерируется при создании задачи.
- `progress` — заполняется во время выполнения.
- `result` и `error` взаимоисключающие.
- Хранится в БД (SQLite). TTL — 30 дней.

---

### 2. `TaskStatus` — статус задачи

```
type TaskStatus = 'pending' | 'running' | 'completed' | 'failed';
```

---

### 3. `TaskProgress` — прогресс задачи

| Поле | Тип | Смысл |
|---|---|---|
| `step` | `PipelineStep` | Текущий шаг пайплайна |
| `stepIndex` | `number` | Номер шага (1..N) |
| `totalSteps` | `number` | Всего шагов |
| `percent` | `number` | 0..100 |
| `detail` | `string \| null` | Уточнение («поиск 2 из 3») |

---

### 4. `PipelineStep` — шаг пайплайна

```
type PipelineStep =
  | 'extract'
  | 'plausibility'
  | 'search'
  | 'rate_sources'
  | 'evidence'
  | 'verdict'
  | 'attributes'
  | 'aggregate';
```

Соответствует use cases UC-3 … UC-10.

---

### 5. `TaskError` — ошибка задачи

| Поле | Тип | Смысл |
|---|---|---|
| `kind` | `ErrorKind` | `transient` / `permanent` / `unknown` |
| `message` | `string` | Понятное пользователю сообщение |
| `technical` | `string \| null` | Технические детали (для логов) |
| `step` | `PipelineStep` | На каком шаге упало |

---

### 6. `ErrorKind` — тип ошибки

```
type ErrorKind = 'transient' | 'permanent' | 'unknown';
```

---

### 7. `FactCheckResult` — результат проверки

Верхнеуровневый контейнер. Содержит **1–3 проверки** (по числу main
в тексте) плюс общий дисклеймер.

| Поле | Тип | Смысл |
|---|---|---|
| `checks` | `MainCheck[]` | 1–3 независимые проверки |
| `disclaimer` | `string` | Общий дисклеймер |
| `checkedAt` | `number` | Когда завершена проверка (ms) |

---

### 8. `MainCheck` — проверка одного main-утверждения

Основная единица результата. Содержит вердикт и всё, на чём он основан.

| Поле | Тип | Смысл |
|---|---|---|
| `mainClaim` | `Claim` | Проверенное утверждение |
| `plausibility` | `Plausibility` | Оценка правдоподобности |
| `evidenceStrength` | `EvidenceStrength` | Сила доказательств |
| `verdict` | `Verdict` | Итоговый вердикт |
| `explanation` | `string` | Объяснение от LLM |
| `sources` | `Source[]` | Источники по main |
| `evidence` | `Evidence[]` | Цитаты, поддерживающие/опровергающие |
| `attributesChecked` | `boolean` | Проверялись ли атрибуты |
| `attributeChecks` | `AttributeCheck[]` | Результаты проверки атрибутов |
| `confidence` | `number` | 0..1 |

---

### 9. `Claim` — утверждение

| Поле | Тип | Смысл |
|---|---|---|
| `id` | `string` | UUID внутри результата |
| `text` | `string` | Текст утверждения |
| `type` | `ClaimType` | `main` / `attribute` / `opinion` |
| `parentId` | `string \| null` | Для attribute — id main |
| `entities` | `Entity[]` | Сущности внутри утверждения |

---

### 10. `ClaimType` — тип утверждения

```
type ClaimType = 'main' | 'attribute' | 'opinion';
```

---

### 11. `Entity` — сущность внутри утверждения

Имя, место, дата, организация, персонаж.

| Поле | Тип | Смысл |
|---|---|---|
| `text` | `string` | Как в тексте («Мадонна», «1947») |
| `kind` | `EntityKind` | Тип сущности |
| `role` | `string` | Роль в утверждении («организатор», «место») |

**Замечание:** `Entity` — это **извлечённая** сущность. Она ещё не
проверена. Расхождение между заявленным `kind` и реальностью
фиксируется в `AttributeCheck.note`, отдельного поля `actualKind` нет.

---

### 12. `EntityKind` — тип сущности

```
type EntityKind =
  | 'person'
  | 'place'
  | 'org'
  | 'date'
  | 'number'
  | 'character'
  | 'unknown';
```

`character` — персонаж книги/фильма (Рикки-тики-тави, Гарри Поттер).
Отличается от `person` (реальных людей).

---

### 13. `Plausibility` — правдоподобность

```
type Plausibility = 'high' | 'medium' | 'low';
```

---

### 14. `EvidenceStrength` — сила доказательств

```
type EvidenceStrength = 'strong' | 'weak' | 'none';
```

- `strong` — 2+ независимых источника.
- `weak` — 1 источник.
- `none` — 0 источников.

---

### 15. `Verdict` — вердикт

```
type Verdict =
  | 'true'
  | 'mostly_true'
  | 'misleading'
  | 'mostly_false'
  | 'false'
  | 'unknown'
  | 'contradictory';
```

Семь категорий. `unknown` и `false` — **разные** вещи.

---

### 16. `Source` — источник

| Поле | Тип | Смысл |
|---|---|---|
| `url` | `string` | Ссылка |
| `title` | `string` | Заголовок страницы |
| `snippet` | `string` | Краткое описание (из поиска) |
| `domain` | `string` | Домен (reuters.com) |
| `trust` | `SourceTrust` | Уровень доверия |
| `retrievedAt` | `number` | Когда скачали (ms) |

---

### 17. `SourceTrust` — доверие к источнику

```
type SourceTrust = 'high' | 'medium' | 'low' | 'unknown';
```

---

### 18. `Evidence` — доказательство

Фрагмент источника, подтверждающий или опровергающий утверждение.

| Поле | Тип | Смысл |
|---|---|---|
| `sourceUrl` | `string` | Ссылка на источник |
| `quote` | `string` | Цитата из текста |
| `relation` | `EvidenceRelation` | `supports` / `refutes` |
| `relevance` | `number` | 0..1, насколько релевантно |

**Замечание:** `Evidence` хранится отдельно от `Source`, потому что
источников может быть 10, а цитат из них — 3–5. Цитата привязана к
конкретному URL.

---

### 19. `EvidenceRelation` — отношение доказательства

```
type EvidenceRelation = 'supports' | 'refutes';
```

`neutral` — отфильтровывается на этапе пайплайна, в модель не попадает.

---

### 20. `AttributeCheck` — результат проверки атрибута

| Поле | Тип | Смысл |
|---|---|---|
| `attribute` | `Claim` | Сам атрибут |
| `signal` | `AttributeSignal` | Результат проверки |
| `evidence` | `Source[]` | Что нашли при поиске |
| `note` | `string \| null` | Пояснение («умер в 1947») |

---

### 21. `AttributeSignal` — сигнал атрибута

```
type AttributeSignal =
  | 'none'
  | 'fabricated'
  | 'distorted'
  | 'anachronistic'
  | 'type_mismatch'
  | 'improbable'
  | 'unverifiable';
```

---

## Связи между сущностями

```
CheckTask
  ├── inputText: string
  ├── status: TaskStatus
  ├── progress: TaskProgress ─── step: PipelineStep
  ├── error: TaskError ─── kind: ErrorKind
  └── result: FactCheckResult
        │
        ├── checks: MainCheck[]  (1–3)
        │     │
        │     ├── mainClaim: Claim ─── entities: Entity[]
        │     │                       └── type: ClaimType
        │     │                       └── attributes (через parentId)
        │     │
        │     ├── plausibility: Plausibility
        │     ├── evidenceStrength: EvidenceStrength
        │     ├── verdict: Verdict
        │     ├── explanation: string
        │     ├── sources: Source[] ─── trust: SourceTrust
        │     ├── evidence: Evidence[] ─── sourceUrl → Source.url
        │     │                            └── relation: EvidenceRelation
        │     │
        │     ├── attributesChecked: boolean
        │     └── attributeChecks: AttributeCheck[]
        │           ├── attribute: Claim
        │           ├── signal: AttributeSignal
        │           └── evidence: Source[]
        │
        └── disclaimer: string
        └── checkedAt: number
```

**Ключевые связи:**

- **`CheckTask 1 → 1 FactCheckResult`** — у задачи один результат.
- **`FactCheckResult 1 → N MainCheck`** — 1–3 независимых проверки.
- **`MainCheck 1 → 1 Claim (main)`** — одно главное утверждение.
- **`Claim 1 → N Entity`** — внутри утверждения сущности.
- **`Claim (main) 1 → N Claim (attribute)`** — через `parentId`.
- **`MainCheck 1 → N Source`** — источники по main.
- **`MainCheck 1 → N Evidence`** — цитаты (ссылаются на `Source.url`).
- **`MainCheck 1 → N AttributeCheck`** — если атрибуты проверялись.

---

## Доменные операции

Что система умеет делать с моделью. Без сигнатур — только смысл.

### Управление задачами

| Операция | Что делает |
|---|---|
| `createTask(inputText)` | Создаёт задачу со статусом `pending` |
| `startTask(task)` | Переводит в `running`, фиксирует `startedAt` |
| `updateProgress(task, step, percent, detail)` | Обновляет прогресс |
| `completeTask(task, result)` | Переводит в `completed`, сохраняет результат |
| `failTask(task, error)` | Переводит в `failed`, сохраняет ошибку |

### Пайплайн (по шагам)

| Операция | Что делает |
|---|---|
| `extractClaims(text)` | Разбивает текст на main + attributes + opinions |
| `extractEntities(claim)` | Извлекает сущности из утверждения |
| `assessPlausibility(main)` | Оценивает правдоподобность |
| `buildQueries(main)` | Формирует поисковые запросы (RU + EN) |
| `rateSource(source)` | Определяет trust |
| `findEvidence(main, sources)` | Ищет доказательства |
| `decideVerdict(plausibility, evidence)` | Применяет матрицу вердиктов |
| `checkAttribute(attribute)` | Проверяет один атрибут |
| `aggregateVerdict(check)` | Финальная агрегация с учётом атрибутов |

### Вспомогательные

| Операция | Что делает |
|---|---|
| `calculateConfidence(check)` | Считает `confidence` (0..1) |
| `applyAttributeSignals(check)` | Понижает вердикт до `misleading` при сигналах |
| `isVerdictConfirmed(verdict)` | `true` для `true` / `mostly_true` |

---

## Что НЕ входит в модель (MVP)

- **Пользователь** — нет авторизации, нет сессий.
- **История** — задача хранится, но нет списка «мои проверки».
- **Обратная связь** — нет отметок «вердикт неверный».
- **Настройки** — язык, провайдер LLM — всё в конфиге, не в модели.
- **Кэш** — это инфраструктура, не домен.
- **LLM-промпты** — инфраструктура.
- **Поисковые запросы** — инфраструктура.
- **HTTP-запросы** — инфраструктура.

**Правило:** если сущность описывает **как** что-то делается (а не
**что** делается) — она в инфраструктуре, а не в домене.

---

## Принятые решения

1. **`FactCheckResult` — массив `MainCheck`.** Один запрос → 1–3
   независимых проверки. Каждая со своим вердиктом.
2. **`Evidence` — отдельная сущность.** Прозрачность: пользователь
   видит конкретные цитаты из источников.
3. **`Entity` без `actualKind`.** Расхождение типа фиксируется в
   `AttributeCheck.note`.
4. **`CheckTask` хранится в БД.** TTL — 30 дней.
5. **`confidence` — 0..1.** Точная формула — на этапе реализации.
6. **`neutral` evidence не попадает в модель.** Отфильтровывается на
   этапе пайплайна.

---

## История изменений

### 2026-09-25 (v1.0)
- Первая версия доменной модели.
- Ключевые решения:
  - массив `MainCheck` вместо одного вердикта;
  - `Evidence` как отдельная сущность;
  - `Entity` без `actualKind`;
  - хранение задач в БД с TTL 30 дней.