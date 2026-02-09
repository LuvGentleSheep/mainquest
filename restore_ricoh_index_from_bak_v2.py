from pathlib import Path


ROOT = Path(__file__).resolve().parent
HTML_PATH = ROOT / "ricoh_generator" / "index.html"
BAK_V2_PATH = ROOT / "ricoh_generator" / "index.bak_v2"


def main() -> None:
    if not BAK_V2_PATH.exists():
        raise SystemExit("找不到 ricoh_generator/index.bak_v2，无法恢复。")

    # 先把当前 index.html 再备份一份，防止后悔
    current_backup = HTML_PATH.with_suffix(".html.restore_backup")
    current_backup.write_text(HTML_PATH.read_text(encoding="utf-8"), encoding="utf-8")

    # 用 bak_v2 覆盖当前 index.html
    html_text = BAK_V2_PATH.read_text(encoding="utf-8")
    HTML_PATH.write_text(html_text, encoding="utf-8")

    print("已将 ricoh_generator/index.html 恢复为 index.bak_v2 版本（并备份当前版本为 index.html.restore_backup）。")


if __name__ == "__main__":
    main()

