// 浏览器端人脸引擎：onnxruntime-web（WASM 单线程）+ YuNet 检测 + SFace 识别。
// 全流程本地推理，照片不出浏览器；只把 128 维归一化特征上传/比对。
// 纯数学部分在 preprocess.js / yunet.js / align.js，均可脱离浏览器在 Node 里对拍（见 specs §6）。
// 关键设定：检测走 BGR、识别走 RGB —— 这一对反向通道序经 OpenCV 逐位对拍确认，改动前务必重跑对拍。
// 用 '/wasm' 子路径而非包主入口：主入口默认解析到 ort.bundle（含 WebGL/WebGPU EP），
// 会拖进 ort-wasm-simd-threaded.jsep.wasm（27.8 MB）；这里只用 WASM CPU，走 wasm-only 构建，
// 运行时 wasm 降到 13.9 MB，首屏下载少一半。
import * as ort from 'onnxruntime-web/wasm'
import { ALIGN_TEMPLATE, similarityTransform } from './align.js'
import { decodeYunet, INPUT_SIZE } from './yunet.js'
import { letterboxRect, toNchwFloat, l2normalize } from './preprocess.js'

const MODEL_BASE = '/face/models'

export const DETECT_SIZE = INPUT_SIZE   // 640：YuNet 模型固定输入，不可改
export const ALIGN_SIZE = 112           // SFace 标准对齐尺寸
export const SCORE_THRESHOLD = 0.9      // YuNet 检出置信下限
export const NMS_IOU = 0.3

let enginePromise = null

/** 加载两个会话（幂等）。失败会清掉缓存，允许重试。 */
export function loadEngine() {
  if (!enginePromise) {
    // 不设 wasmPaths：Vite 构建时会把 wasm 作为资源发出并注入带 hash 的绝对 URL，
    // 手写 wasmPaths 反而会覆盖它、指向不存在的文件名（曾导致引擎加载失败）。
    // wasm 仍随构建产物自托管在 /assets/ 下，不依赖外网 CDN。
    // 单线程：多线程需要 SharedArrayBuffer，也就需要 COOP/COEP 响应头，部署侧没配
    ort.env.wasm.numThreads = 1
    // 注：建会话时 SFace 会刷几十行 "Initializer ... appears in graph inputs" 警告。
    // 那是 native 层直接输出的，ort.env.logLevel='error' 压不住（实测无效），只能放着。
    enginePromise = Promise.all([
      ort.InferenceSession.create(`${MODEL_BASE}/face_detection_yunet_2023mar.onnx`),
      ort.InferenceSession.create(`${MODEL_BASE}/face_recognition_sface_2021dec.onnx`),
    ]).then(([det, rec]) => ({
      det, rec,
      // 两个模型的输入名不一样：YuNet 是 'input'，SFace 是 'data'。写死 'input' 会让识别直接抛
      // "input 'data' is missing in 'feeds'"，故一律从会话里读，不假设。
      detIn: det.inputNames[0],
      recIn: rec.inputNames[0],
      recOut: rec.outputNames[0],
    }))
      .catch((e) => { enginePromise = null; throw e })
  }
  return enginePromise
}

// ── 画布复用：每帧新建 canvas 会持续触发 GC，故固定两个尺寸常驻 ──
const canvases = new Map()
function getCanvas(size) {
  let c = canvases.get(size)
  if (!c) {
    c = document.createElement('canvas')
    c.width = size
    c.height = size
    c._ctx = c.getContext('2d', { willReadFrequently: true })
    canvases.set(size, c)
  }
  return c
}

function sourceSize(src) {
  return {
    w: src.videoWidth || src.naturalWidth || src.width,
    h: src.videoHeight || src.naturalHeight || src.height,
  }
}

/**
 * 检测画面中所有人脸。
 * @returns {Promise<Array<{x,y,width,height,score,landmarks:number[][]}>>} 坐标已换算回源图分辨率
 */
export async function detect(engine, src) {
  const { w, h } = sourceSize(src)
  const { scale, dx, dy, dw, dh } = letterboxRect(w, h, DETECT_SIZE)
  const ctx = getCanvas(DETECT_SIZE)._ctx
  ctx.fillStyle = '#000'                      // letterbox 补黑边；实测比直接拉伸置信更高、框几何更准
  ctx.fillRect(0, 0, DETECT_SIZE, DETECT_SIZE)
  ctx.drawImage(src, 0, 0, w, h, dx, dy, dw, dh)

  const img = ctx.getImageData(0, 0, DETECT_SIZE, DETECT_SIZE)
  const tensor = new ort.Tensor('float32', toNchwFloat(img.data, DETECT_SIZE, 'bgr'),
    [1, 3, DETECT_SIZE, DETECT_SIZE])
  const out = await engine.det.run({ [engine.detIn]: tensor })
  return decodeYunet(out, SCORE_THRESHOLD, NMS_IOU).map(f => ({
    x: (f.x - dx) / scale,
    y: (f.y - dy) / scale,
    width: f.width / scale,
    height: f.height / scale,
    score: f.score,
    landmarks: f.landmarks.map(([lx, ly]) => [(lx - dx) / scale, (ly - dy) / scale]),
  }))
}

/**
 * 按 5 关键点对齐到 112×112 后提取 128 维特征（已 L2 归一化）。
 * @returns {Promise<Float32Array>} 128 维单位向量
 */
export async function embed(engine, src, landmarks) {
  const m = similarityTransform(landmarks, ALIGN_TEMPLATE)
  const ctx = getCanvas(ALIGN_SIZE)._ctx
  ctx.setTransform(1, 0, 0, 1, 0, 0)
  ctx.clearRect(0, 0, ALIGN_SIZE, ALIGN_SIZE)
  // canvas 的 setTransform(a,b,c,d,e,f) 对应矩阵 [[a,c,e],[b,d,f]]，
  // 而 m = [a, -b, tx, b, a, ty]，故映射为 (m0, m3, m1, m4, m2, m5)
  ctx.setTransform(m[0], m[3], m[1], m[4], m[2], m[5])
  ctx.drawImage(src, 0, 0)
  ctx.setTransform(1, 0, 0, 1, 0, 0)

  const img = ctx.getImageData(0, 0, ALIGN_SIZE, ALIGN_SIZE)
  const tensor = new ort.Tensor('float32', toNchwFloat(img.data, ALIGN_SIZE, 'rgb'),
    [1, 3, ALIGN_SIZE, ALIGN_SIZE])
  const out = await engine.rec.run({ [engine.recIn]: tensor })
  return l2normalize(out[engine.recOut].data)
}

/**
 * 检测 + 取最大脸 + 提特征，一步到位。
 * @param {number} minFaceSize 人脸最小边长（源图坐标），低于此视为太远、特征不可靠
 */
export async function detectAndEmbed(engine, src, minFaceSize) {
  const faces = await detect(engine, src)
  if (!faces.length) return null
  const face = faces.reduce((a, b) => (b.width * b.height > a.width * a.height ? b : a))
  if (face.width < minFaceSize || face.height < minFaceSize) return null
  const descriptor = await embed(engine, src, face.landmarks)
  return {
    descriptor,
    box: { x: face.x, y: face.y, width: face.width, height: face.height },
    score: face.score,
  }
}
