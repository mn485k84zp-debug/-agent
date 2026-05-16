<template>
  <div class="page-grid">
    <section class="panel session-panel">
      <div class="panel-header">
        <div>
          <div class="panel-title">会话列表</div>
          <div class="panel-subtitle">保留多轮上下文和分层记忆</div>
        </div>
        <el-button type="primary" plain @click="chatStore.createNewSession">新建</el-button>
      </div>

      <div class="session-list">
        <div
          v-for="session in chatStore.sessions"
          :key="session.session_id"
          :class="['session-card', { active: session.session_id === chatStore.activeSessionId }]"
          @click="chatStore.loadSession(session.session_id)"
        >
          <div class="session-title">{{ session.title }}</div>
          <div class="session-meta">{{ session.updated_at }}</div>
          <div class="session-actions">
            <el-tag size="small" effect="plain">{{ session.last_route || 'rag' }}</el-tag>
            <el-button link type="danger" @click.stop="chatStore.removeSession(session.session_id)">删除</el-button>
          </div>
        </div>
      </div>
    </section>

    <section class="panel chat-panel">
      <div class="panel-header">
        <div>
          <div class="panel-title">智能客服对话</div>
          <div class="panel-subtitle">支持知识检索、工具调用与多 Agent 路由</div>
        </div>
      </div>

      <div class="status-strip">
        <el-tag
          v-for="(stage, index) in chatStore.stages"
          :key="`${stage}-${index}`"
          type="info"
          effect="plain"
        >
          {{ stage }}
        </el-tag>
        <el-tag v-if="chatStore.routeReason" type="success" effect="light">
          路由说明：{{ chatStore.routeReason }}
        </el-tag>
      </div>

      <div ref="messageBoxRef" class="message-box">
        <div v-if="!chatStore.messages.length" class="empty-state">
          试试问我：订单 ORD-1001 发货了吗？或者最近哪类商品销售最好？
        </div>
        <ChatMessage v-for="(message, index) in chatStore.messages" :key="index" :message="message" />
      </div>

      <div class="composer">
        <el-input
          v-model="userInput"
          type="textarea"
          :rows="3"
          resize="none"
          placeholder="输入你的问题，支持客服咨询、订单查询、数据分析..."
          @keydown.enter.prevent="handleEnter"
        />
        <div class="composer-actions">
          <span class="hint">Shift + Enter 换行，Enter 发送</span>
          <el-button type="primary" :loading="chatStore.loading" @click="sendMessage">发送消息</el-button>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ElMessage } from 'element-plus'
import { nextTick, onMounted, ref, watch } from 'vue'

import ChatMessage from '../components/ChatMessage.vue'
import { useChatStore } from '../stores/chat'

const chatStore = useChatStore()
const userInput = ref('')
const messageBoxRef = ref(null)

function scrollToBottom() {
  nextTick(() => {
    if (messageBoxRef.value) {
      messageBoxRef.value.scrollTop = messageBoxRef.value.scrollHeight
    }
  })
}

async function sendMessage() {
  const content = userInput.value.trim()
  if (!content) {
    ElMessage.warning('请输入消息内容')
    return
  }
  userInput.value = ''
  try {
    await chatStore.sendMessage(content)
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    scrollToBottom()
  }
}

function handleEnter(event) {
  if (event.shiftKey) return
  sendMessage()
}

watch(
  () => chatStore.messages,
  () => scrollToBottom(),
  { deep: true }
)

onMounted(async () => {
  try {
    await chatStore.initialize()
    scrollToBottom()
  } catch (error) {
    ElMessage.error(error.message)
  }
})
</script>

<style scoped>
.page-grid {
  display: grid;
  grid-template-columns: 320px 1fr;
  gap: 20px;
  min-height: calc(100vh - 40px);
}

.panel {
  background: rgba(255, 255, 255, 0.88);
  border: 1px solid rgba(125, 173, 226, 0.16);
  border-radius: 24px;
  box-shadow: 0 18px 50px rgba(68, 113, 160, 0.09);
  padding: 20px;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 18px;
}

.panel-title {
  font-size: 20px;
  font-weight: 700;
  color: #12385d;
}

.panel-subtitle {
  margin-top: 4px;
  color: #6e86a1;
  font-size: 13px;
}

.session-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.session-card {
  border: 1px solid rgba(129, 176, 227, 0.18);
  border-radius: 16px;
  padding: 14px;
  cursor: pointer;
  background: #f9fcff;
}

.session-card.active {
  border-color: #4a90e2;
  box-shadow: 0 10px 28px rgba(74, 144, 226, 0.12);
}

.session-title {
  font-weight: 600;
  color: #1d3d62;
}

.session-meta {
  margin-top: 6px;
  color: #7b8ea8;
  font-size: 12px;
}

.session-actions {
  margin-top: 10px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.chat-panel {
  display: flex;
  flex-direction: column;
}

.status-strip {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 16px;
  min-height: 36px;
}

.message-box {
  flex: 1;
  overflow: auto;
  padding: 12px 2px;
  min-height: 420px;
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #7990a8;
}

.composer {
  border-top: 1px solid rgba(125, 173, 226, 0.16);
  padding-top: 16px;
}

.composer-actions {
  margin-top: 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.hint {
  font-size: 12px;
  color: #7a8ea5;
}

@media (max-width: 1100px) {
  .page-grid {
    grid-template-columns: 1fr;
  }
}
</style>
