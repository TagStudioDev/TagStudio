# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only

# pyright: reportPrivateUsage=false

from collections.abc import Iterable
from pathlib import Path

import pytest

from tagstudio.core.constants import IGNORE_NAME, TS_FOLDER_NAME
from tagstudio.core.library.alchemy.library import Library
from tagstudio.core.library.alchemy.models import Entry
from tagstudio.core.library.alchemy.registries.ignored_registry import IgnoredRegistry
from tagstudio.core.library.ignore import (
    Ignore,
    IgnoreMatcher,
    migrate_ext_list,
)
from tagstudio.core.library.scanners import _scan_with_internal_scanner, _scan_with_ripgrep
from tagstudio.core.utils.ripgrep_status import RipgrepStatus


def is_ignored(patterns: list[str], path: str) -> bool:
    return IgnoreMatcher(patterns).is_ignored(path)


def test_negated_root_anchored_pattern():
    """A negated and root-anchored pattern (e.g. "!/keep.txt") only reincludes the root file."""
    patterns = ["*.txt", "!/keep_this.txt"]
    assert is_ignored(patterns, "keep_this.txt") is False
    assert is_ignored(patterns, "sub/keep_this.txt") is True
    assert is_ignored(patterns, "other.txt") is True


def test_root_anchored_directory_ignores_contents():
    """A root-anchored directory pattern (e.g. "/Downloads/") must exclude its contents."""
    patterns = ["/Downloads/"]
    assert is_ignored(patterns, "Downloads/file.txt") is True
    assert is_ignored(patterns, "sub/Downloads/file.txt") is False


def test_root_anchored_pattern_without_trailing_slash():
    """A root-anchored pattern without a trailing slash matches a file or a folder's contents."""
    patterns = ["/Downloads"]
    assert is_ignored(patterns, "Downloads") is True
    assert is_ignored(patterns, "Downloads/file.txt") is True
    assert is_ignored(patterns, "sub/Downloads/file.txt") is False


def test_non_rooted_directory_pattern():
    """A non-rooted directory pattern matches folders at every depth, but never files."""
    patterns = ["Dev/"]
    assert is_ignored(patterns, "Dev/file.txt") is True
    assert is_ignored(patterns, "sub/Dev/file.txt") is True
    assert is_ignored(patterns, "Dev") is False
    assert is_ignored(patterns, "SomeDevFile.txt") is False


def test_leading_globstar_matches_zero_directories():
    """ "**/foo" must also match a root-level "foo", not just nested ones.

    NOTE: wcmatch's "**" only matches "one or more" directories while
    gitignore/ripgrep matches "zero or more", which is the target behavior.
    """
    patterns = ["**/foo"]
    assert is_ignored(patterns, "foo") is True
    assert is_ignored(patterns, "a/foo") is True
    assert is_ignored(patterns, "a/b/foo") is True
    assert is_ignored(patterns, "foobar") is False


def test_middle_globstar_matches_zero_directories():
    """ "a/**/b" must also match "a/b"."""
    patterns = ["a/**/b"]
    assert is_ignored(patterns, "a/b") is True
    assert is_ignored(patterns, "a/x/b") is True
    assert is_ignored(patterns, "a/x/y/b") is True
    assert is_ignored(patterns, "a/bx") is False

    assert is_ignored(patterns, "a/b/file.txt") is True
    assert is_ignored(patterns, "a/x/b/file.txt") is True
    assert is_ignored(patterns, "a/x/y/b/file.txt") is True
    assert is_ignored(patterns, "a/bx/file.txt") is False


def test_escaped_special_characters():
    """A backslash before "#" or "!" must escape these characters."""
    assert is_ignored(["\\#hashtag.jpg"], "#hashtag.jpg") is True
    assert is_ignored(["\\#hashtag.jpg"], "hashtag.jpg") is False
    assert is_ignored(["\\!wowee.jpg"], "!wowee.jpg") is True
    assert is_ignored(["\\!wowee.jpg"], "wowee.jpg") is False


def test_single_asterisk_does_not_match_slash():
    """A single "*" must not match a "/"."""
    patterns = ["Images/*.png"]
    assert is_ignored(patterns, "Images/mario.png") is True
    assert is_ignored(patterns, "Images/Mario/cat.png") is False


def test_ignore_file_preserves_escaped_trailing_space(tmp_path: Path):
    """An escaped trailing space must not be stripped."""
    ts_ignore = tmp_path / ".ts_ignore"
    ts_ignore.write_bytes(b"foo\\ \nbar \n")
    assert Ignore._load_ignore_file(ts_ignore) == ["foo\\ ", "bar"]


