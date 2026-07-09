import { ExternalLink } from "lucide-react"
import GithubIcon from "./GithubIcon"
import { FOUNDER, LINKS } from "../constants"

export default function Footer() {
  return (
    <footer className="site-footer">
      <div className="site-footer__inner">
        <div className="site-footer__brand">
          <span className="site-logo__mark site-logo__mark--sm">CV</span>
          <div>
            <p className="site-footer__name">ClearVoice</p>
            <p className="site-footer__tagline">Evidence-backed health claim verification</p>
          </div>
        </div>

        <div className="site-footer__links">
          <a href={LINKS.github} target="_blank" rel="noopener noreferrer" className="btn btn-ghost btn-sm">
            <GithubIcon size={15} />
            Repository
          </a>
          <a href={LINKS.profile} target="_blank" rel="noopener noreferrer" className="btn btn-ghost btn-sm">
            {FOUNDER.name}
          </a>
          <a href={LINKS.demo} target="_blank" rel="noopener noreferrer" className="btn btn-ghost btn-sm">
            Demo
            <ExternalLink size={13} />
          </a>
        </div>

        <p className="site-footer__copy">
          Built by {FOUNDER.name} · PubMed-powered · {new Date().getFullYear()}
        </p>
      </div>
    </footer>
  )
}
