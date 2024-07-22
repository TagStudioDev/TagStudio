from pathlib import Path

from src.core.search import SearchQuery
from src.core.enums import SearchMode


def sqmtch(
    search_query: SearchQuery,
    tag_ids: list[int] = [],
    fields_text: dict[str, str] = None,
    path="subfolder",
    filename="entry.png",
) -> bool:
    if fields_text is None:
        if tag_ids:
            fields_text = {"tags": None}
        else:
            fields_text = {}
    return search_query.match_entry(
        path=Path(path),
        filename=Path(filename),
        tag_ids=tag_ids,
        fields_text=fields_text,
    )


def test_empty_AND_construction():
    search_query = SearchQuery("", SearchMode.AND)
    assert search_query


def test_empty_OR_construction():
    search_query = SearchQuery("", SearchMode.OR)
    assert search_query


def test_tokenize_empty_list():
    search_query = SearchQuery("", SearchMode.AND)
    assert str(search_query) == "L()"


def test_tokenize_ws_list():
    search_query = SearchQuery(" \t\n\r", SearchMode.AND)
    assert str(search_query) == "L()"


def test_tokenize_ascii_tag():
    search_query = SearchQuery(
        "abcdefghijklmnopqrstuvwxyz0123456789!\"#$%&'()*+,-./:;<=>?@[\\]^_`|{}~",
        SearchMode.AND,
    )
    assert (
        str(search_query)
        == "L(T(abcdefghijklmnopqrstuvwxyz0123456789!\"#$%&'()*+,-./:;<=>?@[\\]^_`|{}~))"
    )


def test_tokenize_leading_ws_tag():
    search_query = SearchQuery(" tag", SearchMode.AND)
    assert str(search_query) == "L(T(tag))"


def test_tokenize_trailing_ws_tag():
    search_query = SearchQuery("tag ", SearchMode.AND)
    assert str(search_query) == "L(T(tag))"


def test_tokenize_unary_minus():
    search_query = SearchQuery("-tag", SearchMode.AND)
    assert str(search_query) == "L(U(- T(tag)))"


def test_tokenize_all_unary():
    search_query = SearchQuery("~-not !tag", SearchMode.AND)
    assert str(search_query) == "L(U(~ U(- U(not U(! T(tag))))))"


def test_tokenize_all_unary_with_ws():
    search_query = SearchQuery(" ~ - not ! tag ", SearchMode.AND)
    assert str(search_query) == "L(U(~ U(- U(not U(! T(tag))))))"


def test_tokenize_exc_before_equ_tag():
    search_query = SearchQuery("!=^_^=", SearchMode.AND)
    assert str(search_query) == "L(U(! T(=^_^=)))"


def test_tokenize_exc_before_equ_equ_tag():
    search_query = SearchQuery("!==tag==", SearchMode.AND)
    assert str(search_query) == "L(U(! T(==tag==)))"


def test_tokenize_exc_before_equ_equ_equ_equ():
    search_query = SearchQuery("!====", SearchMode.AND)
    assert str(search_query) == "L(U(! T(====)))"


def test_tokenize_escaped_unary_tags():
    search_query = SearchQuery("/~ /- /! /not", SearchMode.AND)
    assert str(search_query) == "L(T(/~) T(/-) T(/!) T(/not))"


def test_tokenize_binary_and():
    search_query = SearchQuery("tag1 and tag2", SearchMode.AND)
    assert str(search_query) == "L(B(T(tag1) and T(tag2)))"


def test_tokenize_all_binary():
    search_query = SearchQuery(
        "t01 & t02 ^ t03 | t04 v t05 or t06 || t07 and t08 && t09 nor t10 nand t11 xor t12 != t13 !== t14 xnor t15 == t16 === t17",
        SearchMode.AND,
    )
    assert (
        str(search_query)
        == "L(B(B(B(B(B(B(B(B(B(B(B(B(B(B(B(B(T(t01) & T(t02)) ^ T(t03)) | T(t04)) v T(t05)) or T(t06)) || T(t07)) and T(t08)) && T(t09)) nor T(t10)) nand T(t11)) xor T(t12)) != T(t13)) !== T(t14)) xnor T(t15)) == T(t16)) === T(t17)))"
    )


def test_tokenize_leading_binary_tag():
    search_query = SearchQuery("tag1 ^_^ tag3", SearchMode.AND)
    assert str(search_query) == "L(T(tag1) T(^_^) T(tag3))"


def test_tokenize_binary_oparen_tag():
    search_query = SearchQuery("tag1 |( tag3", SearchMode.AND)
    assert str(search_query) == "L(T(tag1) T(|() T(tag3))"


def test_tokenize_binary_cparen_tag():
    search_query = SearchQuery("tag1 |) tag3", SearchMode.AND)
    assert str(search_query) == "L(T(tag1) T(|)) T(tag3))"


def test_tokenize_oparen_binary_tag():
    search_query = SearchQuery("tag1 (| tag3", SearchMode.AND)
    assert str(search_query) == "L(T(tag1) T((|) T(tag3))"


def test_tokenize_cparen_binary_tag():
    search_query = SearchQuery("tag1 )| tag3", SearchMode.AND)
    assert str(search_query) == "L(T(tag1) T()|) T(tag3))"


