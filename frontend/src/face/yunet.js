// YuNet 检测头解码 + NMS。
// 公式逐字取自 OpenCV modules/objdetect/src/face_detect.cpp:192-215，
// 已实测与 cv2.FaceDetectorYN 输出逐位一致（框/置信/5 关键点全同）。勿凭直觉改写。
// 注意：本模型 ONNX 输入是**固定 640×640**，喂其它尺寸 onnxruntime 直接报 INVALID_ARGUMENT。

export const INPUT_SIZE = 640          // 模型固定输入边长
export const STRIDES = [8, 16, 32]     // 对应特征图 80²/40²/20²

function iou(a, b) {
  const x1 = Math.max(a.x, b.x)
  const y1 = Math.max(a.y, b.y)
  const x2 = Math.min(a.x + a.width, b.x + b.width)
  const y2 = Math.min(a.y + a.height, b.y + b.height)
  const inter = Math.max(0, x2 - x1) * Math.max(0, y2 - y1)
  if (inter <= 0) return 0
  return inter / (a.width * a.height + b.width * b.height - inter)
}

/** 标准贪心 IoU 抑制：按置信降序保留，抑制与之重叠超阈的其余框。 */
export function nms(faces, iouThreshold) {
  const sorted = faces.slice().sort((p, q) => q.score - p.score)
  const kept = []
  for (const f of sorted) {
    if (kept.every(k => iou(f, k) <= iouThreshold)) kept.push(f)
  }
  return kept
}

/**
 * 解码 YuNet 输出。评分 = sqrt(clamp(cls) * clamp(obj))，框为 exp 参数化。
 * @param {Object} out  ONNX 输出，键为 cls_8/obj_8/bbox_8/kps_8 … 值为 {data: Float32Array}
 * @param {number} scoreThreshold 置信下限
 * @param {number} iouThreshold  NMS 的 IoU 阈值
 * @returns {Array<{x,y,width,height,score,landmarks:number[][]}>} 坐标为 640×640 输入系
 */
export function decodeYunet(out, scoreThreshold, iouThreshold = 0.3) {
  const faces = []
  for (const st of STRIDES) {
    const n = INPUT_SIZE / st                  // 特征图边长
    const cls = out[`cls_${st}`].data
    const obj = out[`obj_${st}`].data
    const bbox = out[`bbox_${st}`].data
    const kps = out[`kps_${st}`].data
    for (let r = 0; r < n; r++) {
      for (let c = 0; c < n; c++) {
        const i = r * n + c
        const score = Math.sqrt(
          Math.min(Math.max(cls[i], 0), 1) * Math.min(Math.max(obj[i], 0), 1))
        if (score < scoreThreshold) continue

        const cx = (c + bbox[i * 4]) * st
        const cy = (r + bbox[i * 4 + 1]) * st
        const w = Math.exp(bbox[i * 4 + 2]) * st
        const h = Math.exp(bbox[i * 4 + 3]) * st

        const landmarks = []
        for (let k = 0; k < 5; k++) {
          landmarks.push([(kps[i * 10 + k * 2] + c) * st, (kps[i * 10 + k * 2 + 1] + r) * st])
        }
        faces.push({ x: cx - w / 2, y: cy - h / 2, width: w, height: h, score, landmarks })
      }
    }
  }
  return nms(faces, iouThreshold)
}
