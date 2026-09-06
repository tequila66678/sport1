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
        <p class="hint">识别后自动区分项目：<b class="mk">男生 → 1000 米</b> · <b class="fk">女生 → 800 米</b><br>识别到即直接记入对应项目成绩</p>
        <button class="big primary" @click="startBatch">▶ 开始批次</button>
        <button class="ghost" @click="refreshSync">刷新名单</button>
      </div>
    </div>

    <!-- 计时中：一屏三段 时间 → 人脸 → 成绩榜（一眼 5+ 条） -->
    <div v-else-if="mode === 'running'" class="live">
      <div class="live-top">
        <div class="timer">{{ timerText }}</div>
        <div class="status">{{ statusText }}<span class="rec-count"> · 已记录 {{ records.length }} 人</span></div>
      </div>
      <div class="video-wrap">
        <video ref="video" autoplay playsinline muted></video>
        <canvas ref="overlay"></canvas>
        <div v-if="flashText" class="flash">{{ flashText }}</div>
        <button class="end-btn" @click="endBatch">■ 结束</button>
      </div>
      <div class="manual">
        <input v-model="manualId" class="manual-id" placeholder="识别不到 → 输入学号" @keyup.enter="manualRecord" />
        <button @click="manualRecord">记下</button>
      </div>
      <div class="board">
        <div class="b-head"><span>#</span><span>姓名</span><span>成绩</span></div>
        <div v-for="(r, i) in records" :key="i" class="b-row">
          <span class="b-no">{{ i + 1 }}</span>
          <span class="b-name">{{ r.name }}</span>
          <span class="b-time">{{ r.time }}</span>
        </div>
        <div v-if="!records.length" class="b-empty">等待第一位学生冲线…</div>
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
              <td>{{ i + 1 }}</td><td>{{ r.name }}</td><td>{{ r.class_name }}</td><td class="t">{{ r.time }}</td>
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
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import api from '../api'
import { loadFaceapi, ensureModels, detectOne, bestMatch, rankMatches, verifyStudent, faceQuality, FACE_CONFIG } from '../faceutil'

// 识别流程参数（匹配阈值/余量统一在 faceutil FACE_CONFIG，单一来源，防两处漂移）
const RECOGNITION_FLOW = {
  interval: 100,        // 识别轮询间隔 ms
  voteWindow: 4,        // 投票窗口帧数
  minVotes: 3,          // 窗口内满 3 票才算确认
  unlockFrames: 15,     // 无脸 / verify 持续失败达 N 帧 → 释放（≈1.5s）
  candidateTimeout: 5,  // 人脸在但匹配不上，超 N 轮提示一次
}
const SYNC_KEY = 'run_sync_cache_v1'
const BATCH_KEY = 'run_batch_v1'

const authed = ref(!!localStorage.getItem('admin_token'))
const user = ref(''); const pass = ref(''); const loggingIn = ref(false); const loginErr = ref('')
const schoolName = ref(''); const events = ref([]); const students = ref([]); const faces = ref([])
const schoolId = ref('')
const mode = ref('ready')           // ready | running | review
const video = ref(null); const overlay = ref(null)
const records = ref([])             // { id, name, class_name, gender, event_id, time, timeMs }
const timerText = ref('00:00'); const statusText = ref(''); const flashText = ref('')
const manualId = ref(''); const uploading = ref(false); const messages = ref([])
const uploadRes = ref({})           // sid -> {ok, raw_value?, earned_score?, reason?}
let running = false, startMs = 0, displayTimer = null, recTimer = null, faceapi = null, wakeLock = null
let recordedIds = new Set()

