<script setup lang="ts">
/**
 * 404 页面
 */
import { useRouter } from 'vue-router'

const router = useRouter()
</script>

<template>
  <div class="not-found-page">
    <h1>404</h1>
    <p>页面不存在</p>
    <el-button type="primary" @click="router.push({ name: 'Dashboard' })">返回首页</el-button>
  </div>
</template>

<style scoped>
.not-found-page {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 60vh;
  gap: 16px;
}

.not-found-page h1 {
  font-size: 72px;
  color: var(--el-color-primary);
}
</style>
