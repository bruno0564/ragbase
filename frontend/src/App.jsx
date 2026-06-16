import { useState } from 'react'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export default function App() {
  const [question, setQuestion] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [sources, setSources] = useState([])
  const [tab, setTab] = useState('query')
  const [error, setError] = useState(null)

  async function handleQuery(e) {
    e.preventDefault()
    if (!question.trim()) return
    setLoading(true)
    setResult(null)
    setError(null)
    try {
      const r = await fetch(`${API}/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question }),
      })
      if (!r.ok) throw new Error(`Server error (${r.status})`)
      setResult(await r.json())
    } catch (err) {
      setError(err.message || 'Could not reach the server')
    } finally {
      setLoading(false)
    }
  }

  async function handleUpload(e) {
    const file = e.target.files[0]
    if (!file) return
    setUploading(true)
    setError(null)
    const form = new FormData()
    form.append('file', file)
    try {
      const r = await fetch(`${API}/ingest/pdf`, { method: 'POST', body: form })
      if (!r.ok) throw new Error(`Upload failed (${r.status})`)
      await r.json()
      await loadSources()
    } catch (err) {
      setError(err.message || 'Upload failed')
    } finally {
      setUploading(false)
      e.target.value = ''
    }
  }

  async function loadSources() {
    try {
      const r = await fetch(`${API}/sources`)
      if (!r.ok) throw new Error(`Could not load documents (${r.status})`)
      const data = await r.json()
      setSources(data.sources)
    } catch (err) {
      setError(err.message || 'Could not load documents')
    }
  }

  async function handleDelete(source) {
    if (!confirm(`Remove "${source}" from the index?`)) return
    setError(null)
    try {
      const r = await fetch(`${API}/sources/${encodeURIComponent(source)}`, { method: 'DELETE' })
      if (!r.ok) throw new Error(`Delete failed (${r.status})`)
      await loadSources()
    } catch (err) {
      setError(err.message || 'Delete failed')
    }
  }

  return (
    <div style={{ maxWidth: 720, margin: '0 auto', padding: '2rem 1rem', fontFamily: 'system-ui, sans-serif' }}>
      <h1 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: '1.5rem' }}>ragbase</h1>

      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.5rem' }}>
        {['query', 'upload'].map(t => (
          <button key={t} onClick={() => { setTab(t); setError(null); if (t === 'upload') loadSources() }}
            style={{ padding: '0.4rem 1rem', background: tab === t ? '#818cf8' : '#eee', color: tab === t ? '#fff' : '#333', border: 'none', borderRadius: 6, cursor: 'pointer', fontWeight: 600 }}>
            {t === 'query' ? 'Ask' : 'Upload PDF'}
          </button>
        ))}
      </div>

      {error && (
        <div style={{ background: '#fee2e2', border: '1px solid #fca5a5', color: '#991b1b', borderRadius: 6, padding: '0.6rem 0.85rem', marginBottom: '1.25rem', fontSize: '0.85rem' }}>
          {error}
        </div>
      )}

      {tab === 'query' && (
        <>
          <form onSubmit={handleQuery} style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.5rem' }}>
            <input
              value={question}
              onChange={e => setQuestion(e.target.value)}
              placeholder="Ask something about your documents..."
              style={{ flex: 1, padding: '0.6rem 0.75rem', border: '1px solid #ddd', borderRadius: 6, fontSize: '0.9rem' }}
            />
            <button type="submit" disabled={loading}
              style={{ padding: '0.6rem 1.2rem', background: '#818cf8', color: '#fff', border: 'none', borderRadius: 6, cursor: 'pointer', fontWeight: 600 }}>
              {loading ? '...' : 'Ask'}
            </button>
          </form>

          {result && result.context?.length === 0 && (
            <p style={{ color: '#888', fontSize: '0.9rem' }}>No documents indexed yet — upload a PDF first.</p>
          )}

          {result && result.answer && (
            <div style={{ background: '#eef2ff', border: '1px solid #c7d2fe', borderRadius: 8, padding: '1rem 1.25rem', marginBottom: '1.5rem' }}>
              <p style={{ fontSize: '0.75rem', color: '#6366f1', fontWeight: 700, letterSpacing: '0.05em', marginBottom: '0.5rem' }}>ANSWER</p>
              <p style={{ fontSize: '0.95rem', lineHeight: 1.7, whiteSpace: 'pre-wrap' }}>{result.answer}</p>
            </div>
          )}

          {result && result.context?.length > 0 && (
            <div>
              <p style={{ fontWeight: 600, marginBottom: '1rem' }}>
                {result.answer ? 'Sources' : 'Relevant passages'}
                {!result.answer && <span style={{ fontWeight: 400, color: '#888', fontSize: '0.8rem' }}> (start Ollama for generated answers)</span>}
              </p>
              {result.context.map((c, i) => (
                <div key={i} style={{ background: '#f8f8f8', border: '1px solid #eee', borderRadius: 8, padding: '1rem', marginBottom: '0.75rem' }}>
                  <p style={{ fontSize: '0.75rem', color: '#888', marginBottom: '0.4rem' }}>
                    {c.source} · chunk {c.chunk} · score {c.score}
                  </p>
                  <p style={{ fontSize: '0.875rem', lineHeight: 1.6 }}>{c.text}</p>
                </div>
              ))}
            </div>
          )}
        </>
      )}

      {tab === 'upload' && (
        <div>
          <label style={{ display: 'inline-block', padding: '0.6rem 1.2rem', background: '#818cf8', color: '#fff', borderRadius: 6, cursor: 'pointer', fontWeight: 600 }}>
            {uploading ? 'Uploading...' : 'Choose PDF'}
            <input type="file" accept=".pdf" onChange={handleUpload} style={{ display: 'none' }} disabled={uploading} />
          </label>
          {sources.length > 0 && (
            <div style={{ marginTop: '1.5rem' }}>
              <p style={{ fontWeight: 600, marginBottom: '0.5rem' }}>Indexed documents:</p>
              {sources.map(s => (
                <div key={s} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.875rem', color: '#555', padding: '0.3rem 0' }}>
                  <span>• {s}</span>
                  <button onClick={() => handleDelete(s)}
                    style={{ background: 'none', border: 'none', color: '#ef4444', cursor: 'pointer', fontSize: '0.8rem', fontWeight: 600 }}>
                    Remove
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
