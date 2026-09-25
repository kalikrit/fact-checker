from .models import Claim


def build_queries(main: Claim) -> list[str]:
    """
    Сформировать 2-3 поисковых запроса (RU + EN).
    Без LLM: работает на основе текста main и entities.
    """
    ...