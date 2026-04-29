# Phase 3 Comparison and Conflict Detection

This phase adds structured document comparison and basic conflict detection.

Included:

- `POST /compare`
- `POST /conflicts`
- Document-scoped retrieval for selected workspace documents
- Grouped context by document
- Separate comparison and conflict prompt templates
- Structured response schemas for summaries, similarities, differences, conflicts, citations, and source chunks
- Conservative conflict prompting that avoids overclaiming weak disagreement

Not included yet:

- Report generation
- Frontend comparison workflow
- Advanced claim extraction or entailment scoring
