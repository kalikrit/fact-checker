from typing import Protocol
from dataclasses import dataclass


@dataclass
class SearchResult:
    """Результат одного поискового запроса."""
    url: str
    title: str
    snippet: str


class LLMPort(Protocol):
    """Интерфейс LLM. Домен не знает, GigaChat это или Ollama."""

    def complete(self, prompt: str, *, temperature: float = 0.0) -> str:
        """Отправить промпт, получить ответ."""
        ...

    def complete_json(self, prompt: str, *, temperature: float = 0.0) -> dict:
        """Отправить промпт, получить JSON. Бросает LLMParseError при невалидном JSON."""
        ...


class SearchPort(Protocol):
    """Интерфейс поиска. Домен не знает про DuckDuckGo."""

    def search(self, query: str, *, limit: int = 10) -> list[SearchResult]:
        """Выполнить поисковый запрос."""
        ...


class PageFetcherPort(Protocol):
    """Интерфейс загрузки страниц."""

    def fetch_text(self, url: str) -> str:
        """Скачать URL и извлечь основной текст. Бросает FetchError при ошибке."""
        ...
        
class DomainError(Exception):
    """Базовое исключение домена."""
    ...


class LLMParseError(DomainError):
    """LLM вернула невалидный ответ."""
    ...


class FetchError(DomainError):
    """Не удалось скачать страницу."""
    ...


class SearchError(DomainError):
    """Поиск не сработал."""
    ...