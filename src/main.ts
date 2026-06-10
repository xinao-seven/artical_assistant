/**
 * 应用入口
 * 注册 Vue 插件: Element Plus, Router, Pinia
 */
import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import 'element-plus/theme-chalk/dark/css-vars.css'
import 'katex/dist/katex.min.css'
import 'highlight.js/styles/github-dark.css'

import App from './App.vue'
import router from './router'
import pinia from './stores'
import './style.css'

const app = createApp(App)

// 注册插件
app.use(ElementPlus, { locale: undefined /* 使用默认中文 */ })
app.use(router)
app.use(pinia)

app.mount('#app')
