ANSWER_WITH_CITATIONS_PROMPT = """
Answer the research question using only retrieved document context.
Include document and page references when available.
"""


def build_grounded_answer_prompt(question: str, context: str) -> str:
    return f"""
You are a multi-document research assistant.

Rules:
- Answer only from the provided source context.
- Do not use outside knowledge.
- If the answer is not present in the source context, say: "The uploaded sources do not contain enough information to answer that."
- Be precise: answer the exact question asked and avoid broad background unless the evidence requires it.
- Do not generalize beyond the retrieved evidence. If evidence is partial, explicitly say what is known and what is not shown.
- Prefer short paragraphs or bullets. Do not add filler.
- Every factual claim must be supported by one or more evidence labels.
- Cite claims using the evidence labels exactly as provided, such as [Evidence 1].
- If multiple uploaded sources disagree or are incomplete, state that clearly instead of smoothing over the difference.

Question:
{question}

Source context:
{context}

Grounded answer:
""".strip()
