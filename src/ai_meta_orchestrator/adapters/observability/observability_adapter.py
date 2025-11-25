"""Placeholder observability adapter.

This adapter is a placeholder for future observability implementation.
It will eventually support:
- Structured logging
- Metrics collection (Prometheus, StatsD, etc.)
- Distributed tracing (OpenTelemetry, Jaeger, etc.)
- Health checks and monitoring
"""

import logging
from typing import Any
from uuid import uuid4

from ai_meta_orchestrator.ports.external_ports.external_port import ObservabilityPort


class PlaceholderObservabilityAdapter(ObservabilityPort):
    """Placeholder observability adapter.

    This adapter uses Python's built-in logging as a simple observability solution.
    In production, this should be replaced with a more robust solution.
    """

    def __init__(self, logger_name: str = "ai_meta_orchestrator") -> None:
        """Initialize the placeholder adapter.

        Args:
            logger_name: Name for the logger.
        """
        self._logger = logging.getLogger(logger_name)
        self._spans: dict[str, dict[str, Any]] = {}

    def log_event(self, event_name: str, data: dict[str, Any]) -> None:
        """Log an event.

        Args:
            event_name: Name of the event.
            data: Event data.
        """
        self._logger.info(f"Event: {event_name}", extra={"event_data": data})

    def record_metric(
        self, metric_name: str, value: float, tags: dict[str, str] | None = None
    ) -> None:
        """Record a metric.

        Args:
            metric_name: Name of the metric.
            value: The metric value.
            tags: Optional tags for the metric.
        """
        self._logger.debug(
            f"Metric: {metric_name}={value}",
            extra={"metric_tags": tags or {}},
        )

    def start_span(self, operation_name: str) -> str:
        """Start a tracing span.

        Args:
            operation_name: Name of the operation.

        Returns:
            The span ID.
        """
        span_id = str(uuid4())
        self._spans[span_id] = {
            "operation": operation_name,
            "status": "in_progress",
        }
        self._logger.debug(f"Span started: {operation_name} (ID: {span_id})")
        return span_id

    def end_span(self, span_id: str, status: str = "ok") -> None:
        """End a tracing span.

        Args:
            span_id: The span ID to end.
            status: The final status of the span.
        """
        if span_id in self._spans:
            span = self._spans[span_id]
            span["status"] = status
            self._logger.debug(
                f"Span ended: {span['operation']} (ID: {span_id}, status: {status})"
            )
            del self._spans[span_id]
