<script setup lang="ts">
/**
 * 论文列表组件
 * 卡片网格布局 + 分页器
 */
import { computed } from 'vue'
import type { PaperResponse } from '@/api/papers'
import PaperCard from './PaperCard.vue'

const props = defineProps<{
  papers: PaperResponse[]
  loading: boolean
  total: number
  page: number
  size: number
}>()

const emit = defineEmits<{
  'view-detail': [paperId: string]
  'delete-paper': [paperId: string]
  'page-change': [page: number]
  'size-change': [size: number]
}>()

/** 是否显示分页器 */
const showPagination = computed(() => props.total > props.size)
</script>

<template>
  <div class="paper-list-container">
    <!-- 加载状态 -->
    <div v-if="loading" class="loading-area">
      <el-skeleton :rows="3" animated />
      <el-skeleton :rows="3" animated />
      <el-skeleton :rows="3" animated />
    </div>

    <!-- 空状态 -->
    <el-empty
      v-else-if="papers.length === 0"
      description="还没有论文，上传或搜索添加吧"
      :image-size="120"
    />

    <!-- 卡片网格 -->
    <div v-else class="paper-grid">
      <PaperCard
        v-for="paper in papers"
        :key="paper.id"
        :paper="paper"
        @click="emit('view-detail', paper.id)"
        @delete="emit('delete-paper', paper.id)"
      />
    </div>

    <!-- 分页 -->
    <div v-if="showPagination" class="pagination-area">
      <el-pagination
        :current-page="page"
        :page-size="size"
        :total="total"
        :page-sizes="[12, 24, 48]"
        layout="total, sizes, prev, pager, next"
        background
        @current-change="emit('page-change', $event)"
        @size-change="emit('size-change', $event)"
      />
    </div>
  </div>
</template>

<style scoped>
.paper-list-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.loading-area {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 20px;
}

.paper-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
}

.pagination-area {
  display: flex;
  justify-content: center;
  padding: 16px 0;
}
</style>
