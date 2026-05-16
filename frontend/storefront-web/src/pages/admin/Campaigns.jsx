import { Eye, Plus, ArrowUpRight } from 'lucide-react'
import AdminLayout from '../../components/AdminLayout'
import { useOwnerStore } from '../../hooks/useStorefront'

export default function Campaigns() {
  const { store, user, loading } = useOwnerStore()

  return (
    <AdminLayout store={store} user={user}>
      <div className="mx-auto max-w-5xl space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-black text-gray-900">Marketing Campaigns</h1>
            <p className="text-sm text-gray-500">Track clicks, conversions, and ROI across all your marketing channels.</p>
          </div>
          <button className="inline-flex items-center gap-2 rounded-xl bg-emerald-600 px-4 py-2.5 text-sm font-bold text-white transition hover:bg-emerald-700">
            <Plus className="h-4 w-4" /> New Campaign
          </button>
        </div>

        <div className="grid gap-6 md:grid-cols-3">
          <div className="rounded-xl border border-gray-100 bg-white p-6 shadow-sm">
            <div className="mb-4 flex items-center gap-3 text-emerald-600">
              <Eye className="h-5 w-5" />
              <h3 className="font-bold text-gray-900">Total Visits</h3>
            </div>
            <p className="text-3xl font-black text-gray-900">0</p>
            <p className="mt-2 text-xs font-medium text-gray-500">From tracked links</p>
          </div>
          <div className="rounded-xl border border-gray-100 bg-white p-6 shadow-sm">
            <div className="mb-4 flex items-center gap-3 text-blue-600">
              <ArrowUpRight className="h-5 w-5" />
              <h3 className="font-bold text-gray-900">Conversions</h3>
            </div>
            <p className="text-3xl font-black text-gray-900">0</p>
            <p className="mt-2 text-xs font-medium text-gray-500">Purchases made</p>
          </div>
          <div className="rounded-xl border border-gray-100 bg-white p-6 shadow-sm">
            <div className="mb-4 flex items-center gap-3 text-purple-600">
              <h3 className="font-bold text-gray-900">Revenue Generated</h3>
            </div>
            <p className="text-3xl font-black text-gray-900">₦0.00</p>
            <p className="mt-2 text-xs font-medium text-gray-500">Attributed to campaigns</p>
          </div>
        </div>

        <div className="flex min-h-[300px] items-center justify-center rounded-xl border border-dashed border-gray-300 bg-gray-50">
          <div className="text-center">
            <Eye className="mx-auto mb-3 h-8 w-8 text-gray-400" />
            <p className="text-sm font-bold text-gray-900">No campaigns yet</p>
            <p className="text-xs text-gray-500">Create a campaign to generate tracking links.</p>
          </div>
        </div>
      </div>
    </AdminLayout>
  )
}
