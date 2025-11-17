from __future__ import annotations

import html
import json
import os
import re
import shlex
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple
from urllib.parse import urlparse, unquote

IMAGE_TOKEN_PATTERN = re.compile(r'!\[[^\]]*\]\(([^)]+)\)|!\[\[([^\]]+)\]\]')
BANNER_PATTERN = re.compile(r'^\s*banner::\s*(.+)$', re.IGNORECASE | re.MULTILINE)
ICON_PATTERN = re.compile(r'^\s*icon::\s*(.+)$', re.IGNORECASE | re.MULTILINE)
CODE_FENCE_PATTERN = re.compile(r'^```')
SUMMARY_EXCLUDE_PREFIXES = ("banner::", "icon::")
LOGSEQ_META_PATTERN = re.compile(r'^\s*logseq\.[^:]+::', re.IGNORECASE)
COLLAPSE_PATTERN = re.compile(r'^\s*collapsed::\s*true\s*$', re.IGNORECASE)
CAPTION_DECOR_PATTERN = re.compile(r'\[\[#caption\]\]==.*?==', re.IGNORECASE)
CAPTION_LINE_PATTERN = re.compile(r'^\s*!\[[^\]]*\]\([^)]+\)\s*\[\[#caption\]\]==.*?==\s*$', re.IGNORECASE)
MAX_SUMMARY_LENGTH = 220
META_FILENAME = "journal_meta.json"


@dataclass
class JournalBuildResult:
    entry_name: str
    title: str
    summary: str
    icon: str | None
    timestamp: str
    entry_dir: Path
    html_path: Path
    md_destination: Path
    meta_path: Path
    hero_homepage_src: str
    hero_entry_src: str
    link_href: str
    md_filename: str
    image_map: Dict[str, str]
    warnings: List[str]


def normalize_input_path(raw_path: str) -> Path:
    if not raw_path:
        raise ValueError("未接收到路径，请重新拖拽 Markdown 文件。")
    processed = raw_path.strip()
    if processed.startswith(("'", '"')) and processed.endswith(("'", '"')):
        processed = processed[1:-1]
    if os.name != "nt":
        processed = _unescape_posix_path(processed)
    processed = os.path.expanduser(processed)
    path = Path(processed).expanduser()
    if not path.exists():
        raise FileNotFoundError(f"找不到文件：{path}")
    return path.resolve()


def _unescape_posix_path(raw: str) -> str:
    try:
        parts = shlex.split(raw, posix=True)
        if parts:
            return parts[0]
    except ValueError:
        pass
    return raw.replace("\\ ", " ")


