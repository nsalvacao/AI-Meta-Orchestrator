"""Built-in workflow templates.

This module provides pre-configured workflow templates for common
development scenarios.
"""

from ai_meta_orchestrator.domain.agents.agent_models import AgentRole
from ai_meta_orchestrator.domain.tasks.task_models import TaskPriority
from ai_meta_orchestrator.domain.templates.template_models import (
    TaskTemplate,
    TemplateCategory,
    WorkflowMode,
    WorkflowTemplate,
    WorkflowTemplateConfig,
    WorkflowTemplateRegistry,
)


def create_full_development_template() -> WorkflowTemplate:
    """Create a full development workflow template.

    This template includes all agents: PM planning, development,
    QA review, security review, and documentation.
    """
    template = WorkflowTemplate(
        name="Full Development Workflow",
        description=(
            "Complete development workflow for {project_name}. "
            "Includes planning, implementation, QA, security review, and documentation."
        ),
        category=TemplateCategory.DEVELOPMENT,
        config=WorkflowTemplateConfig(
            mode=WorkflowMode.SEQUENTIAL,
            enable_evaluation=True,
            enable_correction_loop=True,
        ),
        required_params=["project_name", "project_description"],
        optional_params={
            "tech_stack": "Python",
            "requirements": "None specified",
        },
        tags=["full", "development", "complete", "all-agents"],
        version="1.0.0",
    )

    # PM Planning Task
    pm_task = TaskTemplate(
        name_template="Project Planning: {project_name}",
        description_template=(
            "Analyze the following project and create a detailed implementation plan:\n\n"
            "Project: {project_name}\n"
            "Description: {project_description}\n"
            "Tech Stack: {tech_stack}\n"
            "Requirements: {requirements}\n\n"
            "Create a task breakdown with priorities and dependencies."
        ),
        assigned_to=AgentRole.PM,
        expected_output_template=(
            "A detailed project plan for {project_name} with task breakdown, "
            "timeline, and resource allocation."
        ),
        priority=TaskPriority.HIGH,
    )
    template.add_task_template(pm_task)

    # Development Task
    dev_task = TaskTemplate(
        name_template="Implementation: {project_name}",
        description_template=(
            "Implement the solution for {project_name} based on the project plan.\n\n"
            "Requirements:\n{project_description}\n\n"
            "Use {tech_stack} and follow best practices."
        ),
        assigned_to=AgentRole.DEV,
        expected_output_template=(
            "Working implementation of {project_name} with clean, documented code."
        ),
        priority=TaskPriority.HIGH,
        depends_on=[pm_task.id],
    )
    template.add_task_template(dev_task)

    # QA Review Task
    qa_task = TaskTemplate(
        name_template="QA Review: {project_name}",
        description_template=(
            "Review the implementation of {project_name} for quality.\n"
            "Check for bugs, edge cases, and code quality issues.\n"
            "Ensure the implementation meets requirements."
        ),
        assigned_to=AgentRole.QA,
        expected_output_template=(
            "QA report with test results, found issues, and recommendations."
        ),
        priority=TaskPriority.HIGH,
        depends_on=[dev_task.id],
    )
    template.add_task_template(qa_task)

    # Security Review Task
    security_task = TaskTemplate(
        name_template="Security Review: {project_name}",
        description_template=(
            "Perform security review of {project_name}.\n"
            "Check for common vulnerabilities, security best practices, "
            "and compliance requirements."
        ),
        assigned_to=AgentRole.SECURITY,
        expected_output_template=(
            "Security assessment report with vulnerabilities and remediation steps."
        ),
        priority=TaskPriority.HIGH,
        depends_on=[dev_task.id],
    )
    template.add_task_template(security_task)

    # Documentation Task
    docs_task = TaskTemplate(
        name_template="Documentation: {project_name}",
        description_template=(
            "Create comprehensive documentation for {project_name}.\n"
            "Include setup instructions, API documentation, and usage examples."
        ),
        assigned_to=AgentRole.DOCS,
        expected_output_template=(
            "Complete documentation including README, API docs, and examples."
        ),
        priority=TaskPriority.MEDIUM,
        depends_on=[dev_task.id, qa_task.id],
    )
    template.add_task_template(docs_task)

    return template


