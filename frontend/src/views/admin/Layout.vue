<template>
  <div class="app-shell">
    <!-- Semi-transparent overlay -->
    <transition name="fade">
      <div v-if="drawerOpen" class="drawer-overlay" @click="drawerOpen = false" />
    </transition>

    <!-- Slide-out semi-transparent drawer -->
    <transition name="slide">
      <div v-if="drawerOpen" class="nav-drawer">
        <div class="drawer-header">
          <span class="drawer-title">导航菜单</span>
          <el-button text circle @click="drawerOpen = false">
            <el-icon :size="18"><Close /></el-icon>
          </el-button>
        </div>
        <div class="drawer-menu">
          <div
            v-for="item in navItems"
            :key="item.path"
            class="drawer-item"
            :class="{ active: route.path === item.path }"
            @click="navTo(item.path)"
          >
            <el-icon :size="18"><component :is="item.icon" /></el-icon>
            <span>{{ item.label }}</span>
          </div>
        </div>
      </div>
    </transition>

    <!-- Main content area -->
    <div class="main-area">
      <!-- Topbar -->
      <header class="topbar">
        <div class="topbar-left">
          <!-- Nav trigger button -->
          <el-button text class="nav-trigger" @click="drawerOpen = !drawerOpen">
            <el-icon :size="20"><Expand /></el-icon>
          </el-button>
          <!-- Brand dropdown -->
          <el-dropdown trigger="click" @command="navTo">
            <span class="topbar-brand">
              🏫 体育成绩管理系统 <el-icon class="brand-arrow"><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="/admin/dashboard">
                  <el-icon><DataAnalysis /></el-icon> 驾驶舱
                </el-dropdown-item>
                <el-dropdown-item command="/admin/score-entry">
                  <el-icon><EditPen /></el-icon> 成绩录入
                </el-dropdown-item>
                <el-dropdown-item command="/admin/students">
                  <el-icon><User /></el-icon> 学生管理
                </el-dropdown-item>
                <el-dropdown-item command="/admin/statistics">
                  <el-icon><TrendCharts /></el-icon> 统计分析
                </el-dropdown-item>
                <el-dropdown-item v-if="adminInfo?.role !== 'teacher'" command="/admin/settings">
                  <el-icon><Setting /></el-icon> 系统设置
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>

        <div class="topbar-right">
          <span class="current-school">🏫 {{ schoolName }}</span>
          <span class="role-badge" :class="adminInfo?.role">{{ roleLabel }}</span>
          <el-select
            v-if="adminInfo?.role === 'super'"
            v-model="currentSchoolId"
            size="small"
            class="school-switch"
            @change="switchSchool"
            placeholder="切换学校"
          >
            <el-option :value="null" label="全部学校" />
            <el-option v-for="s in schools" :key="s.id" :value="s.id" :label="s.name" />
          </el-select>
          <span class="user-avatar">{{ avatarChar }}</span>
          <span class="user-name">{{ adminInfo?.display_name || '管理员' }}</span>
          <el-button type="danger" text size="small" @click="logout">退出</el-button>
        </div>
      </header>

      <!-- Page content -->
      <main class="main-content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  Expand, ArrowDown, Close, DataAnalysis, EditPen,
  User, TrendCharts, Setting
} from '@element-plus/icons-vue'
import api from '../../api'

const router = useRouter()
const route = useRoute()
const adminInfo = ref(null)
const schoolName = ref('')
const drawerOpen = ref(false)
const schools = ref([])
const currentSchoolId = ref(null)

const navItems = [
  { label: '驾驶舱',   path: '/admin/dashboard',   icon: DataAnalysis },
  { label: '成绩录入', path: '/admin/score-entry',  icon: EditPen },
  { label: '学生管理', path: '/admin/students',     icon: User },
  { label: '统计分析', path: '/admin/statistics',   icon: TrendCharts },
  { label: '系统设置', path: '/admin/settings',     icon: Setting, role: '!teacher' },
]

const avatarChar = computed(() => (adminInfo.value?.display_name || '管')[0])

const roleLabel = computed(() => {
  const map = { super: '超级管理员', admin: '学校管理员', teacher: '教师' }
  return map[adminInfo.value?.role] || '管理员'
})

function navTo(path) {
  drawerOpen.value = false
  router.push(path)
}

onMounted(async () => {
  const info = localStorage.getItem('admin_info')
  if (info) {
    adminInfo.value = JSON.parse(info)
    currentSchoolId.value = adminInfo.value.school_id
  }
  try {
    const res = await api.get('/config/public')
    schoolName.value = res.data.school_name || '体育成绩管理系统'
  } catch {}
  if (adminInfo.value?.role === 'super') {
    try {
      const res = await api.get('/schools')
      schools.value = res.data
    } catch {}
  }
})

