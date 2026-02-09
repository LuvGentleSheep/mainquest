from pathlib import Path


HTML_PATH = Path("ricoh_generator/index.html")


def main() -> None:
    text = HTML_PATH.read_text(encoding="utf-8")

    # 原始 h1 样式块
    h1_old = '''        h1 {
            font-weight: 300;
            letter-spacing: 2px;
            color: var(--accent-color);
            margin-bottom: 30px;
            text-transform: uppercase;
            font-size: 1.2rem;
        }'''

    # 悬浮在屏幕顶部中间的标题样式
    h1_new = '''        h1 {
            position: fixed;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            z-index: 10;

            font-weight: 300;
            letter-spacing: 2px;
            color: var(--accent-color);
            text-transform: uppercase;
            font-size: 1.2rem;
            margin: 0;
        }'''

    if h1_old not in text:
        raise RuntimeError("未找到原始 h1 样式块，脚本没有进行修改。")

    text = text.replace(h1_old, h1_new, 1)
    HTML_PATH.write_text(text, encoding="utf-8")
    print("已更新 h1：标题现在固定悬浮在屏幕顶部中央。")


if __name__ == "__main__":
    main()

