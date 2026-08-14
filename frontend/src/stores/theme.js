import { defineStore } from 'pinia'

const STORAGE_KEY = 'harness-theme'

function getSystemTheme() {
  if (typeof window !== 'undefined' && window.matchMedia) {
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
  }
  return 'light'
}

export const useThemeStore = defineStore('theme', {
  state: () => ({
    // 'light' | 'dark' | 'system'
    theme: 'system',
  }),

  getters: {
    /** 实际生效的主题（system 解析后） */
    effectiveTheme: (state) => {
      if (state.theme === 'system') return getSystemTheme()
      return state.theme
    },
  },

  actions: {
    /** 初始化：读取 localStorage + 应用主题到 html */
    init() {
      let saved = null
      try {
        const raw = localStorage.getItem(STORAGE_KEY)
        if (raw) {
          const parsed = JSON.parse(raw)
          if (['light', 'dark', 'system'].includes(parsed.theme)) {
            saved = parsed.theme
          }
        }
      } catch { /* ignore */ }
      this.theme = saved || 'system'
      this.apply()
    },

    /** 应用当前主题到 <html data-theme> */
    apply() {
      const root = document.documentElement
      root.setAttribute('data-theme', this.effectiveTheme)
      // 触发过渡动画（避免首屏闪烁：首次应用不过渡）
      if (!root.classList.contains('theme-initialized')) {
        root.classList.add('theme-initialized')
      } else {
        root.classList.add('theme-transition')
        setTimeout(() => root.classList.remove('theme-transition'), 400)
      }
    },

    /** 切换主题 */
    setTheme(theme) {
      if (!['light', 'dark', 'system'].includes(theme)) return
      this.theme = theme
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify({ theme }))
      } catch { /* ignore */ }
      this.apply()
    },

    /** 监听系统主题变化（仅在 system 模式生效） */
    watchSystem() {
      if (typeof window === 'undefined' || !window.matchMedia) return
      const mq = window.matchMedia('(prefers-color-scheme: dark)')
      const handler = () => {
        if (this.theme === 'system') this.apply()
      }
      if (mq.addEventListener) {
        mq.addEventListener('change', handler)
      } else if (mq.addListener) {
        mq.addListener(handler)
      }
      this._systemHandler = handler
    },
  },
})
