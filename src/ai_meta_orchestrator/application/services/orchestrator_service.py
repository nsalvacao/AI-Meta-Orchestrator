"""Orchestrator service - Main service for coordinating agents and workflows."""

from typing import Any

from crewai import Crew, Process

from ai_meta_orchestrator.adapters.internal_agents.crewai_agent import (
    CrewAIAgent,
    CrewAIAgentFactory,
)
from ai_meta_orchestrator.adapters.observability.observability_adapter import (
    PlaceholderObservabilityAdapter,
)
from ai_meta_orchestrator.domain.agents.agent_models import AgentRole
from ai_meta_orchestrator.domain.tasks.task_models import (
    EvaluationResult,
    Task,
    TaskResult,
    TaskStatus,
)
from ai_meta_orchestrator.domain.workflows.workflow_models import (
    Workflow,
    WorkflowConfig,
    WorkflowMode,
    WorkflowResult,
    WorkflowStatus,
)
from ai_meta_orchestrator.ports.external_ports.external_port import ObservabilityPort


class TaskEvaluator:
    """Evaluator for task results using the QA agent."""

    def __init__(
        self,
        qa_agent: CrewAIAgent | None = None,
        observability: ObservabilityPort | None = None,
    ) -> None:
        """Initialize the evaluator.

        Args:
            qa_agent: Optional QA agent for evaluation.
            observability: Optional observability adapter.
        """
        self._qa_agent = qa_agent
        self._observability = observability or PlaceholderObservabilityAdapter()

    def evaluate(self, task: Task, result: TaskResult) -> EvaluationResult:
        """Evaluate a task result.

        Args:
            task: The task that was executed.
            result: The result of the task execution.

        Returns:
            EvaluationResult with evaluation details.
        """
        span_id = self._observability.start_span(f"evaluate_task_{task.id}")

        try:
            # Basic evaluation logic
            if not result.success:
                return EvaluationResult(
                    passed=False,
                    score=0.0,
                    feedback="Task failed to execute",
                    issues=[result.error or "Unknown error"],
                )

            # Simple validation - check if output exists
            if result.output is None or result.output == "":
                return EvaluationResult(
                    passed=False,
                    score=30.0,
                    feedback="Task produced no output",
                    issues=["Empty or missing output"],
                    suggestions=["Ensure the task produces meaningful output"],
                )

            # For now, pass evaluation if output exists
            # Future: Use QA agent for more sophisticated evaluation
            return EvaluationResult(
                passed=True,
                score=80.0,
                feedback="Task completed with output",
            )
        finally:
            self._observability.end_span(span_id)


class TaskDistributor:
    """Distributes tasks to appropriate agents."""

    def __init__(
        self,
        agent_factory: CrewAIAgentFactory,
        observability: ObservabilityPort | None = None,
    ) -> None:
        """Initialize the distributor.

        Args:
            agent_factory: Factory for creating agents.
            observability: Optional observability adapter.
        """
        self._agent_factory = agent_factory
        self._observability = observability or PlaceholderObservabilityAdapter()

    def get_agent_for_task(self, task: Task) -> CrewAIAgent:
        """Get the appropriate agent for a task.

        Args:
            task: The task to assign.

        Returns:
            The appropriate CrewAI agent.
        """
        return self._agent_factory.create_agent(task.assigned_to)


