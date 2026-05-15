import { Link } from 'react-router-dom'
import { BarChart3, Loader2 } from 'lucide-react'
import InventoryTable from '../../components/InventoryTable'
import { adjustInventory } from '../../lib/api'
import { useOwnerStore, useProducts } from '../../hooks/useStorefront'
import AdminLayout from '../../components/AdminLayout'

export default function Inventory() {
  const { store, loading: storeLoading } = useOwnerStore()
  const { products, loading, refresh } = useProducts(store?.id)
  const user = JSON.parse(localStorage.getItem('aaje_user') || '{}')

  async function adjust(data) {
    try {
      await adjustInventory(data)
      refresh()
    } catch (err) {
      console.error('Failed to adjust inventory:', err)
      alert('Failed to adjust inventory stock.')
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
          <p className="mt-2 text-gray-500">Create your store first to manage inventory.</p>
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
        <div>
          <h1 className="text-2xl font-black text-[#0f172a]">Inventory</h1>
          <p className="text-sm text-gray-500">Track stock levels and manage product availability</p>
        </div>

        {loading ? (
          <div className="flex h-64 items-center justify-center">
            <Loader2 className="h-8 w-8 animate-spin text-gray-300" />
          </div>
        ) : products.length > 0 ? (
          <div className="rounded-xl border border-gray-200 bg-white shadow-sm overflow-hidden">
            <InventoryTable products={products} onAdjust={adjust} />
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center rounded-xl border-2 border-dashed border-gray-200 bg-white py-20 text-center">
            <div className="grid h-16 w-16 place-items-center rounded-full bg-gray-50 text-gray-400 mb-4">
              <BarChart3 className="h-8 w-8" />
            </div>
            <h3 className="text-lg font-bold text-gray-900">No inventory to track</h3>
            <p className="mt-2 max-w-xs text-sm text-gray-500">
              Once you add products to your store, you can manage their stock levels and inventory history here.
            </p>
            <Link to="/admin/products" className="mt-6 text-sm font-bold text-emerald-700 hover:underline">
              Add your first product
            </Link>
          </div>
        )}
      </div>
    </AdminLayout>
  )
}
