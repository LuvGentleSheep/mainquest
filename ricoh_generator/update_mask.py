#!/usr/bin/env python3
"""用当前目录的 mask.png 更新 mask_data.js 里的 mask base64。"""
import base64
from pathlib import Path

DIR = Path(__file__).resolve().parent
MASK_PNG = DIR / "mask.png"
MASK_JS = DIR / "mask_data.js"

def main():
    if not MASK_PNG.exists():
        print(f"未找到 {MASK_PNG}")
        return 1

    b64 = base64.b64encode(MASK_PNG.read_bytes()).decode("ascii")

    MASK_JS.write_text(
        "// 遮罩图 base64 数据（由 update_mask.py 生成，勿手动编辑）\n"
        f'const MASK_SRC = "data:image/png;base64,{b64}";\n',
        encoding="utf-8",
    )
    print(f"已用 mask.png 更新 {MASK_JS.name}（{len(b64)} 字符）。")
    return 0

if __name__ == "__main__":
    exit(main())
