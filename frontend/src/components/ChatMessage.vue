<template>
  <div :class="['message-row', message.role]">
    <div class="message-bubble">
      <div class="message-role">{{ message.role === 'user' ? '用户' : 'Agent' }}</div>
      <div v-if="message.role === 'assistant'" class="markdown-body" v-html="renderedContent"></div>
      <div v-else class="plain-text">{{ message.content }}</div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import MarkdownIt from 'markdown-it'

const props = defineProps({
  message: {
    type: Object,
    required: true
  }
})

const md = new MarkdownIt({
  html: false,
  linkify: true,
  breaks: true
})

const renderedContent = computed(() => md.render(props.message.content || ''))
</script>

<style scoped>
.message-row {
  display: flex;
  margin-bottom: 16px;
}

.message-row.user {
  justify-content: flex-end;
}

.message-row.assistant {
  justify-content: flex-start;
}

.message-bubble {
  max-width: min(86%, 760px);
  border-radius: 16px;
  padding: 14px 16px;
  box-shadow: 0 10px 30px rgba(15, 76, 129, 0.08);
  backdrop-filter: blur(8px);
}

.user .message-bubble {
  background: linear-gradient(135deg, #3a8ee6, #66b1ff);
  color: #fff;
}

.assistant .message-bubble {
  background: rgba(255, 255, 255, 0.94);
  border: 1px solid rgba(125, 173, 226, 0.18);
}

.message-role {
  font-size: 12px;
  opacity: 0.7;
  margin-bottom: 8px;
}

.plain-text {
  white-space: pre-wrap;
  line-height: 1.7;
}

.markdown-body {
  line-height: 1.75;
  word-break: break-word;
}

.markdown-body :deep(pre) {
  overflow: auto;
  background: #0b2239;
  color: #e8f2ff;
  border-radius: 12px;
  padding: 12px;
}

.markdown-body :deep(code) {
  font-family: Consolas, Monaco, monospace;
}
</style>
