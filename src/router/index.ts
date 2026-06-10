/**
 * Vue Router 路由配置
 * 定义所有页面路由和导航守卫
 */
import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '../stores/user'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      redirect: '/dashboard',
    },
    {
      path: '/login',
      name: 'Login',
      // 懒加载: 组件使用时才加载 (代码分割)
      component: () => import('../views/LoginView.vue'),
      meta: { requiresAuth: false, title: '登录' },
    },
    {
      path: '/register',
      name: 'Register',
      component: () => import('../views/RegisterView.vue'),
      meta: { requiresAuth: false, title: '注册' },
    },
    {
      path: '/dashboard',
      name: 'Dashboard',
      component: () => import('../views/DashboardView.vue'),
      meta: { requiresAuth: true, title: '仪表盘' },
    },
    {
      path: '/search',
      name: 'Search',
      component: () => import('../views/SearchView.vue'),
      meta: { requiresAuth: true, title: '论文检索' },
    },
    {
      path: '/papers/:id',
      name: 'PaperDetail',
      component: () => import('../views/PaperDetailView.vue'),
      meta: { requiresAuth: true, title: '论文详情' },
    },
    {
      path: '/papers/:id/citations',
      name: 'CitationGraph',
      component: () => import('../views/CitationGraphView.vue'),
      meta: { requiresAuth: true, title: '引用图谱' },
    },
    {
      path: '/library',
      name: 'Library',
      component: () => import('../views/LibraryView.vue'),
      meta: { requiresAuth: true, title: '论文库' },
    },
    {
      path: '/settings',
      name: 'Settings',
      component: () => import('../views/SettingsView.vue'),
      meta: { requiresAuth: true, title: '设置' },
    },
    {
      // 404 未匹配的路由
      path: '/:pathMatch(.*)*',
      name: 'NotFound',
      component: () => import('../views/NotFoundView.vue'),
      meta: { title: '404' },
    },
  ],
})

// ===== 全局前置守卫: 检查认证状态 =====
router.beforeEach((to, _from, next) => {
  // 设置页面标题
  document.title = `${to.meta.title} - 论文AI助手`

  const userStore = useUserStore()
  const requiresAuth = to.meta.requiresAuth !== false

  if (requiresAuth && !userStore.isLoggedIn) {
    // 需要认证但未登录 → 跳转登录页
    next({ name: 'Login', query: { redirect: to.fullPath } })
  } else if (!requiresAuth && userStore.isLoggedIn && ['Login', 'Register'].includes(to.name as string)) {
    // 已登录用户访问登录/注册页 → 跳转仪表盘
    next({ name: 'Dashboard' })
  } else {
    next()
  }
})

export default router
