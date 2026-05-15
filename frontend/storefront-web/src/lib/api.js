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

// Auth
export const signup = (data) => api.post('/auth/signup', data)
export const login = (data) => api.post('/auth/login', data)
export const connectWhatsapp = (data) => api.post('/auth/connect-whatsapp', data)
export const updateUser = (data) => api.post('/auth/update-me', data)

// AI Store Generation
export const generateStore = (description) => api.post('/api/storefront/ai/generate-store', { description })

// Store CRUD
export const createStore = (data) => api.post('/api/storefront/stores', data)
export const getStoreBySlug = (slug) => api.get(`/api/storefront/stores/${slug}`)
export const getStoresByUser = (userId) => api.get(`/api/storefront/stores/by-user/${userId}`)
export const updateStore = (storeId, data) => api.put(`/api/storefront/stores/${storeId}`, data)

// Products
export const createProduct = (data) => api.post('/api/storefront/products', data)
export const getProductsByStore = (storeIdOrSlug) => api.get(`/api/storefront/products/${storeIdOrSlug}`)
export const updateProduct = (productId, data) => api.put(`/api/storefront/products/${productId}`, data)
export const deleteProduct = (productId) => api.delete(`/api/storefront/products/${productId}`)
export const generateProductDescription = (payload) => api.post('/api/storefront/ai/generate-product-description', payload)

// Orders
export const createOrder = (data) => api.post('/api/storefront/orders', data)
export const getOrdersByStore = (storeId) => api.get(`/api/storefront/orders/${storeId}`)
export const getOrderDetail = (orderId) => api.get(`/api/storefront/order/${orderId}`)
export const updateOrderStatus = (orderId, payload) => api.put(`/api/storefront/orders/${orderId}/status`, payload)

// Inventory
export const getInventoryByStore = (storeId) => api.get(`/api/storefront/inventory/${storeId}`)
export const adjustInventory = (data) => api.post('/api/storefront/inventory/adjust', data)

// Payments & Intelligence
export const initiatePayment = (data) => api.post('/api/payments/initiate', data)
export const getStoreIntelligence = (storeId) => api.get(`/api/intelligence/store/${storeId}`)
export const emitStorefrontEvent = (data) => api.post('/api/events/storefront', data)

export default api
