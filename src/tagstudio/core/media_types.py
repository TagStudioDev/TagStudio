# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: MIT


import structlog

from tagstudio.core.utils.sanitized_attr import SanitizedAttr

logger = structlog.get_logger(__name__)


class MediaType:
    """A complete description of a media type and its uses."""

    def __init__(self, exts: str | list[str], contexts: str | list[str]) -> None:
        self.exts: set[str]
        self.contexts: set[str]

        if isinstance(exts, str):
            self.exts = set([exts])
        else:
            self.exts = set(exts)

        if isinstance(contexts, str):
            self.contexts = set([contexts])
        else:
            self.contexts = set(contexts)


class MediaTypeGroup:
    def __init__(self, name_key: str, types: list[MediaType]) -> None:
        self.context_sets: dict[str, set[str]] = {}
        self.name_aliases: list[str] = []
        self.name_key = name_key
        self.types: list[MediaType] = []
        self.add_types(types)

    def add_types(self, types: list[MediaType]) -> None:
        for type_ in types:
            updated_types: set[MediaType] = set()
            for existing_type in self.types:
                # If there's any overlap between the extensions, it's the same type
                if not existing_type.exts.isdisjoint(type_.exts):
                    existing_type.contexts |= type_.contexts
                    existing_type.exts |= type_.exts
                    updated_types.add(type_)
            if type_ not in updated_types:
                self.types.append(type_)

            contexts_ = [type_.contexts] if isinstance(type_.contexts, str) else type_.contexts
            for context in contexts_:
                if self.context_sets.get(context) is None:
                    self.context_sets[context] = set()
                for ext in type_.exts:
                    self.context_sets[context].add(ext)

    def contains(self, ext: str, context: str) -> bool:
        equivalent_exts = MediaTypes.equivalent_exts.get(ext) or [ext]
        return any(e in self.context_sets.get(context, []) for e in equivalent_exts)


class MediaTypes(metaclass=SanitizedAttr):
    _chained_groups: dict[str, set[str]] = {}
    _name_to_key_map: dict[str, str] = {}
    all_groups: list[MediaTypeGroup] = []
    equivalent_exts: dict[str, set[str]] = {}

    @classmethod
    def add_name_aliases(cls, group_key: str, names: str | list[str]) -> None:
        """Adds one or more aliases for the proper name of a group.

        If a group with the group_key does not exist, it will be created.

        For example, "Adobe" and "Adobe Photoshop" would be proper group names.
        """
        group = getattr(MediaTypes, group_key, None)
        if group is None:
            cls.register(group_key, [], [])
            group = getattr(MediaTypes, group_key, None)

        if not isinstance(group, MediaTypeGroup):
            return

        if isinstance(names, str):
            names = [names]
        for name in names:
            group.name_aliases.append(name)
            # Map the name and common variants of the name to the group key.
            cls._name_to_key_map[name] = group_key
            cls._name_to_key_map[name.lower()] = group_key
            cls._name_to_key_map[
                name.lower().replace(" ", "").replace("-", "").replace("_", "")
            ] = group_key
            cls._name_to_key_map[name.replace(" ", "").replace("-", "").replace("_", "")] = (
                group_key
            )

    @classmethod
    def chain_group(cls, parent_group: str, child_groups: str | list[str]) -> None:
        """Chain groups so when a type is added to a child group it's also added to a parent group.

        Args:
            parent_group (str): The group that will also update whenever a child group is updated.
                If the group doesn't exist, it will be created.
            child_groups (str | list[str]): Groups that tell a parent group to update as well.
                If the group doesn't exist, it will be created.
        """
        if isinstance(child_groups, str):
            child_groups = [child_groups]

        # If the groups don't exist, register it.
        if getattr(MediaTypes, parent_group.replace(".", "_"), None) is None:
            cls.register(parent_group, [], [])
        for child_group in child_groups:
            if getattr(MediaTypes, child_group.replace(".", "_"), None) is None:
                cls.register(child_group, [], [])

        if cls._chained_groups.get(parent_group) is None:
            cls._chained_groups[parent_group] = set()

        for c_group in child_groups:
            cls._chained_groups[parent_group].add(c_group)

    @classmethod
    def find(cls, ext: str, context: str) -> list[MediaTypeGroup]:
        groups: list[MediaTypeGroup] = []
        for group in cls.all_groups:
            for type_ in group.types:
                equivalent_exts = cls.equivalent_exts.get(ext) or [ext]
                for e in equivalent_exts:
                    if e in type_.exts and context in type_.contexts:
                        groups.append(group)
                        break

        return groups

    @classmethod
    def contains(cls, group_name: str, ext: str, context: str) -> bool:
        """A passthrough method for using `MediaTypeGroup.contains()` given a group name.

        If the group does not exist, this will return False. If ensuring the group exists is
        important, get the group directly with from MediaTypes with (e.g. with `getattr()`).
        """
        group: MediaTypeGroup | None = getattr(MediaTypes, group_name, None)
        return group.contains(ext, context) if group else False

    @classmethod
    def get_group_key_from_name(
        cls, name: str, case_sensitive: bool = True, ignore_whitespace: bool = False
    ) -> str | None:
        """Attempt to return a group key given a proper name for the group."""
        if not case_sensitive:
            name = name.lower()
        if ignore_whitespace:
            name = name.replace(" ", "").replace("-", "").replace("_", "")
        return cls._name_to_key_map.get(name)

    @classmethod
    def register(cls, name: str, ext: list[str] | str, contexts: list[str] | str) -> None:
        # Sanitize and homogenize arguments
        attr_name = name.replace(".", "_")
        if isinstance(ext, str):
            ext = [ext]
        if isinstance(contexts, str):
            contexts = [contexts]

        # Check for existing group or create new one
        group = getattr(MediaTypes, attr_name, None)
        assert isinstance(group, MediaTypeGroup) or group is None

        if group is None:
            logger.debug(f"[MediaTypes] Creating Group: '{attr_name}' with {ext}")
            group = MediaTypeGroup(name, [])
            group.add_types([MediaType(ext, contexts)])
            setattr(MediaTypes, attr_name, group)
            cls.all_groups.append(group)
        else:
            logger.debug(f"[MediaTypes] Amending Group: '{attr_name}' with {ext}")
            group.add_types([MediaType(ext, contexts)])

        # Store any file extention equivalents
        if len(ext) > 1:
            for e in ext:
                existing_ext = cls.equivalent_exts.get(e)
                if existing_ext is None:
                    cls.equivalent_exts[e] = set(ext)

        # Create any chained groups from dot notations (e.g. "adobe.photoshop")
        name_parts = name.split(".")
        for i in range(1, len(name_parts)):
            parent = ".".join(name_parts[:i])
            child = ".".join(name_parts[: i + 1])
            cls.chain_group(parent, [child])

        # Update any chained groups
        chained_groups: set[str] = set()
        for k, v in cls._chained_groups.items():
            if name in v:
                chained_groups.add(k)

        if chained_groups:
            for c_name in chained_groups:
                cls.register(c_name, ext, contexts)

    @classmethod
    def get_equivalent_exts(cls, ext: str) -> set[str]:
        """Return a set of equivalent file extensions given an extention, including itself.

        Args:
            ext (str): The file extension, including leading dot.
        """
        return cls.equivalent_exts.get(ext, {ext})