def prepare_journal_entry(
    md_source_path: Path,
    journals_root: Path,
    *,
    allow_existing: bool,
) -> JournalBuildResult:
    md_source_path = md_source_path.expanduser().resolve()
    if not md_source_path.exists():
        raise FileNotFoundError(f"Markdown 文件不存在：{md_source_path}")

    journals_root.mkdir(parents=True, exist_ok=True)
    entry_name = md_source_path.stem
    entry_dir = journals_root / entry_name
    html_path = entry_dir / f"{entry_name}.html"
    md_destination = entry_dir / f"{entry_name}.md"
    assets_dir = entry_dir / "assets"
    meta_path = entry_dir / META_FILENAME

    if entry_dir.exists() and not allow_existing:
        raise FileExistsError(f"日志《{entry_name}》已存在，若需更新请运行 更新日志.py。")
    if not entry_dir.exists() and allow_existing:
        raise FileNotFoundError(f"未找到日志《{entry_name}》，请先运行 新建日志.py。")

    entry_dir.mkdir(parents=True, exist_ok=True)
    fallback_assets = assets_dir if assets_dir.exists() else None
    temp_assets = entry_dir / "__assets_build"
    if temp_assets.exists():
        shutil.rmtree(temp_assets)
    temp_assets.mkdir(parents=True, exist_ok=True)

    existing_map = _load_existing_meta(meta_path)

    md_text = _read_markdown(md_source_path)
    banner_path = _extract_metadata_value(BANNER_PATTERN, md_text)
    icon_value = _extract_metadata_value(ICON_PATTERN, md_text)
    summary = _extract_summary(md_text)

    md_parent = md_source_path.parent
    image_refs = _extract_image_references(md_text)
    image_map, warnings, used_names = _copy_referenced_assets(
        image_refs,
        md_parent,
        temp_assets,
        fallback_dir=fallback_assets,
        existing_map=existing_map,
    )

    banner_cleaned = _clean_image_reference(banner_path) if banner_path else None
    banner_source = None
    if banner_cleaned:
        banner_source = _ensure_asset_for_reference(
            banner_cleaned,
            md_parent,
            temp_assets,
            image_map,
            fallback_dir=fallback_assets,
            existing_map=existing_map,
            warnings=warnings,
            used_names=used_names,
        )

    hero_candidate = banner_source or _first_local_asset(image_refs, image_map)
    hero_entry_src, hero_homepage_src = _compute_hero_sources(
        entry_name, hero_candidate
    )

    timestamp = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S")
    link_href = f"../journals/{entry_name}/{entry_name}.html"

    if md_destination.resolve() != md_source_path:
        shutil.copy2(md_source_path, md_destination)
    result = JournalBuildResult(
        entry_name=entry_name,
        title=entry_name,
        summary=summary,
        icon=icon_value.strip() if icon_value else None,
        timestamp=timestamp,
        entry_dir=entry_dir,
        html_path=html_path,
        md_destination=md_destination,
        meta_path=meta_path,
        hero_homepage_src=hero_homepage_src,
        hero_entry_src=hero_entry_src,
        link_href=link_href,
        md_filename=md_destination.name,
        image_map=image_map,
        warnings=warnings,
    )
    _write_entry_html(result)
    _write_meta_file(result)
    if assets_dir.exists():
        shutil.rmtree(assets_dir)
    temp_assets.rename(assets_dir)
    return result


def format_update_block(ctx: JournalBuildResult) -> str:
    safe_title = html.escape(ctx.title)
    safe_summary = html.escape(ctx.summary)
    block = f"""
    <div class="update-item">
        <div class="update-image">
            <a href="{ctx.link_href}">
                <img class="lazy" data-src="{ctx.hero_homepage_src}" alt="{safe_title} 封面">
                <div class="image-title"></div>
            </a>
        </div>
        <div class="update-content">
            <div class="update-title">{safe_title}</div>
            <div class="update-main clickable">
                <p>{safe_summary}</p>
            </div>
            <div class="update-time">{ctx.timestamp}</div>
        </div>
    </div>
    """
    return block


def update_listing_file(
    html_path: Path,
    ctx: JournalBuildResult,
    *,
    ensure_container: bool = False,
) -> None:
    if not html_path.exists():
        raise FileNotFoundError(f"未找到 {html_path}")
    content = html_path.read_text(encoding="utf-8")
    if ensure_container and '<div class="update-container">' not in content:
        content = _inject_container_shell(content)
    content = _remove_existing_block(content, ctx.link_href)
    marker = '<div class="update-container">'
    idx = content.find(marker)
    if idx == -1:
        raise RuntimeError(f"{html_path} 中缺少 update-container 容器。")
    insert_at = idx + len(marker)
    updated = content[:insert_at] + format_update_block(ctx) + content[insert_at:]
    html_path.write_text(updated, encoding="utf-8")


def _inject_container_shell(content: str) -> str:
    closing = "</section>"
    placeholder = "            <div class=\"update-container\">\n            </div>\n"
    if closing not in content:
        raise RuntimeError("无法在 journal.html 中找到 </section> 以插入容器。")
    return content.replace(
        closing, f"{placeholder}{closing}", 1
    )


