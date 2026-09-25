from abc import ABC, abstractmethod


class LLMClient(ABC):
    @abstractmethod
    def complete(self, prompt: str, *, temperature: float = 0.0) -> str:
        ...

    @abstractmethod
    def complete_json(self, prompt: str, *, temperature: float = 0.0) -> dict:
        ...