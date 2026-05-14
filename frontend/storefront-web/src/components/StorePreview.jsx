import { Check, Copy, ExternalLink } from 'lucide-react'
import { useState } from 'react'
import { Link } from 'react-router-dom'

export default function StorePreview({ store }) {
  const [copied, setCopied] = useState(false)
  const url = `${window.location.origin}/store/${store.slug}`

  async function copy() {
    await navigator.clipboard.writeText(url)
    setCopied(true)
    setTimeout(() => setCopied(false), 1600)
  }

  return (
    <div className="card p-5">
      <div className="flex items-center justify-between">
        <h3 className="font-bold">Store Link</h3>
        <span className="rounded-full bg-emerald-100 px-2 py-1 text-xs font-semibold text-emerald-800">Live</span>
      </div>
      <div className="mt-4 flex items-center gap-2 rounded-md border bg-gray-50 p-2">
        <p className="flex-1 truncate text-sm text-gray-600">{url}</p>
        <button className="rounded p-2 hover:bg-gray-200" onClick={copy}>{copied ? <Check className="h-4 w-4 text-emerald-600" /> : <Copy className="h-4 w-4" />}</button>
        <Link className="rounded p-2 hover:bg-gray-200" to={`/store/${store.slug}`} target="_blank"><ExternalLink className="h-4 w-4" /></Link>
      </div>
      <p className="mt-3 text-xs text-gray-500">Share this link from WhatsApp or social channels to receive customer orders.</p>
    </div>
  )
}
