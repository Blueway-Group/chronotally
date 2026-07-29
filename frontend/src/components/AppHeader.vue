<!--
Copyright (c) 2026 Blueway Consulting LLC.
Licensed under the LGPL-3.0 License. See LICENSE file for details.
-->

<script setup>
import Navbar from './Navbar.vue'

defineProps({
  showMobileMenuButton: {
    type: Boolean,
    default: false
  }
})
</script>

<template>
  <!-- DaisyUI 5 Header Component -->
  <header class="w-full">
    <Navbar :show-mobile-menu-button="showMobileMenuButton" />
  </header>
</template>