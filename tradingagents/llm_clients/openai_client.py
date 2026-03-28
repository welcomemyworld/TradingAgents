import logging
import os
import random
import time
from typing import Any, Callable, Optional

from langchain_openai import ChatOpenAI
from openai import APIConnectionError, APITimeoutError, InternalServerError, RateLimitError

from .base_client import BaseLLMClient, normalize_content
from .validators import validate_model

logger = logging.getLogger(__name__)


def _is_transient_openai_error(exc: Exception) -> bool:
    """Return True when the error is worth retrying with backoff."""
    if isinstance(exc, (RateLimitError, APIConnectionError, APITimeoutError, InternalServerError)):
        return True
    return getattr(exc, "status_code", None) in {429, 500, 502, 503, 504}


def invoke_with_backoff(
    operation: Callable[[], Any],
    *,
    max_attempts: int,
    base_delay_seconds: float,
    max_delay_seconds: float,
    normalize_fn: Callable[[Any], Any] = normalize_content,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> Any:
    """Execute an LLM call with exponential backoff on transient upstream failures."""
    attempts = max(1, int(max_attempts))

    for attempt in range(attempts):
        try:
            return normalize_fn(operation())
        except Exception as exc:
            if not _is_transient_openai_error(exc) or attempt >= attempts - 1:
                raise

            delay = min(max_delay_seconds, base_delay_seconds * (2 ** attempt))
            # Small jitter reduces synchronized retries when the upstream is saturated.
            delay += random.uniform(0.0, min(1.0, delay * 0.1))
            logger.warning(
                "Transient OpenAI-compatible error (%s). Retrying in %.1fs (%s/%s).",
                type(exc).__name__,
                delay,
                attempt + 1,
                attempts - 1,
            )
            sleep_fn(delay)


class NormalizedChatOpenAI(ChatOpenAI):
    """ChatOpenAI with normalized content output.

    The Responses API returns content as a list of typed blocks
    (reasoning, text, etc.). This normalizes to string for consistent
    downstream handling.
    """

    transient_retry_attempts: int = 3
    retry_base_delay_seconds: float = 1.5
    retry_max_delay_seconds: float = 8.0

    def invoke(self, input, config=None, **kwargs):
        super_invoke = super().invoke
        return invoke_with_backoff(
            lambda: super_invoke(input, config, **kwargs),
            max_attempts=self.transient_retry_attempts,
            base_delay_seconds=self.retry_base_delay_seconds,
            max_delay_seconds=self.retry_max_delay_seconds,
        )

# Kwargs forwarded from user config to ChatOpenAI
_PASSTHROUGH_KWARGS = (
    "timeout", "max_retries", "reasoning_effort",
    "api_key", "callbacks", "http_client", "http_async_client",
)

# Provider base URLs and API key env vars
_PROVIDER_CONFIG = {
    "xai": ("https://api.x.ai/v1", "XAI_API_KEY"),
    "openrouter": ("https://openrouter.ai/api/v1", "OPENROUTER_API_KEY"),
    "vectorengine": ("https://api.vectorengine.ai/v1", ("VECTORENGINE_API_KEY", "OPENAI_API_KEY")),
    "ollama": ("http://localhost:11434/v1", None),
}


def _resolve_api_key(env_keys: Any) -> Optional[str]:
    if isinstance(env_keys, str):
        return os.environ.get(env_keys)
    for env_key in env_keys or ():
        api_key = os.environ.get(env_key)
        if api_key:
            return api_key
    return None


class OpenAIClient(BaseLLMClient):
    """Client for OpenAI, Ollama, OpenRouter, and xAI providers.

    For native OpenAI models, uses the Responses API (/v1/responses) which
    supports reasoning_effort with function tools across all model families
    (GPT-4.1, GPT-5). Third-party compatible providers (xAI, OpenRouter,
    Ollama) use standard Chat Completions.
    """

    def __init__(
        self,
        model: str,
        base_url: Optional[str] = None,
        provider: str = "openai",
        **kwargs,
    ):
        super().__init__(model, base_url, **kwargs)
        self.provider = provider.lower()

    def get_llm(self) -> Any:
        """Return configured ChatOpenAI instance."""
        llm_kwargs = {"model": self.model}

        # Provider-specific base URL and auth
        if self.provider in _PROVIDER_CONFIG:
            base_url, api_key_env = _PROVIDER_CONFIG[self.provider]
            llm_kwargs["base_url"] = base_url
            if api_key_env:
                api_key = _resolve_api_key(api_key_env)
                if api_key:
                    llm_kwargs["api_key"] = api_key
            else:
                llm_kwargs["api_key"] = "ollama"
        elif self.base_url:
            llm_kwargs["base_url"] = self.base_url

        # Forward user-provided kwargs
        for key in _PASSTHROUGH_KWARGS:
            if key in self.kwargs:
                llm_kwargs[key] = self.kwargs[key]

        llm_kwargs["transient_retry_attempts"] = self.kwargs.get(
            "transient_retry_attempts", 3
        )
        llm_kwargs["retry_base_delay_seconds"] = self.kwargs.get(
            "retry_base_delay_seconds", 1.5
        )
        llm_kwargs["retry_max_delay_seconds"] = self.kwargs.get(
            "retry_max_delay_seconds", 8.0
        )

        # Native OpenAI: use Responses API for consistent behavior across
        # all model families. Third-party providers use Chat Completions.
        if self.provider in {"openai", "vectorengine"}:
            llm_kwargs["use_responses_api"] = True

        return NormalizedChatOpenAI(**llm_kwargs)

    def validate_model(self) -> bool:
        """Validate model for the provider."""
        return validate_model(self.provider, self.model)
