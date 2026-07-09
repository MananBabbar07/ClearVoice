import { ExternalLink, Mail, Zap } from "lucide-react"
import GithubIcon from "../components/GithubIcon"
import { FOUNDER, LINKS } from "../constants"

const CONTACTS = [
  {
    icon: GithubIcon,
    label: "GitHub",
    value: "MananBabbar07/ClearVoice",
    href: LINKS.github,
    desc: "Report issues, contribute, or explore the source code.",
  },
  {
    icon: Zap,
    label: "API",
    value: "Hugging Face Spaces",
    href: LINKS.api,
    desc: "Direct access to the verification endpoint for integrations.",
  },
  {
    icon: ExternalLink,
    label: "Live demo",
    value: "clear-voice-five.vercel.app",
    href: LINKS.demo,
    desc: "Try the deployed version of ClearVoice in your browser.",
  },
  {
    icon: Mail,
    label: "Reach out",
    value: FOUNDER.name,
    href: FOUNDER.github,
    desc: "Open a GitHub issue or connect via profile for questions and feedback.",
  },
]

export default function ContactSection() {
  return (
    <section id="contact" className="section section--last">
      <div className="section__header">
        <p className="section__eyebrow">Contact</p>
        <h2 className="section__title">Get in touch</h2>
        <p className="section__desc">
          Questions, feedback, or collaboration — pick whichever channel works best for you.
        </p>
      </div>

      <div className="contact-grid">
        {CONTACTS.map(({ icon: Icon, label, value, href, desc }) => (
          <a key={label} href={href} target="_blank" rel="noopener noreferrer" className="contact-card">
            <div className="contact-card__icon">
              <Icon size={18} strokeWidth={1.5} />
            </div>
            <p className="contact-card__label">{label}</p>
            <p className="contact-card__value">{value}</p>
            <p className="contact-card__desc">{desc}</p>
          </a>
        ))}
      </div>
    </section>
  )
}
