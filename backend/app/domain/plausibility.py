from .enums import Plausibility
from .models import Claim
from .ports import LLMPort


def assess_plausibility(main: Claim, context: str, llm: LLMPort) -> Plausibility:
    """
    Оценить правдоподобность main.
    context — весь исходный текст (для понимания контекста).
    """
    ...


def explain_plausibility(main: Claim, context: str, llm: LLMPort) -> tuple[Plausibility, str]:
    """
    То же, но с объяснением.
    Возвращает (оценка, объяснение).
    """
    ...