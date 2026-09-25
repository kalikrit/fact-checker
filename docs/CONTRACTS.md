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
```

---

## 2. `domain/models.py`

```python
from dataclasses import dataclass, field

from .enums import (
    TaskStatus, PipelineStep, ErrorKind,
    ClaimType, EntityKind,
    Plausibility, EvidenceStrength, Verdict,
    SourceTrust, EvidenceRelation, AttributeSignal,
)


# === Задача ===

@dataclass
class TaskProgress:
    step: PipelineStep
    step_index: int
    total_steps: int
    percent: int
    detail: str | None = None


@dataclass
class TaskError:
    kind: ErrorKind
    message: str
    technical: str | None = None
    step: PipelineStep | None = None


# === Утверждения и сущности ===

@dataclass
class Entity:
    text: str
    kind: EntityKind
    role: str


@dataclass
class Claim:
    id: str
    text: str
    type: ClaimType
    parent_id: str | None = None
    entities: list[Entity] = field(default_factory=list)


# === Источники и доказательства ===

@dataclass
class Source:
    url: str
    title: str
    snippet: str
    domain: str
    trust: SourceTrust
    retrieved_at: int


@dataclass
class Evidence:
    source_url: str
    quote: str
    relation: EvidenceRelation
    relevance: float


# === Проверка ===

@dataclass
class AttributeCheck:
    attribute: Claim
    signal: AttributeSignal
    evidence: list[Source] = field(default_factory=list)
    note: str | None = None


@dataclass
class MainCheck:
    main_claim: Claim
    plausibility: Plausibility
    evidence_strength: EvidenceStrength
    verdict: Verdict
    explanation: str
    sources: list[Source] = field(default_factory=list)
    evidence: list[Evidence] = field(default_factory=list)
    attributes_checked: bool = False
    attribute_checks: list[AttributeCheck] = field(default_factory=list)
    confidence: float = 0.0


@dataclass
class FactCheckResult:
    checks: list[MainCheck]
    disclaimer: str
    checked_at: int


@dataclass
class CheckTask:
    id: str
    input_text: str
    status: TaskStatus
    created_at: int
    progress: TaskProgress | None = None
    started_at: int | None = None
    finished_at: int | None = None
    result: FactCheckResult | None = None
    error: TaskError | None = None
```

---

## 3. `domain/ports.py`

```python
from dataclasses import dataclass
from typing import Protocol


# === Результаты ===

@dataclass
class SearchResult:
    url: str
    title: str
    snippet: str


# === Исключения ===

class DomainError(Exception):
    """Базовое исключение домена."""


class LLMParseError(DomainError):
    """LLM вернула невалидный ответ."""


class FetchError(DomainError):
    """Не удалось скачать страницу."""


class SearchError(DomainError):
    """Поиск не сработал."""


# === Порты ===

class LLMPort(Protocol):
    def complete(self, prompt: str, *, temperature: float = 0.0) -> str:
        """Отправить промпт, получить ответ."""
        ...

    def complete_json(self, prompt: str, *, temperature: float = 0.0) -> dict:
        """Отправить промпт, получить JSON. Бросает LLMParseError."""
        ...


class SearchPort(Protocol):
    def search(self, query: str, *, limit: int = 10) -> list[SearchResult]:
        """Выполнить поисковый запрос."""
        ...


class PageFetcherPort(Protocol):
    def fetch_text(self, url: str) -> str:
        """Скачать URL и извлечь основной текст. Бросает FetchError."""
        ...
```

---

## 4. Функции домена

### 4.1. `domain/extractor.py`

```python
from .models import Claim
from .ports import LLMPort


def extract_claims(text: str, llm: LLMPort) -> list[Claim]:
    """
    Разбить текст на утверждения.
    Возвращает список Claim: 1-3 main + attributes + opinions.
    При ошибке LLM — бросает LLMParseError.
    """
    ...


def extract_entities(claim: Claim, llm: LLMPort) -> Claim:
    """
    Извлечь сущности из утверждения.
    Возвращает Claim с заполненным полем entities.
    """
    ...


def filter_main_claims(claims: list[Claim], *, limit: int = 3) -> list[Claim]:
    """
    Оставить до limit main-утверждений.
    Остальные → attributes (если привязаны) или отбрасываются.
    """
    ...


def get_attributes(main: Claim, all_claims: list[Claim]) -> list[Claim]:
    """
    Вернуть attributes, привязанные к main (по parent_id).
    """
    ...
```

### 4.2. `domain/plausibility.py`

```python
from .enums import Plausibility
from .models import Claim
from .ports import LLMPort