def test_ignore_file_preserves_leading_whitespace(tmp_path: Path):
    """Leading whitespace must not be stripped."""
    ts_ignore = tmp_path / ".ts_ignore"
    ts_ignore.write_bytes(b" baz\n")
    assert Ignore._load_ignore_file(ts_ignore) == [" baz"]


def test_ignore_file_strips_crlf_line_ending(tmp_path: Path):
    """A Windows CRLF line ending must not become part of the pattern."""
    ts_ignore = tmp_path / ".ts_ignore"
    ts_ignore.write_bytes(b"qux\r\n")
    assert Ignore._load_ignore_file(ts_ignore) == ["qux"]


def write_ts_ignore(library_dir: Path, content: str) -> None:
    ts_ignore = library_dir / TS_FOLDER_NAME / IGNORE_NAME
    ts_ignore.parent.mkdir(parents=True, exist_ok=True)
    ts_ignore.write_text(content)


def touch(root: Path, paths: Iterable[str]) -> None:
    for path in paths:
        (root / path).parent.mkdir(parents=True, exist_ok=True)
        (root / path).touch()


def test_library_patterns_override_built_in_patterns(tmp_path: Path):
    """A library's own patterns take precedence over the built-in ones.
    Mimics a global `.gitignore`'s behavior."""
    write_ts_ignore(tmp_path, "!.DS_Store\n")
    Ignore.get_patterns(tmp_path)
    assert Ignore.matcher.is_ignored(".DS_Store") is False
    assert Ignore.matcher.is_ignored(".Trashes/a.png") is True


def test_ts_folder_cannot_be_reincluded(tmp_path: Path):
    """Every .TagStudio folder at any depth must stay ignored, even if folders are reincluded."""
    write_ts_ignore(tmp_path, "*\n!*/\n!*.png\n")
    Ignore.get_patterns(tmp_path)
    assert Ignore.matcher.is_ignored(f"{TS_FOLDER_NAME}/x.png") is True
    assert Ignore.matcher.is_ignored(f"sub/{TS_FOLDER_NAME}/x.png") is True
    assert Ignore.matcher.is_ignored("sub/x.png") is False


def test_matcher_resets_for_a_library_without_a_ts_ignore(tmp_path: Path):
    """Opening a library without a .ts_ignore must not keep the previous library's patterns."""
    with_ts_ignore = tmp_path / "with"
    without_ts_ignore = tmp_path / "without"
    write_ts_ignore(with_ts_ignore, "*.png\n")
    without_ts_ignore.mkdir()

    Ignore.get_patterns(with_ts_ignore)
    assert Ignore.matcher.is_ignored("a.png") is True
    Ignore.get_patterns(without_ts_ignore)
    assert Ignore.matcher.is_ignored("a.png") is False


def test_get_patterns_without_updating_state(tmp_path: Path):
    """Getting a library's patterns with update_state=False must leave Ignore.matcher alone."""
    write_ts_ignore(tmp_path, "*.png\n")
    assert "*.png" in Ignore.get_patterns(tmp_path, update_state=False)
    assert Ignore.matcher.is_ignored("a.png") is False


def test_ignored_registry_respects_ignored_folders(library: Library, tmp_path: Path):
    """The ignored registry must agree with the scanners about files inside ignored folders."""
    write_ts_ignore(tmp_path, "*\n!*.png\n")
    Ignore.get_patterns(tmp_path)
    paths = [Path("a.png"), Path("sub/b.png"), Path("sub/c.jpg")]
    ids = library.add_entries([Entry(path=path, fields=[]) for path in paths])

    registry = IgnoredRegistry(library)
    list(registry.refresh_ignored_entries())
    ignored = {entry.path for entry in registry.ignored_entries if entry.id in ids}
    assert ignored == {Path("sub/b.png"), Path("sub/c.jpg")}


def test_migrated_extension_include_list_keeps_nested_files(tmp_path: Path):
    """An extension include list must keep matching files in subfolders after migrating."""
    write_ts_ignore(tmp_path, migrate_ext_list([".png"], is_exclude_list=False))
    matcher = IgnoreMatcher(Ignore.get_patterns(tmp_path, update_state=False))
    assert matcher.is_ignored("a.png") is False
    assert matcher.is_ignored("sub/deep/a.png") is False
    assert matcher.is_ignored("sub/deep/a.jpg") is True


