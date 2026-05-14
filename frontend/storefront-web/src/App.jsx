import { Route, Routes, Navigate } from 'react-router-dom'
import { useEffect, useState } from 'react'
import Landing from './pages/Landing'
import Signup from './pages/Signup'
import Onboarding from './pages/Onboarding'
import StorePreview from './pages/StorePreview'
import AccountConnect from './pages/AccountConnect'
import Pricing from './pages/Pricing'
import Dashboard from './pages/admin/Dashboard.jsx'
import Inventory from './pages/admin/Inventory.jsx'
import Orders from './pages/admin/Orders.jsx'
import Products from './pages/admin/Products.jsx'
import StorePage from './pages/store/[slug].jsx'

// Simple auth check (for demo)
function ProtectedRoute({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const stored = localStorage.getItem('aaje_user')
    if (stored) {
      setUser(JSON.parse(stored))
    }
    setLoading(false)
  }, [])

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-gray-200 border-t-primary-600"></div>
      </div>
    )
  }

  if (!user) {
    return <Navigate to="/signup" replace />
  }

  return children
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />

      {/* Onboarding flow */}
      <Route path="/signup" element={<Signup />} />
      <Route path="/onboarding" element={<ProtectedRoute><Onboarding /></ProtectedRoute>} />
      <Route path="/store-preview" element={<ProtectedRoute><StorePreview /></ProtectedRoute>} />
      <Route path="/account-connect" element={<ProtectedRoute><AccountConnect /></ProtectedRoute>} />
      <Route path="/pricing" element={<ProtectedRoute><Pricing /></ProtectedRoute>} />

      {/* Admin dashboard */}
      <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
      <Route path="/admin/products" element={<ProtectedRoute><Products /></ProtectedRoute>} />
      <Route path="/admin/orders" element={<ProtectedRoute><Orders /></ProtectedRoute>} />
      <Route path="/admin/inventory" element={<ProtectedRoute><Inventory /></ProtectedRoute>} />

      {/* Public storefront */}
      <Route path="/store/:slug" element={<StorePage />} />

      {/* Default redirect */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
