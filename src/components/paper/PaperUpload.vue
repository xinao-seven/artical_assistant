<script setup lang="ts">
/**
 * 论文上传组件
 * 手动拖拽区 + 点击选择，完全可控的上传体验
 */
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Upload, UploadFilled } from '@element-plus/icons-vue'
import { uploadPdf } from '@/api/papers'
import type { UploadResponse } from '@/api/papers'

const emit = defineEmits<{
  success: [result: UploadResponse]
}>()

// ===== 状态 =====
const dialogVisible = ref(false)
const uploading = ref(false)
const uploadProgress = ref(0)
const uploadResult = ref<UploadResponse | null>(null)
const isDragging = ref(false)
const selectedFile = ref<File | null>(null)

const MAX_SIZE_MB = 50

// ===== 文件校验 =====
function validateFile(file: File): boolean {
  const isPdf = file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf')
  if (!isPdf) {
    ElMessage.error('仅支持 PDF 文件格式')
    return false
  }

  const sizeMB = file.size / 1024 / 1024
  if (sizeMB > MAX_SIZE_MB) {
    ElMessage.error(`文件大小 (${sizeMB.toFixed(1)}MB) 超过限制 (${MAX_SIZE_MB}MB)`)
    return false
  }

  return true
}

// ===== 拖拽处理 =====
function onDragOver(e: DragEvent) {
  e.preventDefault()
  isDragging.value = true
}

function onDragLeave() {
  isDragging.value = false
}

function onDrop(e: DragEvent) {
  e.preventDefault()
  isDragging.value = false

  const file = e.dataTransfer?.files?.[0]
  if (!file) return

  if (validateFile(file)) {
    selectedFile.value = file
    startUpload(file)
  }
}

// ===== 点击选择 =====
function onFileSelect(e: Event) {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return

  if (validateFile(file)) {
    selectedFile.value = file
    startUpload(file)
  }

  // 重置 input，允许重复选择同一文件
  input.value = ''
}

// ===== 执行上传 =====
async function startUpload(file: File) {
  uploading.value = true
  uploadProgress.value = 0
  uploadResult.value = null

  try {
    // 模拟进度
    const progressTimer = setInterval(() => {
      if (uploadProgress.value < 90) {
        uploadProgress.value += 10
      }
    }, 300)

    const { data } = await uploadPdf(file)

    clearInterval(progressTimer)
    uploadProgress.value = 100
    uploadResult.value = data

    ElMessage.success(`论文「${data.title}」上传成功`)
    emit('success', data)

    // 成功后 1.5 秒自动关闭
    setTimeout(() => {
      closeDialog()
    }, 1500)

  } catch (error: any) {
    const detail = error?.response?.data?.detail || '上传失败，请重试'
    ElMessage.error(detail)
    selectedFile.value = null
  } finally {
    uploading.value = false
  }
}

// ===== 关闭弹窗 =====
function closeDialog() {
  dialogVisible.value = false
  uploading.value = false
  uploadProgress.value = 0
  uploadResult.value = null
  selectedFile.value = null
  isDragging.value = false
}

// ===== 格式化 =====
const progressStatus = computed(() => {
  if (uploadResult.value) return 'success'
  return ''
})

function formatSize(bytes: number): string {
  const mb = bytes / 1024 / 1024
  if (mb >= 1) return `${mb.toFixed(1)} MB`
  return `${(bytes / 1024).toFixed(1)} KB`
}
</script>

