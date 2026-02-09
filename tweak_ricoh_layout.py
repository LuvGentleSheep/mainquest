import re
from pathlib import Path


HTML_PATH = Path("ricoh_generator/index.html")


def main() -> None:
    text = HTML_PATH.read_text(encoding="utf-8")

    # 1. 调整 body / .container / #canvas-wrapper / canvas 的样式，让背景铺满整个视口
    body_old = '''        body {
            background-color: var(--bg-color);
            color: var(--text-color);
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            margin: 0;
        }'''

    body_new = '''        body {
            background-color: var(--bg-color);
            color: var(--text-color);
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            margin: 0;
            min-height: 100vh;
        }'''

    if body_old in text:
        text = text.replace(body_old, body_new)

    container_old = '''        .container {
            text-align: center;
            padding: 20px;
        }'''

    container_new = '''        .container {
            text-align: center;
            padding: 20px;
            width: 100vw;
            height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
        }'''

    if container_old in text:
        text = text.replace(container_old, container_new)

    wrapper_old = '''        #canvas-wrapper {
            position: relative;
            width: 100%;
            max-width: 1000px;
            line-height: 0;
            overflow: hidden;
            background: var(--bg-color);
        }'''

    wrapper_new = '''        #canvas-wrapper {
            position: relative;
            width: 100vw;
            height: 100vh;
            line-height: 0;
            overflow: hidden;
            background: var(--bg-color);
        }'''

    if wrapper_old in text:
        text = text.replace(wrapper_old, wrapper_new)

    canvas_old = '''        canvas {
            display: block;
            width: 100%;
            height: auto;
        }'''

    canvas_new = '''        canvas {
            display: block;
            width: 100%;
            height: 100%;
        }'''

    if canvas_old in text:
        text = text.replace(canvas_old, canvas_new)

    # 2. 修复相机内部图片出界：只在遮罩内部窗口区域绘制
    cam_line = '        // 相机在大背景中的位置和尺寸\n        let camX = 0, camY = 0, camW = 0, camH = 0;'
    if cam_line in text:
        cam_with_inner = '''        // 相机在大背景中的位置和尺寸
        let camX = 0, camY = 0, camW = 0, camH = 0;
        // 遮罩内部真正显示照片的窗口（基于原始遮罩坐标）
        const innerX = 190;
        const innerY = 400;
        const innerH = 1040;
        const innerW = innerH * (3 / 2);'''
        text = text.replace(cam_line, cam_with_inner)

    # 调整主图绘制调用，只在 inner 窗口内绘制
    old_draw_main = '                drawImageCoverToRect(mainImg, camX, camY, camW, camH);'
    new_draw_main = '                drawImageCoverToRect(mainImg, camX + innerX, camY + innerY, innerW, innerH);'
    if old_draw_main in text:
        text = text.replace(old_draw_main, new_draw_main)

    # 写回文件（备份一份）
    backup_path = HTML_PATH.with_suffix(".layout_bak")
    backup_path.write_text(text, encoding="utf-8")
    HTML_PATH.write_text(text, encoding="utf-8")
    print("已更新布局：全屏背景 + 相机内窗口裁切，并备份为 index.layout_bak")


if __name__ == "__main__":
    main()