def test_tokenize_escaped_binary_tag():
    search_query = SearchQuery("tag1 /and tag3", SearchMode.AND)
    assert str(search_query) == "L(T(tag1) T(/and) T(tag3))"


def test_tokenize_nested_lists():
    search_query = SearchQuery("( )", SearchMode.AND)
    assert str(search_query) == "L(L())"


def test_tokenize_mixed_paren_nexted_lists():
    search_query = SearchQuery("{ [ ( ] } )", SearchMode.AND)
    assert str(search_query) == "L(L(L(L())))"


def test_tokenize_list_omit_cparen():
    search_query = SearchQuery("{ [ (", SearchMode.AND)
    assert str(search_query) == "L(L(L(L())))"


def test_tokenize_list_omit_oparen():
    search_query = SearchQuery("] } )", SearchMode.AND)
    assert str(search_query) == "L()"


def test_tokenize_leading_ws_list():
    search_query = SearchQuery(" ( )", SearchMode.AND)
    assert str(search_query) == "L(L())"


def test_tokenize_trailing_ws_list():
    search_query = SearchQuery("( ) ", SearchMode.AND)
    assert str(search_query) == "L(L())"


def test_tokenize_leading_ws_omit_cparen():
    search_query = SearchQuery(" (", SearchMode.AND)
    assert str(search_query) == "L(L())"


def test_tokenize_trailing_ws_omit_cparen():
    search_query = SearchQuery("( ", SearchMode.AND)
    assert str(search_query) == "L(L())"


def test_tokenize_leading_ws_omit_oparen():
    search_query = SearchQuery(" )", SearchMode.AND)
    assert str(search_query) == "L()"


def test_tokenize_trailing_ws_omit_oparen():
    search_query = SearchQuery(") ", SearchMode.AND)
    assert str(search_query) == "L()"


def test_tokenize_starting_oparen_tag():
    search_query = SearchQuery("(:", SearchMode.AND)
    assert str(search_query) == "L(T((:))"


def test_tokenize_ending_oparen_tag():
    search_query = SearchQuery(":(", SearchMode.AND)
    assert str(search_query) == "L(T(:())"


def test_tokenize_starting_cparen_tag():
    search_query = SearchQuery("):", SearchMode.AND)
    assert str(search_query) == "L(T():))"


def test_tokenize_ending_cparen_tag():
    search_query = SearchQuery(":)", SearchMode.AND)
    assert str(search_query) == "L(T(:)))"


def test_tokenize_unary_paren():
    search_query = SearchQuery("-( tag", SearchMode.AND)
    assert str(search_query) == "L(U(- L(T(tag))))"


def test_parse_cparen():
    search_query = SearchQuery("( ) ( ) ( )", SearchMode.AND)
    assert str(search_query) == "L(L() L() L())"


def test_parse_nested_cparen():
    search_query = SearchQuery("( ( ) ( ) ) ( ( ) ( ) )", SearchMode.AND)
    assert str(search_query) == "L(L(L() L()) L(L() L()))"


def test_parse_unary_in_nested_list():
    search_query = SearchQuery("( -tag )", SearchMode.AND)
    assert str(search_query) == "L(L(U(- T(tag))))"


def test_parse_binary_in_nested_list():
    search_query = SearchQuery("( tag1 and tag2 )", SearchMode.AND)
    assert str(search_query) == "L(L(B(T(tag1) and T(tag2))))"


def test_parse_tag_in_nested_list():
    search_query = SearchQuery("( tag )", SearchMode.AND)
    assert str(search_query) == "L(L(T(tag)))"


def test_parse_ignore_sole_unary():
    search_query = SearchQuery("not", SearchMode.AND)
    assert str(search_query) == "L()"


def test_parse_ignore_unary_after_tag():
    search_query = SearchQuery("tag -", SearchMode.AND)
    assert str(search_query) == "L(T(tag))"


def test_parse_ignore_unary_before_cparen():
    search_query = SearchQuery("( tag1 -) tag2", SearchMode.AND)
    assert str(search_query) == "L(L(T(tag1)) T(tag2))"


def test_parse_ignore_cparen_after_unary():
    search_query = SearchQuery("tag1 not ) tag2", SearchMode.AND)
    assert str(search_query) == "L(T(tag1) U(not T(tag2)))"


def test_parse_ignore_nested_unary():
    search_query = SearchQuery("tag - - ", SearchMode.AND)
    assert str(search_query) == "L(T(tag))"


def test_parse_ignore_unary_before_binary():
    search_query = SearchQuery("tag1 -and tag2", SearchMode.AND)
    assert str(search_query) == "L(B(T(tag1) and T(tag2)))"


def test_parse_ignore_unary_before_ignored_binary():
    search_query = SearchQuery("( tag1 -and ) tag2", SearchMode.AND)
    assert str(search_query) == "L(L(T(tag1)) T(tag2))"


def test_parse_ignore_exc_before_xnor2():
    search_query = SearchQuery("tag1 !=== tag2", SearchMode.AND)
    assert str(search_query) == "L(B(T(tag1) === T(tag2)))"


def test_parse_list_in_unary():
    search_query = SearchQuery("-( )", SearchMode.AND)
    assert str(search_query) == "L(U(- L()))"


def test_parse_ignore_nested_unary_before_cparen():
    search_query = SearchQuery("-( - ) tag", SearchMode.AND)
    assert str(search_query) == "L(U(- L()) T(tag))"


