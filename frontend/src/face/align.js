// 人脸对齐：5 关键点 → 112×112，SFace/ArcFace 标准模板。
// 模板与变换公式经 OpenCV 金验证（见 docs/superpowers/specs/2026-09-11-face-recognition-sface-design.md §6.2），
// 与 cv2.FaceRecognizerSF.alignCrop 的对齐图像素差 mean=0.00 / max=1，特征余弦 1.00000。勿凭肉眼改动。

// 右眼 / 左眼 / 鼻尖 / 右嘴角 / 左嘴角 —— 顺序与 YuNet 输出一致
export const ALIGN_TEMPLATE = [
  [38.2946, 51.6963],
  [73.5318, 51.5014],
  [56.0252, 71.7366],
  [41.5493, 92.3655],
  [70.7299, 92.2041],
]

/**
 * 求 src → dst 的相似变换（旋转 + 等比缩放 + 平移，4 自由度）闭式最小二乘解。
 * 复平面写法：把点视作复数，最优变换即 (Σ conj(x)·u) / (Σ |x|²)。
 * 无离群点时与 cv2.estimateAffinePartial2D 结果一致（已实测）。
 * @returns {number[]} 2×3 行主序矩阵 [a, -b, tx, b, a, ty]，即 x' = a·x − b·y + tx，y' = b·x + a·y + ty
 */
export function similarityTransform(src, dst) {
  const n = src.length
  let msx = 0, msy = 0, mdx = 0, mdy = 0
  for (let i = 0; i < n; i++) {
    msx += src[i][0]; msy += src[i][1]
    mdx += dst[i][0]; mdy += dst[i][1]
  }
  msx /= n; msy /= n; mdx /= n; mdy /= n

  // 去中心化后，复平面最小二乘：num = Σ (x+iy)‾ · (u+iv)，den = Σ (x²+y²)
  let numRe = 0, numIm = 0, den = 0
  for (let i = 0; i < n; i++) {
    const x = src[i][0] - msx, y = src[i][1] - msy
    const u = dst[i][0] - mdx, v = dst[i][1] - mdy
    numRe += x * u + y * v
    numIm += x * v - y * u
    den += x * x + y * y
  }
  const a = numRe / den
  const b = numIm / den
  return [
    a, -b, mdx - (a * msx - b * msy),
    b, a, mdy - (b * msx + a * msy),
  ]
}
