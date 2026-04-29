# Phase 4 Summaries and Reports

This phase adds topic-wise summaries and saved report generation.

Included:

- `POST /summaries/generate`
- `GET /summaries/{id}`
- `POST /reports/generate`
- `GET /reports/{id}`
- Summary, Report, and ReportSection database models
- Workspace-scoped retrieval for source-grounded synthesis
- Prompt templates for summaries and reports
- Structured summary output with key points and citations
- Structured report output with title, introduction, sections, conclusion, citations, and source chunks
- Report validation before database persistence

Not included yet:

- Frontend summary/report workflows
- Export formats such as PDF or Markdown
- Advanced bibliography formatting
