<template>
  <div class="shell">
    <aside class="sidebar">
      <div class="brand">
        <div class="brand-badge">AI</div>
        <div>
          <div class="brand-title">电商 Agent 控制台</div>
          <div class="brand-subtitle">客服、知识库、分析一体化</div>
        </div>
      </div>

      <el-menu
        :default-active="route.path"
        class="menu"
        router
        background-color="transparent"
        text-color="#c8d8ea"
        active-text-color="#ffffff"
      >
        <el-menu-item index="/chat">智能客服</el-menu-item>
        <el-menu-item index="/knowledge">知识库管理</el-menu-item>
        <el-menu-item index="/analytics">数据分析</el-menu-item>
        <el-menu-item index="/status">系统状态</el-menu-item>
      </el-menu>
    </aside>

    <main class="content">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { useRoute } from 'vue-router'

const route = useRoute()
</script>

<style scoped>
.shell {
  min-height: 100vh;
  display: grid;
  grid-template-columns: 260px 1fr;
  background:
    radial-gradient(circle at top left, rgba(129, 196, 255, 0.22), transparent 32%),
    linear-gradient(180deg, #eaf4ff 0%, #f7fbff 100%);
}

.sidebar {
  padding: 24px 18px;
  background: linear-gradient(180deg, #12385d 0%, #18456d 100%);
  color: #fff;
}

.brand {
  display: flex;
  gap: 12px;
  align-items: center;
  margin-bottom: 24px;
}

.brand-badge {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: linear-gradient(135deg, #5dade2, #7dc8ff);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
}

.brand-title {
  font-size: 16px;
  font-weight: 700;
}

.brand-subtitle {
  font-size: 12px;
  opacity: 0.7;
}

.menu {
  border-right: none;
}

.content {
  padding: 20px;
}

@media (max-width: 900px) {
  .shell {
    grid-template-columns: 1fr;
  }

  .sidebar {
    padding-bottom: 10px;
  }
}
</style>
