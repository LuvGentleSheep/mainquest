from pathlib import Path


ROOT = Path(__file__).resolve().parent
HTML_PATH = ROOT / "ricoh_generator" / "index.html"
LAYERS_BAK_PATH = ROOT / "ricoh_generator" / "index.layers_bak"


def main() -> None:
    if not LAYERS_BAK_PATH.exists():
        raise SystemExit("找不到 ricoh_generator/index.layers_bak，无法只撤销“背景/相机分离”的更新。")

    # 先把当前 index.html 再备份一份，防止后悔
    current_backup = HTML_PATH.with_suffix(".html.restore_layers_backup")
    current_backup.write_text(HTML_PATH.read_text(encoding="utf-8"), encoding="utf-8")

    # 用 index.layers_bak 覆盖当前 index.html
    html_text = LAYERS_BAK_PATH.read_text(encoding="utf-8")
    HTML_PATH.write_text(html_text, encoding="utf-8")

    print("已将 ricoh_generator/index.html 恢复为 index.layers_bak 版本（只撤销分离背景/相机那次更新，"
          "并备份当前版本为 index.html.restore_layers_backup）。")


if __name__ == "__main__":
    main()

