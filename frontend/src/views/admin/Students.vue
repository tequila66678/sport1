<template>
  <div class="students-page">
    <button class="back-btn" @click="$router.push('/admin/dashboard')">← 返回仪表盘</button>

    <!-- Hero + Stats -->
    <div class="hero-row">
      <div class="hero-info">
        <h1>👥 学生管理</h1>
        <p>管理全校学生信息 · 批量导入导出</p>
      </div>
      <div class="stats-mini">
        <div class="stat-item">
          <span class="stat-num">{{ total }}</span>
          <span class="stat-label">学生总数</span>
        </div>
        <div class="stat-item">
          <span class="stat-num">{{ classes.length }}</span>
          <span class="stat-label">班级数</span>
        </div>
      </div>
    </div>

    <!-- Toolbar in glass strip -->
    <div class="toolbar-glass">
      <el-input v-model="search" placeholder="搜索学号/姓名" clearable @change="loadStudents" class="tb-search" size="large">
        <template #prefix><span style="color:#7d8fb9">🔍</span></template>
      </el-input>
      <el-select v-model="filterClassId" placeholder="全部班级" clearable @change="loadStudents" class="tb-class" size="large">
        <el-option v-for="c in classes" :key="c.id" :label="c.label" :value="c.id" />
      </el-select>
      <div class="tb-actions">
        <button class="action-btn primary" @click="showAdd = true">＋ 新增</button>
        <button class="action-btn" @click="downloadTemplate">📥 模板</button>
        <button class="action-btn" @click="showImport = true">📊 导入</button>
        <button class="action-btn" @click="showBatchEdit = true">✎ 批量</button>
        <button class="action-btn danger" @click="batchDelete" :disabled="!selectedIds.length">🗑 删除({{ selectedIds.length }})</button>
      </div>
    </div>

    <!-- Desktop table in glass card -->
    <div class="glass-card desktop-only">
      <el-table :data="students" border stripe size="small" @selection-change="onSelectionChange">
        <el-table-column type="selection" width="40" />
        <el-table-column prop="name" label="姓名" width="80" />
        <el-table-column label="性别" width="50">
          <template #default="{ row }">{{ row.gender === 'M' ? '男' : '女' }}</template>
        </el-table-column>
        <el-table-column label="班级">
          <template #default="{ row }">{{ row.class_grade }}{{ row.class_name }}</template>
        </el-table-column>
        <el-table-column label="操作" width="130">
          <template #default="{ row }">
            <el-button text type="primary" size="small" @click="editStudent(row)">编辑</el-button>
            <el-button text type="danger" size="small" @click="deleteStudent(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="glass-card-footer">
        <el-pagination
          v-model:current-page="page" :page-size="50" :total="total"
          layout="prev, pager, next" small
          @current-change="loadStudents"
        />
      </div>
    </div>

    <!-- Mobile card list -->
    <div class="mobile-only">
      <div v-for="s in students" :key="s.id" class="student-card">
        <el-checkbox :model-value="selectedIds.includes(s.id)" @change="toggleSelect(s.id)" style="margin-right:8px" />
        <div class="sc-info">
          <div class="sc-name">{{ s.name }} <span class="sc-gender">{{ s.gender === 'M' ? '男' : '女' }}</span></div>
          <div class="sc-id">{{ s.student_id }}</div>
          <div class="sc-class">{{ s.class_grade }}{{ s.class_name }}</div>
        </div>
        <div class="sc-actions">
          <el-button text type="primary" size="small" @click="editStudent(s)">编辑</el-button>
          <el-button text type="danger" size="small" @click="deleteStudent(s)">删除</el-button>
        </div>
      </div>
      <el-pagination
        v-model:current-page="page" :page-size="50" :total="total"
        layout="prev, pager, next" small
        @current-change="loadStudents"
        style="margin-top:12px;justify-content:center"
      />
    </div>

    <!-- Dialogs unchanged -->
    <el-dialog v-model="showImport" title="批量导入" width="90%" :fullscreen="isMobile" @close="importResult=null; importing=false">
      <div v-if="importing" style="text-align:center;padding:20px">
        <el-progress :percentage="importProgress" :stroke-width="20" :text-inside="true" />
        <p style="margin-top:8px">正在导入...</p>
      </div>
      <el-upload v-else :http-request="handleImport" accept=".xlsx" :show-file-list="false" drag>
        <div>拖拽Excel文件或点击上传</div>
      </el-upload>
      <div v-if="importResult" style="margin-top:12px">
        <p>导入: {{ importResult.imported }} 人</p>
        <p v-for="e in importResult.errors" :key="e" style="color:red;font-size:11px">{{ e }}</p>
      </div>
    </el-dialog>

    <el-dialog v-model="showBatchEdit" title="批量修改" width="90%">
      <el-form label-width="70px">
        <el-form-item label="原班级">
          <el-select v-model="batchFromClass" placeholder="留空=全部" clearable style="width:100%">
            <el-option v-for="c in classes" :key="c.id" :label="c.label" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="新班级">
          <el-select v-model="batchToClass" placeholder="选择目标" style="width:100%">
            <el-option v-for="c in classes" :key="c.id" :label="c.label" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-checkbox v-model="batchResetPwd">重置密码（学号后6位）</el-checkbox>
        </el-form-item>
        <el-button type="primary" @click="doBatchUpdate" style="width:100%">确认修改</el-button>
      </el-form>
    </el-dialog>

    <el-dialog v-model="showEdit" title="编辑学生" width="90%">
      <el-form label-width="60px" v-if="editForm">
        <el-form-item label="学号"><el-input v-model="editForm.student_id" /></el-form-item>
        <el-form-item label="姓名"><el-input v-model="editForm.name" /></el-form-item>
        <el-form-item label="性别">
          <el-select v-model="editForm.gender" style="width:100%">
            <el-option label="男" value="M" /><el-option label="女" value="F" />
          </el-select>
        </el-form-item>
        <el-form-item label="班级">
          <el-select v-model="editForm.class_id" style="width:100%">
            <el-option v-for="c in classes" :key="c.id" :label="c.label" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-button type="primary" @click="saveEdit" style="width:100%">保存</el-button>
      </el-form>
    </el-dialog>

    <el-dialog v-model="showAdd" title="新增学生" width="90%">
      <el-form label-width="60px">
        <el-form-item label="学号"><el-input v-model="newStudent.student_id" maxlength="6" /></el-form-item>
        <el-form-item label="姓名"><el-input v-model="newStudent.name" /></el-form-item>
        <el-form-item label="性别">
          <el-select v-model="newStudent.gender" style="width:100%">
            <el-option label="男" value="M" /><el-option label="女" value="F" />
          </el-select>
        </el-form-item>
        <el-form-item label="班级">
          <el-select v-model="newStudent.class_id" style="width:100%">
            <el-option v-for="c in classes" :key="c.id" :label="c.label" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-button type="primary" @click="addStudent" style="width:100%">确认新增</el-button>
      </el-form>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../../api'

