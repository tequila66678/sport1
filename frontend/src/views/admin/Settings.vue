<template>
  <div class="settings-page">
    <button class="back-btn" @click="$router.push('/admin/dashboard')">← 返回仪表盘</button>
    <h1>⚙️ 系统设置</h1>

    <div class="glass-card">
      <el-tabs v-model="activeTab">
        <el-tab-pane v-if="isSuper" label="项目设置" name="events">
          <button class="action-btn primary" @click="showAddEvent = true">＋ 新增项目</button>
          <div v-for="e in events" :key="e.id" class="item-card">
            <div class="item-info">
              <div class="item-name">{{ e.name }}</div>
              <div class="item-meta">{{ e.gender === 'M' ? '男' : e.gender === 'F' ? '女' : '通用' }} | {{ e.higher_better ? '越大越好' : '越小越好' }} | 单位:{{ e.unit }}</div>
            </div>
            <div class="item-actions">
              <button class="action-btn small" @click="editStandards(e)">评分标准</button>
              <button class="action-btn small danger" @click="deleteEvent(e)">删除</button>
            </div>
          </div>

          <el-dialog v-model="showAddEvent" title="新增项目" width="90%">
            <el-form label-width="60px">
              <el-form-item label="名称"><el-input v-model="newEvent.name" /></el-form-item>
              <el-form-item label="性别">
                <el-select v-model="newEvent.gender" style="width:100%">
                  <el-option label="通用" value="both" /><el-option label="男" value="M" /><el-option label="女" value="F" />
                </el-select>
              </el-form-item>
              <el-form-item label="方向">
                <el-select v-model="newEvent.higher_better" style="width:100%">
                  <el-option label="越大越好" :value="true" /><el-option label="越小越好" :value="false" />
                </el-select>
              </el-form-item>
              <el-form-item label="单位"><el-input v-model="newEvent.unit" /></el-form-item>
              <el-form-item label="格式">
                <el-select v-model="newEvent.input_format" style="width:100%">
                  <el-option label="分'秒" value="time_ms" /><el-option label="十进制秒" value="decimal_seconds" />
                  <el-option label="十进制米" value="decimal_meters" /><el-option label="整数" value="integer" />
                </el-select>
              </el-form-item>
              <button class="action-btn primary" @click="addEvent" style="width:100%">确认新增</button>
            </el-form>
          </el-dialog>

          <el-dialog v-model="showStandards" title="编辑评分标准" width="90%">
            <div v-for="i in 10" :key="i" style="display:flex;align-items:center;margin-bottom:8px">
              <span style="width:40px;font-size:13px;color:#8ea0c8">{{ 11 - i }}分</span>
              <el-input v-model="standardsForm[i - 1]" style="flex:1" size="small" />
            </div>
            <button class="action-btn primary" @click="saveStandards" style="width:100%;margin-top:8px">保存</button>
          </el-dialog>
        </el-tab-pane>

        <el-tab-pane label="管理员" name="admins">
          <button class="action-btn primary" @click="showAddAdmin = true">＋ 新增管理员</button>
          <div v-for="a in admins" :key="a.id" class="item-card">
            <div class="item-info">
              <div class="item-name">{{ a.display_name }}</div>
              <div class="item-meta">{{ a.username }} | {{ a.role === 'super' ? '超管' : a.role === 'school_admin' ? '学校管理员' : '老师' }}</div>
            </div>
            <div class="item-actions">
              <button v-if="isSuper" class="action-btn small" @click="editAdmin(a)">编辑</button>
              <button class="action-btn small danger" @click="deleteAdmin(a)">删除</button>
            </div>
          </div>

          <el-dialog v-model="showAddAdmin" title="新增管理员" width="90%">
            <el-form label-width="60px">
              <el-form-item label="用户名"><el-input v-model="newAdmin.username" /></el-form-item>
              <el-form-item label="密码"><el-input v-model="newAdmin.password" type="password" /></el-form-item>
              <el-form-item label="姓名"><el-input v-model="newAdmin.display_name" /></el-form-item>
              <el-form-item label="角色">
                <el-select v-model="newAdmin.role" style="width:100%">
                  <el-option v-if="isSuper" label="超管" value="super" />
                  <el-option v-if="isSuper" label="学校管理员" value="school_admin" />
                  <el-option label="老师" value="teacher" />
                </el-select>
              </el-form-item>
              <el-form-item v-if="isSuper && newAdmin.role !== 'super'" label="学校">
                <el-select v-model="newAdmin.school_id" style="width:100%" placeholder="选择学校">
                  <el-option v-for="s in allSchools" :key="s.id" :value="s.id" :label="s.name" />
                </el-select>
              </el-form-item>
              <button class="action-btn primary" @click="addAdmin" style="width:100%">确认新增</button>
            </el-form>
          </el-dialog>

          <el-dialog v-model="showEditAdmin" title="编辑管理员" width="90%">
            <el-form label-width="60px">
              <el-form-item label="用户名"><el-input :model-value="editAdminForm.username" disabled /></el-form-item>
              <el-form-item label="姓名"><el-input v-model="editAdminForm.display_name" /></el-form-item>
              <el-form-item label="新密码"><el-input v-model="editAdminForm.password" type="password" placeholder="留空不修改" /></el-form-item>
              <el-form-item label="角色">
                <el-select v-model="editAdminForm.role" style="width:100%">
                  <el-option label="超管" value="super" />
                  <el-option label="学校管理员" value="school_admin" />
                  <el-option label="老师" value="teacher" />
                </el-select>
              </el-form-item>
              <el-form-item v-if="editAdminForm.role !== 'super'" label="学校">
                <el-select v-model="editAdminForm.school_id" style="width:100%" placeholder="选择学校">
                  <el-option v-for="s in allSchools" :key="s.id" :value="s.id" :label="s.name" />
                </el-select>
              </el-form-item>
              <button class="action-btn primary" @click="saveEditAdmin" style="width:100%">保存修改</button>
            </el-form>
          </el-dialog>
        </el-tab-pane>

        <el-tab-pane v-if="isSuper" label="学校管理" name="schools">
          <button class="action-btn primary" @click="showAddSchool = true">＋ 新建学校</button>
          <div v-for="s in allSchools" :key="s.id" class="item-card">
            <div class="item-info">
              <div class="item-name">{{ s.name }}</div>
            </div>
            <div class="item-actions">
              <button class="action-btn small" @click="editSchool(s)">编辑</button>
              <button class="action-btn small danger" @click="deleteSchool(s)">删除</button>
            </div>
          </div>

          <el-dialog v-model="showAddSchool" title="新建学校" width="90%">
            <el-form label-width="60px">
              <el-form-item label="名称"><el-input v-model="newSchoolName" /></el-form-item>
              <button class="action-btn primary" @click="addSchool" style="width:100%">确认新建</button>
            </el-form>
          </el-dialog>

          <el-dialog v-model="showEditSchool" title="编辑学校" width="90%">
            <el-form label-width="60px">
              <el-form-item label="名称"><el-input v-model="editSchoolName" /></el-form-item>
              <button class="action-btn primary" @click="saveEditSchool" style="width:100%">保存</button>
            </el-form>
          </el-dialog>
        </el-tab-pane>

        <el-tab-pane label="系统设置" name="config">
          <div class="config-section">
            <el-form label-width="100px">
              <el-form-item label="学校名称"><el-input v-model="config.school_name" /></el-form-item>
              <el-form-item label="表扬阈值">
                <el-input-number v-model="config.praise_threshold" :min="1" :max="10" size="small" />
              </el-form-item>
              <el-form-item label="预警阈值">
                <el-input-number v-model="config.warning_threshold" :min="1" :max="10" size="small" />
              </el-form-item>
              <el-form-item label="设计者"><el-input v-model="config.designer" /></el-form-item>
              <el-form-item>
                <button class="action-btn primary" @click="saveConfig" style="width:100%">保存设置</button>
              </el-form-item>
            </el-form>

            <el-divider />
            <h4>数据维护</h4>
            <button class="action-btn" @click="backupData" style="width:100%;margin-bottom:8px">📥 备份全部数据 (Excel)</button>
            <input type="file" ref="restoreFile" accept=".xlsx" style="display:none" @change="restoreData" />
            <button class="action-btn" @click="$refs.restoreFile.click()" style="width:100%;margin-bottom:8px">📤 导入备份数据</button>

            <el-divider />
            <h4 style="color:#f59e0b">危险操作</h4>
            <button class="action-btn danger" @click="clearScores" style="width:100%">⚠ 清空所有成绩数据</button>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../../api'

