"""Agent role definitions and domain models."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class AgentRole(str, Enum):
    """Enumeration of available agent roles in the orchestrator."""

    PM = "project_manager"
    DEV = "developer"
    QA = "quality_assurance"
    SECURITY = "security"
    DOCS = "documentation"


@dataclass
class AgentConfig:
    """Configuration for an agent.

    Attributes:
        role: The role of the agent.
        goal: The main goal of the agent.
        backstory: Background story providing context for the agent.
        verbose: Whether to enable verbose output.
        allow_delegation: Whether this agent can delegate tasks to others.
        tools: List of tools available to this agent.
        memory: Whether to enable memory for the agent.
    """

    role: AgentRole
    goal: str
    backstory: str
    verbose: bool = True
    allow_delegation: bool = False
    tools: list[Any] = field(default_factory=list)
    memory: bool = True


# Default agent configurations for the internal agents
DEFAULT_AGENT_CONFIGS: dict[AgentRole, AgentConfig] = {
    AgentRole.PM: AgentConfig(
        role=AgentRole.PM,
        goal="Coordinate project tasks, manage workflow, and ensure deliverables meet requirements",
        backstory=(
            "You are an experienced Project Manager with expertise in software development "
            "workflows. You excel at breaking down complex projects into manageable tasks, "
            "coordinating between team members, and ensuring quality deliverables."
        ),
        allow_delegation=True,
    ),
    AgentRole.DEV: AgentConfig(
        role=AgentRole.DEV,
        goal="Implement high-quality code solutions that meet specifications",
        backstory=(
            "You are a skilled Software Developer with expertise in multiple programming "
            "languages and frameworks. You write clean, maintainable, and well-documented "
            "code while following best practices and design patterns."
        ),
        allow_delegation=False,
    ),
    AgentRole.QA: AgentConfig(
        role=AgentRole.QA,
        goal="Ensure code quality through thorough testing and review",
        backstory=(
            "You are a meticulous Quality Assurance Engineer who specializes in finding "
            "bugs, edge cases, and potential issues. You create comprehensive test plans "
            "and ensure software meets quality standards before release."
        ),
        allow_delegation=False,
    ),
    AgentRole.SECURITY: AgentConfig(
        role=AgentRole.SECURITY,
        goal="Identify and mitigate security vulnerabilities and ensure compliance",
        backstory=(
            "You are a Security Expert with deep knowledge of security best practices, "
            "common vulnerabilities, and compliance requirements. You review code and "
            "architecture for security issues and provide remediation guidance."
        ),
        allow_delegation=False,
    ),
    AgentRole.DOCS: AgentConfig(
        role=AgentRole.DOCS,
        goal="Create clear, comprehensive, and maintainable documentation",
        backstory=(
            "You are a Technical Writer who excels at creating documentation that is "
            "both thorough and accessible. You understand the importance of good "
            "documentation for code maintainability and user adoption."
        ),
        allow_delegation=False,
    ),
}