const students = ref([])
const classes = ref([])
const search = ref('')
const filterClassId = ref(null)
const page = ref(1)
const total = ref(0)

const showImport = ref(false)
const importing = ref(false)
const importProgress = ref(0)
const importResult = ref(null)
const batchFromClass = ref(null)
const batchToClass = ref(null)
const batchResetPwd = ref(false)
const showEdit = ref(false)
const editForm = ref(null)
const showAdd = ref(false)
const newStudent = ref({ student_id: '', name: '', gender: 'M', class_id: null })
const isMobile = ref(window.innerWidth < 768)

onMounted(async () => {
  const res = await api.get('/events/classes')
  classes.value = res.data
  loadStudents()
})

async function loadStudents() {
  const params = { page: page.value, page_size: 50 }
  if (search.value) params.search = search.value
  if (filterClassId.value) params.class_id = filterClassId.value
  try { const res = await api.get('/students', { params }); students.value = res.data; total.value = res.data.length >= 50 ? (page.value * 50 + 1) : ((page.value - 1) * 50 + res.data.length) } catch {}
  // Try to get total count from headers or make a count request
  try {
    const countRes = await api.get('/students', { params: { page: 1, page_size: 1, ...(search.value ? {search: search.value} : {}), ...(filterClassId.value ? {class_id: filterClassId.value} : {}) } })
    // Cannot get total easily — use pagination-based estimate
  } catch {}
}

function downloadTemplate() { window.open('/api/students/template/download') }

async function handleImport({ file }) {
  importing.value = true; importProgress.value = 0
  const timer = setInterval(() => { if (importProgress.value < 90) importProgress.value += 10 }, 300)
  try {
    const form = new FormData(); form.append('file', file)
    const res = await api.post('/students/batch-import', form)
    importProgress.value = 100
    importResult.value = res.data; loadStudents()
  } finally { clearInterval(timer); importing.value = false }
}

async function doBatchUpdate() {
  await api.put('/students/batch/update', { class_id: batchFromClass.value, new_class_id: batchToClass.value || undefined, reset_password: batchResetPwd.value })
  ElMessage.success('批量修改成功'); showBatchEdit.value = false; loadStudents()
}