def assess_plausibility(
    main: Claim,
    context: str,
    llm: LLMPort,
) -> tuple[Plausibility, str]:
    """
    Оценить правдоподобность main.
    Возвращает (оценка, объяснение).
    """
    ...
```

### 4.3. `domain/query_builder.py`

```python
from .models import Claim


def build_queries(main: Claim) -> list[str]:
    """
    Сформировать 2-3 поисковых запроса (RU + EN).
    Без LLM: работает на основе текста main и entities.
    """
    ...
```

### 4.4. `domain/source_rater.py`

```python
from .enums import SourceTrust
from .models import Source
from .ports import LLMPort


def rate_source_by_domain(domain: str) -> SourceTrust:
    """
    Определить trust по whitelist.
    Возвращает UNKNOWN, если домен не в списке.
    """
    ...


def rate_sources(sources: list[Source], llm: LLMPort) -> list[Source]:
    """
    Проставить trust всем источникам.
    Whitelist → LLM для неизвестных.
    Возвращает новый список с заполненным trust.
    """
    ...
```

### 4.5. `domain/evidence_finder.py`

```python
from .enums import EvidenceStrength
from .models import Claim, Evidence, Source
from .ports import LLMPort


def find_evidence(
    main: Claim,
    sources: list[Source],
    source_texts: dict[str, str],
    llm: LLMPort,
) -> list[Evidence]:
    """
    Найти цитаты, поддерживающие или опровергающие main.
    source_texts — url → текст страницы.
    """
    ...


def calculate_evidence_strength(evidence: list[Evidence]) -> EvidenceStrength:
    """
    strong = 2+ независимых источника.
    weak = 1.
    none = 0.
    Учитывает source_url и relation.
    """
    ...
```

### 4.6. `domain/verdict_maker.py`

```python
from .enums import EvidenceStrength, Plausibility, Verdict
from .models import Claim, Evidence
from .ports import LLMPort


def decide_verdict(
    plausibility: Plausibility,
    evidence_strength: EvidenceStrength,
) -> Verdict:
    """
    Применить матрицу вердиктов (MODEL.md, раздел 6).
    Чистая функция — без LLM.
    """
    ...


def explain_verdict(
    main: Claim,
    verdict: Verdict,
    evidence: list[Evidence],
    llm: LLMPort,
) -> str:
    """
    Сформировать объяснение вердикта.
    """
    ...
```

### 4.7. `domain/attribute_checker.py`

```python
from .models import AttributeCheck, Claim
from .ports import LLMPort, PageFetcherPort, SearchPort


def check_attribute(
    attribute: Claim,
    main: Claim,
    llm: LLMPort,
    search: SearchPort,
    fetcher: PageFetcherPort,
) -> AttributeCheck:
    """
    Проверить один атрибут.
    Возвращает AttributeCheck с сигналом.
    """
    ...


def check_attributes(
    attributes: list[Claim],
    main: Claim,
    llm: LLMPort,
    search: SearchPort,
    fetcher: PageFetcherPort,
    *,
    limit: int = 5,
) -> list[AttributeCheck]:
    """
    Проверить список атрибутов (до limit).
    """
    ...
```

### 4.8. `domain/aggregator.py`

```python
from .enums import Verdict
from .models import FactCheckResult, MainCheck


def apply_attribute_signals(check: MainCheck) -> MainCheck:
    """
    Понизить вердикт до misleading, если есть сигналы
    fabricated / distorted / anachronistic / type_mismatch.
    Чистая функция.
    """
    ...


def aggregate_verdict(check: MainCheck) -> MainCheck:
    """
    Финальная агрегация: применяет сигналы, возвращает обновлённый MainCheck.
    """
    ...


def is_verdict_confirmed(verdict: Verdict) -> bool:
    """
    True для true / mostly_true.
    Используется для решения о проверке атрибутов.
    """
    ...


def build_result(
    checks: list[MainCheck],
    checked_at: int,
) -> FactCheckResult:
    """
    Собрать финальный результат + дисклеймер.
    """
    ...
```

### 4.9. `domain/confidence.py`

```python
from .models import MainCheck


def calculate_confidence(check: MainCheck) -> float:
    """
    Оценка уверенности 0..1.
    Учитывает evidence_strength, plausibility, сигналы атрибутов.
    """
    ...
```

---

## 5. `pipeline/`

### 5.1. `pipeline/steps.py`

```python
from domain.enums import PipelineStep


