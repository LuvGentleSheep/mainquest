#!/usr/bin/env python3
"""用当前目录的 mask.png 更新 index.html 里的 mask base64。"""
import base64
import re
from pathlib import Path

DIR = Path(__file__).resolve().parent
MASK_PNG = DIR / "mask.png"
INDEX_HTML = DIR / "index.html"

def main():
    if not MASK_PNG.exists():
        print(f"未找到 {MASK_PNG}")
        return 1
    if not INDEX_HTML.exists():
        print(f"未找到 {INDEX_HTML}")
        return 1

    b64 = base64.b64encode(MASK_PNG.read_bytes()).decode("ascii")
    content = INDEX_HTML.read_text(encoding="utf-8")

    # 替换已有的 data:image/png;base64,xxx
    pattern = r'(const MASK_SRC = "data:image/png;base64,)[A-Za-z0-9+/=]+(";)'
    if not re.search(pattern, content):
        print("index.html 中未找到 MASK_SRC 的 base64 模式，请检查文件。")
        return 1

    new_content = re.sub(pattern, r'\g<1>' + b64 + r'\g<2>', content, count=1)
    INDEX_HTML.write_text(new_content, encoding="utf-8")
    print("已用 mask.png 更新 index.html 中的 mask。")
    return 0

if __name__ == "__main__":
    exit(main())
