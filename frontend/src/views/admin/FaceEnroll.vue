<template>
  <div class="enroll">
    <h2>人脸录入</h2>
    <p class="sub">已录入 {{ enrolledCount }} / {{ students.length }} 人（同步自学校学生名单，刷新页面自动同步）</p>

    <el-tabs v-model="tab">
      <!-- 批量导入 -->
      <el-tab-pane label="批量导入" name="batch">
        <div class="tip">
          将学生照片放在一个文件夹，文件名格式 <b>学号.jpg</b>（如 <code>270101.jpg</code>）。浏览器本地识别，不上传照片。
        </div>
        <input ref="dirInput" type="file" webkitdirectory directory @change="pickFiles" />
        <button :disabled="!picked.length || writing" @click="runBatch">{{ writing ? '写入中…' : '开始批量写入' }}</button>
        <div class="progress">{{ batchDone }} / {{ picked.length }}</div>
        <div class="log">
          <div v-for="(m, i) in batchLog" :key="i" :class="m.ok ? 'ok' : 'err'">{{ m.text }}</div>
        </div>
      </el-tab-pane>

      <!-- 单个补录 -->
      <el-tab-pane label="单个补录" name="single">
        <el-select v-model="singleSid" filterable placeholder="搜索学生（姓名/学号）" style="width:260px">
          <el-option v-for="s in students" :key="s.id" :label="`${s.name} ${s.student_id} ${s.class_name || ''}${hasFace(s.id) ? ' ✓' : ''}`" :value="s.id" />
        </el-select>
        <button :disabled="!singleSid" @click="startCapture">📷 拍照录入</button>
        <div v-if="capturing" class="cap">
          <video ref="cam" autoplay playsinline muted></video>
          <div>
            <button class="green" @click="captureAndSave">确认这张照片</button>
            <button class="gray" @click="stopCapture">取消</button>
          </div>
        </div>
        <p v-if="capMsg" :class="capMsgOk ? 'ok' : 'err'">{{ capMsg }}</p>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import api from '../../api'
import { loadFaceapi, ensureModels, detectOne } from '../../faceutil'

const tab = ref('batch')
const students = ref([])
const faceIds = ref(new Set())
const picked = ref([])          // { name, file }
const writing = ref(false)
const batchDone = ref(0)
const batchLog = ref([])
const singleSid = ref('')
const capturing = ref(false)
const cam = ref(null)
const capMsg = ref(''); const capMsgOk = ref(false)
let faceapi = null, stream = null

const enrolledCount = computed(() => students.value.filter(s => faceIds.value.has(s.id)).length)
const hasFace = id => faceIds.value.has(id)

async function refresh() {
  const res = await api.get('/device/sync')
  students.value = res.data.students || []
  faceIds.value = new Set((res.data.face_embeddings || []).map(f => f.id))
}

async function readyFace() {
  faceapi = await loadFaceapi()
  await ensureModels()
}

function pickFiles(e) {
  const files = Array.from(e.target.files || [])
  const imgs = files.filter(f => /\.(jpe?g|png)$/i.test(f.name))
  picked.value = imgs.map(f => ({ name: f.name, file: f }))
  batchLog.value = []
}

async function readImageAsCanvas(file) {
  const url = URL.createObjectURL(file)
  const img = new Image()
  await new Promise((res, rej) => { img.onload = res; img.onerror = rej; img.src = url })
  const maxSide = 640
  const scale = Math.min(1, maxSide / Math.max(img.width, img.height))
  const c = document.createElement('canvas')
  c.width = Math.round(img.width * scale); c.height = Math.round(img.height * scale)
  c.getContext('2d').drawImage(img, 0, 0, c.width, c.height)
  URL.revokeObjectURL(url)
  return c
}

async function runBatch() {
  if (!picked.value.length) return
  await readyFace()
  writing.value = true; batchDone.value = 0; batchLog.value = []
  const results = []
  for (const p of picked.value) {
    const sid6 = p.name.replace(/\.[^.]+$/, '').trim()
    const st = students.value.find(s => s.student_id === sid6)
    if (!st) { batchLog.value.push({ ok: false, text: `${p.name}: 学号 ${sid6} 不在学生名单` }); batchDone.value++; continue }
    try {
      const canvas = await readImageAsCanvas(p.file)
      const res = await detectOne(faceapi, canvas)
      if (!res) { batchLog.value.push({ ok: false, text: `${p.name}: 照片里未检测到人脸` }); batchDone.value++; continue }
      results.push({ student_id: st.id, embedding: Array.from(res.descriptor) })
    } catch (err) {
      batchLog.value.push({ ok: false, text: `${p.name}: ${err.message}` })
    }
    batchDone.value++
  }
  if (results.length) {
    try {
      const r = await api.post('/faces/batch', { faces: results })
      r.data.forEach(item => {
        const st = students.value.find(s => s.id === item.student_id)
        batchLog.value.push({ ok: item.ok, text: `${st ? st.name : item.student_id} ${item.ok ? '✓ 已录入' : '✗ ' + (item.reason || '失败')}` })
      })
      await refresh()
    } catch (e) {
      batchLog.value.push({ ok: false, text: '写入请求失败：' + (e.message || e) })
    }
  }
  writing.value = false
}

async function startCapture() {
  await readyFace()
  capturing.value = true; capMsg.value = ''
  stream = await navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480 }, audio: false })
  const v = cam.value
  v.srcObject = stream
  await v.play()
}

async function captureAndSave() {
  const v = cam.value
  const c = document.createElement('canvas')
  c.width = v.videoWidth; c.height = v.videoHeight
  c.getContext('2d').drawImage(v, 0, 0)
  const res = await detectOne(faceapi, c)
  if (!res) { capMsg.value = '未检测到人脸，请正对镜头'; capMsgOk.value = false; return }
  const sid = Number(singleSid.value)
  await api.put(`/faces/${sid}`, { embedding: Array.from(res.descriptor) })
  capMsg.value = '✓ 已录入'; capMsgOk.value = true
  stopCapture()
  await refresh()
}

function stopCapture() {
  capturing.value = false
  if (stream) { stream.getTracks().forEach(t => t.stop()); stream = null }
}

onMounted(() => refresh())
onUnmounted(stopCapture)
</script>

<style scoped>
.enroll { color: #eee; }
h2 { margin: 0 0 6px; }
.sub { color: #94a3b8; }
.tip { color: #cbd5e1; font-size: 14px; margin: 8px 0; background: #1e293b; padding: 10px; border-radius: 8px; }
button { margin: 8px 8px 8px 0; padding: 10px 16px; border: none; border-radius: 8px; cursor: pointer; background: #2563eb; color: #fff; font-size: 15px; }
.green { background: #16a34a; } .gray { background: #475569; }
.progress { margin: 6px 0; color: #facc15; }
.log { max-height: 260px; overflow-y: auto; font-size: 13px; }
.ok { color: #4ade80; } .err { color: #f87171; }
.cap video { width: 100%; max-width: 560px; border-radius: 10px; margin: 8px 0; background: #000; }
</style>
