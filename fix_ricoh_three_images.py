import re
from pathlib import Path


HTML_PATH = Path("ricoh_generator/index.html")


def main() -> None:
    text = HTML_PATH.read_text(encoding="utf-8")

    # 1. 提取原始 MASK_SRC 行
    m = re.search(
        r'const\s+MASK_SRC\s*=\s*"data:image/png;base64,[^"\n]*";',
        text,
    )
    if not m:
        raise RuntimeError("找不到 MASK_SRC 行，请确认 index.html。")
    mask_src_line = m.group(0)

    # 2. 替换 CSS：bg-layer 加 transition 做滑入动画
    css_old = '''        /* === 预览层分离：全屏背景层 + 相机层 === */
        #bg-layer {
            position: fixed;
            inset: 0;
            z-index: 0;
            background-color: var(--bg-color);
            background-position: center;
            background-repeat: no-repeat;
            background-size: cover; /* 始终铺满各种比例的屏幕，多余部分裁掉 */
        }

        #camera-layer {
            position: fixed;
            inset: 0;
            z-index: 1;
            display: flex;
            align-items: center;
            justify-content: center;
            pointer-events: none; /* 不挡住按钮点击（按钮有更高 z-index） */
        }

        #camera-layer canvas {
            display: block;
            width: min(80vw, 80vh * 3 / 2); /* 相机随窗口缩放但保持 3:2，不出屏幕边界 */
            height: auto;
        }'''

    css_new = '''        /* === 预览层分离：全屏背景层 + 相机层 === */
        #bg-layer {
            position: fixed;
            inset: 0;
            z-index: 0;
            background-color: var(--bg-color);
            background-position: center;
            background-repeat: no-repeat;
            background-size: cover;
            /* 滑入动画：默认在屏幕下方，通过 JS 切换 class 触发 */
            transform: translateY(100%);
            transition: transform 0.7s cubic-bezier(0.33, 1, 0.68, 1);
        }

        #bg-layer.bg-visible {
            transform: translateY(0);
        }

        #bg-layer.bg-no-transition {
            transition: none;
        }

        #camera-layer {
            position: fixed;
            inset: 0;
            z-index: 1;
            display: flex;
            align-items: center;
            justify-content: center;
            pointer-events: none;
        }

        #camera-layer canvas {
            display: block;
            max-width: 80vw;
            max-height: 80vh;
            width: auto;
            height: auto;
        }'''

    if css_old in text:
        text = text.replace(css_old, css_new, 1)
    else:
        raise RuntimeError("未找到原始预览层 CSS 块。")

    # 3. 替换整个 <script>...</script>
    script_pattern = re.compile(r'<script>.*?</script>', re.DOTALL)

    script_new = f'''<script>
        const canvas = document.getElementById('mainCanvas');
        const ctx = canvas.getContext('2d');
        const imageLoader = document.getElementById('imageLoader');
        const downloadBtn = document.getElementById('downloadBtn');
        const backgroundBtn = document.getElementById('backgroundBtn');
        const bgLayer = document.getElementById('bg-layer');

        {mask_src_line}

        const maskImg = new Image();

        let mainImg = null;
        let currentImgDataUrl = null;
        let backgroundMode = 0; // 0: 无; 1: #262626; 2: 当前图做背景

        // 主图淡入动画
        let fadeStart = null;
        let fadeAlpha = 1;
        const FADE_DURATION = 500;

        // 遮罩内部真正显示照片的窗口（基于原始遮罩坐标）
        const innerX = 190;
        const innerY = 400;
        const innerH = 1040;
        const innerW = innerH * (3 / 2);

        // 遮罩加载完成后：canvas 尺寸 = 遮罩原始尺寸（只画相机）
        maskImg.onload = function () {{
            canvas.width = maskImg.width;
            canvas.height = maskImg.height;
            draw();
        }};
        maskImg.src = MASK_SRC;

        // 选图：只影响主图 + 淡入动画
        imageLoader.addEventListener('change', (e) => {{
            const file = e.target.files[0];
            if (!file) return;

            const reader = new FileReader();
            reader.onload = (event) => {{
                currentImgDataUrl = event.target.result;
                const img = new Image();
                img.onload = () => {{
                    mainImg = img;
                    fadeAlpha = 0;
                    fadeStart = performance.now();
                    requestAnimationFrame(animate);
                    // 如果当前是背景图模式，同步更新预览背景
                    if (backgroundMode === 2) {{
                        bgLayer.style.backgroundImage = `url(${{currentImgDataUrl}})`;
                    }}
                }};
                img.src = event.target.result;
            }};
            reader.readAsDataURL(file);
        }});

        // 背景按钮：无 → #262626 → 当前图 → 无 ...
        backgroundBtn.addEventListener('click', () => {{
            backgroundMode = (backgroundMode + 1) % 3;
            updateBackgroundUI();
            updateBgLayer();
        }});

        function updateBackgroundUI() {{
            if (backgroundMode === 0) {{
                backgroundBtn.textContent = '背景：无';
            }} else if (backgroundMode === 1) {{
                backgroundBtn.textContent = '背景：#262626';
            }} else {{
                backgroundBtn.textContent = '背景：当前图';
            }}
        }}

        // 控制 bg-layer 的预览背景（CSS transition 做滑入动画）
        function updateBgLayer() {{
            if (backgroundMode === 0) {{
                // 无背景：立即隐藏（不做动画，直接移走）
                bgLayer.classList.add('bg-no-transition');
                bgLayer.classList.remove('bg-visible');
                bgLayer.style.backgroundColor = 'transparent';
                bgLayer.style.backgroundImage = 'none';
                // 下一帧恢复 transition，为下次滑入做准备
                requestAnimationFrame(() => bgLayer.classList.remove('bg-no-transition'));
            }} else if (backgroundMode === 1) {{
                // 纯色 #262626：从下方滑入
                bgLayer.classList.remove('bg-no-transition');
                bgLayer.style.backgroundColor = '#262626';
                bgLayer.style.backgroundImage = 'none';
                bgLayer.classList.remove('bg-visible');
                requestAnimationFrame(() => {{
                    requestAnimationFrame(() => bgLayer.classList.add('bg-visible'));
                }});
            }} else if (backgroundMode === 2) {{
                // 当前图做背景：从下方滑入
                bgLayer.classList.remove('bg-no-transition');
                bgLayer.style.backgroundColor = '#000';
                if (currentImgDataUrl) {{
                    bgLayer.style.backgroundImage = `url(${{currentImgDataUrl}})`;
                }}
                bgLayer.classList.remove('bg-visible');
                requestAnimationFrame(() => {{
                    requestAnimationFrame(() => bgLayer.classList.add('bg-visible'));
                }});
            }}
        }}

        function easeOutCubic(t) {{
            return 1 - Math.pow(1 - t, 3);
        }}

        // 动画循环：只处理主图淡入
        function animate(now) {{
            let needMore = false;

            if (fadeStart !== null) {{
                const t = Math.min(1, (now - fadeStart) / FADE_DURATION);
                fadeAlpha = t;
                if (t < 1) {{
                    needMore = true;
                }} else {{
                    fadeStart = null;
                    fadeAlpha = 1;
                }}
            }}

            draw();

            if (needMore) {{
                requestAnimationFrame(animate);
            }}
        }}

        // 在指定矩形内用 cover 方式画一张图
        function drawImageCoverToRect(img, dx, dy, dWidth, dHeight) {{
            const destRatio = dWidth / dHeight;
            const srcRatio = img.width / img.height;
            let sx, sy, sWidth, sHeight;
            if (srcRatio > destRatio) {{
                sHeight = img.height;
                sWidth = sHeight * destRatio;
                sx = (img.width - sWidth) / 2;
                sy = 0;
            }} else {{
                sWidth = img.width;
                sHeight = sWidth / destRatio;
                sx = 0;
                sy = (img.height - sHeight) / 2;
            }}
            ctx.drawImage(img, sx, sy, sWidth, sHeight, dx, dy, dWidth, dHeight);
        }}

        // 预览绘制：canvas 里只画「相机主图 + 遮罩」，背景由 bg-layer CSS 负责
        function draw() {{
            if (!canvas.width || !canvas.height) return;

            ctx.clearRect(0, 0, canvas.width, canvas.height);

            // 相机内部主图（淡入）
            if (mainImg) {{
                ctx.save();
                ctx.imageSmoothingEnabled = false;
                ctx.globalAlpha = fadeAlpha;
                drawImageCoverToRect(mainImg, innerX, innerY, innerW, innerH);
                ctx.restore();
            }}

            // 遮罩
            ctx.drawImage(maskImg, 0, 0);
        }}

        // 导出：合成「背景 + 相机主图 + 遮罩」到一个标准 3:2 的 offscreen canvas
        downloadBtn.addEventListener('click', () => {{
            const camW = maskImg.width;
            const camH = maskImg.height;
            const bgH = camH * 5 / 3;
            const bgW = bgH * 3 / 2;
            const camX = (bgW - camW) / 2;
            const camY = (bgH - camH) / 2;

            const offscreen = document.createElement('canvas');
            offscreen.width = bgW;
            offscreen.height = bgH;
            const octx = offscreen.getContext('2d');

            // 底层：背景
            if (backgroundMode === 1) {{
                octx.fillStyle = '#262626';
                octx.fillRect(0, 0, bgW, bgH);
            }} else if (backgroundMode === 2 && mainImg) {{
                const scale = Math.max(bgW / mainImg.width, bgH / mainImg.height);
                const w = mainImg.width * scale;
                const h = mainImg.height * scale;
                const x = (bgW - w) / 2;
                const y = (bgH - h) / 2;
                octx.drawImage(mainImg, x, y, w, h);
            }}
            // backgroundMode === 0：透明底

            // 中间层：相机主图
            if (mainImg) {{
                const destRatio = innerW / innerH;
                const srcRatio = mainImg.width / mainImg.height;
                let sx, sy, sW, sH;
                if (srcRatio > destRatio) {{
                    sH = mainImg.height;
                    sW = sH * destRatio;
                    sx = (mainImg.width - sW) / 2;
                    sy = 0;
                }} else {{
                    sW = mainImg.width;
                    sH = sW / destRatio;
                    sx = 0;
                    sy = (mainImg.height - sH) / 2;
                }}
                octx.drawImage(mainImg, sx, sy, sW, sH,
                    camX + innerX, camY + innerY, innerW, innerH);
            }}

            // 最上层：遮罩
            octx.drawImage(maskImg, camX, camY, camW, camH);

            const link = document.createElement('a');
            link.download = 'ricoh-gr-rendering.png';
            link.href = offscreen.toDataURL('image/png');
            link.click();
        }});

        updateBackgroundUI();
    </script>'''

    text, n = script_pattern.subn(script_new, text, count=1)
    if n == 0:
        raise RuntimeError("没有找到 <script>...</script> 区块。")

    # 备份并写回
    backup = HTML_PATH.with_suffix(".three_img_bak")
    backup.write_text(text, encoding="utf-8")
    HTML_PATH.write_text(text, encoding="utf-8")
    print("已修复：预览时 canvas 只画「主图+遮罩」两层，"
          "背景由 bg-layer CSS 全屏展示（带滑入动画），"
          "导出时合成标准 3:2 带背景图。")


if __name__ == "__main__":
    main()
