from __future__ import annotations

import logging
from typing import Optional

from groq import AsyncGroq

from app.config import settings

logger = logging.getLogger(__name__)

GROQ_LLAMA4_SCOUT = "meta-llama/llama-4-scout-17b-16e-instruct"


class LLMClient:
    """Provider-agnostic LLM interface.

    All AI code in agents/, routes/, services/ MUST call the LLM through this
    client — never via a provider SDK directly. The provider is selected by
    settings.llm_provider (env var LLM_PROVIDER).

    Supported now: 'groq' (Llama 4 Scout).
    Supported via the same .complete() interface later: 'ollama', 'anthropic',
    'fine_tuned'. Adding one means implementing _complete_<name>().
    """

    def __init__(self, provider: Optional[str] = None) -> None:
        self.provider = (provider or settings.llm_provider or "groq").lower()
        self._client = None
        self._model = ""
        if self.provider == "groq":
            if settings.groq_api_key:
                self._client = AsyncGroq(api_key=settings.groq_api_key)
                self._model = GROQ_LLAMA4_SCOUT
            else:
                logger.warning("LLM provider 'groq' selected but GROQ_API_KEY is not set")

    async def complete(
        self,
        system: str,
        messages: list[dict],
        tools: Optional[list[dict]] = None,
        temperature: float = 0.3,
        max_tokens: int = 1000,
        response_format: Optional[dict] = None,
    ) -> dict:
        """Return ``{content, tool_calls, usage}``.

        Raises RuntimeError if the provider client is not configured.
        """
        if not self._client:
            raise RuntimeError(f"LLM provider '{self.provider}' has no client configured")

        if self.provider == "groq":
            return await self._complete_groq(
                system, messages, tools, temperature, max_tokens, response_format
            )
        raise NotImplementedError(f"Provider '{self.provider}' is not yet implemented")

    async def _complete_groq(
        self,
        system: str,
        messages: list[dict],
        tools: Optional[list[dict]],
        temperature: float,
        max_tokens: int,
        response_format: Optional[dict],
    ) -> dict:
        kwargs: dict = {
            "model": self._model,
            "messages": [{"role": "system", "content": system}] + messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"
        if response_format:
            kwargs["response_format"] = response_format

        response = await self._client.chat.completions.create(**kwargs)
        message = response.choices[0].message
        return {
            "content": message.content or "",
            "tool_calls": [
                {
                    "id": call.id,
                    "name": call.function.name,
                    "arguments": call.function.arguments,
                }
                for call in (message.tool_calls or [])
            ],
            "usage": (
                {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                }
                if response.usage
                else {}
            ),
        }


_default_client: Optional[LLMClient] = None


def get_llm() -> LLMClient:
    global _default_client
    if _default_client is None:
        _default_client = LLMClient()
    return _default_client
