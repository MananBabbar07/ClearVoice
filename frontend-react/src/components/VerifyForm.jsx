import { Loader2, ArrowRight, RotateCcw } from "lucide-react"
import { SAMPLE_CLAIMS } from "../constants"

export default function VerifyForm({ claim, loading, onClaimChange, onVerify, onClear }) {
  return (
    <section id="verify" className="hero-section">
      <div className="hero-section__content">
        <p className="hero-section__eyebrow">PubMed-backed verification</p>
        <h1 className="hero-section__title">
          Check health claims against real research
        </h1>
        <p className="hero-section__desc">
          Enter any health claim. ClearVoice searches live peer-reviewed studies,
          scores evidence quality, and returns a transparent verdict.
        </p>
      </div>

      <div className="verify-card">
        <label htmlFor="claim-input" className="verify-card__label">
          Health claim
        </label>
        <textarea
          id="claim-input"
          value={claim}
          onChange={(e) => onClaimChange(e.target.value)}
          placeholder="e.g. Vitamin C prevents colds..."
          className="verify-card__input"
          rows={3}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault()
              onVerify()
            }
          }}
        />

        <div className="sample-claims">
          <span className="sample-claims__label">Try an example</span>
          <div className="sample-claims__list">
            {SAMPLE_CLAIMS.map((sample) => (
              <button
                key={sample}
                type="button"
                className="btn btn-chip"
                disabled={loading}
                onClick={() => onClaimChange(sample)}
              >
                {sample}
              </button>
            ))}
          </div>
        </div>

        <div className="verify-card__actions">
          <p className="verify-card__hint">Enter to submit · Shift+Enter for new line</p>
          <div className="verify-card__buttons">
            {(claim.trim() || loading) && (
              <button
                type="button"
                className="btn btn-ghost"
                disabled={loading}
                onClick={onClear}
              >
                <RotateCcw size={16} />
                Clear
              </button>
            )}
            <button
              type="button"
              className="btn btn-primary"
              disabled={loading || !claim.trim()}
              onClick={onVerify}
            >
              {loading ? (
                <>
                  <Loader2 size={16} className="spin" />
                  Analyzing
                </>
              ) : (
                <>
                  Verify claim
                  <ArrowRight size={16} />
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </section>
  )
}
