import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Bot, Loader2, Send, Sparkles, User as UserIcon } from 'lucide-react'
import { generateStore } from '../lib/api'

const QUESTIONS = [
  {
    id: 'business',
    text: "Hi, I'm your AAJE store assistant. What kind of business are you building? Tell me what you sell or offer.",
    placeholder: 'e.g., I sell handmade jewelry to young professionals in Lagos...',
  },
  {
    id: 'customers',
    text: 'Nice. Who are your ideal customers? This helps me choose the right storefront direction.',
    placeholder: 'e.g., College students, fashion lovers, moms...',
  },
  {
    id: 'style',
    text: 'What style fits your brand best?',
    options: ['Clean and minimal', 'Bold and vibrant', 'Local and traditional', 'Premium and elegant', 'Playful and fun'],
  },
  {
    id: 'name',
    text: 'Last one. What should your store be called?',
    placeholder: "e.g., Ada's Collections, Jude Sneakers...",
  },
]

export default function Onboarding() {
  const navigate = useNavigate()
  const [messages, setMessages] = useState([])
  const [questionIndex, setQuestionIndex] = useState(0)
  const [input, setInput] = useState('')
  const [answers, setAnswers] = useState({})
  const [building, setBuilding] = useState(false)

  useEffect(() => {
    setMessages([{ role: 'ai', text: QUESTIONS[0].text }])
  }, [])

  function addMessage(role, text) {
    setMessages((prev) => [...prev, { role, text }])
  }

  function advanceToNext(newAnswers, nextIndex) {
    if (nextIndex < QUESTIONS.length) {
      setQuestionIndex(nextIndex)
      setTimeout(() => {
        addMessage('ai', QUESTIONS[nextIndex].text)
      }, 400)
      setInput('')
    } else {
      buildStore(newAnswers)
    }
  }

  function handleSendText() {
    const value = input.trim()
    if (!value) return

    addMessage('user', value)
    const currentQ = QUESTIONS[questionIndex]
    const newAnswers = { ...answers, [currentQ.id]: value }
    setAnswers(newAnswers)
    advanceToNext(newAnswers, questionIndex + 1)
  }

  function handleOptionSelect(option) {
    addMessage('user', option)
    const currentQ = QUESTIONS[questionIndex]
    const newAnswers = { ...answers, [currentQ.id]: option }
    setAnswers(newAnswers)
    advanceToNext(newAnswers, questionIndex + 1)
  }

  async function buildStore(finalAnswers) {
    setBuilding(true)
    addMessage('ai', 'Great choices. Let me build your storefront now...')

    try {
      const prompt = [
        finalAnswers.business,
        finalAnswers.customers ? `Target customers: ${finalAnswers.customers}` : '',
        finalAnswers.style ? `Style preference: ${finalAnswers.style}` : '',
        finalAnswers.name ? `Store name: ${finalAnswers.name}` : '',
      ].filter(Boolean).join('\n')

      const response = await generateStore(prompt)
      const blueprint = response.data || {}

      const storeName = finalAnswers.name?.trim() || blueprint.store_name || 'My Store'
      const storeData = {
        template: blueprint.template || 'fashion',
        store_name: storeName,
        description: blueprint.description || `${finalAnswers.business || 'Quality products'} for ${finalAnswers.customers || 'everyone'}`,
        tagline: blueprint.tagline || '',
        theme: blueprint.theme || 'default',
        categories: blueprint.categories || ['Popular', 'New Arrivals'],
        starter_products: blueprint.products || blueprint.starter_products || [],
        slug: (storeName).toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, ''),
      }

      sessionStorage.setItem('aaje_store_build', JSON.stringify(storeData))
      sessionStorage.setItem('aaje_onboarding_answers', JSON.stringify(finalAnswers))

      addMessage('ai', `Your store "${storeName}" is ready. Let me show you the details.`)

      setTimeout(() => {
        navigate('/confirm')
      }, 1200)
    } catch (err) {
      console.error('Build error:', err)
      addMessage('ai', 'Something went wrong generating your store. Please try again.')
      setBuilding(false)
    }
  }

  const currentQ = QUESTIONS[questionIndex]
  const isOptions = currentQ?.options && questionIndex < QUESTIONS.length

  return (
    <main className="flex min-h-screen flex-col bg-[#fbf8ff] text-[#12102b]">
      <header className="border-b border-[#ece7f5] bg-white px-4 py-4">
        <div className="mx-auto flex max-w-3xl items-center gap-3">
          <div className="grid h-9 w-9 place-items-center rounded-[8px] bg-[#5a4be7] text-sm font-black text-white">A</div>
          <div>
            <p className="text-sm font-semibold">AAJE Store Builder</p>
            <p className="text-xs text-[#74708a]">AI is setting up your storefront</p>
          </div>
          <div className="ml-auto flex items-center gap-2 rounded-full bg-[#f2edff] px-3 py-1">
            <Sparkles className="h-4 w-4 text-[#5a4be7]" />
            <span className="text-xs font-semibold text-[#5a4be7]">
              Step {Math.min(questionIndex + 1, QUESTIONS.length)} of {QUESTIONS.length}
            </span>
          </div>
        </div>
      </header>

      <div className="flex-1 overflow-y-auto px-4 py-8">
        <div className="mx-auto max-w-3xl space-y-5">
          {messages.map((msg, index) => (
            <div key={index} className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : ''}`}>
              {msg.role === 'ai' && (
                <div className="grid h-9 w-9 flex-shrink-0 place-items-center rounded-full bg-[#5a4be7] text-white">
                  <Bot className="h-4 w-4" />
                </div>
              )}
              <div
                className={`max-w-[82%] rounded-[16px] px-4 py-3 text-sm leading-relaxed ${
                  msg.role === 'user'
                    ? 'bg-[#5a4be7] text-white'
                    : 'border border-[#ece7f5] bg-white text-[#12102b]'
                }`}
              >
                {msg.text}
              </div>
              {msg.role === 'user' && (
                <div className="grid h-9 w-9 flex-shrink-0 place-items-center rounded-full bg-[#ece6ff] text-[#5a4be7]">
                  <UserIcon className="h-4 w-4" />
                </div>
              )}
            </div>
          ))}

          {building && (
            <div className="flex gap-3">
              <div className="grid h-9 w-9 flex-shrink-0 place-items-center rounded-full bg-[#5a4be7] text-white">
                <Bot className="h-4 w-4" />
              </div>
              <div className="flex items-center gap-2 rounded-[16px] border border-[#ece7f5] bg-white px-4 py-3 text-sm text-[#74708a]">
                <Loader2 className="h-4 w-4 animate-spin" />
                Building your store...
              </div>
            </div>
          )}
        </div>
      </div>

      {!building && questionIndex < QUESTIONS.length && (
        <div className="border-t border-[#ece7f5] bg-white px-4 py-4">
          <div className="mx-auto max-w-3xl">
            {isOptions ? (
              <div className="grid gap-2 sm:grid-cols-2">
                {currentQ.options.map((option) => (
                  <button
                    key={option}
                    onClick={() => handleOptionSelect(option)}
                    className="rounded-[8px] border border-[#e4e1ee] bg-white px-4 py-3 text-left text-sm font-medium text-[#12102b] transition hover:border-[#5a4be7] hover:bg-[#f4efff]"
                  >
                    {option}
                  </button>
                ))}
              </div>
            ) : (
              <div className="flex gap-2">
                <input
                  type="text"
                  value={input}
                  onChange={(event) => setInput(event.target.value)}
                  onKeyDown={(event) => event.key === 'Enter' && handleSendText()}
                  placeholder={currentQ?.placeholder || 'Type your answer...'}
                  autoFocus
                  className="flex-1 rounded-[8px] border border-[#e4e1ee] bg-[#fafafa] px-4 py-3 text-sm outline-none transition placeholder:text-[#9b97aa] focus:border-[#5a4be7] focus:ring-2 focus:ring-[#ece6ff]"
                />
                <button
                  onClick={handleSendText}
                  disabled={!input.trim()}
                  className="grid h-12 w-12 place-items-center rounded-[8px] bg-[#5a4be7] text-white transition hover:bg-[#493bd0] disabled:opacity-40"
                >
                  <Send className="h-4 w-4" />
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </main>
  )
}
