#!/usr/bin/env python3
from __future__ import annotations

import argparse

from orchestrator_common import ensure_workspace_scaffold, resolve_state_root, resolve_workspace_root


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Initialize the long-lived my-team workspace scaffold.")
    parser.add_argument("--workspace", help="Workspace root. Defaults to a workspace inferred from the current directory or state root.")
    parser.add_argument("--state-root", help="Optional orchestrator-state path to record in USER_CONTEXT.md")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite bootstrap files if they already exist.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    state_root = resolve_state_root(args.state_root) if args.state_root else None
    workspace_root = resolve_workspace_root(args.workspace, state_root=state_root)
    paths = ensure_workspace_scaffold(workspace_root, state_root=state_root, overwrite=args.overwrite)

    print(f"Bootstrapped workspace at {workspace_root}")
    print(f"Core files: {paths['team']}, {paths['memory']}, {paths['user_context']}, {paths['inbox']}, {paths['current_session']}")
    print(f"Roles directory: {paths['roles_dir']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