async function switchSchool(schoolId) {
  try {
    const res = await api.post('/auth/switch-school', { school_id: schoolId })
    localStorage.setItem('admin_token', res.data.access_token)
    localStorage.setItem('admin_info', JSON.stringify(res.data.admin))
    adminInfo.value = res.data.admin
    currentSchoolId.value = schoolId
    schoolName.value = res.data.admin.school_name || '全部学校'
    location.reload()
  } catch {
    location.reload()
  }
}

function logout() {
  localStorage.removeItem('admin_token')
  localStorage.removeItem('admin_info')
  router.push('/admin/login')
}
</script>

<style scoped>
/* ========== Shell ========== */
.app-shell {
  display: flex;
  min-height: 100vh;
  position: relative;
  overflow: hidden;
}

/* ========== Drawer overlay ========== */
.drawer-overlay {
  position: fixed; inset: 0;
  background: rgba(0, 0, 0, 0.25);
  z-index: 998;
}

/* ========== Drawer panel ========== */
.nav-drawer {
  position: fixed; top: 0; left: 0; bottom: 0;
  width: 260px;
  background: rgba(24, 40, 65, 0.96);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  z-index: 999;
  display: flex; flex-direction: column;
  box-shadow: 4px 0 24px rgba(0, 0, 0, 0.4);
  border-right: 1px solid rgba(255, 255, 255, 0.06);
}

.drawer-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 16px 16px 12px 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}
.drawer-title {
  color: rgba(255, 255, 255, 0.7);
  font-size: 13px; letter-spacing: 1px;
}

.drawer-menu {
  flex: 1; padding: 8px;
  display: flex; flex-direction: column; gap: 2px;
}

.drawer-item {
  display: flex; align-items: center; gap: 12px;
  padding: 12px 16px; border-radius: 8px;
  color: rgba(255, 255, 255, 0.75);
  font-size: 14.5px; cursor: pointer;
  transition: all 0.15s; user-select: none;
}
.drawer-item:hover {
  background: rgba(255, 255, 255, 0.08);
  color: #fff;
}
.drawer-item.active {
  background: rgba(64, 158, 255, 0.2);
  color: #60a5fa;
}

/* ========== Transitions ========== */
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.25s ease;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}

.slide-enter-active, .slide-leave-active {
  transition: transform 0.28s cubic-bezier(0.22, 0.61, 0.36, 1);
}
.slide-enter-from, .slide-leave-to {
  transform: translateX(-100%);
}

/* ========== Main area ========== */
.main-area {
  flex: 1; display: flex; flex-direction: column;
  min-width: 0;
}

/* ========== Topbar ========== */
.topbar {
  background: #fff; border-bottom: 1px solid #e8e6e1;
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 16px; height: 50px; gap: 12px;
  flex-shrink: 0;
}
.topbar-left { display: flex; align-items: center; gap: 4px; }
.topbar-right { display: flex; align-items: center; gap: 12px; }

/* Nav trigger button */
.nav-trigger {
  padding: 6px; color: #6b7280;
}
.nav-trigger:hover { color: #303133; background: #f3f4f6; }

/* Brand dropdown trigger */
.topbar-brand {
  font-size: 15px; font-weight: 700; color: #303133;
  cursor: pointer; display: flex; align-items: center; gap: 4px;
  padding: 4px 8px; border-radius: 6px; transition: background 0.15s;
  white-space: nowrap; user-select: none;
}
.topbar-brand:hover { background: #f5f3f0; }
.brand-arrow { font-size: 12px; color: #a3a3a3; transition: transform 0.2s; }

/* Current school */
.current-school {
  font-size: 12.5px; color: #525252; font-weight: 500;
  max-width: 180px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}

/* Role badge */
.role-badge {
  font-size: 10px; font-weight: 700; letter-spacing: 0.5px;
  padding: 2px 8px; border-radius: 10px; white-space: nowrap;
}
.role-badge.super  { background: #fef3c7; color: #92400e; }
.role-badge.admin  { background: #dbeafe; color: #1e40af; }
.role-badge.teacher { background: #f3f4f6; color: #6b7280; }

/* School switcher */
.school-switch { width: 140px; }

/* User area */
.user-avatar {
  width: 28px; height: 28px; border-radius: 50%;
  background: #4f46e5; color: #fff;
  display: flex; align-items: center; justify-content: center;
  font-size: 12px; font-weight: 700; flex-shrink: 0;
}
.user-name {
  font-size: 13px; color: #303133; font-weight: 500;
  max-width: 100px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}

/* ========== Main content ========== */
.main-content {
  padding: 12px; background: #f0f2f5;
  flex: 1; min-height: 0;
}

@media (max-width: 767px) {
  .main-content { padding: 8px; }
  .current-school { display: none; }
  .role-badge { display: none; }
  .nav-drawer { width: 240px; }
}
</style>
