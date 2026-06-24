<template>
  <div class="se-page">
    <!-- ===== PROGRESS STEPS ===== -->
    <div class="progress-steps">
      <div class="step" :class="{ active: currentStep >= 1, done: currentStep > 1 }">
        <span class="step-num">{{ currentStep > 1 ? '✓' : '1' }}</span>
        <span class="step-label">选择班级</span>
      </div>
      <span class="step-line" :class="{ done: currentStep > 1 }"></span>
      <div class="step" :class="{ active: currentStep >= 2, done: currentStep > 2 }">
        <span class="step-num">{{ currentStep > 2 ? '✓' : '2' }}</span>
        <span class="step-label">选择项目</span>
      </div>
      <span class="step-line" :class="{ done: currentStep > 2 }"></span>
      <div class="step" :class="{ active: currentStep >= 3 }">
        <span class="step-num">3</span>
        <span class="step-label">逐人录入</span>
      </div>
    </div>

    <!-- ===== RECENT RECORDS ===== -->
    <div class="recent-bar" v-if="todaySummary && todaySummary.total > 0">
      <span class="recent-icon">📋</span>
      <span>今天已录入：</span>
      <span v-for="(r, i) in todaySummary.records.slice(0, 3)" :key="i" class="recent-item">
        {{ r.class_label }} {{ r.event_name }} {{ r.student_count }}人{{ i < Math.min(todaySummary.records.length, 3) - 1 ? ' · ' : '' }}
      </span>
      <span class="recent-total">（共 {{ todaySummary.total }} 条）</span>
    </div>

    <!-- ===== SELECTION STEP ===== -->
    <div v-if="!started" class="se-select">
      <button class="back-btn" @click="$router.push('/admin/dashboard')">← 返回仪表盘</button>

      <div class="entry-card">
        <!-- Hero -->
        <div class="hero">
          <div class="hero-icon">📋</div>
          <h1>成绩录入</h1>
          <p>选择班级和项目，开始逐人录入成绩</p>
        </div>

        <!-- Form -->
        <div class="form-group">
          <label>👥 班级</label>
          <el-select v-model="selectedClassId" placeholder="请选择班级" size="large" class="se-select-el">
            <el-option v-for="c in classes" :key="c.id" :label="c.label" :value="c.id" />
          </el-select>
        </div>

        <div class="form-group">
          <label>🏃 项目</label>
          <el-select v-model="selectedEventId" placeholder="请选择项目" size="large" class="se-select-el">
            <el-option v-for="e in events" :key="e.id" :label="e.name" :value="e.id" />
          </el-select>
        </div>

        <div class="form-group">
          <label>📅 日期</label>
          <el-date-picker v-model="testDate" type="date" value-format="YYYY-MM-DD" size="large" class="se-date-el" />
        </div>

        <!-- CTA Button -->
        <button class="start-btn" @click="startEntry" :disabled="!selectedClassId || !selectedEventId">
          开始逐人录入 →
        </button>

        <!-- Action Grid -->
        <div class="action-grid">
          <button class="tool-btn" :disabled="!selectedClassId" @click="$refs.batchFile.click()">
            <div class="tool-icon excel">📊</div>
            <div class="tool-text">
              <h3>批量导入成绩</h3>
              <span>支持 Excel 文件导入</span>
            </div>
          </button>
          <button class="tool-btn" :disabled="!selectedClassId" @click="downloadTemplate">
            <div class="tool-icon download">⬇️</div>
            <div class="tool-text">
              <h3>下载导入模板</h3>
              <span>下载标准导入模板</span>
            </div>
          </button>
          <input type="file" ref="batchFile" accept=".xlsx" style="display:none" @change="batchImport" />
        </div>

        <div class="tip">ℹ Excel格式：学号 ｜ 姓名 ｜ 项目 ｜ 成绩 ｜ 备注（可选）</div>
      </div>
    </div>

    <!-- ===== ENTRY STEP ===== -->
    <div v-else class="se-entry">
      <div class="entry-topbar">
        <button class="back-btn" @click="started = false">← 返回选择</button>
        <span class="entry-context">{{ selectedClassLabel }} · {{ selectedEventName }}</span>
      </div>

      <div class="entry-card entry-card--entry" v-if="currentStudent">
        <!-- Student nav -->
        <div class="student-nav">
          <button class="nav-arrow" @click="prevStudent" :disabled="currentIndex === 0">◀</button>
          <div class="student-info">
            <div class="student-name">{{ currentStudent.name }}</div>
            <div class="student-meta">{{ currentStudent.student_id }} · {{ currentStudent.gender === 'M' ? '男' : '女' }}</div>
          </div>
          <button class="nav-arrow" @click="nextStudent" :disabled="currentIndex >= students.length - 1">▶</button>
        </div>

        <!-- Progress -->
        <div class="entry-progress">
          <el-progress :percentage="Math.round((currentIndex + 1) / students.length * 100)" :stroke-width="6" :show-text="false" color="#5865ff" />
          <span class="entry-progress-text">{{ currentIndex + 1 }} / {{ students.length }}</span>
        </div>

        <!-- Input -->
        <div class="entry-input-area">
          <el-input
            v-model="currentValue"
            :placeholder="placeholder"
            size="large"
            class="entry-input"
            @input="onValueChange"
            clearable
          />
          <div class="entry-hint">支持: {{ formatHint }}</div>
        </div>

        <!-- Save button -->
        <button class="start-btn save-btn" @click="saveAndNext" :disabled="saving || !currentValue">
          💾 保存并下一个
        </button>

        <!-- Result -->
        <div class="entry-result" v-if="currentScore !== null">
          <div class="result-score">{{ currentScore }} <span>分</span></div>
          <div class="result-change">
            <template v-if="previousScore !== null">
              <span class="rc-prev">上次 {{ previousScore }}分</span>
              <span v-if="isPraise" class="rc-praise">↑ 进步表扬 ✨</span>
              <span v-else-if="isWarning" class="rc-warning">↓ 橙色预警 🟠</span>
              <span v-else-if="change > 0" class="rc-up">↑ +{{ change }}</span>
              <span v-else-if="change < 0" class="rc-down">↓ {{ change }}</span>
              <span v-else class="rc-same">→ 持平</span>
            </template>
            <span v-else class="rc-first">首次测试</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../../api'

