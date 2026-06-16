import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_URL || ''

const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// --- Shape adapters --------------------------------------------------------
// The new layer-per-concern backend (routes/store.py, routes/orders.py,
// routes/products.py) uses different field names than the legacy
// /api/storefront/* responses the React components were built against.
// We adapt at the boundary so call sites don't change.

export function adaptStore(raw, fallbackUserId) {
  if (!raw) return raw
  const theme = raw.theme_config || {}
  const products = Array.isArray(raw.products)
    ? raw.products.map(adaptProduct)
    : []
  return {
    ...raw,
    id: raw.id,
    user_id: raw.user_id || fallbackUserId,
    store_name: raw.store_name,
    slug: raw.store_slug || raw.slug,
    description: raw.store_description || raw.description || '',
    tagline: theme.hero_text || raw.tagline || '',
    contact_whatsapp: raw.whatsapp_number || raw.contact_whatsapp || '',
    template: theme.template || raw.template || 'fashion',
    theme: theme.theme || raw.theme || 'default',
    theme_config: theme,
    config_json: {
      categories: theme.categories || raw.categories || [],
      products: theme.products || [],
      tagline: theme.hero_text,
      template: theme.template,
      theme: theme.theme,
      description: raw.store_description,
    },
    logo_url: raw.logo_url || null,
    banner_url: raw.banner_url || null,
    is_active: raw.is_active !== false,
    is_published: !!raw.is_published,
    public_url: raw.public_url || `/store/${raw.store_slug || raw.slug}`,
    payment_account: raw.payment_account || { ready: false },
    products,
  }
}

function adaptProduct(raw) {
  if (!raw) return raw
  return {
    ...raw,
    id: raw.id,
    name: raw.name,
    description: raw.description || '',
    price: Number(raw.price || 0),
    category: raw.category || null,
    image_url: raw.image_url || null,
    stock_quantity: raw.stock_count ?? raw.stock_quantity ?? null,
    stock_count: raw.stock_count ?? raw.stock_quantity ?? null,
    low_stock_threshold: raw.low_stock_threshold ?? 0,
    is_available: raw.is_available !== false,
    is_active: raw.is_available !== false,
  }
}

function adaptOrder(raw) {
  if (!raw) return raw
  return {
    ...raw,
    id: raw.id,
    order_ref: raw.order_ref,
    customer_name: raw.customer_name,
    customer_phone: raw.customer_whatsapp || raw.customer_phone || '',
    customer_whatsapp: raw.customer_whatsapp || raw.customer_phone || '',
    customer_email: raw.customer_email,
    total_amount: Number(raw.total_amount || 0),
    status: raw.status,
    // OrderTable + Dashboard still read `order_status` - keep both in sync.
    order_status: raw.status,
    payment_status: raw.payment_status,
    payment_link: raw.payment_link,
    items: Array.isArray(raw.items)
      ? raw.items.map((item) => ({
          ...item,
          total_price: Number(item.subtotal ?? item.total_price ?? 0),
          unit_price: Number(item.unit_price ?? 0),
        }))
      : [],
    created_at: raw.created_at,
  }
}

function currentUserId() {
  const u = JSON.parse(localStorage.getItem('aaje_user') || '{}')
  return u.id || null
}

// --- Auth -----------------------------------------------------------------
export const signup = (data) => api.post('/auth/signup', data)
export const login = (data) => api.post('/auth/login', data)
export const whatsappLogin = (data) => api.post('/auth/whatsapp-login', data)
export const connectWhatsapp = (data) => api.post('/auth/connect-whatsapp', data)
// Verify the 6-digit OTP that was sent to the trader's WhatsApp.
// Backend: POST /auth/verify-whatsapp { whatsapp_no, otp } -> updated UserResponse.
export const verifyWhatsappConnection = ({ whatsapp_no, otp }) =>
  api.post('/auth/verify-whatsapp', { whatsapp_no, otp })
export const updateUser = (data) => api.post('/auth/update-me', data)

// LLM-driven onboarding (one turn at a time).
export const onboardingTurn = (history) => api.post('/onboarding/turn', { history })
export const fetchTemplates = () => api.get('/templates')
export const fetchTemplate = (id) => api.get(`/templates/${id}`)

