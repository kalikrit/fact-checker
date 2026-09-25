from .enums import Plausibility, EvidenceStrength, Verdict
from .models import Claim
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