// 人脸状态机：WAITING → CANDIDATE(投票中) → LOCKED。锁定后只 verify 这一人，绝不中途换人。
const faceState = reactive({
  phase: 'WAITING',        // WAITING | CANDIDATE | LOCKED
  student: null,           // LOCKED 时锁定的身份（含 embedding，供 verify）
  candidate: null,         // 当前投票跟踪的学生（身份跳变时清票重投）
  votes: [],               // 最近 voteWindow 帧的投票 id
  noFaceFrames: 0,         // 连续无脸/弱脸帧数
  verifyFailFrames: 0,     // LOCKED 后 verify 连续失败帧数（离场解锁依据）
  candidateFrames: 0,      // 人脸在但匹配不上，连续轮数
})

// 识别候选池：只取「有向量」的学生，按本批是否已记录拆成 pending / recorded 两池。
// 池依赖 students/faces/recordedIds，仅在 applySync/startBatch/recordOne/removeRecord/resetBatch 时重建，
// 避免识别循环里每帧 O(n) filter+map。学生对象本身不带向量，此处直接灌注 embedding。
let allFacePool = []
let pendingFacePool = []
let recordedFacePool = []
function rebuildFacePools() {
  allFacePool = students.value
    .filter(s => embeddingById.value.has(s.id))
    .map(s => ({
      id: s.id, student_id: s.student_id, name: s.name, gender: s.gender,
      class_name: s.class_name || '', embedding: embeddingById.value.get(s.id),
    }))
  pendingFacePool = []
  recordedFacePool = []
  for (const p of allFacePool) {
    if (recordedIds.has(p.id)) recordedFacePool.push(p)
    else pendingFacePool.push(p)
  }
}

// 4 帧滑动窗口，数当前学生票数；满 minVotes 即确认
function pushVote(student) {
  faceState.votes.push(student.id)
  if (faceState.votes.length > RECOGNITION_FLOW.voteWindow) faceState.votes.shift()
  let count = 0
  for (const id of faceState.votes) if (id === student.id) count++
  return { id: student.id, count, confirmed: count >= RECOGNITION_FLOW.minVotes }
}

function lockStudent(student) {
  faceState.phase = 'LOCKED'
  faceState.student = student
  faceState.votes = []
  faceState.candidate = null
  faceState.noFaceFrames = 0
  faceState.verifyFailFrames = 0
  faceState.candidateFrames = 0
}

function unlockStudent() {
  faceState.phase = 'WAITING'
  faceState.student = null
  faceState.candidate = null
  faceState.votes = []
  faceState.noFaceFrames = 0
  faceState.verifyFailFrames = 0
  faceState.candidateFrames = 0
}

const studentsById = computed(() => new Map(students.value.map(s => [s.id, s])))
const studentsByNo = computed(() => new Map(students.value.map(s => [s.student_id, s])))
const embeddingById = computed(() => new Map(faces.value.map(f => [f.id, f.embedding])))

// 按性别挑项目：男生→1000米、女生→800米（从本校正的长跑项目里选匹配项）
function pickEvent(gender) {
  const want800 = gender === 'F'
  let ev = events.value.find(e =>
    (e.gender === gender || e.gender === 'both') &&
    (want800 ? e.name.includes('800') : e.name.includes('1000')))
  if (!ev) ev = events.value.find(e => e.gender === gender)
  return ev || null
}

// 闪屏提示：自动 2.2s 后清除。同文案 800ms 内去重（防持续条件每帧重排定时器/刷屏）；
// force=true 用于成功等关键提示，保证不因去重被吞掉。
let flashTimer = null
let lastFlashAt = 0
let lastFlashText = ''
function flashNow(text, force = false) {
  const now = Date.now()
  if (!force && text === lastFlashText && now - lastFlashAt < 800) return
  lastFlashText = text
  lastFlashAt = now
  flashText.value = text
  if (flashTimer) clearTimeout(flashTimer)
  flashTimer = setTimeout(() => {
    if (flashText.value === text) { flashText.value = ''; flashTimer = null }
  }, 2200)
}

function fmt(ms) {
  const s = Math.floor(ms / 1000)
  return `${String(Math.floor(s / 60)).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}`
}

