"""Observability adapters for the AI Meta Orchestrator.

This module provides observability implementations including:
- PlaceholderObservabilityAdapter: Simple logging-based observability
- OpenTelemetryAdapter: Full OpenTelemetry support for production
"""

import logging
import time
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


class OpenTelemetryAdapter(ObservabilityPort):
    """OpenTelemetry-based observability adapter.

    This adapter integrates with OpenTelemetry for production-grade
    observability including metrics, tracing, and logging.
    """

    def __init__(
        self,
        service_name: str = "ai-meta-orchestrator",
        enable_tracing: bool = True,
        enable_metrics: bool = True,
        exporter_endpoint: str | None = None,
    ) -> None:
        """Initialize the OpenTelemetry adapter.

        Args:
            service_name: Name of the service for telemetry.
            enable_tracing: Whether to enable distributed tracing.
            enable_metrics: Whether to enable metrics collection.
            exporter_endpoint: Optional OTLP exporter endpoint.
        """
        self._service_name = service_name
        self._enable_tracing = enable_tracing
        self._enable_metrics = enable_metrics
        self._exporter_endpoint = exporter_endpoint
        self._logger = logging.getLogger(f"otel.{service_name}")
        self._span_map: dict[str, Any] = {}
        self._tracer: Any = None
        self._meter: Any = None
        self._initialized = False

        # Try to initialize OpenTelemetry
        self._try_initialize()

    def _try_initialize(self) -> None:
        """Try to initialize OpenTelemetry components."""
        try:
            from opentelemetry import trace
            from opentelemetry.sdk.resources import Resource
            from opentelemetry.sdk.trace import TracerProvider

            # Set up tracer
            resource = Resource.create({"service.name": self._service_name})
            provider = TracerProvider(resource=resource)
            trace.set_tracer_provider(provider)
            self._tracer = trace.get_tracer(self._service_name)

            # Try to set up metrics
            try:
                from opentelemetry import metrics
                from opentelemetry.sdk.metrics import MeterProvider

                metrics.set_meter_provider(MeterProvider(resource=resource))
                self._meter = metrics.get_meter(self._service_name)
            except ImportError:
                self._meter = None

            self._initialized = True
            self._logger.info("OpenTelemetry initialized successfully")
        except ImportError:
            self._logger.warning(
                "OpenTelemetry not available, falling back to logging"
            )
            self._initialized = False

    def log_event(self, event_name: str, data: dict[str, Any]) -> None:
        """Log an event using OpenTelemetry semantics.

        Args:
            event_name: Name of the event.
            data: Event data.
        """
        self._logger.info(
            f"Event: {event_name}",
            extra={"otel.event_name": event_name, "otel.event_data": data},
        )

    def record_metric(
        self, metric_name: str, value: float, tags: dict[str, str] | None = None
    ) -> None:
        """Record a metric using OpenTelemetry.

        Args:
            metric_name: Name of the metric.
            value: The metric value.
            tags: Optional tags for the metric.
        """
        if self._meter is not None:
            try:
                counter = self._meter.create_counter(metric_name)
                counter.add(value, tags or {})
            except Exception as e:
                self._logger.debug(f"Failed to record metric: {e}")
        else:
            self._logger.debug(
                f"Metric: {metric_name}={value}",
                extra={"metric_tags": tags or {}},
            )

    def start_span(self, operation_name: str) -> str:
        """Start an OpenTelemetry span.

        Args:
            operation_name: Name of the operation.

        Returns:
            The span ID.
        """
        span_id = str(uuid4())

        if self._tracer is not None and self._enable_tracing:
            try:
                span = self._tracer.start_span(operation_name)
                self._span_map[span_id] = {
                    "span": span,
                    "start_time": time.time(),
                    "operation": operation_name,
                }
            except Exception as e:
                self._logger.debug(f"Failed to start span: {e}")
                self._span_map[span_id] = {
                    "span": None,
                    "start_time": time.time(),
                    "operation": operation_name,
                }
        else:
            self._span_map[span_id] = {
                "span": None,
                "start_time": time.time(),
                "operation": operation_name,
            }
            self._logger.debug(f"Span started: {operation_name} (ID: {span_id})")

        return span_id

    def end_span(self, span_id: str, status: str = "ok") -> None:
        """End an OpenTelemetry span.

        Args:
            span_id: The span ID to end.
            status: The final status of the span.
        """
        if span_id in self._span_map:
            span_data = self._span_map[span_id]
            span = span_data.get("span")

            if span is not None:
                try:
                    from opentelemetry.trace import StatusCode

                    span.set_status(
                        StatusCode.OK if status == "ok" else StatusCode.ERROR
                    )
                    span.end()
                except Exception as e:
                    self._logger.debug(f"Failed to end span: {e}")
            else:
                duration = time.time() - span_data["start_time"]
                self._logger.debug(
                    f"Span ended: {span_data['operation']} "
                    f"(ID: {span_id}, status: {status}, duration: {duration:.3f}s)"
                )

            del self._span_map[span_id]

    @property
    def is_initialized(self) -> bool:
        """Check if OpenTelemetry is properly initialized."""
        return self._initialized


def create_observability_adapter(
    backend: str = "placeholder",
    **kwargs: Any,
) -> ObservabilityPort:
    """Factory function to create an observability adapter.

    Args:
        backend: The backend to use ("placeholder" or "opentelemetry").
        **kwargs: Additional arguments for the adapter.

    Returns:
        An ObservabilityPort implementation.
    """
    if backend == "opentelemetry":
        return OpenTelemetryAdapter(**kwargs)
    return PlaceholderObservabilityAdapter(**kwargs)
