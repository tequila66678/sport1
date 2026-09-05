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
        <div class="stat-item">
          <span class="stat-num">{{ faceEnrolled }}</span>
          <span class="stat-label">已录人脸</span>
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
        <button class="action-btn" @click="faceDirInput.click()">📷 录人脸(批量)</button>
        <button class="action-btn danger" @click="batchDelete" :disabled="!selectedIds.length">🗑 删除({{ selectedIds.length }})</button>
      </div>
      <input ref="faceDirInput" type="file" webkitdirectory directory style="display:none" @change="onPickFaceDir" />
    </div>

    <!-- Desktop table in glass card -->
    <div class="glass-card desktop-only">
      <el-table :data="students" border stripe size="small" @selection-change="onSelectionChange">
        <el-table-column type="selection" width="40" />
        <el-table-column prop="name" label="姓名" width="80" />
        <el-table-column label="性别" width="50">
          <template #default="{ row }">{{ row.gender === 'M' ? '男' : '女' }}</template>
        </el-table-column>
        <el-table-column label="人脸" width="76">
          <template #default="{ row }">
            <span class="face-chip" :class="hasFace(row.id) ? 'on' : ''">{{ hasFace(row.id) ? '✓ 已录' : '未录' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="班级">
          <template #default="{ row }">{{ row.class_grade }}{{ row.class_name }}</template>
        </el-table-column>
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button text type="warning" size="small" @click="startFaceCapture(row)">📷 录脸</el-button>
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
          <div class="sc-name">{{ s.name }} <span class="sc-gender">{{ s.gender === 'M' ? '男' : '女' }}</span>
            <span class="face-chip" :class="hasFace(s.id) ? 'on' : ''">{{ hasFace(s.id) ? '✓已录' : '未录' }}</span>
          </div>
          <div class="sc-id">{{ s.student_id }}</div>
          <div class="sc-class">{{ s.class_grade }}{{ s.class_name }}</div>
        </div>
        <div class="sc-actions">
          <el-button text type="warning" size="small" @click="startFaceCapture(s)">📷录脸</el-button>
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

    <!-- 逐人录脸弹窗 -->
    <el-dialog v-model="showFaceCap" title="📷 人脸录入" :width="isMobile ? '100%' : '460px'" @opened="openFaceCam" @closed="closeFaceCam">
      <div v-if="faceTarget" class="face-cap-info">
        正在给 <b>{{ faceTarget.name }}</b>（{{ faceTarget.class_name }} {{ faceTarget.student_id }}）录人脸
        <div class="face-cap-tip">请让学生正对镜头，光线充足</div>
      </div>
      <video ref="camEl" autoplay playsinline muted></video>
      <div class="face-cap-live" :class="capReady ? 'ok' : 'err'">
        <span v-if="capReady">✅ 人脸清晰，大小合适，可以保存</span>
        <span v-else-if="capRatio > 0">👆 人脸太小（{{ Math.round(capRatio * 100) }}%），请靠近镜头</span>
        <span v-else>📷 正对镜头等待识别…</span>
      </div>
      <div class="face-cap-btns">
        <button class="action-btn primary" :disabled="capSaving || !capReady" @click="captureAndSave">📸 确认保存</button>
        <button class="action-btn" @click="showFaceCap = false">取消</button>
      </div>
      <p v-if="capMsg" class="face-cap-msg" :class="capMsgOk ? 'ok' : 'err'">{{ capMsg }}</p>
    </el-dialog>

    <!-- 批量导入人脸照片 -->
    <el-dialog v-model="showFaceBatch" title="📷 批量导入人脸照片" :width="isMobile ? '100%' : '560px'" :close-on-click-modal="false">
      <div class="face-batch-tip">
        ① 照片文件名 <b>必须是 学号 或 姓名 + 图片后缀</b>，支持 <code>jpg</code> <code>jpeg</code> <code>png</code> <code>webp</code> <code>gif</code> <code>bmp</code> <code>avif</code>（例：<code>270101.jpg</code> 或 <code>张三.png</code>）。系统优先按学号、其次按姓名精确匹配；姓名有重名时请改用学号命名<br>
        ② 照片在浏览器本地处理，<b>原图不会上传</b>，只提取人脸特征保存
      </div>
      <div v-if="!faceBatchFiles.length" style="text-align:center;padding:12px">
        <button class="action-btn primary" @click="faceDirInput.click()">选择照片文件夹</button>
      </div>
      <template v-else>
        <p class="face-batch-picked">已选 <b>{{ faceBatchFiles.length }}</b> 张照片<template v-if="faceWriting">，正在识别 {{ faceBatchDone }}/{{ faceBatchFiles.length }}…</template></p>
        <div class="face-batch-actions">
          <button class="action-btn primary" :disabled="faceWriting" @click="runFaceBatch">开始导入</button>
          <button class="action-btn" :disabled="faceWriting" @click="faceBatchFiles = []; faceBatchLog = []">重新选择</button>
        </div>
        <div class="face-log">
          <div v-for="(m, i) in faceBatchLog" :key="i" :class="m.ok ? 'ok' : 'err'">{{ m.text }}</div>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../../api'
import { loadFaceapi, ensureModels, detectOne } from '../../faceutil'

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

// ===== 人脸录入 =====
const allStudents = ref([])                 // 全校名单（来自 /device/sync，含学号）
const faceIds = ref(new Set())              // 已录人脸的内部 id 集合
const showFaceCap = ref(false)
const faceTarget = ref(null)                // 正在录脸的那个学生
const camEl = ref(null)
const capMsg = ref(''); const capMsgOk = ref(false); const capSaving = ref(false)
const faceDirInput = ref(null)
const showFaceBatch = ref(false)
const faceBatchFiles = ref([])
const faceWriting = ref(false)
const faceBatchDone = ref(0)
const faceBatchLog = ref([])
let faceapi = null, camStream = null
let camCheckTimer = null
const capRatio = ref(0)      // 当前镜头里人脸宽度占画面比例(0~1)，用于判断够不够大
const capReady = ref(false)  // 人脸足够大/清晰，才允许保存
let bestFrame = null         // 录脸期间“质量最好”的那帧检测结果，点保存时用它而非手点那瞬
let capTimer = 0             // 防抖：短暂无人脸不立刻清空 bestFrame

const faceEnrolled = computed(() => faceIds.value.size)
const hasFace = id => faceIds.value.has(id)

async function readyFace() {
  if (!faceapi) {
    faceapi = await loadFaceapi()
    await ensureModels()
  }
  return faceapi
}

async function loadSchoolFace() {
  try {
    const res = await api.get('/device/sync')
    allStudents.value = res.data.students || []
    faceIds.value = new Set((res.data.face_embeddings || []).map(f => f.id))
  } catch (e) { /* 非学校管理员时静默 */ }
}

async function startFaceCapture(row) {
  faceTarget.value = row
  capMsg.value = ''; capMsgOk.value = false; capSaving.value = false
  capRatio.value = 0; capReady.value = false; bestFrame = null
  showFaceCap.value = true
}

async function openFaceCam() {
  try {
    await readyFace()
  } catch (e) { capMsg.value = '人脸识别组件加载失败'; capMsgOk.value = false; return }
  try {
    camStream = await navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480 }, audio: false })
    const v = camEl.value
    if (v) { v.srcObject = camStream; await v.play() }
  } catch (e) {
    capMsg.value = '无法打开摄像头，请检查浏览器权限：' + ((e && e.message) || e)
    capMsgOk.value = false
    return
  }
  // 边录边检测：持续找“人脸够大”的最优帧，达到尺寸门槛才允许保存
  capTimer = 0
  const NO_VIDEO_MSG = '摄像头没有出画面，请点“取消”重新打开'
  let noVideo = 0  // 摄像头迟迟不出画面的连续轮数，超过则给出可见提示（别静默卡住）
  const tick = async () => {
    try {
      const vv = camEl.value
      if (!showFaceCap.value || !vv) return              // 弹窗已关 → 真正停止
      if (!vv.videoWidth || !vv.videoHeight) {           // 视频还没出画面：本轮跳过，等下一轮
        noVideo++
        if (noVideo > 25 && !capMsg.value) capMsg.value = NO_VIDEO_MSG  // ~5s 仍无画面 → 提示
        return
      }
      if (capMsg.value === NO_VIDEO_MSG) capMsg.value = ''  // 画面出来了，清掉看门狗提示
      noVideo = 0
      const c = document.createElement('canvas')
      c.width = vv.videoWidth; c.height = vv.videoHeight
      c.getContext('2d').drawImage(vv, 0, 0)
      let res = null
      try { res = await detectOne(faceapi, c) } catch (e) {}
      if (!showFaceCap.value) return                     // 关窗竞态：已清资源就不要再写状态
      if (res) {
        capTimer = 0
        const ratio = res.box.width / c.width
        capRatio.value = Math.min(1, ratio)
        if (ratio >= 0.25) {
          // 达标帧：更新“最优帧”（选人脸更大的），保存用这一帧而非手点那瞬
          capReady.value = true
          if (!bestFrame || res.box.width > bestFrame.box.width) {
            bestFrame = { descriptor: res.descriptor, box: res.box }
          }
        } else {
          // 人脸变小但仍在：保留已达标状态直到离开(用无脸计数重置)，提示靠近
          if (!bestFrame) capReady.value = false
        }
      } else {
        capRatio.value = 0
        capTimer++
        if (capTimer > 3) { capReady.value = false; bestFrame = null }  // 连续无脸约0.6s后重置
      }
    } finally {
      // 关键修复：无论视频是否就绪、检测是否耗时，只要弹窗还开着就每 200ms 续跑。
      // 原 bug：videoWidth 为 0 时提前 return，末尾的 setTimeout 永不执行 → 检测循环静默死亡。
      if (showFaceCap.value) camCheckTimer = setTimeout(tick, 200)
    }
  }
  tick()
}

