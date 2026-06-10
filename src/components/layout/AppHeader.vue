<script setup lang="ts">
/**
 * 顶栏组件: 菜单折叠按钮 + 导航 + 用户头像下拉
 */
import { useRouter } from 'vue-router'
import { useUserStore } from '../../stores/user'

const props = defineProps<{
  isCollapse: boolean
}>()

const emit = defineEmits<{
  'update:isCollapse': [value: boolean]
}>()

const router = useRouter()
const userStore = useUserStore()

/** 切换侧边栏折叠 */
function toggleSidebar() {
  emit('update:isCollapse', !props.isCollapse)
}

/** 退出登录 */
function handleLogout() {
  userStore.logout()
  router.push({ name: 'Login' })
}
</script>

<template>
  <div class="header-content">
    <!-- 左侧: 折叠按钮 -->
    <div class="header-left">
      <el-button :icon="isCollapse ? 'Expand' : 'Fold'" text @click="toggleSidebar" />
      <span class="app-title">论文AI助手</span>
    </div>

    <!-- 右侧: 用户菜单 -->
    <div class="header-right">
      <el-dropdown trigger="click">
        <span class="user-avatar">
          <el-avatar :size="32" icon="UserFilled" />
          <span class="username">{{ userStore.user?.username || userStore.user?.email || '用户' }}</span>
        </span>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item @click="router.push({ name: 'Settings' })">
              <el-icon><Setting /></el-icon> 设置
            </el-dropdown-item>
            <el-dropdown-item divided @click="handleLogout">
              <el-icon><SwitchButton /></el-icon> 退出登录
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </div>
</template>

<style scoped>
.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 100%;
  padding: 0 16px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.app-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.header-right {
  display: flex;
  align-items: center;
}

.user-avatar {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.username {
  font-size: 14px;
  color: var(--el-text-color-regular);
}
</style>
