import { useEffect } from "react"

const FONTS = [
  "https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:ital,wght@0,400;0,500;0,600;1,400&family=Instrument+Serif:ital@0;1&display=swap",
]

export default function FontLoader() {
  useEffect(() => {
    FONTS.forEach((href) => {
      if (document.querySelector(`link[href="${href}"]`)) return
      const link = document.createElement("link")
      link.rel = "stylesheet"
      link.href = href
      document.head.appendChild(link)
    })
  }, [])

  return null
}
