<template>
  <div class="page-stack">
    <section class="panel">
      <div class="panel-header">
        <div>
          <div class="panel-title">自然语言数据分析</div>
          <div class="panel-subtitle">直接提问，系统将自动检索 Schema、生成 SQL 并返回图表</div>
        </div>
      </div>

      <el-input
        v-model="question"
        type="textarea"
        :rows="3"
        resize="none"
        placeholder="例如：上周每天的订单量是多少？客单价最高的商品是哪个？"
      />
      <div class="toolbar">
        <el-button type="primary" :loading="loading" @click="submitQuery">开始分析</el-button>
        <el-radio-group v-model="chartType">
          <el-radio-button label="bar">柱状图</el-radio-button>
          <el-radio-button label="line">折线图</el-radio-button>
        </el-radio-group>
      </div>
    </section>

    <section v-if="result" class="panel">
      <div class="panel-title">分析结论</div>
      <div class="analysis-answer">{{ result.answer }}</div>
      <div class="schema-tags">
        <el-tag v-for="table in result.schema_tables" :key="table" effect="plain">{{ table }}</el-tag>
      </div>
      <el-collapse>
        <el-collapse-item title="查看生成的 SQL" name="sql">
          <pre class="sql-preview">{{ result.sql }}</pre>
        </el-collapse-item>
      </el-collapse>
    </section>

    <section v-if="result?.rows?.length" class="panel">
      <div class="panel-title">图表展示</div>
      <ChartPanel :chart-data="result.chart" :chart-type="chartType" />
    </section>

    <section v-if="result?.rows?.length" class="panel">
      <div class="panel-title">结果表格</div>
      <el-table :data="result.rows" stripe>
        <el-table-column
          v-for="column in result.columns"
          :key="column"
          :prop="column"
          :label="column"
          min-width="140"
        />
      </el-table>
    </section>
  </div>
</template>

<script setup>
import { ElMessage } from 'element-plus'
import { ref } from 'vue'

import { queryData } from '../api/analytics'
import ChartPanel from '../components/ChartPanel.vue'
import { useChatStore } from '../stores/chat'

const chatStore = useChatStore()
const question = ref('')
const loading = ref(false)
const result = ref(null)
const chartType = ref('bar')

async function submitQuery() {
  if (!question.value.trim()) {
    ElMessage.warning('请输入分析问题')
    return
  }
  loading.value = true
  try {
    const response = await queryData({
      question: question.value,
      session_id: chatStore.activeSessionId || null
    })
    result.value = response.data
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    loading.value = false
  }
}
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
  margin-bottom: 18px;
}

.panel-title {
  font-size: 20px;
  font-weight: 700;
  color: #12385d;
  margin-bottom: 12px;
}

.panel-subtitle {
  color: #6e86a1;
  font-size: 13px;
}

.toolbar {
  margin-top: 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.analysis-answer {
  line-height: 1.8;
  color: #254566;
}

.schema-tags {
  margin: 12px 0 16px;
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.sql-preview {
  background: #0b2239;
  color: #e8f2ff;
  padding: 14px;
  border-radius: 14px;
  overflow: auto;
}
</style>
