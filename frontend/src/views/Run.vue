<template>
  <div class="run">
    <!-- 登录 -->
    <div v-if="!authed" class="center">
      <div class="card">
        <h2>🏃 长跑体测设备</h2>
        <p class="sub">请用学校管理员账号登录</p>
        <input v-model="user" placeholder="账号" autocomplete="username" />
        <input v-model="pass" type="password" placeholder="密码" autocomplete="current-password" @keyup.enter="login" />
        <button @click="login" :disabled="loggingIn">{{ loggingIn ? '登录中…' : '登录' }}</button>
        <p v-if="loginErr" class="err">{{ loginErr }}</p>
      </div>
    </div>

    <!-- 待开始 -->
    <div v-else-if="mode === 'ready'" class="center">
      <div class="card">
        <h2>🏃 {{ schoolName }}</h2>
        <p class="sub">长跑体测 · 已录入 {{ faces.length }} / {{ students.length }} 人</p>
        <select v-model="eventId" class="big-select">
          <option disabled value="">—— 选择本次项目 ——</option>
          <option v-for="e in events" :key="e.id" :value="e.id">{{ e.name }}（{{ genderLabel(e.gender) }}）</option>
        </select>
        <button class="big primary" :disabled="!eventId" @click="startBatch">▶ 开始批次</button>
        <button class="ghost" @click="refreshSync">刷新名单</button>
      </div>
    </div>

    <!-- 计时中 -->
    <div v-else-if="mode === 'running'" class="run-split">
      <div class="video-wrap">
        <video ref="video" autoplay playsinline muted></video>
        <canvas ref="overlay"></canvas>
        <div v-if="flashText" class="flash">{{ flashText }}</div>
      </div>
      <div class="side">
        <div class="timer">{{ timerText }}</div>
        <div class="status">{{ statusText }}</div>
        <button class="big danger" @click="endBatch">■ 结束批次</button>
        <div class="manual">
          <select v-model="manualSel" class="manual-select">
            <option value="">识别不到 → 手动选择学生</option>
            <option v-for="s in unrecordedStudents" :key="s.id" :value="s.id">
              {{ s.name }} {{ s.student_id }} {{ s.class_name }}
            </option>
          </select>
          <button @click="manualRecord">记下</button>
        </div>
        <div class="list">
          <div v-for="(r, i) in records" :key="i" class="rec">
            <span>{{ i + 1 }}. {{ r.name }}</span><b>{{ r.time }}</b>
          </div>
        </div>
      </div>
    </div>

    <!-- 结束核对 -->
    <div v-else class="center">
      <div class="card wide">
        <h2>本批结束 · 共 {{ records.length }} 人</h2>
        <table>
          <thead><tr><th>#</th><th>姓名</th><th>班级</th><th>成绩</th><th>状态</th></tr></thead>
          <tbody>
            <tr v-for="(r, i) in records" :key="i">
              <td>{{ i + 1 }}</td><td>{{ r.name }}</td><td>{{ r.class_name }}</td><td>{{ r.time }}</td>
              <td>
                <span v-if="uploadRes[r.id]" :class="uploadRes[r.id].ok ? 'ok' : 'err'">
                  {{ uploadRes[r.id].ok ? '✓ ' + (uploadRes[r.id].raw_value || '') + ' · ' + uploadRes[r.id].earned_score + '分' : '✗ ' + (uploadRes[r.id].reason || '失败') }}
                </span>
                <button class="mini danger" @click="removeRecord(i)" title="删除此行（删除后重新上传其余）">删</button>
              </td>
            </tr>
          </tbody>
        </table>
        <button class="big primary" @click="upload" :disabled="uploading">
          {{ uploading ? '上传中…' : records.length ? '上传成绩到 sport1' : '（本批已空）' }}
        </button>
        <p v-for="(m, i) in messages" :key="i" :class="m.ok ? 'ok' : 'err'">{{ m.text }}</p>
        <button class="ghost" @click="resetBatch">再来一批</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import api from '../api'
import { loadFaceapi, ensureModels, detectOne, bestMatch } from '../faceutil'

const THRESHOLD = 0.5
const SYNC_KEY = 'run_sync_cache_v1'
const BATCH_KEY = 'run_batch_v1'

