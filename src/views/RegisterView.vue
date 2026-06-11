<script setup lang="ts">
/**
 * 注册页面
 * - 邮箱 + 密码 + 确认密码 + 可选用户名
 * - 注册成功后自动登录并跳转仪表盘
 */
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { register, login } from '../api/auth'
import { useUserStore } from '../stores/user'

const router = useRouter()
const userStore = useUserStore()

// ===== 表单引用 =====
const registerFormRef = ref<FormInstance>()

// ===== 表单数据 =====
const registerForm = reactive({
  email: '',
  username: '',
  password: '',
  confirmPassword: '',
})

// ===== 自定义验证: 确认密码 =====
const validateConfirmPassword = (_rule: any, value: string, callback: Function) => {
  if (value !== registerForm.password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

// ===== 表单验证规则 =====
const registerRules: FormRules = {
  email: [
    { required: true, message: '请输入邮箱地址', trigger: 'blur' },
    { type: 'email', message: '请输入有效的邮箱地址', trigger: ['blur', 'change'] },
  ],
  username: [
    { max: 100, message: '用户名不能超过 100 个字符', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少 6 位', trigger: 'blur' },
    { max: 128, message: '密码不能超过 128 位', trigger: 'blur' },
  ],
  confirmPassword: [
    { required: true, message: '请再次输入密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: ['blur', 'change'] },
  ],
}

// ===== 状态 =====
const isLoading = ref(false)
const errorMessage = ref('')

// ===== 注册处理 =====
async function handleRegister() {
  if (!registerFormRef.value) return

  // 表单验证
  const valid = await registerFormRef.value.validate().catch(() => false)
  if (!valid) return

  isLoading.value = true
  errorMessage.value = ''

  try {
    // 1. 注册
    await register({
      email: registerForm.email,
      password: registerForm.password,
      username: registerForm.username || undefined,
    })

    // 2. 注册成功后自动登录
    const { data } = await login({
      email: registerForm.email,
      password: registerForm.password,
    })

    // 3. 存储认证信息
    userStore.login(data.access_token, data.refresh_token, data.user)

    ElMessage.success('注册成功！欢迎加入！')
    router.push('/dashboard')
  } catch (err: any) {
    const detail = err?.response?.data?.detail
    if (detail) {
      errorMessage.value = detail
    } else {
      errorMessage.value = '注册失败，请稍后重试'
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
        <p class="auth-subtitle">创建新账号，开启学术探索之旅</p>
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

      <!-- 注册表单 -->
      <el-form
        ref="registerFormRef"
        :model="registerForm"
        :rules="registerRules"
        label-position="top"
        @keyup.enter="handleRegister"
      >
        <el-form-item label="邮箱" prop="email">
          <el-input
            v-model="registerForm.email"
            placeholder="请输入邮箱地址"
            size="large"
          />
        </el-form-item>

        <el-form-item label="用户名 (选填)" prop="username">
          <el-input
            v-model="registerForm.username"
            placeholder="给自己起个名字吧"
            size="large"
          />
        </el-form-item>

        <el-form-item label="密码" prop="password">
          <el-input
            v-model="registerForm.password"
            type="password"
            placeholder="至少 6 位密码"
            show-password
            size="large"
          />
        </el-form-item>

        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input
            v-model="registerForm.confirmPassword"
            type="password"
            placeholder="请再次输入密码"
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
            @click="handleRegister"
          >
            {{ isLoading ? '注册中...' : '注 册' }}
          </el-button>
        </el-form-item>
      </el-form>

      <!-- 跳转登录 -->
      <div class="auth-footer">
        <span>已有账号？</span>
        <router-link to="/login" class="auth-link">立即登录</router-link>
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
