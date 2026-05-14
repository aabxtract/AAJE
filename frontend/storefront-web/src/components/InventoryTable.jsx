import { useState } from 'react'
import { AlertTriangle, Minus, Plus } from 'lucide-react'

export default function InventoryTable({ products, onAdjust }) {
  const [active, setActive] = useState(null)
  const [quantity, setQuantity] = useState(1)
  const [movementType, setMovementType] = useState('stock_added')
  const [reason, setReason] = useState('')
  const low = products.filter((p) => Number(p.stock_quantity) <= Number(p.low_stock_threshold || 0))

  function submit() {
    onAdjust({
      store_id: active.store_id,
      product_id: active.id,
      movement_type: movementType,
      quantity: Number(quantity),
      reason,
    })
    setActive(null)
    setQuantity(1)
    setReason('')
  }

  return (
    <div className="space-y-5">
      {low.length > 0 && (
        <div className="flex gap-3 rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
          <AlertTriangle className="h-5 w-5" />
          <p>{low.map((p) => p.name).join(', ')} {low.length === 1 ? 'is' : 'are'} low in stock.</p>
        </div>
      )}
      <div className="card overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200 text-sm">
          <thead className="bg-gray-50 text-left text-xs uppercase text-gray-500">
            <tr><th className="px-4 py-3">Product</th><th className="px-4 py-3">Category</th><th className="px-4 py-3 text-right">Stock</th><th className="px-4 py-3 text-right">Actions</th></tr>
          </thead>
          <tbody className="divide-y divide-gray-100 bg-white">
            {products.map((product) => (
              <tr key={product.id}>
                <td className="px-4 py-3 font-medium">{product.name}</td>
                <td className="px-4 py-3 text-gray-500">{product.category}</td>
                <td className="px-4 py-3 text-right">{product.stock_quantity} / {product.low_stock_threshold}</td>
                <td className="px-4 py-3 text-right">
                  <button className="btn-secondary mr-2 px-3 py-1.5" onClick={() => { setActive(product); setMovementType('stock_added') }}><Plus className="h-4 w-4" /></button>
                  <button className="btn-secondary px-3 py-1.5" onClick={() => { setActive(product); setMovementType('stock_removed') }}><Minus className="h-4 w-4" /></button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {active && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="w-full max-w-md rounded-lg bg-white p-5 shadow-xl">
            <h3 className="font-bold">Adjust {active.name}</h3>
            <select className="input-field mt-4" value={movementType} onChange={(e) => setMovementType(e.target.value)}>
              <option value="stock_added">Stock added</option>
              <option value="stock_removed">Stock removed</option>
              <option value="manual_adjustment">Manual adjustment</option>
            </select>
            <input className="input-field mt-3" min="1" type="number" value={quantity} onChange={(e) => setQuantity(e.target.value)} />
            <input className="input-field mt-3" value={reason} onChange={(e) => setReason(e.target.value)} placeholder="Reason" />
            <div className="mt-5 flex gap-3">
              <button className="btn-secondary flex-1" onClick={() => setActive(null)}>Cancel</button>
              <button className="btn-primary flex-1" onClick={submit}>Save</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