def _remove_existing_block(content: str, link_href: str) -> str:
    marker = f'href="{link_href}"'
    target_idx = content.find(marker)
    if target_idx == -1:
        return content
    start = content.rfind('<div class="update-item"', 0, target_idx)
    if start == -1:
        return content
    depth = 0
    pos = start
    length = len(content)
    while pos < length:
        next_open = content.find("<div", pos)
        next_close = content.find("</div>", pos)
        if next_open == -1 and next_close == -1:
            break
        if next_open != -1 and (next_open < next_close or next_close == -1):
            depth += 1
            pos = next_open + 4
            continue
        if next_close != -1:
            depth -= 1
            pos = next_close + len("</div>")
            if depth == 0:
                end = pos
                trimmed = content[:start].rstrip() + "\n" + content[end:].lstrip()
                return trimmed
        else:
            break
    return content


def _read_markdown(md_path: Path) -> str:
    try:
        return md_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return md_path.read_text(encoding="utf-8-sig")


def _extract_metadata_value(pattern: re.Pattern, text: str) -> str | None:
    match = pattern.search(text)
    if not match:
        return None
    value = match.group(1).strip()
    if value.startswith(("'", '"')) and value.endswith(("'", '"')):
        value = value[1:-1]
    return value.strip()


def _extract_image_references(text: str) -> List[str]:
    refs: List[str] = []
    for match in IMAGE_TOKEN_PATTERN.finditer(text):
        ref = match.group(1) or match.group(2)
        if ref:
            refs.append(ref.strip())
    return refs


def _copy_referenced_assets(
    refs: List[str],
    source_dir: Path,
    assets_dir: Path,
    *,
    fallback_dir: Path | None = None,
    existing_map: Dict[str, str] | None = None,
) -> Tuple[Dict[str, str], List[str], Dict[str, str]]:
    image_map: Dict[str, str] = {}
    warnings: List[str] = []
    existing_map = existing_map or {}
    used_names: Dict[str, str] = {}
    fallback_index = _build_fallback_index(fallback_dir)

    for ref in refs:
        cleaned = _clean_image_reference(ref)
        if not cleaned:
            continue
        if cleaned in image_map:
            continue
        if _is_remote_reference(cleaned):
            image_map[cleaned] = cleaned
            base = Path(cleaned).name
            if base and base not in image_map:
                image_map[base] = cleaned
            continue

        src_path = _resolve_reference(cleaned, source_dir)
        if not src_path or not src_path.exists():
            src_path = _lookup_fallback_source(
                cleaned, fallback_dir, existing_map, fallback_index
            )
        if not src_path or not src_path.exists():
            warnings.append(f"⚠️ 无法找到资源：{cleaned}")
            continue

        dest_name = _determine_dest_name(
            cleaned,
            src_path.name,
            used_names,
            existing_map,
        )
        shutil.copy2(src_path, assets_dir / dest_name)
        mapped_value = f"./assets/{dest_name}"
        image_map[cleaned] = mapped_value
        base = src_path.name
        if base not in image_map:
            image_map[base] = mapped_value
    return image_map, warnings, used_names


def _build_fallback_index(fallback_dir: Path | None) -> Dict[str, Path]:
    if not fallback_dir or not fallback_dir.exists():
        return {}
    index: Dict[str, Path] = {}
    for item in fallback_dir.iterdir():
        if item.is_file():
            index[item.name] = item
    return index


def _lookup_fallback_source(
    cleaned: str,
    fallback_dir: Path | None,
    existing_map: Dict[str, str],
    fallback_index: Dict[str, Path],
) -> Path | None:
    if not fallback_dir:
        return None
    existing_target = existing_map.get(cleaned)
    if existing_target:
        candidate = fallback_dir / Path(existing_target).name
        if candidate.exists():
            return candidate
    base = Path(cleaned).name
    if base and base in fallback_index:
        return fallback_index[base]
    return None


