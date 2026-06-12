<script setup lang="ts">
/**
 * 个人论文库页面
 * 功能: 论文列表展示(卡片网格) / 搜索筛选 / 分页 / 上传 / 手动录入
 */
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import {
  getPapers,
  createPaper,
  deletePaper,
} from '@/api/papers'
import type {
  PaperResponse,
  PaperCreate,
  UploadResponse,
} from '@/api/papers'
import PaperList from '@/components/paper/PaperList.vue'
import PaperUpload from '@/components/paper/PaperUpload.vue'

const router = useRouter()

// ===== 数据状态 =====
const papers = ref<PaperResponse[]>([])
const loading = ref(false)
const total = ref(0)
const page = ref(1)
const size = ref(12)

// ===== 筛选状态 =====
const keyword = ref('')
const collectionFilter = ref('')
const sortField = ref('created_at')
const sortOrder = ref('desc')

// 防抖搜索
let searchTimer: ReturnType<typeof setTimeout> | null = null

// ===== 弹窗状态 =====
const showCreateDialog = ref(false)
const createForm = ref<PaperCreate>({
  title: '',
  authors: [],
  abstract: '',
  year: undefined,
  journal: '',
  tags: [],
  collection: 'default',
})
const createSubmitting = ref(false)
const authorInput = ref('')

// ===== 选项配置 =====
const collectionOptions = [
  { label: '默认', value: 'default' },
  { label: '精读', value: 'starred' },
  { label: '待读', value: 'to-read' },
  { label: '已读', value: 'read' },
]

const sortOptions = [
  { label: '添加时间', value: 'created_at' },
  { label: '发表年份', value: 'year' },
  { label: '标题', value: 'title' },
  { label: '引用数', value: 'citation_count' },
]

// ===== 生命周期 =====
onMounted(() => {
  fetchPapers()
})

// ===== 数据获取 =====
async function fetchPapers() {
  loading.value = true
  try {
    const { data } = await getPapers({
      page: page.value,
      size: size.value,
      sort: sortField.value,
      order: sortOrder.value,
      collection: collectionFilter.value || undefined,
      tag: undefined,  // 标签筛选暂不在UI中直接支持
      keyword: keyword.value || undefined,
    })
    papers.value = data.items
    total.value = data.total
  } catch {
    // 错误已在拦截器中统一处理
  } finally {
    loading.value = false
  }
}

// ===== 筛选逻辑 =====
function onKeywordInput() {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    page.value = 1
    fetchPapers()
  }, 400)
}

watch([collectionFilter, sortField, sortOrder], () => {
  page.value = 1
  fetchPapers()
})

// ===== 分页 =====
function onPageChange(p: number) {
  page.value = p
  fetchPapers()
}

function onSizeChange(s: number) {
  size.value = s
  page.value = 1
  fetchPapers()
}

// ===== 论文操作 =====
function viewDetail(paperId: string) {
  router.push({ name: 'PaperDetail', params: { id: paperId } })
}

async function onDeletePaper(paperId: string) {
  try {
    await ElMessageBox.confirm('确定要删除这篇论文吗？此操作不可恢复。', '删除确认', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消',
    })
    await deletePaper(paperId)
    ElMessage.success('论文已删除')
    // 如果当前页没数据了, 回退一页
    if (papers.value.length === 1 && page.value > 1) {
      page.value--
    }
    fetchPapers()
  } catch {
    // 用户取消, 忽略
  }
}

// ===== 上传成功回调 =====
function onUploadSuccess(_result: UploadResponse) {
  page.value = 1
  fetchPapers()
}

// ===== 手动录入 =====
function addAuthor() {
  const name = authorInput.value.trim()
  if (name && !createForm.value.authors!.includes(name)) {
    createForm.value.authors!.push(name)
  }
  authorInput.value = ''
}

function removeAuthor(index: number) {
  createForm.value.authors!.splice(index, 1)
}

function openCreateDialog() {
  createForm.value = {
    title: '',
    authors: [],
    abstract: '',
    year: undefined,
    journal: '',
    tags: [],
    collection: 'default',
  }
  authorInput.value = ''
  showCreateDialog.value = true
}

async function submitCreate() {
  if (!createForm.value.title.trim()) {
    ElMessage.warning('请输入论文标题')
    return
  }
  createSubmitting.value = true
  try {
    await createPaper(createForm.value)
    ElMessage.success('论文录入成功')
    showCreateDialog.value = false
    fetchPapers()
  } catch {
    // 错误已在拦截器中处理
  } finally {
    createSubmitting.value = false
  }
}
</script>

