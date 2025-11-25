"""Infrastructure layer - Cross-cutting concerns and utilities."""

from ai_meta_orchestrator.infrastructure.config import OrchestratorConfig, load_config
from ai_meta_orchestrator.infrastructure.platform import PlatformInfo, get_platform_info

__all__ = [
    "OrchestratorConfig",
    "load_config",
    "PlatformInfo",
    "get_platform_info",
]
