import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Mail, Loader2, ArrowRight } from 'lucide-react'

export default function Signup() {
  const navigate = useNavigate()
  const [step, setStep] = useState('choice')
  const [form, setForm] = useState({ email: '', password: '', phone: '' })
  const [loading, setLoading] = useState(false)

  function handleChange(e) {
    const { name, value } = e.target
    setForm(prev => ({ ...prev, [name]: value }))
  }

  async function handleEmailSignup(e) {
    e.preventDefault()
    setLoading(true)
    try {
      const user = {
        id: Math.random().toString(36).substr(2, 9),
        email: form.email,
        phone: form.phone,
        type: 'email',
        createdAt: new Date().toISOString(),
      }
      localStorage.setItem('aaje_user', JSON.stringify(user))
      navigate('/onboarding')
    } finally {
      setLoading(false)
    }
  }

  function handleGoogleSignup() {
    const user = {
      id: Math.random().toString(36).substr(2, 9),
      email: 'user@gmail.com',
      type: 'google',
      createdAt: new Date().toISOString(),
    }
    localStorage.setItem('aaje_user', JSON.stringify(user))
    navigate('/onboarding')
  }

  if (step === 'email') {
    return (
      <main className="flex min-h-screen items-center justify-center bg-gradient-to-br from-primary-50 to-white p-4">
        <div className="w-full max-w-md">
          <div className="mb-8 text-center">
            <div className="inline-flex items-center justify-center rounded-xl bg-gradient-to-br from-primary-600 to-primary-700 p-3">
              <span className="text-2xl font-bold text-white">AAJE</span>
            </div>
            <p className="mt-3 text-sm text-gray-600">AI-powered African storefronts</p>
          </div>

          <div className="rounded-2xl bg-white p-8 shadow-lg">
            <h1 className="text-2xl font-bold text-gray-900">Sign up with email</h1>
            <p className="mt-1 text-sm text-gray-500">Create your storefront account</p>

            <form onSubmit={handleEmailSignup} className="mt-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                <input
                  type="email"
                  name="email"
                  required
                  value={form.email}
                  onChange={handleChange}
                  placeholder="you@example.com"
                  className="input-field"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Phone number</label>
                <input
                  type="tel"
                  name="phone"
                  required
                  value={form.phone}
                  onChange={handleChange}
                  placeholder="+234 801 234 5678"
                  className="input-field"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
                <input
                  type="password"
                  name="password"
                  required
                  value={form.password}
                  onChange={handleChange}
                  placeholder="At least 8 characters"
                  className="input-field"
                />
              </div>

              <button type="submit" disabled={loading} className="btn-primary w-full justify-center mt-6">
                {loading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Creating account...
                  </>
                ) : (
                  <>
                    Get started
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </>
                )}
              </button>
            </form>

            <button
              type="button"
              onClick={() => setStep('choice')}
              className="mt-4 w-full text-sm text-gray-600 hover:text-gray-900"
            >
              Back to options
            </button>
          </div>
        </div>
      </main>
    )
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-gradient-to-br from-primary-50 to-white p-4">
      <div className="w-full max-w-md">
        <div className="mb-12 text-center">
          <div className="inline-flex items-center justify-center rounded-xl bg-gradient-to-br from-primary-600 to-primary-700 p-3">
            <span className="text-2xl font-bold text-white">AAJE</span>
          </div>
          <h1 className="mt-6 text-3xl font-bold text-gray-900">Welcome to AAJE</h1>
          <p className="mt-2 text-gray-600">
            Create your AI-powered storefront in minutes
          </p>
        </div>

        <div className="space-y-3">
          <button
            onClick={handleGoogleSignup}
            className="flex w-full items-center justify-center gap-2 rounded-lg border-2 border-gray-200 bg-white px-4 py-3 font-semibold text-gray-900 transition hover:border-primary-300 hover:bg-primary-50"
          >
            <svg className="h-5 w-5" viewBox="0 0 24 24">
              <path fill="currentColor" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
              <path fill="currentColor" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
              <path fill="currentColor" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
              <path fill="currentColor" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
            </svg>
            Continue with Google
          </button>

          <button
            onClick={() => setStep('email')}
            className="flex w-full items-center justify-center gap-2 rounded-lg bg-primary-600 px-4 py-3 font-semibold text-white transition hover:bg-primary-700"
          >
            <Mail className="h-5 w-5" />
            Sign up with Email
          </button>
        </div>

        <p className="mt-6 text-center text-xs text-gray-500">
          By continuing, you agree to AAJE's{' '}
          <button className="text-primary-600 hover:underline">Terms of Service</button> and{' '}
          <button className="text-primary-600 hover:underline">Privacy Policy</button>
        </p>
      </div>
    </main>
  )
}
