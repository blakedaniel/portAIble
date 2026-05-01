"""DSPy LM factory — per-job-safe (no global mutation).

Mirrors local-chat-agent/src/local_chat_agent/llm/dspy_config.py:create_dspy_lm so
DSPy modules can run inside async background tasks without racing on global state.
"""

from __future__ import annotations

import dspy

from ...config import AppSettings


def create_dspy_lm(settings: AppSettings, model_override: str | None = None) -> dspy.LM:
    """Create a dspy.LM bound to Ollama's OpenAI-compatible endpoint.

    Use dspy.context(lm=lm) per call — never dspy.configure() in async background tasks.
    """
    model = model_override or settings.source_analyzer_model
    return dspy.LM(
        model=f"openai/{model}",
        base_url=f"{settings.ollama_url}/v1",
        api_key=settings.ollama_api_key,
        temperature=0.1,
        max_tokens=min(settings.num_ctx, 16384),
        timeout=settings.llm_timeout,
        num_retries=settings.llm_max_retries,
    )
