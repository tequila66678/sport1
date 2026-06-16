<template>
  <el-container style="min-height:100vh">
    <!-- Mobile overlay sidebar -->
    <div v-if="mobileOpen" class="sidebar-overlay" @click="mobileOpen = false" />
    <el-aside :width="isMobile ? (mobileOpen ? '220px' : '0px') : '220px'" class="sidebar" :class="{ 'sidebar-fixed': isMobile }">
      <div class="logo">{{ schoolName }}</div>
      <el-menu
        :default-active="route.path"
        background-color="#304156"
        text-color="#bfcbd9"
        active-text-color="#409EFF"
        router
        @select="mobileOpen = false"
      >
        <el-menu-item index="/admin/dashboard">
          <el-icon><DataAnalysis /></el-icon> 驾驶舱
        </el-menu-item>
        <el-menu-item index="/admin/score-entry">
          <el-icon><EditPen /></el-icon> 成绩录入
        </el-menu-item>
        <el-menu-item index="/admin/students">
          <el-icon><User /></el-icon> 学生管理
        </el-menu-item>
        <el-menu-item index="/admin/statistics">
          <el-icon><TrendCharts /></el-icon> 统计分析
        </el-menu-item>
        <el-menu-item v-if="adminInfo?.role !== 'teacher'" index="/admin/settings">
          <el-icon><Setting /></el-icon> 系统设置
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="topbar">
        <div class="topbar-left">
          <!-- Mobile hamburger -->
          <el-button v-if="isMobile" text @click="mobileOpen = !mobileOpen" class="menu-btn">
            <el-icon :size="22"><Expand v-if="!mobileOpen" /><Fold v-else /></el-icon>
          </el-button>
          <!-- Nav dropdown -->
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
          <!-- Current school -->
          <span class="current-school">🏫 {{ schoolName }}</span>
          <!-- Role badge -->
          <span class="role-badge" :class="adminInfo?.role">
            {{ roleLabel }}
          </span>
          <!-- Super-admin school switcher -->
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
          <!-- User info -->
          <span class="user-avatar">{{ avatarChar }}</span>
          <span class="user-name">{{ adminInfo?.display_name || '管理员' }}</span>
          <el-button type="danger" text size="small" @click="logout">退出</el-button>
        </div>
      </el-header>
      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import api from '../../api'

const router = useRouter()
const route = useRoute()
const adminInfo = ref(null)
const schoolName = ref('')
const mobileOpen = ref(false)
const isMobile = ref(window.innerWidth < 768)
const schools = ref([])
const currentSchoolId = ref(null)

const avatarChar = computed(() => {
  return (adminInfo.value?.display_name || '管')[0]
})

const roleLabel = computed(() => {
  const map = { super: '超级管理员', admin: '学校管理员', teacher: '教师' }
  return map[adminInfo.value?.role] || '管理员'
})

function navTo(path) {
  router.push(path)
}

function onResize() { isMobile.value = window.innerWidth < 768 }

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
  window.addEventListener('resize', onResize)
})

onUnmounted(() => { window.removeEventListener('resize', onResize) })

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
/* Sidebar */
.sidebar { transition: width 0.3s; overflow: hidden; background: #304156; }
.sidebar-fixed { position: fixed; left: 0; top: 0; bottom: 0; z-index: 1000; }
.sidebar-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.5); z-index: 999; }
.logo { color: white; text-align: center; padding: 16px 8px; font-size: 14px; font-weight: bold; border-bottom: 1px solid rgba(255,255,255,0.1); white-space: nowrap; }

/* Topbar */
.topbar {
  background: #fff; border-bottom: 1px solid #e8e6e1;
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 16px; height: 50px; gap: 12px;
}
.topbar-left { display: flex; align-items: center; gap: 8px; }
.topbar-right { display: flex; align-items: center; gap: 12px; }

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

/* Mobile */
.menu-btn { padding: 4px; }

/* Main content */
.main-content { padding: 12px; background: #f0f2f5; min-height: calc(100vh - 50px); }
@media (max-width: 767px) {
  .main-content { padding: 8px; }
  .current-school { display: none; }
  .role-badge { display: none; }
}
</style>
