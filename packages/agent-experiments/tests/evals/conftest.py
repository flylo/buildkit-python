from __future__ import annotations

from pathlib import Path

import pytest
import pytest_asyncio
from zeroshot_agent_experiments import SalaryExtractionAgent
from zeroshot_agentic_workflows import AiAgentConfig, AiAgentFactory, AiAgentProvider

FIXTURES_DIR = Path(__file__).parent / "assets" / "fixtures"


@pytest_asyncio.fixture(scope="module", loop_scope="module")
async def salary_agent():
    """Create a SalaryExtractionAgent wired to local Ollama."""
    config = AiAgentConfig(
        local=False,
        provider=AiAgentProvider.OLLAMA,
        ollama_base_url="http://localhost:11434",
        default_model="qwen2.5:latest",
    )
    factory = AiAgentFactory(config)
    service = factory.make_agent_service()
    return SalaryExtractionAgent(service)


def read_fixture(filename: str) -> str:
    """Read a PDF fixture and return its text.

    For simplicity, since the PDFs are generated with plain text content,
    we extract text using a basic approach. For real evals with scanned
    documents, use a Docling container or similar OCR service.
    """
    path = FIXTURES_DIR / filename
    if not path.exists():
        pytest.skip(
            f"Fixture {filename} not found. Run: "
            "python packages/agent-experiments/tests/evals/generate_fixtures.py"
        )

    # Use PyPDF or similar to extract text
    try:
        from pypdf import PdfReader

        reader = PdfReader(str(path))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    except ImportError:
        # Fallback: read the raw fixture text from the generator
        pytest.skip("pypdf not installed; install it or regenerate fixtures as text")
        return ""  # unreachable
