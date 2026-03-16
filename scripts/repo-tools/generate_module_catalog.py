from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class ModuleInfo:
    name: str
    type: str
    platform: str
    status: str
    owner: str
    version: str
    path: Path
    tags: list[str]
    instruments: list[str]


def _as_list(x: Any) -> list[str]:
    if x is None:
        return []
    if isinstance(x, list):
        return [str(i) for i in x]
    return [str(x)]


def load_metadata(meta_path: Path) -> ModuleInfo:
    raw = yaml.safe_load(meta_path.read_text(encoding="utf-8")) or {}

    return ModuleInfo(
        name=str(raw.get("name", meta_path.parent.name)),
        type=str(raw.get("type", "unknown")),
        platform=str(raw.get("platform", "unknown")),
        status=str(raw.get("status", "unknown")),
        owner=str(raw.get("owner", "")),
        version=str(raw.get("version", "")),
        path=meta_path.parent,
        tags=_as_list(raw.get("tags")),
        instruments=_as_list(raw.get("instruments")),
    )


def find_modules(repo_root: Path) -> list[ModuleInfo]:
    metas = list(repo_root.glob("platforms/**/metadata.yaml")) + list(
        repo_root.glob("templates/**/metadata.yaml")
    )
    modules: list[ModuleInfo] = []
    for mp in metas:
        try:
            m = load_metadata(mp)
            # Ensure paths in the catalog are repo-relative (portable links)
            rel_path = mp.parent.relative_to(repo_root)
            modules.append(
                ModuleInfo(
                    name=m.name,
                    type=m.type,
                    platform=m.platform,
                    status=m.status,
                    owner=m.owner,
                    version=m.version,
                    path=rel_path,
                    tags=m.tags,
                    instruments=m.instruments,
                )
            )
        except Exception as e:
            raise RuntimeError(f"Failed to parse {mp}: {e}") from e
    modules.sort(key=lambda m: (m.platform, m.type, m.name))
    return modules


def render_markdown(repo_root: Path, mods: list[ModuleInfo]) -> str:
    lines: list[str] = []
    lines.append("# Module Catalog")
    lines.append("")
    lines.append("> Auto-generated from `metadata.yaml`. Do not edit manually.")
    lines.append("")

    if not mods:
        lines.append("No modules found.")
        lines.append("")
        return "\n".join(lines)

    # Summary counts
    from collections import Counter

    c_platform = Counter(m.platform for m in mods)
    lines.append("## Summary")
    lines.append("")
    for k, v in sorted(c_platform.items()):
        lines.append(f"- **{k}**: {v}")
    lines.append("")

    lines.append("## Modules")
    lines.append("")
    lines.append("| Name | Type | Platform | Status | Version | Owner | Path | Tags | Instruments |")
    lines.append("|---|---|---|---|---|---|---|---|---|")
    for m in mods:
        tags = ", ".join(m.tags)
        inst = ", ".join(m.instruments)
        rel = m.path.as_posix()
        # Use link if README exists
        readme = repo_root / m.path / "README.md"
        name = m.name
        if readme.exists():
            name = f"[{name}]({rel}/README.md)"
        lines.append(
            f"| {name} | {m.type} | {m.platform} | {m.status} | {m.version} | {m.owner} | `{rel}` | {tags} | {inst} |"
        )

    lines.append("")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", default=Path(__file__).resolve().parents[2])
    ap.add_argument("--out", default="MODULES.md")
    args = ap.parse_args()

    repo_root = Path(args.repo_root).resolve()
    out_path = (repo_root / args.out).resolve()

    mods = find_modules(repo_root)
    md = render_markdown(repo_root, mods)
    out_path.write_text(md, encoding="utf-8")
    print(f"Wrote {out_path} ({len(mods)} modules)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