const authed = ref(!!localStorage.getItem('admin_token'))
const user = ref(''); const pass = ref(''); const loggingIn = ref(false); const loginErr = ref('')
const schoolName = ref(''); const events = ref([]); const students = ref([]); const faces = ref([])
const eventId = ref(''); const schoolId = ref('')
const mode = ref('ready')           // ready | running | review
const video = ref(null); const overlay = ref(null)
const records = ref([])             // { id, name, class_name, time, timeMs }
const timerText = ref('00:00'); const statusText = ref(''); const flashText = ref('')
const manualSel = ref(''); const uploading = ref(false); const messages = ref([])
const uploadRes = ref({})           // sid -> {ok, raw_value?, earned_score?, reason?}
let running = false, startMs = 0, displayTimer = null, recTimer = null, faceapi = null, wakeLock = null
let recordedIds = new Set()

const studentsById = computed(() => new Map(students.value.map(s => [s.id, s])))
const embeddingById = computed(() => new Map(faces.value.map(f => [f.id, f.embedding])))
const eventGender = computed(() => {
  const e = events.value.find(x => x.id === Number(eventId.value))
  return e ? e.gender : 'both'
})
const unrecordedStudents = computed(() => {
  const g = eventGender.value
  return students.value.filter(s =>
    !recordedIds.has(s.id) && (g === 'both' || s.gender === g))
})

function genderLabel(g) {
  if (g === 'M') return '男'
  if (g === 'F') return '女'
  return '不限'
}

function fmt(ms) {
  const s = Math.floor(ms / 1000)
  return `${String(Math.floor(s / 60)).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}`
}

function saveBatch() {
  try { localStorage.setItem(BATCH_KEY, JSON.stringify({ eventId: eventId.value, records: records.value, schoolId: schoolId.value })) } catch (e) {}
}
function loadSavedBatch() {
  const raw = localStorage.getItem(BATCH_KEY)
  if (!raw) return
  try {
    const b = JSON.parse(raw)
    if (!b || !Array.isArray(b.records) || !b.records.length) return
    const ev = events.value.find(x => x.id === Number(b.eventId))
    if ((b.schoolId && schoolId.value && b.schoolId !== schoolId.value) || !ev) {
      try { localStorage.removeItem(BATCH_KEY) } catch (e) {}
      return
    }
    records.value = b.records
    eventId.value = b.eventId || ''
    recordedIds = new Set(b.records.map(r => r.id))
    mode.value = 'review'
    messages.value.push({ ok: false, text: `已恢复上次未上传批次（${b.records.length} 人）。核对后上传，或点“再来一批”清空。` })
  } catch (e) {}
}

async function login() {
  loginErr.value = ''
  try {
    const res = await api.post('/auth/login', { username: user.value, password: pass.value })
    localStorage.setItem('admin_token', res.data.access_token)
    localStorage.setItem('admin_info', JSON.stringify(res.data.admin))
    authed.value = true
    await refreshSync()
    loadSavedBatch()
  } catch (e) {
    loginErr.value = '登录失败，请检查账号密码'
  }
}

async function refreshSync() {
  try {
    const res = await api.get('/device/sync')
    const data = res.data
    localStorage.setItem(SYNC_KEY, JSON.stringify(data))
    applySync(data)
  } catch (e) {
    const cache = localStorage.getItem(SYNC_KEY)
    if (cache) applySync(JSON.parse(cache))
    else alert('无法同步学生名单，请检查网络与账号')
  }
}

function applySync(data) {
  schoolName.value = data.school_name || ''
  schoolId.value = data.school_id || ''
  events.value = data.long_run_events || []
  students.value = data.students || []
  faces.value = data.face_embeddings || []
}

function stopCamera() {
  const v = video.value
  if (v && v.srcObject) { v.srcObject.getTracks().forEach(t => t.stop()); v.srcObject = null }
}

async function startBatch() {
  if (!eventId.value) return
  running = true; records.value = []; recordedIds = new Set(); messages.value = []; uploadRes.value = {}
  startMs = performance.now(); mode.value = 'running'; statusText.value = '学生站到镜头前识别'
  try {
    await openCamera()
  } catch (e) {
    if (!running) return           // 期间已被结束/卸载：不覆盖 review
    running = false
    stopCamera()
    mode.value = 'ready'
    alert('无法启动摄像头/识别模型：' + (e && e.message ? e.message : e) + '\n请用 HTTPS 访问并允许摄像头权限')
    return
  }
  if (!running) return             // openCamera 期间被结束：不再起定时器/循环
  displayTimer = setInterval(() => { if (running) timerText.value = fmt(performance.now() - startMs) }, 100)
  recognizeLoop()
  try { if (navigator.wakeLock) wakeLock = await navigator.wakeLock.request('screen') } catch (e) {}
}

