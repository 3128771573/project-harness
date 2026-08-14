import { createRouter, createWebHistory } from 'vue-router'

// 路由懒加载：页面级分包，首屏只加载当前路由
const LandingView = () => import('../views/LandingView.vue')
const LoginView = () => import('../views/LoginView.vue')
const RegisterView = () => import('../views/RegisterView.vue')
const ForgotView = () => import('../views/ForgotView.vue')
const DashboardView = () => import('../views/DashboardView.vue')
const ChatView = () => import('../views/ChatView.vue')
const SettingsView = () => import('../views/SettingsView.vue')
const DemoView = () => import('../views/DemoView.vue')
const IotView = () => import('../views/IotView.vue')
const DocsView = () => import('../views/DocsView.vue')
const TermsView = () => import('../views/TermsView.vue')
const PrivacyView = () => import('../views/PrivacyView.vue')
const PricingView = () => import('../views/PricingView.vue')
const StatusView = () => import('../views/StatusView.vue')
const NotFoundView = () => import('../views/NotFoundView.vue')
const GuestbookView = () => import('../views/GuestbookView.vue')
const MessagesView = () => import('../views/MessagesView.vue')
const OAuthCallbackView = () => import('../views/OAuthCallbackView.vue')
const AdminLayout = () => import('../layouts/AdminLayout.vue')
const AdminDashboardView = () => import('../views/admin/AdminDashboardView.vue')
const AdminUsersView = () => import('../views/admin/AdminUsersView.vue')
const AdminSystemView = () => import('../views/admin/AdminSystemView.vue')
const AdminAiConfigView = () => import('../views/admin/AdminAiConfigView.vue')
const AdminUsageView = () => import('../views/admin/AdminUsageView.vue')
const AdminRolesView = () => import('../views/admin/AdminRolesView.vue')
const AdminAuditView = () => import('../views/admin/AdminAuditView.vue')
const AdminSecurityView = () => import('../views/admin/AdminSecurityView.vue')
const AdminSettingsView = () => import('../views/admin/AdminSettingsView.vue')
const AdminVisitsView = () => import('../views/admin/AdminVisitsView.vue')
const AdminNoticesView = () => import('../views/admin/AdminNoticesView.vue')
const AdminMessagesView = () => import('../views/admin/AdminMessagesView.vue')
const AdminWatermarkView = () => import('../views/admin/AdminWatermarkView.vue')
const AdminImView = () => import('../views/admin/AdminImView.vue')
const AdminExportView = () => import('../views/admin/AdminExportView.vue')

const routes = [
  { path: '/', name: 'home', component: LandingView },
  { path: '/login', name: 'login', component: LoginView },
  { path: '/register', name: 'register', component: RegisterView },
  { path: '/forgot', name: 'forgot', component: ForgotView },
  { path: '/dashboard', name: 'dashboard', component: DashboardView, meta: { requiresAuth: true } },
  { path: '/ai', name: 'ai', component: ChatView, meta: { requiresAuth: true } },
  { path: '/settings', name: 'settings', component: SettingsView, meta: { requiresAuth: true } },
  { path: '/demo', name: 'demo', component: DemoView },
  { path: '/iot', name: 'iot', component: IotView, meta: { requiresAuth: true } },
  { path: '/docs', name: 'docs', component: DocsView },
  { path: '/terms', name: 'terms', component: TermsView },
  { path: '/privacy', name: 'privacy', component: PrivacyView },
  { path: '/pricing', name: 'pricing', component: PricingView },
  { path: '/status', name: 'status', component: StatusView },
  { path: '/guestbook', name: 'guestbook', component: GuestbookView },
  { path: '/messages', name: 'messages', component: MessagesView, meta: { requiresAuth: true } },
  { path: '/oauth/callback', name: 'oauth-callback', component: OAuthCallbackView },
  { path: '/:pathMatch(.*)*', name: 'not-found', component: NotFoundView },
  {
    path: '/admin',
    component: AdminLayout,
    meta: { requiresAuth: true, requiresAdmin: true },
    children: [
      { path: '', redirect: '/admin/dashboard' },
      { path: 'dashboard', name: 'admin-dashboard', component: AdminDashboardView },
      { path: 'users', name: 'admin-users', component: AdminUsersView },
      { path: 'system', name: 'admin-system', component: AdminSystemView },
      { path: 'ai-config', name: 'admin-ai-config', component: AdminAiConfigView },
      { path: 'usage', name: 'admin-usage', component: AdminUsageView },
      { path: 'roles', name: 'admin-roles', component: AdminRolesView },
      { path: 'audit', name: 'admin-audit', component: AdminAuditView },
      { path: 'security', name: 'admin-security', component: AdminSecurityView },
      { path: 'settings', name: 'admin-settings', component: AdminSettingsView },
      { path: 'visits', name: 'admin-visits', component: AdminVisitsView },
      { path: 'notices', name: 'admin-notices', component: AdminNoticesView },
      { path: 'messages', name: 'admin-messages', component: AdminMessagesView },
      { path: 'watermark', name: 'admin-watermark', component: AdminWatermarkView, meta: { requiresSuperAdmin: true } },
      { path: 'im', name: 'admin-im', component: AdminImView },
      { path: 'exports', name: 'admin-exports', component: AdminExportView, meta: { requiresSuperAdmin: true } },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

function getUser() {
  try {
    return JSON.parse(localStorage.getItem('harness_user') || 'null')
  } catch {
    return null
  }
}

router.beforeEach((to) => {
  const token = localStorage.getItem('harness_access')
  if (to.meta.requiresAuth && !token) {
    return { name: 'login' }
  }
  // Admin 路由: 检查角色（前端拦截只是体验优化，真正的权限由后端 RBAC 保证）
  if (to.meta.requiresAdmin) {
    const user = getUser()
    if (!user || !['admin', 'super_admin'].includes(user.role)) {
      return { name: 'dashboard' }
    }
  }
  if (to.meta.requiresSuperAdmin) {
    const user = getUser()
    if (!user || user.role !== 'super_admin') {
      return { name: 'dashboard' }
    }
  }
  if ((to.name === 'login' || to.name === 'register') && token) {
    return { name: 'dashboard' }
  }
})

// ===== 页面访问上报（节流 2s，不记录 admin 内部路由） =====
let lastReport = 0
router.afterEach((to) => {
  const now = Date.now()
  if (now - lastReport < 2000) return
  if (to.path.startsWith('/admin')) return
  lastReport = now
  const token = localStorage.getItem('harness_access')
  const body = JSON.stringify({ path: to.path, referer: document.referrer || null })
  if (navigator.sendBeacon) {
    navigator.sendBeacon('/api/v1/system/visit', new Blob([body], { type: 'application/json' }))
  } else {
    fetch('/api/v1/system/visit', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) },
      body,
      keepalive: true,
    }).catch(() => {})
  }
})

export default router
