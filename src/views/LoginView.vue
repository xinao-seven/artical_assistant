<script setup lang="ts">
/**
 * 登录页面
 * - 邮箱 + 密码登录
 * - 登录成功后跳转到目标页面或仪表盘
 */
import { ref, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { login } from '../api/auth'
import { useUserStore } from '../stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

// ===== 表单引用 =====
const loginFormRef = ref<FormInstance>()

// ===== 表单数据 =====
const loginForm = reactive({
  email: '',
  password: '',
})

// ===== 表单验证规则 =====
const loginRules: FormRules = {
  email: [
    { required: true, message: '请输入邮箱地址', trigger: 'blur' },
    { type: 'email', message: '请输入有效的邮箱地址', trigger: ['blur', 'change'] },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少 6 位', trigger: 'blur' },
  ],
}

// ===== 状态 =====
const isLoading = ref(false)
const errorMessage = ref('')

// ===== 登录处理 =====
async function handleLogin() {
  if (!loginFormRef.value) return

  // 表单验证
  const valid = await loginFormRef.value.validate().catch(() => false)
  if (!valid) return

  isLoading.value = true
  errorMessage.value = ''

  try {
    const { data } = await login({
      email: loginForm.email,
      password: loginForm.password,
    })

    // 存储认证信息到 Pinia Store (自动持久化到 localStorage)
    userStore.login(data.access_token, data.refresh_token, data.user)

    ElMessage.success('登录成功！')

    // 跳转到目标页面 (如果有 redirect 参数) 或仪表盘
    const redirectPath = (route.query.redirect as string) || '/dashboard'
    router.push(redirectPath)
  } catch (err: any) {
    const detail = err?.response?.data?.detail
    if (detail) {
      errorMessage.value = detail
    } else {
      errorMessage.value = '登录失败，请检查网络连接'
    }
    ElMessage.error(errorMessage.value)
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <div class="auth-page">
    <div class="auth-card">
      <!-- Logo + 标题 -->
      <div class="auth-header">
        <h1 class="auth-logo">📄 论文AI助手</h1>
        <p class="auth-subtitle">登录您的账号，开始探索学术论文</p>
      </div>

      <!-- 错误提示 -->
      <el-alert
        v-if="errorMessage"
        :title="errorMessage"
        type="error"
        show-icon
        :closable="true"
        @close="errorMessage = ''"
        class="auth-alert"
      />

      <!-- 登录表单 -->
      <el-form
        ref="loginFormRef"
        :model="loginForm"
        :rules="loginRules"
        label-position="top"
        @keyup.enter="handleLogin"
      >
        <el-form-item label="邮箱" prop="email">
          <el-input
            v-model="loginForm.email"
            placeholder="请输入邮箱地址"
            size="large"
          />
        </el-form-item>

        <el-form-item label="密码" prop="password">
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="请输入密码"
            show-password
            size="large"
          />
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            size="large"
            :loading="isLoading"
            class="auth-btn"
            @click="handleLogin"
          >
            {{ isLoading ? '登录中...' : '登 录' }}
          </el-button>
        </el-form-item>
      </el-form>

      <!-- 跳转注册 -->
      <div class="auth-footer">
        <span>还没有账号？</span>
        <router-link to="/register" class="auth-link">立即注册</router-link>
      </div>
    </div>
  </div>
</template>

<style scoped>
.auth-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.auth-card {
  width: 420px;
  padding: 40px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
}

.auth-header {
  text-align: center;
  margin-bottom: 32px;
}

.auth-logo {
  font-size: 28px;
  font-weight: 700;
  color: #303133;
  margin: 0 0 8px 0;
}

.auth-subtitle {
  color: #909399;
  font-size: 14px;
  margin: 0;
}

.auth-alert {
  margin-bottom: 20px;
}

.auth-btn {
  width: 100%;
}

.auth-footer {
  text-align: center;
  margin-top: 20px;
  font-size: 14px;
  color: #909399;
}

.auth-link {
  color: #409eff;
  text-decoration: none;
  margin-left: 4px;
  font-weight: 500;
}

.auth-link:hover {
  text-decoration: underline;
}
</style>
