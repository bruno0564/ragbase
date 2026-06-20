import { useEffect, useRef, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

import { streamQuery } from './stream'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Paleta mínima reutilizada en los estilos inline.
const INDIGO = '#818cf8'

export default function App() {
  const [tab, setTab] = useState('chat')
  // Cada mensaje: { role: 'user' | 'assistant', content, context?, streamed? }
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)

  const [sources, setSources] = useState([])
  const [uploading, setUploading] = useState(false)

  const bottomRef = useRef(null)
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  async function handleSend(e) {
    e.preventDefault()
    const question = input.trim()
    if (!question || busy) return

    // Historial = turnos previos con contenido (memoria conversacional).
    const history = messages
      .filter((m) => m.content)
      .map((m) => ({ role: m.role, content: m.content }))

    setInput('')
    setError(null)
    setBusy(true)
    // Añadimos el turno del usuario y un hueco para la respuesta del asistente.
    setMessages((prev) => [
      ...prev,
      { role: 'user', content: question },
      { role: 'assistant', content: '', context: [], streamed: false },
    ])

    const update = (patch) =>
      setMessages((prev) => {
        const next = [...prev]
        const last = next.length - 1
        next[last] = typeof patch === 'function' ? patch(next[last]) : { ...next[last], ...patch }
        return next
      })

    try {
      await streamQuery(
        API,
        { question, history },
        {
          onContext: (context) => update({ context: context || [] }),
          onToken: (text) => update((m) => ({ ...m, content: m.content + text, streamed: true })),
          onDone: (payload) => update({ streamed: Boolean(payload.answer) }),
        },
      )
    } catch (err) {
      setError(err.message || 'Could not reach the server')
      // Quitamos el hueco vacío del asistente si falló del todo.
      setMessages((prev) => {
        const last = prev[prev.length - 1]
        if (last?.role === 'assistant' && !last.content) return prev.slice(0, -1)
        return prev
      })
    } finally {
      setBusy(false)
    }
  }

  async function loadSources() {
    try {
      const r = await fetch(`${API}/sources`)
      if (!r.ok) throw new Error(`Could not load documents (${r.status})`)
      setSources((await r.json()).sources)
    } catch (err) {
      setError(err.message || 'Could not load documents')
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
    <div style={S.page}>
      <div style={S.header}>
        <h1 style={S.title}>ragbase</h1>
        {tab === 'chat' && messages.length > 0 && (
          <button onClick={() => setMessages([])} style={S.ghostBtn} disabled={busy}>
            New chat
          </button>
        )}
      </div>

      <div style={S.tabs}>
        {['chat', 'upload'].map((t) => (
          <button
            key={t}
            onClick={() => {
              setTab(t)
              setError(null)
              if (t === 'upload') loadSources()
            }}
            style={tab === t ? S.tabActive : S.tab}
          >
            {t === 'chat' ? 'Chat' : 'Upload PDF'}
          </button>
        ))}
      </div>

      {error && <div style={S.error}>{error}</div>}

      {tab === 'chat' && (
        <>
          <div style={S.thread}>
            {messages.length === 0 && (
              <p style={S.hint}>Ask something about your documents. Upload a PDF first if empty.</p>
            )}
            {messages.map((m, i) => (
              <ChatMessage key={i} message={m} streaming={busy && i === messages.length - 1} />
            ))}
            <div ref={bottomRef} />
          </div>

          <form onSubmit={handleSend} style={S.inputRow}>
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask a question..."
              style={S.input}
              disabled={busy}
            />
            <button type="submit" disabled={busy} style={S.sendBtn}>
              {busy ? '...' : 'Send'}
            </button>
          </form>
        </>
      )}

      {tab === 'upload' && (
        <div>
          <label style={S.uploadBtn}>
            {uploading ? 'Uploading...' : 'Choose PDF'}
            <input type="file" accept=".pdf" onChange={handleUpload} hidden disabled={uploading} />
          </label>
          {sources.length > 0 && (
            <div style={{ marginTop: '1.5rem' }}>
              <p style={{ fontWeight: 600, marginBottom: '0.5rem' }}>Indexed documents:</p>
              {sources.map((s) => (
                <div key={s} style={S.sourceRow}>
                  <span>• {s}</span>
                  <button onClick={() => handleDelete(s)} style={S.removeBtn}>
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

function ChatMessage({ message, streaming }) {
  const isUser = message.role === 'user'
  if (isUser) {
    return (
      <div style={{ ...S.bubbleRow, justifyContent: 'flex-end' }}>
        <div style={S.userBubble}>{message.content}</div>
      </div>
    )
  }

  const hasAnswer = message.content.length > 0
  const passages = message.context || []
  return (
    <div style={{ ...S.bubbleRow, justifyContent: 'flex-start' }}>
      <div style={S.assistantBubble}>
        {hasAnswer ? (
          <div style={S.markdown}>
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>
            {streaming && <span style={S.caret}>▍</span>}
          </div>
        ) : streaming ? (
          <span style={{ color: '#888' }}>Thinking…</span>
        ) : (
          <p style={{ color: '#888', margin: 0, fontSize: '0.85rem' }}>
            {passages.length
              ? 'No generated answer (start Ollama for that). Relevant passages:'
              : 'No documents indexed yet — upload a PDF first.'}
          </p>
        )}

        {passages.length > 0 && (
          <div style={{ marginTop: hasAnswer ? '0.75rem' : '0.5rem' }}>
            {hasAnswer && <p style={S.sourcesLabel}>Sources</p>}
            {passages.map((c, i) => (
              <div key={i} style={S.passage}>
                <p style={S.passageMeta}>
                  {c.source} · chunk {c.chunk} · score {c.score}
                </p>
                <p style={{ margin: 0, fontSize: '0.85rem', lineHeight: 1.5 }}>{c.text}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

const S = {
  page: { maxWidth: 760, margin: '0 auto', padding: '2rem 1rem', fontFamily: 'system-ui, sans-serif' },
  header: { display: 'flex', alignItems: 'center', justifyContent: 'space-between' },
  title: { fontSize: '1.5rem', fontWeight: 700, margin: 0 },
  ghostBtn: { background: 'none', border: '1px solid #ddd', borderRadius: 6, padding: '0.3rem 0.7rem', cursor: 'pointer', fontSize: '0.8rem', color: '#555' },
  tabs: { display: 'flex', gap: '0.5rem', margin: '1.25rem 0' },
  tab: { padding: '0.4rem 1rem', background: '#eee', color: '#333', border: 'none', borderRadius: 6, cursor: 'pointer', fontWeight: 600 },
  tabActive: { padding: '0.4rem 1rem', background: INDIGO, color: '#fff', border: 'none', borderRadius: 6, cursor: 'pointer', fontWeight: 600 },
  error: { background: '#fee2e2', border: '1px solid #fca5a5', color: '#991b1b', borderRadius: 6, padding: '0.6rem 0.85rem', marginBottom: '1rem', fontSize: '0.85rem' },
  thread: { display: 'flex', flexDirection: 'column', gap: '0.75rem', minHeight: 280, maxHeight: '60vh', overflowY: 'auto', padding: '0.5rem 0' },
  hint: { color: '#888', fontSize: '0.9rem' },
  bubbleRow: { display: 'flex' },
  userBubble: { background: INDIGO, color: '#fff', padding: '0.55rem 0.85rem', borderRadius: '14px 14px 2px 14px', maxWidth: '80%', fontSize: '0.9rem', lineHeight: 1.5, whiteSpace: 'pre-wrap' },
  assistantBubble: { background: '#f4f4f6', color: '#1f2330', padding: '0.7rem 0.95rem', borderRadius: '14px 14px 14px 2px', maxWidth: '88%', fontSize: '0.92rem' },
  markdown: { lineHeight: 1.6 },
  caret: { color: INDIGO, marginLeft: 2 },
  sourcesLabel: { fontSize: '0.7rem', color: '#6366f1', fontWeight: 700, letterSpacing: '0.05em', margin: '0 0 0.4rem' },
  passage: { background: '#fff', border: '1px solid #e7e7ec', borderRadius: 8, padding: '0.6rem 0.75rem', marginBottom: '0.5rem' },
  passageMeta: { fontSize: '0.72rem', color: '#999', margin: '0 0 0.3rem' },
  inputRow: { display: 'flex', gap: '0.5rem', marginTop: '1rem' },
  input: { flex: 1, padding: '0.65rem 0.8rem', border: '1px solid #ddd', borderRadius: 8, fontSize: '0.9rem' },
  sendBtn: { padding: '0.65rem 1.3rem', background: INDIGO, color: '#fff', border: 'none', borderRadius: 8, cursor: 'pointer', fontWeight: 600 },
  uploadBtn: { display: 'inline-block', padding: '0.6rem 1.2rem', background: INDIGO, color: '#fff', borderRadius: 6, cursor: 'pointer', fontWeight: 600 },
  sourceRow: { display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.875rem', color: '#555', padding: '0.3rem 0' },
  removeBtn: { background: 'none', border: 'none', color: '#ef4444', cursor: 'pointer', fontSize: '0.8rem', fontWeight: 600 },
}