def _determine_dest_name(
    cleaned: str,
    suggested_name: str,
    used_names: Dict[str, str],
    existing_map: Dict[str, str],
) -> str:
    mapped = existing_map.get(cleaned)
    if mapped:
        existing_name = Path(mapped).name
        if existing_name:
            return existing_name
    candidate = suggested_name or Path(cleaned).name or "asset"
    stem = Path(candidate).stem or "asset"
    suffix = Path(candidate).suffix
    current_names = set(used_names.values())
    dest_name = candidate
    counter = 1
    while dest_name in current_names:
        dest_name = f"{stem}_{counter}{suffix}"
        counter += 1
    used_names[cleaned] = dest_name
    return dest_name


def _ensure_asset_for_reference(
    cleaned_ref: str,
    source_dir: Path,
    assets_dir: Path,
    image_map: Dict[str, str],
    *,
    fallback_dir: Path | None,
    existing_map: Dict[str, str],
    warnings: List[str],
    used_names: Dict[str, str],
) -> str | None:
    if cleaned_ref in image_map:
        return image_map[cleaned_ref]
    if _is_remote_reference(cleaned_ref):
        image_map[cleaned_ref] = cleaned_ref
        return cleaned_ref

    fallback_index = _build_fallback_index(fallback_dir)
    resolved = _resolve_reference(cleaned_ref, source_dir)
    if not resolved or not resolved.exists():
        resolved = _lookup_fallback_source(
            cleaned_ref, fallback_dir, existing_map, fallback_index
        )
    if not resolved or not resolved.exists():
        warnings.append(f"⚠️ banner 所指向的图片不存在：{cleaned_ref}")
        return None

    dest_name = _determine_dest_name(
        cleaned_ref, resolved.name, used_names, existing_map
    )
    shutil.copy2(resolved, assets_dir / dest_name)
    mapped_value = f"./assets/{dest_name}"
    image_map[cleaned_ref] = mapped_value
    base = resolved.name
    if base not in image_map:
        image_map[base] = mapped_value
    return mapped_value


def _first_local_asset(refs: List[str], image_map: Dict[str, str]) -> str | None:
    for ref in refs:
        cleaned = _clean_image_reference(ref)
        mapped = image_map.get(cleaned)
        if mapped:
            return mapped
    return None


def _compute_hero_sources(entry_name: str, hero_source: str | None) -> Tuple[str, str]:
    if not hero_source:
        return ("../default.jpeg", "../journals/default.jpeg")
    if hero_source.startswith("./assets/"):
        tail = hero_source.replace("./", "", 1)
        homepage_src = f"../journals/{entry_name}/{tail}"
        return (hero_source, homepage_src)
    return (hero_source, hero_source)


def _extract_summary(text: str) -> str:
    paragraphs: List[str] = []
    current: List[str] = []
    in_code_block = False

    def flush_current() -> None:
        nonlocal current
        if current:
            paragraphs.append(" ".join(current))
            current = []

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if CODE_FENCE_PATTERN.match(line):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue
        if not line:
            flush_current()
            continue
        lower = line.lower()
        if any(lower.startswith(prefix) for prefix in SUMMARY_EXCLUDE_PREFIXES):
            continue
        if LOGSEQ_META_PATTERN.match(line) or COLLAPSE_PATTERN.match(line):
            continue
        if CAPTION_LINE_PATTERN.match(line):
            flush_current()
            continue
        if line.startswith("![[") or line.startswith("!["):
            continue
        if line.startswith(("-", "*", "+")):
            flush_current()
            paragraphs.append(line.lstrip("-*+").strip())
            continue
        if line.startswith("#"):
            flush_current()
            paragraphs.append(line.lstrip("#").strip())
            continue
        if line.startswith(">"):
            line = line.lstrip(">").strip()
        current.append(line)

    flush_current()

    for para in paragraphs:
        cleaned = _clean_summary_text(para)
        if cleaned:
            return cleaned
    return "这是一篇新的日志，敬请期待。"


