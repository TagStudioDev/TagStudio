
"""Search query parsing functionality for use by the src.core.library.Library object in TagStudio"""

import re

from abc import ABC, abstractmethod
from collections import deque

from src.core.enums import SearchMode

"""Container for search relevant entry data received by SearchQuery instances"""
class _EntrySearchableData:
    def __init__(
        self,
        has_fields,
        has_author,
        filename: str,
        tag_ids: list[int]
    ):
        self.has_fields = has_fields
        self.has_author = has_author
        self.filename = filename
        self.tag_ids = tag_ids


class ParseError(Exception):
    """Thrown when the user formats a search incorrectly.
    
    Usually this is due to a bad Boolean operator or an extra closing
    parenthesis.
    
    Currently there is no handling logic to inform the user that
    that they made a mistake. Instead, ParseErrors are caught, and
    problematic Boolean operators are simply ignored during parsing.
    """

class _Token:
    """A raw token from a search query.
    
    kind should be "oparen", "cparen", "binary", "unary", or "tag".
    """
    
    def __init__(self, kind: str, text: str):
        self.kind = kind
        self.text = text
    
    def __str__(self):
        return f"({self.kind}, {self.text})"

class _SynNode(ABC):
    """A single node in a SearchQuery's syntax tree."""
    
    # _ListNodes need to be able to tell when one of their children is a
    # tilde in _ListNode.eval(), so _SynNode has an is_tilde parameter.
    def __init__(self, is_tilde: bool = False) -> None:
        self.is_tilde = is_tilde
    
    # Recursively tests and returns whether the passed entry matches
    # this _SynNode along with any necessary children.
    #
    # The entry parameter must contain any information needed for any
    # _TagNode in the syntax tree to evaluate whether it matches the
    # entry.
    @abstractmethod
    def match(self, entry: _EntrySearchableData) -> bool:
        pass
    # # Implement this at a later date to replace _SynNode.match().
    # #
    # # Recursively compile and return an SQL query to retrieve entries
    # # that match this _SynNode along with any necessary children.
    # @abstractmethod
    # def compile_SQL(self):
    #     pass
    
    # Recursively returns a string representing this _SynNode and all
    # its children. Useful for debugging.
    @abstractmethod
    def __str__(self) -> str:
        pass

class _ListNode(_SynNode):
    """A list type node in a SearchQuery's syntax tree.
    
    The default root node of a SearchQuery is an instance of this class.
    The _SynNodes that hold the terms after an open parenthesis ( in a
    search query string are also instances of this class.
    
    Instances of this class can have an arbitrary number of child nodes,
    (including zero)
    """
    
    # _ListNode instances change how they match entries based on the
    # search_mode.
    def __init__(self, search_mode: SearchMode, children: list[_SynNode]) -> None:
        super().__init__()
        self.search_mode = search_mode
        self.children = children
    
    # The tilde ~ unary operator acts as a flag to indicate whether a
    # _ListNode's child node should be treated as optional or partial
    # instead of being treated as a normal term.
    #
    # If search mode is AND, then a search query like
    # ( t1 ~t2 t3 ~t4 t5 ~t6 ) is evaluated like
    # ( t1 and t3 and t4 and ( t2 or  t4 or  t6 ) )
    # If search mode is OR, then
    # ( t1 ~t2 t3 ~t4 t5 ~t6 ) is evaluated like
    # ( t1 or  t3 or  t4 or  ( t2 and t4 and t6 ) )
    #
    # Note: _ListNode.match() has to keep track of whether tilde ~ is
    # used, otherwise having at least one "optional term" becomes
    # mandatory in AND mode, and otherwise having no "partial match
    # terms" would automatically count as a full match in OR mode.
    def match(self, entry: _EntrySearchableData) -> bool:
        if self.search_mode is SearchMode.AND:
            uses_optional = False
            fulfils_optional = False
            for child in self.children:
                if child.is_tilde:
                    uses_optional = True
                    if child.match(entry):
                        fulfils_optional = True
                elif not child.match(entry):
                    return False
            return not uses_optional or fulfils_optional
        elif self.search_mode is SearchMode.OR:
            uses_partial = False
            fulfils_partial = True
            for child in self.children:
                if child.is_tilde:
                    uses_partial = True
                    if not child.match(entry):
                        fulfils_partial = False
                elif child.match(entry):
                    return True
            return uses_partial and fulfils_partial
    
    def __str__(self) -> str:
        s = "L("
        for child_node in self.children:
            s += str(child_node)
            s += " "
        s = s.removesuffix(" ")
        s += ")"
        return s
