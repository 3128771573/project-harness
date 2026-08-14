import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import { useThemeStore } from './stores/theme'

// Inter 字体（离线打包）
import '@fontsource-variable/inter'

// 主题样式（顺序：变量 → light → dark）
import './styles/theme.css'
import './styles/light.css'
import './styles/dark.css'
import './assets/main.css'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)

// 初始化主题（在挂载前应用，避免闪烁）
const themeStore = useThemeStore(pinia)
themeStore.init()
themeStore.watchSystem()

app.mount('#app')
