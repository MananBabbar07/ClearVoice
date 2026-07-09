import { useState } from "react"
import axios from "axios"
import FontLoader from "./components/FontLoader"
import Header from "./components/Header"
import Footer from "./components/Footer"
import VerifyForm from "./components/VerifyForm"
import ResultsPanel from "./components/ResultsPanel"
import AboutSection from "./sections/AboutSection"
import FoundersSection from "./sections/FoundersSection"
import ContactSection from "./sections/ContactSection"
import { API_URL } from "./constants"
import "./App.css"

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
    setExpandedPapers({})

    try {
      const response = await axios.post(`${API_URL}/verify`, { claim }, { timeout: 90000 })
      setResult(response.data)
    } catch {
      setError("Failed to connect to API. Please try again.")
    } finally {
      setLoading(false)
    }
  }

  const handleClear = () => {
    setClaim("")
    setResult(null)
    setError(null)
    setExpandedPapers({})
  }

  const handleNavigate = (id) => {
    document.getElementById(id)?.scrollIntoView({ behavior: "smooth", block: "start" })
  }

  const togglePaper = (index) => {
    setExpandedPapers((prev) => ({ ...prev, [index]: !prev[index] }))
  }

  return (
    <>
      <FontLoader />
      <div className="app">
        <Header onNavigate={handleNavigate} />

        <main className="main">
          <VerifyForm
            claim={claim}
            loading={loading}
            onClaimChange={setClaim}
            onVerify={verifyClaim}
            onClear={handleClear}
          />

          {error && (
            <div className="error-banner" role="alert">
              {error}
            </div>
          )}

          <ResultsPanel
            result={result}
            expandedPapers={expandedPapers}
            onTogglePaper={togglePaper}
          />

          <AboutSection />
          <FoundersSection />
          <ContactSection />
        </main>

        <Footer />
      </div>
    </>
  )
}