def create_quick_implementation_template() -> WorkflowTemplate:
    """Create a quick implementation template.

    This template focuses on rapid development with minimal review,
    suitable for prototypes or small features.
    """
    template = WorkflowTemplate(
        name="Quick Implementation",
        description=(
            "Rapid development workflow for {feature_name}. "
            "Focuses on implementation and basic testing."
        ),
        category=TemplateCategory.DEVELOPMENT,
        config=WorkflowTemplateConfig(
            mode=WorkflowMode.SEQUENTIAL,
            enable_evaluation=True,
            enable_correction_loop=False,  # Skip correction for speed
            max_iterations=3,
        ),
        required_params=["feature_name", "feature_description"],
        optional_params={
            "tech_stack": "Python",
        },
        tags=["quick", "prototype", "fast", "development"],
        version="1.0.0",
    )

    # Development Task
    dev_task = TaskTemplate(
        name_template="Implement: {feature_name}",
        description_template=(
            "Quickly implement {feature_name}.\n\n"
            "Description: {feature_description}\n"
            "Tech Stack: {tech_stack}\n\n"
            "Focus on functionality over perfection."
        ),
        assigned_to=AgentRole.DEV,
        expected_output_template="Working implementation of {feature_name}.",
        priority=TaskPriority.HIGH,
    )
    template.add_task_template(dev_task)

    # Basic QA Task
    qa_task = TaskTemplate(
        name_template="Basic Review: {feature_name}",
        description_template="Perform basic testing of {feature_name}.",
        assigned_to=AgentRole.QA,
        expected_output_template="Basic test results and any critical issues.",
        priority=TaskPriority.MEDIUM,
        depends_on=[dev_task.id],
    )
    template.add_task_template(qa_task)

    return template


def create_code_review_template() -> WorkflowTemplate:
    """Create a code review workflow template.

    This template is for reviewing existing code for quality and security.
    """
    template = WorkflowTemplate(
        name="Code Review Workflow",
        description="Review {code_subject} for quality, security, and documentation.",
        category=TemplateCategory.REVIEW,
        config=WorkflowTemplateConfig(
            mode=WorkflowMode.PARALLEL,  # Reviews can run in parallel
            enable_evaluation=True,
            enable_correction_loop=False,
        ),
        required_params=["code_subject", "code_location"],
        optional_params={
            "focus_areas": "all",
        },
        tags=["review", "code-review", "quality", "security"],
        version="1.0.0",
    )

    # QA Review
    qa_task = TaskTemplate(
        name_template="Quality Review: {code_subject}",
        description_template=(
            "Review {code_subject} at {code_location} for code quality.\n"
            "Focus areas: {focus_areas}\n"
            "Check for bugs, code style, and maintainability."
        ),
        assigned_to=AgentRole.QA,
        expected_output_template="Quality review report with findings and recommendations.",
        priority=TaskPriority.HIGH,
    )
    template.add_task_template(qa_task)

    # Security Review
    security_task = TaskTemplate(
        name_template="Security Review: {code_subject}",
        description_template=(
            "Security audit of {code_subject} at {code_location}.\n"
            "Check for vulnerabilities and security best practices."
        ),
        assigned_to=AgentRole.SECURITY,
        expected_output_template="Security review report with vulnerabilities and remediation.",
        priority=TaskPriority.HIGH,
    )
    template.add_task_template(security_task)

    return template


