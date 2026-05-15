import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { ArrowRight, Check, Loader2, Store, Save, Building, CreditCard, ShieldCheck } from 'lucide-react'
import { createStore, updateStore, updateUser } from '../../lib/api'
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
        template: store.template || 'fashion',
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
      // 1. Update User info (Bank details)
      const userRes = await updateUser(bankForm)
      const updatedUser = userRes.data.user
      localStorage.setItem('aaje_user', JSON.stringify(updatedUser))
      setUser(updatedUser)

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
                  <label className="text-sm font-bold text-gray-700">WhatsApp Number</label>
                  <input 
                    className="rounded-lg border border-gray-200 px-4 py-2.5 focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 outline-none transition" 
                    name="contact_whatsapp" 
                    value={form.contact_whatsapp} 
                    onChange={handleFormChange}
                  />
                </div>
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

              <div className="grid sm:grid-cols-2 gap-4">
                <div className="grid gap-2">
                  <label className="text-sm font-bold text-gray-700">Template</label>
                  <select 
                    className="rounded-lg border border-gray-200 px-4 py-2.5 focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 outline-none transition bg-white" 
                    name="template" 
                    value={form.template} 
                    onChange={handleFormChange}
                  >
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

          {/* Settlement Account */}
          <section className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
            <div className="flex items-center justify-between mb-6 pb-2 border-b border-gray-50">
              <h2 className="flex items-center gap-2 font-bold text-gray-900">
                <CreditCard className="h-5 w-5 text-blue-600" />
                Settlement Account
              </h2>
              <div className="flex items-center gap-1 text-[10px] font-bold text-blue-600 uppercase tracking-widest">
                <ShieldCheck className="h-3 w-3" />
                Squad Secure
              </div>
            </div>
            <p className="text-xs text-gray-500 mb-6">
              This is where your funds will be settled after payments are confirmed. Ensure these details are accurate.
            </p>
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