// MVP payout account (manual transfer until Monnify + CAC re-enables).
// Reuses users.verified_bank_* columns; storefront PaymentAccount reads them.
export const getPayoutAccount = () => api.get('/auth/me/payout-account')
export const setPayoutAccount = (data) => api.patch('/auth/me/payout-account', {
  account_number: data.verified_bank_account || data.account_number,
  account_name: data.full_name || data.account_name,
  bank_name: data.verified_bank_name || data.bank_name,
  bank_code: data.verified_bank_code || data.bank_code || null,
})

// --- AI store generation (legacy passthrough - unaffected by new layer) ---
export const generateStore = (description) =>
  api.post('/api/storefront/ai/generate-store', { description })

// --- Store CRUD -----------------------------------------------------------
// Legacy callers pass a full payload; the new backend accepts only
// `business_description` and AI-generates the rest. Map the legacy shape.
export const createStore = async (data) => {
  const description =
    data.business_description || data.description || data.store_name || ''
  const res = await api.post('/store/setup', { business_description: description })
  return { ...res, data: adaptStore(res.data, data.user_id || currentUserId()) }
}

export const getStoreBySlug = async (slug) => {
  const res = await api.get(`/store/${encodeURIComponent(slug)}`)
  return { ...res, data: adaptStore(res.data) }
}

// Auth-scoped - returns at most one store for the current user (the
// dashboard endpoint already enforces this). useOwnerStore expects an array.
export const getStoresByUser = async (_userId) => {
  try {
    const res = await api.get('/store/me/dashboard')
    const store = adaptStore(res.data?.store, currentUserId())
    return { ...res, data: store ? [store] : [] }
  } catch (err) {
    if (err.response?.status === 404) return { data: [] }
    throw err
  }
}

export const updateStore = async (_storeId, data) => {
  const payload = {}
  if (data.store_name !== undefined) payload.store_name = data.store_name
  if (data.description !== undefined) payload.store_description = data.description
  if (data.contact_whatsapp !== undefined) payload.whatsapp_number = data.contact_whatsapp
  if (data.theme_config || data.template || data.theme || data.tagline) {
    payload.theme_config = {
      ...(data.theme_config || {}),
      ...(data.template ? { template: data.template } : {}),
      ...(data.theme ? { theme: data.theme } : {}),
      ...(data.tagline ? { hero_text: data.tagline } : {}),
    }
  }
  const res = await api.patch('/store/me', payload)
  return { ...res, data: adaptStore(res.data, currentUserId()) }
}

export const publishStore = async () => {
  const res = await api.post('/store/me/publish')
  return { ...res, data: adaptStore(res.data, currentUserId()) }
}

// --- Products -------------------------------------------------------------
// New endpoints are auth-scoped - backend infers the store from the JWT.
export const createProduct = async (data) => {
  const payload = {
    name: data.name,
    price: Number(data.price || 0),
    description: data.description || null,
    category: data.category || null,
    image_url: data.image_url || null,
    stock_count: data.stock_count ?? data.stock_quantity ?? null,
  }
  const res = await api.post('/products', payload)
  return { ...res, data: adaptProduct(res.data) }
}

export const getProductsByStore = async (storeIdOrSlug) => {
  // If we have a slug, the public store endpoint returns embedded products
  // (works without auth). Otherwise hit the auth-scoped list.
  if (typeof storeIdOrSlug === 'string' && /[a-z]/i.test(storeIdOrSlug) && !/-{4,}/.test(storeIdOrSlug)) {
    try {
      const res = await api.get(`/store/${encodeURIComponent(storeIdOrSlug)}`)
      const products = (res.data?.products || []).map(adaptProduct)
      return { ...res, data: products }
    } catch (err) {
      if (err.response?.status !== 404) throw err
    }
  }
  const res = await api.get('/products')
  return { ...res, data: (res.data || []).map(adaptProduct) }
}

export const updateProduct = async (productId, data) => {
  const payload = {}
  if (data.name !== undefined) payload.name = data.name
  if (data.description !== undefined) payload.description = data.description
  if (data.price !== undefined) payload.price = Number(data.price)
  if (data.category !== undefined) payload.category = data.category
  if (data.image_url !== undefined) payload.image_url = data.image_url
  if (data.stock_count !== undefined || data.stock_quantity !== undefined) {
    payload.stock_count = data.stock_count ?? data.stock_quantity
  }
  if (data.is_available !== undefined || data.is_active !== undefined) {
    payload.is_available = data.is_available ?? data.is_active
  }
  const res = await api.patch(`/products/${productId}`, payload)
  return { ...res, data: adaptProduct(res.data) }
}

