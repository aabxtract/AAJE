import { AlertTriangle, ShoppingBag } from 'lucide-react'
import { formatCurrency } from '../lib/utils'

export default function ProductCard({ product, isAdmin = false, onSelect, onDelete }) {
  const out = Number(product.stock_quantity) <= 0
  const low = Number(product.stock_quantity) <= Number(product.low_stock_threshold || 0)

  return (
    <article className={`card overflow-hidden ${product.is_active === false ? 'opacity-60' : ''}`}>
      <div className="relative aspect-square bg-gray-100">
        {product.image_url ? (
          <img src={product.image_url} alt={product.name} className="h-full w-full object-cover" />
        ) : (
          <div className="flex h-full w-full items-center justify-center text-sm text-gray-400">No image</div>
        )}
        {(out || low) && (
          <span className={`absolute right-2 top-2 inline-flex items-center gap-1 rounded-full px-2 py-1 text-xs font-semibold ${out ? 'bg-red-100 text-red-800' : 'bg-amber-100 text-amber-800'}`}>
            <AlertTriangle className="h-3 w-3" />
            {out ? 'Out' : 'Low'}
          </span>
        )}
      </div>
      <div className="p-4">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <h3 className="font-semibold">{product.name}</h3>
            <p className="mt-1 line-clamp-2 text-sm text-gray-500">{product.description}</p>
          </div>
          <p className="shrink-0 font-bold text-primary-700">{formatCurrency(product.price)}</p>
        </div>
        <div className="mt-4 flex items-center justify-between gap-2">
          <span className="rounded bg-gray-100 px-2 py-1 text-xs text-gray-600">{product.category || 'General'}</span>
          {isAdmin ? (
            <div className="flex gap-2">
              <button className="text-sm font-semibold text-primary-700" onClick={() => onSelect?.(product)}>Edit</button>
              {onDelete && <button className="text-sm font-semibold text-red-600" onClick={() => onDelete(product)}>Delete</button>}
            </div>
          ) : (
            <button className="btn-primary px-3 py-1.5 text-xs" disabled={out} onClick={() => onSelect?.(product)}>
              <ShoppingBag className="mr-1 h-3 w-3" />
              Buy
            </button>
          )}
        </div>
      </div>
    </article>
  )
}
