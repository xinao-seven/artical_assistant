<script setup lang="ts">
/**
 * 根组件
 * - 根据路由显示登录/注册页 (无布局)
 * - 或显示主布局 (有侧边栏+顶栏)
 */
import { useRouter } from 'vue-router'
import AppLayout from './components/layout/AppLayout.vue'

const router = useRouter()
</script>

<template>
  <!-- 登录/注册页不使用主布局 -->
  <template v-if="router.currentRoute.value.name === 'Login' || router.currentRoute.value.name === 'Register'">
    <router-view />
  </template>
  <!-- 其他页面使用主布局 -->
  <template v-else>
    <AppLayout>
      <router-view />
    </AppLayout>
  </template>
</template>
