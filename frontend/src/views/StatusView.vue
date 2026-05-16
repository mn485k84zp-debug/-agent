<template>
  <div class="page-stack">
    <section class="panel">
      <div class="panel-header">
        <div>
          <div class="panel-title">系统状态</div>
          <div class="panel-subtitle">监控记忆、检索、工具调用与多 Agent 协作情况</div>
        </div>
        <el-button type="primary" plain @click="loadStatus">刷新</el-button>
      </div>

      <div class="card-grid">
        <div class="metric-card">
          <div class="metric-label">当前 Token 数</div>
          <div class="metric-value">{{ statusData.memory?.current_tokens || 0 }}</div>
        </div>
        <div class="metric-card">
          <div class="metric-label">记忆窗口轮数</div>
          <div class="metric-value">{{ statusData.memory?.recent_turn_count || 0 }}/{{ statusData.memory?.window_limit || 0 }}</div>
        </div>
        <div class="metric-card">
          <div class="metric-label">RAG 近似召回率</div>
          <div class="metric-value">{{ statusData.rag?.approx_recall_rate || 0 }}%</div>
        </div>
        <div class="metric-card">
          <div class="metric-label">工具成功率</div>
          <div class="metric-value">{{ statusData.tools?.success_rate || 0 }}%</div>
        </div>
      </div>
    </section>

    <section class="panel">
      <div class="panel-title">核心模块状态</div>
      <el-table :data="moduleRows" stripe>
        <el-table-column prop="module" label="模块" min-width="180" />
        <el-table-column prop="status" label="状态" width="140" />
        <el-table-column prop="description" label="说明" min-width="260" />
      </el-table>
    </section>

    <section class="panel">
      <div class="panel-title">详细指标</div>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="当前会话数">{{ statusData.system?.session_count || 0 }}</el-descriptions-item>
        <el-descriptions-item label="知识库文档数">{{ statusData.system?.knowledge_documents || 0 }}</el-descriptions-item>
        <el-descriptions-item label="摘要 Token">{{ statusData.memory?.summary_tokens || 0 }}</el-descriptions-item>
        <el-descriptions-item label="记忆阈值">{{ statusData.memory?.token_threshold || 0 }}</el-descriptions-item>
        <el-descriptions-item label="RAG 调用次数">{{ statusData.rag?.total_calls || 0 }}</el-descriptions-item>
        <el-descriptions-item label="工具成功次数">{{ statusData.tools?.success_count || 0 }}</el-descriptions-item>
        <el-descriptions-item label="工具错误次数">{{ statusData.tools?.error_count || 0 }}</el-descriptions-item>
        <el-descriptions-item label="上次路由">{{ statusData.rag?.last_route || '-' }}</el-descriptions-item>
      </el-descriptions>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'

import { getStatus } from '../api/status'
import { useChatStore } from '../stores/chat'

const chatStore = useChatStore()
const statusData = ref({
  system: {},
  memory: {},
  rag: {},
  tools: {},
  agents: {}
})
let timer = null

const moduleRows = computed(() => [
  {
    module: 'Supervisor',
    status: statusData.value.agents?.supervisor || 'unknown',
    description: statusData.value.agents?.last_route_reason || '负责意图识别与任务拆解'
  },
  {
    module: 'RAG Agent',
    status: statusData.value.agents?.rag_agent || 'unknown',
    description: `近似召回率 ${statusData.value.rag?.approx_recall_rate || 0}%`
  },
  {
    module: 'SQL Agent',
    status: statusData.value.agents?.sql_agent || 'unknown',
    description: '负责结构化数据查询与可视化分析'
  }
])

async function loadStatus() {
  const result = await getStatus(chatStore.activeSessionId || null)
  statusData.value = result.data || {}
}

onMounted(async () => {
  await loadStatus()
  timer = setInterval(loadStatus, 5000)
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
})
</script>

<style scoped>
.page-stack {
  display: grid;
  gap: 20px;
}

.panel {
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(125, 173, 226, 0.16);
  border-radius: 24px;
  padding: 20px;
  box-shadow: 0 18px 50px rgba(68, 113, 160, 0.09);
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
  color: #6e86a1;
  font-size: 13px;
  margin-top: 4px;
}

.card-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
}

.metric-card {
  border-radius: 18px;
  padding: 18px;
  background: linear-gradient(180deg, #f6fbff, #eef6ff);
  border: 1px solid rgba(125, 173, 226, 0.16);
}

.metric-label {
  color: #7590aa;
  font-size: 13px;
}

.metric-value {
  margin-top: 10px;
  color: #173f67;
  font-size: 28px;
  font-weight: 700;
}

@media (max-width: 900px) {
  .card-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
