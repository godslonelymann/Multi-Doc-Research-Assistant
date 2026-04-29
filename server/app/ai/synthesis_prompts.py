def build_summary_prompt(topic: str, context: str) -> str:
    return f"""
You are generating a comprehensive, high-level summary across multiple uploaded documents.

Rules:
- Use only the provided source context.
- Synthesize across sources when multiple sources support a point.
- Cover the most important themes, evidence, findings, methods, limitations, agreements, and disagreements present in the context.
- Prefer depth and specificity over generic overview text.
- Do not invent unsupported claims.
- Attach citations to key points using the exact evidence labels provided, such as Evidence 1.
- Do not generate a bibliography.
- Return only valid JSON, with no markdown fences.

JSON shape:
{{
  "summary": "substantive synthesis paragraph",
  "key_points": [
    {{"point": "specific supported point", "citations": ["Evidence 1", "Evidence 3"]}}
  ]
}}

Summary topic:
{topic}

Source context:
{context}
""".strip()


def build_report_prompt(title: str, topic: str, context: str) -> str:
    return f"""
You are generating a structured research report from uploaded source documents.

Rules:
- Use only the provided source context.
- Synthesize across sources.
- Do not invent unsupported claims.
- Build a deep, high-level, contextful report from the retrieved evidence, including important themes, findings, limitations, agreements, and disagreements.
- Keep citations attached to claims or sections using the exact evidence labels provided, such as Evidence 2.
- Do not generate a fake bibliography; use only retrieved source references.
- Return only valid JSON, with no markdown fences.

JSON shape:
{{
  "title": "{title}",
  "introduction": "source-grounded introduction with citation labels where useful",
  "sections": [
    {{
      "title": "theme or section title",
      "content": "section content grounded in source context",
      "citations": ["Evidence 1", "Evidence 2"]
    }}
  ],
  "conclusion": "source-grounded conclusion",
  "citations": ["Evidence 1", "Evidence 2"]
}}

Report topic:
{topic}

Source context:
{context}
""".strip()
