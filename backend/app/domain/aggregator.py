from .models import MainCheck
from .enums import Verdict


def apply_attribute_signals(check: MainCheck) -> MainCheck:
    """
    Понизить вердикт до misleading, если есть сигналы
    fabricated / distorted / anachronistic / type_mismatch.
    """
    ...


def aggregate_verdict(check: MainCheck) -> MainCheck:
    """
    Финальная агрегация: применяет сигналы и возвращает обновлённый MainCheck.
    """
    ...


def is_verdict_confirmed(verdict: Verdict) -> bool:
    """
    True для true / mostly_true. Используется для решения о проверке атрибутов.
    """
    ...


def build_result(
    checks: list[MainCheck],
    checked_at: int,
) -> FactCheckResult:
    """
    Собрать финальный результат + дисклеймер.
    """
    ...