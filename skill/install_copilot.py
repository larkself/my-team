#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
from pathlib import Path


RECOMMENDED_SKILL_NAME = "my-team"
PACKAGE_ITEMS = [
    "README.md",
    "SKILL.md",
    "install_copilot.py",
    "install_skill.py",
    "references",
    "scripts",
    "tests",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Install this skill package into the GitHub Copilot skills directory for VS Code."
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--personal",
        action="store_true",
        default=True,
        help="Install as a personal skill to ~/.copilot/skills/ (default).",
    )
    group.add_argument(
        "--project",
        type=str,
        metavar="PROJECT_ROOT",
        help="Install as a project skill to <PROJECT_ROOT>/.github/skills/.",
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

    if args.project:
        project_root = Path(args.project).expanduser().absolute()
        if not project_root.is_dir():
            raise SystemExit(f"Project root does not exist: {project_root}")
        target_dir = project_root / ".github" / "skills" / RECOMMENDED_SKILL_NAME
        scope = "project"
    else:
        target_dir = Path.home() / ".copilot" / "skills" / RECOMMENDED_SKILL_NAME
        scope = "personal"

    if target_dir.exists():
        if not args.force:
            raise SystemExit(f"Destination already exists: {target_dir}. Re-run with --force to overwrite.")
        shutil.rmtree(target_dir)

    target_dir.mkdir(parents=True, exist_ok=True)

    for item_name in PACKAGE_ITEMS:
        src = source_root / item_name
        if src.exists():
            copy_item(src, target_dir / item_name)

    print(f"Source workspace remains at: {source_root}")
    print(f"Installed as {scope} skill to: {target_dir}")
    print(f"Trigger in Copilot chat: /my-team or mention my-team in conversation")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