const classes = ref([])
const events = ref([])
const selectedClassId = ref(null)
const selectedEventId = ref(null)
const testDate = ref(new Date().toISOString().split('T')[0])
const started = ref(false)

const students = ref([])
const currentIndex = ref(0)
const currentValue = ref('')
const currentScore = ref(null)
const previousScore = ref(null)
const change = ref(null)
const isPraise = ref(false)
const isWarning = ref(false)
const saving = ref(false)

const todaySummary = ref(null)

const selectedClassLabel = computed(() => {
  const c = classes.value.find(c => c.id === selectedClassId.value)
  return c ? c.label : ''
})
const selectedEventName = computed(() => {
  const e = events.value.find(e => e.id === selectedEventId.value)
  return e ? e.name : ''
})
const selectedEvent = computed(() => events.value.find(e => e.id === selectedEventId.value))
const currentStudent = computed(() => students.value[currentIndex.value])

const currentStep = computed(() => {
  if (started.value) return 3
  if (!selectedClassId.value) return 1
  if (!selectedEventId.value) return 2
  return 3
})

const placeholder = computed(() => {
  if (!selectedEvent.value) return '输入成绩'
  const fmt = selectedEvent.value.input_format
  if (fmt === 'time_ms') return "3分30 / 3'30"
  if (fmt === 'decimal_seconds') return '8.1'
  if (fmt === 'decimal_meters') return '1.95'
  return '170'
})

const formatHint = computed(() => {
  if (!selectedEvent.value) return ''
  const fmt = selectedEvent.value.input_format
  if (fmt === 'time_ms') return '3分30、3分30秒、3\'30、3\'30"'
  if (fmt === 'decimal_seconds') return '秒.百分秒，如 8.1、22.51'
  if (fmt === 'decimal_meters') return '十进制米，如 1.95'
  return '整数，如 170'
})

onMounted(async () => {
  const [cRes, eRes] = await Promise.all([api.get('/events/classes'), api.get('/events')])
  classes.value = cRes.data; events.value = eRes.data
  loadTodaySummary()
})

async function loadTodaySummary() {
  try {
    const res = await api.get('/scores/today-summary')
    todaySummary.value = res.data
  } catch {}
}

async function startEntry() {
  const res = await api.get(`/scores/student-list/${selectedClassId.value}`, { params: { event_id: selectedEventId.value } })
  students.value = res.data; currentIndex.value = 0; resetInput(); started.value = true
  loadTodaySummary()
}

function prevStudent() { if (currentIndex.value > 0) { currentIndex.value--; resetInput() } }
function nextStudent() { if (currentIndex.value < students.value.length - 1) { currentIndex.value++; resetInput() } }

function resetInput() {
  currentValue.value = ''; currentScore.value = null; previousScore.value = null
  change.value = null; isPraise.value = false; isWarning.value = false
}

async function onValueChange() {
  if (!currentValue.value) { currentScore.value = null; return }
  try {
    const res = await api.post('/scores/batch', { scores: [{ student_id: currentStudent.value.id, event_id: selectedEventId.value, raw_value: currentValue.value, test_date: testDate.value }] })
    const r = res.data[0]
    currentScore.value = r.earned_score; previousScore.value = r.previous_score
    change.value = r.change; isPraise.value = r.is_praise; isWarning.value = r.is_warning
  } catch { currentScore.value = null }
}

