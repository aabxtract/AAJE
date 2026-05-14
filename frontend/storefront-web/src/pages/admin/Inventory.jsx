import { Link } from 'react-router-dom'
import InventoryTable from '../../components/InventoryTable'
import { adjustInventory } from '../../lib/api'
import { useOwnerStore, useProducts } from '../../hooks/useStorefront'

export default function Inventory() {
  const { store, loading: storeLoading } = useOwnerStore()
  const { products, loading, refresh } = useProducts(store?.id)

  async function adjust(data) {
    await adjustInventory(data)
    refresh()
  }

  if (storeLoading) return <main className="p-8 text-gray-500">Loading store...</main>
  if (!store) return <main className="flex min-h-screen items-center justify-center"><Link className="btn-primary" to="/admin/store-setup">Create store first</Link></main>

  return (
    <main className="mx-auto max-w-7xl px-4 py-8">
      <div className="mb-6">
        <h1 className="text-2xl font-bold">Inventory</h1>
        <p className="text-sm text-gray-500">Track stock and emit inventory events to Squad Intelligence.</p>
      </div>
      {loading ? <p className="text-gray-500">Loading inventory...</p> : <InventoryTable products={products} onAdjust={adjust} />}
    </main>
  )
}
