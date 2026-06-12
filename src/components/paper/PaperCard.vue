<script setup lang="ts">
/**
 * 论文卡片组件
 * 展示论文的基本信息: 标题/作者/年份/标签/来源
 */
import { Delete } from '@element-plus/icons-vue'
import type { PaperResponse } from '@/api/papers'

const props = defineProps<{
  paper: PaperResponse
}>()

const emit = defineEmits<{
  click: [paperId: string]
  delete: [paperId: string]
}>()

/** 格式化作者列表 */
function formatAuthors(authors: string[]): string {
  if (!authors || authors.length === 0) return '未知作者'
  if (authors.length <= 3) return authors.join(', ')
  return `${authors.slice(0, 3).join(', ')} 等 ${authors.length} 位`
}

/** 来源标签样式 */
function sourceTagType(source: string): 'success' | 'warning' | 'info' | '' {
  switch (source) {
    case 'upload': return 'success'
    case 'arxiv': return 'warning'
    case 'semantic_scholar': return 'info'
    default: return ''
  }
}

function sourceLabel(source: string): string {
  switch (source) {
    case 'upload': return '上传'
    case 'arxiv': return 'arXiv'
    case 'semantic_scholar': return 'Semantic Scholar'
    default: return '手动'
  }
}
</script>

<template>
  <div class="paper-card" @click="emit('click', paper.id)">
    <!-- 标题 -->
    <h4 class="paper-title">{{ paper.title }}</h4>

    <!-- 作者 -->
    <p class="paper-authors">{{ formatAuthors(paper.authors) }}</p>

    <!-- 摘要预览 -->
    <p v-if="paper.abstract" class="paper-abstract">
      {{ paper.abstract.slice(0, 200) }}{{ paper.abstract.length > 200 ? '...' : '' }}
    </p>

    <!-- 元信息行 -->
    <div class="paper-meta">
      <el-tag v-if="paper.year" size="small" type="info" effect="plain">
        {{ paper.year }}
      </el-tag>
      <el-tag size="small" :type="sourceTagType(paper.source)" effect="plain">
        {{ sourceLabel(paper.source) }}
      </el-tag>
      <el-tag v-if="paper.citation_count > 0" size="small" type="info" effect="plain">
        引用 {{ paper.citation_count }}
      </el-tag>
      <el-tag v-if="paper.pages_count" size="small" type="info" effect="plain">
        {{ paper.pages_count }} 页
      </el-tag>
    </div>

    <!-- 用户标签 -->
    <div v-if="paper.tags && paper.tags.length > 0" class="paper-tags">
      <el-tag
        v-for="tag in paper.tags.slice(0, 5)"
        :key="tag"
        size="small"
        effect="light"
        round
      >
        {{ tag }}
      </el-tag>
      <span v-if="paper.tags.length > 5" class="more-tags">+{{ paper.tags.length - 5 }}</span>
    </div>

    <!-- 操作区 -->
    <div class="paper-actions" @click.stop>
      <el-button
        text
        size="small"
        type="danger"
        @click="emit('delete', paper.id)"
      >
        <el-icon><Delete /></el-icon>
      </el-button>
    </div>
  </div>
</template>

<style scoped>
.paper-card {
  position: relative;
  background: #fff;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-height: 180px;
}

.paper-card:hover {
  border-color: #409eff;
  box-shadow: 0 2px 12px rgba(64, 158, 255, 0.15);
  transform: translateY(-2px);
}

.paper-title {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  line-height: 1.5;
  color: #303133;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.paper-authors {
  margin: 0;
  font-size: 13px;
  color: #909399;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.paper-abstract {
  margin: 0;
  font-size: 13px;
  color: #606266;
  line-height: 1.6;
  flex: 1;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.paper-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.paper-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  align-items: center;
}

.more-tags {
  font-size: 12px;
  color: #909399;
}

.paper-actions {
  position: absolute;
  top: 8px;
  right: 8px;
  opacity: 0;
  transition: opacity 0.2s;
}

.paper-card:hover .paper-actions {
  opacity: 1;
}
</style>
