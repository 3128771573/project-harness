<template>
  <div class="theme-switcher" role="radiogroup" aria-label="主题切换">
    <button
      v-for="opt in options"
      :key="opt.value"
      type="button"
      class="ts-option"
      :class="{ active: themeStore.theme === opt.value }"
      :aria-checked="themeStore.theme === opt.value"
      role="radio"
      :title="opt.label"
      @click="themeStore.setTheme(opt.value)"
    >
      <span class="ts-icon">{{ opt.icon }}</span>
      <span class="ts-label">{{ opt.label }}</span>
    </button>
  </div>
</template>

<script setup>
import { useThemeStore } from '../stores/theme'

const themeStore = useThemeStore()

const options = [
  { value: 'light', icon: '☀️', label: 'Light' },
  { value: 'dark', icon: '🌙', label: 'Dark' },
  { value: 'system', icon: '⚙️', label: 'System' },
]
</script>

<style scoped>
.theme-switcher {
  display: inline-flex;
  align-items: center;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 999px;
  padding: 3px;
  gap: 2px;
}

.ts-option {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 7px 14px;
  border: none;
  border-radius: 999px;
  background: transparent;
  color: var(--text-muted);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  font-family: inherit;
  transition: all 0.2s;
}

.ts-option:hover {
  color: var(--text-primary);
}

.ts-option.active {
  background: var(--bg-card);
  color: var(--text-primary);
  box-shadow: var(--shadow-sm);
}

.ts-icon {
  font-size: 13px;
}
</style>
