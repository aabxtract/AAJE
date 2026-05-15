import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Plus, Package, Loader2 } from 'lucide-react'
import ProductCard from '../../components/ProductCard'
import ProductForm from '../../components/ProductForm'
import { createProduct, deleteProduct, updateProduct } from '../../lib/api'
import { useOwnerStore, useProducts } from '../../hooks/useStorefront'
import AdminLayout from '../../components/AdminLayout'

export default function Products() {
  const { store, loading: storeLoading } = useOwnerStore()
  const { products, loading, refresh } = useProducts(store?.id)
  const [editing, setEditing] = useState(null)
  const [showForm, setShowForm] = useState(false)
  const user = JSON.parse(localStorage.getItem('aaje_user') || '{}')

  async function save(data) {
    try {
      if (editing) await updateProduct(editing.id, data)
      else await createProduct({ ...data, store_id: store.id })
      setEditing(null)
      setShowForm(false)
      refresh()
    } catch (err) {
      console.error('Failed to save product:', err)
      alert('Failed to save product. Please try again.')
    }
  }

  async function remove(product) {
    if (!confirm(`Delete ${product.name}?`)) return
    try {
      await deleteProduct(product.id)
      refresh()
    } catch (err) {
      console.error('Failed to delete product:', err)
      alert('Failed to delete product.')
    }
  }

  if (storeLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-50">
        <Loader2 className="h-8 w-8 animate-spin text-emerald-600" />
      </div>
    )
  }

  if (!store) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-gray-50 p-4">
        <div className="rounded-xl border border-gray-200 bg-white p-8 shadow-sm text-center">
          <h2 className="text-xl font-bold">No store found</h2>
          <p className="mt-2 text-gray-500">Create your store first to manage products.</p>
          <Link className="mt-4 inline-flex items-center justify-center rounded-md bg-[#0f172a] px-6 py-2 text-sm font-bold text-white transition hover:bg-emerald-700" to="/admin/store-setup">
            Go to Store Setup
          </Link>
        </div>
      </main>
    )
  }

  return (
    <AdminLayout store={store} user={user}>
      <div className="space-y-8">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-2xl font-black text-[#0f172a]">Products</h1>
            <p className="text-sm text-gray-500">Manage your store's catalog and offerings</p>
          </div>
          <button 
            className="inline-flex items-center justify-center gap-2 rounded-lg bg-emerald-600 px-5 py-2.5 text-sm font-bold text-white shadow-md transition hover:bg-emerald-700" 
            onClick={() => { setEditing(null); setShowForm(true) }}
          >
            <Plus className="h-4 w-4" />
            Add Product
          </button>
        </div>

        {loading ? (
          <div className="flex h-64 items-center justify-center">
            <Loader2 className="h-8 w-8 animate-spin text-gray-300" />
          </div>
        ) : products.length > 0 ? (
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {products.map((product) => (
              <ProductCard 
                key={product.id} 
                product={product} 
                isAdmin 
                onSelect={(p) => { setEditing(p); setShowForm(true) }} 
                onDelete={remove} 
              />
            ))}
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center rounded-xl border-2 border-dashed border-gray-200 bg-white py-20 text-center">
            <div className="grid h-16 w-16 place-items-center rounded-full bg-gray-50 text-gray-400 mb-4">
              <Package className="h-8 w-8" />
            </div>
            <h3 className="text-lg font-bold text-gray-900">Your catalog is empty</h3>
            <p className="mt-2 max-w-xs text-sm text-gray-500">
              Add your first product or service to start making sales on AAJE.
            </p>
            <button 
              onClick={() => { setEditing(null); setShowForm(true) }}
              className="mt-6 text-sm font-bold text-emerald-700 hover:underline"
            >
              Add your first product
            </button>
          </div>
        )}
      </div>

      {showForm && (
        <ProductForm 
          product={editing} 
          storeId={store.id} 
          onSubmit={save} 
          onCancel={() => { setShowForm(false); setEditing(null) }} 
        />
      )}
    </AdminLayout>
  )
}
