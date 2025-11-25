"""Workflow templates adapters module."""

from ai_meta_orchestrator.adapters.templates.builtin_templates import (
    create_code_review_template,
    create_documentation_template,
    create_full_development_template,
    create_quick_implementation_template,
    create_security_audit_template,
    get_default_template_registry,
)

__all__ = [
    "create_code_review_template",
    "create_documentation_template",
    "create_full_development_template",
    "create_quick_implementation_template",
    "create_security_audit_template",
    "get_default_template_registry",
]
