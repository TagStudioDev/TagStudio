# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only

# pyright: reportPrivateUsage=false

from pathlib import Path

from wcmatch import glob

from tagstudio.core.library.ignore import PATH_GLOB_FLAGS, Ignore, ignore_to_glob


def matches(patterns: list[str], path: str) -> bool:
    return glob.compile(ignore_to_glob(patterns), flags=PATH_GLOB_FLAGS).match(path)


def test_ignore_to_glob_does_not_crash_on_negated_root_anchored_pattern():
    """A pattern like "!/keep.txt" (negated + root-anchored) must not raise an error."""
    patterns = ["*.txt", "!/keep_this.txt"]
    glob_patterns = ignore_to_glob(patterns)

    assert matches(patterns, "keep_this.txt") is False
    assert matches(patterns, "sub/keep_this.txt") is True
    assert matches(patterns, "other.txt") is True
    assert glob_patterns


def test_ignore_to_glob_root_anchored_directory_matches_contents():
    """A root-anchored pattern for a directory (e.g. "/Downloads/") must exclude its contents."""
    patterns = ["/Downloads/"]
    assert matches(patterns, "Downloads/file.txt") is True
    assert matches(patterns, "sub/Downloads/file.txt") is False


def test_ignore_to_glob_root_anchored_directory_without_trailing_slash():
    """A root-anchored pattern without a trailing slash still excludes contents."""
    patterns = ["/Downloads"]
    assert matches(patterns, "Downloads") is True
    assert matches(patterns, "Downloads/file.txt") is True
    assert matches(patterns, "sub/Downloads/file.txt") is False


def test_ignore_to_glob_non_rooted_directory_pattern():
    """A bare/non-rooted directory pattern matches at every depth."""
    patterns = ["Dev/"]
    assert matches(patterns, "Dev/file.txt") is True
    assert matches(patterns, "sub/Dev/file.txt") is True
    assert matches(patterns, "Dev") is False
    assert matches(patterns, "SomeDevFile.txt") is False


def test_ignore_to_glob_leading_globstar_matches_zero_directories():
    """ "**/foo" must also match a root-level "foo", not just nested ones.

    NOTE: wcmatch's "**" only matches "one or more" directories while
    gitignore/ripgrep matches "zero or more", which is the target behavior.
    """
    patterns = ["**/foo"]
    assert matches(patterns, "foo") is True
    assert matches(patterns, "a/foo") is True
    assert matches(patterns, "a/b/foo") is True
    assert matches(patterns, "foobar") is False


def test_ignore_to_glob_middle_globstar_matches_zero_directories():
    """ "a/**/b" must also match "a/b"."""
    patterns = ["a/**/b"]
    assert matches(patterns, "a/b") is True
    assert matches(patterns, "a/x/b") is True
    assert matches(patterns, "a/x/y/b") is True
    assert matches(patterns, "a/bx") is False

    assert matches(patterns, "a/b/file.txt") is True
    assert matches(patterns, "a/x/b/file.txt") is True
    assert matches(patterns, "a/x/y/b/file.txt") is True
    assert matches(patterns, "a/bx/file.txt") is False


def test_ignore_to_glob_escaped_special_characters():
    """A backslash before "#" or "!" must escape these characters."""
    assert matches(["\\#hashtag.jpg"], "#hashtag.jpg") is True
    assert matches(["\\#hashtag.jpg"], "hashtag.jpg") is False
    assert matches(["\\!wowee.jpg"], "!wowee.jpg") is True
    assert matches(["\\!wowee.jpg"], "wowee.jpg") is False


def test_ignore_to_glob_output_has_no_duplicates():
    """Output must be deduplicated."""
    glob_patterns = ignore_to_glob(["*.jpg", "Photos/", "**/foo"])
    assert len(glob_patterns) == len(set(glob_patterns))


def test_single_asterisk_does_not_match_slash():
    """A single "*" must not match a single "/".

    fnmatch will still match "*" to a "/", when gitignore and wcmatch.glob will not.
    """
    patterns = ["Images/*.png"]
    assert matches(patterns, "Images/mario.png") is True
    assert matches(patterns, "Images/Mario/cat.png") is False


def test_negation_does_not_extend_to_deeper_subfolder():
    """A negation must not extend into a deeper subfolder its pattern doesn't match."""
    patterns = ["*.jpg", "!Photos/*.jpg", "Photos/Private/*.jpg"]
    assert matches(patterns, "a.jpg") is True
    assert matches(patterns, "Photos/a.jpg") is False
    assert matches(patterns, "Photos/Private/a.jpg") is True


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
