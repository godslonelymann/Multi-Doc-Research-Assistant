from app.ai.base import LLMProvider
from app.ai.llm.groq_client import GroqClient


class GroqLLMProvider(LLMProvider):
    def __init__(self, client: GroqClient | None = None) -> None:
        self.client = client or GroqClient()

    async def generate(self, prompt: str) -> str:
        return await self.client.generate(prompt)


def get_llm_provider() -> LLMProvider:
    return GroqLLMProvider()