def test_parse_ignore_cparen_with_nested_unary():
    search_query = SearchQuery(" ) - ) - ) tag ) ", SearchMode.AND)
    assert str(search_query) == "L(U(- U(- T(tag))))"


def test_parse_ignore_sole_binary():
    search_query = SearchQuery("and", SearchMode.AND)
    assert str(search_query) == "L()"


def test_parse_ignore_binary_after_tag():
    search_query = SearchQuery("tag and", SearchMode.AND)
    assert str(search_query) == "L(T(tag))"


def test_parse_ignore_binary_before_tag():
    search_query = SearchQuery("and tag", SearchMode.AND)
    assert str(search_query) == "L(T(tag))"


def test_parse_ignore_binary_before_cparen():
    search_query = SearchQuery("( tag1 and ) tag2", SearchMode.AND)
    assert str(search_query) == "L(L(T(tag1)) T(tag2))"


def test_parse_ignore_cparen_after_binary():
    search_query = SearchQuery("tag1 and ) tag2", SearchMode.AND)
    assert str(search_query) == "L(B(T(tag1) and T(tag2)))"


def test_parse_ignore_binary_after_binary():
    search_query = SearchQuery("tag1 and nand tag2", SearchMode.AND)
    assert str(search_query) == "L(B(T(tag1) and T(tag2)))"


def test_parse_binary_before_unary():
    search_query = SearchQuery("tag1 and not tag2", SearchMode.AND)
    assert str(search_query) == "L(B(T(tag1) and U(not T(tag2))))"


def test_parse_ignore_binary_before_failed_unary():
    search_query = SearchQuery("( tag1 and not ) tag2", SearchMode.AND)
    assert str(search_query) == "L(L(T(tag1)) T(tag2))"


def test_share_tag_requests_list():
    search_query = SearchQuery(r"/\tag1 \/tag2 tag3 tag3", SearchMode.AND)
    assert str(search_query) == r"L(T(/\tag1) T(\/tag2) T(tag3) T(tag3))"
    assert search_query.share_tag_requests() == [r"\tag1", "/tag2", "tag3"]
    assert search_query.share_field_requests() == set()


def test_share_tag_requests_unary():
    search_query = SearchQuery(r"~/\tag1 ~\/tag2 ~tag3 ~tag3", SearchMode.AND)
    assert (
        str(search_query)
        == r"L(U(~ T(/\tag1)) U(~ T(\/tag2)) U(~ T(tag3)) U(~ T(tag3)))"
    )
    assert search_query.share_tag_requests() == [r"\tag1", "/tag2", "tag3"]
    assert search_query.share_field_requests() == set()


def test_share_tag_requests_binary():
    search_query = SearchQuery(
        r"( ) and /\tag1 and \/tag2 and tag3 and tag3", SearchMode.AND
    )
    assert (
        str(search_query)
        == r"L(B(B(B(B(L() and T(/\tag1)) and T(\/tag2)) and T(tag3)) and T(tag3)))"
    )
    assert search_query.share_tag_requests() == [r"\tag1", "/tag2", "tag3"]
    assert search_query.share_field_requests() == set()


def test_share_field_requests_list():
    search_query = SearchQuery(
        r"hasfield1 has_field2 has-field3 hasfield4:true has_field5:true has-field6:true field7:text",
        SearchMode.AND,
    )
    assert (
        str(search_query)
        == r"L(T(hasfield1) T(has_field2) T(has-field3) T(hasfield4:true) T(has_field5:true) T(has-field6:true) T(field7:text))"
    )
    assert search_query.share_tag_requests() == [
        "hasfield1",
        "has_field2",
        "has-field3",
        "hasfield4:true",
        "has_field5:true",
        "has-field6:true",
        "field7:text",
    ]
    assert search_query.share_field_requests() == set(
        [
            "field1",
            "field2",
            "field3",
            "field4",
            "field5",
            "field6",
            "field7",
            "_field2",
            "_field5",
            "-field3",
            "-field6",
            "hasfield4",
            "has_field5",
            "has-field6",
            "field4:true",
            "field5:true",
            "field6:true",
            "_field5:true",
            "-field6:true",
        ]
    )


def test_share_field_requests_unary():
    search_query = SearchQuery(
        r"~hasfield1 ~has_field2 ~has-field3 ~hasfield4:true ~has_field5:true ~has-field6:true ~field7:text",
        SearchMode.AND,
    )
    assert (
        str(search_query)
        == r"L(U(~ T(hasfield1)) U(~ T(has_field2)) U(~ T(has-field3)) U(~ T(hasfield4:true)) U(~ T(has_field5:true)) U(~ T(has-field6:true)) U(~ T(field7:text)))"
    )
    assert search_query.share_tag_requests() == [
        "hasfield1",
        "has_field2",
        "has-field3",
        "hasfield4:true",
        "has_field5:true",
        "has-field6:true",
        "field7:text",
    ]
    assert search_query.share_field_requests() == set(
        [
            "field1",
            "field2",
            "field3",
            "field4",
            "field5",
            "field6",
            "field7",
            "_field2",
            "_field5",
            "-field3",
            "-field6",
            "hasfield4",
            "has_field5",
            "has-field6",
            "field4:true",
            "field5:true",
            "field6:true",
            "_field5:true",
            "-field6:true",
        ]
    )


