# Copyright (C) 2025 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

import json
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING, Any, override

import structlog
import toml
from wcmatch import glob

if TYPE_CHECKING:
    from tagstudio.core.library.alchemy.library import Library
    from tagstudio.core.library.alchemy.models import Tag

logger = structlog.get_logger(__name__)

SCHEMA_VERSION = "schema_version"
TRIGGERS = "triggers"
ACTION = "action"

SOURCE_LOCATION = "source_location"
SOURCE_FILER = "source_filters"
SOURCE_FORMAT = "source_format"
FILENAME_PLACEHOLDER = "{filename}"
EXT_PLACEHOLDER = "{ext}"
TEMPLATE = "template"

SOURCE_TYPE = "source_type"
TS_TYPE = "ts_type"
NAME = "name"

VALUE = "value"
TAGS = "tags"
TEXT_LINE = "text_line"
TEXT_BOX = "text_box"
DATETIME = "datetime"

PREFIX = "prefix"
DELIMITER = "delimiter"
STRICT = "strict"
USE_CONTEXT = "use_context"
ON_MISSING = "on_missing"

JSON = "json"
XMP = "xmp"
EXIF = "exif"
ID3 = "id3"

MAP = "map"
INVERSE_MAP = "inverse_map"


class Actions(StrEnum):
    IMPORT_DATA = "import_data"
    ADD_DATA = "add_data"


class OnMissing(StrEnum):
    PROMPT = "prompt"
    CREATE = "create"
    SKIP = "skip"


class Instruction:
    def __init__(self) -> None:
        pass


class AddFieldInstruction(Instruction):
    def __init__(self, content, name: _FieldID, field_type: str) -> None:
        super().__init__()
        self.content = content
        self.name = name
        self.type = field_type

    @override
    def __str__(self) -> str:
        return str(self.content)


class AddTagInstruction(Instruction):
    def __init__(
        self,
        tag_strings: list[str],
        use_context: bool = True,
        strict: bool = False,
        on_missing: str = OnMissing.SKIP,
        prefix: str = "",
    ) -> None:
        super().__init__()
        self.tag_strings = tag_strings
        self.use_context = use_context
        self.strict = strict
        self.on_missing = on_missing
        self.prefix = prefix

    @override
    def __str__(self) -> str:
        return str(self.tag_strings)


def parse_macro_file(
    macro_path: Path,
    filepath: Path,
) -> list[Instruction]:
    """Parse a macro file and return a list of actions for TagStudio to perform.

    Args:
        macro_path (Path): The full path of the macro file.
        filepath (Path): The filepath associated with Entry being operated upon.
    """
    results: list[Instruction] = []
    logger.info("[MacroParser] Parsing Macro", macro_path=macro_path, filepath=filepath)

    if not macro_path.exists():
        logger.error("[MacroParser] Macro path does not exist", macro_path=macro_path)
        return results

    if not macro_path.exists():
        logger.error("[MacroParser] Filepath does not exist", filepath=filepath)
        return results

    with open(macro_path) as f:
        try:
            macro = toml.load(f)
        except toml.TomlDecodeError as e:
            logger.error(
                "[MacroParser] Could not parse macro",
                path=macro_path,
                error=e,
            )
            return results

    logger.info(macro)

    # Check Schema Version
    schema_ver = macro.get(SCHEMA_VERSION, 0)
    if not isinstance(schema_ver, int):
        logger.error(
            f"[MacroParser] Incorrect type for {SCHEMA_VERSION}, expected int",
            schema_ver=schema_ver,
        )
        return results

    if schema_ver != 1:
        logger.error(f"[MacroParser] Unsupported Schema Version: {schema_ver}")
        return results

    logger.info(f"[MacroParser] Schema Version: {schema_ver}")

    # Load Triggers
    triggers = macro[TRIGGERS]
    if not isinstance(triggers, list):
        logger.error(
            f"[MacroParser] Incorrect type for {TRIGGERS}, expected list", triggers=triggers
        )

    # Parse each action table
    for table_key in macro:
        if table_key in {SCHEMA_VERSION, TRIGGERS}:
            continue

        logger.info("[MacroParser] Parsing Table", table_key=table_key)
        table: dict[str, Any] = macro[table_key]
        logger.info(table.keys())

        # TODO: Replace with table conditionals
        source_filters: list[str] = table.get(SOURCE_FILER, [])
        conditions_met: bool = False
        if not source_filters:
            logger.info('[MacroParser] No "{SOURCE_FILER}" provided')
        else:
            for filter_ in source_filters:
                if glob.globmatch(filepath, filter_, flags=glob.GLOBSTAR):
                    logger.info(
                        f"[MacroParser] [{table_key}] "
                        f'{SOURCE_FILER}" Met filter requirement: {filter_}'
                    )
                    conditions_met = True

        if not conditions_met:
            logger.warning(
                f"[MacroParser] [{table_key}] File didn't meet any path filter requirement",
                filters=source_filters,
                filepath=filepath,
            )
            continue

        action: str = table.get(ACTION, "")
        logger.info(f'[MacroParser] [{table_key}] "{ACTION}": {action}')

        if action == Actions.IMPORT_DATA:
            results.extend(_import_data(table, table_key, filepath))
        elif action == Actions.ADD_DATA:
            results.extend(_add_data(table))

    logger.info(results)
    return results