<template>
  <div class="library-page">
    <!-- 头部操作栏 -->
    <div class="library-header">
      <h2>我的论文库</h2>
      <div class="header-actions">
        <PaperUpload @success="onUploadSuccess" />
        <el-button @click="openCreateDialog">
          <el-icon style="margin-right: 4px"><Plus /></el-icon>
          手动录入
        </el-button>
      </div>
    </div>

    <!-- 筛选栏 -->
    <div class="filter-bar">
      <!-- 搜索 -->
      <el-input
        v-model="keyword"
        placeholder="搜索论文标题..."
        :prefix-icon="'Search'"
        clearable
        style="width: 260px"
        @input="onKeywordInput"
        @clear="fetchPapers"
      />

      <!-- 分组筛选 -->
      <el-select
        v-model="collectionFilter"
        placeholder="分组筛选"
        clearable
        style="width: 140px"
      >
        <el-option
          v-for="opt in collectionOptions"
          :key="opt.value"
          :label="opt.label"
          :value="opt.value"
        />
      </el-select>

      <!-- 排序 -->
      <div class="sort-group">
        <span class="sort-label">排序:</span>
        <el-select v-model="sortField" style="width: 120px">
          <el-option
            v-for="opt in sortOptions"
            :key="opt.value"
            :label="opt.label"
            :value="opt.value"
          />
        </el-select>
        <el-button
          :icon="sortOrder === 'desc' ? 'SortDown' : 'SortUp'"
          @click="sortOrder = sortOrder === 'desc' ? 'asc' : 'desc'"
        />
      </div>
    </div>

    <!-- 论文列表 -->
    <PaperList
      :papers="papers"
      :loading="loading"
      :total="total"
      :page="page"
      :size="size"
      @view-detail="viewDetail"
      @delete-paper="onDeletePaper"
      @page-change="onPageChange"
      @size-change="onSizeChange"
    />

    <!-- 手动录入弹窗 -->
    <el-dialog
      v-model="showCreateDialog"
      title="手动录入论文"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form :model="createForm" label-width="80px">
        <el-form-item label="标题" required>
          <el-input v-model="createForm.title" placeholder="请输入论文标题" maxlength="1000" show-word-limit />
        </el-form-item>

        <el-form-item label="作者">
          <div style="display: flex; gap: 8px; width: 100%">
            <el-input
              v-model="authorInput"
              placeholder="输入作者名，回车添加"
              @keyup.enter="addAuthor"
            />
            <el-button @click="addAuthor">添加</el-button>
          </div>
          <div v-if="createForm.authors!.length > 0" class="author-tags">
            <el-tag
              v-for="(author, idx) in createForm.authors"
              :key="idx"
              closable
              @close="removeAuthor(idx)"
              style="margin-top: 6px; margin-right: 6px"
            >
              {{ author }}
            </el-tag>
          </div>
        </el-form-item>

        <el-form-item label="摘要">
          <el-input
            v-model="createForm.abstract"
            type="textarea"
            :rows="4"
            placeholder="请输入论文摘要"
            maxlength="5000"
            show-word-limit
          />
        </el-form-item>

        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="年份">
              <el-input-number
                v-model="createForm.year"
                :min="1900"
                :max="2100"
                placeholder="发表年份"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="期刊">
              <el-input v-model="createForm.journal" placeholder="期刊/会议名称" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="标签">
          <el-input
            v-model="createForm.tags"
            placeholder="输入标签，用逗号分隔"
          />
          <div style="font-size: 12px; color: #909399; margin-top: 4px">
            多个标签请用逗号分隔，例如: 深度学习, NLP, Transformer
          </div>
        </el-form-item>

        <el-form-item label="分组">
          <el-select v-model="createForm.collection" style="width: 100%">
            <el-option
              v-for="opt in collectionOptions"
              :key="opt.value"
              :label="opt.label"
              :value="opt.value"
            />
          </el-select>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button
          type="primary"
          :loading="createSubmitting"
          @click="submitCreate"
        >
          确认录入
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.library-page {
  padding: 24px;
  max-width: 1400px;
  margin: 0 auto;
}

.library-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;

  h2 {
    margin: 0;
    font-size: 22px;
    font-weight: 600;
    color: #303133;
  }
}

.header-actions {
  display: flex;
  gap: 12px;
}

.filter-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.sort-group {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-left: auto;
}

.sort-label {
  font-size: 13px;
  color: #909399;
  white-space: nowrap;
}

.author-tags {
  display: flex;
  flex-wrap: wrap;
}
</style>