def test_share_field_requests_binary():
    search_query = SearchQuery(
        r"hasfield1 and has_field2 and has-field3 and hasfield4:true and has_field5:true and has-field6:true and field7:text",
        SearchMode.AND,
    )
    assert (
        str(search_query)
        == r"L(B(B(B(B(B(B(T(hasfield1) and T(has_field2)) and T(has-field3)) and T(hasfield4:true)) and T(has_field5:true)) and T(has-field6:true)) and T(field7:text)))"
    )
    assert search_query.share_tag_requests() == [
        "hasfield1",
        "has_field2",
        "has-field3",
        "hasfield4:true",
        "has_field5:true",
        "has-field6:true",
        "field7:text",
    ]
    assert search_query.share_field_requests() == set(
        [
            "field1",
            "field2",
            "field3",
            "field4",
            "field5",
            "field6",
            "field7",
            "_field2",
            "_field5",
            "-field3",
            "-field6",
            "hasfield4",
            "has_field5",
            "has-field6",
            "field4:true",
            "field5:true",
            "field6:true",
            "_field5:true",
            "-field6:true",
        ]
    )


def test_receive_requested_lib_info_true():
    search_query = SearchQuery("tag1 tag2 tag2", SearchMode.AND)
    assert str(search_query) == "L(T(tag1) T(tag2) T(tag2))"
    assert search_query.share_tag_requests() == ["tag1", "tag2"]
    assert search_query.share_field_requests() == set()
    search_query.receive_requested_lib_info({"tag1": [2, 4], "tag2": [3, 5]}, set())
    assert sqmtch(search_query, tag_ids=[2, 3])
    assert sqmtch(search_query, tag_ids=[2, 5])
    assert sqmtch(search_query, tag_ids=[4, 3])
    assert sqmtch(search_query, tag_ids=[4, 5])
    assert not sqmtch(search_query, tag_ids=[2, 4])
    assert not sqmtch(search_query, tag_ids=[3, 5])
    assert not sqmtch(search_query, tag_ids=[2, 6])
    assert not sqmtch(search_query, tag_ids=[1, 3])


def test_eval_and_mode_list():
    search_query = SearchQuery("tag1 tag2 tag3", SearchMode.AND)
    assert str(search_query) == "L(T(tag1) T(tag2) T(tag3))"
    assert search_query.share_tag_requests() == ["tag1", "tag2", "tag3"]
    assert search_query.share_field_requests() == set()
    search_query.receive_requested_lib_info(
        {"tag1": [1], "tag2": [2], "tag3": [3]}, set()
    )
    assert sqmtch(search_query, tag_ids=[1, 2, 3])
    assert not sqmtch(search_query, tag_ids=[2, 3])
    assert not sqmtch(search_query, tag_ids=[1, 3])
    assert not sqmtch(search_query, tag_ids=[3])
    assert not sqmtch(search_query, tag_ids=[1, 2])
    assert not sqmtch(search_query, tag_ids=[2])
    assert not sqmtch(search_query, tag_ids=[1])
    assert not sqmtch(search_query, tag_ids=[])


def test_eval_or_mode_list():
    search_query = SearchQuery("tag1 tag2 tag3", SearchMode.OR)
    assert str(search_query) == "L(T(tag1) T(tag2) T(tag3))"
    assert search_query.share_tag_requests() == ["tag1", "tag2", "tag3"]
    assert search_query.share_field_requests() == set()
    search_query.receive_requested_lib_info(
        {"tag1": [1], "tag2": [2], "tag3": [3]}, set()
    )
    assert sqmtch(search_query, tag_ids=[1, 2, 3])
    assert sqmtch(search_query, tag_ids=[2, 3])
    assert sqmtch(search_query, tag_ids=[1, 3])
    assert sqmtch(search_query, tag_ids=[3])
    assert sqmtch(search_query, tag_ids=[1, 2])
    assert sqmtch(search_query, tag_ids=[2])
    assert sqmtch(search_query, tag_ids=[1])
    assert not sqmtch(search_query, tag_ids=[])


def test_eval_optional_tags_list():
    search_query = SearchQuery("tag1 ~tag2 ~tag3", SearchMode.AND)
    assert str(search_query) == "L(T(tag1) U(~ T(tag2)) U(~ T(tag3)))"
    assert search_query.share_tag_requests() == ["tag1", "tag2", "tag3"]
    assert search_query.share_field_requests() == set()
    search_query.receive_requested_lib_info(
        {"tag1": [1], "tag2": [2], "tag3": [3]}, set()
    )
    assert sqmtch(search_query, tag_ids=[1, 2, 3])
    assert not sqmtch(search_query, tag_ids=[2, 3])
    assert sqmtch(search_query, tag_ids=[1, 3])
    assert not sqmtch(search_query, tag_ids=[3])
    assert sqmtch(search_query, tag_ids=[1, 2])
    assert not sqmtch(search_query, tag_ids=[2])
    assert not sqmtch(search_query, tag_ids=[1])
    assert not sqmtch(search_query, tag_ids=[])


