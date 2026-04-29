import CitationList from "./CitationList.jsx";

function EvidenceSnippets({ chunks = [] }) {
  if (!chunks.length) {
    return null;
  }

  return (
    <section className="mt-8 border-t border-[#e8e8ed] pt-6">
      <h3 className="text-sm font-semibold text-[#1d1d1f]">Evidence used</h3>
      <div className="mt-3 divide-y divide-[#e8e8ed]">
        {chunks.map((chunk) => (
          <article key={chunk.vector_id} className="py-3 first:pt-0 last:pb-0">
            <p className="text-xs font-medium text-[#86868b]">
              {chunk.document_name}
              {chunk.page_number ? `, page ${chunk.page_number}` : ""} · chunk {chunk.chunk_index}
            </p>
            <p className="mt-2 line-clamp-4 text-sm leading-6 text-[#424245]">{chunk.text}</p>
          </article>
        ))}
      </div>
    </section>
  );
}

function CompareGroup({ title, items = [], type }) {
  if (!items.length) {
    return null;
  }

  return (
    <section className="border-t border-[#e8e8ed] pt-6">
      <h3 className="text-xs font-semibold uppercase text-[#86868b]">{title}</h3>
      <div className="mt-4 space-y-5">
        {items.map((item, index) => (
          <div key={`${title}-${index}`} className="text-sm leading-7 text-[#424245]">
            {type === "conflict" ? (
              <>
                <p>
                  <span className="font-semibold text-[#1d1d1f]">Claim A:</span> {item.claim_a}
                </p>
                <CitationList citations={item.citations_a || []} />
                <p className="mt-3">
                  <span className="font-semibold text-[#1d1d1f]">Claim B:</span> {item.claim_b}
                </p>
                <CitationList citations={item.citations_b || []} />
                <p className="mt-3">{item.explanation}</p>
              </>
            ) : (
              <>
                <p>{item.point}</p>
                <CitationList citations={item.citations || []} />
              </>
            )}
          </div>
        ))}
      </div>
    </section>
  );
}

function ReportView({ report }) {
  return (
    <div className="space-y-8">
      <section>
        <h3 className="text-2xl font-semibold text-[#1d1d1f]">{report.title}</h3>
        <p className="mt-4 whitespace-pre-wrap text-sm leading-7 text-[#424245]">{report.introduction}</p>
      </section>
      {report.sections?.map((section) => (
        <section key={`${section.order_index}-${section.title}`} className="border-t border-[#e8e8ed] pt-6">
          <h3 className="text-lg font-semibold text-[#1d1d1f]">{section.title}</h3>
          <p className="mt-3 whitespace-pre-wrap text-sm leading-7 text-[#424245]">{section.content}</p>
          <CitationList citations={section.citations || []} />
        </section>
      ))}
      <section className="border-t border-[#e8e8ed] pt-6">
        <h3 className="text-lg font-semibold text-[#1d1d1f]">Conclusion</h3>
        <p className="mt-3 whitespace-pre-wrap text-sm leading-7 text-[#424245]">{report.conclusion}</p>
        <CitationList citations={report.citations || []} />
      </section>
    </div>
  );
}

function ResultPanel({ mode, result }) {
  if (!result) {
    return (
      <div className="surface p-6 sm:p-8">
        <p className="text-xs font-semibold uppercase text-[#86868b]">Result</p>
        <h3 className="mt-4 text-2xl font-semibold text-[#1d1d1f]">Nothing generated yet</h3>
        <p className="mt-3 max-w-2xl text-sm leading-6 text-[#6e6e73]">
          Choose a mode, enter a focused prompt, and the output will appear here with the same calm reading layout.
        </p>
      </div>
    );
  }

  return (
    <article className="surface p-6 sm:p-8">
      {mode === "ask" ? (
        <>
          <p className="text-xs font-semibold uppercase text-[#86868b]">Answer</p>
          <div className="mt-3 text-sm text-[#6e6e73]">
            {result.uploaded_document_count ?? 0} uploaded sources · {result.ready_document_count ?? 0} ready ·{" "}
            {result.used_document_count ?? result.document_names?.length ?? 0} used ·{" "}
            {result.evidence_count ?? result.source_chunks?.length ?? 0} evidence snippets
          </div>
          <p className="mt-5 whitespace-pre-wrap text-base leading-8 text-[#1d1d1f]">{result.answer}</p>
          <CitationList citations={result.citations || []} />
          <EvidenceSnippets chunks={result.source_chunks || []} />
        </>
      ) : null}

      {mode === "summarize" ? (
        <>
          <p className="text-xs font-semibold uppercase text-[#86868b]">Summary</p>
          <h3 className="mt-4 text-2xl font-semibold text-[#1d1d1f]">{result.topic}</h3>
          <p className="mt-4 whitespace-pre-wrap text-base leading-8 text-[#1d1d1f]">{result.summary}</p>
          {result.key_points?.length ? (
            <section className="mt-8 border-t border-[#e8e8ed] pt-6">
              <h3 className="text-xs font-semibold uppercase text-[#86868b]">Key points</h3>
              <div className="mt-4 space-y-5">
                {result.key_points.map((point, index) => (
                  <div key={index}>
                    <p className="text-sm leading-7 text-[#424245]">{point.point}</p>
                    <CitationList citations={point.citations || []} />
                  </div>
                ))}
              </div>
            </section>
          ) : null}
        </>
      ) : null}

      {mode === "compare" ? (
        <div className="space-y-8">
          <section>
            <p className="text-xs font-semibold uppercase text-[#86868b]">Comparison</p>
            <p className="mt-5 whitespace-pre-wrap text-base leading-8 text-[#1d1d1f]">{result.summary}</p>
          </section>
          <CompareGroup title="Similarities" items={result.similarities || []} />
          <CompareGroup title="Differences" items={result.differences || []} />
          <CompareGroup title="Conflicts" items={result.conflicts || []} type="conflict" />
        </div>
      ) : null}

      {mode === "report" ? <ReportView report={result} /> : null}
    </article>
  );
}

export default ResultPanel;
