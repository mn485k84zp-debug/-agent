<template>
  <div class="page-stack">
    <section class="panel">
      <div class="panel-header">
        <div>
          <div class="panel-title">知识库管理</div>
          <div class="panel-subtitle">上传 Markdown 或 PDF，自动切分并写入 ChromaDB</div>
        </div>
      </div>

      <el-upload
        drag
        :auto-upload="false"
        :show-file-list="false"
        :http-request="() => {}"
        accept=".md,.markdown,.txt,.pdf"
        @change="handleFileChange"
      >
        <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
        <div class="el-upload__text">拖拽文件到这里，或点击选择文档</div>
      </el-upload>

      <div class="upload-actions">
        <el-button type="primary" :disabled="!selectedFile" :loading="uploading" @click="submitUpload">
          上传并重建索引
        </el-button>
        <span class="upload-name">{{ selectedFile?.name || '未选择文件' }}</span>
      </div>

      <el-progress v-if="uploading" :percentage="uploadProgress" />
    </section>

    <section class="panel">
      <div class="panel-header">
        <div>
          <div class="panel-title">文档列表</div>
          <div class="panel-subtitle">当前已加入知识库的文档</div>
        </div>
      </div>

      <el-table :data="documents" stripe>
        <el-table-column prop="display_name" label="文件名" min-width="260" />
        <el-table-column prop="source_type" label="类型" width="120" />
        <el-table-column prop="size" label="大小(Byte)" width="140" />
        <el-table-column prop="updated_at" label="更新时间" min-width="180" />
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button link type="danger" @click="removeDocument(row.file_name)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </section>
  </div>
</template>

<script setup>
import { UploadFilled } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { onMounted, ref } from 'vue'

import { deleteDocument, listDocuments, uploadDocument } from '../api/knowledge'

const documents = ref([])
const selectedFile = ref(null)
const uploading = ref(false)
const uploadProgress = ref(0)

async function loadDocuments() {
  const result = await listDocuments()
  documents.value = result.data || []
}

function handleFileChange(file) {
  selectedFile.value = file.raw
}

async function submitUpload() {
  if (!selectedFile.value) {
    ElMessage.warning('请先选择文件')
    return
  }

  const formData = new FormData()
  formData.append('file', selectedFile.value)
  uploading.value = true
  uploadProgress.value = 0

  try {
    await uploadDocument(formData, (event) => {
      if (event.total) {
        uploadProgress.value = Math.round((event.loaded / event.total) * 100)
      }
    })
    ElMessage.success('文档已成功加入知识库')
    selectedFile.value = null
    await loadDocuments()
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    uploading.value = false
  }
}

async function removeDocument(fileName) {
  await ElMessageBox.confirm('删除后会自动重建知识库索引，确认继续吗？', '删除提示', {
    type: 'warning'
  })
  await deleteDocument(fileName)
  ElMessage.success('文档已删除')
  await loadDocuments()
}

onMounted(loadDocuments)
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
}

.panel-subtitle {
  margin-top: 4px;
  color: #6e86a1;
  font-size: 13px;
}

.upload-actions {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-top: 16px;
}

.upload-name {
  color: #5f7590;
}
</style>