export const deleteProduct = (productId) => api.delete(`/products/${productId}`)

export const generateProductDescription = (payload) =>
  api.post('/api/storefront/ai/generate-product-description', payload)

// --- Orders ---------------------------------------------------------------
// New POST /orders requires {store_slug, items:[{product_id, quantity}]}
// and ignores client-supplied pricing (server computes from product price).
export const createOrder = async (data) => {
  const stored = JSON.parse(localStorage.getItem('aaje_store') || '{}')
  const storeSlug = data.store_slug || stored.slug || stored.store_slug
  if (!storeSlug) throw new Error('Missing store_slug for order creation')
  const items = Array.isArray(data.items) ? data.items : []
  const payload = {
    store_slug: storeSlug,
    customer_name: data.customer_name,
    customer_whatsapp: data.customer_whatsapp || data.customer_phone,
    customer_email: data.customer_email || undefined,
    items: items.map((item) => ({
      product_id: item.product_id,
      quantity: Number(item.quantity || 1),
    })),
    delivery_address: data.delivery_address || undefined,
    notes: data.notes || undefined,
  }
  const res = await api.post('/orders', payload)
  return { ...res, data: adaptOrder(res.data) }
}

// Auth-scoped. storeId is no longer needed - kept for signature compatibility.
export const getOrdersByStore = async (_storeId, opts = {}) => {
  const params = {}
  if (opts.status) params.status = opts.status
  if (opts.limit) params.limit = opts.limit
  if (opts.offset) params.offset = opts.offset
  const res = await api.get('/orders', { params })
  const orders = (res.data?.orders || []).map(adaptOrder)
  return { ...res, data: orders }
}

// Legacy callers pass an order ID; the new endpoint keys on order_ref.
// If the caller already has an order_ref (AAJE-NNNN), use it directly;
// otherwise fall back to scanning the auth-scoped list.
export const getOrderDetail = async (orderIdOrRef) => {
  const looksLikeRef = typeof orderIdOrRef === 'string' && /^AAJE-/i.test(orderIdOrRef)
  if (looksLikeRef) {
    const res = await api.get(`/orders/${encodeURIComponent(orderIdOrRef)}`)
    return { ...res, data: adaptOrder(res.data) }
  }
  const list = await getOrdersByStore(null, { limit: 100 })
  const match = (list.data || []).find((o) => o.id === orderIdOrRef)
  return { data: match || null }
}

// Buyer signals they've transferred. Public endpoint, no auth.
// Idempotent on transfer_claimed (re-claim returns same order, no re-notify).
export const claimOrderTransfer = async (orderRef) => {
  const res = await api.patch(`/orders/${encodeURIComponent(orderRef)}/claim-transfer`)
  return { ...res, data: adaptOrder(res.data) }
}

export const updateOrderStatus = async (orderIdOrRef, payload) => {
  // Server-side status enum is the MVP set (transfer_claimed, confirmed, ...).
  // The legacy "simulate_payment" hack from the old backend is dropped here -
  // simulate-payment now means flipping status=confirmed.
  const status = payload?.simulate_payment ? 'confirmed' : payload?.status
  if (!status) throw new Error('updateOrderStatus: status required')

  let orderRef = orderIdOrRef
  if (!/^AAJE-/i.test(String(orderIdOrRef))) {
    const detail = await getOrderDetail(orderIdOrRef)
    orderRef = detail.data?.order_ref
    if (!orderRef) throw new Error(`Could not find order ${orderIdOrRef}`)
  }
  const res = await api.patch(
    `/orders/${encodeURIComponent(orderRef)}/status`,
    { status },
  )
  return { ...res, data: adaptOrder(res.data) }
}

// --- Inventory (legacy passthrough - separate endpoint) -------------------
export const getInventoryByStore = (storeId) =>
  api.get(`/api/storefront/inventory/${storeId}`)
export const adjustInventory = (data) =>
  api.post('/api/storefront/inventory/adjust', data)

// --- Intelligence (legacy passthrough) ------------------------------------
// MVP has no payment gateway - customers transfer direct to the trader's bank
// account (see claimOrderTransfer). Squad/Monnify return post-CAC.
export const getStoreIntelligence = (storeId) =>
  api.get(`/api/intelligence/store/${storeId}`)
export const emitStorefrontEvent = (data) =>
  api.post('/api/events/storefront', data)

export default api
