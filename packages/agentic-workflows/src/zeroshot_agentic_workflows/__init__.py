"""Agent workflow building blocks for Zeroshot Python packages."""

from .agent_service import (
    AgentConfig,
    AgentRunConfig,
    AgentRunResult,
    AgentType,
    AiAgentConfig,
    AiAgentProvider,
    AiAgentService,
    AiAgentServiceLocal,
    ConsensusRunResult,
    ConsensusStrategy,
)
from .decorators import agent, agentic_workflow, consensus_agent
from .factory import AiAgentFactory
from .param_mapper import AgentParameterMapper
from .prompt_utils import (
    ParsedPrompt,
    PromptFrontmatter,
    generate_tools_reference,
    parse_prompt_frontmatter,
)
from .session import (
    CONVERSATION_SESSION_REPOSITORY,
    ConversationItemModel,
    ConversationMessage,
    ConversationSessionModel,
    ConversationSessionRepository,
    InMemoryConversationSessionRepository,
    RepositorySession,
    SessionItem,
    SessionNotFoundError,
)
from .session_factory import AiSessionFactory

__all__ = [
    "CONVERSATION_SESSION_REPOSITORY",
    "AgentConfig",
    "AgentParameterMapper",
    "AgentRunConfig",
    "AgentRunResult",
    "AgentType",
    "AiAgentConfig",
    "AiAgentFactory",
    "AiAgentProvider",
    "AiAgentService",
    "AiAgentServiceLocal",
    "AiSessionFactory",
    "ConsensusRunResult",
    "ConsensusStrategy",
    "ConversationItemModel",
    "ConversationMessage",
    "ConversationSessionModel",
    "ConversationSessionRepository",
    "InMemoryConversationSessionRepository",
    "ParsedPrompt",
    "PromptFrontmatter",
    "RepositorySession",
    "SessionItem",
    "SessionNotFoundError",
    "agent",
    "agentic_workflow",
    "consensus_agent",
    "generate_tools_reference",
    "parse_prompt_frontmatter",
]
