import os
import subprocess
import sys
from pathlib import Path

from journal_utils import (
    normalize_input_path,
    prepare_journal_entry,
    update_listing_file,
)

PROJECT_ROOT = Path(__file__).resolve().parent
JOURNALS_ROOT = PROJECT_ROOT / "journals"
RECENT_UPDATES = PROJECT_ROOT / "homepage" / "recent-updates.html"
JOURNAL_PAGE = PROJECT_ROOT / "homepage" / "journal.html"


def open_folder(path: Path) -> None:
    try:
        if sys.platform.startswith("darwin"):
            subprocess.Popen(["open", str(path)])
        elif sys.platform.startswith("win"):
            os.startfile(str(path))  # type: ignore[attr-defined]
        else:
            subprocess.Popen(["xdg-open", str(path)])
    except Exception:
        pass


def main() -> None:
    open_folder(JOURNALS_ROOT)
    raw_input_path = input("请拖拽日志 Markdown 文件到此终端并按回车键: ").strip()
    try:
        md_path = normalize_input_path(raw_input_path)
        result = prepare_journal_entry(md_path, JOURNALS_ROOT, allow_existing=False)
    except Exception as exc:  # noqa: BLE001
        print(f"❌ {exc}")
        return

    try:
        update_listing_file(RECENT_UPDATES, result)
        update_listing_file(JOURNAL_PAGE, result, ensure_container=True)
    except Exception as exc:  # noqa: BLE001
        print(f"⚠️ 无法更新首页：{exc}")

    print(f"✅ 日志《{result.title}》已创建：{result.html_path}")
    if result.warnings:
        for warn in result.warnings:
            print(warn)


if __name__ == "__main__":
    main()

