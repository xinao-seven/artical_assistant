# 前端设计文档

## 1. 路由设计

```
/                        → 重定向到 /dashboard
/login                   → LoginView        (无需认证)
/register                → RegisterView     (无需认证)
/dashboard               → DashboardView    (需认证)
/search                  → SearchView       (需认证)
/papers/:id              → PaperDetailView  (需认证)
/papers/:id/citations    → CitationGraphView(需认证)
/library                 → LibraryView      (需认证)
/settings                → SettingsView     (需认证)
```

### 路由守卫逻辑
```typescript
router.beforeEach(async (to, from) => {
  const userStore = useUserStore()
  const publicPages = ['/login', '/register']

  if (!userStore.isLoggedIn && !publicPages.includes(to.path)) {
    return '/login'
  }
  if (userStore.isLoggedIn && publicPages.includes(to.path)) {
    return '/dashboard'
  }
})
```

## 2. 组件树

```
App.vue
├── LoginView.vue                    # 登录页
│   └── el-form (email + password)
├── RegisterView.vue                 # 注册页
│   └── el-form (email + password + confirm)
├── AppLayout.vue                    # 主布局（认证后）
│   ├── AppHeader.vue               # 顶栏
│   │   ├── Logo + 标题
│   │   ├── 导航菜单 (Dashboard/Search/Library)
│   │   ├── 暗色模式切换
│   │   └── 用户头像下拉 (个人信息/设置/退出)
│   ├── AppSidebar.vue              # 侧边栏
│   │   └── el-menu (垂直导航)
│   └── router-view
│       ├── DashboardView.vue       # 仪表盘
│       │   ├── 统计卡片 (论文数/搜索次数/追踪数)
│       │   ├── 最近搜索历史
│       │   └── 最近添加的论文
│       ├── SearchView.vue          # 搜索页
│       │   ├── SearchBar.vue       # 搜索输入框
│       │   ├── SearchFilters.vue   # 筛选器面板
│       │   └── PaperList.vue       # 结果列表 (虚拟滚动)
│       │       └── PaperCard.vue × N
│       ├── PaperDetailView.vue     # 论文详情
│       │   ├── 论文元信息区
│       │   ├── PDF预览 (pdfjs-dist)
│       │   ├── SummaryStream.vue   # AI摘要 (SSE流式)
│       │   ├── TranslatePanel.vue  # 翻译面板
│       │   └── 操作按钮组
│       ├── LibraryView.vue         # 论文库
│       │   ├── 筛选栏 (标签/分组)
│       │   └── PaperList.vue
│       ├── CitationGraphView.vue   # 引用图谱
│       │   └── ECharts 力导向图
│       └── SettingsView.vue        # 设置
│           ├── 个人资料编辑
│           └── 追踪管理
└── MarkdownViewer.vue              # 通用Markdown渲染
```

## 3. 状态管理 (Pinia)

### 3.1 userStore
```typescript
interface UserState {
  user: User | null
  accessToken: string
  refreshToken: string
  isLoggedIn: boolean
}
// Actions: login, register, logout, refreshToken, fetchProfile
```

### 3.2 paperStore
```typescript
interface PaperState {
  currentPaper: Paper | null
  summary: string
  isSummaryLoading: boolean
  libraryPapers: Paper[]
  libraryTotal: number
  libraryPage: number
}
// Actions: fetchPaper, fetchLibrary, addToLibrary, removeFromLibrary
```

### 3.3 searchStore
```typescript
interface SearchState {
  query: string
  filters: SearchFilters
  results: SearchResult[]
  total: number
  page: number
  isLoading: boolean
  history: SearchHistoryItem[]
}
// Actions: search, loadMore, fetchHistory, deleteHistory
```

## 4. SSE 流式渲染实现

### 4.1 useSSE composable

```typescript
// composables/useSSE.ts
interface UseSSEOptions {
  url: string | (() => string)
  onMessage: (token: string) => void
  onStep?: (step: string, message: string) => void
  onError?: (error: Error) => void
  onDone?: () => void
}

function useSSE(options: UseSSEOptions) {
  const isStreaming = ref(false)
  const abortController = ref<AbortController | null>(null)
  
  const start = async () => {
    isStreaming.value = true
    abortController.value = new AbortController()
    
    const url = typeof options.url === 'function' ? options.url() : options.url
    const response = await fetch(url, {
      headers: { 'Authorization': `Bearer ${token}` },
      signal: abortController.value.signal
    })
    
    const reader = response.body!.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    
    while (true) {
      const { done, value } = await reader.read()
      if (done) { options.onDone?.(); break }
      
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''
      
      for (const line of lines) {
        if (line.startsWith('event: step')) { /* parse step event */ }
        else if (line.startsWith('data: ')) {
          const data = line.slice(6)
          if (data === '[DONE]') { options.onDone?.(); break }
          try { options.onMessage(JSON.parse(data).token) }
          catch { options.onMessage(data) }
        }
      }
    }
    isStreaming.value = false
  }
  
  const stop = () => abortController.value?.abort()
  
  return { isStreaming, start, stop }
}
```

