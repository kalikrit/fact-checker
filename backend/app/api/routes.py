from fastapi import APIRouter, Depends, HTTPException
from .schemas import (
    CheckRequest, CheckCreatedResponse, CheckStatusResponse,
)


router = APIRouter(prefix="/api", tags=["check"])


@router.post("/check", response_model=CheckCreatedResponse, status_code=202)
def create_check(
    request: CheckRequest,
    pipeline: "Pipeline" = Depends(get_pipeline),
    repo: "TaskRepository" = Depends(get_repository),
) -> CheckCreatedResponse:
    """
    Создать задачу проверки.
    Возвращает task_id. Пайплайн запускается в фоне.
    """
    ...


@router.get("/check/{task_id}", response_model=CheckStatusResponse)
def get_check(
    task_id: str,
    repo: "TaskRepository" = Depends(get_repository),
) -> CheckStatusResponse:
    """
    Получить статус задачи и результат.
    """
    ...


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}