# Expected results were generated with `git ls-files --others --exclude-standard`
GITIGNORE_TREE = {
    "a.png",
    "a.jpg",
    ".hidden.png",
    "sub/b.png",
    "sub/b.jpg",
    "sub/deep/c.png",
    "sub/deep/c.txt",
    "Photos/x.jpg",
    "Photos/Private/y.jpg",
    "build/out.o",
    "src/build/gen.o",
    "src/main.c",
    "docs/build",
    "#hash.txt",
    "!bang.txt",
    "keep/k.png",
    "keep/k.txt",
    "a/b",
    "a/x/b",
    "a/x/y/b/z.txt",
}
GITIGNORE_CASES: list[tuple[list[str], set[str]]] = [
    (["*", "!*.png"], GITIGNORE_TREE - {"a.png", ".hidden.png"}),
    (
        ["*", "!*/", "!*.png"],
        GITIGNORE_TREE - {"a.png", ".hidden.png", "sub/b.png", "sub/deep/c.png", "keep/k.png"},
    ),
    (["*", "!*/"], GITIGNORE_TREE),
    (["*", "!keep/", "!keep/**"], GITIGNORE_TREE - {"keep/k.png", "keep/k.txt"}),
    (
        ["*.jpg", "!Photos/*.jpg", "Photos/Private/*.jpg"],
        {"a.jpg", "sub/b.jpg", "Photos/Private/y.jpg"},
    ),
    (
        ["*.png", "!a.png", "a.png"],
        {"a.png", ".hidden.png", "sub/b.png", "sub/deep/c.png", "keep/k.png"},
    ),
    (["*.png", "a.png", "!a.png"], {".hidden.png", "sub/b.png", "sub/deep/c.png", "keep/k.png"}),
    (["Photos/", "!Photos/x.jpg"], {"Photos/x.jpg", "Photos/Private/y.jpg"}),
    (["*.o", "!src/**/*.o"], {"build/out.o"}),
    (["build/"], {"build/out.o", "src/build/gen.o"}),
    (["/build/"], {"build/out.o"}),
    (["build"], {"build/out.o", "src/build/gen.o", "docs/build"}),
    (["sub/**"], {"sub/b.png", "sub/b.jpg", "sub/deep/c.png", "sub/deep/c.txt"}),
    (["sub/*"], {"sub/b.png", "sub/b.jpg", "sub/deep/c.png", "sub/deep/c.txt"}),
    (["sub/*/"], {"sub/deep/c.png", "sub/deep/c.txt"}),
    (["**/deep"], {"sub/deep/c.png", "sub/deep/c.txt"}),
    (["**/b"], {"a/b", "a/x/b", "a/x/y/b/z.txt"}),
    (["a/**/b"], {"a/b", "a/x/b", "a/x/y/b/z.txt"}),
    (["/a.png", "!/a.png"], set()),
    (["\\#hash.txt", "\\!bang.txt"], {"#hash.txt", "!bang.txt"}),
    ([".*"], {".hidden.png"}),
    (["**"], GITIGNORE_TREE),
    (["*/"], GITIGNORE_TREE - {"a.png", "a.jpg", ".hidden.png", "#hash.txt", "!bang.txt"}),
    (["?.png"], {"a.png", "sub/b.png", "sub/deep/c.png", "keep/k.png"}),
    (["[ab].*"], {"a.png", "a.jpg", "sub/b.png", "sub/b.jpg"}),
    (["./a.png"], set()),
]


def scanned_files(paths: list[Path]) -> set[str]:
    return {path.as_posix() for path in paths if path.parts[0] != TS_FOLDER_NAME}


@pytest.mark.parametrize(("patterns", "ignored"), GITIGNORE_CASES)
def test_matcher_follows_gitignore(patterns: list[str], ignored: set[str]):
    """The ignore matcher must ignore exactly the same files as a .gitignore would."""
    matcher = IgnoreMatcher(patterns)
    assert {path for path in GITIGNORE_TREE if matcher.is_ignored(path)} == ignored


@pytest.mark.parametrize(("patterns", "ignored"), GITIGNORE_CASES)
def test_internal_scanner_follows_gitignore(tmp_path: Path, patterns: list[str], ignored: set[str]):
    """The internal scanner must skip exactly the same files as a .gitignore would."""
    touch(tmp_path, GITIGNORE_TREE)
    scanned = scanned_files(list(_scan_with_internal_scanner(tmp_path, patterns)))
    assert scanned == GITIGNORE_TREE - ignored


@pytest.mark.skipif(RipgrepStatus.which() is None, reason="ripgrep isn't installed")
@pytest.mark.parametrize(("patterns", "ignored"), GITIGNORE_CASES)
def test_ripgrep_scanner_follows_gitignore(tmp_path: Path, patterns: list[str], ignored: set[str]):
    """The ripgrep scanner must skip exactly the same files as a .gitignore would."""
    touch(tmp_path, GITIGNORE_TREE)
    scanned = scanned_files(list(_scan_with_ripgrep(tmp_path, patterns)))
    assert scanned == GITIGNORE_TREE - ignored