class _BinaryNode(_SynNode):
    """A two-input operator node in a SearchQuery's syntax tree.
    
    Instances of this class represent any explicit Boolean operations on
    two inputs in the search query string.
    
    This class has two child nodes to act as the two operands of this
    Boolean operator.
    """
    
    # operator_text is the operator's raw representation in the search
    # query string. This should be one of "and", "^", "&", "&&", "or",
    # "v", "|", "||", "nor", "nand", "xor", "!=", "!==", "xnor", "=",
    # "==", or "===".
    def __init__(self, operator_text, left_operand: _SynNode, right_operand: _SynNode) -> None:
        super().__init__()
        self.operator_text = operator_text
        self.left_operand = left_operand
        self.right_operand = right_operand
    
    def match(self, entry: _EntrySearchableData) -> bool:
        match self.operator_text:
            case "and" | "^" | "&" | "&&":
                return     self.left_operand.match(entry) and     self.right_operand.match(entry)
            case "or" | "v" | "|" | "||":
                return     self.left_operand.match(entry) or      self.right_operand.match(entry)
            case "nor":
                return not self.left_operand.match(entry) and not self.right_operand.match(entry)
            case "nand":
                return not self.left_operand.match(entry) or  not self.right_operand.match(entry)
            case "xor" | "!=" | "!==":
                return     self.left_operand.match(entry) !=      self.right_operand.match(entry)
            case "xnor" | "=" | "==" | "===":
                return     self.left_operand.match(entry) ==      self.right_operand.match(entry)
            case other:
                raise ValueError("self.operator_text must be a valid binary operator."
                               f" self.operator_text was '{self.operator_text}'")
    
    def __str__(self) -> str:
        return f"B({self.left_operand} {self.operator_text} {self.right_operand})"
class _UnaryNode(_SynNode):
    """A one-input operator node in a SearchQuery's syntax tree.
    
    Instances of this class represent either the tilde flag, or
    exclusion operations in the search query string.
    
    This class has one child node.
    """
    
    # operator_text is the operator's raw representation in the search
    # query string. This should be one of "not", "-", "!", or "~".
    def __init__(self, operator_text, operand: _SynNode) -> None:
        super().__init__(is_tilde = operator_text == "~")
        self.operator_text = operator_text
        self.operand = operand
    
    def match(self, entry: _EntrySearchableData) -> bool:
        match self.operator_text:
            case "not" | "-" | "!":
                return not self.operand.match(entry)
            # Tilde ~ acts like the identity operator. ~ does not
            # directly affect the output. Tilde ~ acts as a flag for
            # _ListNode.match() and should not have any other affect.
            case "~":
                return     self.operand.match(entry)
            case other:
                raise ValueError("self.operator_text must be a valid unary operator."
                               f" self.operator_text was '{self.operator_text}'")
    def __str__(self) -> str:
        return f"U({self.operator_text} {self.operand})"
