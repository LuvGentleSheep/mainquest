import re
from pathlib import Path


HTML_PATH = Path("ricoh_generator/index.html")


def main() -> None:
    text = HTML_PATH.read_text(encoding="utf-8")

    # 1. 在 h1 和 canvas 之间插入 bg-layer 与 camera-layer，使预览层分离
    html_block_old = '''        <h1>RICOH GR Image Processor</h1>
        
        <div id="canvas-wrapper">
            <canvas id="mainCanvas"></canvas>
        </div>'''

    html_block_new = '''        <h1>RICOH GR Image Processor</h1>
        
        <!-- 全屏背景层，用于预览时铺满屏幕 -->
        <div id="bg-layer"></div>

        <!-- 相机层：只负责显示相机画面，居中缩放 -->
        <div id="camera-layer">
            <canvas id="mainCanvas"></canvas>
        </div>'''

    if html_block_old in text:
        text = text.replace(html_block_old, html_block_new, 1)
    elif "id=\"bg-layer\"" not in text:
        raise RuntimeError("未找到原始 h1 + canvas-wrapper 结构，且尚未插入 bg-layer。请检查 HTML 结构。")

    # 2. 在样式结尾追加预览分离相关的 CSS
    style_insert = '''
        /* === 预览层分离：全屏背景层 + 相机层 === */
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
        }
'''

    # 把这段 CSS 插到 </style> 之前（如果还没插入过）
    if "#bg-layer {" not in text:
        text = text.replace("    </style>", style_insert + "\n    </style>", 1)

    # 3. JS：增加 bgLayer 引用和 currentImgDataUrl，用于同步预览背景
    # 3.1 在脚本顶部加入 bgLayer / currentImgDataUrl
    js_header_old = '''        const canvas = document.getElementById('mainCanvas');
        const ctx = canvas.getContext('2d');
        const imageLoader = document.getElementById('imageLoader');
        const downloadBtn = document.getElementById('downloadBtn');
        const backgroundBtn = document.getElementById('backgroundBtn');'''

    js_header_new = '''        const canvas = document.getElementById('mainCanvas');
        const ctx = canvas.getContext('2d');
        const imageLoader = document.getElementById('imageLoader');
        const downloadBtn = document.getElementById('downloadBtn');
        const backgroundBtn = document.getElementById('backgroundBtn');
        const bgLayer = document.getElementById('bg-layer');'''

    if js_header_old in text:
        text = text.replace(js_header_old, js_header_new, 1)

    # 3.2 声明 currentImgDataUrl
    state_old = '''        const maskImg = new Image();

        let mainImg = null;        // 相机内部当前这张图
        let backgroundMode = 0;    // 0: 无; 1: #262626; 2: 当前图做背景'''

    state_new = '''        const maskImg = new Image();

        let mainImg = null;        // 相机内部当前这张图
        let currentImgDataUrl = null; // 预览用 dataURL，用于 bg-layer
        let backgroundMode = 0;    // 0: 无; 1: #262626; 2: 当前图做背景'''

    if state_old in text:
        text = text.replace(state_old, state_new, 1)

    # 3.3 在 imageLoader 回调中保存 dataURL
    loader_old = '''        imageLoader.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (!file) return;

            const reader = new FileReader();
            reader.onload = (event) => {
                const img = new Image();
                img.onload = () => {
                    mainImg = img;
                    // 每次换图都从 0 → 1 做淡入
                    fadeAlpha = 0;
                    fadeStart = performance.now();
                    requestAnimationFrame(animate);
                };
                img.src = event.target.result;
            };
            reader.readAsDataURL(file);
        });'''

    loader_new = '''        imageLoader.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (!file) return;

            const reader = new FileReader();
            reader.onload = (event) => {
                currentImgDataUrl = event.target.result; // 用于预览背景
                const img = new Image();
                img.onload = () => {
                    mainImg = img;
                    // 每次换图都从 0 → 1 做淡入
                    fadeAlpha = 0;
                    fadeStart = performance.now();
                    requestAnimationFrame(animate);
                };
                img.src = event.target.result;
            };
            reader.readAsDataURL(file);
        });'''

    if loader_old in text:
        text = text.replace(loader_old, loader_new, 1)

    # 3.4 在 draw() 中同步 bgLayer 的预览背景，而不影响 canvas 导出内容
    draw_sig = "        // 三层：背景(透明 / #262626 / 当前图) → 主图 → 遮罩\n        function draw() {"
    if draw_sig in text and "bgLayer" in text:
        # 在 draw() 开头加入 bgLayer 的样式更新逻辑
        draw_prefix = '''        // 三层：背景(透明 / #262626 / 当前图) → 主图 → 遮罩
        function draw() {
            if (!canvas.width || !canvas.height) return;

            // 预览层背景：通过 bg-layer 控制全屏背景，不影响导出
            if (bgLayer) {
                if (backgroundMode === 0) {
                    bgLayer.style.backgroundColor = 'transparent';
                    bgLayer.style.backgroundImage = 'none';
                } else if (backgroundMode === 1) {
                    bgLayer.style.backgroundColor = '#262626';
                    bgLayer.style.backgroundImage = 'none';
                } else if (backgroundMode === 2 && currentImgDataUrl) {
                    bgLayer.style.backgroundColor = '#000';
                    bgLayer.style.backgroundImage = `url(${currentImgDataUrl})`;
                }
            }
'''
        # 原来的 draw 开头是:
        # function draw() {
        #     if (!canvas.width || !canvas.height) return;
        # 我们用新的前缀整段替换掉那部分
        text = text.replace(
            "        // 三层：背景(透明 / #262626 / 当前图) → 主图 → 遮罩\n        function draw() {\n            if (!canvas.width || !canvas.height) return;\n",
            draw_prefix,
            1,
        )

    # 写回文件并备份
    backup_path = HTML_PATH.with_suffix(".layers_bak")
    backup_path.write_text(text, encoding="utf-8")
    HTML_PATH.write_text(text, encoding="utf-8")
    print("已完成预览层分离：bg-layer 全屏背景 + camera-layer 相机画面，导出仍使用标准化 3:2 画布。")


if __name__ == "__main__":
    main()