const adminInfo = JSON.parse(localStorage.getItem('admin_info') || '{}')
const isSuper = adminInfo.role === 'super'

const activeTab = ref(isSuper ? 'events' : 'admins')
const events = ref([])
const admins = ref([])
const config = ref({ school_name: '', praise_threshold: 1, warning_threshold: 2, designer: '' })

const showAddEvent = ref(false)
const newEvent = ref({ name: '', gender: 'both', higher_better: true, unit: '', input_format: 'decimal_seconds' })
const showStandards = ref(false)
const editingEventId = ref(null)
const standardsForm = ref(Array(10).fill(''))

const showAddAdmin = ref(false)
const newAdmin = ref({ username: '', password: '', display_name: '', role: 'teacher', school_id: null })
const showEditAdmin = ref(false)
const editAdminForm = ref({ id: null, username: '', display_name: '', password: '', role: 'teacher', school_id: null })
const allSchools = ref([])

onMounted(async () => {
  try {
    const [eRes, aRes, cRes] = await Promise.all([api.get('/events'), api.get('/admins'), api.get('/config')])
    events.value = eRes.data; admins.value = aRes.data
    for (const c of cRes.data) { if (c.key in config.value) config.value[c.key] = c.key.includes('threshold') ? parseInt(c.value) : c.value }
  } catch {}
  if (isSuper) {
    try { const sRes = await api.get('/schools'); allSchools.value = sRes.data } catch {}
  }
})

