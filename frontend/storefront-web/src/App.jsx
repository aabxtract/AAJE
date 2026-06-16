import { Route, Routes, Navigate, useParams } from 'react-router-dom'
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
import { detectStoreSlug } from './lib/subdomain'

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
  // On a subdomain, render ONLY the storefront for that slug. No router needed
  // because there's only one path on a buyer subdomain.
  const subdomain = detectStoreSlug()
  if (subdomain) {
    return <StorePage slug={subdomain} />
  }

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

      {/* Legacy /store/:slug - redirect to subdomain */}
      <Route path="/store/:slug" element={<LegacyStoreRedirect />} />

      {/* Default redirect */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}


function LegacyStoreRedirect() {
  const { slug } = useParams()
  useEffect(() => {
    if (!slug) return
    const host = window.location.hostname
    let target
    if (host.endsWith('aaje.store')) {
      target = `${window.location.protocol}//${slug}.aaje.store${window.location.search}`
    } else if (host.includes('localtest.me') || host === 'localhost') {
      const port = window.location.port ? `:${window.location.port}` : ''
      target = `${window.location.protocol}//${slug}.localtest.me${port}${window.location.search}`
    } else {
      // Fallback: just render in place (dev/preview hostnames we don't know about)
      return
    }
    window.location.replace(target)
  }, [slug])

  return (
    <main className="flex min-h-screen items-center justify-center bg-gray-50 text-sm text-gray-500">
      Redirecting to {slug}.aaje.store...
    </main>
  )
}
