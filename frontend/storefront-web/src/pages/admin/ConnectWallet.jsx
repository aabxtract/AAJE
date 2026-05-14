import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Wallet, Building2, CheckCircle2, ChevronRight, Loader2, ShieldCheck } from 'lucide-react'

export default function ConnectWallet() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [step, setStep] = useState('connect') // connect, account-details, success

  function handleConnect(e) {
    e.preventDefault()
    setLoading(true)
    setTimeout(() => {
      setLoading(false)
      setStep('account-details')
    }, 1500)
  }

  function handleSetup(e) {
    e.preventDefault()
    setLoading(true)
    setTimeout(() => {
      setLoading(false)
      setStep('success')
    }, 1500)
  }

  function handleContinue() {
    navigate('/pricing')
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-gray-50 p-4">
      <div className="w-full max-w-md">
        
        {step === 'connect' && (
          <div className="card p-8 text-center shadow-xl border-0 ring-1 ring-gray-200">
            <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-emerald-100 text-emerald-600 mb-6">
              <Wallet className="h-8 w-8" />
            </div>
            <h1 className="text-2xl font-bold text-gray-900 mb-2">Connect Your Account</h1>
            <p className="text-gray-600 mb-8">
              Enable Squad payments to start receiving money directly from your customers. We deduct a ₦50 monthly maintenance fee.
            </p>
            <button onClick={handleConnect} disabled={loading} className="btn-primary w-full py-3">
              {loading ? <Loader2 className="mr-2 h-5 w-5 animate-spin" /> : 'Connect Bank Account'}
            </button>
            <p className="mt-6 text-xs text-gray-500 flex items-center justify-center">
              <ShieldCheck className="w-4 h-4 mr-1 text-gray-400" /> Secured by Squad
            </p>
          </div>
        )}

        {step === 'account-details' && (
          <div className="card p-8 shadow-xl border-0 ring-1 ring-gray-200">
            <div className="flex items-center gap-3 mb-6">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary-100 text-primary-600">
                <Building2 className="h-5 w-5" />
              </div>
              <h1 className="text-xl font-bold text-gray-900">Add Account Details</h1>
            </div>
            <form onSubmit={handleSetup} className="space-y-4">
              <div>
                <label className="text-sm font-medium text-gray-700">Bank Name</label>
                <select required className="input-field mt-1">
                  <option value="">Select Bank</option>
                  <option value="access">Access Bank</option>
                  <option value="gtb">Guaranty Trust Bank</option>
                  <option value="zenith">Zenith Bank</option>
                  <option value="opay">OPay</option>
                  <option value="moniepoint">Moniepoint</option>
                </select>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700">Account Number</label>
                <input required type="text" pattern="[0-9]{10}" maxLength={10} className="input-field mt-1" placeholder="0123456789" />
              </div>
              <div className="pt-2">
                <button type="submit" disabled={loading} className="btn-primary w-full py-3">
                  {loading ? <Loader2 className="mr-2 h-5 w-5 animate-spin" /> : 'Complete Setup'}
                </button>
              </div>
            </form>
          </div>
        )}

        {step === 'success' && (
          <div className="card p-8 text-center shadow-xl border-0 ring-1 ring-emerald-200 bg-emerald-50/50">
            <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-emerald-100 text-emerald-600 mb-6">
              <CheckCircle2 className="h-8 w-8" />
            </div>
            <h1 className="text-2xl font-bold text-gray-900 mb-2">Wallet Ready!</h1>
            <p className="text-gray-600 mb-8">
              Your store can now receive payments instantly via Squad. You are all set up.
            </p>
            <button onClick={handleContinue} className="btn-primary w-full py-3 flex items-center justify-center">
              Continue to Plans <ChevronRight className="ml-2 h-5 w-5" />
            </button>
          </div>
        )}

      </div>
    </main>
  )
}
