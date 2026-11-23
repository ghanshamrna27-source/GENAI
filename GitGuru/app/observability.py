"""
app/observability.py
Production observability, request latency tracking, token consumption logging,
and performance metrics for GitGuru.
"""

import time
import logging
import threading
from typing import Dict, Any, List
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.cache import GLOBAL_CACHE

logger = logging.getLogger("gitguru.observability")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [OBSERVABILITY] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def estimate_tokens(text: str) -> int:
    """
    Estimates token count for a text string.
    Rule of thumb for English/Code: 1 token ≈ 4 characters or ~0.75 words.
    """
    if not text:
        return 0
    words = len(text.split())
    by_words = int(words * 1.33)
    by_chars = max(1, len(text) // 4)
    return max(by_words, by_chars)


class ObservabilityTelemetry:
    """
    Thread-safe metrics aggregator for API performance, latency, and token spend.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self.total_requests = 0
        self.total_errors = 0
        self.total_latency_ms = 0.0
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.endpoint_counts: Dict[str, int] = {}
        self.recent_latencies: List[float] = []

    def record(
        self,
        method: str,
        path: str,
        status_code: int,
        latency_ms: float,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        cached: bool = False,
    ) -> None:
        """Records a request event into aggregate telemetry."""
        with self._lock:
            self.total_requests += 1
            if status_code >= 400:
                self.total_errors += 1

            self.total_latency_ms += latency_ms
            self.total_prompt_tokens += prompt_tokens
            self.total_completion_tokens += completion_tokens

            endpoint_key = f"{method} {path}"
            self.endpoint_counts[endpoint_key] = self.endpoint_counts.get(endpoint_key, 0) + 1

            # Keep rolling window of last 100 latencies for percentiles
            self.recent_latencies.append(latency_ms)
            if len(self.recent_latencies) > 100:
                self.recent_latencies.pop(0)

        # Structured log
        logger.info(
            f"method={method} path={path} status={status_code} latency_ms={latency_ms:.2f} "
            f"prompt_tokens={prompt_tokens} completion_tokens={completion_tokens} "
            f"cached={cached}"
        )

    def get_metrics(self) -> Dict[str, Any]:
        """Returns comprehensive production observability metrics."""
        with self._lock:
            avg_latency = (
                round(self.total_latency_ms / self.total_requests, 2)
                if self.total_requests > 0
                else 0.0
            )

            p95_latency = 0.0
            if self.recent_latencies:
                sorted_lats = sorted(self.recent_latencies)
                p95_idx = int(len(sorted_lats) * 0.95)
                p95_latency = round(sorted_lats[min(p95_idx, len(sorted_lats) - 1)], 2)

            total_tokens = self.total_prompt_tokens + self.total_completion_tokens
            # Standard blended token cost estimate ($0.50 per 1M tokens)
            est_cost_usd = round(total_tokens * 0.0000005, 6)

            cache_stats = GLOBAL_CACHE.stats()
            tokens_saved = cache_stats["tokens_saved"]
            cost_saved_usd = round(tokens_saved * 0.0000005, 6)

            return {
                "service": "GitGuru",
                "uptime_status": "healthy",
                "traffic": {
                    "total_requests": self.total_requests,
                    "total_errors": self.total_errors,
                    "error_rate_percent": round(
                        (self.total_errors / self.total_requests * 100.0)
                        if self.total_requests > 0
                        else 0.0,
                        2,
                    ),
                    "endpoints": dict(self.endpoint_counts),
                },
                "latency_ms": {
                    "average": avg_latency,
                    "p95": p95_latency,
                    "total_processing_ms": round(self.total_latency_ms, 2),
                },
                "tokens": {
                    "prompt_tokens": self.total_prompt_tokens,
                    "completion_tokens": self.total_completion_tokens,
                    "total_tokens": total_tokens,
                    "tokens_saved_by_cache": tokens_saved,
                },
                "cost_usd": {
                    "estimated_incurred_cost": est_cost_usd,
                    "estimated_savings_from_cache": cost_saved_usd,
                },
                "cache": cache_stats,
            }


GLOBAL_TELEMETRY = ObservabilityTelemetry()


class ObservabilityMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware recording request latency, cache headers, and emitting logs.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.perf_counter()
        response = await call_next(request)
        latency_ms = (time.perf_counter() - start_time) * 1000.0

        # Inject timing header
        response.headers["X-Process-Time-Ms"] = f"{latency_ms:.2f}"

        # Record metrics if not already handled by endpoint
        is_cached = response.headers.get("X-Cache-Status") == "HIT"
        prompt_tokens = int(response.headers.get("X-Prompt-Tokens", "0"))
        completion_tokens = int(response.headers.get("X-Completion-Tokens", "0"))

        GLOBAL_TELEMETRY.record(
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            latency_ms=latency_ms,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cached=is_cached,
        )

        return response
