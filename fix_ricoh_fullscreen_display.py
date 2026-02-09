from pathlib import Path


HTML_PATH = Path("ricoh_generator/index.html")


def main() -> None:
    text = HTML_PATH.read_text(encoding="utf-8")

    # 1. 调整 #canvas-wrapper：充满视口，居中显示 canvas，多余部分裁掉
    wrapper_old = '''        #canvas-wrapper {
            position: relative;
            width: 100vw;
            height: 100vh;
            line-height: 0;
            overflow: hidden;
            background: var(--bg-color);
        }'''

    wrapper_new = '''        #canvas-wrapper {
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            line-height: 0;
            overflow: hidden;
            background: var(--bg-color);
            display: flex;
            align-items: center;
            justify-content: center;
        }'''

    if wrapper_old in text:
        text = text.replace(wrapper_old, wrapper_new)

    # 2. 恢复 canvas 比例：只控制高度，宽度自适应，保持 3:2，不再拉伸
    canvas_old = '''        canvas {
            display: block;
            width: 100%;
            height: 100%;
        }'''

    canvas_new = '''        canvas {
            display: block;
            height: 100vh;   /* 高度总是铺满屏幕 */
            width: auto;     /* 宽度按 3:2 比例自动缩放，水平多余部分裁掉 */
        }'''

    if canvas_old in text:
        text = text.replace(canvas_old, canvas_new)

    # 3. 还原 body，使其不再用 flex 撑开，避免再次影响比例
    body_old_flex = '''        body {
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

    body_simple = '''        body {
            background-color: var(--bg-color);
            color: var(--text-color);
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            margin: 0;
            min-height: 100vh;
        }'''

    if body_old_flex in text:
        text = text.replace(body_old_flex, body_simple)

    HTML_PATH.write_text(text, encoding="utf-8")
    print("已更新显示：canvas 全屏显示但保持 3:2 比例，输出尺寸不受影响。")


if __name__ == "__main__":
    main()

