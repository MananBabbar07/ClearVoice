import { useState } from "react"
import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { describe, it, expect, vi } from "vitest"
import ResultsPanel from "../ResultsPanel"

function StatefulResultsPanel({ result }) {
  const [expandedPapers, setExpandedPapers] = useState({})
  const onTogglePaper = (key) => {
    setExpandedPapers((prev) => ({ ...prev, [key]: !prev[key] }))
  }
  return <ResultsPanel result={result} expandedPapers={expandedPapers} onTogglePaper={onTogglePaper} />
}

describe("ResultsPanel", () => {
  it("renders the verdict, stats, and multiple sub_results", () => {
    const result = {
      verdict: "MISLEADING",
      confidence: 0.72,
      evidence_strength: "Moderate",
      plain_english: "One sub-claim is supported while the other is false.",
      takeaway: "Verify individual claims separately.",
      explanation: "Sub-claim breakdown technical details.",
      sub_results: [
        { sub_claim: "Smoking causes lung cancer", verdict: "TRUE", confidence: 0.95, papers: [{ pmid: "1" }, { pmid: "2" }] },
        { sub_claim: "Antibiotics cure viral flu", verdict: "FALSE", confidence: 0.92, papers: [{ pmid: "3" }] },
      ],
      papers: [],
      judge: { overall_quality: "UNKNOWN" },
      meta: { model_used: { decomposer: "openai/gpt-oss-120b", verdict: ["openai/gpt-oss-120b", "openai/gpt-oss-120b"] } },
    }

    render(<StatefulResultsPanel result={result} />)

    expect(screen.getByText("Misleading")).toBeInTheDocument()
    expect(screen.getByText("72%")).toBeInTheDocument()
    expect(screen.getByText(/complex claim — 2 sub-claims analyzed/i)).toBeInTheDocument()
    expect(screen.getByText("Smoking causes lung cancer")).toBeInTheDocument()
    expect(screen.getByText("Antibiotics cure viral flu")).toBeInTheDocument()
    expect(screen.getByText("2 studies")).toBeInTheDocument()
    expect(screen.getByText("1 studies")).toBeInTheDocument()
  })

  it("pairs judge papers with result papers by pmid regardless of array order", async () => {
    const user = userEvent.setup()
    const result = {
      verdict: "TRUE",
      confidence: 0.9,
      evidence_strength: "Strong",
      explanation: "Supported by trials.",
      papers: [
        { pmid: "2002", title: "Second Order Study", journal: "Lancet", year: 2022, similarity: 0.71, study_type: "Review" },
        { pmid: "1001", title: "First Matched Study", journal: "NEJM", year: 2024, similarity: 0.89, study_type: "Meta-Analysis" },
      ],
      judge: {
        overall_quality: "HIGH",
        quality_explanation: "High quality evidence.",
        papers: [
          {
            pmid: "1001",
            paper_number: 1,
            stance: "SUPPORTS",
            quality_score: 5,
            study_type: "Meta-Analysis",
            one_line_summary: "Strong support in meta-analysis.",
          },
          {
            pmid: "2002",
            paper_number: 2,
            stance: "NEUTRAL",
            quality_score: 3,
            study_type: "Review",
            one_line_summary: "Neutral findings.",
          },
        ],
      },
    }

    render(<StatefulResultsPanel result={result} />)

    const firstToggle = screen.getByRole("button", { name: /First Matched Study \(2024\)/i })
    await user.click(firstToggle)

    expect(screen.getByText("NEJM")).toBeInTheDocument()
    expect(screen.getByText("0.89")).toBeInTheDocument()
    expect(screen.getByText("Meta-Analysis")).toBeInTheDocument()
    expect(screen.getByRole("link", { name: /view on pubmed/i })).toHaveAttribute(
      "href",
      "https://pubmed.ncbi.nlm.nih.gov/1001/"
    )
  })

  it("tolerates legacy cached payloads missing sub_results, meta, and pmid", async () => {
    const user = userEvent.setup()
    const onTogglePaper = vi.fn()
    const legacyResult = {
      verdict: "FALSE",
      confidence: 0.85,
      evidence_strength: "Moderate",
      explanation: "Legacy explanation without sub_results or meta.",
      decomposition: {
        is_complex: true,
        sub_claims: ["Legacy sub-claim A", "Legacy sub-claim B"],
      },
      papers: [],
      judge: {
        overall_quality: "MEDIUM",
        quality_explanation: "Older format judge.",
        papers: [
          {
            paper_number: 1,
            stance: "CONTRADICTS",
            quality_score: 4,
            one_line_summary: "Legacy summary without pmid",
          },
        ],
      },
    }

    render(<ResultsPanel result={legacyResult} expandedPapers={{ 0: true }} onTogglePaper={onTogglePaper} />)

    expect(screen.getByText("False")).toBeInTheDocument()
    expect(screen.getByText("Legacy sub-claim A")).toBeInTheDocument()
    expect(screen.getByText("Legacy sub-claim B")).toBeInTheDocument()

    const toggle = screen.getByRole("button", { name: /Legacy summary without pmid/i })
    await user.click(toggle)
    expect(onTogglePaper).toHaveBeenCalledWith(0)
    expect(screen.getByText("Other")).toBeInTheDocument()
    expect(screen.getByText("4/5")).toBeInTheDocument()
  })
})