async function openCamera() {
  faceapi = await loadFaceapi()
  await ensureModels()
  const stream = await navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480 }, audio: false })
  // 异步间隙里可能已被「结束」或离开：迟到流立即释放，不上抛
  if (!running || !video.value) {
    stream.getTracks().forEach(t => t.stop())
    return
  }
  const v = video.value
  v.srcObject = stream
  await v.play()
  const c = overlay.value
  if (!c) return
  c.width = v.videoWidth
  c.height = v.videoHeight
  c._ctx = c.getContext('2d')
}

async function recognizeLoop() {
  if (!running) return
  let res = null
  try {
    const v = video.value
    if (v && v.readyState >= 2) res = await detectOne(faceapi, v)
  } catch (e) { res = null }
  if (!running) return               // 结束瞬间的在途帧：丢弃，不再追加
  const c = overlay.value, ctx = c._ctx, v = video.value
  if (ctx) ctx.clearRect(0, 0, c.width, c.height)
  if (res && ctx) {
    const sx = c.width / v.videoWidth, sy = c.height / v.videoHeight
    ctx.strokeStyle = '#5ce38a'; ctx.lineWidth = 3
    ctx.strokeRect(res.box.x * sx, res.box.y * sy, res.box.width * sx, res.box.height * sy)
    const g = eventGender.value
    const entries = students.value
      .filter(s => !recordedIds.has(s.id) && (g === 'both' || s.gender === g) && embeddingById.value.has(s.id))
      .map(s => ({ student: s, embedding: embeddingById.value.get(s.id) }))
    const hit = bestMatch(res.descriptor, entries, THRESHOLD)
    if (hit) {
      const elapsed = performance.now() - startMs
      recordOne(hit.student, elapsed)
      flashText.value = `✅ ${hit.student.name} · ${fmt(elapsed)}`
    } else {
      flashText.value = '❓ 未识别，请靠近或手动选择'
    }
    setTimeout(() => { if (flashText.value) flashText.value = '' }, 2200)
  }
  if (running) recTimer = setTimeout(recognizeLoop, 180)
}

function recordOne(s, elapsedMs) {
  if (recordedIds.has(s.id)) return
  recordedIds.add(s.id)
  records.value.push({ id: s.id, name: s.name, class_name: s.class_name || '', time: fmt(elapsedMs), timeMs: Math.round(elapsedMs) })
  statusText.value = `已记录 ${records.value.length} 人`
  saveBatch()
}

function manualRecord() {
  if (!manualSel.value) return
  const s = studentsById.value.get(Number(manualSel.value))
  if (!s || recordedIds.has(s.id)) return
  recordOne(s, performance.now() - startMs)
  manualSel.value = ''
}

function endBatch() {
  if (!running) return
  running = false
  clearInterval(displayTimer); clearTimeout(recTimer)
  if (wakeLock) { try { wakeLock.release() } catch (e) {} wakeLock = null }
  stopCamera()
  mode.value = 'review'
}

function removeRecord(i) {
  const r = records.value[i]
  if (!r) return
  recordedIds.delete(r.id)
  records.value.splice(i, 1)
  uploadRes.value = {}
  saveBatch()
}

function resetBatch() {
  records.value = []; messages.value = []; uploadRes.value = {}; eventId.value = ''
  try { localStorage.removeItem(BATCH_KEY) } catch (e) {}
  mode.value = 'ready'
}

