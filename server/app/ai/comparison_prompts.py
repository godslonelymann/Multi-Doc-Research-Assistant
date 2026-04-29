def build_comparison_prompt(topic: str, grouped_context: str) -> str:
    return f"""
You are comparing multiple uploaded research documents.

Rules:
- Use only the provided grouped source context.
- Do not use outside knowledge.
- Do not invent similarities, differences, or conflicts.
- Compare the documents at a deep, high-level, contextful level: themes, methods, evidence, findings, assumptions, limitations, agreements, and disagreements.
- Cite every item with the exact source labels provided, such as D1-S2.
- If evidence is weak, say so and avoid labeling it as a conflict.
- Return only valid JSON, with no markdown fences.

JSON shape:
{{
  "summary": "short overall comparison",
  "similarities": [
    {{"point": "shared point", "citations": ["D1-S1", "D2-S1"]}}
  ],
  "differences": [
    {{"point": "difference", "citations": ["D1-S2", "D2-S3"]}}
  ],
  "conflicts": [
    {{
      "claim_a": "first disagreeing claim",
      "citations_a": ["D1-S2"],
      "claim_b": "second disagreeing claim",
      "citations_b": ["D2-S3"],
      "explanation": "why these claims appear to disagree",
      "confidence": "low|medium|high"
    }}
  ]
}}

Comparison topic:
{topic}

Grouped source context:
{grouped_context}
""".strip()


def build_conflict_prompt(topic: str, grouped_context: str) -> str:
    return f"""
You are detecting possible conflicts across uploaded research documents.

Rules:
- Use only the provided grouped source context.
- Do not use outside knowledge.
- Identify a conflict only when sources clearly disagree.
- If evidence is weak, mark confidence as low and explain the uncertainty.
- Cite both sides with exact source labels, such as D1-S2.
- Return only valid JSON, with no markdown fences.

JSON shape:
{{
  "summary": "short summary of whether conflicts were found",
  "conflicts": [
    {{
      "claim_a": "first claim",
      "citations_a": ["D1-S1"],
      "claim_b": "conflicting claim",
      "citations_b": ["D2-S2"],
      "explanation": "why these claims appear to disagree",
      "confidence": "low|medium|high"
    }}
  ]
}}

Conflict detection topic:
{topic}

Grouped source context:
{grouped_context}
""".strip()
