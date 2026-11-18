<!--
Copyright (c) 2026 Blueway Consulting LLC.
Licensed under the LGPL-3.0 License. See LICENSE file for details.
-->

<script setup>
import { appContext } from '@/stores/appContext'
import { logout } from '@/utils/client/api'

defineProps({
  showMobileMenuButton: {
    type: Boolean,
    default: true
  }
})

// The User document form in the Frappe desk: /desk/user/{userId}
const profileUrl = `/desk/user/${appContext.userName}`

async function handleLogout() {
  try {
    await logout()
  } catch (error) {
    console.error('Logout failed:', error)
    // Fallback to direct redirect if API fails
    window.location.href = '/login?redirect-to=/chronotally'
  }
}
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

      <!-- User Avatar Menu -->
      <div class="dropdown dropdown-end ml-2">
        <button
          type="button"
          tabindex="0"
          aria-haspopup="menu"
          aria-label="open user menu"
          class="btn btn-ghost btn-circle"
        >
          <!-- User Avatar -->
          <div v-if="appContext.userImage" class="avatar">
            <div class="w-10 rounded-full">
              <img :src="appContext.userImage" :alt="appContext.userFullName || appContext.userInitials" />
            </div>
          </div>
          <!-- User Initials Placeholder -->
          <div v-else-if="appContext.userInitials" class="avatar avatar-placeholder">
            <div class="w-10 rounded-full bg-neutral text-neutral-content">
              <span class="text-sm">{{ appContext.userInitials }}</span>
            </div>
          </div>
          <!-- Generic Placeholder -->
          <span v-else class="material-symbols-rounded text-2xl">
            account_circle
          </span>
        </button>

        <!-- Dropdown Menu -->
        <ul tabindex="-1" class="dropdown-content menu bg-base-100 rounded-box z-1 w-52 p-2 shadow-sm">
          <li>
            <a :href="profileUrl">
              <span class="material-symbols-rounded text-xl">
                person
              </span>
              <span class="font-medium">Profile</span>
            </a>
          </li>
          <li>
            <button type="button" @click="handleLogout">
              <span class="material-symbols-rounded text-xl">
                logout
              </span>
              <span class="font-medium">Logout</span>
            </button>
          </li>
        </ul>
      </div>

    </div>
  </div>
</template>