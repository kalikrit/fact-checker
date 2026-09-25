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
    retrieved_at: int  # ms


@dataclass
class Evidence:
    source_url: str
    quote: str
    relation: EvidenceRelation
    relevance: float  # 0..1


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
    confidence: float = 0.0  # 0..1


@dataclass
class FactCheckResult:
    checks: list[MainCheck]
    disclaimer: str
    checked_at: int  # ms


@dataclass
class CheckTask:
    id: str
    input_text: str
    status: TaskStatus
    created_at: int  # ms
    progress: TaskProgress | None = None
    started_at: int | None = None
    finished_at: int | None = None
    result: FactCheckResult | None = None
    error: TaskError | None = None