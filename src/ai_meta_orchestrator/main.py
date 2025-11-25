"""Main entry point for the AI Meta Orchestrator."""

import argparse
import logging
import sys

from ai_meta_orchestrator import __version__
from ai_meta_orchestrator.application.services.orchestrator_service import (
    OrchestratorService,
)
from ai_meta_orchestrator.infrastructure import (
    PlatformInfo,
    get_platform_info,
    load_config,
)


def setup_logging(level: str = "INFO") -> None:
    """Set up logging configuration.

    Args:
        level: The logging level.
    """
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def print_banner() -> None:
    """Print the application banner."""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                  AI Meta Orchestrator                        ║
    ║         CrewAI-based Multi-Agent Orchestration               ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)


def print_platform_info(platform_info: PlatformInfo) -> None:
    """Print platform information.

    Args:
        platform_info: Platform information to print.
    """
    print(f"Platform: {platform_info.platform.value}")
    print(f"System: {platform_info.system} {platform_info.release}")
    print(f"Python: {platform_info.python_version}")
    if platform_info.is_wsl:
        print("Running in WSL environment")
    print()


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser.

    Returns:
        Configured ArgumentParser.
    """
    parser = argparse.ArgumentParser(
        description="AI Meta Orchestrator - CrewAI-based multi-agent orchestration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose output",
    )

    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Set the logging level",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Info command
    subparsers.add_parser("info", help="Show system and configuration information")

    # Run command
    run_parser = subparsers.add_parser("run", help="Run a workflow")
    run_parser.add_argument(
        "-d",
        "--description",
        required=True,
        help="Project/task description",
    )
    run_parser.add_argument(
        "-n",
        "--name",
        default="Custom Workflow",
        help="Workflow name",
    )

    # Demo command
    subparsers.add_parser("demo", help="Run a demo workflow")

    # Server command
    server_parser = subparsers.add_parser("serve", help="Start the REST API server")
    server_parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)",
    )
    server_parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to listen on (default: 8000)",
    )
    server_parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development",
    )

    # Templates command
    templates_parser = subparsers.add_parser("templates", help="List available workflow templates")
    templates_parser.add_argument(
        "-c",
        "--category",
        help="Filter by category",
    )

    return parser


def cmd_info() -> None:
    """Handle the info command."""
    print_banner()
    print(f"Version: {__version__}")
    print()

    platform_info = get_platform_info()
    print_platform_info(platform_info)

    config = load_config()
    print("Configuration:")
    print(f"  LLM Provider: {config.llm.provider}")
    print(f"  LLM Model: {config.llm.model}")
    print(f"  Verbose: {config.workflow.verbose}")
    print(f"  Observability: {'Enabled' if config.observability.enabled else 'Disabled'}")


def cmd_run(description: str, name: str, verbose: bool = False) -> int:
    """Handle the run command.

    Args:
        description: Project/task description.
        name: Workflow name.
        verbose: Whether to enable verbose output.

    Returns:
        Exit code (0 for success, non-zero for failure).
    """
    logger = logging.getLogger(__name__)

    print_banner()
    print(f"Running workflow: {name}")
    print(f"Description: {description}")
    print()

    try:
        orchestrator = OrchestratorService()
        workflow = orchestrator.create_standard_workflow(
            project_description=description,
            name=name,
        )

        logger.info(f"Starting workflow with {len(workflow.tasks)} tasks")
        result = orchestrator.run_workflow(workflow)

        print()
        print("=" * 60)
        print("Workflow Results")
        print("=" * 60)
        print(f"Success: {result.success}")
        print(f"Tasks Completed: {result.tasks_completed}")
        print(f"Tasks Failed: {result.tasks_failed}")
        print(f"Duration: {result.duration_seconds:.2f} seconds")

        if result.errors:
            print()
            print("Errors:")
            for error in result.errors:
                print(f"  - {error}")

        return 0 if result.success else 1

    except Exception as e:
        logger.error(f"Workflow failed: {e}")
        return 1


def cmd_demo(verbose: bool = False) -> int:
    """Handle the demo command.

    Args:
        verbose: Whether to enable verbose output.

    Returns:
        Exit code (0 for success, non-zero for failure).
    """
    demo_description = """
    Create a simple Python utility that:
    1. Reads a text file
    2. Counts word frequencies
    3. Outputs the top 10 most common words

    The utility should handle edge cases like empty files and
    use proper error handling.
    """

    return cmd_run(
        description=demo_description,
        name="Demo: Word Frequency Counter",
        verbose=verbose,
    )


def cmd_serve(host: str, port: int, reload: bool = False) -> int:
    """Handle the serve command to start the REST API server.

    Args:
        host: Host to bind to.
        port: Port to listen on.
        reload: Enable auto-reload for development.

    Returns:
        Exit code (0 for success, non-zero for failure).
    """
    print_banner()
    print(f"Starting REST API server at http://{host}:{port}")
    print(f"API Documentation: http://{host}:{port}/docs")
    print()

    try:
        from ai_meta_orchestrator.api import run_server

        run_server(host=host, port=port, reload=reload)
        return 0
    except ImportError:
        print("Error: FastAPI and uvicorn are required for the API server.")
        print("Install with: pip install ai-meta-orchestrator[api]")
        return 1
    except Exception as e:
        print(f"Server error: {e}")
        return 1


def cmd_templates(category: str | None = None) -> None:
    """Handle the templates command.

    Args:
        category: Optional category to filter by.
    """
    from ai_meta_orchestrator.adapters.templates import get_default_template_registry
    from ai_meta_orchestrator.domain.templates.template_models import TemplateCategory

    print_banner()
    print("Available Workflow Templates")
    print("=" * 60)
    print()

    registry = get_default_template_registry()

    if category:
        try:
            cat = TemplateCategory(category.lower())
            templates = registry.get_by_category(cat)
        except ValueError:
            print(f"Unknown category: {category}")
            print(f"Available categories: {[c.value for c in TemplateCategory]}")
            return
    else:
        templates = registry.list_all()

    for template in templates:
        print(f"📋 {template.name} (v{template.version})")
        print(f"   Category: {template.category.value}")
        print(f"   Description: {template.description}")
        print(f"   Required params: {', '.join(template.required_params)}")
        if template.optional_params:
            print(f"   Optional params: {', '.join(template.optional_params.keys())}")
        if template.tags:
            print(f"   Tags: {', '.join(template.tags)}")
        print()


def main() -> int:
    """Main entry point.

    Returns:
        Exit code (0 for success, non-zero for failure).
    """
    parser = create_parser()
    args = parser.parse_args()

    setup_logging(args.log_level)

    if args.command == "info" or args.command is None:
        cmd_info()
        return 0
    elif args.command == "run":
        return cmd_run(
            description=args.description,
            name=args.name,
            verbose=args.verbose,
        )
    elif args.command == "demo":
        return cmd_demo(verbose=args.verbose)
    elif args.command == "serve":
        return cmd_serve(
            host=args.host,
            port=args.port,
            reload=args.reload,
        )
    elif args.command == "templates":
        cmd_templates(category=args.category if hasattr(args, "category") else None)
        return 0
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