class _TagNode(_SynNode):
    """A tag or metatag leaf node in a SearchQuery's syntax tree.
    
    Instances of this class represent tags and metatags in search query
    strings.
    
    Instances of his class don't have child nodes, but currently their
    id_cluster attribute must be set by SearchQuery before their match()
    method can be called. id_cluster should contain any ids associated
    with the tag and with any child tags it may have.
    """
    
    # token_text should store this tag's raw representation in the
    # search query string. (With any escape character included.)
    def __init__(self, token_text) -> None:
        super().__init__()
        self.token_text = token_text
    
    # search.py is not meant to have direct access to src.core.library,
    # so all relevant data has to be passed into this _TagNode manually.
    # In the future, a compile_SQL method can be used to return an SQL
    # query without any library data being passed at all.
    id_cluster: list[int]
    def match(self, entry: _EntrySearchableData) -> bool:
        match self.token_text:
            case "empty" | "no_fields" | "no-fields" | "nofields":
                return not entry.has_fields
            case "no_author" | "no-author" | "noauthor" | "no_artist" | "no-artist" | "noartist":
                return not entry.has_author
            case "untagged" | "no_tags" | "no-tags" | "notags":
                return not entry.tag_ids
        
        if self.token_text.startswith("filename:"):
            filename = self.token_text.removeprefix("filename:")
            return filename in entry.filename
        if (
               self.token_text.startswith("tag_id:")
            or self.token_text.startswith("tag-id:")
            or self.token_text.startswith("tagid:")
        ):
            tag_id_text = self.token_text.removeprefix("tag")
            tag_id_text = tag_id_text.removeprefix("_")
            tag_id_text = tag_id_text.removeprefix("-")
            tag_id_text = tag_id_text.removeprefix("id:")
            return tag_id_text.isdecimal() and int(tag_id_text) in entry.tag_ids
        
        for tag_id in self.id_cluster:
            # If the ID actually is in the src.core.library.Entry,
            if tag_id in entry.tag_ids:
                return True
        
        return False
    
    def __str__(self) -> str:
        return f"T({self.token_text})"

