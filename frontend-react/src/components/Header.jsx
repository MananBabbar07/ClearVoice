import { ExternalLink, Menu, X } from "lucide-react"
import GithubIcon from "./GithubIcon"
import { useState } from "react"
import { LINKS, NAV_ITEMS } from "../constants"

export default function Header({ onNavigate }) {
  const [menuOpen, setMenuOpen] = useState(false)

  function handleNav(id) {
    onNavigate(id)
    setMenuOpen(false)
  }

  return (
    <header className="site-header">
      <div className="site-header__inner">
        <button type="button" className="site-logo" onClick={() => handleNav("verify")}>
          <span className="site-logo__mark">CV</span>
          <span className="site-logo__text">
            <strong>ClearVoice</strong>
            <small>Medical fact-checker</small>
          </span>
        </button>

        <nav className={`site-nav ${menuOpen ? "site-nav--open" : ""}`}>
          {NAV_ITEMS.map(({ id, label }) => (
            <button key={id} type="button" className="btn btn-ghost btn-sm" onClick={() => handleNav(id)}>
              {label}
            </button>
          ))}
          <a href={LINKS.github} target="_blank" rel="noopener noreferrer" className="btn btn-ghost btn-sm">
            <GithubIcon size={15} />
            GitHub
          </a>
          <a href={LINKS.api} target="_blank" rel="noopener noreferrer" className="btn btn-outline btn-sm">
            API
            <ExternalLink size={13} />
          </a>
          <a href={LINKS.demo} target="_blank" rel="noopener noreferrer" className="btn btn-primary btn-sm">
            Live demo
          </a>
        </nav>

        <button
          type="button"
          className="site-menu-toggle"
          aria-label={menuOpen ? "Close menu" : "Open menu"}
          onClick={() => setMenuOpen((v) => !v)}
        >
          {menuOpen ? <X size={20} /> : <Menu size={20} />}
        </button>
      </div>
    </header>
  )
}
