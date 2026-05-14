import { useEffect } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { Loader2 } from 'lucide-react'

export default function Checkout() {
  const location = useLocation()
  const navigate = useNavigate()

  useEffect(() => {
    const params = new URLSearchParams(location.search)
    const orderId = params.get('order_id')
    const reference = params.get('reference')
    const status = params.get('status')
    if (status === 'success' || status === 'paid') navigate(`/payment-success?order_id=${orderId || ''}&reference=${reference || ''}`)
    else navigate('/')
  }, [location.search, navigate])

  return <main className="flex min-h-screen items-center justify-center"><Loader2 className="h-8 w-8 animate-spin text-primary-600" /></main>
}
