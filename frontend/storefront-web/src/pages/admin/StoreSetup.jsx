import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { ArrowRight, Check, Loader2, Store } from 'lucide-react'
import AIStoreBuilder from '../../components/AIStoreBuilder'
import { createStore } from '../../lib/api'
import { generateSlug, getDemoUserId } from '../../lib/utils'

export default function StoreSetup() {
  const navigate = useNavigate()
  const [step, setStep] = useState('ai')
  const [aiResult, setAiResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [created, setCreated] = useState(null)
  const [form, setForm] = useState({
    user_id: getDemoUserId(),
    store_name: '',
    slug: '',
    description: '',
    logo_url: '',
    contact_whatsapp: '',
    business_category: '',
    pickup_delivery_note: '',
    theme_json: { style: 'clean', primary_color: '#111827', layout: 'simple_grid' },
    is_active: true,
  })

  useEffect(() => {
    if (!aiResult) return
    setForm((current) => ({
      ...current,
      store_name: aiResult.store_name || '',
      slug: generateSlug(aiResult.store_name || ''),
      description: aiResult.description || '',
      business_category: aiResult.categories?.[0] || '',
      theme_json: { ...current.theme_json, ...(aiResult.theme || {}) },
    }))
  }, [aiResult])

  function change(event) {
    const { name, value } = event.target
    setForm((current) => ({ ...current, [name]: value, ...(name === 'store_name' ? { slug: generateSlug(value) } : {}) }))
  }

  function themeChange(event) {
    setForm((current) => ({ ...current, theme_json: { ...current.theme_json, [event.target.name]: event.target.value } }))
  }

  function imageChange(event) {
    const file = event.target.files?.[0]
    if (!file) return
    const reader = new FileReader()
    reader.onload = () => setForm((current) => ({ ...current, logo_url: reader.result }))
    reader.readAsDataURL(file)
  }

  async function submit(event) {
    event.preventDefault()
    setLoading(true)
    try {
      const res = await createStore(form)
      setCreated(res.data)
      setStep('success')
    } finally {
      setLoading(false)
    }
  }

  if (step === 'ai') {
    return (
      <main className="flex min-h-screen items-center justify-center p-4">
        <div className="w-full max-w-xl">
          <AIStoreBuilder onUseStore={(data) => { setAiResult(data); setStep('form') }} />
        </div>
      </main>
    )
  }

  if (step === 'success') {
    const slug = created?.slug || form.slug
    return (
      <main className="flex min-h-screen items-center justify-center p-4 text-center">
        <div className="card w-full max-w-md p-8">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-emerald-100"><Check className="h-7 w-7 text-emerald-700" /></div>
          <h1 className="mt-4 text-2xl font-bold">Store Created</h1>
          <p className="mt-2 text-sm text-gray-500">Your storefront is ready to receive products and orders.</p>
          <div className="mt-6 flex gap-3">
            <Link className="btn-secondary flex-1" to={`/store/${slug}`}>Open Store</Link>
            <button className="btn-primary flex-1" onClick={() => navigate('/admin/dashboard')}>Dashboard</button>
          </div>
        </div>
      </main>
    )
  }

  return (
    <main className="mx-auto max-w-3xl px-4 py-8">
      <div className="mb-6">
        <h1 className="flex items-center gap-2 text-2xl font-bold"><Store className="h-6 w-6 text-primary-600" />Store Setup</h1>
        <p className="text-sm text-gray-500">Confirm the AI setup and add the owner details.</p>
      </div>
      <form onSubmit={submit} className="space-y-5">
        <section className="card grid gap-4 p-5">
          <label className="text-sm font-medium">Logo/image<input className="input-field mt-1" type="file" accept="image/*" onChange={imageChange} /></label>
          {form.logo_url && <img src={form.logo_url} alt="" className="h-20 w-20 rounded-lg object-cover" />}
          <label className="text-sm font-medium">Store name<input required className="input-field mt-1" name="store_name" value={form.store_name} onChange={change} /></label>
          <label className="text-sm font-medium">Slug<input required className="input-field mt-1" name="slug" value={form.slug} onChange={change} /></label>
          <label className="text-sm font-medium">Description<textarea className="input-field mt-1 min-h-24" name="description" value={form.description} onChange={change} /></label>
          <div className="grid gap-4 sm:grid-cols-2">
            <label className="text-sm font-medium">WhatsApp<input className="input-field mt-1" name="contact_whatsapp" value={form.contact_whatsapp} onChange={change} /></label>
            <label className="text-sm font-medium">Business category<input className="input-field mt-1" name="business_category" value={form.business_category} onChange={change} /></label>
          </div>
          <label className="text-sm font-medium">Pickup/delivery note<textarea className="input-field mt-1" name="pickup_delivery_note" value={form.pickup_delivery_note} onChange={change} /></label>
        </section>
        <section className="card grid gap-4 p-5 sm:grid-cols-3">
          <label className="text-sm font-medium">Style<select className="input-field mt-1" name="style" value={form.theme_json.style} onChange={themeChange}><option>clean</option><option>bold</option><option>local</option><option>premium</option><option>playful</option></select></label>
          <label className="text-sm font-medium">Primary color<input className="mt-1 h-10 w-full" type="color" name="primary_color" value={form.theme_json.primary_color} onChange={themeChange} /></label>
          <label className="text-sm font-medium">Layout<select className="input-field mt-1" name="layout" value={form.theme_json.layout} onChange={themeChange}><option>simple_grid</option><option>list</option></select></label>
        </section>
        <div className="flex gap-3">
          <button type="button" className="btn-secondary" onClick={() => setStep('ai')}>Back</button>
          <button className="btn-primary flex-1" disabled={loading}>{loading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <ArrowRight className="mr-2 h-4 w-4" />}Create Store</button>
        </div>
      </form>
    </main>
  )
}
