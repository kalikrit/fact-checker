from .models import Claim, Source, Evidence
from .ports import LLMPort


def find_evidence(
    main: Claim,
    sources: list[Source],
    source_texts: dict[str, str],  # url → текст
    llm: LLMPort,
) -> list[Evidence]:
    """
    Найти цитаты, поддерживающие или опровергающие main.
    source_texts — уже скачанные тексты страниц.
    """
    ...


def calculate_evidence_strength(evidence: list[Evidence]) -> EvidenceStrength:
    """
    Определить силу доказательств.
    strong = 2+ независимых источника; weak = 1; none = 0.
    """
    ...