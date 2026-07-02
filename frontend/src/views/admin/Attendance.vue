<template>
  <div class="at-page">
    <button class="back-btn" @click="started ? (started = false) : $router.push('/admin/dashboard')">{{ started ? '← 返回选择' : '← 返回仪表盘' }}</button>

    <!-- ===== TAB BAR ===== -->
    <div class="tab-bar">
      <button :class="['tab-btn', { active: activeTab === 'entry' }]" @click="activeTab = 'entry'">📝 签到操作</button>
      <button :class="['tab-btn', { active: activeTab === 'stats' }]" @click="activeTab = 'stats'">📊 签到统计</button>
    </div>

    <!-- ==================== TAB: 签到操作 ==================== -->
    <template v-if="activeTab === 'entry'">
    <!-- ===== PROGRESS STEPS ===== -->
    <div class="progress-steps">
      <div class="step" :class="{ active: currentStep >= 1, done: currentStep > 1 }">
        <span class="step-num">{{ currentStep > 1 ? '✓' : '1' }}</span>
        <span class="step-label">选择班级</span>
      </div>
      <span class="step-line" :class="{ done: currentStep > 1 }"></span>
      <div class="step" :class="{ active: currentStep >= 2 }">
        <span class="step-num">2</span>
        <span class="step-label">签到操作</span>
      </div>
    </div>

    <!-- ===== RECENT SESSIONS BAR ===== -->
    <div class="recent-bar" v-if="recentSessions.length > 0">
      <span class="recent-icon">📋</span>
      <span>近期签到：</span>
      <span v-for="(r, i) in recentSessions.slice(0, 3)" :key="i" class="recent-item">
        {{ r.class_name }} {{ r.session_date }}{{ r.label ? ' ' + r.label : '' }}（{{ r.present_count + r.late_count }}/{{ r.present_count + r.late_count + r.excused_count + r.absent_count }}）{{ i < Math.min(recentSessions.length, 3) - 1 ? ' · ' : '' }}
      </span>
    </div>

    <!-- ===== SELECTION STEP ===== -->
    <div v-if="!started" class="at-select">
      <button class="back-btn" @click="$router.push('/admin/dashboard')">← 返回仪表盘</button>

      <div class="entry-card">
        <!-- Hero -->
        <div class="hero">
          <div class="hero-icon">📋</div>
          <h1>签到管理</h1>
          <p>默认全员出勤 · 仅需标记异常情况</p>
        </div>

        <!-- Form -->
        <div class="form-group">
          <label>👥 班级</label>
          <el-select v-model="selectedClassId" placeholder="请选择班级" size="large" class="at-select-el">
            <el-option v-for="c in classes" :key="c.id" :label="c.label || c.grade + ' ' + c.name" :value="c.id" />
          </el-select>
        </div>

        <div class="form-group">
          <label>📅 日期</label>
          <el-date-picker v-model="sessionDate" type="date" placeholder="选择日期" value-format="YYYY-MM-DD" size="large" class="at-date-el" />
        </div>

        <div class="form-group">
          <label>🏷️ 节次标签 <span style="color:#7d8fb9;font-weight:400;font-size:13px">（可选）</span></label>
          <el-input v-model="sessionLabel" placeholder="如：第1节、周一训练" size="large" class="at-input-el" clearable />
        </div>

        <!-- CTA Button -->
        <button class="start-btn" @click="startAttendance" :disabled="!selectedClassId || !sessionDate">
          开始签到 →
        </button>
      </div>
    </div>

    <!-- ===== ENTRY STEP ===== -->
    <div v-else class="at-entry">
      <div class="entry-topbar">
        <button class="back-btn" @click="started = false">← 返回选择</button>
        <span class="entry-context">{{ selectedClassName }} · {{ sessionDate }}{{ sessionLabel ? ' · ' + sessionLabel : '' }}</span>
        <button class="back-btn" style="margin-left:auto" @click="started = false; loadRecentSessions()">✕ 结束签到</button>
      </div>

      <!-- Summary + batch toolbar -->
      <div class="summary-toolbar">
        <div class="summary-counts">
          <span class="sc-item present">✓ 出勤 {{ statusCounts.present }}</span>
          <span class="sc-item late">⏰ 迟到 {{ statusCounts.late }}</span>
          <span class="sc-item excused">📝 请假 {{ statusCounts.excused }}</span>
          <span class="sc-item absent">✗ 缺勤 {{ statusCounts.absent }}</span>
        </div>
        <div class="batch-actions">
          <button class="action-btn-sm" @click="batchToggle('late')">全部标为迟到</button>
          <button class="action-btn-sm" @click="batchToggle('excused')">全部标为请假</button>
          <button class="action-btn-sm" @click="batchToggle('absent')">全部标为缺勤</button>
          <button class="action-btn-sm reset" @click="resetAll">重置全部出勤</button>
        </div>
      </div>

      <!-- Existing session notice -->
      <div v-if="existingSessionId" class="notice-bar">
        <span>⚠ 此班级当日已有签到记录，将继续编辑</span>
      </div>

      <!-- Desktop table -->
      <div class="glass-card" v-if="!isMobile">
        <el-table :data="students" stripe max-height="calc(100vh - 360px)">
          <el-table-column prop="name" label="姓名" width="80" />
          <el-table-column prop="gender" label="性别" width="50">
            <template #default="{ row }">{{ row.gender === 'M' ? '男' : '女' }}</template>
          </el-table-column>
          <el-table-column label="状态" width="280">
            <template #default="{ row }">
              <div class="status-toggle">
                <button
                  v-for="opt in statusOptions"
                  :key="opt.value"
                  :class="['st-btn', opt.value, { on: records[row.id]?.status === opt.value }]"
                  @click="setStatus(row.id, opt.value)"
                >{{ opt.emoji }} {{ opt.label }}</button>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="备注" min-width="1">
            <template #default="{ row }">
              <el-input
                v-model="records[row.id].remark"
                size="small"
                placeholder="选填备注"
                clearable
                :disabled="records[row.id]?.status === 'present'"
              />
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- Mobile cards -->
      <div v-if="isMobile" class="mobile-list">
        <div
          v-for="s in students"
          :key="s.id"
          :class="['student-card', records[s.id]?.status || 'present']"
        >
          <div class="sc-top">
            <span class="sc-name">{{ s.name }}</span>
            <span class="sc-gender">{{ s.gender === 'M' ? '男' : '女' }}</span>
          </div>
          <div class="sc-status">
            <button
              v-for="opt in statusOptions"
              :key="opt.value"
              :class="['st-btn', 'st-btn-sm', opt.value, { on: records[s.id]?.status === opt.value }]"
              @click="setStatus(s.id, opt.value)"
            >{{ opt.emoji }}</button>
          </div>
          <el-input
            v-model="records[s.id].remark"
            size="small"
            placeholder="备注"
            clearable
            :disabled="records[s.id]?.status === 'present'"
            style="margin-top:6px"
          />
        </div>
      </div>

      <!-- Save -->
      <div class="save-bar">
        <button class="start-btn save-btn" :disabled="saving" @click="saveSession">
          {{ saving ? '保存中...' : (existingSessionId ? '💾 更新签到' : '💾 保存签到') }}
        </button>
        <div class="save-footer">
          <span>{{ students.length }} 名学生 · 异常 {{ statusCounts.late + statusCounts.excused + statusCounts.absent }} 人</span>
        </div>
      </div>
    </div>
    </template>

    <!-- ==================== TAB: 签到统计 ==================== -->
    <template v-if="activeTab === 'stats'">
      <div class="toolbar-glass">
        <el-select v-model="statsClassId" placeholder="选择班级" @change="loadClassStats" clearable class="tb-select" size="large">
          <el-option v-for="c in classes" :key="c.id" :value="c.id" :label="c.label || c.grade + ' ' + c.name" />
        </el-select>
        <el-date-picker v-model="statsDateRange" type="daterange" range-separator="至"
          start-placeholder="开始日期" end-placeholder="结束日期" value-format="YYYY-MM-DD"
          @change="loadClassStats" class="tb-date-range" size="large" />
        <span style="color:#8ea0c8;font-size:13px">预警阈值:</span>
        <el-input-number v-model="warningThreshold" :min="0" :max="100" :step="5" size="small" style="width:90px" @change="loadClassStats" />
        <span style="color:#8ea0c8;font-size:13px">%</span>
      </div>

      <!-- Stats cards -->
      <div v-if="classStats" class="stats-mini">
        <div class="stat-item">
          <span class="stat-num">{{ classStats.total_sessions }}</span>
          <span class="stat-label">考勤次数</span>
        </div>
        <div class="stat-item">
          <span class="stat-num" style="color:#10b981">{{ classStats.avg_attendance_rate }}%</span>
          <span class="stat-label">平均出勤率</span>
        </div>
        <div class="stat-item">
          <span class="stat-num" style="color:#fca5a5">{{ classStats.warning_students?.length || 0 }}</span>
          <span class="stat-label">预警人数</span>
        </div>
        <div class="stat-item">
          <span class="stat-num">{{ classStats.student_stats?.length || 0 }}</span>
          <span class="stat-label">班级人数</span>
        </div>
      </div>

      <!-- Desktop student table -->
      <div v-if="classStats && !isMobile" class="glass-card">
        <el-table :data="classStats.student_stats" stripe max-height="calc(100vh - 380px)">
          <el-table-column label="姓名" width="90">
            <template #default="{ row }">
              <span class="student-link" @click="openStudentDetail(row)">{{ row.student_name }}</span>
            </template>
          </el-table-column>
          <el-table-column label="出勤率" min-width="200">
            <template #default="{ row }">
              <div class="rate-cell">
                <el-progress :percentage="row.attendance_rate" :color="rateColor(row.attendance_rate)" :stroke-width="16" style="flex:1" />
                <span :style="{color:rateColor(row.attendance_rate),fontWeight:'bold',fontSize:'13px',marginLeft:'10px'}">{{ row.attendance_rate }}%</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="present_count" label="出勤" width="65" />
          <el-table-column prop="late_count" label="迟到" width="65" />
          <el-table-column prop="excused_count" label="请假" width="65" />
          <el-table-column prop="absent_count" label="缺勤" width="65" />
          <el-table-column prop="total_sessions" label="总计" width="65" />
        </el-table>
      </div>

      <!-- Mobile stats -->
      <div v-if="classStats && isMobile" class="mobile-list">
        <div v-for="s in classStats.student_stats" :key="s.student_id" class="student-card" @click="openStudentDetail(s)">
          <div class="sc-top">
            <span class="sc-name">{{ s.student_name }}</span>
            <span :style="{color:rateColor(s.attendance_rate),fontWeight:'bold'}">{{ s.attendance_rate }}%</span>
          </div>
          <el-progress :percentage="s.attendance_rate" :color="rateColor(s.attendance_rate)" :stroke-width="8" style="margin:8px 0" />
          <div style="display:flex;gap:12px;font-size:12px;color:#8ea0c8">
            <span>出勤{{ s.present_count }}</span><span>迟到{{ s.late_count }}</span><span>请假{{ s.excused_count }}</span><span>缺勤{{ s.absent_count }}</span>
          </div>
        </div>
      </div>

      <!-- Warnings -->
      <div v-if="classStats && classStats.warning_students?.length" style="margin-top:20px">
        <div style="color:#fca5a5;font-weight:bold;font-size:14px;margin-bottom:10px">
          ⚠ 缺勤预警 — 出勤率低于 {{ warningThreshold }}%（{{ classStats.warning_students.length }}人）
        </div>
        <div class="glass-card">
          <el-table :data="classStats.warning_students" stripe size="small" max-height="260">
            <el-table-column prop="student_name" label="姓名" width="100" />
            <el-table-column label="出勤率" width="110">
              <template #default="{ row }">
                <span style="color:#fca5a5;font-weight:bold">{{ row.attendance_rate }}%</span>
              </template>
            </el-table-column>
            <el-table-column prop="absent_count" label="缺勤次数" width="100" />
            <el-table-column prop="total_sessions" label="总次数" width="80" />
          </el-table>
        </div>
      </div>

      <!-- ===== Student detail dialog ===== -->
      <el-dialog v-model="studentDialogVisible" :title="dialogStudentName + ' - 异常签到明细'" width="600px" destroy-on-close>
        <div v-if="studentAbnormalRecords.length > 0">
          <el-table :data="studentAbnormalRecords" stripe size="small" max-height="400">
            <el-table-column label="状态" width="80">
              <template #default="{ row }">
                <span :class="'tag-' + row.status">{{ row.status_label }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="session_date" label="日期" width="120" />
            <el-table-column prop="session_label" label="节次" width="90">
              <template #default="{ row }">{{ row.session_label || '-' }}</template>
            </el-table-column>
            <el-table-column prop="remark" label="备注" min-width="1">
              <template #default="{ row }">{{ row.remark || '-' }}</template>
            </el-table-column>
          </el-table>
        </div>
        <div v-else style="text-align:center;padding:40px;color:#7d8fb9">该生暂无异常签到记录</div>
      </el-dialog>

      <div v-if="!classStats" style="text-align:center;padding:60px 0;color:#7d8fb9">
        请选择班级查看出勤统计
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../../api'

const isMobile = ref(window.innerWidth < 768)
window.addEventListener('resize', () => { isMobile.value = window.innerWidth < 768 })

const activeTab = ref('entry')
const classes = ref([])
const selectedClassId = ref(null)
const sessionDate = ref(new Date().toISOString().split('T')[0])
const sessionLabel = ref('')
const started = ref(false)
const students = ref([])
const records = ref({})
const existingSessionId = ref(null)
const saving = ref(false)
const recentSessions = ref([])

// Stats tab
const statsClassId = ref(null)
const statsDateRange = ref(null)
const warningThreshold = ref(80)
const classStats = ref(null)

function rateColor(rate) {
  if (rate >= 90) return '#67c23a'
  if (rate >= 80) return '#e6a23c'
  return '#f56c6c'
}

async function loadClassStats() {
  if (!statsClassId.value) { classStats.value = null; return }
  const params = { class_id: statsClassId.value, threshold: warningThreshold.value }
  if (statsDateRange.value?.length === 2) {
    params.date_from = statsDateRange.value[0]; params.date_to = statsDateRange.value[1]
  }
  try {
    const res = await api.get('/attendance/class-stats', { params })
    classStats.value = res.data
  } catch {}
}

// Student detail dialog
const studentDialogVisible = ref(false)
const dialogStudentName = ref('')
const studentAbnormalRecords = ref([])

async function openStudentDetail(row) {
  dialogStudentName.value = row.student_name
  studentDialogVisible.value = true
  try {
    const res = await api.get(`/attendance/student-stats/${row.student_id}`)
    const all = res.data.records || []
    // Filter only abnormal records (not present) and add status labels
    studentAbnormalRecords.value = all
      .filter(r => r.status !== 'present')
      .map(r => ({
        ...r,
        status_label: { late: '迟到', excused: '请假', absent: '缺勤' }[r.status] || r.status,
      }))
  } catch {
    studentAbnormalRecords.value = []
  }
}

const statusOptions = [
  { value: 'present', label: '出勤', emoji: '✓' },
  { value: 'late',    label: '迟到', emoji: '⏰' },
  { value: 'excused', label: '请假', emoji: '📝' },
  { value: 'absent',  label: '缺勤', emoji: '✗' },
]

const currentStep = computed(() => {
  if (started.value) return 2
  if (!selectedClassId.value) return 1
  return 2
})

const selectedClassName = computed(() => {
  const c = classes.value.find(c => c.id === selectedClassId.value)
  return c ? (c.label || c.grade + ' ' + c.name) : ''
})

const statusCounts = computed(() => {
  const counts = { present: 0, late: 0, excused: 0, absent: 0 }
  for (const sid of students.value.map(s => s.id)) {
    const s = records.value[sid]?.status || 'present'
    if (counts[s] !== undefined) counts[s]++
  }
  return counts
})

onMounted(async () => {
  try {
    const res = await api.get('/events/classes')
    classes.value = res.data
  } catch {}
  loadRecentSessions()
})

async function loadRecentSessions() {
  try {
    const today = new Date().toISOString().split('T')[0]
    const res = await api.get('/attendance/sessions', { params: { date_from: today, page_size: 5 } })
    recentSessions.value = res.data.items || []
  } catch {}
}

async function startAttendance() {
  if (!selectedClassId.value || !sessionDate.value) return

  // Check for existing session
  try {
    const res = await api.get('/attendance/sessions', {
      params: { class_id: selectedClassId.value, date_from: sessionDate.value, date_to: sessionDate.value }
    })
    if (res.data.items?.length > 0) {
      const ses = res.data.items[0]
      existingSessionId.value = ses.id
      sessionLabel.value = ses.label || ''
      try {
        const detail = await api.get(`/attendance/sessions/${ses.id}`)
        const newRecords = {}
        for (const r of detail.data.records) {
          newRecords[r.student_id] = { status: r.status, remark: r.remark || '' }
        }
        records.value = newRecords
      } catch {}
    } else {
      existingSessionId.value = null
      records.value = {}
    }
  } catch {
    existingSessionId.value = null
    records.value = {}
  }

  // Load students
  try {
    const res = await api.get('/students', { params: { class_id: selectedClassId.value, page_size: 500 } })
    students.value = res.data
    // Default all to present
    for (const s of students.value) {
      if (!records.value[s.id]) {
        records.value[s.id] = { status: 'present', remark: '' }
      }
    }
  } catch {}

  started.value = true
}

function setStatus(studentId, status) {
  records.value[studentId] = {
    status,
    remark: status === 'present' ? '' : (records.value[studentId]?.remark || ''),
  }
}

function batchToggle(status) {
  for (const s of students.value) {
    records.value[s.id] = { ...records.value[s.id], status }
  }
}

function resetAll() {
  for (const s of students.value) {
    records.value[s.id] = { status: 'present', remark: '' }
  }
}

async function saveSession() {
  if (!selectedClassId.value || !sessionDate.value) return
  saving.value = true
  try {
    const recordList = students.value.map(s => ({
      student_id: s.id,
      status: records.value[s.id]?.status || 'present',
      remark: records.value[s.id]?.remark || null,
    }))

    if (existingSessionId.value) {
      await api.put(`/attendance/sessions/${existingSessionId.value}`, {
        label: sessionLabel.value || null,
        records: recordList,
      })
      ElMessage.success('签到已更新')
    } else {
      const res = await api.post('/attendance/sessions', {
        class_id: selectedClassId.value,
        session_date: sessionDate.value,
        label: sessionLabel.value || null,
        records: recordList,
      })
      existingSessionId.value = res.data.id
      ElMessage.success('签到保存成功')
    }
    loadRecentSessions()
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
/* ===== PAGE CONTAINER ===== */
.at-page {
  margin: -12px; padding: 20px 24px 40px;
  min-height: calc(100vh - 50px);
  background: radial-gradient(circle at top, #112b72, #07142f 50%, #020817 100%);
  font-family: "PingFang SC", "Microsoft YaHei", sans-serif;
  max-width: 900px; margin-left: auto; margin-right: auto;
}

/* ===== PROGRESS STEPS ===== */
.progress-steps {
  display: flex; align-items: center; justify-content: center;
  gap: 0; margin-bottom: 20px; padding: 0 16px;
}
.step {
  display: flex; align-items: center; gap: 8px;
  color: rgba(255,255,255,0.3); transition: all 0.3s;
}
.step.active { color: rgba(255,255,255,0.9); }
.step.done { color: rgba(255,255,255,0.6); }
.step-num {
  width: 28px; height: 28px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 12px; font-weight: 700;
  background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.15);
}
.step.active .step-num {
  background: linear-gradient(135deg, #4f6cff, #5865ff);
  border-color: transparent; color: #fff;
}
.step.done .step-num {
  background: rgba(16,185,129,0.25); border-color: rgba(16,185,129,0.4); color: #10b981;
}
.step-label { font-size: 12px; font-weight: 500; white-space: nowrap; }
.step-line {
  width: 40px; height: 1px; margin: 0 8px;
  background: rgba(255,255,255,0.1); transition: background 0.3s;
}
.step-line.done { background: rgba(16,185,129,0.3); }

/* ===== RECENT BAR ===== */
.recent-bar {
  display: flex; align-items: center; gap: 6px; flex-wrap: wrap;
  padding: 10px 18px; margin-bottom: 20px;
  background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.08);
  border-radius: 12px; font-size: 13px; color: #8ea0c8;
}
.recent-icon { font-size: 15px; }
.recent-item { color: #c0d0f0; font-weight: 500; }

/* ===== BACK BUTTON ===== */
.back-btn {
  background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.12);
  color: #fff; padding: 10px 22px; border-radius: 14px;
  cursor: pointer; font-size: 14px; margin-bottom: 20px;
  transition: all 0.2s; font-family: inherit;
}
.back-btn:hover { background: rgba(255,255,255,0.14); }

/* ===== TAB BAR ===== */
.tab-bar { display: flex; gap: 4px; margin-bottom: 20px; }
.tab-btn {
  padding: 10px 24px; border-radius: 12px; font-size: 14px; font-weight: 500;
  border: 1px solid rgba(255,255,255,0.08); background: rgba(255,255,255,0.04);
  color: #8ea0c8; cursor: pointer; transition: all 0.2s; font-family: inherit;
}
.tab-btn:hover { background: rgba(255,255,255,0.08); color: #c0d0f0; }
.tab-btn.active { background: rgba(88,101,255,0.2); border-color: rgba(88,101,255,0.35); color: #a0b8ff; }

/* ===== ENTRY TOPBAR ===== */
.entry-topbar {
  display: flex; align-items: center; gap: 16px; margin-bottom: 20px;
}
.entry-context {
  color: rgba(255,255,255,0.7); font-size: 15px; font-weight: 500;
}

/* ===== TOOLBAR (stats) ===== */
.toolbar-glass {
  display: flex; gap: 8px; margin-bottom: 16px; flex-wrap: wrap; align-items: center;
  background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08);
  border-radius: 16px; padding: 12px 14px; backdrop-filter: blur(10px);
}
.tb-select { width: 180px; flex-shrink: 0; }
.tb-date-range { width: 260px; flex-shrink: 0; }

/* ===== STATS CARDS ===== */
.stats-mini { display: flex; gap: 12px; margin-bottom: 16px; flex-wrap: wrap; }
.stat-item {
  background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.1);
  border-radius: 14px; padding: 14px 22px; text-align: center; min-width: 100px; flex: 1;
}
.stat-num { display: block; font-size: 26px; font-weight: 800; color: #a0b8ff; }
.stat-label { font-size: 11px; color: #7d8fb9; letter-spacing: 0.5px; margin-top: 2px; }

/* ===== CLICKABLE STUDENT NAME ===== */
.student-link {
  color: #a0b8ff; cursor: pointer; text-decoration: underline;
  text-underline-offset: 3px; transition: color 0.15s;
}
.student-link:hover { color: #c0d0ff; }

/* ===== RATE CELL ===== */
.rate-cell { display: flex; align-items: center; gap: 10px; }

/* ===== DETAIL TAGS ===== */
.tag-late {
  display:inline-block; padding:2px 10px; border-radius:10px; font-size:12px; font-weight:600;
  background:rgba(245,158,11,0.18); color:#f59e0b;
}
.tag-excused {
  display:inline-block; padding:2px 10px; border-radius:10px; font-size:12px; font-weight:600;
  background:rgba(96,165,250,0.18); color:#60a5fa;
}
.tag-absent {
  display:inline-block; padding:2px 10px; border-radius:10px; font-size:12px; font-weight:600;
  background:rgba(239,68,68,0.18); color:#ef4444;
}

.glass-card-footer { padding: 10px 16px; display: flex; justify-content: center; border-top: 1px solid rgba(255,255,255,0.05); }

/* ===== TOOLBAR ACTION BTN ===== */
.action-btn-sm {
  padding: 5px 12px; border-radius: 8px; font-size: 11px; font-weight: 500;
  border: 1px solid rgba(255,255,255,0.12); background: rgba(255,255,255,0.05);
  color: #8ea0c8; cursor: pointer; transition: all 0.15s; font-family: inherit;
  white-space: nowrap;
}
.action-btn-sm:hover { background: rgba(255,255,255,0.12); color: #c0d0f0; }
.action-btn-sm.primary { background: rgba(88,101,255,0.2); border-color: rgba(88,101,255,0.35); color: #a0b8ff; }

.at-page :deep(.el-pagination button), .at-page :deep(.el-pager li) { color: #8ea0c8; background: transparent; }
.at-page :deep(.el-pager li.is-active) { background: rgba(88,101,255,0.25); color: #a0b8ff; border-radius: 8px; }

/* ===== GLASS CARD ===== */
.entry-card {
  background: rgba(12,26,61,0.72);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(90,120,255,0.25);
  border-radius: 32px; padding: 50px;
  box-shadow: 0 0 60px rgba(80,120,255,0.15);
}
.glass-card {
  background: rgba(12,26,61,0.65); backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid rgba(90,120,255,0.15); border-radius: 24px;
  overflow: hidden; box-shadow: 0 0 40px rgba(80,120,255,0.08);
}

/* ===== HERO ===== */
.hero { text-align: center; margin-bottom: 36px; }
.hero-icon {
  width: 100px; height: 100px; margin: 0 auto 20px;
  display: flex; align-items: center; justify-content: center;
  font-size: 46px; border-radius: 50%;
  background: radial-gradient(circle, rgba(100,120,255,0.4), transparent);
  border: 1px solid rgba(120,140,255,0.4);
}
.hero h1 { color: #fff; font-size: 38px; margin: 0 0 8px; font-weight: 700; }
.hero p { color: #8fa3d8; font-size: 16px; margin: 0; }

/* ===== FORM ===== */
.form-group { margin-bottom: 20px; }
.form-group label {
  display: block; color: #fff; margin-bottom: 8px;
  font-size: 15px; font-weight: 500;
}

/* ===== CTA BUTTON ===== */
.start-btn {
  width: 100%; height: 68px; margin-top: 8px;
  border: none; border-radius: 20px;
  background: linear-gradient(90deg, #4f6cff, #5865ff, #6d4cff);
  color: #fff; font-size: 24px; font-weight: 700; cursor: pointer;
  box-shadow: 0 12px 30px rgba(80,100,255,0.35);
  transition: all 0.2s; font-family: inherit;
  letter-spacing: 1px;
}
.start-btn:hover:not(:disabled) { transform: translateY(-2px); box-shadow: 0 16px 36px rgba(80,100,255,0.45); }
.start-btn:disabled { opacity: 0.35; cursor: not-allowed; transform: none; }
.save-btn { height: 60px; font-size: 20px; margin-top: 0; }

/* ===== SUMMARY TOOLBAR ===== */
.summary-toolbar {
  display: flex; align-items: center; justify-content: space-between;
  flex-wrap: wrap; gap: 10px; margin-bottom: 12px;
  padding: 12px 16px;
  background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08);
  border-radius: 14px;
}
.summary-counts { display: flex; gap: 14px; flex-wrap: wrap; }
.sc-item { font-size: 14px; font-weight: 600; }
.sc-item.present { color: #10b981; }
.sc-item.late { color: #f59e0b; }
.sc-item.excused { color: #60a5fa; }
.sc-item.absent { color: #ef4444; }

.batch-actions { display: flex; gap: 6px; flex-wrap: wrap; }
.action-btn-sm {
  padding: 4px 10px; border-radius: 8px; font-size: 11px; font-weight: 500;
  border: 1px solid rgba(255,255,255,0.12); background: rgba(255,255,255,0.05);
  color: #8ea0c8; cursor: pointer; transition: all 0.15s; font-family: inherit;
  white-space: nowrap;
}
.action-btn-sm:hover { background: rgba(255,255,255,0.12); color: #c0d0f0; }
.action-btn-sm.reset { color: #fca5a5; border-color: rgba(239,68,68,0.2); }
.action-btn-sm.reset:hover { background: rgba(239,68,68,0.1); }

/* ===== NOTICE BAR ===== */
.notice-bar {
  padding: 10px 16px; margin-bottom: 12px;
  background: rgba(234,179,8,0.1); border: 1px solid rgba(234,179,8,0.25);
  border-radius: 12px; color: #facc15; font-size: 13px;
}

/* ===== STATUS TOGGLE BUTTONS ===== */
.status-toggle { display: flex; gap: 4px; }
.st-btn {
  padding: 5px 10px; border-radius: 8px; font-size: 12px; font-weight: 500;
  border: 1px solid rgba(255,255,255,0.10); background: rgba(255,255,255,0.04);
  color: rgba(255,255,255,0.30); cursor: pointer; transition: all 0.15s;
  font-family: inherit; white-space: nowrap;
}
.st-btn:hover { background: rgba(255,255,255,0.10); color: rgba(255,255,255,0.65); }
.st-btn.present.on { background: rgba(16,185,129,0.22); border-color: rgba(16,185,129,0.45); color: #10b981; font-weight: 600; }
.st-btn.late.on    { background: rgba(245,158,11,0.22); border-color: rgba(245,158,11,0.45); color: #f59e0b; font-weight: 600; }
.st-btn.excused.on { background: rgba(96,165,250,0.22); border-color: rgba(96,165,250,0.45); color: #60a5fa; font-weight: 600; }
.st-btn.absent.on  { background: rgba(239,68,68,0.22); border-color: rgba(239,68,68,0.50); color: #ef4444; font-weight: 600; }

/* ===== SAVE BAR ===== */
.save-bar { margin-top: 20px; }
.save-footer { text-align: center; margin-top: 10px; color: #7d8fb9; font-size: 13px; }

/* ===== TABLE OVERRIDES ===== */
.at-page :deep(.el-table) { background: transparent; --el-table-bg-color: transparent; --el-table-tr-bg-color: transparent; }
.at-page :deep(.el-table th.el-table__cell) { background: rgba(255,255,255,0.03); color: #8ea0c8; border-bottom-color: rgba(255,255,255,0.06); font-weight: 600; font-size: 12px; }
.at-page :deep(.el-table td.el-table__cell) { background: transparent; color: #e0e8f8; border-bottom-color: rgba(255,255,255,0.04); }
.at-page :deep(.el-table--striped .el-table__body tr.el-table__row--striped td.el-table__cell) { background: rgba(255,255,255,0.015); }
.at-page :deep(.el-table__body tr:hover td.el-table__cell) { background: rgba(88,101,255,0.06) !important; }
.at-page :deep(.el-input__wrapper) { background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.12); border-radius: 10px; box-shadow: none; }
.at-page :deep(.el-input__wrapper:hover) { border-color: rgba(255,255,255,0.2); }
.at-page :deep(.el-input.is-focus .el-input__wrapper) { border-color: rgba(100,120,255,0.4); box-shadow: 0 0 0 1px rgba(100,120,255,0.15); }
.at-page :deep(.el-input__inner) { color: #fff; }
.at-page :deep(.el-select-dropdown) { background: #0f1e3d; border: 1px solid rgba(100,120,255,0.25); }
.at-page :deep(.el-select-dropdown__item) { color: #c0d0f0; }
.at-page :deep(.el-select-dropdown__item.hover) { background: rgba(100,120,255,0.15); }
.at-page :deep(.el-select-dropdown__item.selected) { color: #a0b8ff; font-weight: 600; }
.at-page :deep(.el-dialog) { background: rgba(12,26,61,0.95); backdrop-filter: blur(20px); border: 1px solid rgba(100,120,255,0.2); border-radius: 20px; }
.at-page :deep(.el-dialog__title) { color: #fff; }
.at-page :deep(.el-dialog__body) { color: #c0d0f0; }

/* Select & date-picker large inputs */
.at-select-el, .at-date-el, .at-input-el { width: 100%; display: block; }
.at-page :deep(.at-select-el .el-input__wrapper),
.at-page :deep(.at-date-el .el-input__wrapper),
.at-page :deep(.at-input-el .el-input__wrapper) {
  height: 60px; background: rgba(255,255,255,0.03);
  border: 1px solid rgba(100,120,255,0.2); border-radius: 16px;
  box-shadow: none;
}
.at-page :deep(.at-select-el .el-input__inner),
.at-page :deep(.at-date-el .el-input__inner),
.at-page :deep(.at-input-el .el-input__inner) {
  color: #fff; font-size: 17px;
}
.at-page :deep(.at-select-el .el-input__wrapper:hover),
.at-page :deep(.at-date-el .el-input__wrapper:hover),
.at-page :deep(.at-input-el .el-input__wrapper:hover) {
  border-color: rgba(100,120,255,0.35);
}
.at-page :deep(.el-select.is-focus .el-input__wrapper) {
  border-color: rgba(100,120,255,0.5);
  box-shadow: 0 0 0 1px rgba(100,120,255,0.15);
}
.at-page :deep(.el-select .el-input__suffix) { color: rgba(255,255,255,0.5); }

/* ===== MOBILE ===== */
.mobile-list { display: flex; flex-direction: column; gap: 8px; max-height: calc(100vh - 340px); overflow-y: auto; }
.student-card {
  padding: 12px; background: rgba(12,26,61,0.5);
  border: 1px solid rgba(255,255,255,0.06); border-radius: 12px;
}
.student-card.present { border-left: 3px solid #10b981; }
.student-card.late { border-left: 3px solid #f59e0b; }
.student-card.excused { border-left: 3px solid #60a5fa; }
.student-card.absent { border-left: 3px solid #ef4444; }
.sc-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.sc-name { font-size: 15px; font-weight: bold; color: #fff; }
.sc-gender { font-size: 12px; color: #8ea0c8; }
.sc-status { display: flex; gap: 6px; }
.st-btn-sm { padding: 6px 10px; font-size: 14px; }

/* ===== RESPONSIVE ===== */
@media (max-width: 768px) {
  .at-page { max-width: 100%; padding: 12px 12px 24px; }
  .entry-card { padding: 30px 18px; }
  .hero h1 { font-size: 30px; }
  .hero-icon { width: 80px; height: 80px; font-size: 36px; }
  .start-btn { height: 58px; font-size: 20px; }
  .step-label { font-size: 10px; }
  .step-line { width: 24px; }
  .summary-toolbar { flex-direction: column; align-items: stretch; }
}
</style>
