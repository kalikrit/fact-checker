from .client import SearchClient


class DuckDuckGoClient(SearchClient):
    def search(self, query: str, *, limit: int = 10) -> list[SearchResult]:
        ...