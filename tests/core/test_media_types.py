# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: MIT


from pytestqt.exceptions import pytest

from tagstudio.core.media_types import MediaTypes


def test_register_and_contains():
    MediaTypes.register("zzztest.basic", ".zzzfoo", "SEARCH")

    assert MediaTypes.contains("zzztest.basic", ".zzzfoo", "SEARCH")
    assert not MediaTypes.contains("zzztest.basic", ".zzzfoo", "RENDER")


def test_additive_register():
    MediaTypes.register("zzztest.additive", ".zzzfoo", "SEARCH")
    MediaTypes.register("zzztest.additive", ".zzzbar", "SEARCH")

    assert MediaTypes.contains("zzztest.additive", ".zzzfoo", "SEARCH")
    assert MediaTypes.contains("zzztest.additive", ".zzzbar", "SEARCH")


def test_contains_missing_group_raises_error():
    with pytest.raises(AttributeError, match=r"is not registered"):
        MediaTypes.contains("zzztest.does_not_exist", ".zzzfoo", "SEARCH")


def test_dot_notation_chains_to_parents():
    MediaTypes.register("zzztest.chain.parent.child", ".zzzchild", "SEARCH")

    assert MediaTypes.contains("zzztest.chain.parent.child", ".zzzchild", "SEARCH")
    assert MediaTypes.contains("zzztest.chain.parent", ".zzzchild", "SEARCH")
    assert MediaTypes.contains("zzztest.chain", ".zzzchild", "SEARCH")


def test_explicit_chain_group():
    MediaTypes.chain_group("zzztest.composite", ["zzztest.composite_child"])
    MediaTypes.register("zzztest.composite_child", ".zzzcomposite", "SEARCH")

    assert MediaTypes.contains("zzztest.composite", ".zzzcomposite", "SEARCH")


def test_equivalent_extensions():
    MediaTypes.register("zzztest.equiv", [".zzzone", ".zzztwo"], "SEARCH")

    assert MediaTypes.get_equivalent_exts(".zzzone") == {".zzzone", ".zzztwo"}
    assert MediaTypes.get_equivalent_exts(".zzztwo") == {".zzzone", ".zzztwo"}
    assert MediaTypes.contains("zzztest.equiv", ".zzzone", "SEARCH")
    assert MediaTypes.contains("zzztest.equiv", ".zzztwo", "SEARCH")


def test_get_equivalent_exts_defaults_to_itself():
    assert MediaTypes.get_equivalent_exts(".zzzunregistered") == {".zzzunregistered"}


def test_find():
    MediaTypes.register("zzztest.find_a", ".zzzfind", "SEARCH")
    MediaTypes.register("zzztest.find_b", ".zzzfind", "RENDER")

    search_keys = {group.key for group in MediaTypes.find(".zzzfind", "SEARCH")}
    render_keys = {group.key for group in MediaTypes.find(".zzzfind", "RENDER")}

    assert "zzztest.find_a" in search_keys
    assert "zzztest.find_a" not in render_keys
    assert "zzztest.find_b" in render_keys
    assert "zzztest.find_b" not in search_keys


def test_add_name_aliases_and_lookup():
    MediaTypes.register("zzztest.alias_target", ".zzzalias", "SEARCH")
    MediaTypes.add_name_aliases("zzztest.alias_target", ["ZZZ Test Group", "zzztest"])

    assert MediaTypes.get_group_key_from_name("ZZZ Test Group") == "zzztest.alias_target"
    assert MediaTypes.get_group_key_from_name("zzz test group", case_sensitive=False) == (
        "zzztest.alias_target"
    )
    assert (
        MediaTypes.get_group_key_from_name(
            "zzztestGroup", case_sensitive=False, ignore_whitespace=True
        )
        == "zzztest.alias_target"
    )
    assert MediaTypes.get_group_key_from_name("Not A Real Alias") is None
