import { useState } from 'react'
import {
  Building2,
  CheckCircle2,
  CreditCard,
  Landmark,
  Loader2,
  Shield,
  Sparkles,
  X,
} from 'lucide-react'

export default function MonoConnectOverlay({ onComplete, onSkip }) {
  const [step, setStep] = useState('intro')
  const [selectedBank, setSelectedBank] = useState(null)

  const demoBanks = [
    { code: '058', name: 'Guaranty Trust Bank', short: 'GTBank' },
    { code: '033', name: 'United Bank for Africa', short: 'UBA' },
    { code: '011', name: 'First Bank of Nigeria', short: 'FirstBank' },
    { code: '057', name: 'Zenith Bank', short: 'Zenith' },
    { code: '044', name: 'Access Bank', short: 'Access' },
    { code: '221', name: 'Stanbic IBTC Bank', short: 'Stanbic' },
  ]

  function handleSelectBank(bank) {
    setSelectedBank(bank)
    setStep('connecting')

    setTimeout(() => setStep('verifying'), 1800)
    setTimeout(() => setStep('success'), 3600)
    setTimeout(() => {
      onComplete({
        mono_account_id: 'mono_demo_' + Date.now(),
        bank_name: bank.name,
        bank_code: bank.code,
        account_number: '0' + Math.floor(100000000 + Math.random() * 900000000),
        account_name: JSON.parse(localStorage.getItem('aaje_user') || '{}').full_name || 'AAJE Demo User',
      })
    }, 5000)
  }

  return (
    <div className="fixed inset-0 z-[200] flex items-center justify-center bg-[#030328]/45 p-4 backdrop-blur-sm">
      <div className="relative w-full max-w-lg overflow-hidden rounded-[12px] border border-[#dcd6ea] bg-white shadow-[0_28px_80px_rgba(35,18,82,0.18)]">
        <div className="relative overflow-hidden bg-[#030328] px-8 py-10 text-white">
          <div className="absolute right-0 top-0 h-40 w-40 translate-x-1/3 -translate-y-1/3 rounded-full bg-[#077ef6]/25 blur-3xl" />
          <div className="relative z-10">
            <div className="mb-6 flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="grid h-12 w-12 place-items-center rounded-[8px] bg-white/10 text-[#93c5fd]">
                  <Landmark className="h-6 w-6" />
                </div>
                <div>
                  <h2 className="text-xl font-bold tracking-normal">Connect your bank</h2>
                  <div className="mt-1 flex items-center gap-1.5 text-[0.68rem] font-semibold uppercase tracking-[0.14em] text-white/60">
                    <Sparkles className="h-3 w-3" /> Powered by Mono
                  </div>
                </div>
              </div>
              {onSkip && (
                <button onClick={onSkip} className="grid h-10 w-10 place-items-center rounded-[8px] bg-white/10 text-white/75 transition hover:bg-white/15 hover:text-white" aria-label="Close bank connection">
                  <X className="h-5 w-5" />
                </button>
              )}
            </div>
            <p className="max-w-sm text-sm font-medium leading-6 text-white/78">
              Securely link your bank account to unlock instant payment settlements and strengthen your economic identity.
            </p>
          </div>
        </div>

        <div className="bg-[#fbf8ff] p-8">
          {step === 'intro' && (
            <div className="space-y-8">
              <div className="grid grid-cols-3 gap-3">
                {[
                  { icon: CreditCard, label: 'Free Biz Account', color: 'bg-[#eef6ff] text-[#077ef6]' },
                  { icon: Shield, label: 'Encrypted', color: 'bg-[#ecfdf3] text-[#027a48]' },
                  { icon: Building2, label: 'Instant Payouts', color: 'bg-[#f0eaff] text-[#5a4be7]' },
                ].map((benefit) => (
                  <div key={benefit.label} className="rounded-[8px] border border-[#e3ddec] bg-white p-3 text-center shadow-[0_12px_30px_rgba(35,18,82,0.06)]">
                    <div className={`mx-auto mb-2 grid h-9 w-9 place-items-center rounded-[8px] ${benefit.color}`}>
                      <benefit.icon className="h-4.5 w-4.5" />
                    </div>
                    <p className="text-[0.68rem] font-bold leading-tight text-[#030328]">{benefit.label}</p>
                  </div>
                ))}
              </div>

              <div>
                <p className="mb-4 text-[0.68rem] font-bold uppercase tracking-[0.16em] text-[#77738c]">Select your bank</p>
                <div className="grid grid-cols-2 gap-3">
                  {demoBanks.map((bank) => (
                    <button
                      key={bank.code}
                      onClick={() => handleSelectBank(bank)}
                      className="flex items-center gap-3 rounded-[8px] border border-[#e3ddec] bg-white p-3.5 text-left transition hover:border-[#077ef6] hover:shadow-[0_14px_32px_rgba(42,25,91,0.08)]"
                    >
                      <div className="grid h-10 w-10 place-items-center rounded-[8px] bg-[#eef6ff] text-xs font-bold text-[#077ef6]">
                        {bank.short[0]}
                      </div>
                      <div>
                        <p className="text-xs font-bold text-[#030328]">{bank.short}</p>
                        <p className="text-[0.68rem] font-medium text-[#77738c]">{bank.name}</p>
                      </div>
                    </button>
                  ))}
                </div>
              </div>

              <p className="text-center text-[0.68rem] font-medium text-[#9a94aa]">
                By continuing you agree to Mono's <span className="text-[#077ef6] underline">Terms</span> and <span className="text-[#077ef6] underline">Privacy Policy</span>.
              </p>
            </div>
          )}

          {step === 'connecting' && (
            <ProgressState
              icon={Loader2}
              title={`Connecting to ${selectedBank?.short}...`}
              body="Establishing secure SSL connection."
              progress={40}
              spinning
            />
          )}

          {step === 'verifying' && (
            <ProgressState
              icon={Shield}
              title="Verifying identity"
              body="Provisioning your Squad settlement account."
              progress={75}
            />
          )}

          {step === 'success' && (
            <div className="space-y-6 py-12 text-center">
              <div className="mx-auto grid h-20 w-20 place-items-center rounded-[12px] bg-[#ecfdf3] text-[#027a48]">
                <CheckCircle2 className="h-10 w-10" />
              </div>
              <div>
                <h3 className="text-xl font-bold tracking-normal text-[#05051f]">Bank linked</h3>
                <p className="mt-1 text-sm font-medium text-[#625d75]">Your business is now fully operational.</p>
              </div>
              <div className="mx-auto inline-flex items-center gap-2 rounded-full bg-white px-4 py-2 text-xs font-bold text-[#077ef6] shadow-[0_12px_30px_rgba(35,18,82,0.07)]">
                <Sparkles className="h-3.5 w-3.5" />
                Dashboard access granted
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function ProgressState({ icon: Icon, title, body, progress, spinning = false }) {
  return (
    <div className="space-y-6 py-12 text-center">
      <div className="mx-auto grid h-20 w-20 place-items-center rounded-[12px] bg-[#eef6ff] text-[#077ef6]">
        <Icon className={`h-10 w-10 ${spinning ? 'animate-spin' : ''}`} />
      </div>
      <div>
        <h3 className="text-xl font-bold tracking-normal text-[#05051f]">{title}</h3>
        <p className="mt-1 text-sm font-medium text-[#625d75]">{body}</p>
      </div>
      <div className="mx-auto h-2 w-64 overflow-hidden rounded-full bg-[#eee8f7]">
        <div className="h-full rounded-full bg-[#077ef6] transition-all duration-500" style={{ width: `${progress}%` }} />
      </div>
    </div>
  )
}
