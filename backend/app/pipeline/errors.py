from domain.ports import DomainError


class TaskFailedError(Exception):
    """Permanent ошибка — пайплайн останавливается."""
    def __init__(self, step: str, message: str, technical: str | None = None):
        ...


def classify_error(exc: Exception) -> "ErrorKind":
    """
    Классифицировать ошибку как transient / permanent / unknown.
    """
    ...


def retry_on_transient(fn, *, max_attempts: int = 3):
    """
    Декоратор: retry при transient ошибках.
    """
    ...