def test_eval_partial_tags_list():
    search_query = SearchQuery("tag1 ~tag2 ~tag3", SearchMode.OR)
    assert str(search_query) == "L(T(tag1) U(~ T(tag2)) U(~ T(tag3)))"
    assert search_query.share_tag_requests() == ["tag1", "tag2", "tag3"]
    assert search_query.share_field_requests() == set()
    search_query.receive_requested_lib_info(
        {"tag1": [1], "tag2": [2], "tag3": [3]}, set()
    )
    assert sqmtch(search_query, tag_ids=[1, 2, 3])
    assert sqmtch(search_query, tag_ids=[2, 3])
    assert sqmtch(search_query, tag_ids=[1, 3])
    assert not sqmtch(search_query, tag_ids=[3])
    assert sqmtch(search_query, tag_ids=[1, 2])
    assert not sqmtch(search_query, tag_ids=[2])
    assert sqmtch(search_query, tag_ids=[1])
    assert not sqmtch(search_query, tag_ids=[])


def test_eval_all_unary():
    search_query = SearchQuery("-tag1 !tag2 not tag3 -~tag4", SearchMode.AND)
    assert (
        str(search_query)
        == "L(U(- T(tag1)) U(! T(tag2)) U(not T(tag3)) U(- U(~ T(tag4))))"
    )
    assert search_query.share_tag_requests() == ["tag1", "tag2", "tag3", "tag4"]
    assert search_query.share_field_requests() == set()
    search_query.receive_requested_lib_info(
        {"tag1": [1], "tag2": [2], "tag3": [3], "tag4": [4]}, set()
    )
    assert sqmtch(search_query, tag_ids=[])


def test_eval_binary_and_false():
    search_query = SearchQuery("t1 and t2 t1 ^ t2 t1 & t2 t1 && t2", SearchMode.OR)
    assert (
        str(search_query)
        == "L(B(T(t1) and T(t2)) B(T(t1) ^ T(t2)) B(T(t1) & T(t2)) B(T(t1) && T(t2)))"
    )
    assert search_query.share_tag_requests() == ["t1", "t2"]
    assert search_query.share_field_requests() == set()
    search_query.receive_requested_lib_info({"t1": [1], "t2": [2]}, set())
    assert not sqmtch(search_query, tag_ids=[])
    assert not sqmtch(search_query, tag_ids=[1])
    assert not sqmtch(search_query, tag_ids=[2])


def test_eval_binary_and_true():
    search_query = SearchQuery("t1 and t2 t1 ^ t2 t1 & t2 t1 && t2", SearchMode.AND)
    assert (
        str(search_query)
        == "L(B(T(t1) and T(t2)) B(T(t1) ^ T(t2)) B(T(t1) & T(t2)) B(T(t1) && T(t2)))"
    )
    assert search_query.share_tag_requests() == ["t1", "t2"]
    assert search_query.share_field_requests() == set()
    search_query.receive_requested_lib_info({"t1": [1], "t2": [2]}, set())
    assert sqmtch(search_query, tag_ids=[1, 2])


def test_eval_binary_or_false():
    search_query = SearchQuery("t1 or t2 t1 v t2 t1 | t2 t1 || t2", SearchMode.OR)
    assert (
        str(search_query)
        == "L(B(T(t1) or T(t2)) B(T(t1) v T(t2)) B(T(t1) | T(t2)) B(T(t1) || T(t2)))"
    )
    assert search_query.share_tag_requests() == ["t1", "t2"]
    assert search_query.share_field_requests() == set()
    search_query.receive_requested_lib_info({"t1": [1], "t2": [2]}, set())
    assert not sqmtch(search_query, tag_ids=[])


def test_eval_binary_or_true():
    search_query = SearchQuery("t1 or t2 t1 v t2 t1 | t2 t1 || t2", SearchMode.AND)
    assert (
        str(search_query)
        == "L(B(T(t1) or T(t2)) B(T(t1) v T(t2)) B(T(t1) | T(t2)) B(T(t1) || T(t2)))"
    )
    assert search_query.share_tag_requests() == ["t1", "t2"]
    assert search_query.share_field_requests() == set()
    search_query.receive_requested_lib_info({"t1": [1], "t2": [2]}, set())
    assert sqmtch(search_query, tag_ids=[1])
    assert sqmtch(search_query, tag_ids=[2])
    assert sqmtch(search_query, tag_ids=[1, 2])


def test_eval_binary_nor_false():
    search_query = SearchQuery("t1 nor t2", SearchMode.OR)
    assert str(search_query) == "L(B(T(t1) nor T(t2)))"
    assert search_query.share_tag_requests() == ["t1", "t2"]
    assert search_query.share_field_requests() == set()
    search_query.receive_requested_lib_info({"t1": [1], "t2": [2]}, set())
    assert not sqmtch(search_query, tag_ids=[1])
    assert not sqmtch(search_query, tag_ids=[2])
    assert not sqmtch(search_query, tag_ids=[1, 2])


def test_eval_binary_nor_true():
    search_query = SearchQuery("t1 nor t2", SearchMode.AND)
    assert str(search_query) == "L(B(T(t1) nor T(t2)))"
    assert search_query.share_tag_requests() == ["t1", "t2"]
    assert search_query.share_field_requests() == set()
    search_query.receive_requested_lib_info({"t1": [1], "t2": [2]}, set())
    assert sqmtch(search_query, tag_ids=[])


def test_eval_binary_nand_false():
    search_query = SearchQuery("t1 nand t2", SearchMode.OR)
    assert str(search_query) == "L(B(T(t1) nand T(t2)))"
    assert search_query.share_tag_requests() == ["t1", "t2"]
    search_query.receive_requested_lib_info({"t1": [1], "t2": [2]}, set())
    assert not sqmtch(search_query, tag_ids=[1, 2])


