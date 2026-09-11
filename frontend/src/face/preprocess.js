// 引擎的纯数学部分：不碰 DOM、不碰 onnxruntime，因此可在 Node 里直接跑对拍测试。
// 与 browser 端共用同一份代码，避免「测的是另一份实现」这种假验证。

/**
 * 等比缩放居中补边的目标矩形。整数取整规则须与 Python 侧一致，否则对拍会有 1px 漂移。
 * @returns {{scale:number, dx:number, dy:number, dw:number, dh:number}}
 */
export function letterboxRect(w, h, size) {
  const scale = Math.min(size / w, size / h)
  const dw = Math.round(w * scale)
  const dh = Math.round(h * scale)
  const dx = Math.floor((size - dw) / 2)
  const dy = Math.floor((size - dh) / 2)
  return { scale, dx, dy, dw, dh }
}

/**
 * RGBA 像素 → NCHW float32（0-255，不减均值）。
 * @param {Uint8ClampedArray|Uint8Array} rgba 长度须为 size*size*4
 * @param {'bgr'|'rgb'} channels YuNet 用 bgr、SFace 用 rgb —— 这一对反向设定是关键，勿统一
 */
export function toNchwFloat(rgba, size, channels) {
  const order = channels === 'bgr' ? [2, 1, 0] : [0, 1, 2]
  const n = size * size
  const out = new Float32Array(3 * n)
  for (let i = 0; i < n; i++) {
    const p = i * 4
    out[i] = rgba[p + order[0]]
    out[n + i] = rgba[p + order[1]]
    out[2 * n + i] = rgba[p + order[2]]
  }
  return out
}

/** L2 归一化：SFace 原始输出范数≈10.4，归一化后点积才等于余弦相似度。 */
export function l2normalize(vec) {
  let sum = 0
  for (let i = 0; i < vec.length; i++) sum += vec[i] * vec[i]
  const norm = Math.sqrt(sum) || 1
  const out = new Float32Array(vec.length)
  for (let i = 0; i < vec.length; i++) out[i] = vec[i] / norm
  return out
}

/** 余弦相似度：两侧各自归一化后点积。 */
export function cosine(a, b) {
  let dot = 0, na = 0, nb = 0
  for (let i = 0; i < a.length; i++) {
    dot += a[i] * b[i]
    na += a[i] * a[i]
    nb += b[i] * b[i]
  }
  const denom = Math.sqrt(na) * Math.sqrt(nb)
  return denom ? dot / denom : 0
}
