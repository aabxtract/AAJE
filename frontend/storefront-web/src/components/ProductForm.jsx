import { useEffect, useState } from 'react'
import { Loader2, Sparkles, X } from 'lucide-react'
import { generateProductDescription } from '../lib/api'

export default function ProductForm({ product, storeId, onSubmit, onCancel }) {
  const [form, setForm] = useState({
    store_id: storeId,
    name: '',
    description: '',
    category: '',
    price: '',
    image_url: '',
    stock_quantity: 0,
    low_stock_threshold: 3,
    is_active: true,
  })
  const [generating, setGenerating] = useState(false)

  useEffect(() => {
    if (product) setForm({ ...product, price: String(product.price ?? ''), stock_quantity: Number(product.stock_quantity || 0) })
  }, [product])

  function change(event) {
    const { name, value, checked, type } = event.target
    setForm((current) => ({ ...current, [name]: type === 'checkbox' ? checked : value }))
  }

  function imageChange(event) {
    const file = event.target.files?.[0]
    if (!file) return
    const reader = new FileReader()
    reader.onload = () => setForm((current) => ({ ...current, image_url: reader.result }))
    reader.readAsDataURL(file)
  }

  async function describe() {
    if (!form.name) return
    setGenerating(true)
    try {
      const res = await generateProductDescription({ product_name: form.name, category: form.category })
      setForm((current) => ({ ...current, description: res.data.description || res.data.sales_copy || current.description, category: res.data.category || current.category }))
    } finally {
      setGenerating(false)
    }
  }

  function submit(event) {
    event.preventDefault()
    onSubmit({
      ...form,
      store_id: storeId,
      price: Number(form.price),
      stock_quantity: Number(form.stock_quantity),
      low_stock_threshold: Number(form.low_stock_threshold),
    })
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <form onSubmit={submit} className="max-h-[92vh] w-full max-w-xl overflow-y-auto rounded-lg bg-white shadow-xl">
        <div className="sticky top-0 flex items-center justify-between border-b bg-white px-5 py-4">
          <h2 className="font-bold">{product ? 'Edit Product' : 'Add Product'}</h2>
          <button type="button" className="rounded p-1 hover:bg-gray-100" onClick={onCancel}><X className="h-5 w-5" /></button>
        </div>
        <div className="grid gap-4 p-5">
          <label className="text-sm font-medium">
            Product image
            <input className="input-field mt-1" type="file" accept="image/*" onChange={imageChange} />
          </label>
          {form.image_url && <img src={form.image_url} alt="" className="h-28 w-28 rounded-lg object-cover" />}
          <label className="text-sm font-medium">Name<input required name="name" value={form.name} onChange={change} className="input-field mt-1" /></label>
          <label className="text-sm font-medium">Category<input name="category" value={form.category} onChange={change} className="input-field mt-1" /></label>
          <label className="text-sm font-medium">
            Description
            <textarea name="description" value={form.description || ''} onChange={change} className="input-field mt-1 min-h-24" />
          </label>
          <button type="button" className="btn-secondary justify-self-start" onClick={describe} disabled={generating || !form.name}>
            {generating ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Sparkles className="mr-2 h-4 w-4" />}
            Generate Description
          </button>
          <div className="grid gap-4 sm:grid-cols-3">
            <label className="text-sm font-medium">Price<input required min="0" name="price" type="number" value={form.price} onChange={change} className="input-field mt-1" /></label>
            <label className="text-sm font-medium">Stock<input required min="0" name="stock_quantity" type="number" value={form.stock_quantity} onChange={change} className="input-field mt-1" /></label>
            <label className="text-sm font-medium">Low stock<input min="0" name="low_stock_threshold" type="number" value={form.low_stock_threshold} onChange={change} className="input-field mt-1" /></label>
          </div>
          <label className="flex items-center gap-2 text-sm"><input type="checkbox" name="is_active" checked={form.is_active} onChange={change} /> Active in store</label>
        </div>
        <div className="flex gap-3 border-t p-5">
          <button type="button" className="btn-secondary flex-1" onClick={onCancel}>Cancel</button>
          <button className="btn-primary flex-1">{product ? 'Save Product' : 'Add Product'}</button>
        </div>
      </form>
    </div>
  )
}
