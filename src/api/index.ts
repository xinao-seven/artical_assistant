/**
 * Axios 实例
 * - 请求拦截器: 自动附加 Token
 * - 响应拦截器: 401 自动刷新 Token, 统一错误提示
 */
import axios, { type AxiosError, type InternalAxiosRequestConfig } from 'axios'
import { ElMessage } from 'element-plus'
import { getAccessToken, setAccessToken, getRefreshToken, setRefreshToken, clearAuth } from '../utils/storage'
import router from '../router'

// 创建 axios 实例
const api = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,  // 30 秒超时
  headers: {
    'Content-Type': 'application/json',
  },
})

// 防止并发刷新 Token
let isRefreshing = false
let refreshQueue: Array<{ resolve: (token: string) => void; reject: (err: unknown) => void }> = []

// ========== 请求拦截器: 附加 Token ==========
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = getAccessToken()
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error),
)

// ========== 响应拦截器: Token 刷新 + 统一错误 ==========
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<{ detail?: string }>) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean }

    // 401 未认证 → 尝试刷新 Token
    if (error.response?.status === 401 && !originalRequest._retry) {
      const refreshToken = getRefreshToken()

      if (!refreshToken) {
        // 没有刷新令牌 → 直接踢到登录页
        clearAuth()
        router.push({ name: 'Login' })
        return Promise.reject(error)
      }

      // 防止并发刷新
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          refreshQueue.push({ resolve, reject })
        }).then((newToken) => {
          if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${newToken}`
          }
          return api(originalRequest)
        })
      }

      isRefreshing = true
      originalRequest._retry = true

      try {
        const { data } = await axios.post('/api/v1/auth/refresh', {
          refresh_token: refreshToken,
        })

        const newAccessToken = data.access_token
        const newRefreshToken = data.refresh_token

        setAccessToken(newAccessToken)
        setRefreshToken(newRefreshToken)

        // 重放队列中的请求
        refreshQueue.forEach(({ resolve }) => resolve(newAccessToken))
        refreshQueue = []

        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${newAccessToken}`
        }
        return api(originalRequest)
      } catch (refreshError) {
        refreshQueue.forEach(({ reject }) => reject(refreshError))
        refreshQueue = []
        clearAuth()
        router.push({ name: 'Login' })
        return Promise.reject(refreshError)
      } finally {
        isRefreshing = false
      }
    }

    // 其他错误 → 统一提示
    const message = error.response?.data?.detail || error.message || '请求失败，请重试'

    // 不重复提示 401 (刷新失败时已经跳转)
    if (error.response?.status !== 401) {
      ElMessage.error(message)
    }

    return Promise.reject(error)
  },
)

export default api
