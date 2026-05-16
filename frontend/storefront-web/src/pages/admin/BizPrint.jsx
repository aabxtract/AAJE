import { BarChart3, TrendingUp, Sparkles, AlertCircle } from 'lucide-react'
import AdminLayout from '../../components/AdminLayout'
import { useOwnerStore } from '../../hooks/useStorefront'

export default function BizPrint() {
  const { store, user, loading } = useOwnerStore()

  return (
    <AdminLayout store={store} user={user}>
      <div className="mx-auto max-w-5xl space-y-6">
        <div className="flex items-center justify-between border-b border-gray-200 pb-5">
          <div>
            <h1 className="flex items-center gap-2 text-2xl font-black text-gray-900">
              <BarChart3 className="h-6 w-6 text-emerald-600" />
              BizPrint Intelligence
            </h1>
            <p className="mt-1 text-sm text-gray-500">Your AI-generated business footprint and health assessment.</p>
          </div>
          <div className="flex items-center gap-2 rounded-full bg-emerald-50 px-3 py-1 text-xs font-bold text-emerald-700 border border-emerald-100">
            <Sparkles className="h-4 w-4" /> Auto-updating
          </div>
        </div>

        <div className="grid gap-6 lg:grid-cols-3">
          <div className="lg:col-span-2 space-y-6">
            <section className="rounded-2xl border border-gray-100 bg-white p-6 shadow-sm">
              <h2 className="mb-4 text-lg font-bold text-gray-900">Executive Summary</h2>
              <div className="rounded-xl bg-gray-50 p-4 text-sm leading-relaxed text-gray-600">
                BizPrint is analyzing your storefront operations. Your business footprint is currently forming based on customer interactions, product views, and sales velocity. Make your first few sales to unlock detailed AI summaries.
              </div>
            </section>
            
            <section className="rounded-2xl border border-gray-100 bg-white p-6 shadow-sm">
              <h2 className="mb-4 text-lg font-bold text-gray-900">Growth Opportunities</h2>
              <ul className="space-y-3">
                <li className="flex items-start gap-3 rounded-xl border border-blue-50 bg-blue-50/50 p-4">
                  <TrendingUp className="mt-0.5 h-5 w-5 text-blue-600 shrink-0" />
                  <div>
                    <p className="text-sm font-bold text-blue-900">Connect WhatsApp</p>
                    <p className="mt-1 text-xs text-blue-700">Ensure your WhatsApp is connected to capture abandoned cart data and provide instant support.</p>
                  </div>
                </li>
              </ul>
            </section>
          </div>

          <div className="space-y-6">
            <section className="rounded-2xl border border-gray-100 bg-[#0f172a] p-6 text-white shadow-lg">
              <h2 className="mb-4 text-sm font-bold uppercase tracking-widest text-emerald-400">Data Quality Score</h2>
              <div className="flex items-end gap-2">
                <span className="text-5xl font-black">Low</span>
              </div>
              <p className="mt-2 text-xs text-gray-400">Requires more transaction volume for a 'High' confidence rating.</p>
            </section>

            <section className="rounded-2xl border border-amber-100 bg-amber-50 p-6 shadow-sm">
              <h2 className="mb-4 flex items-center gap-2 text-sm font-bold text-amber-900">
                <AlertCircle className="h-4 w-4" /> Action Required
              </h2>
              <p className="text-xs leading-relaxed text-amber-800">
                To improve your BizPrint data quality, actively share your store link and add more products to inventory.
              </p>
            </section>
          </div>
        </div>
      </div>
    </AdminLayout>
  )
}
