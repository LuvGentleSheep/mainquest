import re
from pathlib import Path


HTML_PATH = Path("ricoh_generator/index.html")


def main() -> None:
    text = HTML_PATH.read_text(encoding="utf-8")

    # 1. 找出并保留原有的 MASK_SRC 行
    m = re.search(
        r'const\s+MASK_SRC\s*=\s*"data:image/png;base64,[^"\n]*";',
        text,
    )
    if not m:
        raise RuntimeError(
            "没有找到 const MASK_SRC = \"data:image/png;base64,...\" 这一行，请先确认 index.html 内容。"
        )
    mask_src_line = m.group(0)

    # 2. 替换第一个 controls 区块
    controls_pattern = re.compile(
        r'<div class="controls">.*?</div>',
        re.DOTALL,
    )
    controls_replacement = '''<div class="controls">
            <label for="imageLoader" class="upload-label">Select Photo (3:2)</label>
            <input type="file" id="imageLoader" accept="image/*">
            <button class="btn" id="backgroundBtn" type="button" title="无 → 纯色 #262626 → 当前图做背景">
                背景：无
            </button>
            <button class="btn" id="downloadBtn">Save Rendering</button>
        </div>'''

    text, n_controls = controls_pattern.subn(controls_replacement, text, count=1)
    if n_controls == 0:
        raise RuntimeError("没有成功替换 <div class=\"controls\"> 区块，请检查 HTML 结构。")

    # 3. 替换整个 <script>...</script> 块，插入新的 3:2 背景 + 动画逻辑
    script_pattern = re.compile(
        r'<script>.*?</script>',
        re.DOTALL,
    )

    script_replacement = f'''<script>
        const canvas = document.getElementById('mainCanvas');
        const ctx = canvas.getContext('2d');
        const imageLoader = document.getElementById('imageLoader');
        const downloadBtn = document.getElementById('downloadBtn');
        const backgroundBtn = document.getElementById('backgroundBtn');

        // 保留原始遮罩的 base64
        {mask_src_line}

        const maskImg = new Image();

        let mainImg = null;        // 相机内部当前这张图
        let backgroundMode = 0;    // 0: 无; 1: #262626; 2: 当前图做背景

        // 主图淡入动画
        let fadeStart = null;
        let fadeAlpha = 1;
        const FADE_DURATION = 500; // ms

        // 背景滑入动画（只给背景层用）
        let bgAnimStart = null;
        let bgShift = 0;
        const BG_ANIM_DURATION = 700; // ms

        // 相机在大背景中的位置和尺寸
        let camX = 0, camY = 0, camW = 0, camH = 0;

        // 遮罩加载完成后：确定「大背景 3:2」和「相机在中间」
        maskImg.onload = function () {{
            camW = maskImg.width;
            camH = maskImg.height;

            // 背景高度 = 相机高度 * 5/3，使相机高度 ≈ 背景高度的 3/5
            const bgH = camH * 5 / 3;
            const bgW = bgH * 3 / 2; // 保持大背景为 3:2

            canvas.width = bgW;
            canvas.height = bgH;

            // 相机（遮罩）居中放在大背景中间
            camX = (bgW - camW) / 2;
            camY = (bgH - camH) / 2;

            draw();
        }};
        maskImg.src = MASK_SRC;

        // 选图：只影响主图 + 淡入动画，不动背景
        imageLoader.addEventListener('change', (e) => {{
            const file = e.target.files[0];
            if (!file) return;

            const reader = new FileReader();
            reader.onload = (event) => {{
                const img = new Image();
                img.onload = () => {{
                    mainImg = img;
                    // 每次换图都从 0 → 1 做淡入
                    fadeAlpha = 0;
                    fadeStart = performance.now();
                    requestAnimationFrame(animate);
                }};
                img.src = event.target.result;
            }};
            reader.readAsDataURL(file);
        }});

        // 背景按钮：无 → #262626 → 当前图 → 无 ...
        backgroundBtn.addEventListener('click', () => {{
            backgroundMode = (backgroundMode + 1) % 3;
            updateBackgroundUI();

            if (backgroundMode === 2 && mainImg) {{
                // 切到「当前图做背景」：背景从下方滑入
                bgShift = canvas.height;
                bgAnimStart = performance.now();
                requestAnimationFrame(animate);
            }} else {{
                // 背景无 / 纯色：不需要动画
                bgAnimStart = null;
                bgShift = 0;
                draw();
            }}
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

        function easeOutCubic(t) {{
            return 1 - Math.pow(1 - t, 3);
        }}

        // 统一动画循环：主图淡入 + 背景滑入，彼此解耦
        function animate(now) {{
            let needMore = false;

            // 主图淡入（相机内部那张）
            if (fadeStart !== null) {{
                const t = Math.min(1, (now - fadeStart) / FADE_DURATION);
                fadeAlpha = t; // 从 0 到 1
                if (t < 1) {{
                    needMore = true;
                }} else {{
                    fadeStart = null;
                    fadeAlpha = 1;
                }}
            }}

            // 背景滑入（只在背景模式为「当前图」时生效）
            if (bgAnimStart !== null) {{
                const t = Math.min(1, (now - bgAnimStart) / BG_ANIM_DURATION);
                const k = easeOutCubic(t);
                bgShift = canvas.height * (1 - k); // 从 height → 0
                if (t < 1) {{
                    needMore = true;
                }} else {{
                    bgAnimStart = null;
                    bgShift = 0;
                }}
            }}

            draw();

            if (needMore) {{
                requestAnimationFrame(animate);
            }}
        }}

        // 在指定矩形内用 cover 方式画一张图（用于相机里的主图）
        function drawImageCoverToRect(img, dx, dy, dWidth, dHeight) {{
            const destRatio = dWidth / dHeight;
            const srcRatio = img.width / img.height;

            let sx, sy, sWidth, sHeight;

            if (srcRatio > destRatio) {{
                // 源图更宽：裁左右
                sHeight = img.height;
                sWidth = sHeight * destRatio;
                sx = (img.width - sWidth) / 2;
                sy = 0;
            }} else {{
                // 源图更高：裁上下
                sWidth = img.width;
                sHeight = sWidth / destRatio;
                sx = 0;
                sy = (img.height - sHeight) / 2;
            }}

            ctx.drawImage(img, sx, sy, sWidth, sHeight, dx, dy, dWidth, dHeight);
        }}

        // 三层：背景(透明 / #262626 / 当前图) → 主图 → 遮罩
        function draw() {{
            if (!canvas.width || !canvas.height) return;

            ctx.clearRect(0, 0, canvas.width, canvas.height);

            // 底层：大 3:2 背景
            if (backgroundMode === 1) {{
                // 纯色 #262626
                ctx.fillStyle = '#262626';
                ctx.fillRect(0, 0, canvas.width, canvas.height);
            }} else if (backgroundMode === 2 && mainImg) {{
                // 当前图做背景：整屏 cover，叠加 bgShift 做滑入
                const scale = Math.max(
                    canvas.width / mainImg.width,
                    canvas.height / mainImg.height
                );
                const w = mainImg.width * scale;
                const h = mainImg.height * scale;
                const x = (canvas.width - w) / 2;
                const baseY = (canvas.height - h) / 2;
                ctx.drawImage(mainImg, x, baseY + bgShift, w, h);
            }}
            // backgroundMode === 0：透明底，不画背景

            // 中间层：相机内部主图（固定在 camX, camY 的区域，淡入，不滑动）
            if (mainImg && camW > 0 && camH > 0) {{
                ctx.save();
                ctx.imageSmoothingEnabled = false;
                ctx.globalAlpha = fadeAlpha;
                drawImageCoverToRect(mainImg, camX, camY, camW, camH);
                ctx.restore();
            }}

            // 最上层：遮罩，相机整体居中放在 camX, camY
            if (camW > 0 && camH > 0) {{
                ctx.drawImage(maskImg, camX, camY, camW, camH);
            }}
        }}

        // 保存当前画布
        downloadBtn.addEventListener('click', () => {{
            const link = document.createElement('a');
            link.download = 'ricoh-gr-rendering.png';
            link.href = canvas.toDataURL('image/png');
            link.click();
        }});

        // 初始化按钮 UI
        updateBackgroundUI();
    </script>'''

    text, n_script = script_pattern.subn(script_replacement, text, count=1)
    if n_script == 0:
        raise RuntimeError("没有找到 <script>...</script> 区块，请检查 index.html 结构。")

    # 4. 备份并写回文件
    backup_path = HTML_PATH.with_suffix(".bak_v2")
    backup_path.write_text(text, encoding="utf-8")
    HTML_PATH.write_text(text, encoding="utf-8")
    print("已成功更新 ricoh_generator/index.html（布局为 3:2 大背景 + 中间相机），并保留原始 MASK_SRC。")


if __name__ == "__main__":
    main()