def _import_data(table: dict[str, Any], table_key: str, filepath: Path) -> list[Instruction]:
    """Process an import_data instruction and return a list of DataResults.

    Importing data refers to importing data from a source external to TagStudio or any macro.
    """
    results: list[Instruction] = []

    source_format: str = str(table.get(SOURCE_FORMAT, ""))
    if not source_format:
        logger.error('[MacroParser] Parser Error: No "{SOURCE_FORMAT}" provided for table')
    logger.info(f'[MacroParser] [{table_key}] "{SOURCE_FORMAT}": {source_format}')

    raw_source_location = str(table.get(SOURCE_LOCATION, ""))
    if FILENAME_PLACEHOLDER in raw_source_location:
        # logger.info(f"[MacroParser] Filename placeholder detected: {raw_source_location}")
        raw_source_location = raw_source_location.replace(FILENAME_PLACEHOLDER, str(filepath.stem))

    if EXT_PLACEHOLDER in raw_source_location:
        # logger.info(f"[MacroParser] File extension placeholder detected: {raw_source_location}")
        # TODO: Make work with files that have multiple suffixes, like .tar.gz
        raw_source_location = raw_source_location.replace(
            EXT_PLACEHOLDER,
            str(filepath.suffix)[1:],  # Remove leading "."
        )

    if not raw_source_location.startswith(("/", "~")):
        # The source location must be relative to the given filepath
        source_location = filepath.parent / Path(raw_source_location)
    else:
        source_location = Path(raw_source_location)

    logger.info(f'[MacroParser] [{table_key}] "{SOURCE_LOCATION}": {source_location}')

    if not source_location.exists():
        logger.error(
            "[MacroParser] Sidecar filepath does not exist", source_location=source_location
        )
        return results

    if source_format.lower() in JSON:
        logger.info("[MacroParser] Parsing JSON sidecar file", sidecar_path=source_location)
        with open(source_location, encoding="utf8") as f:
            json_dump = json.load(f)
        if not json_dump:
            logger.warning("[MacroParser] Empty JSON sidecar file")
            return results
        logger.info(json_dump.items())

        for key, table_value in table.items():
            objects: list[dict[str, Any] | str] = []
            content_value = ""
            if isinstance(table_value, list):
                objects = table_value
            else:
                objects.append(table_value)
            for obj in objects:
                if not isinstance(obj, dict):
                    continue
                ts_type: str = str(obj.get(TS_TYPE, ""))
                if not ts_type:
                    logger.warning(
                        f'[MacroParser] [{table_key}] No "{TS_TYPE}" key provided, skipping'
                    )
                    continue

                if key in json_dump:
                    json_value = json_dump.get(key)
                    logger.info(
                        f"[MacroParser] [{table_key}] Parsing JSON sidecar key",
                        key=key,
                        table_value=obj,
                        json_value=json_value,
                    )
                    content_value = json_value

                    if not json_value or isinstance(json_value, str) and not json_value.strip():
                        logger.warning(
                            f"[MacroParser] [{table_key}] Value for key was empty, skipping"
                        )
                        continue

                elif key == TEMPLATE:
                    template: str = str(obj.get(TEMPLATE, ""))
                    logger.info(f"[MacroParser] [{table_key}] Filling template", template=template)
                    if not template:
                        logger.warning(f"[MacroParser] [{table_key}] Empty template, skipping")
                        continue
                    for k in json_dump:
                        template = _fill_template(template, json_dump, k)
                    logger.info(f"[MacroParser] [{table_key}] Template filled!", template=template)
                    content_value = template

                else:
                    continue

                # TODO: Determine if the source_type is even really ever needed
                # source_type: str = str(tab_value.get(SOURCE_TYPE, ""))

                str_name: str = str(obj.get(NAME, _FieldID.NOTES.name))
                name: _FieldID = _FieldID.NOTES
                for fid in _FieldID:
                    field_id = str_name.upper().replace(" ", "_")
                    if field_id == fid.name:
                        name = fid
                        continue

                if ts_type == TAGS:
                    use_context: bool = bool(obj.get(USE_CONTEXT, False))
                    on_missing: str = str(obj.get(ON_MISSING, OnMissing.SKIP))
                    strict: bool = bool(obj.get(STRICT, False))
                    delimiter: str = ""

                    tag_strings: list[str] = []
                    # Tags are part of a single string
                    if isinstance(content_value, str):
                        delimiter = str(obj.get(DELIMITER, ""))
                        if delimiter:
                            # Split string based on given delimiter
                            tag_strings = content_value.split(delimiter)
                        else:
                            # If no delimiter is provided, assume the string is a single tag
                            tag_strings.append(content_value)
                    else:
                        tag_strings = content_value

                    # Remove a prefix (if given) from all tags strings (if any)
                    prefix = str(obj.get(PREFIX, ""))
                    if prefix:
                        tag_strings = [t.lstrip(prefix) for t in tag_strings]

                    # Swap any mapped tags for their new tag values
                    tag_map: dict[str, str] = obj.get(MAP, {})
                    mapped: list[str] = []
                    if tag_map:
                        for map_key, map_value in tag_map.items():
                            if map_key in tag_strings:
                                logger.info("[MacroParser] Mapping tag", old=map_key, new=map_value)
                                if isinstance(map_value, list):
                                    mapped.extend(map_value)
                                else:
                                    mapped.append(map_value)
                                tag_strings.remove(map_key)
                        tag_strings.extend(mapped)

                    logger.info("[MacroParser] Found tags", tag_strings=tag_strings)
                    results.append(
                        AddTagInstruction(
                            tag_strings=tag_strings,
                            use_context=use_context,
                            strict=strict,
                            on_missing=on_missing,
                            prefix="",
                        )
                    )

                elif ts_type in (TEXT_LINE, TEXT_BOX, DATETIME):
                    results.append(
                        AddFieldInstruction(content=content_value, name=name, field_type=ts_type)
                    )
                else:
                    logger.error('[MacroParser] [{table_key}] Unknown "{TS_TYPE}"', type=ts_type)

    return results


