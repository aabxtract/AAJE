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

export const generateStore = (prompt) => api.post('/api/storefront/ai/generate-store', { prompt })
export const generateProductDescription = (payload) => api.post('/api/storefront/ai/generate-product-description', payload)

export const createStore = (data) => api.post('/api/storefront/stores', data)
export const getStoreBySlug = (slug) => api.get(`/api/storefront/stores/${slug}`)
export const getStoresByUser = (userId) => api.get(`/api/storefront/stores/by-user/${userId}`)
export const updateStore = (storeId, data) => api.put(`/api/storefront/stores/${storeId}`, data)

export const createProduct = (data) => api.post('/api/storefront/products', data)
export const getProductsByStore = (storeIdOrSlug) => api.get(`/api/storefront/products/${storeIdOrSlug}`)
export const updateProduct = (productId, data) => api.put(`/api/storefront/products/${productId}`, data)
export const deleteProduct = (productId) => api.delete(`/api/storefront/products/${productId}`)

export const createOrder = (data) => api.post('/api/storefront/orders', data)
export const getOrdersByStore = (storeId) => api.get(`/api/storefront/orders/${storeId}`)
export const getOrderDetail = (orderId) => api.get(`/api/storefront/orders/detail/${orderId}`)
export const updateOrderStatus = (orderId, payload) => api.put(`/api/storefront/orders/${orderId}/status`, payload)

export const getInventoryByStore = (storeId) => api.get(`/api/storefront/inventory/${storeId}`)
export const adjustInventory = (data) => api.post('/api/storefront/inventory/adjust', data)

export const initiatePayment = (data) => api.post('/api/payments/initiate', data)
export const getStoreIntelligence = (storeId) => api.get(`/api/intelligence/store/${storeId}`)
export const emitStorefrontEvent = (data) => api.post('/api/events/storefront', data)

export default api
