# 模式 4 导出顶区虚化：技术说明（减色带）

本文记录「照片背景 + 上半虚化」在**导出 PNG** 时顶区模糊的实现思路、管线与可调参数，便于后续维护或改版。

## 1. 背景与问题

- **预览**：使用 DOM（如 `filter: blur`）由浏览器合成器绘制，像素密度接近屏幕，观感通常较柔和。
- **导出**：在**高分辨率 Canvas** 上生成位图，再经 **8 bit/通道** 写入 PNG。连续渐变被量化成 256 级台阶时，暗部斜率小的区域容易出现**可见色带（banding）**。
- **额外因素**：若在 **sRGB 编码的数值**上直接做空间平均（等价于许多 `CanvasRenderingContext2D.filter` / 部分 SVG 模糊路径），并不等价于对**线性光强**做模糊，暗部更容易出现**假轮廓**。

因此导出需要一条与「屏幕 CSS 模糊」不必逐像素一致、但在**物理上更合理**且**对 8 bit 量化更友好**的专用路径。

## 2. 设计目标

| 目标 | 说明 |
|------|------|
| 全浏览器统一 | 不再分支 Safari SVG `feGaussianBlur` / `ctx.filter` 等易不一致或易出带的组合。 |
| 色彩正确性 | 模糊在线性 RGB（光强域）进行，再转回 sRGB。 |
| 性能可控 | 可分离的盒式模糊 + 前缀和，单轮 **O(宽高)**；工作分辨率可上限。 |
| 减轻量化台阶 | 回写 8 bit 前加入**轻微抖动**，将误差扩散为噪点而非规则条纹。 |

## 3. 数据流概览

实现集中在 `index.html` 内联脚本（无单独模块文件）。

```
源 Canvas (big，含 padding，全尺寸)
    → 缩放到工作分辨率 (maxWork 约束长边，双线性采样)
    → getImageData → 每像素 RGB 转线性 (Float32 ×3)
    → 盒式模糊：水平 + 竖直，重复 3 轮（近似 Gaussian）
    → 线性 → sRGB 字节 + 抖动 → putImageData
    → 高质量 drawImage 放大回原 (w,h)
    → 作为顶条模糊层贴回导出 offscreen
```

与预览仍通过 `getMode4BlurPx()` 共享**同一套 `exportBlur` 基准**（见下节），保证模糊半径语义一致；**像素级算法**与 CSS 预览不同属预期。

## 4. 与预览的半径对齐

`getMode4BlurPx(camHOverride)`（约 `MODE4_BLUR_FRAC_CAMH = 0.056`）：

- **`exportBlur`**：`max(12, round(camH * 0.056))`，导出顶条合成用 `blurPx`。
- **`previewBlur`**：按导出整图高度与视口高度比例，把同一物理语义缩放到屏幕 CSS `px`。

导出函数 `blurExportMode4TopStrip(big, blurPx)` 接收的即为 **`exportBlur`**（与遮罩高度 `camH` 绑定）。

## 5. 色彩空间：sRGB ↔ 线性

- **`srgbByteToLinear(c)`**：8 bit 通道 → 线性 `[0,1]`，使用标准 sRGB EOTF 分段公式。
- **`linearToSrgbByte(lin)`**：线性 clamp 到 `[0,1]` → OETF → **0–255 浮点**（再经抖动与 `round` 落回整数）。

模糊仅对 **R/G/B 三通道**在 `Float32Array` 中交错存储（每像素 3  float），**不参与 alpha 的卷积**；写回 `ImageData` 时将 alpha 置为 255。

## 6. 模糊核：可分离盒式 + 多轮