function editStudent(row) {
  editForm.value = { id: row.id, student_id: row.student_id, name: row.name, gender: row.gender, class_id: row.class_id }
  showEdit.value = true
}

async function saveEdit() {
  await api.put(`/students/${editForm.value.id}`, { student_id: editForm.value.student_id, name: editForm.value.name, gender: editForm.value.gender, class_id: editForm.value.class_id })
  ElMessage.success('修改成功'); showEdit.value = false; loadStudents()
}

async function addStudent() {
  if (!newStudent.value.class_id) { ElMessage.warning('请选择班级'); return }
  try {
    await api.post('/students', newStudent.value)
    ElMessage.success('已新增')
    showAdd.value = false
    newStudent.value = { student_id: '', name: '', gender: 'M', class_id: null }
    loadStudents()
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '添加失败')
  }
}

const selectedIds = ref([])

function onSelectionChange(rows) { selectedIds.value = rows.map(r => r.id) }
function toggleSelect(id) {
  const idx = selectedIds.value.indexOf(id)
  if (idx >= 0) selectedIds.value.splice(idx, 1)
  else selectedIds.value.push(id)
}

async function batchDelete() {
  if (!selectedIds.value.length) return
  await ElMessageBox.confirm(`确定删除选中的 ${selectedIds.value.length} 名学生？`, '批量删除', { type: 'error' })
  await api.delete('/students/batch-delete', { data: selectedIds.value })
  ElMessage.success('删除成功'); selectedIds.value = []; loadStudents()
}

async function deleteStudent(row) {
  await ElMessageBox.confirm(`确定删除 ${row.name} (${row.student_id})？`, '确认删除', { type: 'warning' })
  await api.delete(`/students/${row.id}`); ElMessage.success('删除成功'); loadStudents()
}
</script>

<style scoped>
/* ===== PAGE CONTAINER ===== */
.students-page {
  margin: -12px; padding: 20px 24px 40px;
  min-height: calc(100vh - 50px);
  background: radial-gradient(circle at top, #112b72, #07142f 50%, #020817 100%);
  font-family: "PingFang SC", "Microsoft YaHei", sans-serif;
  max-width: 1100px; margin-left: auto; margin-right: auto;
}

/* ===== BACK BUTTON ===== */
.back-btn {
  background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.12);
  color: #fff; padding: 10px 22px; border-radius: 14px;
  cursor: pointer; font-size: 14px; margin-bottom: 20px;
  transition: all 0.2s; font-family: inherit;
}
.back-btn:hover { background: rgba(255,255,255,0.14); }

