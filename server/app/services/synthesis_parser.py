import json

from app.schemas.chat import Citation
from app.utils.citations import normalize_source_label


class SynthesisParser:
    def parse_json_object(self, raw_output: str) -> dict:
        cleaned = raw_output.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]
        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {}

    def resolve_citations(self, labels: list[str], citation_map: dict[str, Citation]) -> list[Citation]:
        normalized_map = {normalize_source_label(label): citation for label, citation in citation_map.items()}
        resolved: list[Citation] = []
        for label in labels:
            normalized = normalize_source_label(label)
            if normalized in normalized_map:
                resolved.append(normalized_map[normalized])
        return resolved

    def citation_dicts(self, citations: list[Citation]) -> list[dict]:
        return [citation.model_dump() for citation in citations]