async function upload() {
  if (!records.value.length || uploading.value) return
  uploading.value = true; messages.value = []
  try {
    const res = await api.post('/device/scores', {
      event_id: Number(eventId.value),
      scores: records.value.map(r => ({ student_id: r.id, time_ms: r.timeMs })),
    })
    const items = res.data
    const bySid = {}
    items.forEach(i => { bySid[i.student_id] = i })
    uploadRes.value = bySid
    const failed = items.filter(i => !i.ok)
    if (failed.length === 0) {
      messages.value.push({ ok: true, text: `✅ 已上传 ${items.length} 条，全部成功` })
      try { localStorage.removeItem(BATCH_KEY) } catch (e) {}
    } else {
      for (const f of failed) {
        const s = studentsById.value.get(f.student_id)
        messages.value.push({ ok: false, text: `${s ? s.name : f.student_id} 上传失败：${f.reason}（可删除该行后重传）` })
      }
      messages.value.push({ ok: true, text: `成功 ${items.length - failed.length} 条，其余处理后可再点上传（已成功行会安全覆盖，不重复）` })
      saveBatch()
    }
  } catch (e) {
    const st = e && e.response ? e.response.status : 0
    if (st === 401) {
      messages.value.push({ ok: false, text: '登录已过期。请重新登录后继续上传（本批已保存在本机，重新登录会自动恢复）' })
      authed.value = false
      saveBatch()
    } else if (st === 404) {
      messages.value.push({ ok: false, text: '项目不存在或已失效，无法上传。请点“再来一批”重新开始。' })
      try { localStorage.removeItem(BATCH_KEY) } catch (e) {}
    } else if (st >= 400) {
      messages.value.push({ ok: false, text: `上传被拒绝（HTTP ${st}），数据异常。请检查本批记录，或点“再来一批”重来。` })
      saveBatch()
    } else {
      messages.value.push({ ok: false, text: '网络错误：上传失败。本批已保存在本机，可稍后重试或“再来一批”' })
      saveBatch()
    }
  }
  uploading.value = false
}

onMounted(async () => {
  if (authed.value) { await refreshSync(); loadSavedBatch() }
})
onUnmounted(() => {
  running = false
  clearInterval(displayTimer); clearTimeout(recTimer)
  stopCamera()
})
</script>

<style scoped>
.run { min-height: 100vh; background: #020817; color: #eee; font-family: "Microsoft YaHei", system-ui; }
.center { min-height: 100vh; display: flex; align-items: center; justify-content: center; }
.card { background: #0f172a; border: 1px solid #1e293b; border-radius: 16px; padding: 32px 28px; width: 420px; max-width: 94vw; text-align: center; }
.card.wide { width: 700px; }
.card h2 { margin: 0 0 6px; font-size: 24px; }
.sub { color: #94a3b8; margin: 0 0 18px; }
input { display: block; width: 100%; box-sizing: border-box; margin: 8px 0; padding: 12px; font-size: 16px; border-radius: 8px; border: 1px solid #334155; background: #1e293b; color: #eee; }
button { margin: 8px 4px; padding: 12px 18px; font-size: 16px; border: none; border-radius: 8px; cursor: pointer; color: #fff; }
.big.primary { background: #16a34a; font-size: 22px; padding: 16px 28px; }
.big.danger { background: #dc2626; font-size: 20px; padding: 14px 24px; width: 100%; }
.ghost { background: #475569; }
.mini.danger { padding: 4px 10px; font-size: 13px; background: #dc2626; margin: 0 0 0 6px; }
button:disabled { opacity: .4; }
.err { color: #f87171; font-size: 13px; }
.ok { color: #4ade80; font-size: 13px; }
.big-select { display: block; width: 100%; margin: 8px 0; padding: 12px; font-size: 18px; border-radius: 8px; background: #1e293b; color: #eee; border: 1px solid #334155; }
.run-split { min-height: 100vh; display: flex; gap: 16px; padding: 16px; }
.video-wrap { position: relative; flex: 1; min-width: 300px; }
video { width: 100%; border-radius: 12px; background: #000; }
canvas { position: absolute; inset: 0; }
.flash { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); background: rgba(0,0,0,.75); padding: 12px 24px; border-radius: 12px; font-size: 30px; font-weight: bold; white-space: nowrap; }
.side { width: 360px; display: flex; flex-direction: column; gap: 10px; }
.timer { font-size: 72px; font-weight: bold; font-variant-numeric: tabular-nums; color: #4ade80; }
.status { color: #facc15; }
.manual { display: flex; gap: 6px; }
.manual-select { flex: 1; padding: 10px; font-size: 15px; border-radius: 8px; background: #1e293b; color: #eee; border: 1px solid #334155; }
.list { flex: 1; overflow-y: auto; }
.rec { display: flex; justify-content: space-between; padding: 6px 10px; background: #0f172a; border-radius: 8px; margin-bottom: 4px; }
.rec b { color: #4ade80; font-variant-numeric: tabular-nums; }
table { width: 100%; border-collapse: collapse; margin: 12px 0; font-size: 15px; }
th, td { border: 1px solid #1e293b; padding: 6px 8px; }
th { background: #1e293b; }
</style>
