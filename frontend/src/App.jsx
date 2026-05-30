import { useState } from 'react'

const API = 'http://localhost:8000'

export default function App() {
  const [question, setQuestion] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [sources, setSources] = useState([])
  const [tab, setTab] = useState('query')

  async function handleQuery(e) {
    e.preventDefault()
    if (!question.trim()) return
    setLoading(true)
    setResult(null)
    try {
      const r = await fetch(`${API}/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question }),
      })
      setResult(await r.json())
    } finally {
      setLoading(false)
    }
  }

  async function handleUpload(e) {
    const file = e.target.files[0]
    if (!file) return
    setUploading(true)
    const form = new FormData()
    form.append('file', file)
    try {
      const r = await fetch(`${API}/ingest/pdf`, { method: 'POST', body: form })
      const data = await r.json()
      alert(`Indexed ${data.chunks_indexed} chunks from ${data.filename}`)
      loadSources()
    } finally {
      setUploading(false)
    }
  }

  async function loadSources() {
    const r = await fetch(`${API}/sources`)
    const data = await r.json()
    setSources(data.sources)
  }

  return (
    <div style={{ maxWidth: 720, margin: '0 auto', padding: '2rem 1rem', fontFamily: 'system-ui, sans-serif' }}>
      <h1 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: '1.5rem' }}>ragbase</h1>

      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.5rem' }}>
        {['query', 'upload'].map(t => (
          <button key={t} onClick={() => { setTab(t); if (t === 'upload') loadSources() }}
            style={{ padding: '0.4rem 1rem', background: tab === t ? '#818cf8' : '#eee', color: tab === t ? '#fff' : '#333', border: 'none', borderRadius: 6, cursor: 'pointer', fontWeight: 600 }}>
            {t === 'query' ? 'Ask' : 'Upload PDF'}
          </button>
        ))}
      </div>

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

          {result && (
            <div>
              <p style={{ fontWeight: 600, marginBottom: '1rem' }}>Relevant passages:</p>
              {result.context?.map((c, i) => (
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
              {sources.map(s => <p key={s} style={{ fontSize: '0.875rem', color: '#555' }}>• {s}</p>)}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
