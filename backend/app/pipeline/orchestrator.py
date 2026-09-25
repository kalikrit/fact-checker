from domain.models import CheckTask, FactCheckResult
from domain.ports import LLMPort, SearchPort, PageFetcherPort


class Pipeline:
    def __init__(
        self,
        llm: LLMPort,
        search: SearchPort,
        fetcher: PageFetcherPort,
        repository: "TaskRepository",
    ):
        ...

    def run(self, task_id: str, input_text: str) -> FactCheckResult:
        """
        Синхронный запуск пайплайна.
        Обновляет статус и прогресс через repository.
        Бросает TaskFailedError при permanent ошибке.
        """
        ...

    def _extract(self, text: str) -> list[Claim]:
        ...

    def _assess_plausibility(self, main: Claim, text: str) -> Plausibility:
        ...

    def _search_and_fetch(self, main: Claim) -> tuple[list[Source], dict[str, str]]:
        ...

    def _rate_sources(self, sources: list[Source]) -> list[Source]:
        ...

    def _find_evidence(
        self,
        main: Claim,
        sources: list[Source],
        texts: dict[str, str],
    ) -> list[Evidence]:
        ...

    def _decide_verdict(self, main: Claim, evidence: list[Evidence]) -> Verdict:
        ...

    def _check_attributes_if_needed(
        self,
        main: Claim,
        attributes: list[Claim],
        verdict: Verdict,
    ) -> list[AttributeCheck]:
        ...