/* ===== HERO + STATS ===== */
.hero-row { display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; flex-wrap: wrap; gap: 16px; }
.hero-info h1 { color: #fff; font-size: 32px; margin: 0 0 4px; font-weight: 700; }
.hero-info p { color: #8fa3d8; font-size: 14px; margin: 0; }
.stats-mini { display: flex; gap: 12px; }
.stat-item {
  background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.1);
  border-radius: 14px; padding: 14px 22px; text-align: center; min-width: 90px;
}
.stat-num { display: block; font-size: 26px; font-weight: 800; color: #a0b8ff; }
.stat-label { font-size: 11px; color: #7d8fb9; letter-spacing: 0.5px; }

/* ===== TOOLBAR GLASS ===== */
.toolbar-glass {
  display: flex; gap: 8px; margin-bottom: 16px; flex-wrap: wrap; align-items: center;
  background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08);
  border-radius: 16px; padding: 12px 14px;
  backdrop-filter: blur(10px);
}
.tb-search { flex: 1; min-width: 160px; }
.tb-class { width: 130px; flex-shrink: 0; }
.tb-actions { display: flex; gap: 6px; flex-wrap: wrap; }

.action-btn {
  padding: 8px 14px; border-radius: 10px; font-size: 12.5px; font-weight: 500;
  border: 1px solid rgba(255,255,255,0.15); background: rgba(255,255,255,0.05);
  color: #c0d0f0; cursor: pointer; transition: all 0.2s; font-family: inherit;
  white-space: nowrap;
}
.action-btn:hover:not(:disabled) { background: rgba(255,255,255,0.12); border-color: rgba(255,255,255,0.25); }
.action-btn:disabled { opacity: 0.3; cursor: not-allowed; }
.action-btn.primary { background: rgba(88,101,255,0.2); border-color: rgba(88,101,255,0.35); color: #a0b8ff; }
.action-btn.primary:hover:not(:disabled) { background: rgba(88,101,255,0.3); }
.action-btn.danger { color: #fca5a5; }
.action-btn.danger:hover:not(:disabled) { background: rgba(239,68,68,0.15); border-color: rgba(239,68,68,0.35); }

/* ===== GLASS CARD (table) ===== */
.glass-card {
  background: rgba(12,26,61,0.65); backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid rgba(90,120,255,0.15); border-radius: 24px;
  overflow: hidden; box-shadow: 0 0 40px rgba(80,120,255,0.08);
}
.glass-card-footer { padding: 12px 16px; display: flex; justify-content: center; border-top: 1px solid rgba(255,255,255,0.05); }

/* ===== Element Plus overrides ===== */
.students-page :deep(.el-input__inner) { background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.12); color: #fff; border-radius: 10px; }
.students-page :deep(.el-input__inner:focus) { border-color: rgba(100,120,255,0.4); }
.students-page :deep(.el-select .el-input__inner) { background: rgba(255,255,255,0.04); border-color: rgba(255,255,255,0.12); color: #fff; }
.students-page :deep(.el-select-dropdown) { background: #0f1e3d; border: 1px solid rgba(100,120,255,0.25); }
.students-page :deep(.el-select-dropdown__item) { color: #c0d0f0; }
.students-page :deep(.el-select-dropdown__item.hover) { background: rgba(100,120,255,0.15); }
.students-page :deep(.el-select-dropdown__item.selected) { color: #a0b8ff; }
.students-page :deep(.el-button--default) { background: transparent; border-color: rgba(255,255,255,0.15); color: #c0d0f0; }

/* Table */
.students-page :deep(.el-table) { background: transparent; --el-table-bg-color: transparent; --el-table-tr-bg-color: transparent; }
.students-page :deep(.el-table th.el-table__cell) { background: rgba(255,255,255,0.03); color: #8ea0c8; border-bottom-color: rgba(255,255,255,0.06); font-weight: 600; font-size: 12px; }
.students-page :deep(.el-table td.el-table__cell) { background: transparent; color: #e0e8f8; border-bottom-color: rgba(255,255,255,0.04); }
.students-page :deep(.el-table--striped .el-table__body tr.el-table__row--striped td.el-table__cell) { background: rgba(255,255,255,0.015); }
.students-page :deep(.el-table__body tr:hover td.el-table__cell) { background: rgba(88,101,255,0.06) !important; }
.students-page :deep(.el-table--border .el-table__cell) { border-right-color: rgba(255,255,255,0.05); }
.students-page :deep(.el-checkbox__inner) { background: rgba(255,255,255,0.06); border-color: rgba(255,255,255,0.2); }

/* Pagination */
.students-page :deep(.el-pagination button), .students-page :deep(.el-pager li) { color: #8ea0c8; background: transparent; }
.students-page :deep(.el-pager li.is-active) { background: rgba(88,101,255,0.25); color: #a0b8ff; border-radius: 8px; }

/* Dialog */
.students-page :deep(.el-dialog) { background: rgba(12,26,61,0.95); backdrop-filter: blur(20px); border: 1px solid rgba(100,120,255,0.2); border-radius: 20px; }
.students-page :deep(.el-dialog__title) { color: #fff; }
.students-page :deep(.el-dialog__body) { color: #c0d0f0; }
.students-page :deep(.el-form-item__label) { color: #8ea0c8; }
.students-page :deep(.el-upload-dragger) { background: rgba(255,255,255,0.03); border-color: rgba(255,255,255,0.12); }
.students-page :deep(.el-upload__text) { color: #8ea0c8; }
.students-page :deep(.el-progress-bar__outer) { background: rgba(255,255,255,0.06); }

/* Mobile cards */
.student-card {
  display: flex; justify-content: space-between; align-items: center;
  padding: 14px; background: rgba(12,26,61,0.65); backdrop-filter: blur(12px);
  border: 1px solid rgba(255,255,255,0.08); border-radius: 14px; margin-bottom: 8px;
}
.sc-name { font-size: 15px; font-weight: bold; color: #fff; }
.sc-gender { font-size: 12px; color: #8ea0c8; margin-left: 6px; }
.sc-id { font-size: 12px; color: #8ea0c8; }
.sc-class { font-size: 12px; color: #7d8fb9; }
.sc-actions { display: flex; gap: 4px; flex-shrink: 0; }

@media (min-width: 768px) { .mobile-only { display: none; } }
@media (max-width: 767px) {
  .desktop-only { display: none; }
  .students-page { padding: 12px; }
  .hero-info h1 { font-size: 24px; }
  .toolbar-glass { flex-direction: column; }
}
</style>
