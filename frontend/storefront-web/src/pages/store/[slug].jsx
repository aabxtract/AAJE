import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { Check, Copy, Loader2 } from 'lucide-react'
import TemplateRenderer from '../../templates/TemplateRenderer'
import CheckoutForm from '../../components/CheckoutForm'
import { createOrder, fetchTemplate, getProductsByStore, getStoreBySlug, claimOrderTransfer } from '../../lib/api'
import { formatCurrency } from '../../lib/utils'

// MVP buyer flow (no Squad/Monnify):
//   product card → CheckoutForm → POST /orders → transferStep (bank details +
//   "I've Transferred") → claimedStep (notify trader on WhatsApp).
// The trader's bank account comes back on the store response as
// `payment_account` (PaymentAccountResponse from /store/:slug).
//
// `slug` can come from useParams (legacy /store/:slug route) or be passed
// directly as a prop when rendered from a subdomain (App.jsx).

export default function StorePage({ slug: slugProp }) {
  const params = useParams()
  const slug = slugProp || params.slug
  const [template, setTemplate] = useState(null)
  const [store, setStore] = useState(null)
  const [products, setProducts] = useState([])
  const [loading, setLoading] = useState(true)
  const [selected, setSelected] = useState(null)
  const [checkoutLoading, setCheckoutLoading] = useState(false)
  const [stage, setStage] = useState('browse') // browse | transfer | claimed
  const [order, setOrder] = useState(null)
  const [error, setError] = useState('')
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    if (!slug) {
      setLoading(false)
      return
    }
    async function load() {
      setLoading(true)
      try {
        const storeRes = await getStoreBySlug(slug)
        setStore(storeRes.data)
        const productsRes = await getProductsByStore(storeRes.data.id || slug)
        setProducts((productsRes.data || []).filter((item) => item.is_active !== false))

        // Pull the matching template JSON. The store's theme_config carries the
        // template_id chosen during onboarding; fall back to creator_portfolio
        // (minimal) if missing/legacy.
        const templateId =
          storeRes.data.theme_config?.template_id ||
          storeRes.data.template ||
          'creator_portfolio'
        try {
          const tplRes = await fetchTemplate(templateId)
          setTemplate(tplRes.data)
        } catch {
          // Template not found — renderer handles null gracefully (returns null)
          setTemplate(null)
        }
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [slug])

  async function checkout(data) {
    setCheckoutLoading(true)
    setError('')
    try {
      const orderRes = await createOrder({
        store_id: store.id,
        store_slug: store.slug,
        customer_name: data.customer_name,
        customer_phone: data.customer_phone,
        customer_whatsapp: data.customer_phone,
        items: [{ product_id: data.product_id, quantity: data.quantity }],
      })
      setOrder(orderRes.data)
      setStage('transfer')
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not place order. Please try again.')
    } finally {
      setCheckoutLoading(false)
    }
  }

  async function handleClaimedTransfer() {
    if (!order) return
    setCheckoutLoading(true)
    setError('')
    try {
      await claimOrderTransfer(order.order_ref)
      setStage('claimed')
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          'Could not notify the seller. Please contact the store directly on WhatsApp.',
      )
    } finally {
      setCheckoutLoading(false)
    }
  }

  function copyAccountNumber() {
    const account = store?.payment_account?.account_number
    if (!account) return
    navigator.clipboard.writeText(account)
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }

  async function share() {
    const url = window.location.href
    if (navigator.share) await navigator.share({ title: store.store_name, text: store.description, url })
    else await navigator.clipboard.writeText(url)
  }

  if (loading) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-gray-50">
        <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
      </main>
    )
  }

  if (!store) {
    return (
      <main className="flex min-h-screen items-center justify-center text-center">
        <div>
          <h1 className="text-2xl font-bold">Store not found</h1>
          <p className="text-gray-500">This storefront is not available.</p>
        </div>
      </main>
    )
  }

  // --- Transfer step: order created, show bank details + "I've Transferred" --
  if (stage === 'transfer' && order) {
    const account = store.payment_account || { ready: false }
    return (
      <TransferStep
        order={order}
        store={store}
        account={account}
        loading={checkoutLoading}
        error={error}
        copied={copied}
        onCopy={copyAccountNumber}
        onClaim={handleClaimedTransfer}
        onCancel={() => {
          setStage('browse')
          setSelected(null)
          setOrder(null)
        }}
      />
    )
  }

  // --- Claimed step: trader notified, buyer waits ----------------------------
  if (stage === 'claimed' && order) {
    return (
      <ClaimedStep
        order={order}
        store={store}
        onDone={() => {
          setStage('browse')
          setSelected(null)
          setOrder(null)
        }}
      />
    )
  }

  // --- Selected product: show checkout form ----------------------------------
  if (selected) {
    return (
      <CheckoutForm
        product={selected}
        store={store}
        loading={checkoutLoading}
        error={error}
        onCancel={() => setSelected(null)}
        onSubmit={checkout}
      />
    )
  }

  // --- Browse: render the storefront via the universal template renderer ----
  return (
    <TemplateRenderer
      template={template}
      store={store}
      products={products}
      onSelect={setSelected}
      onShare={share}
    />
  )
}


