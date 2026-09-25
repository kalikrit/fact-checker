from .models import Source
from .enums import SourceTrust
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
    """
    ...