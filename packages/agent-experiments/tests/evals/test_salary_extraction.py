"""Salary extraction eval suite.

These tests exercise real LLM inference via Ollama and are skipped
by default.  Run with:

    uv run pytest --eval packages/agent-experiments/tests/evals/

Requires:
  - Ollama running locally with ``qwen2.5:latest`` pulled
  - PDF fixtures generated (run generate_fixtures.py first)
"""

from __future__ import annotations

import pytest

from zeroshot_agent_experiments import SalaryExtractionAgent

from .conftest import read_fixture

pytestmark = [
    pytest.mark.eval,
    pytest.mark.asyncio(loop_scope="module"),
    pytest.mark.timeout(300),
]


class TestAcmeDocuments:
    async def test_acme_paystub_w2_offer(self, salary_agent: SalaryExtractionAgent) -> None:
        """ACME paystub + W-2 + offer letter → ~$95K."""
        docs = [
            read_fixture("paystub-acme-biweekly.pdf"),
            read_fixture("w2-acme-2024.pdf"),
            read_fixture("offer-letter-acme.pdf"),
        ]
        result = await salary_agent.extract_salary(docs)

        assert result.annual_salary is not None
        assert 90_000 <= result.annual_salary <= 100_000
        assert result.employee_name is not None
        assert "Mitchell" in result.employee_name
        assert result.confidence > 0.5
        assert len(result.breakdown) == 3


class TestTechForwardDocuments:
    async def test_techforward_paystub_verification(
        self, salary_agent: SalaryExtractionAgent
    ) -> None:
        """TechForward monthly paystub + verification letter → ~$120K."""
        docs = [
            read_fixture("paystub-techforward-monthly.pdf"),
            read_fixture("employment-verification-techforward.pdf"),
        ]
        result = await salary_agent.extract_salary(docs)

        assert result.annual_salary is not None
        assert 115_000 <= result.annual_salary <= 125_000
        assert result.employee_name is not None
        assert "Chen" in result.employee_name
        assert result.confidence > 0.5


class TestGreenleafDocuments:
    async def test_greenleaf_weekly_paystub(self, salary_agent: SalaryExtractionAgent) -> None:
        """Greenleaf weekly paystub alone → ~$83.2K (40 * 40 * 52)."""
        docs = [read_fixture("paystub-greenleaf-weekly.pdf")]
        result = await salary_agent.extract_salary(docs)

        assert result.annual_salary is not None
        assert 78_000 <= result.annual_salary <= 90_000
        assert result.employee_name is not None
        assert "Torres" in result.employee_name


class TestAllDocuments:
    async def test_all_documents_together(self, salary_agent: SalaryExtractionAgent) -> None:
        """All documents together → validates breakdown and methodology."""
        docs = [
            read_fixture("paystub-acme-biweekly.pdf"),
            read_fixture("paystub-techforward-monthly.pdf"),
            read_fixture("paystub-greenleaf-weekly.pdf"),
            read_fixture("w2-acme-2024.pdf"),
            read_fixture("offer-letter-acme.pdf"),
            read_fixture("employment-verification-techforward.pdf"),
        ]
        result = await salary_agent.extract_salary(docs)

        assert result.annual_salary is not None
        assert len(result.breakdown) > 0
        assert result.methodology != ""