# Порядок шагов пайплайна и их человекочитаемые названия.
STEP_ORDER: list[PipelineStep] = [
    PipelineStep.EXTRACT,
    PipelineStep.PLAUSIBILITY,
    PipelineStep.SEARCH,
    PipelineStep.RATE_SOURCES,
    PipelineStep.EVIDENCE,
    PipelineStep.VERDICT,
    PipelineStep.ATTRIBUTES,
    PipelineStep.AGGREGATE,
]

STEP_LABELS: dict[PipelineStep, str] = {
    PipelineStep.EXTRACT: "Извлечение фактов",
    PipelineStep.PLAUSIBILITY: "Оценка правдоподобности",
    PipelineStep.SEARCH: "Поиск источников",
    PipelineStep.RATE_SOURCES: "Оценка надёжности источников",
    PipelineStep.EVIDENCE: "Анализ доказательств",
    PipelineStep.VERDICT: "Формирование вердикта",
    PipelineStep.ATTRIBUTES: "Проверка деталей",
    PipelineStep.AGGREGATE: "Агрегация результата",
}

TOTAL_STEPS = len(STEP_ORDER)
```

### 5.2. `pipeline/errors.py`

```python
from domain.enums import ErrorKind
from domain.ports import DomainError


class TaskFailedError(Exception):
    """Permanent ошибка — пайплайн останавливается."""

    def __init__(
        self,
        step: str,
        message: str,
        technical: str | None = None,
    ):
        ...


def classify_error(exc: Exception) -> ErrorKind:
    """
    Классифицировать ошибку: transient / permanent / unknown.
    Сетевые и таймауты → transient. LLMParseError → permanent.
    """
    ...


def retry_on_transient(fn, *, max_attempts: int = 3):
    """
    Декоратор: retry при transient ошибках с экспоненциальной задержкой.
    """
    ...
```

### 5.3. `pipeline/orchestrator.py`

```python
from domain.enums import Plausibility, Verdict
from domain.models import (
    AttributeCheck, CheckTask, Claim, Evidence, FactCheckResult, Source,
)
from domain.ports import LLMPort, PageFetcherPort, SearchPort


class Pipeline:
    def __init__(
        self,
        llm: LLMPort,
        search: SearchPort,
        fetcher: PageFetcherPort,
        repository: "TaskRepository",
    ):
        ...

    def run(self, task_id: str, input_text: str) -> FactCheckResult:
        """
        Главный метод. Синхронный.
        Обновляет статус и прогресс через repository.
        Бросает TaskFailedError при permanent ошибке.
        """
        ...

    # === Приватные шаги ===

    def _extract(self, text: str) -> list[Claim]:
        ...

    def _assess_plausibility(
        self, main: Claim, text: str,
    ) -> tuple[Plausibility, str]:
        ...

    def _search_and_fetch(
        self, main: Claim,
    ) -> tuple[list[Source], dict[str, str]]:
        ...

    def _rate_sources(self, sources: list[Source]) -> list[Source]:
        ...

    def _find_evidence(
        self,
        main: Claim,
        sources: list[Source],
        texts: dict[str, str],
    ) -> list[Evidence]:
        ...

    def _decide_verdict(self, main: Claim, evidence: list[Evidence]) -> Verdict:
        ...

    def _check_attributes_if_needed(
        self,
        main: Claim,
        attributes: list[Claim],
        verdict: Verdict,
    ) -> list[AttributeCheck]:
        ...
```

---

## 6. `infrastructure/llm/`

### 6.1. `infrastructure/llm/client.py`

```python
from abc import ABC, abstractmethod


class LLMClient(ABC):
    """Базовый класс LLM-клиента. Реализует LLMPort."""

    @abstractmethod
    def complete(self, prompt: str, *, temperature: float = 0.0) -> str:
        ...

    @abstractmethod
    def complete_json(
        self, prompt: str, *, temperature: float = 0.0,
    ) -> dict:
        ...
```

### 6.2. `infrastructure/llm/gigachat.py`

```python
from .client import LLMClient


class GigaChatClient(LLMClient):
    def __init__(self, api_key: str, base_url: str, model: str = "GigaChat"):
        ...

    def complete(self, prompt: str, *, temperature: float = 0.0) -> str:
        ...

    def complete_json(
        self, prompt: str, *, temperature: float = 0.0,
    ) -> dict:
        ...
```

### 6.3. `infrastructure/llm/prompts.py`

```python
"""Все промпты в одном месте. Легко менять и версионировать."""


EXTRACT_CLAIMS_PROMPT = """
... (полный текст промпта для извлечения утверждений)
"""


