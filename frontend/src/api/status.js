import http from './http'

export function getStatus(sessionId) {
  return http.get('/status', { params: sessionId ? { session_id: sessionId } : {} })
}