- **`boxBlurHLinear` / `boxBlurVLinear`**：对每一行或每一列，用**前缀和**在 **O(n)** 内完成半径 `rad` 的盒式平均；边界为**镜像式截断**（窗口 `[x-r, x+r]` 与画布求交）。
- **半径**：`rad = max(1, round(blurPx * sc * 0.48))`，再限制为 `min(rad, 96, floor(min(sw,sh)/2) - 1)`，避免核过大或越界无意义。
- **轮数**：固定 **3 次**「水平盒 + 竖直盒」串联；多次盒式模糊在视觉上接近 **Gaussian**（经典近似）。

复杂度量级约为 **O(sw × sh × 轮数 × 2)**，与核半径无关（半径只影响前缀和差分的区间宽度）。

## 7. 工作分辨率与放大

- **`maxWork = 1920`**：`sc = min(1, maxWork / max(w,h))`，工作画布 `sw×sh`。
- 缩小：`drawImage` + `imageSmoothingQuality = 'high'`。
- 模糊与量化在 `sw×sh` 上完成。
- 放大：新建与源同尺寸的 `out` Canvas，再次 `drawImage` 将工作画布拉回原尺寸。

在极高位图上先降维再模糊，有利于**控制耗时与内存**；略损高频细节，但对「大尺度虚化」通常可接受。若需更锐的过渡，可提高 `maxWork`（代价为时间与内存）。

## 8. 抖动量化（deband）

线性域结果经 `linearToSrgbByte` 得到浮点 sRGB 强度后，对每个通道加上：

`(Math.random() - 0.5) * dith`，当前 **`dith = 0.75`**，再 `round` 并 clamp 到 `[0,255]`。

作用是将**系统性台阶**转为**类噪声**，人眼对低频带的敏感度高于对细微颗粒。若觉得颗粒感偏重，可略减 `dith`；若仍偶发带纹，可略增或改为有序抖动（未实现，可后续迭代）。

## 9. 导出集成点

模式 4 分支中：在 `big` 上完成 `drawImageCover2xZoom` 等内容后，执行：

```js
const blurCanvas = blurExportMode4TopStrip(big, blurPx);
octx.drawImage(blurCanvas, pad, pad, outW, topH, 0, 0, outW, topH);
```

不再使用：

- `isLikelyAppleSafari` / `canvasBlurFilterExportWorks` / `useSvgBlurForMode4Export`
- `blurCanvasViaSvgGaussian`（SVG 内嵌 PNG + `feGaussianBlur`）
- 纯 `ctx.filter = 'blur(...)'` 的导出路径

## 10. 建议调参表

| 符号 / 位置 | 含义 | 调大效果 | 调小效果 |
|-------------|------|----------|----------|
| `maxWork`（默认 1920） | 工作画布长边上界 | 更细、更慢、更占内存 | 更快、略糊 |
| `blurPx * sc * 0.48` 中的 `0.48` | 导出核半径与 CSS `blur` 的经验比例 | 更虚 | 更实 |
| `rad` 上限 `96` | 核半径硬顶 | — | 极大图时虚化上限 |
| `it < 3`（三轮 H+V） | 接近 Gaussian 的程度 | 更柔和、更慢 | 更接近方盒、略快 |
| `dith`（默认 0.75） | 随机抖动幅度 | 带更轻、噪更明显 | 更干净、带可能略现 |

## 11. Service Worker 缓存

修改 `index.html` 后若线上仍像旧逻辑，检查 `sw.js` 中 **`CACHE_NAME`** 是否已递增，并引导用户硬刷新或跳过等待新 SW，避免缓存旧脚本。

## 12. 局限说明

- 源图若为 **8 bit 且暗部信息极少**，任何单帧导出都无法从信息论上「恢复」丢失的连续灰阶；本方案是**减轻** banding 的工程手段，而非魔法。
- 导出与 **CSS 预览**在采样、分辨率、合成时机上仍可能略有视觉差，属正常；以导出文件为准调参即可。

---

*文档版本与实现对应：仓库内 `blurExportMode4TopStrip` 及 `srgbByteToLinear` / `boxBlur*` 系列函数。*