# The named regex capturing groups each correspond with one kind of
# token, these are oparen, cparen, binary, unary, and tag.
#
# This regex is designed so that exactly one named capturing group will
# capture a token every time the regex matches.
#
# Only intended to be used by SearchQuery._tokenize().
_token_regex = re.compile(
     r"(?P<oparen>[([{])(?:\s|$)"
    r"|(?P<cparen>[)\]}])(?:\s|$)"
    r"|(?P<binary>[&^|v=]|or|\|\||and|&&|nor|nand|xor|!=|!==|xnor|==|===)(?:\s|$)"
    r"|(?P<unary>[-~!]|not(?=\s|$))"
    r"|(?P<tag>\S+)(?:\s|$)"
)
class SearchQuery:
    """This class parses, manages, and interprets search queries.
    
    search.py is not meant to have direct access to src.core.library, so
    so all relevant data has to be passed through to this SearchQuery's
    _TagNodes to be stored while this SearchQuery is evaluated against
    each and every entry in the library.
    
    In the future, a compile_SQL method can be used to return an SQL
    query without having to manage any library data at all. No
    persistence would be needed for that use case and this class could
    be converted entirely into a function.
    """
    
    def __init__(self, query_string, search_mode: SearchMode):
        query_tokens: list[_Token] = self._tokenize(query_string.lower())
        
        # The _tag_text_to_tag_nodes attribute keeps track of the
        # library information that the _TagNodes need, and which tag
        # nodes requested the information. That way this SearchQuery can
        # share requests for the information, and that way this
        # SearchQuery can pass received information to the proper
        # _TagNodes.
        self._tag_text_to_tag_nodes: dict[str, list[_TagNode]] = {}
        self._syntax_root: _ListNode = self._parse_list_node(deque(query_tokens), search_mode)
    
    def _tokenize(self, query_string: str) -> list[_Token]:
        regex_matches = _token_regex.finditer(query_string)
        
        tokens: list[_Token] = []
        for match in regex_matches:
            # Each re.Match contains a dictionary for the named
            # capturing groups in the regex. The keys of the dictionary
            # are the names of the groups. If a particular named group
            # in a re.Match captured a string of text, then the value of
            # the group's dictionary entry is the text that it captured.
            # If the named group captured nothing, then its entry's
            # value is None.
            for match_key, match_value in match.groupdict().items():
                if match_value is not None:
                    tokens.append(_Token(kind=match_key, text=match_value))
                    break
        
        return tokens
    
    # This operation can be done because of an open parenthesis in the
    # token list or in order to parse the root node of the syntax tree.
    # oparens is True to indicate the former case, and False to indicate
    # the latter.
    #
    # The only reason this is an instance method is because
    # self._save_lib_info_request() needs to be called whenever a
    # _TagNode is called.
    def _parse_list_node(
        self,
        tokens: deque[_Token],
        search_mode: SearchMode,
        oparens=False
    ) -> _ListNode:
        children: list[_SynNode] = []
        while tokens:
            token = tokens.popleft()
            match token.kind:
                case "oparen":
                    list_node = self._parse_list_node(tokens, search_mode, oparens=True)
                    children.append(list_node)
                case "cparen":
                    if oparens:
                        return _ListNode(search_mode, children)
                    # Ignore the erroneous token. Do not raise exception.
                    # else:
                    #    cparen_text = token.text
                    #    raise ParseError(f"'{cparen_text}' has no corresponding open parenthesis.")
                case "binary":
                    if not children:
                        continue
                    last_child = children.pop()
                    try:
                        binary_node = self._parse_binary_node(
                            tokens,
                            search_mode,
                            oparens,
                            left_operand=last_child,
                            operator_text=token.text
                        )
                    # Ignore the error. Do not inform the user.
                    except ParseError:
                        children.append(last_child)
                    else:
                        children.append(binary_node)
                case "unary":
                    try:
                        unary_node = self._parse_unary_node(
                            tokens,
                            search_mode,
                            oparens,
                            operator_text=token.text
                        )
                    # Ignore the error. Do not inform the user.
                    except ParseError:
                        pass
                    else:
                        children.append(unary_node)
                case "tag":
                    tag_node = _TagNode(token.text)
                    
                    self._save_lib_info_request(tag_node)
                    
                    children.append(tag_node)
        return _ListNode(search_mode, children)
    # This parse operation should only ever be called with a
    # _parse_list_node operation higher on the call stack. If that
    # operation is waiting for a closed parenthesis, then this operation
    # is erroneous and the closed parenthesis should be returned to the
    # queue. If that operation is not waiting for a closed parenthesis,
    # then this operation can safely consume and ignore closed
    # parentheses. oparens is True to indicate the former case, and
    # False to indicate the latter.
    #
    # The only reason this is an instance method is because
    # self._save_lib_info_request() needs to be called whenever a
    # _TagNode is called.
    def _parse_binary_node(
        self,
        tokens: deque[_Token],
        search_mode: SearchMode,
        oparens: bool,
        operator_text,
        left_operand: _SynNode
    ) -> _BinaryNode:
        while tokens:
            token = tokens.popleft()
            match token.kind:
                case "oparen":
                    list_node = self._parse_list_node(tokens, search_mode, oparens=True)
                    return _BinaryNode(operator_text, left_operand, list_node)
                case "cparen":
                    if oparens:
                        tokens.appendleft(token)
                        cparen_text = token.text
                        raise ParseError(f"'{operator_text}' cannot be followed by"
                                        f" '{cparen_text}'.")
                    # Ignore the erroneous token. Do not raise exception.
                    # else:
                    #    cparen_text = token.text
                    #    raise ParseError(f"'{cparen_text}' has no corresponding open parenthesis.")
                # Ignore the erroneous token. Do not raise exception.
                case "binary":
                    # second_operator_text = token_text
                    # raise ParseError(f"'{operator_text}' cannot be followed by"
                    #                  " '{second_operator_text}'")
                    pass
                case "unary":
                    unary_node = self._parse_unary_node(
                        tokens,
                        search_mode,
                        oparens,
                        operator_text=token.text
                    )
                    return _BinaryNode(operator_text, left_operand, unary_node)
                case "tag":
                    tag_node = _TagNode(token.text)
                    
                    self._save_lib_info_request(tag_node)
                    
                    return _BinaryNode(operator_text, left_operand, tag_node)
        raise ParseError(f"'{operator_text}' is not followed by a second term.")
    # This parse operation should only ever be called with a
    # _parse_list_node operation higher on the call stack. If that
    # operation is waiting for a closed parenthesis, then this operation
    # is erroneous and the closed parenthesis should be returned to the
    # queue. If that operation is not waiting for a closed parenthesis,
    # then this operation can safely consume and ignore closed
    # parentheses. oparens is True to indicate the former case, and
    # False to indicate the latter.
    #
    # The only reason this is an instance method is because
    # self._save_lib_info_request() needs to be called whenever a
    # _TagNode is called.
    def _parse_unary_node(
        self,
        tokens: deque[_Token],
        search_mode: SearchMode,
        oparens: bool,
        operator_text: str
    ) -> _UnaryNode:
        while tokens:
            token = tokens.popleft()
            match token.kind:
                case "oparen":
                    list_node = self._parse_list_node(tokens, search_mode, oparens=True)
                    return _UnaryNode(operator_text, list_node)
                case "cparen":
                    if oparens:
                        tokens.appendleft(token)
                        cparen_text = token.text
                        raise ParseError(f"'{operator_text}' cannot be followed by"
                                        f" '{cparen_text}'.")
                    # Ignore the erroneous token. Do not raise exception.
                    # else:
                    #    cparen_text = token.text
                    #    raise ParseError(f"'{cparen_text}' has no corresponding open parenthesis.")
                case "binary":
                    tokens.appendleft(token)
                    second_operator_text = token.text
                    raise ParseError(f"'{operator_text}' cannot be followed by"
                                    f" '{second_operator_text}'.")
                case "unary":
                    unary_node = self._parse_unary_node(
                        tokens,
                        search_mode,
                        oparens,
                        operator_text=token.text
                    )
                    return _UnaryNode(operator_text=operator_text, operand=unary_node)
                case "tag":
                    tag_node = _TagNode(token.text)
                    
                    self._save_lib_info_request(tag_node)
                    
                    return _UnaryNode(operator_text, tag_node)
        raise ParseError(f"'{operator_text}' is not followed by a term.")
    
    # Assumes the token_text is for a regular tag and not a metatag.
    # The reply will be ignored anyway if it is.
    def _save_lib_info_request(self, tag_node: _TagNode) -> None:
        # These escape characters prevent the syntax node from being
        # interpreted as an open parenthesis, a closed parenthesis, a
        # unary operator, a binary operator, or a metatag, but this code
        # ensures that an escape character it will not interfere with it
        # as a tag.
        if tag_node.token_text.startswith("/"):
            tag_text = tag_node.token_text.removeprefix("/")
        else:
            tag_text = tag_node.token_text.removeprefix("\\")
        # Multiple tag nodes can be associated with the same tag text.
        if tag_text not in self._tag_text_to_tag_nodes:
            self._tag_text_to_tag_nodes[tag_text] = []
        self._tag_text_to_tag_nodes[tag_text].append(tag_node)
    def share_tag_requests(self) -> list[str]:
        return list(self._tag_text_to_tag_nodes.keys())
    def receive_requested_lib_info(self, tag_text_to_id_clusters: dict[str, list[int]]):
        for tag_text, id_cluster in tag_text_to_id_clusters.items():
            for tag_node in self._tag_text_to_tag_nodes[tag_text]:
                tag_node.id_cluster = id_cluster
    
    def match_entry(
        self,
        has_fields,
        has_author,
        filename: str,
        tag_ids: list[int]
    ):
        return self._syntax_root.match(_EntrySearchableData(
            has_fields,
            has_author,
            filename,
            tag_ids
        ))
    
    def __str__(self):
        return str(self._syntax_root)