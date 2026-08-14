import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 60000,
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('harness_access')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 并发 401 时只发起一次 refresh（单例 Promise），避免多个请求各自刷新、
// 旧 refresh_token 被轮换吊销后其余请求全部失败导致强制登出
let refreshing = null

api.interceptors.response.use(
  (res) => res,
  async (err) => {
    // access_token 过期时尝试用 refresh_token 静默续期
    const original = err.config
    if (err.response?.status === 401 && !original._retried) {
      const refresh = localStorage.getItem('harness_refresh')
      if (refresh) {
        original._retried = true
        try {
          if (!refreshing) {
            refreshing = axios
              .post('/api/v1/auth/refresh', { refresh_token: refresh })
              .finally(() => {
                refreshing = null
              })
          }
          const { data } = await refreshing
          localStorage.setItem('harness_access', data.access_token)
          localStorage.setItem('harness_refresh', data.refresh_token)
          localStorage.setItem('harness_user', JSON.stringify(data.user))
          original.headers.Authorization = `Bearer ${data.access_token}`
          return api(original)
        } catch {
          // refresh 也失败 -> 强制登出
        }
      }
      localStorage.removeItem('harness_access')
      localStorage.removeItem('harness_refresh')
      localStorage.removeItem('harness_user')
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    }
    return Promise.reject(err)
  }
)

export default api
