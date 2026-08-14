<template>
  <span ref="el" class="count-up">{{ display }}</span>
</template>

<script setup>
import { onMounted, onUnmounted, ref, watch } from 'vue'

const props = defineProps({
  value: { type: Number, default: 0 },
  duration: { type: Number, default: 1200 },
  decimals: { type: Number, default: 0 },
  prefix: { type: String, default: '' },
  suffix: { type: String, default: '' },
})

const el = ref(null)
const display = ref('0')
let rafId = null
let started = false
let observer = null

function animate() {
  const startTime = performance.now()
  const startVal = 0
  const endVal = props.value || 0

  const tick = (now) => {
    const progress = Math.min(1, (now - startTime) / props.duration)
    // easeOutCubic
    const eased = 1 - Math.pow(1 - progress, 3)
    const current = startVal + (endVal - startVal) * eased
    display.value = props.prefix + current.toFixed(props.decimals) + props.suffix
    if (progress < 1) {
      rafId = requestAnimationFrame(tick)
    } else {
      display.value = props.prefix + endVal.toFixed(props.decimals) + props.suffix
    }
  }
  rafId = requestAnimationFrame(tick)
}

onMounted(() => {
  if (typeof IntersectionObserver !== 'undefined' && el.value) {
    observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && !started) {
          started = true
          animate()
        }
      },
      { threshold: 0.3 }
    )
    observer.observe(el.value)
  } else {
    animate()
  }
})

watch(
  () => props.value,
  () => {
    if (started) {
      display.value = '0'
      animate()
    }
  }
)

onUnmounted(() => {
  if (rafId) cancelAnimationFrame(rafId)
  if (observer) observer.disconnect()
})
</script>