def _add_data(table: dict[str, Any]) -> list[Instruction]:
    """Process an add_data instruction and return a list of DataResults.

    Adding data refers to adding data defined inside a TagStudio macro, not from an external source.
    """
    results: list[Instruction] = []
    logger.error(table)
    for table_value in table.values():
        objects: list[dict[str, Any] | str] = []
        if isinstance(table_value, list):
            objects = table_value
        else:
            objects.append(table_value)
        for obj in objects:
            if not isinstance(obj, dict):
                continue
            ts_type = obj.get(TS_TYPE, "")
            if ts_type == TAGS:
                tag_strings: list[str] = obj.get(VALUE, [])
                logger.error(tag_strings)
                results.append(
                    AddTagInstruction(
                        tag_strings=tag_strings,
                        use_context=False,
                    )
                )
            elif ts_type in (TEXT_LINE, TEXT_BOX, DATETIME):
                str_name: str = str(obj.get(NAME, _FieldID.NOTES.name))
                name: _FieldID = _FieldID.NOTES
                for fid in _FieldID:
                    field_id = str_name.upper().replace(" ", "_")
                    if field_id == fid.name:
                        name = fid
                        continue

                content_value: str = str(obj.get(VALUE, ""))
                results.append(
                    AddFieldInstruction(content=content_value, name=name, field_type=ts_type)
                )

    return results


