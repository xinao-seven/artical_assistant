/**
 * 认证 API 调用封装
 */
import api from './index'
import type { AxiosResponse } from 'axios'

// ========== 类型定义 ==========

export interface RegisterRequest {
  email: string
  password: string
  username?: string
}

export interface LoginRequest {
  email: string
  password: string
}

export interface UserInfo {
  id: string
  email: string
  username?: string
  avatar?: string
  is_active: boolean
  created_at: string
}

export interface AuthResponse {
  access_token: string
  refresh_token: string
  token_type: string
  user: UserInfo
}

// ========== API 方法 ==========

/** 用户注册 */
export function register(data: RegisterRequest): Promise<AxiosResponse<UserInfo>> {
  return api.post('/auth/register', data)
}

/** 用户登录 */
export function login(data: LoginRequest): Promise<AxiosResponse<AuthResponse>> {
  return api.post('/auth/login', data)
}

/** 刷新 Token */
export function refreshToken(refreshToken: string): Promise<AxiosResponse<AuthResponse>> {
  return api.post('/auth/refresh', { refresh_token: refreshToken })
}

/** 获取当前用户信息 */
export function getMe(): Promise<AxiosResponse<UserInfo>> {
  return api.get('/auth/me')
}
