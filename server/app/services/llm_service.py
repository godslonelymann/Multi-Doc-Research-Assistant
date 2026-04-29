from app.ai.prompts import build_grounded_answer_prompt
from app.ai.provider import get_llm_provider
from app.schemas.chat import SourceChunk
from app.services.context_builder import ContextBuilder


class LLMService:
    def __init__(self, context_builder: ContextBuilder | None = None) -> None:
        self.context_builder = context_builder or ContextBuilder()
        self.provider = get_llm_provider()

    async def answer_question(self, question: str, source_chunks: list[SourceChunk]) -> str:
        if not source_chunks:
            return "The uploaded sources do not contain enough information to answer that."

        context, _ = self.context_builder.build(source_chunks)
        prompt = build_grounded_answer_prompt(question=question, context=context)
        return await self.provider.generate(prompt)

    async def generate(self, prompt: str) -> str:
        return await self.provider.generate(prompt)
