import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { ArrowRight, Check, Loader2, Store, Save, Building, CreditCard, ShieldCheck } from 'lucide-react'
import { createStore, updateStore, updateUser, setPayoutAccount, connectWhatsapp, verifyWhatsappConnection } from '../../lib/api'
import { generateSlug, getDemoUserId } from '../../lib/utils'
import { useOwnerStore } from '../../hooks/useStorefront'
import AdminLayout from '../../components/AdminLayout'

export default function StoreSetup() {
  const navigate = useNavigate()
  const { store, loading: storeLoading, refresh } = useOwnerStore()
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState(false)
  const [user, setUser] = useState(() => JSON.parse(localStorage.getItem('aaje_user') || '{}'))

  const [form, setForm] = useState({
    store_name: '',
    slug: '',
    description: '',
    tagline: '',
    contact_whatsapp: '',
    business_category: '',
    theme: 'default',
    template: 'fashion',
  })

  const [bankForm, setBankForm] = useState({
    full_name: user.full_name || '',
    verified_bank_account: user.verified_bank_account || '',
    verified_bank_name: user.verified_bank_name || '',
    verified_bank_code: user.verified_bank_code || '',
  })

  // WhatsApp connect OTP state machine.
  // idle → awaiting_otp (after sending code) → verified (after successful OTP).
  const [otpStage, setOtpStage] = useState(user.whatsapp_verified ? 'verified' : 'idle')
  const [otpValue, setOtpValue] = useState('')
  const [otpBusy, setOtpBusy] = useState(false)
  const [otpFeedback, setOtpFeedback] = useState(null) // { kind: 'ok' | 'err', text }

  async function handleSendOtp() {
    if (!form.contact_whatsapp) {
      setOtpFeedback({ kind: 'err', text: 'Enter your WhatsApp number first.' })
      return
    }
    setOtpBusy(true)
    setOtpFeedback(null)
    try {
      await connectWhatsapp({ whatsapp_no: form.contact_whatsapp })
      setOtpStage('awaiting_otp')
      setOtpFeedback({ kind: 'ok', text: 'Code sent. Check your WhatsApp.' })
    } catch (err) {
      const detail = err.response?.data?.detail || 'Could not send code. Try again.'
      setOtpFeedback({ kind: 'err', text: detail })
    } finally {
      setOtpBusy(false)
    }
  }

  async function handleVerifyOtp() {
    if (!otpValue || otpValue.length !== 6) {
      setOtpFeedback({ kind: 'err', text: 'Enter the 6-digit code.' })
      return
    }
    setOtpBusy(true)
    setOtpFeedback(null)
    try {
      const res = await verifyWhatsappConnection({
        whatsapp_no: form.contact_whatsapp,
        otp: otpValue,
      })
      const updatedUser = res.data || {}
      const merged = {
        ...user,
        ...updatedUser,
        whatsapp_connected: true,
        whatsapp_verified: true,
      }
      localStorage.setItem('aaje_user', JSON.stringify(merged))
      setUser(merged)
      setOtpStage('verified')
      setOtpValue('')
      setOtpFeedback({ kind: 'ok', text: 'WhatsApp linked.' })
    } catch (err) {
      const detail = err.response?.data?.detail || 'Invalid or expired code.'
      setOtpFeedback({ kind: 'err', text: detail })
    } finally {
      setOtpBusy(false)
    }
  }

  useEffect(() => {
    if (store) {
      setForm({
        store_name: store.store_name || '',
        slug: store.slug || '',
        description: store.description || '',
        tagline: store.tagline || '',
        contact_whatsapp: store.contact_whatsapp || '',
        business_category: store.config_json?.categories?.[0] || '',
        theme: store.theme || 'default',
        template: store.template || 'premium',
      })
    }
  }, [store])

  function handleFormChange(e) {
    const { name, value } = e.target
    setForm(prev => ({ 
      ...prev, 
      [name]: value,
      ...(name === 'store_name' && !store ? { slug: generateSlug(value) } : {}) 
    }))
  }

  function handleBankChange(e) {
    const { name, value } = e.target
    setBankForm(prev => ({ ...prev, [name]: value }))
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setLoading(true)
    setSuccess(false)
    try {
      // 1a. Persist payout account via the MVP endpoint. Customers see this
      //     account on the storefront checkout for the manual-transfer flow.
      let updatedUser = user
      try {
        await setPayoutAccount(bankForm)
      } catch (err) {
        console.warn('setPayoutAccount failed (legacy backend?):', err)
      }
      // 1b. Legacy updateUser — kept while the old auth router is still
      //     serving the deployed backend. Safe to remove once migration completes.
      try {
        const userRes = await updateUser(bankForm)
        updatedUser = userRes.data.user || updatedUser
      } catch (err) {
        console.warn('updateUser (legacy) failed:', err)
      }
      const mergedUser = {
        ...updatedUser,
        full_name: bankForm.full_name || updatedUser?.full_name,
        verified_bank_account: bankForm.verified_bank_account,
        verified_bank_name: bankForm.verified_bank_name,
        verified_bank_code: bankForm.verified_bank_code,
      }
      localStorage.setItem('aaje_user', JSON.stringify(mergedUser))
      setUser(mergedUser)

      // 2. Update Store info
      if (store) {
        await updateStore(store.id, form)
      } else {
        const res = await createStore({
          ...form,
          user_id: user.id,
          theme_json: { style: form.theme },
          config_json: { ...form, categories: [form.business_category] }
        })
        localStorage.setItem('aaje_store', JSON.stringify(res.data))
      }
      
      setSuccess(true)
      refresh()
      setTimeout(() => setSuccess(false), 3000)
    } catch (err) {
      console.error('Save error:', err)
      alert('Failed to save settings. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  if (storeLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-50">
        <Loader2 className="h-8 w-8 animate-spin text-emerald-600" />
      </div>
    )
  }

  return (
    <AdminLayout store={store} user={user}>
      <div className="max-w-4xl mx-auto space-y-8 pb-12">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-black text-[#0f172a]">{store ? 'Store Settings' : 'Store Setup'}</h1>
            <p className="text-sm text-gray-500">Configure your storefront identity and settlement accounts</p>
          </div>
          {success && (
            <div className="flex items-center gap-2 text-emerald-600 font-bold text-sm bg-emerald-50 px-3 py-1.5 rounded-full border border-emerald-100 animate-in fade-in slide-in-from-top-2">
              <Check className="h-4 w-4" />
              Settings Saved
            </div>
          )}
        </div>

        <form onSubmit={handleSubmit} className="space-y-8">
          {/* Business Identity */}
          <section className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
            <h2 className="flex items-center gap-2 font-bold text-gray-900 mb-6 pb-2 border-b border-gray-50">
              <Store className="h-5 w-5 text-emerald-600" />
              Business Identity
            </h2>
            <div className="grid gap-6">
              <div className="grid gap-2">
                <label className="text-sm font-bold text-gray-700">Store Name</label>
                <input 
                  required 
                  className="rounded-lg border border-gray-200 px-4 py-2.5 focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 outline-none transition" 
                  name="store_name" 
                  value={form.store_name} 
                  onChange={handleFormChange} 
                  placeholder="e.g. Lagos Luxury Wears"
                />
              </div>

              <div className="grid gap-2">
                <label className="text-sm font-bold text-gray-700">Store Slug (URL)</label>
                <div className="flex items-center">
                  <span className="bg-gray-50 border border-r-0 border-gray-200 px-3 py-2.5 rounded-l-lg text-sm text-gray-400 font-medium">aaje.store/</span>
                  <input 
                    required 
                    className="flex-1 rounded-r-lg border border-gray-200 px-4 py-2.5 focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 outline-none transition" 
                    name="slug" 
                    value={form.slug} 
                    onChange={handleFormChange}
                    disabled={!!store}
                  />
                </div>
                <p className="text-[10px] text-gray-400 font-medium mt-1 uppercase tracking-wider">Note: Slugs cannot be changed after creation</p>
              </div>

              <div className="grid gap-2">
                <label className="text-sm font-bold text-gray-700">Tagline / Motto</label>
                <input 
                  className="rounded-lg border border-gray-200 px-4 py-2.5 focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 outline-none transition" 
                  name="tagline" 
                  value={form.tagline} 
                  onChange={handleFormChange}
                  placeholder="e.g. Your one-stop shop for affordable tech"
                />
              </div>

              <div className="grid gap-2">
                <label className="text-sm font-bold text-gray-700">Description</label>
                <textarea 
                  className="rounded-lg border border-gray-200 px-4 py-2.5 focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 outline-none transition min-h-[100px]" 
                  name="description" 
                  value={form.description} 
                  onChange={handleFormChange}
                  placeholder="Tell customers about your business..."
                />
              </div>

              <div className="grid sm:grid-cols-2 gap-4">
                <div className="grid gap-2">
                  <label className="text-sm font-bold text-gray-700">Business Category</label>
                  <input 
                    className="rounded-lg border border-gray-200 px-4 py-2.5 focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 outline-none transition" 
                    name="business_category" 
                    value={form.business_category} 
                    onChange={handleFormChange}
                  />
                </div>
              </div>

              <div className="pt-4 border-t border-gray-50">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h3 className="text-sm font-bold text-gray-900">WhatsApp Bot Connection</h3>
                    <p className="text-xs text-gray-500">
                      {otpStage === 'verified'
                        ? 'Linked. The bot will WhatsApp you for new orders and status changes.'
                        : 'Link your WhatsApp so the bot can alert you when buyers claim a transfer.'}
                    </p>
                  </div>
                  {otpStage === 'verified' && (
                    <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2.5 py-1 text-[11px] font-bold text-emerald-700 border border-emerald-100">
                      <Check className="h-3 w-3" />
                      Verified
                    </span>
                  )}
                </div>

                <div className="grid gap-2">
                  <label className="text-sm font-bold text-gray-700">WhatsApp Number</label>
                  <div className="flex gap-2">
                    <input
                      className="flex-1 rounded-lg border border-gray-200 px-4 py-2.5 focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 outline-none transition disabled:bg-gray-50 disabled:text-gray-400"
                      name="contact_whatsapp"
                      value={form.contact_whatsapp}
                      onChange={handleFormChange}
                      placeholder="e.g. 2348012345678"
                      disabled={otpStage !== 'idle'}
                    />
                    {otpStage !== 'verified' && (
                      <button
                        type="button"
                        onClick={handleSendOtp}
                        disabled={otpBusy || otpStage === 'awaiting_otp'}
                        className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-50 px-3 py-2 text-xs font-bold text-emerald-700 hover:bg-emerald-100 transition disabled:opacity-50"
                      >
                        {otpBusy && otpStage === 'idle' ? <Loader2 className="h-3 w-3 animate-spin" /> : null}
                        {otpStage === 'awaiting_otp' ? 'Code sent' : 'Send code'}
                      </button>
                    )}
                  </div>
                  <p className="text-[10px] text-gray-400">
                    Twilio sandbox? Send <code>join &lt;sandbox-code&gt;</code> from this number to
                    the Twilio bot first.
                  </p>
                </div>

                {otpStage === 'awaiting_otp' && (
                  <div className="mt-4 grid gap-2">
                    <label className="text-sm font-bold text-gray-700">Enter the 6-digit code</label>
                    <div className="flex gap-2">
                      <input
                        inputMode="numeric"
                        maxLength={6}
                        autoComplete="one-time-code"
                        className="flex-1 rounded-lg border border-gray-200 px-4 py-2.5 font-mono text-base tracking-[0.5em] focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 outline-none transition"
                        value={otpValue}
                        onChange={(e) => setOtpValue(e.target.value.replace(/\D/g, '').slice(0, 6))}
                        placeholder="• • • • • •"
                      />
                      <button
                        type="button"
                        onClick={handleVerifyOtp}
                        disabled={otpBusy || otpValue.length !== 6}
                        className="inline-flex items-center gap-1.5 rounded-lg bg-[#0f172a] px-4 py-2 text-xs font-bold text-white hover:bg-emerald-700 transition disabled:opacity-50"
                      >
                        {otpBusy ? <Loader2 className="h-3 w-3 animate-spin" /> : null}
                        Verify
                      </button>
                      <button
                        type="button"
                        onClick={() => {
                          setOtpStage('idle')
                          setOtpValue('')
                          setOtpFeedback(null)
                        }}
                        className="text-[11px] font-bold text-gray-500 hover:text-gray-900 transition"
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                )}

                {otpFeedback && (
                  <p
                    className={`mt-2 text-xs ${
                      otpFeedback.kind === 'ok' ? 'text-emerald-600' : 'text-red-600'
                    }`}
                  >
                    {otpFeedback.text}
                  </p>
                )}
              </div>

              <div className="grid sm:grid-cols-2 gap-4">
                <div className="grid gap-2">
                  <label className="text-sm font-bold text-gray-700">Template</label>
                  <select 
                    className="rounded-lg border border-gray-200 px-4 py-2.5 focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 outline-none transition bg-white" 
                    name="template" 
                    value={form.template} 
                    onChange={handleFormChange}
                  >
                    <option value="premium">Premium Commerce (Modern)</option>
                    <option value="fashion">Fashion & Lifestyle</option>
                    <option value="gadgets">Tech & Gadgets</option>
                    <option value="food">Food & Drinks</option>
                    <option value="creator">Creator & Services</option>
                  </select>
                </div>
                <div className="grid gap-2">
                  <label className="text-sm font-bold text-gray-700">Theme Color</label>
                  <select 
                    className="rounded-lg border border-gray-200 px-4 py-2.5 focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 outline-none transition bg-white" 
                    name="theme" 
                    value={form.theme} 
                    onChange={handleFormChange}
                  >
                    <option value="default">Default</option>
                    <option value="dark">Dark Mode</option>
                    <option value="luxury">Luxury Gold</option>
                    <option value="eco">Eco Green</option>
                  </select>
                </div>
              </div>
            </div>
          </section>

          {/* Payout Account (Manual transfer — MVP) */}
          <section className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
            <div className="flex items-center justify-between mb-6 pb-2 border-b border-gray-50">
              <h2 className="flex items-center gap-2 font-bold text-gray-900">
                <CreditCard className="h-5 w-5 text-blue-600" />
                Payout Account
              </h2>
              <div className="flex items-center gap-1 text-[10px] font-bold text-blue-600 uppercase tracking-widest">
                <ShieldCheck className="h-3 w-3" />
                Public on checkout
              </div>
            </div>
            <div className="mb-6 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-xs text-amber-900">
              <strong>Heads up:</strong> Your account number will be shown to
              customers at checkout. Make sure this is the account you want to
              receive payments on. When AAJE integrates Monnify next month,
              this becomes automated — for now it's manual and transparent.
            </div>
            <div className="grid gap-6">
              <div className="grid gap-2">
                <label className="text-sm font-bold text-gray-700">Beneficiary Name</label>
                <input 
                  className="rounded-lg border border-gray-200 px-4 py-2.5 focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 outline-none transition" 
                  name="full_name" 
                  value={bankForm.full_name} 
                  onChange={handleBankChange}
                  placeholder="Name as it appears on bank statement"
                />
              </div>

              <div className="grid sm:grid-cols-2 gap-4">
                <div className="grid gap-2">
                  <label className="text-sm font-bold text-gray-700">Account Number</label>
                  <input 
                    className="rounded-lg border border-gray-200 px-4 py-2.5 focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 outline-none transition" 
                    name="verified_bank_account" 
                    value={bankForm.verified_bank_account} 
                    onChange={handleBankChange}
                    placeholder="10-digit NUBAN"
                  />
                </div>
                <div className="grid gap-2">
                  <label className="text-sm font-bold text-gray-700">Bank Name</label>
                  <input 
                    className="rounded-lg border border-gray-200 px-4 py-2.5 focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 outline-none transition" 
                    name="verified_bank_name" 
                    value={bankForm.verified_bank_name} 
                    onChange={handleBankChange}
                    placeholder="e.g. Zenith Bank"
                  />
                </div>
              </div>
            </div>
          </section>

          <div className="flex gap-4 pt-4">
            <button 
              type="submit" 
              disabled={loading}
              className="flex-1 inline-flex items-center justify-center gap-2 rounded-xl bg-[#0f172a] px-6 py-4 text-sm font-bold text-white shadow-lg transition hover:bg-emerald-700 disabled:opacity-50"
            >
              {loading ? <Loader2 className="h-5 w-5 animate-spin" /> : <Save className="h-5 w-5" />}
              {store ? 'Save Changes' : 'Complete Setup'}
            </button>
            <button 
              type="button" 
              onClick={() => navigate('/dashboard')}
              className="px-6 py-4 text-sm font-bold text-gray-600 hover:text-gray-900 transition"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </AdminLayout>
  )
}