ASSESS_PLAUSIBILITY_PROMPT = """
... (полный текст промпта для оценки правдоподобности)
"""


EXTRACT_ENTITIES_PROMPT = """
... (промпт для извлечения сущностей)
"""


FIND_EVIDENCE_PROMPT = """
... (промпт для поиска цитат)
"""


EXPLAIN_VERDICT_PROMPT = """
... (промпт для объяснения вердикта)
"""


CHECK_ATTRIBUTE_PROMPT = """
... (промпт для проверки одного атрибута)
"""
```

---

## 7. `infrastructure/search/`

### 7.1. `infrastructure/search/client.py`

```python
from abc import ABC, abstractmethod

from domain.ports import SearchResult


class SearchClient(ABC):
    @abstractmethod
    def search(self, query: str, *, limit: int = 10) -> list[SearchResult]:
        ...
```

### 7.2. `infrastructure/search/duckduckgo.py`

```python
from .client import SearchClient
from domain.ports import SearchResult


class DuckDuckGoClient(SearchClient):
    def search(self, query: str, *, limit: int = 10) -> list[SearchResult]:
        ...
```

### 7.3. `infrastructure/search/wikipedia.py`

```python
from .client import SearchClient
from domain.ports import SearchResult


class WikipediaClient(SearchClient):
    def search(self, query: str, *, limit: int = 10) -> list[SearchResult]:
        ...
```

---

## 8. `infrastructure/fetching/page_fetcher.py`

```python
class PageFetcher:
    """Скачивает URL, извлекает основной текст. Реализует PageFetcherPort."""

    def __init__(self, *, timeout: float = 10.0, user_agent: str | None = None):
        ...

    def fetch_text(self, url: str) -> str:
        """
        Скачать URL и извлечь основной текст.
        Бросает FetchError при ошибке или пустом тексте.
        """
        ...
```

---

## 9. `infrastructure/storage/`

### 9.1. `infrastructure/storage/db.py`

```python
import sqlite3


def create_connection(db_path: str) -> sqlite3.Connection:
    """
    Создать соединение с SQLite.
    check_same_thread=False для использования из фоновых потоков.
    """
    ...


def init_schema(conn: sqlite3.Connection) -> None:
    """Создать таблицы, если их нет."""
    ...
```

### 9.2. `infrastructure/storage/repositories.py`

```python
from domain.models import (
    CheckTask, FactCheckResult, TaskError, TaskProgress,
)


class TaskRepository:
    def __init__(self, conn: "sqlite3.Connection"):
        ...

    def save_task(self, task: CheckTask) -> None:
        ...

    def get_task(self, task_id: str) -> CheckTask | None:
        ...

    def update_status(self, task_id: str, status: str) -> None:
        ...

    def update_progress(
        self, task_id: str, progress: TaskProgress,
    ) -> None:
        ...

    def complete_task(
        self, task_id: str, result: FactCheckResult,
    ) -> None:
        ...

    def fail_task(self, task_id: str, error: TaskError) -> None:
        ...

    def delete_older_than(self, days: int) -> int:
        """Удалить задачи старше N дней. Возвращает количество удалённых."""
        ...
```

### 9.3. `infrastructure/storage/models.py`

```python
"""
ORM-модели, отдельные от доменных.
Содержит только описания таблиц и маппинг domain ↔ БД.
"""
```

---

## 10. `infrastructure/cache/`

### 10.1. `infrastructure/cache/cache.py`

```python
from abc import ABC, abstractmethod


class Cache(ABC):
    @abstractmethod
    def get(self, key: str) -> str | None:
        ...

    @abstractmethod
    def set(self, key: str, value: str, *, ttl_seconds: int) -> None:
        ...

    @abstractmethod
    def clear_expired(self) -> int:
        ...
```

### 10.2. `infrastructure/cache/sqlite_cache.py`

```python
from .cache import Cache


class SqliteCache(Cache):
    def __init__(self, conn: "sqlite3.Connection", namespace: str):
        ...

    def get(self, key: str) -> str | None:
        ...

    def set(self, key: str, value: str, *, ttl_seconds: int) -> None:
        ...

    def clear_expired(self) -> int:
        ...
```

---

## 11. `api/`

### 11.1. `api/schemas.py`

Pydantic-схемы. См. полное описание в предыдущем сообщении
(раздел 9 «Шаг 4»). Дублировать здесь не будем.

### 11.2. `api/mappers.py`

```python
"""Маппинг domain dataclass ↔ Pydantic DTO."""

