# 前端双 Token 刷新与防止并发刷新

> 相关文件：`src/api/index.ts`、`src/utils/storage.ts`、`src/stores/user.ts`

---

## 架构总览

```
请求A ──(401)──→ Axios 拦截器 ──→ 发起刷新 (isRefreshing=true)
                                         │
请求B ──(401)──→ Axios 拦截器 ──→ 检测 isRefreshing=true → 加入队列等待
                                         │
请求C ──(401)──→ Axios 拦截器 ──→ 检测 isRefreshing=true → 加入队列等待
                                         │
                                   刷新成功 ↓
                                         │
                                   存储新 Token
                                   遍历队列 resolve(newToken)
                                   A、B、C 用新 Token 重试
```

---

## 第 1 层：Token 存储 (`utils/storage.ts`)

两个 Token 分别存在 `localStorage` 中，页面刷新不丢失：

| Key | 内容 | 生命周期 |
|-----|------|----------|
| `access_token` | JWT 访问令牌 | 30 分钟 |
| `refresh_token` | JWT 刷新令牌 | 7 天 |

```typescript
getAccessToken()    // 读取
setAccessToken()    // 写入
getRefreshToken()
setRefreshToken()
clearAuth()         // 清除全部（登出时）
```

---

## 第 2 层：请求拦截器 — 自动附带 Token

每次请求前从 `localStorage` 读取 `access_token`，自动附加到 `Authorization` 请求头：

```typescript
api.interceptors.request.use((config) => {
  const token = getAccessToken()
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})
```

---

## 第 3 层：响应拦截器 — 核心刷新逻辑

### 场景 1：单个 401 → 正常刷新

```typescript
// 收到 401 → 检查是否有 refresh_token
if (error.response?.status === 401 && !originalRequest._retry) {
  const refreshToken = getRefreshToken()

  if (!refreshToken) {
    // 无 refresh_token → 直接踢到登录页
    clearAuth()
    router.push({ name: 'Login' })
    return Promise.reject(error)
  }

  // isRefreshing = false → 由本请求发起刷新
  isRefreshing = true          // 🔒 加锁
  originalRequest._retry = true // 标记，防死循环

  // 用原生 axios 调刷新接口（避免走本实例拦截器导致递归）
  const { data } = await axios.post('/api/v1/auth/refresh', {
    refresh_token: refreshToken,
  })

  // 存储新 Token
  setAccessToken(data.access_token)
  setRefreshToken(data.refresh_token)

  // 用新 Token 重放原请求
  originalRequest.headers.Authorization = `Bearer ${data.access_token}`
  return api(originalRequest)
}
```

### 场景 2：并发 401 → 排队等待（核心防并发设计）

```typescript
let isRefreshing = false   // 🚦 刷新锁
let refreshQueue: Array<{
  resolve: (token: string) => void
  reject: (err: unknown) => void
}> = []                     // 📋 等待队列

// 收到 401 但已有请求在刷新 → 排队
if (isRefreshing) {
  return new Promise((resolve, reject) => {
    refreshQueue.push({ resolve, reject })
  }).then((newToken) => {
    // 被唤醒后，用新 Token 重试
    originalRequest.headers.Authorization = `Bearer ${newToken}`
    return api(originalRequest)
  })
}
```

**工作原理**：
1. 请求 A 收到 401 → `isRefreshing=false` → 设为 `true`，发起刷新
2. 请求 B 收到 401 → `isRefreshing=true` → 把自己的 `resolve/reject` 放入队列，挂起
3. 请求 C 收到 401 → 同理挂起
4. 刷新完成 → `refreshQueue.forEach(resolve)` → B、C 被唤醒，用新 Token 重试

### 场景 3：刷新完成后 — 唤醒队列

```typescript
// ✅ 刷新成功 → 唤醒所有等待的请求
refreshQueue.forEach(({ resolve }) => resolve(newAccessToken))
refreshQueue = []

// ❌ 刷新失败 → 全部 reject，跳转登录
refreshQueue.forEach(({ reject }) => reject(refreshError))
refreshQueue = []
clearAuth()
router.push({ name: 'Login' })
```

---

## 关键设计决策

### 为什么 `/auth/refresh` 用原生 `axios.post` 而不是 `api.post`？

```typescript
// ✅ 正确：原生 axios，不触发拦截器
const { data } = await axios.post('/api/v1/auth/refresh', { ... })

// ❌ 错误：api 实例会再次触发请求/响应拦截器
// 如果 refresh_token 也过期返回 401 → 拦截器会无限递归调用刷新
```

### 为什么需要 `_retry` 标记？

防止刷新后的重试请求再次 401 时陷入死循环。标记为 `_retry=true` 的请求不会再尝试刷新。

### 为什么用 Promise 队列而不是简单重试？

如果不用队列，并发场景下多个请求会同时发起多次 `/auth/refresh`，导致：
- 多余的网络请求
- 前面的 refresh_token 被后面的覆盖（令牌轮换冲突）

---

## 完整流程图

```
请求发出
  │
  ├─ 请求拦截器: 附加 access_token
  │
  ▼
响应回来
  │
  ├─ 200 → 正常返回
  │
  ├─ 401 → 是 _retry 请求? ──是──→ 放弃，跳转登录
  │           │
  │           否
  │           │
  │         有 refresh_token? ──无──→ 跳转登录
  │           │
  │           有
  │           │
  │         isRefreshing? ──是──→ 加入等待队列 → 被唤醒 → 用新 Token 重试
  │           │
  │           否
  │           │
  │         isRefreshing = true (加锁)
  │           发起 POST /auth/refresh
  │           │
  │      ┌────┴────┐
  │    成功        失败
  │      │          │
  │   存储新Token   清空队列
  │   唤醒队列      clearAuth()
  │   重放请求      跳转登录
  └──────────────────────┘
```
