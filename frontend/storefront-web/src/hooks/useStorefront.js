import { useCallback, useEffect, useMemo, useState } from 'react'
import * as api from '../lib/api'
import { getDemoUserId } from '../lib/utils'

export function useOwnerStore() {
  const [store, setStore] = useState(() => {
    try {
      const stored = JSON.parse(localStorage.getItem('aaje_store') || 'null')
      return stored ? api.adaptStore(stored, getDemoUserId()) : null
    } catch {
      return null
    }
  })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const refresh = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await api.getStoresByUser(getDemoUserId())
      const ownerStore = res.data?.[0] || null
      if (ownerStore) {
        setStore(ownerStore)
        localStorage.setItem('aaje_store', JSON.stringify(ownerStore))
      } else {
        setStore(null)
        localStorage.removeItem('aaje_store')
      }
    } catch (err) {
      const stored = (() => {
        try {
          const raw = JSON.parse(localStorage.getItem('aaje_store') || 'null')
          return raw ? api.adaptStore(raw, getDemoUserId()) : null
        } catch {
          return null
        }
      })()
      if (stored) {
        setStore(stored)
      }
      setError(err)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    refresh()
  }, [refresh])

  return { store, loading, error, refresh, setStore }
}

export function useProducts(storeId) {
  const [products, setProducts] = useState([])
  const [loading, setLoading] = useState(false)

  const refresh = useCallback(async () => {
    if (!storeId) return
    setLoading(true)
    try {
      const res = await api.getProductsByStore(storeId)
      setProducts(res.data || [])
    } finally {
      setLoading(false)
    }
  }, [storeId])

  useEffect(() => {
    refresh()
  }, [refresh])

  return { products, loading, refresh, setProducts }
}

export function useOrders(storeId) {
  const [orders, setOrders] = useState([])
  const [loading, setLoading] = useState(false)

  const refresh = useCallback(async () => {
    if (!storeId) return
    setLoading(true)
    try {
      const res = await api.getOrdersByStore(storeId)
      setOrders(res.data || [])
    } finally {
      setLoading(false)
    }
  }, [storeId])

  useEffect(() => {
    refresh()
  }, [refresh])

  return { orders, loading, refresh }
}

export function useInventory(storeId) {
  const [inventory, setInventory] = useState([])
  const [loading, setLoading] = useState(false)

  const refresh = useCallback(async () => {
    if (!storeId) return
    setLoading(true)
    try {
      const res = await api.getInventoryByStore(storeId)
      setInventory(res.data || [])
    } finally {
      setLoading(false)
    }
  }, [storeId])

  useEffect(() => {
    refresh()
  }, [refresh])

  return { inventory, loading, refresh }
}

export function useDashboard(storeId) {
  const { products, refresh: refreshProducts } = useProducts(storeId)
  const { orders, refresh: refreshOrders } = useOrders(storeId)
  const [intelligence, setIntelligence] = useState(null)

  useEffect(() => {
    if (!storeId) return
    api.getStoreIntelligence(storeId)
      .then((res) => setIntelligence(res.data))
      .catch(() => setIntelligence(null))
  }, [storeId])

  useEffect(() => {
    if (!storeId) return undefined
    const timer = window.setInterval(() => {
      refreshProducts()
      refreshOrders()
    }, 5000)
    return () => window.clearInterval(timer)
  }, [storeId, refreshProducts, refreshOrders])

  const stats = useMemo(() => {
    const today = new Date().toDateString()
    const paid = orders.filter((order) => order.payment_status === 'paid')
    const todaySales = paid
      .filter((order) => new Date(order.paid_at || order.updated_at || order.created_at).toDateString() === today)
      .reduce((sum, order) => sum + Number(order.total_amount || 0), 0)
    const lowStock = products.filter((p) => Number(p.stock_quantity) <= Number(p.low_stock_threshold || 0))

    return {
      todaySales,
      totalOrders: orders.length,
      pendingOrders: orders.filter((o) => o.order_status === 'pending').length,
      productsInStock: products.filter((p) => Number(p.stock_quantity) > 0).length,
      lowStockProducts: lowStock,
      recentOrders: orders.slice(0, 5),
      topProduct: paid[0]?.items?.[0]?.product_name || products[0]?.name || 'No sales yet',
    }
  }, [orders, products])

  const fallbackIntelligence = {
    summary: stats.lowStockProducts.length
      ? `${stats.lowStockProducts[0].name} is running low.`
      : 'Your storefront data will power AAJE business insights as orders come in.',
    top_product: stats.topProduct,
    low_stock: stats.lowStockProducts.map((p) => p.name),
    sales_trend: stats.todaySales > 0 ? 'up' : 'flat',
    recommendation: stats.lowStockProducts.length ? `Restock ${stats.lowStockProducts[0].name} soon.` : 'Add more products and share your store link.',
  }

  return {
    products,
    orders,
    stats,
    intelligence: intelligence || fallbackIntelligence,
    refresh: () => {
      refreshProducts()
      refreshOrders()
    },
  }
}
