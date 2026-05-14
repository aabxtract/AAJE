import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Lock, CheckCircle, ArrowRight, Loader2, CreditCard } from 'lucide-react'

export default function AccountConnect() {
  const navigate = useNavigate()
  const [step, setStep] = useState('info')
  const [loading, setLoading] = useState(false)
  const [form, setForm] = useState({
    bankName: '',
    accountNumber: '',
    accountName: '',
  })

  function handleChange(e) {
    const { name, value } = e.target
    setForm(prev => ({ ...prev, [name]: value }))
  }

  async function handleConnect(e) {
    e.preventDefault()
    setLoading(true)
    try {
      // Simulate bank connection
      await new Promise(resolve => setTimeout(resolve, 2000))
      setStep('success')
    } finally {
      setLoading(false)
    }
  }

  if (step === 'success') {
    return (
      <main className="flex min-h-screen items-center justify-center bg-gradient-to-br from-primary-50 to-white p-4">
        <div className="w-full max-w-md">
          <div className="rounded-2xl bg-white p-8 shadow-lg text-center">
            <div className="inline-flex items-center justify-center rounded-full bg-emerald-100 p-4 mb-4">
              <CheckCircle className="h-8 w-8 text-emerald-600" />
            </div>

            <h1 className="text-2xl font-bold text-gray-900">Account Connected!</h1>
            <p className="mt-2 text-gray-600">Your bank account is ready to receive payments.</p>

            <div className="mt-6 space-y-3 rounded-lg bg-gray-50 p-4 text-left">
              <div>
                <p className="text-xs font-semibold text-gray-500 uppercase">Monthly maintenance fee</p>
                <p className="mt-1 text-gray-900">₦50 deducted monthly</p>
              </div>
              <div>
                <p className="text-xs font-semibold text-gray-500 uppercase">Payment method</p>
                <p className="mt-1 text-gray-900">Squad Payment Gateway</p>
              </div>
              <div>
                <p className="text-xs font-semibold text-gray-500 uppercase">Settlement</p>
                <p className="mt-1 text-gray-900">Instant to your bank</p>
              </div>
            </div>

            <button
              onClick={() => navigate('/pricing')}
              className="mt-6 w-full btn-primary flex items-center justify-center gap-2"
            >
              <ArrowRight className="h-4 w-4" />
              Choose Your Plan
            </button>
          </div>
        </div>
      </main>
    )
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-gradient-to-br from-primary-50 to-white p-4">
      <div className="w-full max-w-md">
        <div className="rounded-2xl bg-white p-8 shadow-lg">
          <div className="mb-6">
            <div className="inline-flex items-center justify-center rounded-lg bg-primary-100 p-3 mb-4">
              <CreditCard className="h-6 w-6 text-primary-600" />
            </div>
            <h1 className="text-2xl font-bold text-gray-900">Connect Your Account</h1>
            <p className="mt-2 text-gray-600">Enable free wallet to receive payments via Squad</p>
          </div>

          <div className="rounded-lg bg-blue-50 border border-blue-200 p-4 mb-6">
            <p className="text-sm text-blue-900">
              <span className="font-semibold">Free Setup:</span> No setup fees. ₦50 monthly maintenance charge only.
            </p>
          </div>

          <form onSubmit={handleConnect} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Bank Name</label>
              <input
                type="text"
                name="bankName"
                required
                value={form.bankName}
                onChange={handleChange}
                placeholder="e.g., GTBank, Access Bank"
                className="input-field"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Account Number</label>
              <input
                type="text"
                name="accountNumber"
                required
                value={form.accountNumber}
                onChange={handleChange}
                placeholder="Your 10-digit account number"
                className="input-field"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Account Name</label>
              <input
                type="text"
                name="accountName"
                required
                value={form.accountName}
                onChange={handleChange}
                placeholder="As it appears on your bank statement"
                className="input-field"
              />
            </div>

            <div className="rounded-lg bg-gray-50 p-4 space-y-2">
              <div className="flex items-center gap-2">
                <Lock className="h-4 w-4 text-gray-500" />
                <p className="text-xs text-gray-600">
                  <span className="font-semibold">Secure:</span> Encrypted end-to-end
                </p>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full mt-6 flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Verifying...
                </>
              ) : (
                <>
                  <ArrowRight className="h-4 w-4" />
                  Connect Account
                </>
              )}
            </button>
          </form>

          <p className="mt-4 text-xs text-gray-500 text-center">
            We'll verify your account instantly. No documents needed for MVP.
          </p>
        </div>
      </div>
    </main>
  )
}