async function addEvent() {
  await api.post('/events', newEvent.value); ElMessage.success('已新增'); showAddEvent.value = false
  newEvent.value = { name: '', gender: 'both', higher_better: true, unit: '', input_format: 'decimal_seconds' }
  const res = await api.get('/events'); events.value = res.data
}

async function deleteEvent(row) {
  await ElMessageBox.confirm(`确定删除 ${row.name}？`); await api.delete(`/events/${row.id}`)
  const res = await api.get('/events'); events.value = res.data
}

function editStandards(row) {
  editingEventId.value = row.id
  const stds = [...row.standards].sort((a, b) => b.score - a.score)
  standardsForm.value = stds.map(s => s.standard_value); showStandards.value = true
}

async function saveStandards() {
  const payload = []
  for (let i = 0; i < 10; i++) { if (standardsForm.value[i]) payload.push({ gender: 'both', score: 10 - i, standard_value: standardsForm.value[i] }) }
  await api.put(`/events/${editingEventId.value}/standards`, payload); ElMessage.success('已更新'); showStandards.value = false
  const res = await api.get('/events'); events.value = res.data
}

async function addAdmin() {
  await api.post('/admins', newAdmin.value); ElMessage.success('已创建'); showAddAdmin.value = false
  const res = await api.get('/admins'); admins.value = res.data
}

async function deleteAdmin(row) {
  await ElMessageBox.confirm(`确定删除 ${row.display_name}？`); await api.delete(`/admins/${row.id}`)
  const res = await api.get('/admins'); admins.value = res.data
}

function editAdmin(a) {
  editAdminForm.value = { id: a.id, username: a.username, display_name: a.display_name, password: '', role: a.role, school_id: a.school_id }
  showEditAdmin.value = true
}

async function saveEditAdmin() {
  const payload = { display_name: editAdminForm.value.display_name, role: editAdminForm.value.role, school_id: editAdminForm.value.school_id }
  if (editAdminForm.value.password) payload.password = editAdminForm.value.password
  await api.put(`/admins/${editAdminForm.value.id}`, payload)
  ElMessage.success('已更新'); showEditAdmin.value = false
  const res = await api.get('/admins'); admins.value = res.data
}

async function saveConfig() {
  for (const [key, value] of Object.entries(config.value)) { await api.put(`/config/${key}`, { value: String(value) }) }
  ElMessage.success('已保存')
}

function backupData() {
  const token = localStorage.getItem('admin_token')
  window.open(`/api/scores/backup-all?token=${encodeURIComponent(token)}`)
}