async function batchImport(e) {
  const file = e.target.files[0]
  if (!file) return
  const loading = ElMessage({ message: '正在导入成绩...', type: 'info', duration: 0 })
  try {
    const form = new FormData()
    form.append('file', file)
    const params = { class_id: selectedClassId.value, test_date: testDate.value }
    const res = await api.post('/scores/batch-import', form, { params })
    loading.close()
    const r = res.data
    let msg = `导入成功：${r.imported} 条成绩`
    if (r.skipped.length) msg += `，${r.skipped.length} 条跳过`
    ElMessage.success({ message: msg, duration: 5000 })
    if (r.skipped.length > 0 && r.skipped.length <= 20) {
      setTimeout(() => { ElMessage.warning({ message: r.skipped.join('；'), duration: 8000 }) }, 500)
    }
    e.target.value = ''
    loadTodaySummary()
  } catch (err) {
    loading.close()
    ElMessage.error(err.response?.data?.detail || '导入失败')
  }
}

async function downloadTemplate() {
  try {
    const res = await api.get('/scores/batch-import-template', { responseType: 'blob' })
    const url = window.URL.createObjectURL(new Blob([res.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', '成绩导入模板.xlsx')
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    ElMessage.success('模板已下载')
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '下载模板失败')
  }
}

async function saveAndNext() {
  if (!currentValue.value) { ElMessage.warning('请先输入成绩'); return }
  saving.value = true
  try {
    await api.post('/scores/batch', { scores: [{ student_id: currentStudent.value.id, event_id: selectedEventId.value, raw_value: currentValue.value, test_date: testDate.value }] })
    ElMessage.success('保存成功')
    loadTodaySummary()
    if (currentIndex.value < students.value.length - 1) { nextStudent() } else { ElMessage.success('全部录入完成！') }
  } catch { ElMessage.error('保存失败') } finally { saving.value = false }
}
</script>

<style scoped>
/* ===== PAGE CONTAINER ===== */
.se-page {
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
.recent-total { color: #7d8fb9; margin-left: 4px; }

/* ===== BACK BUTTON ===== */
.back-btn {
  background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.12);
  color: #fff; padding: 10px 22px; border-radius: 14px;
  cursor: pointer; font-size: 14px; margin-bottom: 20px;
  transition: all 0.2s; font-family: inherit;
}
.back-btn:hover { background: rgba(255,255,255,0.14); }

/* ===== ENTRY TOPBAR ===== */
.entry-topbar {
  display: flex; align-items: center; gap: 16px; margin-bottom: 20px;
}
.entry-context {
  color: rgba(255,255,255,0.7); font-size: 15px; font-weight: 500;
}

/* ===== GLASS CARD ===== */
.entry-card {
  background: rgba(12,26,61,0.72);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(90,120,255,0.25);
  border-radius: 32px; padding: 50px;
  box-shadow: 0 0 60px rgba(80,120,255,0.15);
}
.entry-card--entry { padding: 40px; }

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

/* Element Plus select & date-picker glass overrides */
.se-select-el, .se-date-el { width: 100%; display: block; }
.se-page :deep(.se-select-el .el-input__wrapper),
.se-page :deep(.se-date-el .el-input__wrapper) {
  height: 60px; background: rgba(255,255,255,0.03);
  border: 1px solid rgba(100,120,255,0.2); border-radius: 16px;
  box-shadow: none;
}
.se-page :deep(.se-select-el .el-input__inner),
.se-page :deep(.se-date-el .el-input__inner) {
  color: #fff; font-size: 17px;
}
.se-page :deep(.se-select-el .el-input__wrapper:hover),
.se-page :deep(.se-date-el .el-input__wrapper:hover) {
  border-color: rgba(100,120,255,0.35);
}
.se-page :deep(.el-select.is-focus .el-input__wrapper) {
  border-color: rgba(100,120,255,0.5);
  box-shadow: 0 0 0 1px rgba(100,120,255,0.15);
}
.se-page :deep(.el-select .el-input__suffix) { color: rgba(255,255,255,0.5); }
.se-page :deep(.el-select-dropdown) { background: #0f1e3d; border: 1px solid rgba(100,120,255,0.25); }
.se-page :deep(.el-select-dropdown__item) { color: #c0d0f0; }
.se-page :deep(.el-select-dropdown__item.hover),
.se-page :deep(.el-select-dropdown__item:hover) { background: rgba(100,120,255,0.15); }
.se-page :deep(.el-select-dropdown__item.selected) { color: #a0b8ff; font-weight: 600; }
.se-page :deep(.el-date-picker__header-label) { color: #fff; }
.se-page :deep(.el-picker-panel) { background: #0f1e3d; border-color: rgba(100,120,255,0.25); color: #c0d0f0; }

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
.save-btn { height: 60px; font-size: 20px; }

/* ===== ACTION GRID ===== */
.action-grid { margin-top: 24px; display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; }
.tool-btn {
  display: flex; align-items: center; gap: 16px;
  background: rgba(255,255,255,0.04); border: 1px solid rgba(100,120,255,0.18);
  border-radius: 18px; padding: 20px; color: #fff; cursor: pointer;
  text-align: left; font-family: inherit;
  transition: all 0.2s;
}
.tool-btn:hover:not(:disabled) { background: rgba(255,255,255,0.08); border-color: rgba(100,120,255,0.35); }
.tool-btn:disabled { opacity: 0.3; cursor: not-allowed; }
.tool-icon {
  width: 52px; height: 52px; display: flex; align-items: center; justify-content: center;
  font-size: 26px; border-radius: 14px; flex-shrink: 0;
}
.tool-icon.excel { background: #0c6f42; }
.tool-icon.download { background: #245dff; }
.tool-text h3 { margin: 0 0 4px; font-size: 16px; font-weight: 600; }
.tool-text span { color: #8ea0c8; font-size: 12px; }

/* ===== TIP ===== */
.tip { margin-top: 24px; text-align: center; color: #7d8fb9; font-size: 13px; }

/* ===== ENTRY STEP ===== */
.se-entry { max-width: 560px; margin: 0 auto; }

/* Student nav */
.student-nav {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 20px;
}
.nav-arrow {
  width: 44px; height: 44px; border-radius: 50%;
  background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.15);
  color: #c0d0f0; font-size: 16px; cursor: pointer; transition: all 0.2s;
  display: flex; align-items: center; justify-content: center; font-family: inherit;
}
.nav-arrow:hover:not(:disabled) { background: rgba(255,255,255,0.14); border-color: rgba(100,120,255,0.4); }
.nav-arrow:disabled { opacity: 0.2; cursor: not-allowed; }
.student-info { text-align: center; flex: 1; }
.student-name { font-size: 28px; font-weight: 700; color: #fff; }
.student-meta { font-size: 14px; color: #8fa3d8; margin-top: 4px; }

/* Entry progress */
.entry-progress { display: flex; align-items: center; gap: 10px; margin-bottom: 28px; }
.se-page :deep(.el-progress-bar__outer) { background: rgba(255,255,255,0.06); border-radius: 10px; }
.entry-progress-text { font-size: 12px; color: #7d8fb9; white-space: nowrap; }

/* Entry input */
.entry-input-area { margin: 12px 0 8px; }
.se-page :deep(.entry-input .el-input__wrapper) {
  border-radius: 16px;
  background: rgba(255,255,255,0.03);
  border: 2px solid rgba(100,120,255,0.2);
  box-shadow: none;
}
.se-page :deep(.entry-input .el-input__inner) {
  text-align: center; font-size: 32px; height: 64px;
  color: #fff; font-weight: 600; letter-spacing: 1px;
}
.se-page :deep(.entry-input.el-input.is-focus .el-input__wrapper) {
  border-color: #5865ff;
  box-shadow: 0 0 0 2px rgba(88,101,255,0.15);
}
.entry-hint { font-size: 12px; color: #7d8fb9; margin-top: 8px; text-align: center; }

/* Entry result */
.entry-result {
  margin: 20px 0 0; padding: 20px; border-radius: 16px;
  background: rgba(88,101,255,0.08); border: 1px solid rgba(88,101,255,0.15);
  text-align: center;
}
.result-score { font-size: 42px; font-weight: 800; color: #a0b8ff; }
.result-score span { font-size: 18px; font-weight: 400; color: #7d8fb9; }
.result-change { margin-top: 10px; font-size: 14px; }
.rc-prev { color: #7d8fb9; margin-right: 8px; }
.rc-praise { color: #10b981; font-weight: 600; }
.rc-warning { color: #f59e0b; font-weight: 600; animation: warn-pulse 1.5s ease-in-out infinite; }
@keyframes warn-pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.35; } }
.rc-up { color: #10b981; }
.rc-down { color: #ef4444; }
.rc-same { color: #7d8fb9; }
.rc-first { color: #7d8fb9; }

/* ===== RESPONSIVE ===== */
@media (max-width: 768px) {
  .se-page { max-width: 100%; padding: 12px 12px 24px; }
  .entry-card { padding: 30px 18px; }
  .entry-card--entry { padding: 24px 16px; }
  .hero h1 { font-size: 30px; }
  .hero-icon { width: 80px; height: 80px; font-size: 36px; }
  .action-grid { grid-template-columns: 1fr; }
  .start-btn { height: 58px; font-size: 20px; }
  .step-label { font-size: 10px; }
  .step-line { width: 24px; }
  .student-name { font-size: 22px; }
}
</style>
