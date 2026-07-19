import {
  ChevronDown,
  ChevronUp,
  ExternalLink,
  Zap,
  Layers,
  FileText,
  Lightbulb,
  BookOpen,
} from "lucide-react"
import VerdictBadge from "./VerdictBadge"

function StanceDot({ stance }) {
  const cls =
    stance === "SUPPORTS"
      ? "stance-dot--supports"
      : stance === "CONTRADICTS"
        ? "stance-dot--contradicts"
        : "stance-dot--neutral"
  return <span className={`stance-dot ${cls}`} aria-hidden="true" />
}

export default function ResultsPanel({ result, expandedPapers, onTogglePaper }) {
  if (!result) return null

  return (
    <div className="results">
      <div className="results-card">
        <div className="results-card__header">
          <VerdictBadge verdict={result.verdict} />
          <div className="results-stats">
            <div className="results-stat">
              <span className="results-stat__value">{Math.round(result.confidence * 100)}%</span>
              <span className="results-stat__label">Confidence</span>
            </div>
            <div className="results-stat">
              <span className="results-stat__value">{result.evidence_strength || "—"}</span>
              <span className="results-stat__label">Evidence</span>
            </div>
          </div>
        </div>

        {result.cached && (
          <p className="results-cache">
            <Zap size={13} />
            Served from cache
          </p>
        )}

        {result.decomposition?.is_complex && (
          <div className="results-block results-block--accent">
            <div className="results-block__heading">
              <Layers size={15} />
              Complex claim — {result.decomposition.sub_claims.length} sub-claims analyzed
            </div>
            <ul className="results-list">
              {result.decomposition.sub_claims.map((sc, i) => (
                <li key={i}>{sc}</li>
              ))}
            </ul>
          </div>
        )}

        {result.plain_english && (
          <div className="results-block">
            <div className="results-block__heading">
              <FileText size={15} />
              In plain English
            </div>
            <p className="results-block__text">{result.plain_english}</p>
          </div>
        )}

        {result.takeaway && (
          <div className="results-takeaway">
            <Lightbulb size={15} />
            <p><strong>Takeaway.</strong> {result.takeaway}</p>
          </div>
        )}
      </div>

      <details className="results-card results-details">
        <summary className="results-details__summary">
          <BookOpen size={15} />
          Technical explanation
        </summary>
        <p className="results-block__text">{result.explanation}</p>

        {result.citations?.length > 0 && (
          <div className="citations">
            <p className="citations__title">Citations</p>
            {result.citations.map((c, i) => (
              <div key={i} className="citation-row">
                {c.pmid && /^\d+$/.test(c.pmid) ? (
                  <a
                    href={`https://pubmed.ncbi.nlm.nih.gov/${c.pmid}/`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="citation-link"
                  >
                    {c.title}
                    <ExternalLink size={12} />
                  </a>
                ) : (
                  <span className="citation-text">{c.title}</span>
                )}
              </div>
            ))}
          </div>
        )}
      </details>

      {result.judge && result.judge.overall_quality && result.judge.overall_quality !== "UNKNOWN" && (
        <div className="results-card">
          <div className="results-card__row">
            <div className="results-block__heading">Evidence quality</div>
            <span className={`quality-badge quality-badge--${result.judge.overall_quality.toLowerCase()}`}>
              {result.judge.overall_quality}
            </span>
          </div>
          <p className="results-block__text results-block__text--muted">
            {result.judge.quality_explanation}
          </p>

          <div className="papers-list">
            {result.judge.papers.map((jp, i) => {
              const paper = result.papers?.[i]
              return (
                <div key={i} className="paper-item">
                  <button
                    type="button"
                    className="paper-item__toggle"
                    onClick={() => onTogglePaper(i)}
                  >
                    <div className="paper-item__title">
                      <StanceDot stance={jp.stance} />
                      <span>{paper?.title} ({paper?.year})</span>
                    </div>
                    {expandedPapers[i] ? (
                      <ChevronUp size={16} className="paper-item__chevron" />
                    ) : (
                      <ChevronDown size={16} className="paper-item__chevron" />
                    )}
                  </button>

                  {expandedPapers[i] && paper && (
                    <div className="paper-item__body">
                      <div className="paper-metrics">
                        <div className="paper-metric">
                          <span>Study type</span>
                          <strong>{jp.study_type}</strong>
                        </div>
                        <div className="paper-metric">
                          <span>Quality</span>
                          <strong>{jp.quality_score}/5</strong>
                        </div>
                        <div className="paper-metric">
                          <span>Similarity</span>
                          <strong>{paper.similarity}</strong>
                        </div>
                      </div>
                      <p className="paper-item__summary">{jp.one_line_summary}</p>
                      <p className="paper-item__journal">{paper.journal}</p>
                      <a
                        href={`https://pubmed.ncbi.nlm.nih.gov/${paper.pmid}/`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="citation-link citation-link--sm"
                      >
                        View on PubMed
                        <ExternalLink size={10} />
                      </a>
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}
