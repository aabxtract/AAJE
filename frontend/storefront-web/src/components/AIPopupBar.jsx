/**
 * The pop-up message bar for AI-driven onboarding.
 *
 * Centered in the viewport like a modal — the AI message card and input row
 * sit together in the middle of the screen, focused, with a soft backdrop
 * behind. ONE question visible at a time, no scrolling history.
 *
 * Caller controls:
 *   - `message`: current AI text to show
 *   - `quickReplies`: optional string array, rendered as chips
 *   - `placeholder`: input hint
 *   - `loading`: true while the next turn is fetching (disables input + shows spinner)
 *   - `onSubmit(text)`: called when user sends (chip tap OR free-text submit)
 *   - `disabled`: hard-disable the input (e.g. after done=true)
 */
import { useEffect, useRef, useState } from 'react'
import { ArrowUp, Loader2, Sparkles } from 'lucide-react'

export default function AIPopupBar({
  message,
  quickReplies,
  placeholder = 'Type your answer…',
  loading = false,
  disabled = false,
  onSubmit,
}) {
  const [draft, setDraft] = useState('')
  const inputRef = useRef(null)

  useEffect(() => {
    if (!loading && !disabled && inputRef.current) {
      inputRef.current.focus()
    }
  }, [message, loading, disabled])

  function handleSend(text) {
    const value = (text ?? draft).trim()
    if (!value || loading || disabled) return
    setDraft('')
    onSubmit?.(value)
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="fixed inset-0 z-50 grid place-items-center px-4">
      {/* Soft backdrop so the popup reads as the focal point */}
      <div className="absolute inset-0 bg-[#0b0820]/30 backdrop-blur-sm" aria-hidden="true" />

      <div className="relative w-full max-w-xl">
        {/* AI message card */}
        <div className="rounded-3xl border border-white/40 bg-white/95 p-6 shadow-[0_30px_80px_rgba(15,23,42,0.28)] backdrop-blur">
          <div className="flex items-start gap-3">
            <div className="grid h-10 w-10 flex-shrink-0 place-items-center rounded-full bg-gradient-to-br from-[#5a4be7] to-[#7c3aed] text-white">
              {loading ? (
                <Loader2 className="h-5 w-5 animate-spin" />
              ) : (
                <Sparkles className="h-5 w-5" />
              )}
            </div>
            <p className="flex-1 whitespace-pre-wrap text-[15px] leading-6 text-[#12102b]">
              {loading && !message ? 'Thinking…' : message || 'Hi! Let’s set up your store.'}
            </p>
          </div>

          {quickReplies && quickReplies.length > 0 && !loading && !disabled && (
            <div className="mt-4 flex flex-wrap gap-2">
              {quickReplies.map((reply) => (
                <button
                  key={reply}
                  type="button"
                  onClick={() => handleSend(reply)}
                  className="inline-flex items-center rounded-full border border-[#dcd4ed] bg-[#f8f5ff] px-3.5 py-1.5 text-xs font-semibold text-[#5a4be7] transition hover:border-[#5a4be7] hover:bg-[#eee6ff]"
                >
                  {reply}
                </button>
              ))}
            </div>
          )}

          {/* Input row — kept inside the same card so it reads as one popup */}
          <div className="mt-5 flex items-center gap-2 rounded-full border border-[#dcd4ed] bg-white p-1.5 shadow-[0_10px_30px_rgba(15,23,42,0.08)]">
            <input
              ref={inputRef}
              type="text"
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={placeholder}
              disabled={loading || disabled}
              className="flex-1 bg-transparent px-4 py-2.5 text-[15px] text-[#12102b] placeholder:text-[#9a94aa] focus:outline-none disabled:opacity-50"
            />
            <button
              onClick={() => handleSend()}
              disabled={loading || disabled || !draft.trim()}
              className="grid h-10 w-10 flex-shrink-0 place-items-center rounded-full bg-[#5a4be7] text-white transition hover:bg-[#493bd0] disabled:opacity-40"
              aria-label="Send"
            >
              {loading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <ArrowUp className="h-4 w-4" />
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
