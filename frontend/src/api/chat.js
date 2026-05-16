import http from './http'

export function listSessions() {
  return http.get('/sessions')
}

export function createSession() {
  return http.post('/sessions')
}

export function getSessionMessages(sessionId) {
  return http.get(`/sessions/${sessionId}/messages`)
}

export function deleteSession(sessionId) {
  return http.delete(`/sessions/${sessionId}`)
}

export async function streamChat(payload, handlers) {
  const response = await fetch(`${import.meta.env.VITE_API_BASE_URL || ''}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })

  if (!response.ok || !response.body) {
    throw new Error('流式对话连接失败')
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder('utf-8')
  let buffer = ''

  while (true) {
    const { value, done } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const events = buffer.split('\n\n')
    buffer = events.pop() || ''

    for (const event of events) {
      const line = event
        .split('\n')
        .find((item) => item.startsWith('data: '))
      if (!line) continue
      const payload = JSON.parse(line.slice(6))
      handlers?.onEvent?.(payload)
    }
  }
}
