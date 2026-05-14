import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Plus } from 'lucide-react'
import ProductCard from '../../components/ProductCard'
import ProductForm from '../../components/ProductForm'
import { createProduct, deleteProduct, updateProduct } from '../../lib/api'
import { useOwnerStore, useProducts } from '../../hooks/useStorefront'

export default function Products() {
  const { store, loading: storeLoading } = useOwnerStore()
  const { products, loading, refresh } = useProducts(store?.id)
  const [editing, setEditing] = useState(null)
  const [showForm, setShowForm] = useState(false)

  async function save(data) {
    if (editing) await updateProduct(editing.id, data)
    else await createProduct(data)
    setEditing(null)
    setShowForm(false)
    refresh()
  }

  async function remove(product) {
    if (!confirm(`Delete ${product.name}?`)) return
    await deleteProduct(product.id)
    refresh()
  }

  if (storeLoading) return <main className="p-8 text-gray-500">Loading store...</main>
  if (!store) return <main className="flex min-h-screen items-center justify-center"><Link className="btn-primary" to="/admin/store-setup">Create store first</Link></main>

  return (
    <main className="mx-auto max-w-7xl px-4 py-8">
      <div className="mb-6 flex items-center justify-between">
        <div><h1 className="text-2xl font-bold">Products</h1><p className="text-sm text-gray-500">{products.length} listed products</p></div>
        <button className="btn-primary" onClick={() => { setEditing(null); setShowForm(true) }}><Plus className="mr-2 h-4 w-4" />Add Product</button>
      </div>
      {loading ? <p className="text-gray-500">Loading products...</p> : (
        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {products.map((product) => <ProductCard key={product.id} product={product} isAdmin onSelect={(p) => { setEditing(p); setShowForm(true) }} onDelete={remove} />)}
        </div>
      )}
      {showForm && <ProductForm product={editing} storeId={store.id} onSubmit={save} onCancel={() => { setShowForm(false); setEditing(null) }} />}
    </main>
  )
}