def _clean_summary_text(raw: str) -> str:
    if not raw:
        return ""
    text = re.sub(r'\[\[([^\]|]+)(?:\|([^\]]+))?\]\]', r'\1', raw)
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    text = CAPTION_DECOR_PATTERN.sub("", text)
    text = re.sub(r"[#*_>`~]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return ""
    if len(text) > MAX_SUMMARY_LENGTH:
        text = text[:MAX_SUMMARY_LENGTH].rstrip() + "…"
    return text


def _clean_image_reference(ref: str | None) -> str:
    if not ref:
        return ""
    cleaned = ref.strip().strip("'").strip('"')
    return cleaned.replace("\\", "/")


def _is_remote_reference(ref: str) -> bool:
    lowered = ref.lower()
    return lowered.startswith("http://") or lowered.startswith("https://") or lowered.startswith("data:")


def _resolve_reference(ref: str, base_dir: Path) -> Path | None:
    if ref.startswith("file://"):
        parsed = urlparse(ref)
        return Path(unquote(parsed.path or ""))
    path = Path(ref)
    if path.is_absolute():
        return path
    return (base_dir / path).resolve()


def _write_entry_html(ctx: JournalBuildResult) -> None:
    icon = html.escape(ctx.icon) if ctx.icon else "📓"
    safe_title = html.escape(ctx.title)
    hero_src = html.escape(ctx.hero_entry_src)
    summary_meta = html.escape(ctx.summary)
    image_map_json = json.dumps(ctx.image_map, ensure_ascii=False, indent=2)
    template = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{safe_title}</title>
    <meta name="description" content="{summary_meta}">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            color-scheme: light;
            --bg: #f5f5f5;
            --text: #1a1a1a;
            --card: rgba(255, 255, 255, 0.85);
            --border: rgba(0, 0, 0, 0.08);
            --muted: #5f5f5f;
            --accent: #111;
            --code-bg: rgba(0, 0, 0, 0.05);
            --code-text: #c7254e;
        }}
        @media (prefers-color-scheme: dark) {{
            :root {{
                color-scheme: dark;
                --bg: #050505;
                --text: #f5f5f5;
                --card: rgba(8, 8, 8, 0.85);
                --border: rgba(255, 255, 255, 0.12);
                --muted: #c7c7c7;
                --accent: #fff;
                --code-bg: rgba(255, 255, 255, 0.08);
                --code-text: #ffb4b4;
            }}
        }}
        * {{
            box-sizing: border-box;
        }}
        body {{
            margin: 0;
            min-height: 100vh;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            color: var(--text);
            background: radial-gradient(circle at top, rgba(255,255,255,0.15), transparent), var(--bg);
            padding: 32px 16px 64px;
        }}
        .page-shell {{
            max-width: 840px;
            margin: 0 auto;
            background: var(--card);
            border-radius: 24px;
            border: 1px solid var(--border);
            box-shadow: 0 30px 80px rgba(0,0,0,0.08);
            overflow: hidden;
            backdrop-filter: blur(16px);
        }}
        .entry-header {{
            padding: 32px;
            border-bottom: 1px solid var(--border);
        }}
        .eyebrow {{
            text-transform: uppercase;
            letter-spacing: 0.2em;
            font-size: 12px;
            color: var(--muted);
            margin-bottom: 8px;
        }}
        .title-row {{
            display: flex;
            gap: 16px;
            align-items: center;
        }}
        .icon-badge {{
            width: 56px;
            height: 56px;
            border-radius: 16px;
            background: rgba(0,0,0,0.08);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 28px;
        }}
        .entry-header h1 {{
            margin: 0;
            font-size: 32px;
            line-height: 1.2;
        }}
        .meta {{
            margin-top: 18px;
            color: var(--muted);
            font-size: 14px;
        }}
        .hero {{
            position: relative;
            padding: 0 32px 32px;
        }}
        .hero img {{
            width: 100%;
            border-radius: 18px;
            display: block;
            object-fit: cover;
            max-height: 420px;
        }}
        .markdown-body {{
            padding: 0 32px 48px;
            font-size: 16px;
            line-height: 1.8;
        }}
        .markdown-body h1,
        .markdown-body h2,
        .markdown-body h3,
        .markdown-body h4 {{
            margin-top: 2.5em;
            margin-bottom: 0.8em;
            line-height: 1.3;
        }}
        .markdown-body p {{
            margin: 0 0 1.2em;
        }}
        .markdown-body a {{
            color: var(--accent);
            text-decoration: underline;
        }}
        .markdown-body blockquote {{
            margin: 1.5em 0;
            padding: 1em 1.2em;
            border-left: 3px solid var(--accent);
            background: rgba(0,0,0,0.03);
            border-radius: 0 12px 12px 0;
        }}
        .markdown-body pre {{
            background: var(--code-bg);
            border-radius: 14px;
            padding: 16px;
            overflow: auto;
            font-size: 14px;
        }}
        .markdown-body code {{
            background: var(--code-bg);
            color: var(--code-text);
            padding: 2px 6px;
            border-radius: 6px;
        }}
        .markdown-body table {{
            border-collapse: collapse;
            width: 100%;
            margin-bottom: 1.5em;
        }}
        .markdown-body th,
        .markdown-body td {{
            border: 1px solid var(--border);
            padding: 12px;
            text-align: left;
        }}
        .markdown-body img {{
            max-width: 100%;
            border-radius: 16px;
            border: 1px solid var(--border);
            margin: 1em 0;
        }}
        .markdown-body figure.md-figure {{
            margin: 2.5em auto;
            text-align: center;
        }}
        .markdown-body figure.md-figure img {{
            width: 100%;
            height: auto;
            border-radius: 18px;
            border: 1px solid var(--border);
        }}
        .markdown-body figure.md-figure figcaption {{
            margin-top: 0.8em;
            font-size: 0.95em;
            color: var(--muted);
        }}
        .markdown-body ul {{
            margin: 0 0 1.2em;
            padding-left: 1.5em;
        }}
        .markdown-body .flat-entry {{
            margin: 0 0 1.2em;
        }}
        .markdown-body .flat-entry:last-child {{
            margin-bottom: 0;
        }}
        @media (max-width: 640px) {{
            .entry-header,
            .hero,
            .markdown-body {{
                padding: 24px;
            }}
            .entry-header h1 {{
                font-size: 26px;
            }}
            .title-row {{
                flex-direction: column;
                align-items: flex-start;
            }}
            .icon-badge {{
                width: 48px;
                height: 48px;
                font-size: 24px;
            }}
        }}
    </style>