class OrchestratorService:
    """Main orchestrator service for managing workflows and agents.

    This service coordinates:
    - Agent creation and management
    - Task distribution and execution
    - Evaluation and correction loops
    - Workflow orchestration
    """

    def __init__(
        self,
        agent_factory: CrewAIAgentFactory | None = None,
        observability: ObservabilityPort | None = None,
    ) -> None:
        """Initialize the orchestrator service.

        Args:
            agent_factory: Optional agent factory (creates default if not provided).
            observability: Optional observability adapter.
        """
        self._agent_factory = agent_factory or CrewAIAgentFactory()
        self._observability = observability or PlaceholderObservabilityAdapter()
        self._distributor = TaskDistributor(self._agent_factory, self._observability)
        self._evaluator = TaskEvaluator(observability=self._observability)
        self._agents: dict[AgentRole, CrewAIAgent] = {}

    def initialize_agents(self, roles: list[AgentRole] | None = None) -> None:
        """Initialize agents for the specified roles.

        Args:
            roles: List of roles to initialize. If None, initializes all roles.
        """
        span_id = self._observability.start_span("initialize_agents")

        try:
            roles_to_init = roles or list(AgentRole)
            for role in roles_to_init:
                agent = self._agent_factory.create_agent(role)
                self._agents[role] = agent
                self._observability.log_event(
                    "agent_initialized",
                    {"role": role.value},
                )
        finally:
            self._observability.end_span(span_id)

    def get_agent(self, role: AgentRole) -> CrewAIAgent | None:
        """Get an agent by role.

        Args:
            role: The agent role.

        Returns:
            The agent or None if not initialized.
        """
        return self._agents.get(role)

    def execute_task(
        self,
        task: Task,
        with_evaluation: bool = True,
    ) -> TaskResult:
        """Execute a single task.

        Args:
            task: The task to execute.
            with_evaluation: Whether to evaluate the result.

        Returns:
            The task result.
        """
        span_id = self._observability.start_span(f"execute_task_{task.id}")

        try:
            task.mark_in_progress()

            # Get the appropriate agent
            agent = self._distributor.get_agent_for_task(task)

            # Execute the task
            result = agent.execute_task(task)

            # Evaluate if requested
            if with_evaluation and result.success:
                evaluation = self._evaluator.evaluate(task, result)
                if not evaluation.passed and task.can_be_revised():
                    task.request_revision(evaluation)
                    return result

            task.complete(result)
            self._observability.log_event(
                "task_completed",
                {
                    "task_id": str(task.id),
                    "success": result.success,
                },
            )

            return result
        finally:
            self._observability.end_span(span_id)

    def execute_with_correction_loop(
        self,
        task: Task,
        max_corrections: int = 3,
    ) -> TaskResult:
        """Execute a task with correction loop for failed evaluations.

        Args:
            task: The task to execute.
            max_corrections: Maximum number of correction attempts.

        Returns:
            The final task result.
        """
        span_id = self._observability.start_span(f"correction_loop_{task.id}")

        try:
            for attempt in range(max_corrections + 1):
                result = self.execute_task(task)

                if result.success and task.status == TaskStatus.COMPLETED:
                    return result

                if task.status == TaskStatus.NEEDS_REVISION:
                    self._observability.log_event(
                        "task_revision_requested",
                        {
                            "task_id": str(task.id),
                            "attempt": attempt + 1,
                            "feedback": task.evaluation.feedback if task.evaluation else "",
                        },
                    )
                    # Prepare for retry
                    task.status = TaskStatus.PENDING
                else:
                    # Task failed without revision option
                    break

            return result
        finally:
            self._observability.end_span(span_id)

    def run_workflow(self, workflow: Workflow) -> WorkflowResult:
        """Run a complete workflow.

        Args:
            workflow: The workflow to run.

        Returns:
            WorkflowResult with execution details.
        """
        span_id = self._observability.start_span(f"workflow_{workflow.id}")
        import time
        start_time = time.time()

        try:
            workflow.start()

            # Ensure all required agents are initialized
            required_roles = {task.assigned_to for task in workflow.tasks}
            self.initialize_agents(list(required_roles))

            outputs: dict[str, Any] = {}
            errors: list[str] = []
            tasks_completed = 0
            tasks_failed = 0

            if workflow.config.mode == WorkflowMode.SEQUENTIAL:
                # Sequential execution
                for task in workflow.tasks:
                    # Check for pause
                    if workflow.status == WorkflowStatus.PAUSED:
                        self._observability.log_event(
                            "workflow_paused",
                            {"workflow_id": str(workflow.id)},
                        )
                        break

                    if workflow.config.enable_correction_loop:
                        result = self.execute_with_correction_loop(task)
                    else:
                        result = self.execute_task(
                            task,
                            with_evaluation=workflow.config.enable_evaluation,
                        )

                    if result.success:
                        tasks_completed += 1
                        outputs[str(task.id)] = result.output
                    else:
                        tasks_failed += 1
                        if result.error:
                            errors.append(f"Task {task.name}: {result.error}")

                    workflow.increment_iteration()

            elif workflow.config.mode == WorkflowMode.PARALLEL:
                # Parallel execution with dependency resolution
                tasks_completed, tasks_failed, outputs, errors = (
                    self._run_parallel_workflow(workflow)
                )

            else:
                # For HIERARCHICAL mode, use CrewAI's Crew
                crew_agents = [
                    self._agents[role].crewai_agent
                    for role in required_roles
                    if role in self._agents
                ]

                from crewai import Task as CrewAITask

                crew_tasks = [
                    CrewAITask(
                        description=task.description,
                        expected_output=task.expected_output or "Complete successfully",
                        agent=self._agents[task.assigned_to].crewai_agent,
                    )
                    for task in workflow.tasks
                    if task.assigned_to in self._agents
                ]

                # Note: CrewAI's Crew expects list[BaseAgent], but Agent inherits from
                # BaseAgent. The type: ignore is needed due to list invariance in mypy.
                crew = Crew(
                    agents=crew_agents,  # type: ignore[arg-type]
                    tasks=crew_tasks,
                    process=Process.hierarchical,
                    verbose=workflow.config.verbose,
                    memory=workflow.config.memory,
                )

                try:
                    crew_result = crew.kickoff()
                    tasks_completed = len(workflow.tasks)
                    outputs["crew_result"] = str(crew_result)
                except Exception as e:
                    tasks_failed = len(workflow.tasks)
                    errors.append(str(e))

            duration = time.time() - start_time

            # Only complete if not paused
            if workflow.status != WorkflowStatus.PAUSED:
                success = tasks_failed == 0

                workflow_result = WorkflowResult(
                    success=success,
                    tasks_completed=tasks_completed,
                    tasks_failed=tasks_failed,
                    total_iterations=workflow.current_iteration,
                    outputs=outputs,
                    errors=errors,
                    duration_seconds=duration,
                )

                workflow.complete(workflow_result)
                self._observability.log_event(
                    "workflow_completed",
                    {
                        "workflow_id": str(workflow.id),
                        "success": success,
                        "tasks_completed": tasks_completed,
                        "tasks_failed": tasks_failed,
                        "duration": duration,
                    },
                )

                return workflow_result
            else:
                # Return partial result for paused workflows
                return WorkflowResult(
                    success=False,
                    tasks_completed=tasks_completed,
                    tasks_failed=tasks_failed,
                    total_iterations=workflow.current_iteration,
                    outputs=outputs,
                    errors=["Workflow paused"],
                    duration_seconds=duration,
                )
        finally:
            self._observability.end_span(span_id)

    def _run_parallel_workflow(
        self,
        workflow: Workflow,
    ) -> tuple[int, int, dict[str, Any], list[str]]:
        """Run workflow tasks in parallel where dependencies allow.

        This method executes tasks that have no dependencies or whose
        dependencies have been completed, allowing for parallel execution.

        Args:
            workflow: The workflow to run.

        Returns:
            Tuple of (tasks_completed, tasks_failed, outputs, errors).
        """
        import concurrent.futures
        import threading

        outputs: dict[str, Any] = {}
        errors: list[str] = []
        tasks_completed = 0
        tasks_failed = 0
        lock = threading.Lock()

        def execute_single_task(task: Task) -> TaskResult:
            """Execute a single task and return the result."""
            if workflow.config.enable_correction_loop:
                return self.execute_with_correction_loop(task)
            return self.execute_task(
                task,
                with_evaluation=workflow.config.enable_evaluation,
            )

        # Continue until all tasks are processed or workflow is paused
        with concurrent.futures.ThreadPoolExecutor() as executor:
            while not workflow.is_complete():
                # Check for pause
                if workflow.status == WorkflowStatus.PAUSED:
                    break

                # Get tasks ready to execute
                ready_tasks = workflow.get_ready_tasks()
                if not ready_tasks:
                    # No tasks ready but not complete - may have circular deps
                    pending = workflow.get_pending_tasks()
                    if pending:
                        errors.append(
                            "Workflow has unresolvable dependencies or no ready tasks"
                        )
                    break

                # Submit ready tasks for parallel execution
                futures = {
                    executor.submit(execute_single_task, task): task
                    for task in ready_tasks
                }

                # Process completed futures
                for future in concurrent.futures.as_completed(futures):
                    task = futures[future]
                    try:
                        result = future.result()
                        with lock:
                            if result.success:
                                tasks_completed += 1
                                outputs[str(task.id)] = result.output
                            else:
                                tasks_failed += 1
                                if result.error:
                                    errors.append(f"Task {task.name}: {result.error}")
                            workflow.increment_iteration()
                    except Exception as e:
                        with lock:
                            # Update task status on exception
                            task.status = TaskStatus.FAILED
                            tasks_failed += 1
                            errors.append(f"Task {task.name} raised exception: {e}")

        return tasks_completed, tasks_failed, outputs, errors

    def create_standard_workflow(
        self,
        project_description: str,
        name: str = "Standard Development Workflow",
    ) -> Workflow:
        """Create a standard development workflow with all agents.

        This creates a typical workflow that:
        1. PM breaks down the project into tasks
        2. Dev implements the solution
        3. QA reviews and tests
        4. Security reviews for vulnerabilities
        5. Docs creates documentation

        Args:
            project_description: Description of the project/task.
            name: Name for the workflow.

        Returns:
            A configured Workflow instance.
        """
        workflow = Workflow(
            name=name,
            description=project_description,
            config=WorkflowConfig(
                mode=WorkflowMode.SEQUENTIAL,
                enable_evaluation=True,
                enable_correction_loop=True,
            ),
        )

        # Task 1: PM analyzes and plans
        pm_task = Task(
            name="Project Analysis and Planning",
            description=(
                f"Analyze the following project requirements and create a detailed plan:\n\n"
                f"{project_description}\n\n"
                "Create a breakdown of tasks, identify key requirements, "
                "and outline the implementation approach."
            ),
            assigned_to=AgentRole.PM,
            expected_output="A detailed project plan with task breakdown and timeline",
        )
        workflow.add_task(pm_task)

        # Task 2: Dev implements
        dev_task = Task(
            name="Implementation",
            description=(
                "Based on the project plan, implement the solution. "
                "Write clean, well-structured code following best practices."
            ),
            assigned_to=AgentRole.DEV,
            expected_output="Implemented solution with code",
            context_tasks=[pm_task.id],
        )
        workflow.add_task(dev_task)

        # Task 3: QA reviews
        qa_task = Task(
            name="Quality Assurance Review",
            description=(
                "Review the implementation for quality. "
                "Check for bugs, edge cases, and ensure it meets requirements."
            ),
            assigned_to=AgentRole.QA,
            expected_output="QA report with findings and recommendations",
            context_tasks=[pm_task.id, dev_task.id],
        )
        workflow.add_task(qa_task)

        # Task 4: Security reviews
        security_task = Task(
            name="Security Review",
            description=(
                "Review the implementation for security vulnerabilities. "
                "Check for common security issues and compliance requirements."
            ),
            assigned_to=AgentRole.SECURITY,
            expected_output="Security report with findings and recommendations",
            context_tasks=[dev_task.id],
        )
        workflow.add_task(security_task)

        # Task 5: Docs creates documentation
        docs_task = Task(
            name="Documentation",
            description=(
                "Create comprehensive documentation for the implementation. "
                "Include usage examples, API documentation, and setup instructions."
            ),
            assigned_to=AgentRole.DOCS,
            expected_output="Complete documentation",
            context_tasks=[pm_task.id, dev_task.id],
        )
        workflow.add_task(docs_task)

        return workflow
