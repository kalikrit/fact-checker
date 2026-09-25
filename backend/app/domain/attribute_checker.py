from .models import Claim, AttributeCheck
from .ports import LLMPort, SearchPort, PageFetcherPort


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