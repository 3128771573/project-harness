<template>
  <div class="auth-page">
    <div class="auth-card">
      <div class="brand">
        <div class="logo">H</div>
        <h1>{{ title }}</h1>
        <p>{{ subtitle }}</p>
      </div>
      <slot />
    </div>
  </div>
</template>

<script setup>
defineProps({
  title: { type: String, required: true },
  subtitle: { type: String, default: '' },
})
</script>
