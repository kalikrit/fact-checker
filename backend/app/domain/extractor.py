from .models import Claim
from .ports import LLMPort


def extract_claims(text: str, llm: LLMPort) -> list[Claim]:
    """
    Разбить текст на утверждения.
    Возвращает список Claim: 1-3 main + attributes + opinions.
    """
    ...


def extract_entities(claim: Claim, llm: LLMPort) -> list[Entity]:
    """
    Извлечь сущности из утверждения.
    Возвращает обновлённый Claim с заполненными entities.
    """
    ...