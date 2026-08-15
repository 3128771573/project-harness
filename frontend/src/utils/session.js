// 登录会话统一工具：保存/清除/读取（LoginView/RegisterView 后续可迁移到此）
export function saveSession(data) {
  localStorage.setItem('harness_access', data.access_token)
  localStorage.setItem('harness_refresh', data.refresh_token)
  localStorage.setItem('harness_user', JSON.stringify(data.user))
}

export function clearSession() {
  localStorage.removeItem('harness_access')
  localStorage.removeItem('harness_refresh')
  localStorage.removeItem('harness_user')
}

// 登出：吊销服务端 refresh token + 清理本地会话（安全基线 §1.4：防 refresh 盗用窗口）
export async function logoutSession() {
  const refresh = localStorage.getItem('harness_refresh')
  try {
    if (refresh) {
      await fetch('/api/v1/auth/logout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refresh }),
      })
    }
  } catch {
    /* 网络失败不影响本地登出 */
  }
  clearSession()
}

export function getUser() {
  try {
    return JSON.parse(localStorage.getItem('harness_user') || 'null')
  } catch {
    return null
  }
}