</head>
<body>
    <div class="page-shell">
        <header class="entry-header">
            <p class="eyebrow">Journal Entry</p>
            <div class="title-row">
                <span class="icon-badge">{icon}</span>
                <h1>{safe_title}</h1>
            </div>
            <p class="meta">最后更新：{ctx.timestamp}</p>
        </header>
        <section class="hero">
            <img src="{hero_src}" alt="{safe_title} hero" loading="lazy" decoding="async">
        </section>
        <main id="journal-body" class="markdown-body"></main>
    </div>
    <script>
        const MD_FILE = "{ctx.md_filename}";
        const IMAGE_MAP = {image_map_json};
    </script>
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <script>
        marked.setOptions({{ gfm: true, breaks: true }});
        const cleanRef = (src) => src.trim().replace(/^['"]|['"]$/g, "").replace(/\\\\/g, "/");
        const remapSrc = (src) => {{
            const cleaned = cleanRef(src);
            if (IMAGE_MAP[cleaned]) {{
                return IMAGE_MAP[cleaned];
            }}
            const fileName = cleaned.split(/[\\\\/]/).pop();
            if (fileName && IMAGE_MAP[fileName]) {{
                return IMAGE_MAP[fileName];
            }}
            return fileName ? `./assets/${{fileName}}` : cleaned;
        }};
        const escapeHtmlAttr = (value = "") => value
            .replace(/&/g, "&amp;")
            .replace(/"/g, "&quot;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;");
        const escapeHtml = (value = "") => value
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;");
        const stripMetaLines = (md) => md
            .split(/\\r?\\n/)
            .filter(line => !/^\\s*(?:banner|icon)::/i.test(line))
            .filter(line => !/^\\s*logseq\\.[^:]+::/i.test(line))
            .filter(line => !/^\\s*collapsed::\\s*true\\s*$/i.test(line))
            .join("\\n");
        const applyCaptionBlocks = (md) => {{
            const pattern = /!\\[([^\\]]*)\\]\\(([^)]+)\\)\\s*\\[\\[#caption\\]\\]==([\\s\\S]*?)==/gi;
            return md.replace(pattern, (_, alt, src, caption) => {{
                const resolved = remapSrc(src);
                const safeAlt = escapeHtmlAttr(alt);
                const safeCaption = escapeHtml(caption.trim());
                return `<figure class="md-figure"><img src="${{resolved}}" alt="${{safeAlt}}" loading="lazy" decoding="async"><figcaption>${{safeCaption}}</figcaption></figure>`;
            }});
        }};
        const normalizeMarkdown = (md) => {{
            const withCaptions = applyCaptionBlocks(md);
            const standard = /!\\[([^\\]]*)\\]\\(([^)]+)\\)/g;
            const embeds = /!\\[\\[([^\\]]+)\\]\\]/g;
            const step1 = withCaptions.replace(standard, (_, alt, src) => `![${{alt}}](${{remapSrc(src)}})`);
            return step1.replace(embeds, (_, src) => `![${{src}}](${{remapSrc(src)}})`);
        }};
        const flattenTopLevelLists = (container) => {{
            const topLists = Array.from(container.children || []).filter(
                node => node.tagName === "UL"
            );
            topLists.forEach(list => {{
                const fragment = document.createDocumentFragment();
                Array.from(list.children || []).forEach(li => {{
                    if (!(li instanceof HTMLElement)) {{
                        return;
                    }}
                    const wrapper = document.createElement("div");
                    wrapper.className = "flat-entry";
                    while (li.firstChild) {{
                        wrapper.appendChild(li.firstChild);
                    }}
                    fragment.appendChild(wrapper);
                }});
                list.replaceWith(fragment);
            }});
        }};
        async function renderMarkdown() {{
            try {{
                const res = await fetch(`./${{MD_FILE}}?t=${{Date.now()}}`);
                const raw = await res.text();
                const cleaned = stripMetaLines(raw);
                const htmlContent = marked.parse(normalizeMarkdown(cleaned));
                const container = document.getElementById("journal-body");
                container.innerHTML = htmlContent;
                flattenTopLevelLists(container);
                container.querySelectorAll("img").forEach(img => {{
                    img.loading = "lazy";
                    img.decoding = "async";
                }});
            }} catch (err) {{
                document.getElementById("journal-body").innerHTML = "<p>无法加载 Markdown 内容，请稍后再试。</p>";
                console.error(err);
            }}
        }}
        renderMarkdown();
    </script>
</body>
</html>
"""
    ctx.html_path.write_text(template, encoding="utf-8")


def _write_meta_file(ctx: JournalBuildResult) -> None:
    meta = {
        "image_map": ctx.image_map,
        "updated_at": ctx.timestamp,
    }
    ctx.meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")


def _load_existing_meta(meta_path: Path) -> Dict[str, str]:
    if not meta_path.exists():
        return {}
    try:
        data = json.loads(meta_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    if isinstance(data, dict):
        stored_map = data.get("image_map", {})
        if isinstance(stored_map, dict):
            return stored_map
    return {}