async function restoreData(e) {
  const file = e.target.files[0]
  if (!file) return
  try {
    await ElMessageBox.confirm('导入备份将覆盖当前所有数据，此操作不可恢复！确定继续？', '危险操作', { type: 'error', confirmButtonText: '确定导入' })
  } catch { return }
  const form = new FormData()
  form.append('file', file)
  try {
    const res = await api.post('/scores/restore-all', form)
    ElMessage.success(`已恢复：${res.data.classes}个班级, ${res.data.events}个项目, ${res.data.students}名学生, ${res.data.scores}条成绩, ${res.data.admins}个管理员, ${res.data.configs}项设置`)
    setTimeout(() => location.reload(), 1500)
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '恢复失败')
  }
}

// School management
const showAddSchool = ref(false)
const showEditSchool = ref(false)
const newSchoolName = ref('')
const editSchoolName = ref('')
const editingSchoolId = ref(null)

async function addSchool() {
  if (!newSchoolName.value.trim()) return
  await api.post('/schools', { name: newSchoolName.value.trim() })
  ElMessage.success('学校已创建（含默认项目+班级）')
  showAddSchool.value = false; newSchoolName.value = ''
  const res = await api.get('/schools'); allSchools.value = res.data
}

function editSchool(s) {
  editingSchoolId.value = s.id; editSchoolName.value = s.name; showEditSchool.value = true
}

async function saveEditSchool() {
  await api.put(`/schools/${editingSchoolId.value}`, { name: editSchoolName.value.trim() })
  ElMessage.success('已更新'); showEditSchool.value = false
  const res = await api.get('/schools'); allSchools.value = res.data
}

async function deleteSchool(s) {
  try {
    await ElMessageBox.confirm(`确定删除「${s.name}」吗？将级联删除该校所有数据！`, '危险操作', { type: 'error', confirmButtonText: '下一步' })
  } catch { return }
  try {
    const { value: password } = await ElMessageBox.prompt('请输入超级管理员密码确认', '身份验证', { inputType: 'password', confirmButtonText: '确认删除' })
    if (!password) return
    await api.delete(`/schools/${s.id}`, { params: { password } })
    ElMessage.success('已删除')
    const res = await api.get('/schools'); allSchools.value = res.data
  } catch (err) {
    if (err === 'cancel' || err === 'close') return
    ElMessage.error(err.response?.data?.detail || '删除失败')
  }
}

async function clearScores() {
  try {
    await ElMessageBox.confirm('确定清空所有成绩数据吗？此操作不可恢复！', '危险操作', { type: 'error', confirmButtonText: '下一步' })
  } catch { return }
  try {
    const { value: password } = await ElMessageBox.prompt('请输入超级管理员密码以确认操作', '身份验证', { inputType: 'password', confirmButtonText: '确认清空' })
    if (!password) return
    await api.post('/scores/clear-all', { password })
    ElMessage.success('已清空所有成绩')
  } catch (err) {
    if (err === 'cancel' || err === 'close') return
    ElMessage.error(err.response?.data?.detail || '操作失败')
  }
}
</script>

<style scoped>
/* ===== PAGE CONTAINER ===== */
.settings-page {
  margin: -12px; padding: 20px 24px 40px;
  min-height: calc(100vh - 50px);
  background: radial-gradient(circle at top, #112b72, #07142f 50%, #020817 100%);
  font-family: "PingFang SC", "Microsoft YaHei", sans-serif;
  max-width: 800px; margin-left: auto; margin-right: auto;
}

/* ===== BACK BUTTON ===== */
.back-btn {
  background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.12);
  color: #fff; padding: 10px 22px; border-radius: 14px;
  cursor: pointer; font-size: 14px; margin-bottom: 16px;
  transition: all 0.2s; font-family: inherit;
}
.back-btn:hover { background: rgba(255,255,255,0.14); }

