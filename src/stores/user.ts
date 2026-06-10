/**
 * 用户状态管理 (Pinia Store)
 * 管理当前用户信息和登录状态
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getAccessToken, setAccessToken, setRefreshToken, getUserInfo, setUserInfo, clearAuth } from '../utils/storage'

interface User {
  id: string
  email: string
  username?: string
  avatar?: string
  created_at: string
}

export const useUserStore = defineStore('user', () => {
  // ===== 状态 =====
  const user = ref<User | null>(getUserInfo() as User | null)
  const accessToken = ref<string | null>(getAccessToken())

  // ===== 计算属性 =====
  const isLoggedIn = computed(() => !!accessToken.value && !!user.value)

  // ===== 操作 =====

  /** 登录: 保存 Token 和用户信息 */
  function login(access: string, refresh: string, userInfo: User) {
    accessToken.value = access
    user.value = userInfo
    setAccessToken(access)
    setRefreshToken(refresh)
    setUserInfo(userInfo)
  }

  /** 登出: 清除所有认证信息 */
  function logout() {
    accessToken.value = null
    user.value = null
    clearAuth()
  }

  /** 更新用户信息 */
  function updateUser(partial: Partial<User>) {
    if (user.value) {
      user.value = { ...user.value, ...partial }
      setUserInfo(user.value)
    }
  }

  return { user, accessToken, isLoggedIn, login, logout, updateUser }
})