### 4.2 SummaryStream.vue 使用示例

```vue
<template>
  <div class="summary-stream">
    <MarkdownViewer :content="accumulatedText" />
    <span v-if="isStreaming" class="cursor-blink">|</span>
  </div>
</template>

<script setup lang="ts">
const accumulatedText = ref('')
const { isStreaming, start } = useSSE({
  url: () => `/api/v1/papers/${props.paperId}/summary`,
  onMessage: (token) => { accumulatedText.value += token },
  onDone: () => { /* 隐藏光标 */ }
})
</script>
```

## 5. 虚拟列表

### 5.1 使用 vue-virtual-scroller

```vue
<template>
  <RecycleScroller
    :items="papers"
    :item-size="180"
    key-field="id"
    v-slot="{ item }"
    :buffer="200"
  >
    <PaperCard :paper="item" />
  </RecycleScroller>
</template>
```

### 5.2 滚动加载更多

```typescript
const onScrollEnd = () => {
  if (searchStore.total > searchStore.results.length) {
    searchStore.loadMore()
  }
}
```

## 6. Markdown 渲染配置

```typescript
// composables/useMarkdown.ts
import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js'
import katex from 'katex'

const md = new MarkdownIt({
  html: false,           // XSS 防护：禁用HTML标签
  linkify: true,
  typographer: true,
  highlight: (code, lang) => {
    if (lang && hljs.getLanguage(lang)) {
      return hljs.highlight(code, { language: lang }).value
    }
    return hljs.highlightAuto(code).value
  }
})

// 数学公式 (katex)
md.use(require('markdown-it-texmath'), {
  engine: katex,
  delimiters: ['dollars', 'brackets']
})

export function useMarkdown() {
  const render = (text: string) => md.render(text)
  return { render }
}
```

## 7. 大文件上传（分片 + 进度）

```typescript
// 分片上传
const CHUNK_SIZE = 5 * 1024 * 1024  // 5MB
const uploadFile = async (file: File) => {
  const chunks = Math.ceil(file.size / CHUNK_SIZE)
  const fileId = await SparkMD5.hash(file)  // 用于秒传校验
  
  for (let i = 0; i < chunks; i++) {
    const chunk = file.slice(i * CHUNK_SIZE, (i + 1) * CHUNK_SIZE)
    const formData = new FormData()
    formData.append('file', chunk)
    formData.append('chunk_index', String(i))
    formData.append('total_chunks', String(chunks))
    formData.append('file_id', fileId)
    
    await axios.post('/api/v1/upload/chunk', formData, {
      onUploadProgress: (e) => {
        // 更新进度条
      }
    })
  }
}
```

## 8. 错误处理

### 8.1 axios 拦截器

```typescript
// api/index.ts
const api = axios.create({ baseURL: '/api/v1' })

// 请求拦截器：附加 Token
api.interceptors.request.use((config) => {
  const token = storage.getAccessToken()
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// 响应拦截器：统一错误处理 + Token刷新
api.interceptors.response.use(
  (res) => res,
  async (error) => {
    if (error.response?.status === 401) {
      // 尝试刷新 Token
      try {
        const newToken = await authApi.refresh()
        storage.setAccessToken(newToken)
        error.config.headers.Authorization = `Bearer ${newToken}`
        return api(error.config)  // 重试原请求
      } catch {
        userStore.logout()
        router.push('/login')
      }
    }
    // 统一错误提示
    ElMessage.error(error.response?.data?.detail || '请求失败')
    return Promise.reject(error)
  }
)
```

## 9. 暗色模式

```typescript
// Element Plus 暗色模式切换
const isDark = useDark()
const toggleDark = useToggle(isDark)

// 在 App.vue 中
watchEffect(() => {
  document.documentElement.classList.toggle('dark', isDark.value)
})
```

```css
/* style.css */
:root {
  --bg-primary: #ffffff;
  --text-primary: #303133;
}
html.dark {
  --bg-primary: #141414;
  --text-primary: #e5eaf0;
}
```