// ---- Sub-components --------------------------------------------------------

function TransferStep({ order, store, account, loading, error, copied, onCopy, onClaim, onCancel }) {
  return (
    <main className="flex min-h-screen items-center justify-center bg-gray-50 p-4">
      <div className="w-full max-w-md rounded-2xl border border-emerald-100 bg-white p-6 shadow-lg">
        <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-4">
          <p className="text-xs font-bold uppercase tracking-wider text-emerald-700">
            Order {order.order_ref} placed
          </p>
          <p className="mt-1 text-sm text-gray-700">
            Complete payment by transferring to the account below.
          </p>
        </div>

        {account.ready && account.account_number ? (
          <div className="mt-5 divide-y divide-gray-100">
            <BankRow label="Bank" value={account.bank_name || '—'} />
            <BankRow label="Account name" value={account.account_name || '—'} />
            <div className="flex items-center justify-between py-2.5">
              <span className="text-sm text-gray-500">Account number</span>
              <div className="flex items-center gap-2">
                <span className="font-mono text-base font-semibold text-gray-900">
                  {account.account_number}
                </span>
                <button
                  onClick={onCopy}
                  className="inline-flex items-center gap-1 rounded-md border border-emerald-600 px-2.5 py-1 text-xs font-bold text-emerald-700 hover:bg-emerald-50"
                >
                  {copied ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
                  {copied ? 'Copied' : 'Copy'}
                </button>
              </div>
            </div>
          </div>
        ) : (
          <div className="mt-5 rounded-md bg-amber-50 p-3 text-xs text-amber-900">
            This seller hasn't added a bank account yet. Please contact{' '}
            <strong>{store.store_name}</strong> directly on WhatsApp to arrange payment.
          </div>
        )}

        <div className="mt-5 rounded-lg border-2 border-dashed border-amber-300 bg-white p-4 text-center">
          <p className="text-xs text-gray-500">Transfer exactly</p>
          <p className="text-3xl font-bold text-gray-900">{formatCurrency(order.total_amount)}</p>
        </div>

        <p className="mt-4 text-xs leading-relaxed text-gray-600">
          Open your banking app and send the exact amount above. After transferring, tap the
          button below — the seller will get a WhatsApp alert and confirm once they see your
          transfer.
        </p>

        {error && (
          <div className="mt-3 rounded-md bg-red-50 p-2.5 text-xs text-red-700">{error}</div>
        )}

        <div className="mt-5 flex gap-2">
          <button
            onClick={onCancel}
            className="flex-1 rounded-lg bg-gray-100 px-4 py-3 text-sm font-bold text-gray-700 hover:bg-gray-200"
          >
            Close
          </button>
          <button
            onClick={onClaim}
            disabled={loading || !account.ready}
            className="flex-1 inline-flex items-center justify-center gap-1.5 rounded-lg bg-emerald-600 px-4 py-3 text-sm font-bold text-white hover:bg-emerald-700 disabled:opacity-50"
          >
            {loading && <Loader2 className="h-4 w-4 animate-spin" />}
            I've Transferred
          </button>
        </div>
      </div>
    </main>
  )
}


function ClaimedStep({ order, store, onDone }) {
  return (
    <main className="flex min-h-screen items-center justify-center bg-gray-50 p-4">
      <div className="w-full max-w-md rounded-2xl bg-white p-8 text-center shadow-lg">
        <div className="mb-3 text-5xl">✅</div>
        <h2 className="text-lg font-bold text-emerald-700">Transfer claim sent</h2>
        <p className="mt-2 text-sm text-gray-700">
          We've notified <strong>{store.store_name}</strong> on WhatsApp. They'll check their
          bank and confirm your order shortly. You'll hear back from them on WhatsApp directly.
        </p>
        <p className="mt-4 text-xs text-gray-500">
          Order ref: <strong>{order.order_ref}</strong>
        </p>
        <button
          onClick={onDone}
          className="mt-5 w-full rounded-lg bg-emerald-600 px-4 py-3 text-sm font-bold text-white hover:bg-emerald-700"
        >
          Done
        </button>
      </div>
    </main>
  )
}


function BankRow({ label, value }) {
  return (
    <div className="flex items-center justify-between py-2.5">
      <span className="text-sm text-gray-500">{label}</span>
      <span className="text-sm font-semibold text-gray-900">{value}</span>
    </div>
  )
}
