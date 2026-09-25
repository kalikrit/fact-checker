from domain.models import CheckTask, FactCheckResult, TaskError


class TaskRepository:
    def __init__(self, db_path: str):
        ...

    def save_task(self, task: CheckTask) -> None:
        ...

    def get_task(self, task_id: str) -> CheckTask | None:
        ...

    def update_status(self, task_id: str, status: str) -> None:
        ...

    def update_progress(self, task_id: str, progress: TaskProgress) -> None:
        ...

    def complete_task(self, task_id: str, result: FactCheckResult) -> None:
        ...

    def fail_task(self, task_id: str, error: TaskError) -> None:
        ...

    def delete_older_than(self, days: int) -> int:
        """Удалить задачи старше N дней. Возвращает количество удалённых."""
        ...