// face-api.js 加载 + 单脸特征 + 比对。库与模型由后端 /face 静态托管。
let loadPromise = null

// 匹配阈值/余量/质量门槛唯一来源（V2：Run.vue 不再重复定义 threshold/margin；改动这些参数不影响特征空间，无需全员重录）
export const FACE_CONFIG = {
  threshold: 0.45,             // 欧氏距离上限，越小越像
  margin: 0.08,                // 第一名须比第二名明显更近，否则视为不确定
  verifyTolerance: 0.05,       // LOCKED 期间只验一人时额外放宽的距离，防转头/轻微遮挡抖动误判离场
  detectorInputSize: 416,      // TinyFaceDetector 输入尺寸；416 保证中距离小脸仍可检出（维持，等真机 416 vs 320 实测再定）
  detectorScoreThreshold: 0.5, // TinyFaceDetector 检出置信下限
  minFaceSize: 80,             // 人脸最小像素（原图坐标），低于此视为无脸
  qualityThreshold: 60,        // faceQuality 低于此 → 视为弱脸/无脸（Run.vue 引用，过滤垃圾帧）
}

export function loadFaceapi() {
  if (window.faceapi) return Promise.resolve(window.faceapi)
  if (loadPromise) return loadPromise
  loadPromise = new Promise((resolve, reject) => {
    const s = document.createElement('script')
    s.src = '/face/lib/face-api.min.js'
    s.onload = () => resolve(window.faceapi)
    s.onerror = () => { loadPromise = null; reject(new Error('face-api.js 加载失败')) }
    document.head.appendChild(s)
  })
  return loadPromise
}

export async function ensureModels() {
  const faceapi = await loadFaceapi()
  if (!faceapi.nets.tinyFaceDetector.isLoaded) await faceapi.nets.tinyFaceDetector.loadFromUri('/face/models')
  if (!faceapi.nets.faceLandmark68Net.isLoaded) await faceapi.nets.faceLandmark68Net.loadFromUri('/face/models')
  if (!faceapi.nets.faceRecognitionNet.isLoaded) await faceapi.nets.faceRecognitionNet.loadFromUri('/face/models')
}

// 检测器选项与单帧无关，缓存一份避免每帧 new（参数恒定，可安全复用）
let detectorOptions = null
function getDetectorOptions(faceapi) {
  if (!detectorOptions) {
    detectorOptions = new faceapi.TinyFaceDetectorOptions({
      inputSize: FACE_CONFIG.detectorInputSize,
      scoreThreshold: FACE_CONFIG.detectorScoreThreshold,
    })
  }
  return detectorOptions
}

// 检测 + 提特征。landmark 保留：对齐能提升识别准确率，且录脸/识别共用本函数保证特征空间一致。
export async function detectOne(faceapi, input) {
  const res = await faceapi.detectSingleFace(input, getDetectorOptions(faceapi))
    .withFaceLandmarks()
    .withFaceDescriptor()
  if (!res) return null
  const box = res.detection.box
  if (box.width < FACE_CONFIG.minFaceSize || box.height < FACE_CONFIG.minFaceSize) return null
  return { descriptor: res.descriptor, box, score: res.detection.score }
}

// 平方距离：匹配阶段全程只做平方比较，只在真正需要返回距离时才开一次 sqrt
function squaredDistance(a, b) {
  let sum = 0
  for (let i = 0; i < a.length; i++) {
    const d = a[i] - b[i]
    sum += d * d
  }
  return sum
}

export function euclidean(a, b) {
  return Math.sqrt(squaredDistance(a, b))
}

// 单学生与 descriptor 的最小平方距离（支持未来多模板）：
//   { embedding: [128] }          旧结构（当前后端）
//   { embeddings: [[128], ...] }  未来多模板
function bestSquaredToStudent(descriptor, student) {
  let templates = []
  if (Array.isArray(student.embeddings)) templates = student.embeddings
  else if (student.embedding) templates = [student.embedding]
  if (!templates.length) return Infinity
  let best = Infinity
  for (const temp of templates) {
    const d = squaredDistance(descriptor, temp)
    if (d < best) best = d
  }
  return best
}

export function studentDistance(descriptor, student) {
  const dSq = bestSquaredToStudent(descriptor, student)
  return dSq === Infinity ? Infinity : Math.sqrt(dSq)
}

// Top1/Top2 单次扫描（不 sort 全数组）。平方域比较，只对前两名各开一次 sqrt。
// 返回 { best, second, bestDistance, secondDistance, pass }
export function rankMatches(descriptor, candidates) {
  let best = null, second = null
  let bestSq = Infinity, secondSq = Infinity
  for (const student of candidates) {
    const dSq = bestSquaredToStudent(descriptor, student)
    if (dSq < bestSq) {
      secondSq = bestSq; second = best
      bestSq = dSq; best = student
    } else if (dSq < secondSq) {
      secondSq = dSq; second = student
    }
  }
  const bestDistance = best ? Math.sqrt(bestSq) : Infinity
  const secondDistance = second ? Math.sqrt(secondSq) : Infinity
  const pass = !!best &&
    bestDistance < FACE_CONFIG.threshold &&
    (secondDistance - bestDistance) > FACE_CONFIG.margin
  return { best, second, bestDistance, secondDistance, pass }
}

// 在 candidates 里找最近的一个，距离 < threshold 才命中。返回 { student, dist } 或 null
export function bestMatch(descriptor, candidates, threshold = FACE_CONFIG.threshold) {
  let best = null
  let bestSq = Infinity
  for (const c of candidates) {
    const dSq = bestSquaredToStudent(descriptor, c)
    if (dSq < bestSq) { bestSq = dSq; best = c }
  }
  const tSq = threshold * threshold
  if (best && bestSq < tSq) return { student: best, dist: Math.sqrt(bestSq) }
  return null
}

// 锁定期间只验这一人：距离略放宽（threshold + verifyTolerance），防转头/轻微遮挡抖动误判离场
export function verifyStudent(descriptor, student) {
  if (!student) return false
  const tSq = (FACE_CONFIG.threshold + FACE_CONFIG.verifyTolerance) ** 2
  return bestSquaredToStudent(descriptor, student) < tSq
}

// 人脸质量分 0-100（Run.vue 以 FACE_CONFIG.qualityThreshold 过滤“脸小/低置信”的垃圾帧）。
// 本轮保持离散分（100 尺寸/置信都达标 → 75 一项不达标 → 50 两项都不达标）；
// 连续化留到 V2 真机测得画面数据后再调，避免同轮换标尺污染验证信号。
export function faceQuality(face) {
  if (!face) return 0
  let score = 100
  const { width: w, height: h } = face.box
  if (w < 100 || h < 100) score -= 25
  if (face.score < 0.7) score -= 25
  return Math.max(0, score)
}
