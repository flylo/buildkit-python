# AI Agents

We have a custom package for making AI Agents that uses the OpenAI Agents SDK (`packages/agentic-workflows`).

## Agent Service

The core is an agent service (`packages/agentic-workflows/src/zeroshot_agentic_workflows/agent_service.py`) with
multiple implementations:

- `service_openai.py`: production implementation using the OpenAI Agents SDK
- `agent_service.py` (`AiAgentServiceLocal`): mocked implementation for testing non-AI portions of workflows
  (orchestration, task management, error handling, etc)
- `service_ollama.py`: hits a local Ollama deployment for development/testing with local models

## Factory

`AiAgentFactory` (`factory.py`) creates the correct service implementation based on `AiAgentConfig`:

```python
from zeroshot_agentic_workflows import AiAgentConfig, AiAgentFactory, AiAgentProvider

config = AiAgentConfig(
    local=False,
    provider=AiAgentProvider.OLLAMA,
    ollama_base_url="http://localhost:11434",
    default_model="qwen2.5:latest",
)
factory = AiAgentFactory(config)
service = factory.make_agent_service()
```

## Decorators

Agents are defined using decorators on workflow classes:

```python
from zeroshot_agentic_workflows import (
    AgentRunResult, AiAgentService, ConsensusStrategy,
    agent, agentic_workflow, consensus_agent,
)

@agentic_workflow(prompts_directory=str(Path(__file__).parent / "prompts"))
class MyWorkflow:
    def __init__(self, ai_agent_service: AiAgentService) -> None:
        self._ai_agent_service = ai_agent_service

    @agent(output_schema=MyOutputSchema)
    async def classify(self, document_text: str) -> AgentRunResult[MyOutputSchema]:
        ...  # Body replaced by decorator

    @consensus_agent(
        runs=3,
        consensus_strategy=ConsensusStrategy.MAJORITY,
        output_schema=MyOutputSchema,
    )
    async def classify_with_consensus(self, document_text: str):
        ...  # Body replaced by decorator
```

### Prompt Files

Each `@agent` / `@consensus_agent` method loads its prompt from a markdown file named after the method in the
`prompts_directory`. Prompts can have YAML frontmatter declaring tools:

```markdown
---
tools:
  - search
  - summarize
---
You are a document classifier. Analyze the input and return structured output.
```

### Parameter Mapping

Method parameters are automatically serialized to JSON and passed as the agent's input. Two special parameters are
handled differently:

- `context` → passed as the agent's context object, excluded from input JSON
- `RepositorySession` instances → passed to the agent SDK for conversation history, excluded from input JSON

## Update Checklist

Every time you update an agent, you must also update:
- Any fixtures
- Any tests that assume a certain agent structure
