import { useState } from "react"
import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { describe, it, expect, vi } from "vitest"
import VerifyForm from "../VerifyForm"
import { SAMPLE_CLAIMS } from "../../constants"

function ControlledVerifyForm({ initialClaim = "", onVerify = vi.fn(), onClear = vi.fn(), loading = false }) {
  const [claim, setClaim] = useState(initialClaim)
  return (
    <VerifyForm
      claim={claim}
      loading={loading}
      onClaimChange={setClaim}
      onVerify={onVerify}
      onClear={onClear}
    />
  )
}

describe("VerifyForm", () => {
  it("submits when Enter is pressed", async () => {
    const user = userEvent.setup()
    const onVerify = vi.fn()
    render(<ControlledVerifyForm initialClaim="Exercise lowers heart risk" onVerify={onVerify} />)

    const textarea = screen.getByLabelText(/health claim/i)
    await user.click(textarea)
    await user.keyboard("{Enter}")

    expect(onVerify).toHaveBeenCalledTimes(1)
  })

  it("inserts a newline without submitting on Shift+Enter", async () => {
    const user = userEvent.setup()
    const onVerify = vi.fn()
    render(<ControlledVerifyForm initialClaim="Line one" onVerify={onVerify} />)

    const textarea = screen.getByLabelText(/health claim/i)
    await user.click(textarea)
    await user.keyboard("{Shift>}{Enter}{/Shift}Line two")

    expect(onVerify).not.toHaveBeenCalled()
    expect(textarea).toHaveValue("Line one\nLine two")
  })

  it("fills the textarea when a sample chip is clicked", async () => {
    const user = userEvent.setup()
    render(<ControlledVerifyForm />)

    const firstSample = SAMPLE_CLAIMS[0]
    await user.click(screen.getByRole("button", { name: firstSample }))

    expect(screen.getByLabelText(/health claim/i)).toHaveValue(firstSample)
  })
})
