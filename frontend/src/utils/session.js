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

export function getUser() {
  try {
    return JSON.parse(localStorage.getItem('harness_user') || 'null')
  } catch {
    return null
  }
}
