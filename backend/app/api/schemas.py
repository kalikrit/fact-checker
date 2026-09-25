from pydantic import BaseModel, Field
from domain.enums import (
    TaskStatus, PipelineStep, ClaimType, EntityKind,
    Plausibility, EvidenceStrength, Verdict, SourceTrust,
    EvidenceRelation, AttributeSignal,
)


# === Запросы ===

class CheckRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=1000)


# === Ответы ===

class TaskProgressDTO(BaseModel):
    step: PipelineStep
    step_index: int
    total_steps: int
    percent: int
    detail: str | None


class TaskErrorDTO(BaseModel):
    kind: str
    message: str
    step: PipelineStep | None


class EntityDTO(BaseModel):
    text: str
    kind: EntityKind
    role: str


class ClaimDTO(BaseModel):
    id: str
    text: str
    type: ClaimType
    parent_id: str | None
    entities: list[EntityDTO]


class SourceDTO(BaseModel):
    url: str
    title: str
    snippet: str
    domain: str
    trust: SourceTrust
    retrieved_at: int


class EvidenceDTO(BaseModel):
    source_url: str
    quote: str
    relation: EvidenceRelation
    relevance: float


class AttributeCheckDTO(BaseModel):
    attribute: ClaimDTO
    signal: AttributeSignal
    evidence: list[SourceDTO]
    note: str | None


class MainCheckDTO(BaseModel):
    main_claim: ClaimDTO
    plausibility: Plausibility
    evidence_strength: EvidenceStrength
    verdict: Verdict
    explanation: str
    sources: list[SourceDTO]
    evidence: list[EvidenceDTO]
    attributes_checked: bool
    attribute_checks: list[AttributeCheckDTO]
    confidence: float


class FactCheckResultDTO(BaseModel):
    checks: list[MainCheckDTO]
    disclaimer: str
    checked_at: int


class CheckCreatedResponse(BaseModel):
    task_id: str
    status: TaskStatus


class CheckStatusResponse(BaseModel):
    task_id: str
    status: TaskStatus
    progress: TaskProgressDTO | None = None
    result: FactCheckResultDTO | None = None
    error: TaskErrorDTO | None = None