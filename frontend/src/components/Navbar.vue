<!--
Copyright (c) 2026 Blueway Consulting LLC.
Licensed under the LGPL-3.0 License. See LICENSE file for details.
-->

<script setup>
import { appContext } from '@/stores/appContext'

defineProps({
  showMobileMenuButton: {
    type: Boolean,
    default: true
  }
})
</script>

<template>
  <!-- DaisyUI 5 Navbar Component -->
  <div class="navbar bg-base-200 border-b border-base-200 shadow-sm">
    <!-- Mobile menu button (left side) -->
    <div class="navbar-start">
      <label
        v-if="showMobileMenuButton"
        for="app-drawer"
        aria-label="open sidebar"
        class="btn btn-square btn-ghost lg:hidden"
      >
        <span class="material-symbols-rounded text-2xl">
          menu
        </span>
      </label>
    </div>

    <!-- Brand/Title (center) -->
    <div class="navbar-center">
      <a class="btn btn-ghost text-xl font-bold">ChronoTally</a>
    </div>

    <!-- Actions (right side) -->
    <div class="navbar-end">
      <!-- Search button -->
      <button class="btn btn-ghost btn-circle">
        <span class="material-symbols-rounded text-xl">
          search
        </span>
      </button>

      <!-- Notifications button with indicator -->
      <button class="btn btn-ghost btn-circle">
        <div class="indicator">
          <span class="material-symbols-rounded text-xl">
            notifications
          </span>
          <span class="badge badge-xs badge-primary indicator-item"></span>
        </div>
      </button>

      <!-- User Avatar -->
      <div v-if="appContext.userImage" class="avatar">
        <div class="w-10 rounded-full">
          <img :src="appContext.userImage" :alt="appContext.userInitials" />
        </div>
      </div>
      <!-- User Initials Placeholder -->
      <button v-else-if="appContext.userInitials" class="ml-2 btn btn-ghost btn-circle">
      
      <div class="avatar avatar-placeholder">
        <div class="w-10 rounded-full bg-neutral text-neutral-content">
          <span class="text-sm">{{ appContext.userInitials }}</span>
        </div>
      </div>
      </button>
      
    </div>
  </div>
</template>
