import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  ArrowLeft,
  ArrowRight,
  CheckCircle2,
  Loader2,
  Mail,
  MessageCircle,
  ShieldCheck,
  Sparkles,
} from 'lucide-react'
import { googleSignIn, signup } from '../lib/api'

const merchantImage =
  'https://images.unsplash.com/photo-1556742049-0cfed4f6a45d?auto=format&fit=crop&w=1200&q=85'

const flowNotes = [
  'AI drafts your store setup',
  'Products and services live in one catalog',
  'Squad sandbox checkout creates paid orders',
  'WhatsApp sends the operating updates',
]

export default function Signup() {
  const navigate = useNavigate()
  const [form, setForm] = useState({
    fullName: '',
    email: '',
    phone: '',
    password: '',
    businessDescription: '',
  })
  const [loading, setLoading] = useState(false)

  function handleChange(event) {
    const { name, value } = event.target
    setForm((previous) => ({ ...previous, [name]: value }))
  }

  async function handleEmailSignup(event) {
    event.preventDefault()
    setLoading(true)

    try {
      const response = await signup({
        email: form.email,
        password: form.password,
        full_name: form.fullName,
        phone: form.phone,
        business_description: form.businessDescription,
      })
      
      const { user, token, store } = response.data

      localStorage.setItem('auth_token', token)
      localStorage.setItem('aaje_user', JSON.stringify(user))
      localStorage.setItem('aaje_user_id', user.id)
      if (store) {
        localStorage.setItem('aaje_store', JSON.stringify(store))
      }
      
      sessionStorage.setItem('aaje_onboarding_seed', JSON.stringify({
        business: form.businessDescription,
        name: form.fullName,
        phone: form.phone,
      }))
      navigate('/onboarding')
    } catch (err) {
      console.error("Signup error:", err)
      alert(err.response?.data?.detail || "Signup failed. Please try again.")
    } finally {
      setLoading(false)
    }
  }

  async function handleGoogleSignup() {
    setLoading(true)
    try {
      const response = await googleSignIn({
        email: 'founder@gmail.com',
        full_name: 'AAJE Founder',
      })
      const { user, token } = response.data
      localStorage.setItem('auth_token', token)
      localStorage.setItem('aaje_user', JSON.stringify(user))
      localStorage.setItem('aaje_user_id', user.id)
      sessionStorage.setItem('aaje_onboarding_seed', JSON.stringify({ business: '' }))
      navigate('/onboarding')
    } catch (err) {
      console.error('Google signup error:', err)
      alert(err.response?.data?.detail || 'Google signup failed. Please try email signup.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="min-h-screen bg-[#f7f8f4] text-[#111827]">
      <div className="grid min-h-screen lg:grid-cols-[0.95fr_1.05fr]">
        <section className="relative hidden overflow-hidden bg-[#0f172a] lg:block">
          <img
            src={merchantImage}
            alt="Online store checkout on a merchant laptop"
            className="absolute inset-0 h-full w-full object-cover opacity-72"
          />
          <div className="absolute inset-0 bg-[#07111f]/68" />

          <div className="relative z-10 flex h-full flex-col justify-between p-10 text-white">
            <Link to="/" className="inline-flex items-center gap-2 text-sm font-semibold text-white/80 transition hover:text-white">
              <ArrowLeft className="h-4 w-4" />
              Back to AAJE
            </Link>

            <div className="max-w-xl">
              <p className="inline-flex items-center gap-2 rounded-md border border-white/20 bg-white/10 px-3 py-1 text-xs font-bold uppercase text-[#dff7e8]">
                <Sparkles className="h-3.5 w-3.5" />
                Free storefront setup
              </p>
              <h1 className="mt-5 text-5xl font-semibold leading-tight">
                Create the account that powers your store, checkout, and WhatsApp alerts.
              </h1>
              <div className="mt-8 grid gap-3">
                {flowNotes.map((note) => (
                  <div key={note} className="flex items-center gap-3 rounded-md border border-white/16 bg-white/10 p-3 backdrop-blur">
                    <CheckCircle2 className="h-4 w-4 text-[#dff7e8]" />
                    <span className="text-sm font-medium text-white/86">{note}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="grid grid-cols-3 gap-3 text-sm">
              <div className="rounded-md border border-white/16 bg-white/10 p-4">
                <p className="font-bold">1 store</p>
                <p className="mt-1 text-white/62">free plan</p>
              </div>
              <div className="rounded-md border border-white/16 bg-white/10 p-4">
                <p className="font-bold">8PM</p>
                <p className="mt-1 text-white/62">daily summary</p>
              </div>
              <div className="rounded-md border border-white/16 bg-white/10 p-4">
                <p className="font-bold">BizPrint</p>
                <p className="mt-1 text-white/62">basic score</p>
              </div>
            </div>
          </div>
        </section>

        <section className="flex items-center justify-center px-4 py-10 sm:px-6 lg:px-10">
          <div className="w-full max-w-xl">
            <div className="mb-8 flex items-center justify-between">
              <Link to="/" className="flex items-center gap-2 text-[#0f172a]" aria-label="AAJE home">
                <span className="grid h-9 w-9 place-items-center rounded-md bg-[#0f172a] text-sm font-black text-white">
                  A
                </span>
                <span className="text-sm font-semibold tracking-wide">AAJE</span>
              </Link>
              <Link to="/" className="inline-flex items-center gap-2 text-sm font-semibold text-slate-600 transition hover:text-[#0f172a] lg:hidden">
                <ArrowLeft className="h-4 w-4" />
                Back
              </Link>
            </div>

            <div className="rounded-md border border-[#d9dfd4] bg-white p-5 shadow-sm sm:p-7">
              <div>
                <p className="text-xs font-bold uppercase text-emerald-700">Start with your business</p>
                <h2 className="mt-3 text-3xl font-semibold leading-tight text-[#0f172a]">
                  Sign up and generate your first storefront.
                </h2>
                <p className="mt-3 text-sm leading-6 text-slate-600">
                  No verification required for the demo. Add your phone so WhatsApp notifications can be configured after setup.
                </p>
              </div>

              <button
                type="button"
                onClick={handleGoogleSignup}
                className="mt-6 flex h-12 w-full items-center justify-center gap-2 rounded-md border border-slate-200 bg-[#fbfcf8] px-4 text-sm font-semibold text-[#0f172a] transition hover:border-[#0f766e] hover:bg-[#eef8f1]"
              >
                <Mail className="h-4 w-4" />
                Continue with Google
              </button>

              <div className="my-5 flex items-center gap-3">
                <div className="h-px flex-1 bg-slate-200" />
                <span className="text-xs font-semibold uppercase text-slate-400">or</span>
                <div className="h-px flex-1 bg-slate-200" />
              </div>

              <form onSubmit={handleEmailSignup} className="space-y-4">
                <div className="grid gap-4 sm:grid-cols-2">
                  <Field
                    label="Full name"
                    name="fullName"
                    value={form.fullName}
                    onChange={handleChange}
                    placeholder="Ada Okafor"
                    required
                  />
                  <Field
                    label="Phone"
                    name="phone"
                    type="tel"
                    value={form.phone}
                    onChange={handleChange}
                    placeholder="+234 801 234 5678"
                    required
                  />
                </div>

                <Field
                  label="Email"
                  name="email"
                  type="email"
                  value={form.email}
                  onChange={handleChange}
                  placeholder="you@example.com"
                  required
                />

                <Field
                  label="Password"
                  name="password"
                  type="password"
                  value={form.password}
                  onChange={handleChange}
                  placeholder="At least 8 characters"
                  minLength={8}
                  required
                />

                <div>
                  <label htmlFor="businessDescription" className="mb-1.5 block text-sm font-semibold text-slate-700">
                    Business description
                  </label>
                  <textarea
                    id="businessDescription"
                    name="businessDescription"
                    required
                    value={form.businessDescription}
                    onChange={handleChange}
                    placeholder="I sell natural skincare products to young professionals in Lagos..."
                    rows={4}
                    className="block w-full resize-none rounded-md border border-slate-300 bg-white px-4 py-3 text-sm shadow-sm outline-none transition placeholder:text-slate-400 focus:border-[#0f766e] focus:ring-2 focus:ring-emerald-100"
                  />
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="inline-flex h-12 w-full items-center justify-center gap-2 rounded-md bg-[#0f172a] px-5 text-sm font-bold text-white transition hover:bg-[#0f766e] disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {loading ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Creating account
                    </>
                  ) : (
                    <>
                      Continue to AI setup
                      <ArrowRight className="h-4 w-4" />
                    </>
                  )}
                </button>
              </form>

              <div className="mt-5 grid gap-2 text-xs text-slate-500 sm:grid-cols-2">
                <p className="flex items-center gap-2">
                  <ShieldCheck className="h-4 w-4 text-emerald-700" />
                  Free plan starts with one store
                </p>
                <p className="flex items-center gap-2">
                  <MessageCircle className="h-4 w-4 text-emerald-700" />
                  WhatsApp setup comes next
                </p>
              </div>
            </div>
          </div>
        </section>
      </div>
    </main>
  )
}

function Field({ label, name, value, onChange, type = 'text', ...props }) {
  return (
    <div>
      <label htmlFor={name} className="mb-1.5 block text-sm font-semibold text-slate-700">
        {label}
      </label>
      <input
        id={name}
        name={name}
        type={type}
        value={value}
        onChange={onChange}
        className="block h-11 w-full rounded-md border border-slate-300 bg-white px-4 text-sm shadow-sm outline-none transition placeholder:text-slate-400 focus:border-[#0f766e] focus:ring-2 focus:ring-emerald-100"
        {...props}
      />
    </div>
  )
}
