import { CheckCircle, XCircle, AlertTriangle, HelpCircle } from "lucide-react"

const VERDICT_CONFIG = {
  TRUE: {
    Icon: CheckCircle,
    label: "True",
    className: "verdict--success",
  },
  FALSE: {
    Icon: XCircle,
    label: "False",
    className: "verdict--danger",
  },
  MISLEADING: {
    Icon: AlertTriangle,
    label: "Misleading",
    className: "verdict--warning",
  },
  "INSUFFICIENT EVIDENCE": {
    Icon: HelpCircle,
    label: "Insufficient evidence",
    className: "verdict--neutral",
  },
  ERROR: {
    Icon: XCircle,
    label: "Error",
    className: "verdict--neutral",
  },
}

export default function VerdictBadge({ verdict }) {
  const config = VERDICT_CONFIG[verdict] || VERDICT_CONFIG.ERROR
  const { Icon, label, className } = config

  return (
    <div className={`verdict-badge ${className}`}>
      <Icon size={18} strokeWidth={2} />
      <span>{label}</span>
    </div>
  )
}
