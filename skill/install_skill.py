#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path


RECOMMENDED_SKILL_NAME = "my-team"
PACKAGE_ITEMS = [
    "README.md",
    "SKILL.md",
    "install_skill.py",
    "install_copilot.py",
    "references",
    "scripts",
    "tests",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Install this skill package from the source workspace into the user's Codex skills directory."
    )
    parser.add_argument(
        "--codex-home",
        default=os.environ.get("CODEX_HOME") or str(Path.home() / ".codex"),
        help="Target CODEX_HOME directory. Defaults to $CODEX_HOME or ~/.codex",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite the destination directory if it already exists.",
    )
    return parser


def copy_item(src: Path, dest: Path) -> None:
    if src.is_dir():
        shutil.copytree(src, dest)
    else:
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)


def main() -> int:
    args = build_parser().parse_args()
    source_root = Path(__file__).resolve().parent
    codex_home = Path(args.codex_home).expanduser().absolute()
    target_dir = codex_home / "skills" / RECOMMENDED_SKILL_NAME

    if target_dir.exists():
        if not args.force:
            raise SystemExit(f"Destination already exists: {target_dir}. Re-run with --force to overwrite.")
        shutil.rmtree(target_dir)

    target_dir.mkdir(parents=True, exist_ok=True)

    for item_name in PACKAGE_ITEMS:
        copy_item(source_root / item_name, target_dir / item_name)

    print(f"Source workspace remains at: {source_root}")
    print("Installed package contents: README.md, SKILL.md, install_skill.py, references/, scripts/, tests/")
    print(f"Installed skill to user directory: {target_dir}")
    print(f"Recommended invocation: Use [${RECOMMENDED_SKILL_NAME}]({target_dir / 'SKILL.md'}) ...")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