h1 { color: #fff; font-size: 28px; margin: 0 0 20px; font-weight: 700; }
h4 { color: #e0e8f8; }

/* ===== GLASS CARD ===== */
.glass-card {
  background: rgba(12,26,61,0.65); backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid rgba(90,120,255,0.15); border-radius: 24px;
  padding: 24px; box-shadow: 0 0 40px rgba(80,120,255,0.08);
}

/* ===== TABS ===== */
.settings-page :deep(.el-tabs__header) { border-bottom-color: rgba(255,255,255,0.06); margin-bottom: 16px; }
.settings-page :deep(.el-tabs__item) { color: #7d8fb9; font-size: 14px; }
.settings-page :deep(.el-tabs__item.is-active) { color: #a0b8ff; }
.settings-page :deep(.el-tabs__active-bar) { background: #5865ff; }
.settings-page :deep(.el-tabs__content) { padding: 0; }

/* ===== ITEM CARDS ===== */
.item-card {
  display: flex; justify-content: space-between; align-items: center;
  padding: 14px 16px; margin-bottom: 6px;
  background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06);
  border-radius: 12px; transition: all 0.2s;
}
.item-card:hover { background: rgba(255,255,255,0.06); border-color: rgba(255,255,255,0.1); }
.item-info { flex: 1; min-width: 0; }
.item-name { font-size: 14px; font-weight: 600; color: #e0e8f8; }
.item-meta { font-size: 11px; color: #7d8fb9; margin-top: 2px; }
.item-actions { display: flex; gap: 6px; flex-shrink: 0; }

/* ===== BUTTONS ===== */
.action-btn {
  padding: 8px 14px; border-radius: 10px; font-size: 12.5px; font-weight: 500;
  border: 1px solid rgba(255,255,255,0.12); background: rgba(255,255,255,0.05);
  color: #c0d0f0; cursor: pointer; transition: all 0.2s; font-family: inherit;
  white-space: nowrap;
}
.action-btn:hover { background: rgba(255,255,255,0.12); border-color: rgba(255,255,255,0.2); }
.action-btn.primary { background: rgba(88,101,255,0.2); border-color: rgba(88,101,255,0.35); color: #a0b8ff; }
.action-btn.primary:hover { background: rgba(88,101,255,0.3); }
.action-btn.danger { color: #fca5a5; }
.action-btn.danger:hover { background: rgba(239,68,68,0.15); border-color: rgba(239,68,68,0.3); }
.action-btn.small { padding: 5px 10px; font-size: 11px; border-radius: 8px; }
.action-btn:disabled { opacity: 0.3; cursor: not-allowed; }

/* ===== CONFIG SECTION ===== */
.config-section { max-width: 500px; }

/* ===== Element Plus overrides ===== */
.settings-page :deep(.el-input__inner) { background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.12); color: #fff; border-radius: 10px; }
.settings-page :deep(.el-input__inner:focus) { border-color: rgba(100,120,255,0.4); }
.settings-page :deep(.el-select .el-input__inner) { background: rgba(255,255,255,0.04); border-color: rgba(255,255,255,0.12); color: #fff; }
.settings-page :deep(.el-input-number .el-input__inner) { background: rgba(255,255,255,0.04); border-color: rgba(255,255,255,0.12); color: #fff; }
.settings-page :deep(.el-select-dropdown) { background: #0f1e3d; border: 1px solid rgba(100,120,255,0.25); }
.settings-page :deep(.el-select-dropdown__item) { color: #c0d0f0; }
.settings-page :deep(.el-select-dropdown__item.hover) { background: rgba(100,120,255,0.15); }
.settings-page :deep(.el-select-dropdown__item.selected) { color: #a0b8ff; }
.settings-page :deep(.el-button--default) { background: transparent; border-color: rgba(255,255,255,0.12); color: #c0d0f0; }
.settings-page :deep(.el-dialog) { background: rgba(12,26,61,0.95); backdrop-filter: blur(20px); border: 1px solid rgba(100,120,255,0.2); border-radius: 20px; }
.settings-page :deep(.el-dialog__title) { color: #fff; }
.settings-page :deep(.el-dialog__body) { color: #c0d0f0; }
.settings-page :deep(.el-form-item__label) { color: #8ea0c8; }
.settings-page :deep(.el-divider) { border-color: rgba(255,255,255,0.06); }

@media (max-width: 767px) {
  .settings-page { padding: 12px; }
  .glass-card { padding: 16px; }
  h1 { font-size: 22px; }
}
</style>