<template>
  <div class="paper-upload">
    <!-- 触发按钮 -->
    <el-button type="primary" @click="dialogVisible = true">
      <el-icon style="margin-right: 4px"><Upload /></el-icon>
      上传论文
    </el-button>

    <!-- 上传弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      title="上传论文 PDF"
      width="520px"
      :close-on-click-modal="false"
      @close="closeDialog"
    >
      <!-- 拖拽上传区 (未上传/未完成时显示) -->
      <div
        v-if="!uploadResult"
        class="drop-zone"
        :class="{ 'is-dragging': isDragging, 'is-uploading': uploading }"
        @dragover="onDragOver"
        @dragleave="onDragLeave"
        @drop="onDrop"
      >
        <template v-if="!uploading">
          <el-icon class="upload-icon"><UploadFilled /></el-icon>
          <div class="upload-text">
            <p>将 PDF 文件拖到此处，或
              <label class="file-label">
                点击选择
                <input
                  type="file"
                  class="file-input"
                  accept=".pdf"
                  @change="onFileSelect"
                />
              </label>
            </p>
            <p class="upload-hint">支持最大 {{ MAX_SIZE_MB }}MB 的 PDF 文件</p>
          </div>

          <!-- 已选文件预览 -->
          <div v-if="selectedFile && !uploading" class="file-preview">
            <span class="file-name">{{ selectedFile.name }}</span>
            <span class="file-size">{{ formatSize(selectedFile.size) }}</span>
          </div>
        </template>
      </div>

      <!-- 进度条 -->
      <div v-if="uploading" class="progress-area">
        <el-progress
          :percentage="uploadProgress"
          :status="progressStatus"
          :stroke-width="16"
          :text-inside="true"
        />
        <p class="progress-hint">
          {{ selectedFile?.name }} — 正在上传并解析论文...
        </p>
      </div>

      <!-- 上传成功信息 -->
      <div v-if="uploadResult" class="result-area">
        <el-result icon="success" title="上传成功" :sub-title="uploadResult.title">
          <template #extra>
            <div class="result-detail">
              <p v-if="uploadResult.authors?.length">
                <strong>作者:</strong> {{ uploadResult.authors.join(', ') }}
              </p>
              <p v-if="uploadResult.pages_count">
                <strong>页数:</strong> {{ uploadResult.pages_count }}
              </p>
            </div>
          </template>
        </el-result>
      </div>

      <!-- 底部按钮 -->
      <template #footer>
        <el-button @click="closeDialog" :disabled="uploading">
          {{ uploadResult ? '关闭' : '取消' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
/* ===== 拖拽区 ===== */
.drop-zone {
  border: 2px dashed #dcdfe6;
  border-radius: 8px;
  padding: 40px 20px;
  text-align: center;
  transition: all 0.3s;
  background: #fafafa;
  cursor: pointer;
}

.drop-zone.is-dragging {
  border-color: #409eff;
  background: #ecf5ff;
}

.drop-zone.is-uploading {
  display: none;
}

.upload-icon {
  font-size: 48px;
  color: #c0c4cc;
}

.drop-zone.is-dragging .upload-icon {
  color: #409eff;
}

.upload-text p {
  margin: 8px 0 0;
  font-size: 14px;
  color: #606266;
}

.upload-hint {
  font-size: 12px !important;
  color: #c0c4cc !important;
}

.file-label {
  color: #409eff;
  cursor: pointer;
  text-decoration: underline;
}

.file-input {
  position: absolute;
  opacity: 0;
  width: 0;
  height: 0;
}

/* ===== 文件预览 ===== */
.file-preview {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin-top: 12px;
  padding: 6px 14px;
  background: #ecf5ff;
  border-radius: 6px;
  font-size: 13px;
}

.file-name {
  color: #409eff;
  font-weight: 500;
  max-width: 260px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-size {
  color: #909399;
}

/* ===== 进度条 ===== */
.progress-area {
  text-align: center;
  padding: 20px 0;
}

.progress-hint {
  margin-top: 12px;
  font-size: 13px;
  color: #909399;
}

/* ===== 结果 ===== */
.result-area {
  margin-top: 16px;
}

.result-detail {
  text-align: left;
  max-width: 300px;
  margin: 0 auto;
  font-size: 13px;
  color: #606266;
  line-height: 1.8;
}
</style>
