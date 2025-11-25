# AI Meta Orchestrator

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

CrewAI-based meta-orchestrator with internal agents (PM, Dev, QA, Security, Docs) and a sequential workflow with evaluation and task return loops. Modular structure using ports-and-adapters (hexagonal) architecture, ready to grow with external integrations (Gemini CLI, Codex CLI, Copilot Agent CLI) and future extensions such as Git/CI-CD, credential management, and advanced observability.

## Features

- **Multi-Agent Orchestration**: Coordinate multiple specialized AI agents
  - **PM Agent**: Project planning and task coordination
  - **Dev Agent**: Code implementation and development
  - **QA Agent**: Quality assurance and testing
  - **Security Agent**: Security review and vulnerability assessment
  - **Docs Agent**: Documentation generation

- **Task Distribution & Evaluation**: Intelligent task routing with built-in evaluation loops
- **Correction Loops**: Automatic retry with feedback for failed tasks
- **Ports-and-Adapters Architecture**: Clean separation of concerns for easy extension
- **Linux-First, Cross-OS Aware**: Optimized for Linux/WSL with cross-platform support

## Architecture

```
src/ai_meta_orchestrator/
├── domain/              # Core business logic
│   ├── agents/          # Agent models and configurations
│   ├── tasks/           # Task models and status management
│   └── workflows/       # Workflow orchestration models
├── ports/               # Interface definitions (abstractions)
│   ├── agent_ports/     # Agent operation interfaces
│   ├── task_ports/      # Task execution interfaces
│   └── external_ports/  # External system interfaces
├── adapters/            # Implementation of port interfaces
│   ├── internal_agents/ # CrewAI agent implementations
│   ├── external_cli/    # External CLI placeholders
│   ├── credentials/     # Credential management placeholders
│   ├── git_cicd/        # Git/CI-CD placeholders
│   └── observability/   # Observability placeholders
├── application/         # Application layer (services, use cases)
│   └── services/        # Orchestrator service
└── infrastructure/      # Cross-cutting concerns
    ├── config.py        # Configuration management
    └── platform.py      # Platform detection utilities
```

## Installation

### Requirements

- Python 3.10 or higher
- pip (Python package installer)

### Quick Start

```bash
# Clone the repository
git clone https://github.com/nsalvacao/AI-Meta-Orchestrator.git
cd AI-Meta-Orchestrator

# Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install the package with development dependencies
pip install -e ".[dev]"
```

### Environment Variables

Set up your LLM provider credentials:

```bash
# For OpenAI (default)
export OPENAI_API_KEY="your-api-key"

# Optional: Override defaults
export ORCHESTRATOR_LLM_PROVIDER="openai"  # or "anthropic"
export ORCHESTRATOR_LLM_MODEL="gpt-4"
export ORCHESTRATOR_LOG_LEVEL="INFO"
export ORCHESTRATOR_VERBOSE="true"
```

## Usage

### Command Line Interface

```bash
# Show system information
orchestrator info

# Run a workflow with a description
orchestrator run -d "Create a Python utility that counts word frequencies in a text file"

# Run the demo workflow
orchestrator demo
```

### Programmatic Usage

```python
from ai_meta_orchestrator.application.services.orchestrator_service import (
    OrchestratorService,
)
from ai_meta_orchestrator.domain.agents.agent_models import AgentRole

# Create orchestrator
orchestrator = OrchestratorService()

# Initialize agents
orchestrator.initialize_agents([AgentRole.PM, AgentRole.DEV, AgentRole.QA])

# Create and run a workflow
workflow = orchestrator.create_standard_workflow(
    project_description="Create a REST API endpoint",
    name="API Development",
)
result = orchestrator.run_workflow(workflow)

print(f"Success: {result.success}")
print(f"Tasks completed: {result.tasks_completed}")
```

### Custom Tasks and Workflows

```python
from ai_meta_orchestrator.domain.agents.agent_models import AgentRole
from ai_meta_orchestrator.domain.tasks.task_models import Task
from ai_meta_orchestrator.domain.workflows.workflow_models import Workflow, WorkflowConfig

# Create a custom workflow
workflow = Workflow(
    name="Custom Workflow",
    description="My custom workflow",
    config=WorkflowConfig(
        enable_evaluation=True,
        enable_correction_loop=True,
        max_iterations=5,
    ),
)

# Add tasks
dev_task = Task(
    name="Implement Feature",
    description="Implement the requested feature",
    assigned_to=AgentRole.DEV,
    expected_output="Working code implementation",
)
workflow.add_task(dev_task)

qa_task = Task(
    name="Review Code",
    description="Review the implementation",
    assigned_to=AgentRole.QA,
    context_tasks=[dev_task.id],
)
workflow.add_task(qa_task)
```

## Development

### Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run all tests
pytest

# Run with coverage
pytest --cov=ai_meta_orchestrator

# Run specific test file
pytest tests/unit/test_agent_models.py
```

### Linting and Type Checking

```bash
# Run ruff linter
ruff check src tests

# Run type checking
mypy src
```

## Roadmap

### Current (MVP)

- [x] Core agent architecture (PM, Dev, QA, Security, Docs)
- [x] Task distribution and execution
- [x] Evaluation and correction loops
- [x] Ports-and-adapters architecture
- [x] Platform detection (Linux-first, cross-OS aware)

### Planned

- [ ] External CLI integrations (Gemini CLI, Codex CLI, Copilot Agent CLI)
- [ ] Secure credential management
- [ ] Git/CI-CD integration
- [ ] Advanced observability (OpenTelemetry, metrics)
- [ ] REST API server
- [ ] Web dashboard
- [ ] Plugin system for custom agents
- [ ] Workflow templates and presets

## Project Structure

```
AI-Meta-Orchestrator/
├── src/
│   └── ai_meta_orchestrator/    # Main package
├── tests/
│   ├── unit/                    # Unit tests
│   └── integration/             # Integration tests
├── pyproject.toml               # Project configuration
├── README.md                    # This file
└── LICENSE                      # MIT License
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [CrewAI](https://github.com/joaomdmoura/crewAI) - Multi-agent orchestration framework
- The open-source AI community
