from typing import TypedDict
from typing_extensions import NotRequired


class JsonLibary(TypedDict("", {"ts-version": str})):
    # "ts-version": str
    tags: "list[JsonTag]"
    collations: "list[JsonCollation]"
    fields: list  # TODO
    macros: "list[JsonMacro]"
    entries: "list[JsonEntry]"
    ext_list: list[str]
    is_exclude_list: bool
    ignored_extensions: NotRequired[list[str]]  # deprecated


class JsonBase(TypedDict):
    id: int


class JsonTag(JsonBase, total=False):
    name: str
    aliases: list[str]
    color: str
    shorthand: str
    subtag_ids: list[int]


class JsonCollation(JsonBase, total=False):
    title: str
    e_ids_and_pages: list[list[int]]
    sort_order: str
    cover_id: int


class JsonEntry(JsonBase, total=False):
    filename: str
    path: str
    fields: list[dict]  # TODO


class JsonMacro(JsonBase, total=False): ...  # TODO