def test_eval_binary_nand_true():
    search_query = SearchQuery("t1 nand t2", SearchMode.AND)
    assert str(search_query) == "L(B(T(t1) nand T(t2)))"
    assert search_query.share_tag_requests() == ["t1", "t2"]
    assert search_query.share_field_requests() == set()
    search_query.receive_requested_lib_info({"t1": [1], "t2": [2]}, set())
    assert sqmtch(search_query, tag_ids=[])
    assert sqmtch(search_query, tag_ids=[1])
    assert sqmtch(search_query, tag_ids=[2])


def test_eval_binary_xor_false():
    search_query = SearchQuery("t1 xor t2 t1 != t2 t1 !== t2", SearchMode.OR)
    assert (
        str(search_query)
        == "L(B(T(t1) xor T(t2)) B(T(t1) != T(t2)) B(T(t1) !== T(t2)))"
    )
    assert search_query.share_tag_requests() == ["t1", "t2"]
    assert search_query.share_field_requests() == set()
    search_query.receive_requested_lib_info({"t1": [1], "t2": [2]}, set())
    assert not sqmtch(search_query, tag_ids=[1, 2])
    assert not sqmtch(search_query, tag_ids=[])


def test_eval_binary_xor_true():
    search_query = SearchQuery("t1 xor t2 t1 != t2 t1 !== t2", SearchMode.AND)
    assert (
        str(search_query)
        == "L(B(T(t1) xor T(t2)) B(T(t1) != T(t2)) B(T(t1) !== T(t2)))"
    )
    assert search_query.share_tag_requests() == ["t1", "t2"]
    assert search_query.share_field_requests() == set()
    search_query.receive_requested_lib_info({"t1": [1], "t2": [2]}, set())
    assert sqmtch(search_query, tag_ids=[1])
    assert sqmtch(search_query, tag_ids=[2])


def test_eval_binary_xnor_false():
    search_query = SearchQuery("t1 xnor t2 t1 = t2 t1 == t2 t1 === t2", SearchMode.OR)
    assert (
        str(search_query)
        == "L(B(T(t1) xnor T(t2)) B(T(t1) = T(t2)) B(T(t1) == T(t2)) B(T(t1) === T(t2)))"
    )
    assert search_query.share_tag_requests() == ["t1", "t2"]
    assert search_query.share_field_requests() == set()
    search_query.receive_requested_lib_info({"t1": [1], "t2": [2]}, set())
    assert not sqmtch(search_query, tag_ids=[1])
    assert not sqmtch(search_query, tag_ids=[2])


def test_eval_binary_xnor_true():
    search_query = SearchQuery("t1 xnor t2 t1 = t2 t1 == t2 t1 === t2", SearchMode.AND)
    assert (
        str(search_query)
        == "L(B(T(t1) xnor T(t2)) B(T(t1) = T(t2)) B(T(t1) == T(t2)) B(T(t1) === T(t2)))"
    )
    assert search_query.share_tag_requests() == ["t1", "t2"]
    assert search_query.share_field_requests() == set()
    search_query.receive_requested_lib_info({"t1": [1], "t2": [2]}, set())
    assert sqmtch(search_query, tag_ids=[1, 2])
    assert sqmtch(search_query, tag_ids=[])


def test_eval_tag_empty_tags_false():
    search_query = SearchQuery("empty no_fields no-fields nofields", SearchMode.OR)
    assert str(search_query) == "L(T(empty) T(no_fields) T(no-fields) T(nofields))"
    assert search_query.share_tag_requests() == [
        "empty",
        "no_fields",
        "no-fields",
        "nofields",
    ]
    assert search_query.share_field_requests() == set()
    search_query.receive_requested_lib_info(
        {"empty": [], "no_fields": [], "no-fields": [], "nofields": []}, set()
    )
    assert not sqmtch(search_query, fields_text={"tags": None})


def test_eval_tag_empty_text_false():
    search_query = SearchQuery("empty no_fields no-fields nofields", SearchMode.OR)
    assert str(search_query) == "L(T(empty) T(no_fields) T(no-fields) T(nofields))"
    assert search_query.share_tag_requests() == [
        "empty",
        "no_fields",
        "no-fields",
        "nofields",
    ]
    assert search_query.share_field_requests() == set()
    search_query.receive_requested_lib_info(
        {"empty": [], "no_fields": [], "no-fields": [], "nofields": []}, set()
    )
    assert not sqmtch(search_query, fields_text={"description": "desc"})


def test_eval_tag_empty_true():
    search_query = SearchQuery("empty no_fields no-fields nofields", SearchMode.AND)
    assert str(search_query) == "L(T(empty) T(no_fields) T(no-fields) T(nofields))"
    assert search_query.share_tag_requests() == [
        "empty",
        "no_fields",
        "no-fields",
        "nofields",
    ]
    assert search_query.share_field_requests() == set()
    search_query.receive_requested_lib_info(
        {"empty": [], "no_fields": [], "no-fields": [], "nofields": []}, set()
    )
    assert sqmtch(search_query)


