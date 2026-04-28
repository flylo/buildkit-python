from __future__ import annotations

import logging
from pathlib import Path

from zeroshot_agentic_workflows import (
    AgentRunResult,
    AiAgentService,
    ConsensusRunResult,
    ConsensusStrategy,
    agent,
    agentic_workflow,
    consensus_agent,
)

from .schemas import (
    DocumentClassification,
    DocumentType,
    PayDataExtraction,
    SalaryBreakdown,
    SalaryCalculation,
)

logger = logging.getLogger(__name__)

PERIODS_PER_YEAR: dict[str, int] = {
    "weekly": 52,
    "biweekly": 26,
    "semi_monthly": 24,
    "monthly": 12,
    "annual": 1,
}

_PROMPTS_DIR = str(Path(__file__).parent / "prompts")


@agentic_workflow(prompts_directory=_PROMPTS_DIR)
class SalaryExtractionAgent:
    def __init__(self, ai_agent_service: AiAgentService) -> None:
        self._ai_agent_service = ai_agent_service

    @consensus_agent(
        runs=3,
        consensus_strategy=ConsensusStrategy.MAJORITY,
        output_schema=DocumentClassification,
    )
    async def classify_document(
            self, document_text: str
    ) -> ConsensusRunResult[DocumentClassification]:
        ...

    @agent(output_schema=PayDataExtraction)
    async def extract_pay_data(
            self, document_text: str, document_type: str
    ) -> AgentRunResult[PayDataExtraction]:
        ...

    async def extract_salary(
            self, documents: list[str]
    ) -> SalaryCalculation:
        breakdowns: list[SalaryBreakdown] = []
        best_salary: float | None = None
        best_confidence: float = 0.0
        best_methodology: str = ""
        employee_name: str | None = None
        employer_name: str | None = None

        for i, doc_text in enumerate(documents):
            # Phase 1: Classify (consensus — 3 runs, majority vote)
            classification_result = await self.classify_document(doc_text)
            if not classification_result.success:
                logger.warning("Failed to classify document %d", i)
                continue

            classification = classification_result.output
            if classification.employee_name and not employee_name:
                employee_name = classification.employee_name
            if classification.employer_name and not employer_name:
                employer_name = classification.employer_name

            # Phase 2: Extract pay data
            extraction_result = await self.extract_pay_data(
                doc_text, classification.document_type.value
            )
            if not extraction_result.success:
                logger.warning("Failed to extract pay data from document %d", i)
                continue

            pay_data = extraction_result.output

            # Phase 3: Calculate salary deterministically
            salary, confidence, methodology = _calculate_salary(
                classification.document_type, pay_data
            )

            breakdowns.append(
                SalaryBreakdown(
                    document_index=i,
                    document_type=classification.document_type.value,
                    annual_salary=salary,
                    confidence=confidence,
                    methodology=methodology,
                )
            )

            if salary is not None and confidence > best_confidence:
                best_salary = salary
                best_confidence = confidence
                best_methodology = methodology

        return SalaryCalculation(
            annual_salary=best_salary,
            confidence=best_confidence,
            methodology=best_methodology,
            employee_name=employee_name,
            employer_name=employer_name,
            breakdown=breakdowns,
        )


def _calculate_salary(
        doc_type: DocumentType,
        pay_data: PayDataExtraction,
) -> tuple[float | None, float, str]:
    """Deterministic salary calculation with priority-based approach."""

    # Priority 1: Directly stated annual salary
    if pay_data.annual_salary is not None:
        return pay_data.annual_salary, 1.0, "directly_stated_annual_salary"

    if pay_data.stated_annual_wages is not None:
        return pay_data.stated_annual_wages, 1.0, "stated_annual_wages"

    # Priority 2: Gross pay × periods per year
    if pay_data.gross_pay_period is not None and pay_data.pay_frequency is not None:
        periods = PERIODS_PER_YEAR.get(pay_data.pay_frequency)
        if periods:
            annual = pay_data.gross_pay_period * periods
            return annual, 0.9, "gross_pay_times_periods"

    # Priority 3: Hourly rate × hours × periods
    if (
            pay_data.hourly_rate is not None
            and pay_data.hours_worked is not None
            and pay_data.pay_frequency is not None
    ):
        periods = PERIODS_PER_YEAR.get(pay_data.pay_frequency)
        if periods:
            annual = pay_data.hourly_rate * pay_data.hours_worked * periods
            return annual, 0.8, "hourly_rate_calculation"

    return None, 0.0, "unable_to_calculate"