def create_documentation_template() -> WorkflowTemplate:
    """Create a documentation workflow template.

    This template is for creating or updating documentation.
    """
    template = WorkflowTemplate(
        name="Documentation Workflow",
        description="Create documentation for {subject}.",
        category=TemplateCategory.DOCUMENTATION,
        config=WorkflowTemplateConfig(
            mode=WorkflowMode.SEQUENTIAL,
            enable_evaluation=True,
            enable_correction_loop=True,
        ),
        required_params=["subject", "subject_description"],
        optional_params={
            "doc_type": "README and API documentation",
            "audience": "developers",
        },
        tags=["documentation", "docs", "readme", "api-docs"],
        version="1.0.0",
    )

    # Planning
    pm_task = TaskTemplate(
        name_template="Documentation Plan: {subject}",
        description_template=(
            "Plan documentation structure for {subject}.\n"
            "Subject: {subject_description}\n"
            "Documentation type: {doc_type}\n"
            "Target audience: {audience}"
        ),
        assigned_to=AgentRole.PM,
        expected_output_template="Documentation outline with sections and content plan.",
        priority=TaskPriority.HIGH,
    )
    template.add_task_template(pm_task)

    # Documentation
    docs_task = TaskTemplate(
        name_template="Write Documentation: {subject}",
        description_template=(
            "Create {doc_type} for {subject}.\n"
            "Description: {subject_description}\n"
            "Audience: {audience}"
        ),
        assigned_to=AgentRole.DOCS,
        expected_output_template="Complete documentation with examples.",
        priority=TaskPriority.HIGH,
        depends_on=[pm_task.id],
    )
    template.add_task_template(docs_task)

    return template


def create_security_audit_template() -> WorkflowTemplate:
    """Create a security audit workflow template."""
    template = WorkflowTemplate(
        name="Security Audit Workflow",
        description="Comprehensive security audit for {system_name}.",
        category=TemplateCategory.SECURITY,
        config=WorkflowTemplateConfig(
            mode=WorkflowMode.SEQUENTIAL,
            enable_evaluation=True,
            enable_correction_loop=True,
            max_iterations=5,
        ),
        required_params=["system_name", "system_description"],
        optional_params={
            "compliance_standards": "OWASP Top 10",
            "scope": "full system",
        },
        tags=["security", "audit", "compliance", "vulnerability"],
        version="1.0.0",
    )

    # Planning
    pm_task = TaskTemplate(
        name_template="Security Audit Plan: {system_name}",
        description_template=(
            "Plan security audit for {system_name}.\n"
            "Description: {system_description}\n"
            "Scope: {scope}\n"
            "Compliance: {compliance_standards}"
        ),
        assigned_to=AgentRole.PM,
        expected_output_template="Security audit plan with methodology and checklist.",
        priority=TaskPriority.CRITICAL,
    )
    template.add_task_template(pm_task)

    # Security Audit
    security_task = TaskTemplate(
        name_template="Security Audit: {system_name}",
        description_template=(
            "Perform security audit of {system_name}.\n"
            "Follow {compliance_standards} guidelines.\n"
            "Scope: {scope}"
        ),
        assigned_to=AgentRole.SECURITY,
        expected_output_template=(
            "Security audit report with vulnerabilities, risk ratings, and remediation."
        ),
        priority=TaskPriority.CRITICAL,
        depends_on=[pm_task.id],
    )
    template.add_task_template(security_task)

    # Remediation Documentation
    docs_task = TaskTemplate(
        name_template="Remediation Guide: {system_name}",
        description_template=(
            "Create remediation documentation for security findings in {system_name}."
        ),
        assigned_to=AgentRole.DOCS,
        expected_output_template="Remediation guide with step-by-step fix instructions.",
        priority=TaskPriority.HIGH,
        depends_on=[security_task.id],
    )
    template.add_task_template(docs_task)

    return template


def get_default_template_registry() -> WorkflowTemplateRegistry:
    """Get a registry with all built-in templates registered.

    Returns:
        WorkflowTemplateRegistry with default templates.
    """
    registry = WorkflowTemplateRegistry()

    # Register all built-in templates
    registry.register(create_full_development_template())
    registry.register(create_quick_implementation_template())
    registry.register(create_code_review_template())
    registry.register(create_documentation_template())
    registry.register(create_security_audit_template())

    return registry
