import { useState } from 'react'
import { Check, Loader2, RefreshCw, Sparkles, Wand2 } from 'lucide-react'
import { generateStore } from '../lib/api'

const examples = [
  'I sell thrift clothes for students and I want a clean affordable store.',
  'I sell foodstuff and household provisions for busy families.',
  'I sell phone accessories for young professionals.',
  'I make small chops and snacks for office events.',
]

export default function AIStoreBuilder({ onUseStore }) {
  const [prompt, setPrompt] = useState('')
  const [result, setResult] = useState(null)
  const [draft, setDraft] = useState(null)
  const [editing, setEditing] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function handleGenerate() {
    if (!prompt.trim()) return
    setLoading(true)
    setError('')
    try {
      const res = await generateStore(prompt)
      setResult(res.data)
      setDraft(res.data)
      setEditing(false)
    } catch (err) {
      setError(err.response?.data?.detail || 'AI store generation failed. Try again!')
    } finally {
      setLoading(false)
    }
  }

  function patchTheme(key, value) {
    setDraft((current) => ({ ...current, theme: { ...(current.theme || {}), [key]: value } }))
  }

  if (loading) {
    return (
      <div className="card p-10 text-center">
        <Loader2 className="mx-auto h-8 w-8 animate-spin text-primary-600" />
        <p className="mt-3 text-sm text-gray-500">Building a storefront concept...</p>
      </div>
    )
  }

  if (!result) {
    return (
      <div className="card p-6">
        <div className="text-center">
          <Sparkles className="mx-auto h-10 w-10 text-primary-600" />
          <h1 className="mt-3 text-2xl font-bold">AI Store Builder</h1>
          <p className="mt-1 text-sm text-gray-500">Describe the business. AAJE will shape a starter store.</p>
        </div>
        <textarea
          value={prompt}
          onChange={(event) => setPrompt(event.target.value)}
          className="input-field mt-5 min-h-32"
          placeholder="I sell thrift clothes for students and I want a clean affordable store..."
        />
        {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
        <button className="btn-primary mt-4 w-full" onClick={handleGenerate} disabled={!prompt.trim()}>
          <Wand2 className="mr-2 h-4 w-4" />
          Generate Store
        </button>
        <div className="mt-4 grid gap-2 sm:grid-cols-2">
          {examples.map((example) => (
            <button key={example} className="rounded-md bg-gray-50 p-3 text-left text-xs text-gray-600 hover:bg-gray-100" onClick={() => setPrompt(example)}>
              {example}
            </button>
          ))}
        </div>
      </div>
    )
  }

  const shown = editing ? draft : result

  return (
    <div className="card p-6">
      <div className="flex items-center justify-between gap-3">
        <h2 className="text-lg font-bold">Generated Store</h2>
        <button className="btn-secondary px-3 py-2" onClick={handleGenerate}>
          <RefreshCw className="mr-2 h-4 w-4" />
          Regenerate
        </button>
      </div>

      {editing ? (
        <div className="mt-5 grid gap-4">
          <input className="input-field" value={draft.store_name || ''} onChange={(e) => setDraft({ ...draft, store_name: e.target.value })} />
          <input className="input-field" value={draft.tagline || ''} onChange={(e) => setDraft({ ...draft, tagline: e.target.value })} />
          <textarea className="input-field min-h-24" value={draft.description || ''} onChange={(e) => setDraft({ ...draft, description: e.target.value })} />
          <input
            className="input-field"
            value={(draft.categories || []).join(', ')}
            onChange={(e) => setDraft({ ...draft, categories: e.target.value.split(',').map((value) => value.trim()).filter(Boolean) })}
          />
          <div className="flex items-center gap-3">
            <input type="color" value={draft.theme?.primary_color || '#111827'} onChange={(e) => patchTheme('primary_color', e.target.value)} className="h-10 w-16" />
            <select className="input-field max-w-48" value={draft.theme?.style || 'clean'} onChange={(e) => patchTheme('style', e.target.value)}>
              <option value="clean">Clean</option>
              <option value="bold">Bold</option>
              <option value="local">Local</option>
              <option value="premium">Premium</option>
              <option value="playful">Playful</option>
            </select>
          </div>
        </div>
      ) : (
        <div className="mt-5 rounded-lg border border-gray-200 p-5">
          <h3 className="text-2xl font-bold">{shown.store_name}</h3>
          <p className="mt-1 font-medium text-primary-700">{shown.tagline}</p>
          <p className="mt-3 text-sm text-gray-600">{shown.description}</p>
          <div className="mt-4 flex flex-wrap gap-2">
            {(shown.categories || []).map((category) => (
              <span key={category} className="rounded-full bg-gray-100 px-3 py-1 text-xs font-medium text-gray-700">{category}</span>
            ))}
          </div>
          <div className="mt-4 flex items-center gap-2 text-sm text-gray-500">
            <span className="h-6 w-6 rounded-full border" style={{ backgroundColor: shown.theme?.primary_color || '#111827' }} />
            {shown.theme?.style || 'clean'} / {shown.theme?.layout || 'simple_grid'}
          </div>
        </div>
      )}

      <div className="mt-5 flex gap-3">
        <button className="btn-primary flex-1" onClick={() => onUseStore(editing ? draft : result)}>
          <Check className="mr-2 h-4 w-4" />
          Use This
        </button>
        <button className="btn-secondary" onClick={() => setEditing((value) => !value)}>
          {editing ? 'Done' : 'Edit'}
        </button>
      </div>
    </div>
  )
}
