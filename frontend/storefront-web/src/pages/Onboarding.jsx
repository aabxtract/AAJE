import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Send, Loader2, Sparkles, ArrowRight } from 'lucide-react'

const AI_QUESTIONS = [
  {
    id: 'business',
    question: 'What do you sell?',
    placeholder: 'e.g., Handmade jewelry, Fresh produce, Tech accessories...',
    type: 'product_or_service'
  },
  {
    id: 'customers',
    question: 'Who are your customers?',
    placeholder: 'e.g., College students, Moms, Fashion enthusiasts...',
    type: 'audience'
  },
  {
    id: 'style',
    question: 'What style appeals to you?',
    options: ['Clean & Minimal', 'Bold & Vibrant', 'Local & Traditional', 'Premium & Elegant', 'Playful & Fun'],
    type: 'choice'
  },
  {
    id: 'name',
    question: 'What should your store be called?',
    placeholder: 'e.g., Ada\'s Collections, Jude Sneakers...',
    type: 'text'
  }
]

export default function Onboarding() {
  const navigate = useNavigate()
  const [currentIndex, setCurrentIndex] = useState(0)
  const [answers, setAnswers] = useState({})
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [store, setStore] = useState(null)

  const currentQuestion = AI_QUESTIONS[currentIndex]
  const isComplete = currentIndex === AI_QUESTIONS.length

  function handleSubmitAnswer() {
    if (!input.trim() && currentQuestion.type !== 'choice') return

    const newAnswers = { ...answers, [currentQuestion.id]: input }
    setAnswers(newAnswers)

    if (currentIndex < AI_QUESTIONS.length - 1) {
      setCurrentIndex(currentIndex + 1)
      setInput('')
    } else {
      generateStore(newAnswers)
    }
  }

  function handleOptionSelect(option) {
    const newAnswers = { ...answers, [currentQuestion.id]: option }
    setAnswers(newAnswers)
    setCurrentIndex(currentIndex + 1)
  }

  async function generateStore(finalAnswers) {
    setLoading(true)
    try {
      // Simulate AI store generation
      await new Promise(resolve => setTimeout(resolve, 2000))

      const generatedStore = {
        name: finalAnswers.name || 'My Store',
        slug: finalAnswers.name.toLowerCase().replace(/\s+/g, '-'),
        description: `${finalAnswers.business || 'Quality products'} for ${finalAnswers.customers || 'everyone'}`,
        category: finalAnswers.business,
        theme: finalAnswers.style,
        products: [
          { id: 1, name: 'Product 1', price: 15000, image: 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=300&h=300&fit=crop' },
          { id: 2, name: 'Product 2', price: 25000, image: 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=300&h=300&fit=crop' },
          { id: 3, name: 'Product 3', price: 35000, image: 'https://images.unsplash.com/photo-1572635196237-14b3f281503f?w=300&h=300&fit=crop' },
        ]
      }

      setStore(generatedStore)
      setCurrentIndex(currentIndex + 1)
    } finally {
      setLoading(false)
    }
  }

  if (isComplete && store) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-gradient-to-br from-primary-50 to-white p-4">
        <div className="w-full max-w-2xl">
          <div className="rounded-2xl bg-white p-8 shadow-lg text-center">
            <div className="inline-flex items-center justify-center rounded-full bg-gradient-to-br from-primary-100 to-primary-50 p-4 mb-4">
              <Sparkles className="h-8 w-8 text-primary-600" />
            </div>
            
            <h1 className="text-3xl font-bold text-gray-900">Your storefront is ready!</h1>
            <p className="mt-2 text-gray-600">We've created a beautiful store for you.</p>

            <div className="mt-8 rounded-xl bg-gray-50 p-6 text-left">
              <div className="space-y-3">
                <div>
                  <p className="text-xs font-semibold text-gray-500 uppercase">Store name</p>
                  <p className="text-lg font-bold text-gray-900">{store.name}</p>
                </div>
                <div>
                  <p className="text-xs font-semibold text-gray-500 uppercase">Description</p>
                  <p className="text-gray-700">{store.description}</p>
                </div>
                <div>
                  <p className="text-xs font-semibold text-gray-500 uppercase">Theme</p>
                  <p className="text-gray-700">{store.theme}</p>
                </div>
                <div>
                  <p className="text-xs font-semibold text-gray-500 uppercase">Sample products generated</p>
                  <p className="text-gray-700">{store.products.length} starter products</p>
                </div>
              </div>
            </div>

            <div className="mt-6 flex flex-col gap-3 sm:flex-row">
              <button
                onClick={() => navigate('/store-preview')}
                className="flex-1 rounded-lg bg-primary-600 px-4 py-3 font-semibold text-white transition hover:bg-primary-700 flex items-center justify-center gap-2"
              >
                <ArrowRight className="h-4 w-4" />
                Review Store
              </button>
            </div>
          </div>
        </div>
      </main>
    )
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-gradient-to-br from-primary-50 to-white p-4">
      <div className="w-full max-w-lg">
        <div className="rounded-2xl bg-white p-8 shadow-lg">
          {/* Progress indicator */}
          <div className="mb-6">
            <div className="flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-primary-600" />
              <p className="text-sm text-gray-600">
                Step <span className="font-bold">{currentIndex + 1}</span> of <span className="font-bold">{AI_QUESTIONS.length}</span>
              </p>
            </div>
            <div className="mt-3 h-1.5 w-full rounded-full bg-gray-100 overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-primary-600 to-primary-500 transition-all duration-300"
                style={{ width: `${((currentIndex + 1) / AI_QUESTIONS.length) * 100}%` }}
              />
            </div>
          </div>

          {/* Question */}
          <h2 className="text-2xl font-bold text-gray-900">{currentQuestion.question}</h2>

          {/* Answer input/options */}
          <div className="mt-6 space-y-3">
            {currentQuestion.type === 'choice' && currentQuestion.options ? (
              <>
                {currentQuestion.options.map((option) => (
                  <button
                    key={option}
                    onClick={() => handleOptionSelect(option)}
                    className="w-full rounded-lg border-2 border-gray-200 bg-white px-4 py-3 text-left font-medium text-gray-900 transition hover:border-primary-500 hover:bg-primary-50"
                  >
                    {option}
                  </button>
                ))}
              </>
            ) : (
              <div className="flex gap-2">
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleSubmitAnswer()}
                  placeholder={currentQuestion.placeholder}
                  autoFocus
                  className="input-field flex-1"
                />
                <button
                  onClick={handleSubmitAnswer}
                  disabled={!input.trim() || loading}
                  className="btn-primary px-4"
                >
                  {loading ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Send className="h-4 w-4" />
                  )}
                </button>
              </div>
            )}
          </div>

          {/* Footer */}
          <p className="mt-6 text-xs text-gray-500 text-center">
            AI-powered storefront setup. Takes 2 minutes.
          </p>
        </div>
      </div>
    </main>
  )
}
