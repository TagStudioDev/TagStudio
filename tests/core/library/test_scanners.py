# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only

# pyright: reportPrivateUsage=false

import os
from pathlib import Path

from tagstudio.core.library.scanners import _scan_with_internal_scanner


def test_scan_finds_normal_files(tmp_path: Path):
    """Normal files are found."""
    (tmp_path / "a.txt").touch()
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "b.txt").touch()

    results = set(_scan_with_internal_scanner(tmp_path, []))
    assert results == {Path("a.txt"), Path("sub/b.txt")}


def test_scan_ignore_directory(tmp_path: Path):
    """An ignored directory ignores the files within it."""
    (tmp_path / "keep.txt").touch()
    (tmp_path / "ignore_dir").mkdir()
    (tmp_path / "ignore_dir" / "skip.txt").touch()

    results = set(_scan_with_internal_scanner(tmp_path, ["ignore_dir"]))
    assert results == {Path("keep.txt")}


def test_scan_follows_symlinked_directory(tmp_path: Path):
    """A non-cyclic symlink directory must be followed."""
    real_target = tmp_path / "original_dir"
    real_target.mkdir()
    (real_target / "photo.jpg").touch()
    os.symlink(real_target, tmp_path / "symlink_dir", target_is_directory=True)

    results = set(_scan_with_internal_scanner(tmp_path, []))
    assert results == {Path("original_dir/photo.jpg"), Path("symlink_dir/photo.jpg")}


def test_scan_stop_infinite_symlink_cycle(tmp_path: Path):
    """A cyclic symlink shouldn't cause an infinite loop, and be truncated."""
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "file.txt").touch()
    os.symlink(tmp_path, tmp_path / "sub" / "loop", target_is_directory=True)

    results = set(_scan_with_internal_scanner(tmp_path, []))
    assert results == {Path("sub/file.txt")}


def test_scan_handles_mutual_symlink_cycle(tmp_path: Path):
    """Two directories symlinking into each other must terminate."""
    # NOTE: Example names are from pnpn packages that triggered this weird case while testing.
    store = tmp_path / "node_modules" / ".pnpm"
    a_real = store / "pkgA@1.0.0" / "node_modules" / "pkgA"
    b_real = store / "pkgB@1.0.0" / "node_modules" / "pkgB"
    a_real.mkdir(parents=True)
    b_real.mkdir(parents=True)
    (a_real / "index.js").touch()
    (b_real / "index.js").touch()
    (a_real / "node_modules").mkdir()
    (b_real / "node_modules").mkdir()
    os.symlink(a_real, tmp_path / "node_modules" / "pkgA", target_is_directory=True)
    os.symlink(b_real, tmp_path / "node_modules" / "pkgB", target_is_directory=True)
    os.symlink(b_real, a_real / "node_modules" / "pkgB", target_is_directory=True)
    os.symlink(a_real, b_real / "node_modules" / "pkgA", target_is_directory=True)

    results = list(_scan_with_internal_scanner(tmp_path, []))
    assert len(results) == 8  # Bounded - matches ripgrep's own count on this fixture
    assert set(results) == {
        Path("node_modules/pkgA/index.js"),
        Path("node_modules/pkgA/node_modules/pkgB/index.js"),
        Path("node_modules/pkgB/index.js"),
        Path("node_modules/pkgB/node_modules/pkgA/index.js"),
        Path("node_modules/.pnpm/pkgA@1.0.0/node_modules/pkgA/index.js"),
        Path("node_modules/.pnpm/pkgA@1.0.0/node_modules/pkgA/node_modules/pkgB/index.js"),
        Path("node_modules/.pnpm/pkgB@1.0.0/node_modules/pkgB/index.js"),
        Path("node_modules/.pnpm/pkgB@1.0.0/node_modules/pkgB/node_modules/pkgA/index.js"),
    }
