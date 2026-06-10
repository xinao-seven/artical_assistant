<script setup lang="ts">
/**
 * 主布局组件: 侧边栏 + 顶栏 + 内容区
 */
import { ref } from 'vue'
import AppHeader from './AppHeader.vue'
import AppSidebar from './AppSidebar.vue'

const isCollapse = ref(false) // 侧边栏是否折叠
</script>

<template>
  <el-container class="app-layout">
    <!-- 侧边栏 -->
    <el-aside :width="isCollapse ? '64px' : '220px'" class="app-aside">
      <AppSidebar :is-collapse="isCollapse" />
    </el-aside>

    <!-- 右侧: 顶栏 + 内容 -->
    <el-container>
      <el-header class="app-header">
        <AppHeader v-model:is-collapse="isCollapse" />
      </el-header>

      <el-main class="app-main">
        <slot />
      </el-main>
    </el-container>
  </el-container>
</template>

<style scoped>
.app-layout {
  height: 100vh;
}

.app-aside {
  background-color: var(--el-bg-color);
  border-right: 1px solid var(--el-border-color);
  transition: width 0.3s;
  overflow: hidden;
}

.app-header {
  height: 60px;
  padding: 0;
  border-bottom: 1px solid var(--el-border-color);
  background-color: var(--el-bg-color);
}

.app-main {
  background-color: var(--el-bg-color-page, #f5f5f5);
  min-height: 0;
  overflow-y: auto;
  padding: 20px;
}
</style>
