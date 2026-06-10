<script setup lang="ts">
/**
 * 侧边栏导航菜单
 */
import { useRoute } from 'vue-router'

defineProps<{
  isCollapse: boolean
}>()

const route = useRoute()

// 菜单项配置
const menuItems = [
  { path: '/dashboard', title: '仪表盘', icon: 'Odometer' },
  { path: '/search', title: '论文检索', icon: 'Search' },
  { path: '/library', title: '论文库', icon: 'Collection' },
  { path: '/settings', title: '设置', icon: 'Setting' },
]
</script>

<template>
  <div class="sidebar-container">
    <!-- Logo区域 -->
    <div class="logo-area">
      <span class="logo-text">{{ isCollapse ? 'AI' : '论文AI助手' }}</span>
    </div>

    <!-- 菜单 -->
    <el-menu
      :default-active="route.path"
      :collapse="isCollapse"
      :router="true"
      background-color="transparent"
    >
      <el-menu-item v-for="item in menuItems" :key="item.path" :index="item.path">
        <el-icon><component :is="item.icon" /></el-icon>
        <template #title>{{ item.title }}</template>
      </el-menu-item>
    </el-menu>
  </div>
</template>

<style scoped>
.sidebar-container {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.logo-area {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-bottom: 1px solid var(--el-border-color);
}

.logo-text {
  font-size: 18px;
  font-weight: 700;
  color: var(--el-color-primary);
  white-space: nowrap;
}

.el-menu {
  border-right: none;
}
</style>
