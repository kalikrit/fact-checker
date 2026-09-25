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