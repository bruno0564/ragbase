// Cliente de Server-Sent Events sobre fetch.
//
// El endpoint /query/stream es un POST (lleva la pregunta y el historial en el
// cuerpo), así que no se puede usar EventSource —solo admite GET—. Leemos el
// ReadableStream a mano y parseamos los eventos SSE (bloques separados por una
// línea en blanco, con líneas `event:` y `data:`).

export async function streamQuery(api, { question, history }, { onContext, onToken, onDone }) {
  const response = await fetch(`${api}/query/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, history }),
  })
  if (!response.ok || !response.body) {
    throw new Error(`Server error (${response.status})`)
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  for (;;) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })

    const blocks = buffer.split('\n\n')
    buffer = blocks.pop() ?? '' // el último puede estar incompleto

    for (const block of blocks) {
      let name = 'message'
      let data = ''
      for (const line of block.split('\n')) {
        if (line.startsWith('event:')) name = line.slice(6).trim()
        else if (line.startsWith('data:')) data += line.slice(5).trim()
      }
      if (!data) continue

      const payload = JSON.parse(data)
      if (name === 'context') onContext?.(payload.context)
      else if (name === 'token') onToken?.(payload.text)
      else if (name === 'done') onDone?.(payload)
    }
  }
}
