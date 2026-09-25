from abc import ABC, abstractmethod
from domain.ports import SearchResult


class SearchClient(ABC):
    @abstractmethod
    def search(self, query: str, *, limit: int = 10) -> list[SearchResult]:
        ...