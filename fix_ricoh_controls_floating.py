from pathlib import Path


HTML_PATH = Path("ricoh_generator/index.html")


def main() -> None:
    text = HTML_PATH.read_text(encoding="utf-8")

    # 原来的 .controls 样式（脚本只替换第一处定义）
    controls_old = '''        .controls {
            margin-top: 30px;
            background: var(--panel-color);
            padding: 20px 40px;
            border-radius: 4px;
            display: flex;
            gap: 20px;
            align-items: center;
        }'''

    controls_new = '''        .controls {
            position: fixed;
            left: 50%;
            bottom: 30px;
            transform: translateX(-50%);
            z-index: 10;

            background: var(--panel-color);
            padding: 12px 24px;
            border-radius: 999px;

            display: flex;
            gap: 16px;
            align-items: center;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.5);
        }'''

    if controls_old not in text:
        raise RuntimeError("未找到原始 .controls 样式块，脚本没有进行任何修改。")

    text = text.replace(controls_old, controls_new, 1)

    HTML_PATH.write_text(text, encoding="utf-8")
    print("已更新 .controls：按钮现在固定悬浮在屏幕底部中央。")


if __name__ == "__main__":
    main()