function saveBatch() {
  try { localStorage.setItem(BATCH_KEY, JSON.stringify({ records: records.value, schoolId: schoolId.value })) } catch (e) {}
}
function loadSavedBatch() {
  const raw = localStorage.getItem(BATCH_KEY)
  if (!raw) return
  try {
    const b = JSON.parse(raw)
    const saved = Array.isArray(b.records) ? b.records.filter(r => r && r.event_id && r.gender) : []
    if (!saved.length || (b.schoolId && schoolId.value && b.schoolId !== schoolId.value)) {
      try { localStorage.removeItem(BATCH_KEY) } catch (e) {}
      return
    }
    records.value = saved
    recordedIds = new Set(saved.map(r => r.id))
    mode.value = 'review'
    messages.value.push({ ok: false, text: `已恢复上次未上传批次（${saved.length} 人）。核对后上传，或点“再来一批”清空。` })
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
  rebuildFacePools()
}

function stopCamera() {
  const v = video.value
  if (v && v.srcObject) { v.srcObject.getTracks().forEach(t => t.stop()); v.srcObject = null }
}

async function startBatch() {
  running = true; records.value = []; recordedIds = new Set(); messages.value = []; uploadRes.value = {}
  unlockStudent()
  rebuildFacePools()      // recordedIds 已清空，池子必须回落到「全员可识别」，否则上批已记录者本批永远匹配不上
  startMs = performance.now(); mode.value = 'running'
  statusText.value = '男生→1000米 · 女生→800米，站到镜头前识别'
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

  // —— 无脸 / 脸太弱：LOCKED 时攒满帧数才释放，防上一人刚记完立刻连记下一位 ——
  //    弱脸也算「离场」，避免有人躲在镜头边缘脸小不动导致锁死
  if (!res || faceQuality(res) < FACE_CONFIG.qualityThreshold) {
    faceState.noFaceFrames++
    faceState.candidateFrames = 0
    if (faceState.phase === 'LOCKED' && faceState.noFaceFrames >= RECOGNITION_FLOW.unlockFrames) unlockStudent()
    if (running) recTimer = setTimeout(recognizeLoop, RECOGNITION_FLOW.interval)
    return
  }
  faceState.noFaceFrames = 0

  // —— LOCKED：只 verify 当前锁定的人，锁内绝不换人 ——
  if (faceState.phase === 'LOCKED') {
    if (verifyStudent(res.descriptor, faceState.student)) {
      faceState.verifyFailFrames = 0
    } else {
      // 连续 1.5s verify 不过 = 本人已离开 / 他人占镜 → 释放，别死锁
      faceState.verifyFailFrames++
      if (faceState.verifyFailFrames >= RECOGNITION_FLOW.unlockFrames) unlockStudent()
    }
    if (running) recTimer = setTimeout(recognizeLoop, RECOGNITION_FLOW.interval)
    return
  }

  // —— 未锁定：只在「本批未记录」的池子里 Top1/Top2 匹配（已灌注 embedding）——
  const result = rankMatches(res.descriptor, pendingFacePool)
  if (!result.pass) {
    // 是已记录的人又回来 → 明确提示「已记录」，不误报未识别
    faceState.candidateFrames++
    const again = bestMatch(res.descriptor, recordedFacePool)
    if (again) {
      faceState.candidateFrames = 0
      flashNow(`⚠️ ${again.student.name} 本批已记录`)
    } else if (faceState.candidateFrames >= RECOGNITION_FLOW.candidateTimeout) {
      faceState.votes = []
      faceState.candidate = null
      faceState.candidateFrames = 0
      flashNow('❓ 未识别，请靠近或手动输学号')
    }
    if (running) recTimer = setTimeout(recognizeLoop, RECOGNITION_FLOW.interval)
    return
  }

  // —— 投票确认：身份跳变则清窗重投，防 A/B 交替混出错误多数 ——
  const best = result.best
  if (faceState.candidate && faceState.candidate.id !== best.id) {
    faceState.votes = []
    faceState.candidateFrames = 0
  }
  faceState.candidate = best

  const vote = pushVote(best)
  if (vote.confirmed) {
    lockStudent(best)
    // 模型 A：识别确认帧 = 冲线帧，elapsed 此刻冻结，成绩只从这一个出口产生
    const elapsed = performance.now() - startMs
    if (recordOne(best, elapsed)) {
      flashNow(`✅ ${best.name} · ${fmt(elapsed)}`, true)
    } else {
      unlockStudent()
      flashNow('⚠️ 该生无 800/1000 项目，无法记录')
    }
  } else {
    statusText.value = `确认 ${best.name} …（${vote.count}/${RECOGNITION_FLOW.minVotes}）`
  }
  if (running) recTimer = setTimeout(recognizeLoop, RECOGNITION_FLOW.interval)
}

function recordOne(s, elapsedMs) {
  if (recordedIds.has(s.id)) return false
  const ev = pickEvent(s.gender)
  if (!ev) return false
  recordedIds.add(s.id)
  records.value.push({
    id: s.id, name: s.name, class_name: s.class_name || '', gender: s.gender,
    event_id: ev.id, time: fmt(elapsedMs), timeMs: Math.round(elapsedMs),
  })
  rebuildFacePools()      // 该生移入 recordedFacePool，下帧起不会重复进入 pending 被再次识别
  statusText.value = `已记录 ${records.value.length} 人`
  saveBatch()
  return true
}

function manualRecord() {
  const no = manualId.value.trim()
  if (!no) return
  const s = studentsByNo.value.get(no)
  if (!s) { flashNow(`未找到学号 ${no}`); return }
  if (recordedIds.has(s.id)) { flashNow(`⚠️ ${s.name} 本批已记录`); manualId.value = ''; return }
  const elapsed = performance.now() - startMs
  if (recordOne(s, elapsed)) {
    // 手动纠错成功 → 状态机归位，机器立即可接下一位（不必等 LOCKED 的 1.5s verify 超时）。
    // recordedIds 仍挡住重复；该生若有向量又回镜头，走「已记录」提示。
    unlockStudent()
    flashNow(`✅ 手动 ${s.name} · ${fmt(elapsed)}`, true)
  } else {
    flashNow('⚠️ 该生无 800/1000 项目，无法记录')
  }
  manualId.value = ''
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
  rebuildFacePools()      // 该生退回 pending，若回炉重跑可被再次识别
  saveBatch()
}

function resetBatch() {
  records.value = []; messages.value = []; uploadRes.value = {}; manualId.value = ''
  recordedIds = new Set()
  unlockStudent()
  rebuildFacePools()      // 清空本批记录后，池子回落为全员可识别
  try { localStorage.removeItem(BATCH_KEY) } catch (e) {}
  mode.value = 'ready'
}

async function upload() {
  if (!records.value.length || uploading.value) return
  uploading.value = true; messages.value = []
  try {
    // 按项目分组上传：男→1000米、女→800米 各自成一批
    const groups = {}
    for (const r of records.value) {
      if (!groups[r.event_id]) groups[r.event_id] = []
      groups[r.event_id].push(r)
    }
    const bySid = {}
    let okCount = 0
    for (const evId of Object.keys(groups)) {
      const list = groups[evId]
      const res = await api.post('/device/scores', {
        event_id: Number(evId),
        scores: list.map(r => ({ student_id: r.id, time_ms: r.timeMs })),
      })
      res.data.forEach(i => { bySid[i.student_id] = i; if (i.ok) okCount++ })
    }
    uploadRes.value = bySid
    const failed = records.value.filter(r => {
      const result = bySid[r.id]
      return !result || !result.ok      // 服务端未确认(缺条目)同样算失败，绝不能清空本批
    })
    if (failed.length === 0) {
      messages.value.push({ ok: true, text: `✅ 已上传 ${records.value.length} 条，全部成功` })
      try { localStorage.removeItem(BATCH_KEY) } catch (e) {}
    } else {
      for (const f of failed) {
        const s = studentsById.value.get(f.id)
        const result = bySid[f.id]
        const reason = result ? (result.reason || '未知原因') : '服务端未返回确认'
        messages.value.push({ ok: false, text: `${s ? s.name : f.id} 上传失败：${reason}（可删除该行后重传）` })
      }
      messages.value.push({ ok: true, text: `成功 ${okCount} 条，其余处理后可再点上传（已成功行会安全覆盖，不重复）` })
      saveBatch()
    }
  } catch (e) {
    const st = e && e.response ? e.response.status : 0
    if (st === 401) {
      messages.value.push({ ok: false, text: '登录已过期。请重新登录后继续上传（本批已保存在本机，重新登录会自动恢复）' })
      authed.value = false
      saveBatch()
    } else if (st === 404) {
      messages.value.push({ ok: false, text: '某个项目不存在或已失效，无法上传。请点“再来一批”重新开始。' })
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

/* 登录 / 待开始 / 结束核对：全屏居中卡片，移动端自适应 */
.center { min-height: 100vh; display: flex; align-items: center; justify-content: center; padding: 14px; box-sizing: border-box; }
.card { background: #0f172a; border: 1px solid #1e293b; border-radius: 18px; padding: 26px 18px; width: 100%; max-width: 480px; text-align: center; box-sizing: border-box; }
.card.wide { max-width: 700px; }
.card h2 { margin: 0 0 8px; font-size: clamp(20px, 5.6vw, 28px); }
.sub { color: #94a3b8; margin: 0 0 18px; font-size: clamp(13px, 3.6vw, 16px); }
.hint { color: #cbd5e1; font-size: clamp(13px, 3.6vw, 16px); margin: 2px 0 16px; line-height: 1.6; }
.hint b.mk { color: #60a5fa; }
.hint b.fk { color: #f472b6; }
input { display: block; width: 100%; box-sizing: border-box; margin: 10px 0; padding: clamp(12px, 3.4vw, 15px); font-size: clamp(17px, 4.4vw, 20px); border-radius: 10px; border: 1px solid #334155; background: #1e293b; color: #eee; }
button { margin: 6px 2px; padding: clamp(12px, 3.6vw, 16px) clamp(16px, 5vw, 26px); font-size: clamp(16px, 4.2vw, 19px); border: none; border-radius: 12px; cursor: pointer; color: #fff; touch-action: manipulation; }
.big.primary { background: #16a34a; font-size: clamp(20px, 5.6vw, 26px); padding: clamp(14px, 4vw, 18px) clamp(24px, 8vw, 40px); }
.big.danger { background: #dc2626; font-size: clamp(19px, 5.2vw, 24px); padding: clamp(12px, 3.6vw, 15px); width: 100%; }
.ghost { background: #475569; }
.mini.danger { padding: 6px 12px; font-size: clamp(13px, 3.4vw, 16px); background: #dc2626; margin: 0 0 0 6px; border-radius: 8px; }
button:disabled { opacity: .4; }
.err { color: #f87171; font-size: clamp(13px, 3.5vw, 16px); }
.ok { color: #4ade80; font-size: clamp(13px, 3.5vw, 16px); }
.big-select { display: block; width: 100%; margin: 10px 0; padding: clamp(13px, 3.8vw, 16px); font-size: clamp(17px, 4.4vw, 20px); border-radius: 10px; background: #1e293b; color: #eee; border: 1px solid #334155; }

/* —— 计时中：一屏三段 时间→人脸→成绩榜 —— */
.live { height: 100vh; height: 100dvh; display: flex; flex-direction: column; overflow: hidden; box-sizing: border-box; padding: 6px 8px calc(6px + env(safe-area-inset-bottom)); gap: 6px; }
.live-top { text-align: center; flex: none; line-height: 1.08; }
.timer { font-size: clamp(56px, 15vh, 150px); font-weight: bold; font-variant-numeric: tabular-nums; color: #4ade80; text-shadow: 0 0 18px rgba(74,222,128,.28); }
.status { font-size: clamp(12px, 3.2vw, 15px); color: #94a3b8; margin-top: 2px; }
.rec-count { color: #facc15; }
.video-wrap { flex: none; height: clamp(150px, 30vh, 300px); position: relative; background: #000; border-radius: 12px; overflow: hidden; }
video { width: 100%; height: 100%; object-fit: cover; display: block; background: #000; }
canvas { position: absolute; inset: 0; width: 100%; height: 100%; }
.flash { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); background: rgba(0,0,0,.8); padding: clamp(6px, 2vw, 12px) clamp(14px, 4vw, 26px); border-radius: 14px; font-size: clamp(24px, 6vw, 44px); font-weight: bold; white-space: nowrap; max-width: 94%; overflow: hidden; text-overflow: ellipsis; border: 2px solid rgba(255,255,255,.2); }
.end-btn { position: absolute; right: 8px; bottom: 8px; background: rgba(220,38,38,.92); color: #fff; font-size: clamp(16px, 4vw, 20px); font-weight: bold; padding: clamp(8px, 2vw, 12px) clamp(14px, 3.6vw, 20px); border: none; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,.4); }
.manual { flex: none; display: flex; gap: 6px; }
.manual-id { flex: 1; min-width: 0; width: auto; margin: 0; padding: clamp(8px, 2vw, 11px); font-size: clamp(15px, 4vw, 19px); border-radius: 8px; border: 1px solid #334155; background: #1e293b; color: #eee; }
.manual button { background: #475569; white-space: nowrap; padding: clamp(6px, 2vw, 9px) clamp(12px, 3vw, 16px); font-size: clamp(14px, 3.6vw, 17px); }
.board { flex: 1; min-height: 0; overflow-y: auto; display: flex; flex-direction: column; gap: 3px; }
.b-head, .b-row { display: flex; align-items: center; gap: 8px; padding: 0 10px; }
.b-head { flex: none; color: #64748b; font-size: clamp(11px, 2.8vw, 13px); padding: 2px 10px; }
.b-head > span:nth-child(1) { width: 26px; text-align: center; flex: none; }
.b-head > span:nth-child(2) { flex: 1; }
.b-head > span:nth-child(3) { flex: none; }
.b-row { flex: none; min-height: clamp(40px, 6.6vh, 54px); background: #0f172a; border-radius: 8px; font-size: clamp(15px, 4.2vw, 19px); }
.b-no { width: 26px; color: #64748b; text-align: center; font-variant-numeric: tabular-nums; flex: none; }
.b-name { flex: 1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.b-time { flex: none; font-variant-numeric: tabular-nums; font-weight: bold; color: #4ade80; font-size: clamp(19px, 5.4vw, 28px); }
.b-empty { color: #475569; font-size: clamp(14px, 3.6vw, 17px); text-align: center; padding: 10px; }

/* —— 结束核对：成绩列大字号 —— */
table { width: 100%; border-collapse: collapse; margin: 12px 0; font-size: clamp(14px, 3.8vw, 17px); }
th, td { border: 1px solid #1e293b; padding: clamp(7px, 1.8vw, 10px) 6px; text-align: left; }
th { background: #1e293b; text-align: center; }
td:first-child, th:first-child { text-align: center; }
td.t { font-variant-numeric: tabular-nums; font-weight: bold; font-size: clamp(20px, 5.4vw, 30px); color: #4ade80; text-align: center; }
</style>
