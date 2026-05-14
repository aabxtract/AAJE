import { Route, Routes } from 'react-router-dom'
import StorePage from './pages/store/[slug].jsx'
import Dashboard from './pages/admin/Dashboard.jsx'
import Inventory from './pages/admin/Inventory.jsx'
import Orders from './pages/admin/Orders.jsx'
import Products from './pages/admin/Products.jsx'
import StoreSetup from './pages/admin/StoreSetup.jsx'
import Checkout from './pages/checkout/index.jsx'
import PaymentSuccess from './pages/payment-success/index.jsx'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<StoreSetup />} />
      <Route path="/store/:slug" element={<StorePage />} />
      <Route path="/checkout" element={<Checkout />} />
      <Route path="/payment-success" element={<PaymentSuccess />} />
      <Route path="/admin/dashboard" element={<Dashboard />} />
      <Route path="/admin/store-setup" element={<StoreSetup />} />
      <Route path="/admin/products" element={<Products />} />
      <Route path="/admin/orders" element={<Orders />} />
      <Route path="/admin/inventory" element={<Inventory />} />
    </Routes>
  )
}
