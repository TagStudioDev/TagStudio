"""Thin wrapper around PyInstaller for TagStudio.

Runs the existing ``tagstudio.spec`` with consistent output locations and
supports toggling the portable build via environment variable.
"""

from __future__ import annotations

import argparse
import os
import platform
import subprocess
import sys
from pathlib import Path

import tomllib


ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_DIST = ROOT / "dist" / "pyinstaller"
DEFAULT_BUILD = ROOT / "build" / "pyinstaller"


def read_version() -> str:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text("utf-8"))
    return pyproject["project"]["version"]


def run_pyinstaller(distpath: Path, workpath: Path, clean: bool, portable: bool) -> Path:
    env = os.environ.copy()
    env["TS_PORTABLE"] = "1" if portable else "0"

    system = platform.system().lower()
    dist_for_platform = distpath / system
    work_for_platform = workpath / system
    dist_for_platform.mkdir(parents=True, exist_ok=True)
    work_for_platform.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "tagstudio.spec",
        "--noconfirm",
        f"--distpath={dist_for_platform}",
        f"--workpath={work_for_platform}",
    ]
    if clean:
        cmd.append("--clean")

    print(f"[build] Running PyInstaller ({'portable' if portable else 'standard'})...")
    subprocess.check_call(cmd, cwd=ROOT, env=env)

    # PyInstaller output name varies by platform/build (exe dir or .app bundle); pick the first produced entry.
    stage_candidates = list(dist_for_platform.glob("*"))
    if not stage_candidates:
        raise RuntimeError(f"No PyInstaller output in {dist_for_platform}")
    stage_dir = stage_candidates[0]
    print(f"[build] Staged at: {stage_dir}")
    return stage_dir


def main() -> None:
    parser = argparse.ArgumentParser(description="Run PyInstaller with TagStudio spec.")
    parser.add_argument(
        "--distpath",
        type=Path,
        default=DEFAULT_DIST,
        help="Output directory for PyInstaller artifacts (per platform subdir will be created).",
    )
    parser.add_argument(
        "--workpath",
        type=Path,
        default=DEFAULT_BUILD,
        help="Work directory for PyInstaller build artifacts (per platform subdir).",
    )
    parser.add_argument("--clean", action="store_true", help="Clean PyInstaller cache before building.")
    parser.add_argument(
        "--portable",
        action="store_true",
        help="Emit a portable build (includes binaries/datas directly).",
    )

    args = parser.parse_args()
    version = read_version()
    print(f"[build] TagStudio {version}")
    run_pyinstaller(args.distpath, args.workpath, args.clean, args.portable)


if __name__ == "__main__":
    main()