def _fill_template(
    template: str, table: dict[str, Any], table_key: str, template_key: str = ""
) -> str:
    """Replaces placeholder keys in a string with the value from that table.

    Args:
        template (str): The string containing placeholder keys.
            Key names should be surrounded in curly braces. (e.g. "{key}").
            Nested keys should be accessed with square bracket syntax. (e.g. "{key[nested_key]}").
        table (dict[str, Any]): The table to lookup values from.
        table_key (str): The key to search for in the template and access the table with.
        template_key (str): Similar to table_key, but is not used for accessing the table and
            is instead used for representing the template key syntax for nested keys.
            Used in recursive calls.
    """
    key = template_key or table_key
    value = table.get(table_key, "")

    if isinstance(value, dict):
        for v in value:
            normalized_key: str = f"{key}[{str(v)}]"
            template.replace(f"{{{normalized_key}}}", f"{{{str(v)}}}")
            template = _fill_template(template, value, str(v), normalized_key)

    value = str(value)
    return template.replace(f"{{{key}}}", f"{value}")


def exec_instructions(library: "Library", entry_id: int, results: list[Instruction]) -> None:
    for result in results:
        if isinstance(result, AddTagInstruction):
            _exec_add_tag(library, entry_id, result)
        elif isinstance(result, AddFieldInstruction):
            _exec_add_field(library, entry_id, result)


def _exec_add_tag(library: "Library", entry_id: int, result: AddTagInstruction):
    tag_ids: set[int] = set()
    for string in result.tag_strings:
        if not string.strip():
            continue
        string = string.replace("_", " ")
        base_and_parent = string.split("(")
        parent = ""
        base = base_and_parent[0].strip(" ")
        parent_results: list[int] = []
        if len(base_and_parent) > 1:
            parent = base_and_parent[1].split(")")[0]
            r: list[set[Tag]] = library.search_tags(name=parent, limit=-1)
            if len(r) > 0:
                parent_results = [t.id for t in r[0]]
        # NOTE: The following code overlaps with update_tags() in tag_search.py
        # Sort and prioritize the results
        tag_results: list[set[Tag]] = library.search_tags(name=base, limit=-1)
        results_0 = list(tag_results[0])
        results_0.sort(key=lambda tag: tag.name.lower())
        results_1 = list(tag_results[1])
        results_1.sort(key=lambda tag: tag.name.lower())
        raw_results = list(results_0 + results_1)
        priority_results: set[Tag] = set()

        for tag in raw_results:
            if tag.name.lower().startswith(base.strip().lower()):
                priority_results.add(tag)
        all_results = sorted(list(priority_results), key=lambda tag: len(tag.name)) + [
            r for r in raw_results if r not in priority_results
        ]

        if parent and parent_results:
            filtered_parents: list[Tag] = []
            for tag in all_results:
                for p_id in tag.parent_ids:
                    if p_id in parent_results:
                        filtered_parents.append(tag)
                        break
            all_results = [t for t in all_results if t in filtered_parents]

        final_tag: Tag | None = None
        if len(all_results) > 0:
            final_tag = all_results[0]
        if final_tag:
            tag_ids.add(final_tag.id)

    if not tag_ids:
        return

    library.add_tags_to_entries(entry_id, tag_ids)


def _exec_add_field(library: "Library", entry_id: int, result: AddFieldInstruction):
    library.add_field_to_entry(
        entry_id, field_id=result.name, value=result.content, skip_on_exists=True
    )
