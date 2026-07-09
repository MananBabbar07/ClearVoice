import { ExternalLink } from "lucide-react"
import GithubIcon from "../components/GithubIcon"
import { FOUNDER, LINKS } from "../constants"

export default function FoundersSection() {
  return (
    <section id="founders" className="section">
      <div className="section__header">
        <p className="section__eyebrow">Founder</p>
        <h2 className="section__title">Built with intent</h2>
        <p className="section__desc">
          ClearVoice started as a project to fight medical misinformation with open, traceable evidence.
        </p>
      </div>

      <article className="founder-card">
        <div className="founder-card__avatar">{FOUNDER.name.split(" ").map((n) => n[0]).join("")}</div>
        <div className="founder-card__body">
          <div className="founder-card__top">
            <div>
              <h3>{FOUNDER.name}</h3>
              <p className="founder-card__role">{FOUNDER.role}</p>
            </div>
            <div className="founder-card__actions">
              <a href={FOUNDER.github} target="_blank" rel="noopener noreferrer" className="btn btn-outline btn-sm">
                <GithubIcon size={15} />
                GitHub
              </a>
              <a href={LINKS.github} target="_blank" rel="noopener noreferrer" className="btn btn-primary btn-sm">
                View project
                <ExternalLink size={13} />
              </a>
            </div>
          </div>
          <p className="founder-card__bio">{FOUNDER.bio}</p>
        </div>
      </article>
    </section>
  )
}