async function captureAndSave() {
  if (!capReady.value || !bestFrame) {
    capMsg.value = '人脸还不够大/不清晰，请靠近镜头'; capMsgOk.value = false
    return
  }
  capSaving.value = true
  try {
    await api.put(`/faces/${faceTarget.value.id}`, { embedding: Array.from(bestFrame.descriptor) })
    faceIds.value = new Set([...faceIds.value, faceTarget.value.id])
    capMsg.value = '✓ 已录入'; capMsgOk.value = true
    ElMessage.success(`${faceTarget.value.name} 人脸已保存`)
    showFaceCap.value = false
  } catch (e) {
    capMsg.value = '保存失败：' + ((e.response && e.response.data && e.response.data.detail) || e.message)
    capMsgOk.value = false
  } finally {
    capSaving.value = false
  }
}

function closeFaceCam() {
  if (camCheckTimer) clearTimeout(camCheckTimer)
  camCheckTimer = null
  if (camStream) { camStream.getTracks().forEach(t => t.stop()); camStream = null }
  capRatio.value = 0; capReady.value = false; bestFrame = null; capTimer = 0
  capMsg.value = ''
}

// 批量录脸支持多种常用图片格式（后缀匹配；HEIC 浏览器解不了，需先转 jpg/png）
const FACE_IMG_RE = /\.(jpe?g|png|webp|gif|bmp|avif)$/i
function onPickFaceDir(e) {
  const files = Array.from(e.target.files || [])
  e.target.value = ''
  const imgs = files.filter(f => FACE_IMG_RE.test(f.name))
  if (!imgs.length) { ElMessage.warning('文件夹里没找到照片（支持 jpg/jpeg/png/webp/gif/bmp/avif）'); return }
  // 归一成 { name, file }：按文件名找学生 + 用 file 解码。File 对象本身没有 .file 属性，
  // 直接存裸 File 会让 runFaceBatch 里 p.file 取到 undefined → 批量永远读不出图。
  faceBatchFiles.value = imgs.map(f => ({ name: f.name, file: f }))
  faceBatchLog.value = []; faceBatchDone.value = 0
  showFaceBatch.value = true
}

