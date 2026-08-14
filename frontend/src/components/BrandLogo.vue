<template>
  <span class="brand-logo" :class="[size, inverse ? 'inverse' : '']" :style="{ width: px, height: px }">
    <svg viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="hg" x1="4" y1="4" x2="28" y2="28" gradientUnits="userSpaceOnUse">
          <stop stop-color="#2563EB"/>
          <stop offset="1" stop-color="#7C3AED"/>
        </linearGradient>
      </defs>
      <!-- 圆角方块底 -->
      <rect x="1" y="1" width="30" height="30" rx="8" fill="url(#hg)"/>
      <!-- H 造型（两条竖杠 + 横梁） -->
      <rect x="8" y="9" width="3.4" height="14" rx="1.7" fill="#fff"/>
      <rect x="20.6" y="9" width="3.4" height="14" rx="1.7" fill="#fff"/>
      <rect x="8" y="14.3" width="16" height="3.4" rx="1.7" fill="#fff" opacity="0.95"/>
    </svg>
  </span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  size: { type: String, default: 'md' }, // sm / md / lg
  inverse: { type: Boolean, default: false },
})

const px = computed(() => ({ sm: '28px', md: '36px', lg: '52px' }[props.size] || '36px'))
</script>

<style scoped>
.brand-logo {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.brand-logo svg {
  width: 100%;
  height: 100%;
}
</style>