def test_eval_tag_no_author_author_false():
    search_query = SearchQuery(
        "no_author no-author noauthor no_artist no-artist noartist", SearchMode.OR
    )
    assert (
        str(search_query)
        == "L(T(no_author) T(no-author) T(noauthor) T(no_artist) T(no-artist) T(noartist))"
    )
    assert search_query.share_tag_requests() == [
        "no_author",
        "no-author",
        "noauthor",
        "no_artist",
        "no-artist",
        "noartist",
    ]
    assert search_query.share_field_requests() == set()
    search_query.receive_requested_lib_info(
        {
            "no_author": [],
            "no-author": [],
            "noauthor": [],
            "no_artist": [],
            "no-artist": [],
            "noartist": [],
        },
        set(),
    )
    assert not sqmtch(search_query, fields_text={"author": "william_shakespeare"})


def test_eval_tag_no_author_artist_false():
    search_query = SearchQuery(
        "no_author no-author noauthor no_artist no-artist noartist", SearchMode.OR
    )
    assert (
        str(search_query)
        == "L(T(no_author) T(no-author) T(noauthor) T(no_artist) T(no-artist) T(noartist))"
    )
    assert search_query.share_tag_requests() == [
        "no_author",
        "no-author",
        "noauthor",
        "no_artist",
        "no-artist",
        "noartist",
    ]
    assert search_query.share_field_requests() == set()
    search_query.receive_requested_lib_info(
        {
            "no_author": [],
            "no-author": [],
            "noauthor": [],
            "no_artist": [],
            "no-artist": [],
            "noartist": [],
        },
        set(),
    )
    assert not sqmtch(search_query, fields_text={"artist": "leonardo_da_vinci"})


def test_eval_tag_no_author_true():
    search_query = SearchQuery(
        "no_author no-author noauthor no_artist no-artist noartist", SearchMode.AND
    )
    assert (
        str(search_query)
        == "L(T(no_author) T(no-author) T(noauthor) T(no_artist) T(no-artist) T(noartist))"
    )
    assert search_query.share_tag_requests() == [
        "no_author",
        "no-author",
        "noauthor",
        "no_artist",
        "no-artist",
        "noartist",
    ]
    assert search_query.share_field_requests() == set()
    search_query.receive_requested_lib_info(
        {
            "no_author": [],
            "no-author": [],
            "noauthor": [],
            "no_artist": [],
            "no-artist": [],
            "noartist": [],
        },
        set(),
    )
    assert sqmtch(
        search_query,
        fields_text={"tags": None, "title": "title", "description": "desc"},
    )
    assert sqmtch(search_query)


def test_eval_tag_untagged_false():
    search_query = SearchQuery("untagged no_tags no-tags notags", SearchMode.OR)
    assert str(search_query) == "L(T(untagged) T(no_tags) T(no-tags) T(notags))"
    assert search_query.share_tag_requests() == [
        "untagged",
        "no_tags",
        "no-tags",
        "notags",
    ]
    assert search_query.share_field_requests() == set()
    search_query.receive_requested_lib_info(
        {"untagged": [], "no_tags": [], "no-tags": [], "notags": []}, set()
    )
    assert not sqmtch(
        search_query,
        tag_ids=[1],
        fields_text={"tags": None, "title": "title", "description": "desc"},
    )
    assert not sqmtch(search_query, tag_ids=[1], fields_text={"tags": None})


def test_eval_tag_untagged_true():
    search_query = SearchQuery("untagged no_tags no-tags notags", SearchMode.AND)
    assert str(search_query) == "L(T(untagged) T(no_tags) T(no-tags) T(notags))"
    assert search_query.share_tag_requests() == [
        "untagged",
        "no_tags",
        "no-tags",
        "notags",
    ]
    assert search_query.share_field_requests() == set()
    search_query.receive_requested_lib_info(
        {"untagged": [], "no_tags": [], "no-tags": [], "notags": []}, set()
    )
    assert sqmtch(
        search_query,
        tag_ids=[],
        fields_text={"tags": None, "title": "title", "description": "desc"},
    )
    assert sqmtch(search_query, tag_ids=[], fields_text={"tags": None})
    assert sqmtch(
        search_query, tag_ids=[], fields_text={"title": "title", "description": "desc"}
    )


def test_eval_tag_filename():
    search_query = SearchQuery(
        "filename:subfolder1 file_name:subfolder1 file-name:subfolder1 filename:entry1.png file_name:entry1.png file-name:entry1.png",
        SearchMode.AND,
    )
    assert (
        str(search_query)
        == "L(T(filename:subfolder1) T(file_name:subfolder1) T(file-name:subfolder1) T(filename:entry1.png) T(file_name:entry1.png) T(file-name:entry1.png))"
    )
    assert search_query.share_tag_requests() == [
        "filename:subfolder1",
        "file_name:subfolder1",
        "file-name:subfolder1",
        "filename:entry1.png",
        "file_name:entry1.png",
        "file-name:entry1.png",
    ]
    assert search_query.share_field_requests() == set(
        ["filename", "file_name", "file-name"]
    )
    search_query.receive_requested_lib_info(
        {
            "filename:subfolder1": [],
            "file_name:subfolder1": [],
            "file-name:subfolder1": [],
            "filename:entry1.png": [],
            "file_name:entry1.png": [],
            "file-name:entry1.png": [],
        },
        set(),
    )
    assert sqmtch(search_query, path="subfolder1", filename="entry1.png")
    assert not sqmtch(search_query, path="subfolder2", filename="entry1.png")
    assert not sqmtch(search_query, path="subfolder1", filename="entry2.png")
    assert not sqmtch(search_query, path="subfolder2", filename="entry2.png")