function readImageAsCanvas(file) {
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(file)
    const img = new Image()
    img.onload = () => {
      const maxSide = 640
      const scale = Math.min(1, maxSide / Math.max(img.width, img.height))
      const c = document.createElement('canvas')
      c.width = Math.round(img.width * scale); c.height = Math.round(img.height * scale)
      c.getContext('2d').drawImage(img, 0, 0, c.width, c.height)
      URL.revokeObjectURL(url)
      resolve(c)
    }
    img.onerror = () => { URL.revokeObjectURL(url); reject(new Error('图片读取失败')) }
    img.src = url
  })
}

async function runFaceBatch() {
  const list = faceBatchFiles.value
  if (!list.length || faceWriting.value) return
  try { await readyFace() } catch (e) { ElMessage.error('人脸识别组件加载失败'); return }
  faceWriting.value = true; faceBatchDone.value = 0; faceBatchLog.value = []
  const results = []
  for (const p of list) {
    const key = p.name.replace(/\.[^.]+$/, '').trim()
    // 优先按学号精确匹配；学号找不到再按姓名精确匹配（姓名重名则跳过，请改用学号）
    let st = allStudents.value.find(s => s.student_id === key)
    if (!st) {
      const byName = allStudents.value.filter(s => s.name === key)
      if (byName.length === 1) st = byName[0]
      else if (byName.length > 1) { faceBatchLog.value.push({ ok: false, text: `${p.name}：姓名「${key}」有 ${byName.length} 人重名，请把文件名改成学号` }); faceBatchDone.value++; continue }
    }
    if (!st) { faceBatchLog.value.push({ ok: false, text: `${p.name}：未找到学号或姓名为「${key}」的学生` }); faceBatchDone.value++; continue }
    try {
      const canvas = await readImageAsCanvas(p.file)
      const res = await detectOne(faceapi, canvas)
      if (!res) { faceBatchLog.value.push({ ok: false, text: `${p.name}：照片里未检测到人脸` }); faceBatchDone.value++; continue }
      // 质量门槛：人脸至少要占画面约 15%（太小的脸提不出可用特征，容易认错）
      const ratio = res.box.width / canvas.width
      if (ratio < 0.15) { faceBatchLog.value.push({ ok: false, text: `${p.name}：人脸在照片中太小（占画面 ${Math.round(ratio * 100)}%），请用清晰正面照` }); faceBatchDone.value++; continue }
      results.push({ student_id: st.id, embedding: Array.from(res.descriptor) })
    } catch (err) {
      faceBatchLog.value.push({ ok: false, text: `${p.name}：${err.message}` })
    }
    faceBatchDone.value++
  }
  if (results.length) {
    try {
      const r = await api.post('/faces/batch', { faces: results })
      r.data.forEach(item => {
        const st = allStudents.value.find(s => s.id === item.student_id)
        faceBatchLog.value.push({ ok: item.ok, text: `${st ? st.name : item.student_id} ${item.ok ? '✓ 已录入' : '✗ ' + (item.reason || '失败')}` })
      })
      await loadSchoolFace()
    } catch (e) {
      faceBatchLog.value.push({ ok: false, text: '写入请求失败：' + ((e && e.message) || e) })
    }
  }
  faceWriting.value = false
}

