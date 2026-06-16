/**
 * LLM-driven onboarding shell.
 *
 * The Python script no longer decides what to ask. The trader talks to the
 * AI through <AIPopupBar />; each answer POSTs the full history to
 * /onboarding/turn; the LLM decides what comes next (questions, template
 * suggestions, finalization). When the server returns `done: true` with a
 * store payload, we route the trader to /admin/store-setup.
 *
 * Visual: a soft gradient page with the centered popup as the only focus.
 */
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Sparkles } from 'lucide-react'
import AIPopupBar from '../components/AIPopupBar'
import { onboardingTurn } from '../lib/api'

export default function Onboarding() {
  const navigate = useNavigate()
  const [history, setHistory] = useState([])
  const [current, setCurrent] = useState({
    message: '',
    quick_replies: null,
    placeholder: 'Tell me what your business is about…',
  })
  const [loading, setLoading] = useState(false)
  const [done, setDone] = useState(false)

  useEffect(() => {
    let cancelled = false
    async function start() {
      setLoading(true)
      try {
        const res = await onboardingTurn([])
        if (cancelled) return
        applyTurn(res.data)
      } catch (err) {
        if (cancelled) return
        // Surface the actual cause so we don't get the misleading
        // "AI host" message when the real issue is auth (e.g. missing token).
        const status = err?.response?.status
        const detail = err?.response?.data?.detail
        let message
        if (status === 401) {
          message = "Your session expired. Log in again to keep building."
        } else if (status >= 500) {
          message = "Our AI host hiccuped. Refresh to try again."
        } else if (detail) {
          message = String(detail)
        } else {
          message = "Couldn't reach the AI host. Refresh to try again."
        }
        setCurrent({ message, quick_replies: null, placeholder: '' })
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    start()
    return () => { cancelled = true }
  }, [])

  function applyTurn(data) {
    setCurrent({
      message: data.message,
      quick_replies: data.quick_replies,
      placeholder: data.placeholder || 'Type your answer…',
    })
    if (data.done && data.store) {
      setDone(true)
      localStorage.setItem('aaje_store', JSON.stringify(data.store))
      const user = JSON.parse(localStorage.getItem('aaje_user') || '{}')
      user.onboarding_complete = true
      localStorage.setItem('aaje_user', JSON.stringify(user))
      setTimeout(() => navigate('/admin/store-setup'), 2400)
    }
  }

  async function handleAnswer(text) {
    const nextHistory = [
      ...history,
      ...(current.message
        ? [{ role: 'assistant', content: current.message }]
        : []),
      { role: 'user', content: text },
    ]
    setHistory(nextHistory)
    setLoading(true)
    try {
      const res = await onboardingTurn(nextHistory)
      applyTurn(res.data)
    } catch (err) {
      setCurrent({
        message: "Couldn't process that. Try again?",
        quick_replies: null,
        placeholder: 'Type your answer…',
      })
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="relative min-h-screen overflow-hidden bg-gradient-to-br from-[#f7f4ff] via-[#fbf8ff] to-[#f0e7ff] text-[#12102b]">
      {/* Ambient blur — keeps the gradient lively behind the centered popup */}
      <div className="pointer-events-none absolute -left-32 top-20 h-72 w-72 rounded-full bg-[#a78bfa]/30 blur-3xl" />
      <div className="pointer-events-none absolute -right-32 top-1/3 h-96 w-96 rounded-full bg-[#fb7185]/20 blur-3xl" />
      <div className="pointer-events-none absolute bottom-40 left-1/3 h-80 w-80 rounded-full bg-[#38bdf8]/20 blur-3xl" />

      {/* Quiet header — pushed to the top so the popup owns the center */}
      <div className="relative z-10 mx-auto max-w-3xl px-6 pt-10 text-center">
        <div className="inline-flex items-center gap-2 rounded-full border border-white/60 bg-white/70 px-4 py-1.5 text-xs font-bold uppercase text-[#5a4be7] backdrop-blur">
          <Sparkles className="h-3.5 w-3.5" />
          AAJE Onboarding
        </div>
      </div>

      <AIPopupBar
        message={current.message}
        quickReplies={current.quick_replies}
        placeholder={current.placeholder}
        loading={loading}
        disabled={done}
        onSubmit={handleAnswer}
      />
    </main>
  )
}
