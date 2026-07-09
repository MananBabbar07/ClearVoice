import { Search, BookOpen, Scale, MessageSquare } from "lucide-react"

const STEPS = [
  {
    icon: Search,
    title: "Live PubMed search",
    text: "Your claim is searched against real-time peer-reviewed literature — not a stale offline database.",
  },
  {
    icon: Scale,
    title: "Multi-agent evaluation",
    text: "Retrieval, quality judging, and contradiction detection work together to weigh the evidence.",
  },
  {
    icon: MessageSquare,
    title: "Transparent verdict",
    text: "You get a clear verdict, confidence score, study breakdown, and plain-English explanation.",
  },
]

export default function AboutSection() {
  return (
    <section id="about" className="section">
      <div className="section__header">
        <p className="section__eyebrow">How it works</p>
        <h2 className="section__title">Science-first verification</h2>
        <p className="section__desc">
          ClearVoice evaluates health claims using live medical research. Every response cites
          actual studies with quality scores and stance analysis.
        </p>
      </div>

      <div className="steps-grid">
        {STEPS.map(({ icon: Icon, title, text }) => (
          <article key={title} className="step-card">
            <div className="step-card__icon">
              <Icon size={20} strokeWidth={1.5} />
            </div>
            <h3>{title}</h3>
            <p>{text}</p>
          </article>
        ))}
      </div>

      <div className="feature-strip">
        <div className="feature-strip__item">
          <BookOpen size={16} />
          <span>PubMedBERT semantic search</span>
        </div>
        <div className="feature-strip__item">
          <Scale size={16} />
          <span>Evidence quality scoring</span>
        </div>
        <div className="feature-strip__item">
          <MessageSquare size={16} />
          <span>Plain-English summaries</span>
        </div>
      </div>
    </section>
  )
}
