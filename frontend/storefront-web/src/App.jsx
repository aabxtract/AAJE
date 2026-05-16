import { Route, Routes, Navigate } from 'react-router-dom'
import { useEffect, useState } from 'react'
import Landing from './pages/Landing'
import Pricing from './pages/Pricing'
import FAQs from './pages/FAQs'
import Contact from './pages/Contact'
import Signup from './pages/Signup'
import Login from './pages/Login'
import Onboarding from './pages/Onboarding'
import ConfirmBuild from './pages/ConfirmBuild'
import Publish from './pages/Publish'
import Dashboard from './pages/admin/Dashboard.jsx'
import Inventory from './pages/admin/Inventory.jsx'
import Orders from './pages/admin/Orders.jsx'
import Products from './pages/admin/Products.jsx'
import StoreSetup from './pages/admin/StoreSetup.jsx'
import Campaigns from './pages/admin/Campaigns.jsx'
import BizPrint from './pages/admin/BizPrint.jsx'
import StorePage from './pages/store/[slug].jsx'
import Checkout from './pages/checkout/index.jsx'
import PaymentSuccess from './pages/payment-success/index.jsx'

function ProtectedRoute({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const stored = localStorage.getItem('aaje_user')
    const token = localStorage.getItem('auth_token')
    if (stored && token) {
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
    return <Navigate to="/" replace />
  }

  return children
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/pricing" element={<Pricing />} />
      <Route path="/faqs" element={<FAQs />} />
      <Route path="/faq" element={<Navigate to="/faqs" replace />} />
      <Route path="/contact" element={<Contact />} />
      <Route path="/contact-us" element={<Navigate to="/contact" replace />} />

      {/* Auth */}
      <Route path="/signup" element={<Signup />} />
      <Route path="/login" element={<Login />} />

      {/* Onboarding flow */}
      <Route path="/onboarding" element={<ProtectedRoute><Onboarding /></ProtectedRoute>} />
      <Route path="/confirm" element={<ProtectedRoute><ConfirmBuild /></ProtectedRoute>} />
      <Route path="/publish" element={<ProtectedRoute><Publish /></ProtectedRoute>} />

      {/* Dashboard */}
      <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
      <Route path="/admin/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
      <Route path="/admin/products" element={<ProtectedRoute><Products /></ProtectedRoute>} />
      <Route path="/admin/inventory" element={<ProtectedRoute><Inventory /></ProtectedRoute>} />
      <Route path="/admin/orders" element={<ProtectedRoute><Orders /></ProtectedRoute>} />
      <Route path="/admin/store-setup" element={<ProtectedRoute><StoreSetup /></ProtectedRoute>} />
      <Route path="/admin/campaigns" element={<ProtectedRoute><Campaigns /></ProtectedRoute>} />
      <Route path="/admin/bizprint" element={<ProtectedRoute><BizPrint /></ProtectedRoute>} />

      {/* Public storefront + checkout */}
      <Route path="/store/:slug" element={<StorePage />} />
      <Route path="/checkout" element={<Checkout />} />
      <Route path="/payment-success" element={<PaymentSuccess />} />

      {/* Default redirect */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
