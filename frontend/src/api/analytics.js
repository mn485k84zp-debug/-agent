import http from './http'

export function queryData(payload) {
  return http.post('/query_data', payload)
}