onMounted(async () => {
  const res = await api.get('/events/classes')
  classes.value = res.data
  loadStudents()
  loadSchoolFace()
})

onUnmounted(closeFaceCam)

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
.students-page :deep(.el-input__wrapper) {
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.12);
  border-radius: 10px;
  box-shadow: none;
}
.students-page :deep(.el-input__wrapper:hover) { border-color: rgba(255,255,255,0.2); }
.students-page :deep(.el-input.is-focus .el-input__wrapper) {
  border-color: rgba(100,120,255,0.4);
  box-shadow: 0 0 0 1px rgba(100,120,255,0.15);
}
.students-page :deep(.el-input__inner) { color: #fff; }
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

/* Face chip */
.face-chip {
  display: inline-block; font-size: 11px; padding: 1px 7px; border-radius: 20px;
  background: rgba(148,163,184,0.15); color: #94a3b8; margin-left: 4px; vertical-align: 1px;
}
.face-chip.on { background: rgba(74,222,128,0.16); color: #4ade80; }

/* Face capture dialog */
.face-cap-info { color: #e0e8f8; margin-bottom: 4px; font-size: 14px; }
.face-cap-info b { color: #fff; }
.face-cap-tip { color: #7d8fb9; font-size: 12px; margin-top: 2px; }
video { width: 100%; max-width: 460px; border-radius: 12px; background: #000; margin: 8px auto 0; display: block; }
.face-cap-live {
  text-align: center; font-size: 13px; font-weight: 600;
  margin: 8px 0 0; min-height: 18px;
}
.face-cap-live.ok { color: #4ade80; }
.face-cap-live.err { color: #fbbf24; }
.face-cap-btns { text-align: center; margin: 10px 0 4px; }
.face-cap-btns .primary:disabled { opacity: .4; cursor: not-allowed; }
.face-cap-msg { text-align: center; font-size: 14px; margin: 6px 0 0; }
.face-cap-msg.ok { color: #4ade80; } .face-cap-msg.err { color: #f87171; }

/* Batch import */
.face-batch-tip {
  color: #cbd5f0; font-size: 13px; background: rgba(255,255,255,0.05);
  border: 1px solid rgba(255,255,255,0.1); padding: 10px 12px; border-radius: 10px; margin-bottom: 8px;
}
.face-batch-tip code { color: #a0b8ff; }
.face-batch-picked { color: #e0e8f8; margin: 8px 0 0; }
.face-batch-actions { margin: 8px 0; display: flex; gap: 8px; }
.face-log { max-height: 240px; overflow-y: auto; font-size: 13px; line-height: 1.7; border-top: 1px solid rgba(255,255,255,0.07); padding-top: 8px; }
.face-log .ok { color: #4ade80; } .face-log .err { color: #f87171; }

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
