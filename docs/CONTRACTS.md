# Контракты модулей

Сигнатуры функций и классов — без реализации. Договор между модулями.
После этого документа можно писать тела.

Версия: 1.0
Дата: 2026-09-25

---

## Принятые решения

1. **Пайплайн — синхронный.** Запускается в фоне через
   `ThreadPoolExecutor` (или `BackgroundTasks` FastAPI). GigaChat SDK и
   `duckduckgo-search` — синхронные, async усложнит MVP.
2. **`TaskRepository` — синхронный.** SQLite с
   `check_same_thread=False`. Потокобезопасность — через блокировки
   или отдельное соединение на поток.
3. **Маппинг DTO — в `api/mappers.py`.** Отдельный модуль, чтобы
   `routes.py` был тонким.
4. **`assess_plausibility` возвращает `(Plausibility, str)`** — оценка
   + объяснение. Отдельной `explain_*` нет.
5. **`extract_entities(claim, llm) → Claim`** — принимает Claim,
   возвращает Claim с заполненными entities.
6. **Промпты — в `infrastructure/llm/prompts.py`.** Единое место.
7. **Wikipedia — отдельный клиент** `infrastructure/search/wikipedia.py`.
8. **`page_fetcher` и `cache` — реализуются**, как описано в
   ARCHITECTURE.md.

---

## 1. `domain/enums.py`

```python
from enum import Enum


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class PipelineStep(str, Enum):
    EXTRACT = "extract"
    PLAUSIBILITY = "plausibility"
    SEARCH = "search"
    RATE_SOURCES = "rate_sources"
    EVIDENCE = "evidence"
    VERDICT = "verdict"
    ATTRIBUTES = "attributes"
    AGGREGATE = "aggregate"


class ErrorKind(str, Enum):
    TRANSIENT = "transient"
    PERMANENT = "permanent"
    UNKNOWN = "unknown"


class ClaimType(str, Enum):
    MAIN = "main"
    ATTRIBUTE = "attribute"
    OPINION = "opinion"


class EntityKind(str, Enum):
    PERSON = "person"
    PLACE = "place"
    ORG = "org"
    DATE = "date"
    NUMBER = "number"
    CHARACTER = "character"
    UNKNOWN = "unknown"


class Plausibility(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class EvidenceStrength(str, Enum):
    STRONG = "strong"
    WEAK = "weak"
    NONE = "none"


class Verdict(str, Enum):
    TRUE = "true"
    MOSTLY_TRUE = "mostly_true"
    MISLEADING = "misleading"
    MOSTLY_FALSE = "mostly_false"
    FALSE = "false"
    UNKNOWN = "unknown"
    CONTRADICTORY = "contradictory"


class SourceTrust(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


class EvidenceRelation(str, Enum):
    SUPPORTS = "supports"
    REFUTES = "refutes"


class AttributeSignal(str, Enum):
    NONE = "none"
    FABRICATED = "fabricated"
    DISTORTED = "distorted"
    ANACHRONISTIC = "anachronistic"
    TYPE_MISMATCH = "type_mismatch"
    IMPROBABLE = "improbable"
    UNVERIFIABLE = "unverifiable"