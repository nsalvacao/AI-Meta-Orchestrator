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
- **Workflow Templates**: Pre-built templates for common development scenarios
- **Plugin System**: Extensible architecture for custom agents and tools
- **REST API**: FastAPI-based REST API for integration
- **Ports-and-Adapters Architecture**: Clean separation of concerns for easy extension
- **Linux-First, Cross-OS Aware**: Optimized for Linux/WSL with cross-platform support

## Architecture

```
src/ai_meta_orchestrator/
├── domain/              # Core business logic
│   ├── agents/          # Agent models and configurations
│   ├── tasks/           # Task models and status management
│   ├── workflows/       # Workflow orchestration models
│   ├── templates/       # Workflow template models
│   └── plugins/         # Plugin system models
├── ports/               # Interface definitions (abstractions)
│   ├── agent_ports/     # Agent operation interfaces
│   ├── task_ports/      # Task execution interfaces
│   └── external_ports/  # External system interfaces
├── adapters/            # Implementation of port interfaces
│   ├── internal_agents/ # CrewAI agent implementations
│   ├── external_cli/    # External CLI adapters and agents
│   ├── templates/       # Built-in workflow templates
│   ├── credentials/     # Credential management
│   ├── git_cicd/        # Git/CI-CD integration
│   └── observability/   # Observability (logging, tracing)
├── api/                 # REST API (FastAPI)
│   ├── app.py           # Application setup
│   ├── routes.py        # API endpoints
│   └── models.py        # Request/Response models
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

# List available workflow templates
orchestrator templates

# Start the REST API server
orchestrator serve --host 0.0.0.0 --port 8000
```

### REST API

Start the API server:

```bash
orchestrator serve
```

Access the API at `http://localhost:8000`. API documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

Example API calls:

```bash
# Health check
curl http://localhost:8000/health

# List agents
curl http://localhost:8000/agents

# List templates
curl http://localhost:8000/templates

# Create workflow from template
curl -X POST http://localhost:8000/templates/instantiate \
  -H "Content-Type: application/json" \
  -d '{"template_name": "Full Development Workflow", "params": {"project_name": "MyProject", "project_description": "A new project"}}'
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

### Using Workflow Templates

```python
from ai_meta_orchestrator.adapters.templates import get_default_template_registry
from ai_meta_orchestrator.application.services.orchestrator_service import OrchestratorService

# Get the template registry
registry = get_default_template_registry()

# List available templates
for template in registry.list_all():
    print(f"{template.name} - {template.description}")

# Instantiate a template
template = registry.get("Full Development Workflow")
workflow = template.instantiate({
    "project_name": "MyProject",
    "project_description": "Build a REST API",
})

# Run the workflow
orchestrator = OrchestratorService()
result = orchestrator.run_workflow(workflow)
```

### Using the Plugin System

```python
from ai_meta_orchestrator.domain.plugins import (
    PluginRegistry,
    HookPlugin,
    HookPoint,
    PluginMetadata,
    PluginType,
)

# Create a custom hook plugin
class MyLoggingPlugin(HookPlugin):
    @property
    def metadata(self):
        return PluginMetadata(
            name="my_logger",
            version="1.0.0",
            description="Logs workflow events",
            plugin_type=PluginType.HOOK,
        )
    
    @property
    def hook_points(self):
        return [HookPoint.BEFORE_TASK_EXECUTE, HookPoint.AFTER_TASK_EXECUTE]
    
    def initialize(self, config):
        return True
    
    def shutdown(self):
        pass
    
    def on_hook(self, hook_point, context):
        print(f"Hook triggered: {hook_point.value}")
        return context

# Register the plugin
registry = PluginRegistry()
registry.register(MyLoggingPlugin())
```

### Using External CLI Agents

The orchestrator supports external AI CLI tools as agents:

```python
from ai_meta_orchestrator.adapters.external_cli import (
    GeminiAgent,
    CodexAgent,
    CopilotAgent,
    create_cli_agent,
)
from ai_meta_orchestrator.domain.agents.agent_models import AgentRole
from ai_meta_orchestrator.domain.tasks.task_models import Task
from ai_meta_orchestrator.ports.external_ports.external_port import ExternalCLIType

# Create a Gemini-powered agent
# Requires: GOOGLE_API_KEY or GEMINI_API_KEY environment variable
gemini_agent = GeminiAgent(role=AgentRole.DEV)

# Create a Codex/OpenAI-powered agent
# Requires: OPENAI_API_KEY environment variable
codex_agent = CodexAgent(role=AgentRole.DEV)

# Create a GitHub Copilot CLI agent
# Requires: gh CLI installed with copilot extension
copilot_agent = CopilotAgent(role=AgentRole.DEV)

# Use factory function
agent = create_cli_agent(ExternalCLIType.GEMINI, role=AgentRole.QA)

# Check availability
if gemini_agent.is_available():
    task = Task(
        name="Generate Code",
        description="Write a Python function to sort a list",
        assigned_to=AgentRole.DEV,
        expected_output="Python code",
    )
    result = gemini_agent.execute_task(task)
    print(result.output)
```

**Prerequisites for External CLI Agents:**

- **Gemini CLI**: Set `GOOGLE_API_KEY` or `GEMINI_API_KEY` environment variable
- **Codex CLI**: Set `OPENAI_API_KEY` environment variable and install OpenAI CLI
- **Copilot CLI**: Install GitHub CLI (`gh`) and the copilot extension:
  ```bash
  gh extension install github/gh-copilot
  gh auth login
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

### Current (v0.2.0)

- [x] Core agent architecture (PM, Dev, QA, Security, Docs)
- [x] Task distribution and execution
- [x] Evaluation and correction loops
- [x] Ports-and-adapters architecture
- [x] Platform detection (Linux-first, cross-OS aware)
- [x] Workflow templates and presets
- [x] Plugin system for custom agents
- [x] REST API server (FastAPI)
- [x] Enhanced observability (OpenTelemetry support)
- [x] Secure credential management
- [x] Git integration
- [x] External CLI integrations (Gemini CLI, Codex CLI, Copilot Agent CLI)

### Planned (v0.3.0+)

- [ ] Web dashboard
- [ ] Database persistence
- [ ] Advanced workflow features (parallel, hierarchical)
- [ ] Plugin marketplace

See [BACKLOG.md](BACKLOG.md) for detailed task breakdown and implementation tracking.

## Project Structure

```
AI-Meta-Orchestrator/
├── src/
│   └── ai_meta_orchestrator/    # Main package
├── tests/
│   ├── unit/                    # Unit tests
│   └── integration/             # Integration tests
├── pyproject.toml               # Project configuration
├── BACKLOG.md                   # Evolutionary backlog
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
