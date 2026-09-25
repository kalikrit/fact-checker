from .models import MainCheck


def calculate_confidence(check: MainCheck) -> float:
    """
    Оценка уверенности 0..1.
    Учитывает evidence_strength, plausibility, сигналы атрибутов.
    """
    ...