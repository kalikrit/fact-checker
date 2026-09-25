from .client import LLMClient


class GigaChatClient(LLMClient):
    def __init__(self, api_key: str, base_url: str, model: str = "GigaChat"):
        ...

    def complete(self, prompt: str, *, temperature: float = 0.0) -> str:
        ...

    def complete_json(self, prompt: str, *, temperature: float = 0.0) -> dict:
        ...