from domain.models import (
    AttributeCheck, Claim, Entity, Evidence, FactCheckResult, MainCheck, Source,
)
from .schemas import (
    AttributeCheckDTO, ClaimDTO, EntityDTO, EvidenceDTO,
    FactCheckResultDTO, MainCheckDTO, SourceDTO,
)


def to_entity_dto(entity: Entity) -> EntityDTO:
    ...


def to_claim_dto(claim: Claim) -> ClaimDTO:
    ...


def to_source_dto(source: Source) -> SourceDTO:
    ...


def to_evidence_dto(evidence: Evidence) -> EvidenceDTO:
    ...


def to_attribute_check_dto(check: AttributeCheck) -> AttributeCheckDTO:
    ...


def to_main_check_dto(check: MainCheck) -> MainCheckDTO:
    ...


def to_result_dto(result: FactCheckResult) -> FactCheckResultDTO:
    ...
```

### 11.3. `api/dependencies.py`

```python
from fastapi import Request
from infrastructure.storage.repositories import TaskRepository
from pipeline.orchestrator import Pipeline


def get_repository(request: Request) -> TaskRepository:
    """Получить репозиторий из app.state."""
    ...


def get_pipeline(request: Request) -> Pipeline:
    """Получить пайплайн из app.state."""
    ...
```

### 11.4. `api/routes.py`

```python
from fastapi import APIRouter, Depends, HTTPException

from pipeline.orchestrator import Pipeline
from infrastructure.storage.repositories import TaskRepository

from .schemas import (
    CheckCreatedResponse, CheckRequest, CheckStatusResponse,
)


router = APIRouter(prefix="/api", tags=["check"])


@router.post("/check", response_model=CheckCreatedResponse, status_code=202)
def create_check(
    request: CheckRequest,
    pipeline: Pipeline = Depends(get_pipeline),
    repo: TaskRepository = Depends(get_repository),
) -> CheckCreatedResponse:
    """Создать задачу проверки. Пайплайн запускается в фоне."""
    ...


@router.get("/check/{task_id}", response_model=CheckStatusResponse)
def get_check(
    task_id: str,
    repo: TaskRepository = Depends(get_repository),
) -> CheckStatusResponse:
    """Получить статус задачи и результат."""
    ...


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}
```

---

## 12. `config.py`

```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    gigachat_api_key: str
    gigachat_base_url: str = "https://gigachat.devices.sberbank.ru/api/v1"
    gigachat_model: str = "GigaChat"

    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    log_level: str = "INFO"

    database_url: str = "sqlite:///./data/fact_checker.db"

    cache_enabled: bool = True
    cache_ttl_seconds: int = 86400

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
```

---

## 13. `main.py`

```python
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Инициализация БД, кэша, LLM, поиска, пайплайна
    # Сохранение в app.state
    yield
    # Очистка


app = FastAPI(title="Fact Checker", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # для MVP
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
```

---

## Frontend

### 14. `src/api/types.ts`

См. полное описание в предыдущем сообщении (раздел 11).
Дублировать не будем.

### 15. `src/api/client.ts`

```ts
const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

export async function request<T>(
  path: string,
  options?: RequestInit,
): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!response.ok) {
    throw new Error(`Ошибка запроса: ${response.status}`);
  }
  return response.json();
}
```

### 16. `src/api/check.ts`

```ts
import { request } from './client';
import type { CheckCreatedResponse, CheckStatusResponse } from './types';

export async function createCheck(text: string): Promise<CheckCreatedResponse> {
  return request<CheckCreatedResponse>('/api/check', {
    method: 'POST',
    body: JSON.stringify({ text }),
  });
}

export async function getCheck(taskId: string): Promise<CheckStatusResponse> {
  return request<CheckStatusResponse>(`/api/check/${taskId}`);
}
```

### 17. `src/composables/useCheck.ts`

```ts
import { computed, ref } from 'vue';
import type { ComputedRef, Ref } from 'vue';

import { createCheck, getCheck } from '@/api/check';
import type {
  FactCheckResult, TaskError, TaskProgress, TaskStatus,
} from '@/api/types';

const POLL_INTERVAL_MS = 2000;

export interface UseCheckReturn {
  inputText: Ref<string>;
  taskId: Ref<string | null>;
  status: Ref<TaskStatus | null>;
  progress: Ref<TaskProgress | null>;
  result: Ref<FactCheckResult | null>;
  error: Ref<TaskError | null>;
  isRunning: ComputedRef<boolean>;

  submit: () => Promise<void>;
  cancel: () => void;
  reset: () => void;
}

export function useCheck(): UseCheckReturn {
  ...
}
