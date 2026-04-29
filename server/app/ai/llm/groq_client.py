from groq import APIConnectionError, APIStatusError, AsyncGroq, AuthenticationError, BadRequestError, RateLimitError

from app.ai.errors import (
    LLMAuthenticationError,
    LLMConfigurationError,
    LLMInvalidModelError,
    LLMProviderError,
    LLMRateLimitError,
)
from app.core.config import settings


class GroqClient:
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        timeout_seconds: float | None = None,
        temperature: float | None = None,
    ) -> None:
        self.api_key = api_key if api_key is not None else settings.groq_api_key
        self.base_url = base_url or settings.groq_base_url
        self.model = model or settings.groq_model
        self.timeout_seconds = timeout_seconds or settings.groq_timeout_seconds
        self.temperature = temperature if temperature is not None else settings.groq_temperature

        if not self.api_key:
            raise LLMConfigurationError("Missing GROQ_API_KEY. Add it to server/.env before using generation features.")

        self.client = AsyncGroq(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=self.timeout_seconds,
        )

    async def generate(self, prompt: str) -> str:
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
            )
            content = response.choices[0].message.content
            if not content:
                raise LLMProviderError("Groq returned an empty response.")
            return content.strip()
        except LLMProviderError:
            raise
        except AuthenticationError as exc:
            raise LLMAuthenticationError("Groq authentication failed. Check GROQ_API_KEY.") from exc
        except RateLimitError as exc:
            raise LLMRateLimitError("Groq rate limit reached. Try again later.") from exc
        except BadRequestError as exc:
            message = self._extract_error_message(exc)
            if "model" in message.lower():
                raise LLMInvalidModelError(f"Groq rejected the configured model '{self.model}': {message}") from exc
            raise LLMProviderError(f"Groq rejected the request: {message}") from exc
        except APIConnectionError as exc:
            raise LLMProviderError("Could not reach Groq. Check your network connection and GROQ_BASE_URL.") from exc
        except APIStatusError as exc:
            message = self._extract_error_message(exc)
            if exc.status_code == 401:
                raise LLMAuthenticationError("Groq authentication failed. Check GROQ_API_KEY.") from exc
            if exc.status_code == 429:
                raise LLMRateLimitError("Groq rate limit reached. Try again later.") from exc
            if exc.status_code in {400, 404, 422} and "model" in message.lower():
                raise LLMInvalidModelError(f"Groq rejected the configured model '{self.model}': {message}") from exc
            raise LLMProviderError(f"Groq provider error ({exc.status_code}): {message}") from exc
        except TimeoutError as exc:
            raise LLMProviderError("Groq request timed out. Try again or increase GROQ_TIMEOUT_SECONDS.") from exc
        except Exception as exc:
            if exc.__class__.__name__ == "APITimeoutError":
                raise LLMProviderError("Groq request timed out. Try again or increase GROQ_TIMEOUT_SECONDS.") from exc
            raise LLMProviderError(f"Unexpected Groq provider failure: {exc}") from exc

    def _extract_error_message(self, exc: APIStatusError) -> str:
        try:
            payload = exc.response.json()
        except Exception:
            return str(exc)

        error = payload.get("error", payload)
        if isinstance(error, dict):
            return str(error.get("message") or error)
        return str(error)
