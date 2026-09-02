// face-api.js 加载 + 单脸特征 + 比对。库与模型由后端 /face 静态托管。
let loadPromise = null

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

export async function detectOne(faceapi, input) {
  const opts = new faceapi.TinyFaceDetectorOptions({ inputSize: 416 })
  const res = await faceapi.detectSingleFace(input, opts).withFaceLandmarks().withFaceDescriptor()
  return res ? { descriptor: res.descriptor, box: res.detection.box } : null
}

export function euclidean(a, b) {
  let s = 0
  for (let i = 0; i < a.length; i++) { const d = a[i] - b[i]; s += d * d }
  return Math.sqrt(s)
}

// entries: [{ student, embedding: [128] }]；返回 { student, dist } 或 null
export function bestMatch(desc, entries, threshold) {
  let best = null, bestDist = Infinity
  for (const e of entries) {
    const d = euclidean(desc, e.embedding)
    if (d < bestDist) { bestDist = d; best = e }
  }
  if (best && bestDist < threshold) return { student: best.student, dist: bestDist }
  return null
}
