from typing import TypedDict

class Json_Libary(TypedDict("",{"ts-version":str})):
    #"ts-version": str
    tags: "list[Json_Tag]"
    collations: "list[Json_Collation]"
    fields: list #TODO
    macros: "list[Json_Macro]"
    entries: "list[Json_Entry]"

class Json_Base(TypedDict):
    id: int

class Json_Tag(Json_Base,total=False):
    name: str
    aliases: list[str]
    color: str
    shorthand: str
    subtag_ids: list[int]

class Json_Collation(Json_Base,total=False):
    title: str
    e_ids_and_pages: list[list[int]]
    sort_order: str
    cover_id: int

class Json_Entry(Json_Base,total=False):
    filename: str
    path: str
    fields: list[dict] #TODO

class Json_Macro(Json_Base,total=False):
    ... #TODO