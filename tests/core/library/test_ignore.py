# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only

import wcmatch.fnmatch as fnmatch

from tagstudio.core.library.ignore import PATH_GLOB_FLAGS, ignore_to_glob


def matches(patterns: list[str], path: str) -> bool:
    return fnmatch.compile(ignore_to_glob(patterns), PATH_GLOB_FLAGS).match(path)


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
