import { defineStore } from 'pinia'

import {
  createSession,
  deleteSession,
  getSessionMessages,
  listSessions,
  streamChat
} from '../api/chat'

export const useChatStore = defineStore('chat', {
  state: () => ({
    sessions: [],
    activeSessionId: '',
    messages: [],
    loading: false,
    streamingText: '',
    stages: [],
    routeReason: ''
  }),
  actions: {
    async initialize() {
      const result = await listSessions()
      this.sessions = result.data || []
      if (!this.sessions.length) {
        const created = await createSession()
        this.sessions = [created.data]
      }
      this.activeSessionId = this.sessions[0]?.session_id || ''
      if (this.activeSessionId) {
        await this.loadSession(this.activeSessionId)
      }
    },
    async createNewSession() {
      const result = await createSession()
      this.sessions.unshift(result.data)
      this.activeSessionId = result.data.session_id
      this.messages = []
      this.stages = []
      this.routeReason = ''
    },
    async loadSession(sessionId) {
      this.activeSessionId = sessionId
      const result = await getSessionMessages(sessionId)
      this.messages = result.data.messages || []
      this.routeReason = ''
      this.stages = []
    },
    async removeSession(sessionId) {
      await deleteSession(sessionId)
      this.sessions = this.sessions.filter((item) => item.session_id !== sessionId)
      if (this.activeSessionId === sessionId) {
        if (!this.sessions.length) {
          await this.createNewSession()
        } else {
          await this.loadSession(this.sessions[0].session_id)
        }
      }
    },
    async sendMessage(message) {
      if (!message.trim() || this.loading) return

      this.loading = true
      this.streamingText = ''
      this.stages = []
      this.messages.push({ role: 'user', content: message })
      this.messages.push({ role: 'assistant', content: '', streaming: true })

      await streamChat(
        {
          session_id: this.activeSessionId || null,
          message
        },
        {
          onEvent: async (event) => {
            if (event.type === 'session') {
              this.activeSessionId = event.session_id
              const exists = this.sessions.some((item) => item.session_id === event.session_id)
              if (!exists) {
                this.sessions.unshift({
                  session_id: event.session_id,
                  title: event.title,
                  updated_at: new Date().toISOString(),
                  created_at: new Date().toISOString(),
                  last_route: 'rag'
                })
              }
            }

            if (event.type === 'status') {
              this.stages.push(event.message)
            }

            if (event.type === 'delta') {
              this.streamingText += event.content
              this.messages[this.messages.length - 1].content = this.streamingText
            }

            if (event.type === 'done') {
              const session = event.data.session
              this.messages = session.messages || this.messages
              this.routeReason = event.data.route_reason || ''
              this.sessions = this.sessions.map((item) =>
                item.session_id === session.session_id ? { ...item, ...session } : item
              )
              this.loading = false
            }

            if (event.type === 'error') {
              this.messages[this.messages.length - 1].content = event.message
              this.loading = false
            }
          }
        }
      )

      this.loading = false
      await this.refreshSessions()
    },
    async refreshSessions() {
      const result = await listSessions()
      this.sessions = result.data || []
    }
  }
})
