// 人脸识别适配层：把 face/ 引擎（onnxruntime-web + YuNet + SFace）包成 Run.vue / Students.vue 用的接口。
// 对外函数名与返回结构保持不变，但**度量语义已翻转**：
//   旧 face-api：128 维欧氏距离，越小越像；新 SFace：128 维余弦相似度，**越大越像**。
// 判定阈值/余量只在此处定义，是唯一来源（改这些参数不动特征空间，无需全员重录）。
import { loadEngine, detectAndEmbed } from './face/engine.js'
import { cosine } from './face/preprocess.js'

export const FACE_CONFIG = {
  model: 'sface',            // 特征空间标识，须与 backend/app/routers/faces.py 的 FACE_MODEL 一致
  threshold: 0.45,           // 余弦相似度下限；SFace 官方基准 0.363，实战从严起步，真机标定后再定
  margin: 0.06,              // 第一名须比第二名高出这么多相似度，否则视为不确定
  verifyTolerance: 0.05,     // LOCKED 期间只验一人时放宽的相似度，防转头/轻微遮挡抖动误判离场
  minFaceSize: 80,           // 人脸最小边长（源图坐标），低于此视为太远、特征不可靠
  qualityThreshold: 60,      // faceQuality 低于此 → 视为弱脸/无脸（Run.vue 引用，过滤垃圾帧）
}

/** 加载引擎（幂等）。返回值是不透明的会话句柄，直接透传给 detectOne。 */
export function loadFaceapi() { return loadEngine() }

export async function ensureModels() { await loadEngine() }

/**
 * 检测最清晰的一张脸并提取特征。
 * @returns {Promise<{descriptor: Float32Array, box: {x,y,width,height}, score: number} | null>}
 */
export async function detectOne(engine, input) {
  return detectAndEmbed(engine, input, FACE_CONFIG.minFaceSize)
}

// 单学生与 descriptor 的最高相似度（支持未来多模板）：
//   { embedding: [128] }          当前后端结构
//   { embeddings: [[128], ...] }  未来多模板
function bestSimToStudent(descriptor, student) {
  let templates = []
  if (Array.isArray(student.embeddings)) templates = student.embeddings
  else if (student.embedding) templates = [student.embedding]
  if (!templates.length) return -Infinity
  let best = -Infinity
  for (const temp of templates) {
    const s = cosine(descriptor, temp)
    if (s > best) best = s
  }
  return best
}

export function studentSimilarity(descriptor, student) {
  return bestSimToStudent(descriptor, student)
}

// Top1/Top2 单次扫描（不 sort 全数组）。
// 返回 { best, second, bestSimilarity, secondSimilarity, pass }
export function rankMatches(descriptor, candidates) {
  let best = null, second = null
  let bestSim = -Infinity, secondSim = -Infinity
  for (const student of candidates) {
    const sim = bestSimToStudent(descriptor, student)
    if (sim > bestSim) {
      secondSim = bestSim; second = best
      bestSim = sim; best = student
    } else if (sim > secondSim) {
      secondSim = sim; second = student
    }
  }
  const pass = !!best &&
    bestSim >= FACE_CONFIG.threshold &&
    // 只有一名候选时没有第二名可比，不该被余量条款一票否决
    (second === null || (bestSim - secondSim) >= FACE_CONFIG.margin)
  return { best, second, bestSimilarity: bestSim, secondSimilarity: secondSim, pass }
}

/** 在 candidates 里找最像的一个，相似度 ≥ threshold 才命中。返回 { student, sim } 或 null */
export function bestMatch(descriptor, candidates, threshold = FACE_CONFIG.threshold) {
  let best = null, bestSim = -Infinity
  for (const c of candidates) {
    const sim = bestSimToStudent(descriptor, c)
    if (sim > bestSim) { bestSim = sim; best = c }
  }
  if (best && bestSim >= threshold) return { student: best, sim: bestSim }
  return null
}

// 锁定期间只验这一人：阈值略放宽（相减，因为越大越像），防转头/轻微遮挡抖动误判离场
export function verifyStudent(descriptor, student) {
  if (!student) return false
  return bestSimToStudent(descriptor, student) >= FACE_CONFIG.threshold - FACE_CONFIG.verifyTolerance
}

// 人脸质量分 0-100（Run.vue 以 FACE_CONFIG.qualityThreshold 过滤「脸小/低置信」的垃圾帧）。
// 判据沿用旧版标尺，便于两代引擎的现场表现可比；YuNet 置信普遍高于 face-api 的 tiny detector，
// 故 score 一项几乎不扣分，实际起筛选作用的是尺寸。
export function faceQuality(face) {
  if (!face) return 0
  let score = 100
  const { width: w, height: h } = face.box
  if (w < 100 || h < 100) score -= 25
  if (face.score < 0.7) score -= 25
  return Math.max(0, score)
}