def test_eval_tag_tag_id():
    search_query = SearchQuery("tag_id:1 tag-id:2 tagid:3", SearchMode.AND)
    assert str(search_query) == "L(T(tag_id:1) T(tag-id:2) T(tagid:3))"
    assert search_query.share_tag_requests() == ["tag_id:1", "tag-id:2", "tagid:3"]
    assert search_query.share_field_requests() == set(["tag_id", "tag-id", "tagid"])
    search_query.receive_requested_lib_info(
        {"tag_id:1": [], "tag-id:2": [], "tagid:3": []}, set()
    )
    assert sqmtch(search_query, tag_ids=[1, 2, 3])
    assert not sqmtch(search_query, tag_ids=[1, 2])
    assert not sqmtch(search_query, tag_ids=[2, 3])
    assert not sqmtch(search_query, tag_ids=[1, 3])


def test_eval_tag_fields_true():
    search_query = SearchQuery(
        r"hasfield1 has_field2 has-field3 hasfield4:false has_field5:false has-field6:false field7:text",
        SearchMode.AND,
    )
    assert (
        str(search_query)
        == r"L(T(hasfield1) T(has_field2) T(has-field3) T(hasfield4:false) T(has_field5:false) T(has-field6:false) T(field7:text))"
    )
    assert search_query.share_tag_requests() == [
        "hasfield1",
        "has_field2",
        "has-field3",
        "hasfield4:false",
        "has_field5:false",
        "has-field6:false",
        "field7:text",
    ]
    assert search_query.share_field_requests() == set(
        [
            "field1",
            "field2",
            "field3",
            "field4",
            "field5",
            "field6",
            "field7",
            "_field2",
            "_field5",
            "-field3",
            "-field6",
            "hasfield4",
            "has_field5",
            "has-field6",
            "field4:false",
            "field5:false",
            "field6:false",
            "_field5:false",
            "-field6:false",
        ]
    )
    search_query.receive_requested_lib_info(
        {
            "hasfield1": [],
            "has_field2": [],
            "has-field3": [],
            "hasfield4:false": [],
            "has_field5:false": [],
            "has-field6:false": [],
            "field7:text": [],
        },
        set(
            [
                "field1",
                "field2",
                "field3",
                "field4",
                "field5",
                "field6",
                "field7",
            ]
        ),
    )
    assert sqmtch(
        search_query,
        fields_text={
            "tags": None,
            "description": "desc",
            "field1": "",
            "field2": "",
            "field3": "",
            "field7": "text",
        },
    )
    assert sqmtch(
        search_query,
        fields_text={
            "field1": "",
            "field2": "",
            "field3": "",
            "field7": "text",
        },
    )
    assert sqmtch(
        search_query,
        fields_text={
            "tags": None,
            "description": "desc",
            "field1": None,
            "field2": None,
            "field3": None,
            "field7": "text",
        },
    )
    assert sqmtch(
        search_query,
        fields_text={
            "field1": None,
            "field2": None,
            "field3": None,
            "field7": "text",
        },
    )


def test_eval_tag_fields_false():
    search_query = SearchQuery(
        r"hasfield1 has_field2 has-field3 hasfield4:false has_field5:false has-field6:false field7:text",
        SearchMode.OR,
    )
    assert (
        str(search_query)
        == r"L(T(hasfield1) T(has_field2) T(has-field3) T(hasfield4:false) T(has_field5:false) T(has-field6:false) T(field7:text))"
    )
    assert search_query.share_tag_requests() == [
        "hasfield1",
        "has_field2",
        "has-field3",
        "hasfield4:false",
        "has_field5:false",
        "has-field6:false",
        "field7:text",
    ]
    assert search_query.share_field_requests() == set(
        [
            "field1",
            "field2",
            "field3",
            "field4",
            "field5",
            "field6",
            "field7",
            "_field2",
            "_field5",
            "-field3",
            "-field6",
            "hasfield4",
            "has_field5",
            "has-field6",
            "field4:false",
            "field5:false",
            "field6:false",
            "_field5:false",
            "-field6:false",
        ]
    )
    search_query.receive_requested_lib_info(
        {
            "hasfield1": [],
            "has_field2": [],
            "has-field3": [],
            "hasfield4:false": [],
            "has_field5:false": [],
            "has-field6:false": [],
            "field7:text": [],
        },
        set(
            [
                "field1",
                "field2",
                "field3",
                "field4",
                "field5",
                "field6",
                "field7",
            ]
        ),
    )
    assert not sqmtch(
        search_query,
        fields_text={
            "tags": None,
            "description": "desc",
            "field4": "",
            "field5": "",
            "field6": "",
            "field7": "te_xt_txet",
        },
    )
    assert not sqmtch(
        search_query,
        fields_text={
            "field4": "",
            "field5": "",
            "field6": "",
            "field7": "te_xt_txet",
        },
    )
    assert not sqmtch(
        search_query,
        fields_text={
            "tags": None,
            "description": "desc",
            "field4": None,
            "field5": None,
            "field6": None,
            "field7": None,
        },
    )
    assert not sqmtch(
        search_query,
        fields_text={
            "field4": None,
            "field5": None,
            "field6": None,
            "field7": None,
        },
    )
