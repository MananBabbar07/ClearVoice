import { useState } from "react"
import axios from "axios"
import { Microscope, Mic, Loader2, CheckCircle, XCircle, AlertTriangle, Info, ChevronDown, ChevronUp, ExternalLink } from "lucide-react"

const API_URL = "https://manan77709-clearvoice-api.hf.space"
// const API_URL = "http://localhost:8000"
export default function App() {
  const [claim, setClaim] = useState("")
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [expandedPapers, setExpandedPapers] = useState({})

  const verifyClaim = async () => {
    if (!claim.trim()) return
    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const response = await axios.post(`${API_URL}/verify`, { claim }, { timeout: 90000 })
      setResult(response.data)
      
    } catch (err) {
      setError("Failed to connect to API. Please try again.")
    } finally {
      setLoading(false)
    }
  }

  const togglePaper = (index) => {
    setExpandedPapers(prev => ({ ...prev, [index]: !prev[index] }))
  }

  const VerdictBadge = ({ verdict }) => {
    const config = {
      TRUE: { icon: CheckCircle, bg: "bg-green-500/20", border: "border-green-500", text: "text-green-400", label: "✅ TRUE" },
      FALSE: { icon: XCircle, bg: "bg-red-500/20", border: "border-red-500", text: "text-red-400", label: "❌ FALSE" },
      MISLEADING: { icon: AlertTriangle, bg: "bg-yellow-500/20", border: "border-yellow-500", text: "text-yellow-400", label: "⚠️ MISLEADING" },
      "INSUFFICIENT EVIDENCE": { icon: Info, bg: "bg-blue-500/20", border: "border-blue-500", text: "text-blue-400", label: "ℹ️ INSUFFICIENT EVIDENCE" },
      ERROR: { icon: XCircle, bg: "bg-gray-500/20", border: "border-gray-500", text: "text-gray-400", label: "ERROR" },
    }
    const c = config[verdict] || config.ERROR
    return (
      <div className={`inline-flex items-center gap-2 px-4 py-2 rounded-full border ${c.bg} ${c.border} ${c.text} text-lg font-bold`}>
        {c.label}
      </div>
    )
  }

  const StanceIcon = ({ stance }) => {
    if (stance === "SUPPORTS") return <span className="text-green-400">🟢</span>
    if (stance === "CONTRADICTS") return <span className="text-red-400">🔴</span>
    return <span className="text-gray-400">⚪</span>
  }

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      {/* Header */}
      <div className="border-b border-gray-800 bg-gray-900/50 backdrop-blur">
        <div className="max-w-4xl mx-auto px-6 py-4 flex items-center gap-3">
          <Microscope className="text-blue-400" size={28} />
          <div>
            <h1 className="text-xl font-bold text-white">ClearVoice</h1>
            <p className="text-xs text-gray-400">Medical Misinformation Checker</p>
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-6 py-12">
        {/* Hero */}
        <div className="text-center mb-12">
          <h2 className="text-4xl font-bold text-white mb-4">
            Verify Health Claims with <span className="text-blue-400">Real Science</span>
          </h2>
          <p className="text-gray-400 text-lg max-w-2xl mx-auto">
            Every verdict is backed by peer-reviewed PubMed studies, with full transparency on evidence quality and study types.
          </p>
        </div>

        {/* Input */}
        <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6 mb-8">
          <label className="block text-sm text-gray-400 mb-2">Enter a health claim</label>
          <textarea
            value={claim}
            onChange={(e) => setClaim(e.target.value)}
            placeholder="e.g. Vitamin C prevents colds..."
            className="w-full bg-gray-800 border border-gray-700 rounded-xl p-4 text-white placeholder-gray-500 resize-none focus:outline-none focus:border-blue-500 transition-colors"
            rows={3}
            onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); verifyClaim() } }}
          />
          <div className="flex justify-between items-center mt-4">
            <p className="text-xs text-gray-500">Press Enter to verify</p>
            <button
              onClick={verifyClaim}
              disabled={loading || !claim.trim()}
              className="flex items-center gap-2 bg-blue-600 hover:bg-blue-500 disabled:bg-gray-700 disabled:text-gray-500 text-white font-semibold px-6 py-3 rounded-xl transition-colors"
            >
              {loading ? <Loader2 size={18} className="animate-spin" /> : <Microscope size={18} />}
              {loading ? "Analyzing..." : "Verify Claim"}
            </button>
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 mb-6 text-red-400">
            {error}
          </div>
        )}

        {/* Results */}
        {result && (
          <div className="space-y-6">

            {/* Verdict Card */}
            <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6">
              <div className="flex flex-wrap items-center justify-between gap-4 mb-4">
                <VerdictBadge verdict={result.verdict} />
                <div className="flex gap-4">
                  <div className="text-center">
                    <p className="text-2xl font-bold text-white">{Math.round(result.confidence * 100)}%</p>
                    <p className="text-xs text-gray-400">Confidence</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold text-white">{result.evidence_strength || "—"}</p>
                    <p className="text-xs text-gray-400">Evidence</p>
                  </div>
                </div>
              </div>

              {result.cached && (
                <p className="text-xs text-blue-400 mb-3">⚡ Served from cache</p>
              )}

              {/* Decomposition */}
              {result.decomposition?.is_complex && (
                <div className="bg-blue-500/10 border border-blue-500/20 rounded-xl p-3 mb-4">
                  <p className="text-sm text-blue-400 font-medium mb-1">🔍 Complex claim — analyzed {result.decomposition.sub_claims.length} sub-claims:</p>
                  {result.decomposition.sub_claims.map((sc, i) => (
                    <p key={i} className="text-sm text-gray-300 ml-2">• {sc}</p>
                  ))}
                </div>
              )}

              {/* Plain English */}
              {result.plain_english && (
                <div className="mb-4">
                  <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-2">💬 In Plain English</h3>
                  <p className="text-gray-200 leading-relaxed">{result.plain_english}</p>
                </div>
              )}

              {/* Takeaway */}
              {result.takeaway && (
                <div className="bg-gray-800 rounded-xl p-3">
                  <p className="text-sm text-gray-300"><span className="text-yellow-400 font-semibold">💡 Takeaway:</span> {result.takeaway}</p>
                </div>
              )}
            </div>

            {/* Technical Explanation */}
            <details className="bg-gray-900 border border-gray-800 rounded-2xl p-6">
              <summary className="cursor-pointer text-sm font-semibold text-gray-400 uppercase tracking-wide">🔬 Technical Explanation</summary>
              <p className="text-gray-300 mt-3 leading-relaxed">{result.explanation}</p>

              {result.citations?.length > 0 && (
                <div className="mt-4">
                  <p className="text-sm font-semibold text-gray-400 mb-2">Citations:</p>
                  {result.citations.map((c, i) => (
                    <div key={i} className="flex items-start gap-2 mb-1">
                      <span className="text-gray-500 text-sm">•</span>
                      {c.pmid && /^\d+$/.test(c.pmid) ? (
                        <a href={`https://pubmed.ncbi.nlm.nih.gov/${c.pmid}/`} target="_blank" rel="noopener noreferrer"
                          className="text-blue-400 hover:underline text-sm flex items-center gap-1">
                          {c.title} <ExternalLink size={12} />
                        </a>
                      ) : (
                        <span className="text-gray-300 text-sm">{c.title}</span>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </details>

            {/* Evidence Quality */}
            {result.judge && result.judge.overall_quality !== "UNKNOWN" && (
              <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wide">📊 Evidence Quality</h3>
                  <span className={`text-sm font-bold px-3 py-1 rounded-full ${
                    result.judge.overall_quality === "HIGH" ? "bg-green-500/20 text-green-400" :
                    result.judge.overall_quality === "MEDIUM" ? "bg-yellow-500/20 text-yellow-400" :
                    "bg-red-500/20 text-red-400"
                  }`}>{result.judge.overall_quality}</span>
                </div>
                <p className="text-gray-400 text-sm mb-4">{result.judge.quality_explanation}</p>

                <div className="space-y-3">
                  {result.judge.papers.map((jp, i) => {
                    const paper = result.papers?.[i]
                    return (
                      <div key={i} className="border border-gray-800 rounded-xl overflow-hidden">
                        <button
                          onClick={() => togglePaper(i)}
                          className="w-full flex items-center justify-between p-4 hover:bg-gray-800 transition-colors text-left"
                        >
                          <div className="flex items-center gap-2">
                            <StanceIcon stance={jp.stance} />
                            <span className="text-sm text-gray-200">{paper?.title} ({paper?.year})</span>
                          </div>
                          {expandedPapers[i] ? <ChevronUp size={16} className="text-gray-400" /> : <ChevronDown size={16} className="text-gray-400" />}
                        </button>

                        {expandedPapers[i] && paper && (
                          <div className="px-4 pb-4 border-t border-gray-800 pt-3">
                            <div className="grid grid-cols-3 gap-3 mb-3">
                              <div className="bg-gray-800 rounded-lg p-2 text-center">
                                <p className="text-xs text-gray-400">Study Type</p>
                                <p className="text-sm font-semibold text-white">{jp.study_type}</p>
                              </div>
                              <div className="bg-gray-800 rounded-lg p-2 text-center">
                                <p className="text-xs text-gray-400">Quality</p>
                                <p className="text-sm font-semibold text-white">{jp.quality_score}/5</p>
                              </div>
                              <div className="bg-gray-800 rounded-lg p-2 text-center">
                                <p className="text-xs text-gray-400">Similarity</p>
                                <p className="text-sm font-semibold text-white">{paper.similarity}</p>
                              </div>
                            </div>
                            <p className="text-sm text-gray-300 mb-2">{jp.one_line_summary}</p>
                            <p className="text-xs text-gray-400 mb-2">{paper.journal}</p>
                            <a href={`https://pubmed.ncbi.nlm.nih.gov/${paper.pmid}/`} target="_blank" rel="noopener noreferrer"
                              className="text-blue-400 hover:underline text-xs flex items-center gap-1">
                              View on PubMed <ExternalLink size={10} />
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
        )}
      </div>
    </div>
  )
}