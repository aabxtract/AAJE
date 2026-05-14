import { MessageCircle, Share2, Store } from 'lucide-react'

export default function StoreHeader({ store, onShare }) {
  const theme = store?.theme_json || store?.theme || {}
  const color = theme.primary_color || '#111827'
  const whatsapp = (store.contact_whatsapp || '').replace(/\D/g, '')

  return (
    <header className="border-b bg-white">
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-4 sm:px-6 lg:px-8">
        <div className="flex min-w-0 items-center gap-3">
          {store.logo_url ? (
            <img src={store.logo_url} alt={store.store_name} className="h-12 w-12 rounded-lg object-cover" />
          ) : (
            <div className="flex h-12 w-12 items-center justify-center rounded-lg" style={{ backgroundColor: `${color}18` }}>
              <Store className="h-6 w-6" style={{ color }} />
            </div>
          )}
          <div className="min-w-0">
            <h1 className="truncate text-xl font-bold">{store.store_name}</h1>
            {(store.tagline || store.business_category) && <p className="truncate text-sm text-gray-500">{store.tagline || store.business_category}</p>}
          </div>
        </div>
        <div className="flex items-center gap-2">
          {whatsapp && (
            <a className="btn-secondary px-3" href={`https://wa.me/${whatsapp}`} target="_blank" rel="noreferrer">
              <MessageCircle className="h-4 w-4" />
            </a>
          )}
          <button className="btn-secondary px-3" onClick={onShare}>
            <Share2 className="h-4 w-4" />
          </button>
        </div>
      </div>
      {store.description && <div className="mx-auto max-w-7xl px-4 pb-4 text-sm text-gray-600 sm:px-6 lg:px-8">{store.description}</div>}
    </header>
  )
}
