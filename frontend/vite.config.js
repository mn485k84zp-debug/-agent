import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, path.resolve(__dirname, '..'), '')
  const target = env.VITE_API_BASE_URL || `http://127.0.0.1:${env.API_PORT || '8000'}`

  return {
    plugins: [vue()],
    envDir: '..',
    server: {
      host: '0.0.0.0',
      port: 5173,
      proxy: {
        '/chat': target,
        '/sessions': target,
        '/documents': target,
        '/upload': target,
        '/query_data': target,
        '/status': target,
        '/health': target
      }
    }
  }
})
