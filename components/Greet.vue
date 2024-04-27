<script setup lang="ts">
  import { invoke } from '@tauri-apps/api/tauri';
  const greeting = ref("");

  onMounted( () => {
    invoke<string>('greet', { name: 'Next.js' })
        .then((result) => {greeting.value = result;})
        .catch(console.error)
  })

</script>

<template>
  <div>
    {{ greeting }}
  </div>

</template>

