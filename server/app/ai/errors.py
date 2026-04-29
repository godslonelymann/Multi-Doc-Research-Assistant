class LLMProviderError(Exception):
    status_code = 503

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class LLMConfigurationError(LLMProviderError):
    status_code = 503


class LLMAuthenticationError(LLMProviderError):
    status_code = 401


class LLMRateLimitError(LLMProviderError):
    status_code = 429


class LLMInvalidModelError(LLMProviderError):
    status_code = 400
