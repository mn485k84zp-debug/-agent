import http from './http'

export function listDocuments() {
  return http.get('/documents')
}

export function uploadDocument(formData, onUploadProgress) {
  return http.post('/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress
  })
}

export function deleteDocument(fileName) {
  return http.delete(`/documents/${encodeURIComponent(fileName)}`)
}
