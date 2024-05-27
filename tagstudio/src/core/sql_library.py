# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

"""The Library object and related methods for TagStudio."""

import glob
import hashlib
import json
import logging
import os
import sqlite3
import sys
import time
import traceback
import xml.etree.ElementTree as ET
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, Protocol, Generator

import ujson

from src.core.json_typing import JsonCollation, JsonEntry, JsonLibary, JsonTag
from src.core.constants import (
    VERSION,
    TS_FOLDER_NAME,
    BACKUP_FOLDER_NAME,
    COLLAGE_FOLDER_NAME,
    TEXT_FIELDS,
)

from src.core.utils.str import strip_punctuation
from src.core.utils.web import strip_web_protocol

TYPE = ["file", "meta", "alt", "mask"]


# RESULT_TYPE = Enum('Result', ['ENTRY', 'COLLATION', 'TAG_GROUP'])
class ItemType(Enum):
    ENTRY = 0
    COLLATION = 1
    TAG_GROUP = 2


logging.basicConfig(format="%(message)s", level=logging.INFO)


class DataSource(Protocol):
    """Protocol for a library data source.
    This can be a SQLite database, a JSON file, or any other data source."""

    def get_locations(self) -> list["Location"]: ...

    def get_location(self, location_id: int) -> list["Location"]: ...

    def get_entries(self) -> dict[int, "Entry"]: ...

    def get_entry(self, entry_id: int) -> "Entry": ...

    def remove_entry(self, entry_id: int) -> None: ...

    def remove_entries(self, entry_ids: list[int]) -> None: ...

    def get_tags(self) -> dict[int, "Tag"]: ...

    def get_tag(self, tag_id: int) -> "Tag": ...

    def get_groups(self) -> list["Tag"]:
        """Return a list of title tags for the groups in the data source."""
        ...

    def get_group(self, tag: "Tag") -> list["Group"]:
        """Return the group with a given title tag."""
        ...

    def get_entry_attributes(
        self, entry_id: int
    ) -> dict[int, str | float | datetime | list[int]]: ...

    def get_tag_relations(
        self, tag_id: int, find_parents: bool = True
    ) -> list[int]: ...

    def get_aliases(self, tag_id: int) -> list[str]: ...

    def get_version(self) -> tuple[int, int, int]:
        """Should return the version of the data source in the format Major.Minor.Patch"""
        ...

    def save(self, path: Optional[Path] = None) -> int:
        """Saves the library to the given path."""
        ...


class SqliteLibrary:
    def __init__(self, db: sqlite3.Connection) -> None:
        self.db = db

    def get_locations(self) -> list["Location"]:
        locations = self.db.execute("SELECT (id, path, name) FROM location;").fetchall()
        return [Location(*loc) for loc in locations]

    def get_location(self, location_id: int) -> "Location":
        location = self.db.execute(
            "SELECT (id, path, name) FROM location WHERE id = ?;", (location_id,)
        )
        return Location(*location.fetchone())

    def get_entries(self) -> list["Entry"]:
        # This function really shouldn't exist, entries should be loaded as needed for searches
        # and or the first screen full when loading a library
        entries = self.db.execute("SELECT (id, path, location) FROM entry;").fetchall()
        return [Entry(*entry) for entry in entries]

    def get_entry(self, entry_id: int) -> "Entry":
        """Get an entry by its ID.
        raises ValueError if the entry is not found.
        """
        entry = self.db.execute(
            "SELECT (id, path, location) FROM entry WHERE id = ?;", (entry_id,)
        ).fetchone()
        if not entry:
            raise ValueError(
                f"[SQLite Library] [get_entry] Entry {entry_id} not found in database."
            )
        return Entry(*entry.fetchone())

    def remove_entry(self, entry_id: int) -> None:
        self.db.execute("DELETE FROM entry WHERE id = ?;", (entry_id,))

    def remove_entries(self, entry_ids: list[int]) -> None:
        sql_entry_ids = [(entry_id,) for entry_id in entry_ids]
        self.db.executemany("DELETE FROM entry WHERE id = ?;", sql_entry_ids)

    def get_attributes(
        self, entry_id: int
    ) -> dict[int, str | float | datetime | list[int]]:
        attributes = self.db.execute(
            "SELECT (title_tag, tag, text, number, datetime) FROM entry_attribute WHERE entry = ?;",
            (entry_id,),
        ).fetchall()
        # Author: "John Smith",
        # Description: "This is an example",
        # Meta_Tag group contains the favorite tag id (default 33)
        # {2: 'John Smith', 6: 'This is an example',  10: [33]}
        entry_attributes = {}
        for attr in attributes:
            title_tag, tag, text, number, dt = attr
            if text is not None:
                entry_attributes[title_tag] = text
            elif number is not None:
                entry_attributes[title_tag] = number
            elif dt is not None:
                entry_attributes[title_tag] = datetime.fromisoformat(dt)
            elif tag is not None:
                # In order for this to work with the current schema,
                # the title_tag plays the opposite role as normal this limits tags to being assigned once
                # rather than only allowing tag_groups to have a single child
                if not entry_attributes[tag]:
                    entry_attributes[tag] = []
                entry_attributes[tag].append(title_tag)
            else:
                logging.error("[Sqlite Library] [get_attr] How did you get here?")
        return entry_attributes

    def get_tags(self) -> dict[int, "Tag"]:
        tags = self.db.execute(
            "SELECT (id, name, shorthand, color) FROM tag;"
        ).fetchall()
        return {tag[0]: Tag(*tag) for tag in tags}

    def get_tag(self, tag_id: int) -> "Tag":
        tag = self.db.execute(
            "SELECT (id, name, shorthand, color) FROM tag WHERE id = ?;", (tag_id,)
        )
        return Tag(*tag.fetchone())

    def get_tag_relations(self, tag_id: int, find_parents: bool = True) -> list[int]:
        if find_parents:
            relations = self.db.execute(
                "SELECT (parent) FROM tag_relation WHERE tag = ?;", (tag_id,)
            ).fetchall()
        else:
            relations = self.db.execute(
                "SELECT (tag) FROM tag_relation WHERE parent = ?;", (tag_id,)
            ).fetchall()
        return [rel[0] for rel in relations]

    def get_aliases(self, tag_id: int) -> list[str]:
        aliases = self.db.execute(
            "SELECT (name) FROM alias WHERE tag = ?;", (tag_id,)
        ).fetchall()
        return [alias[0] for alias in aliases]

    def get_version(self) -> tuple[int, int, int]:
        # PRAGMA user_version is only able to store an unsigned int
        database_versions = {1: (9, 2, 0)}
        pragma_version = self.db.execute("PRAGMA user_version").fetchone()
        return database_versions.get(pragma_version[0], (0, 0, 0))

    def save(self, path: Optional[Path] = None) -> int:
        """Save a library, either to the current location or to a new location.
        Returns 0 on success, 1 on failure."""
        self.db.commit()

        if path:
            db_id, db_name, db_location = self.db.execute(
                "PRAGMA database_list"
            ).fetchone()
            if db_location == str(path):
                return 0
            else:
                try:
                    backup_db = sqlite3.connect(path)
                    self.db.backup(backup_db)
                    backup_db.commit()
                    backup_db.close()
                except sqlite3.Error as e:
                    logging.error(f"[Sqlite Library] [Save] {e}")
                    return 1
                return 0


# =============================================================================
# Memory Cache Objects to avoid slowing down due to DB calls
# =============================================================================
class Location:
    """A Library Location Object. Used to allow multiple directories within a single library."""

    def __init__(self, loc_id: int, path: Path, name: str = None) -> None:
        self.location_id = loc_id
        self.path = path
        self.name = name

    def __repr__(self):
        return f"Location {self.location_id}: {self.path=}, {self.name=}"

    def __str__(self):
        return f"Location {self.name} @ {self.path}"

    def to_json(self):
        return {"id": self.location_id, "path": str(self.path), "name": self.name}


class Entry:
    """A Library Entry Object. Referenced by ID."""

    def __init__(self, entry_id: int, path: Path, location: Location) -> None:
        # Required Fields ======================================================
        self.entry_id = entry_id
        self.location = location  # TODO: replace int
        self.path = path
        self.hash = self.update_hash()
        self._attributes: Optional[dict[int, str | float | datetime | list[int]]] = None

    @property
    def fields(self) -> list[int] | None:
        if self._attributes is None:
            logging.warning(
                f"[Entry] {self.entry_id} Fields accessed before attributes loaded"
            )
            return None
        return list(self._attributes.keys())

    @property
    def tags(self) -> list[int] | None:
        if self._attributes is None:
            logging.warning(
                f"[Entry] {self.entry_id} Tags accessed before attributes loaded"
            )
            return None
        contained_tags = []
        for tag, value in self._attributes.items():
            # All fields are tags
            contained_tags.append(tag)
            if isinstance(value, list):
                # values that are lists are tag boxes so add those tags also
                contained_tags += value
        return contained_tags

    def set_attributes(self, attributes: dict[int, str | float | datetime | list[int]]):
        """Sets the attributes of the Entry.
        Should only be called by the Library.
        """
        self._attributes = attributes

    def update_hash(self) -> bytes:
        # TODO: Choose and implement a hashing algorithm (hashlib.SHA1?)
        return b""

    def __str__(self) -> str:
        return f"Entry {self.entry_id}: {self.location.path / self.path}"

    def __repr__(self) -> str:
        return f"Entry {self.entry_id}: {self.location=} {self.path=}"

    def __eq__(self, __value: object) -> bool:
        if not isinstance(__value, Entry):
            raise NotImplemented
        return self.entry_id == __value.entry_id

    def to_json(self) -> JsonEntry:
        # TODO: Talk about changing the fields type in JsonEntry
        temp_fields = [{k: v} for k, v in self._attributes.items()]
        return JsonEntry(
            id=self.entry_id,
            filename=self.path.name,
            path=str(self.path),
            fields=temp_fields,
        )


class Tag:
    """A Library Tag Object. Referenced by ID."""

    def __init__(self, tag_id: int, name: str, shorthand: str, color: str) -> None:
        self.tag_id = tag_id
        self.name = name
        self.shorthand = shorthand
        self.color = color
        self.aliases: list[str] = []  # TODO: Load aliases from database (Lazy Load?)
        self.parents: list[int] = []  # TODO: Load parents from database (Lazy Load?)
        # self.parents probably needs to be a load on init since its part of the tag title

    def __str__(self) -> str:
        return f"Tag {self.tag_id}: {self.name=}, {self.shorthand=}, {self.color=}"

    def __repr__(self) -> str:
        return f"Tag {self.tag_id}: {self.name=}, {self.shorthand=}, {self.color=}, {self.aliases=}, {self.parents=}"

    def to_json(self) -> JsonTag:
        return JsonTag(
            id=self.tag_id,
            name=self.name,
            aliases=self.aliases,
            color=self.color,
            shorthand=self.shorthand,
            subtag_ids=self.parents,
        )

    # TODO: Check where this is used
    def debug_name(self) -> str:
        """Returns a formatted tag name intended for displaying."""
        return f"{self.name} (ID: {self.tag_id})"

    def display_name(self) -> str:
        """Returns a formatted tag name intended for displaying."""
        if self.parents:
            if self.parents[0].shorthand:
                return f"{self.name} ({self.parents[0].shorthand})"
            else:
                return f"{self.name} ({self.parents[0].name})"
        else:
            return f"{self.name}"


class Group:  # Maps to entry_page table
    """
    A Library Group Object. Referenced by ID.
    Entries and their Page #s are grouped together in the e_ids_and_paged tuple.
    Sort order is `(filename | title | date, asc | desc)`.
    """

    # TODO: Implement Group object


class Library:
    """Class for the Library object, and all CRUD operations made upon it."""

    def __init__(self) -> None:
        self.library_dir: Optional[Path] = None
        self.data_source: Optional[DataSource] = None
        self.locations: list[Location] = []
        self.entries: dict[int, Entry] = {}
        self._filename_to_entry_id_map: dict[str, int] = {}
        self.tags: dict[int, Tag] = {}
        self.groups: list[Group] = []

    def create_library(self, path: Path, data_source: DataSource) -> int:
        """Creates a TagStudio library in the given directory.
        Return Codes:
        0: Library Successfully Created
        2: File creation error
        """

        try:
            self.clear_internal_vars()
            self.library_dir = path
            self.verify_ts_folders()
            self.save_library_to_disk()
            self.open_library(self.library_dir, data_source)
        except:
            traceback.print_exc()
            return 2

        return 0

    def verify_ts_folders(self) -> None:
        """Verifies/creates folders required by TagStudio."""

        full_ts_path = self.library_dir / TS_FOLDER_NAME
        full_backup_path = self.library_dir / TS_FOLDER_NAME / BACKUP_FOLDER_NAME
        full_collage_path = self.library_dir / TS_FOLDER_NAME / COLLAGE_FOLDER_NAME

        if not full_ts_path.exists():
            full_ts_path.mkdir()

        if not full_backup_path.exists():
            full_backup_path.mkdir()

        if not full_collage_path.exists():
            full_collage_path.mkdir()

    def open_library(self, lib_path: Path, data_source: DataSource) -> int:
        """Opens a TagStudio v9+ Library.
        Returns 0 if library does not exist, 1 if successfully opened, 2 if corrupted.
        """

        if lib_path.is_dir():
            self.library_dir = lib_path
            self.verify_ts_folders()
        else:
            # TODO: check if this needs to do anything more
            return 0

        self.data_source = data_source

        major, minor, patch = self.data_source.get_version()
        # TODO: For now load the entire DB into memory, this should be optimized (lazy loads or other)
        self.locations = self.data_source.get_locations()
        self.entries = self.data_source.get_entries()
        for entry_id, entry in self.entries.items():
            entry.set_attributes(self.data_source.get_entry_attributes(entry_id))
            self._filename_to_entry_id_map[str(entry.path)] = entry_id
        self.tags = self.data_source.get_tags()
        for tag_id, tag in self.tags.items():
            tag.parents = self.data_source.get_tag_relations(tag_id)
            tag.aliases = self.data_source.get_aliases(tag_id)
        # self.groups = self.data_source.get_groups()  # TODO: Not implemented in v9.2.0

        return 1

    def to_json(self):
        """
        Creates a JSON serialized string from the Library object.
        Used in saving the library to disk.
        """

        file_to_save: JsonLibary = JsonLibary()
        file_to_save["ts-version"] = VERSION

        logging.info("[LIBRARY] Formatting Locations to JSON...")
        file_to_save["locations"] = []
        for location in self.locations:
            file_to_save["locations"].append(location.to_json())

        logging.info("[LIBRARY] Formatting Tags to JSON...")
        file_to_save["tags"] = []
        for tag in self.tags:
            file_to_save["tags"].append(tag.to_json())

        logging.info("[LIBRARY] Formatting Entries to JSON...")
        file_to_save["entries"] = []
        for entry in self.entries.values():
            file_to_save["entries"].append(entry.to_json())

        # TODO: Implement groups
        # logging.info("[LIBRARY] Formatting Groups to JSON...")
        # for group in self.groups:
        #     file_to_save["groups"].append(group.to_json())

        logging.info("[LIBRARY] Done Formatting to JSON!")
        return file_to_save

    def save_library_to_disk(self) -> int:
        """Calls the DataSource to save the Library."""
        return self.data_source.save()

    def backup_library(self, path: Path) -> int:
        """Creates a backup of the Library."""
        # Only way I could think of verifying a file that MIGHT exist
        if not path.suffix:
            raise ValueError("Backup path must point to a file.")
        return self.data_source.save(path)

    def export_library_to_disk(self, path: Path) -> int:
        """Exports a JSON file of the Library to disk at the specified path.
        Returns the 0 on success, 1 on failure"""

        logging.info(f"[LIBRARY] Exporting Library to Disk...")
        start_time = time.time()

        with open(path, mode="w", encoding="utf-8") as outfile:
            outfile.flush()
            ujson.dump(
                self.to_json(),
                outfile,
                ensure_ascii=False,
                escape_forward_slashes=False,
                indent=4,
            )
        end_time = time.time()
        logging.info(
            f"[LIBRARY] Library exported to {path} disk in {(end_time - start_time):.3f} seconds"
        )
        return 0

    def clear_internal_vars(self):
        """Clears the internal variables of the Library object."""
        # TODO: Verify that this is all that needs to be cleared
        self.library_dir = None
        self.data_source = None

        self.entries.clear()
        self._filename_to_entry_id_map.clear()

        self.tags.clear()
        self.groups.clear()
        self.locations.clear()

    def refresh_dir(self):
        """Scans a directory for files, and adds those relative filenames to internal variables."""

        dir_file_count: int = 0
        files_not_in_library = []

        # Scans the directory for files, keeping track of:
        #   - Total file count
        #   - Files without library entries
        start_time = time.time()
        for location in self.locations:
            for f in location.path.rglob("*"):
                if f.is_dir() or TS_FOLDER_NAME in f or "$RECYCLE.BIN" in f:
                    continue

                dir_file_count += 1
                file = str(f.relative_to(location.path))

                try:
                    _ = self._filename_to_entry_id_map[str(file)]
                except KeyError:
                    # print(file)
                    files_not_in_library.append(file)

                end_time = time.time()
                # Yield output every 1/30 of a second
                if (end_time - start_time) > 0.034:
                    yield dir_file_count
                    start_time = time.time()

    def get_missing_files(self) -> Generator[Entry, None, None]:
        """Generator that yields a list of Entries with missing files."""
        for entry in self.entries.values():
            if not entry.path.exists():
                yield entry

    def remove_entry(self, entry_id: int) -> None:
        """Removes an Entry from the Library."""
        # Remove Entry from library
        entry = self.entries[entry_id]

        del self._filename_to_entry_id_map[str(entry.path)]
        del self.entries[entry_id]

        # Remove Entry from DataSource
        self.data_source.remove_entry(entry_id)

    def remove_entries(self, entry_ids: list[int]) -> None:
        """Removes a list of Entries from the Library."""

        # Remove Entries from library
        for entry_id in entry_ids:
            entry = self.entries[entry_id]

            del self._filename_to_entry_id_map[str(entry.path)]
            del self.entries[entry_id]

        # Remove Entries from DataSource
        self.remove_entries(entry_ids)

    def get_duplicate_entries(self) -> list[list[Entry]]:
        """Get all duplicate entries"""
        checked: set[Entry] = set[Entry]()
        duplicate_entries: list[list[Entry]] = []
        for entry in self.entries.values():
            if entry not in checked:
                matched: list[Entry] = []
                for other_entry in self.entries.values():
                    if entry.path == other_entry.path:
                        matched.append(other_entry)
                if matched:
                    matched.insert(0, entry)
                    duplicate_entries.append(matched)
                    logging.log(
                        f"[LIBRARY] Entry {entry.entry_id} has {len(matched)} duplicates"
                    )
                else:
                    logging.log(f"[LIBRARY] Entry {entry.entry_id} has no duplicates")
                checked.add(entry)
        return duplicate_entries

    def merge_dupe_entries(self):
        """
        Merges duplicate Entries.
        A duplicate Entry is defined as an Entry pointing to a file that one or more
        other Entries are also pointing to.\n
        `dupe_entries = tuple(int, list[int])`
        """

        print("[LIBRARY] Mirroring Duplicate Entries...")
        for dupe in self.dupe_entries:
            self.mirror_entry_fields([dupe[0]] + dupe[1])

        # print('Consolidating Entries...')
        # for dupe in self.dupe_entries:
        # 	for index in dupe[1]:
        # 		print(f'Consolidating Duplicate: {(self.entries[index].path + os.pathsep + self.entries[index].filename)}')
        # 		self.entries.remove(self.entries[index])
        # self._map_filenames_to_entry_indices()

        print(
            "[LIBRARY] Consolidating Entries... (This may take a while for larger libraries)"
        )
        unique: list[Entry] = []
        for i, e in enumerate(self.entries):
            if e not in unique:
                unique.append(e)
                # print(f'[{i}/{len(self.entries)}] Appending: {(e.path + os.pathsep + e.filename)[0:32]}...')
                sys.stdout.write(
                    f"\r[LIBRARY] [{i}/{len(self.entries)}] Appending Unique Entry..."
                )
            else:
                sys.stdout.write(
                    f"\r[LIBRARY] [{i}/{len(self.entries)}] Consolidating Duplicate: {(e.path + os.pathsep + e.filename)[0:]}..."
                )
        print("")
        # [unique.append(x) for x in self.entries if x not in unique]
        self.entries = unique
        self._map_filenames_to_entry_ids()

    def refresh_dupe_files(self, results_filepath):
        """
        Refreshes the list of duplicate files.
        A duplicate file is defined as an identical or near-identical file as determined
        by a DupeGuru results file.
        """
        full_results_path = (
            os.path.normpath(f"{self.library_dir}/{results_filepath}")
            if self.library_dir not in results_filepath
            else os.path.normpath(f"{results_filepath}")
        )
        if os.path.exists(full_results_path):
            self.dupe_files.clear()
            self._map_filenames_to_entry_ids()
            tree = ET.parse(full_results_path)
            root = tree.getroot()
            for i, group in enumerate(root):
                # print(f'-------------------- Match Group {i}---------------------')
                files: list[str] = []
                # (File Index, Matched File Index, Match Percentage)
                matches: list[tuple[int, int, int]] = []
                for element in group:
                    if element.tag == "file":
                        file = element.attrib.get("path")
                        files.append(file)
                    if element.tag == "match":
                        matches.append(
                            (
                                int(element.attrib.get("first")),
                                int(element.attrib.get("second")),
                                int(element.attrib.get("percentage")),
                            )
                        )
                for match in matches:
                    # print(f'MATCHED ({match[2]}%): \n   {files[match[0]]} \n-> {files[match[1]]}')
                    if os.name == "nt":
                        file_1 = str(os.path.relpath(files[match[0]], self.library_dir))
                        file_2 = str(os.path.relpath(files[match[1]], self.library_dir))
                        if (
                            file_1.lower() in self.filename_to_entry_id_map.keys()
                            and file_2.lower() in self.filename_to_entry_id_map.keys()
                        ):
                            self.dupe_files.append(
                                (files[match[0]], files[match[1]], match[2])
                            )
                    else:
                        if (
                            file_1 in self.filename_to_entry_id_map.keys()
                            and file_2 in self.filename_to_entry_id_map.keys()
                        ):
                            self.dupe_files.append(
                                (files[match[0]], files[match[1]], match[2])
                            )
                    # self.dupe_files.append((files[match[0]], files[match[1]], match[2]))

                print("")

            for dupe in self.dupe_files:
                print(
                    f"[LIBRARY] MATCHED ({dupe[2]}%): \n   {dupe[0]} \n-> {dupe[1]}",
                    end="\n",
                )
                # self.dupe_files.append(full_path)

    def remove_missing_files(self):
        deleted = []
        for i, missing in enumerate(self.missing_files):
            # pb.setValue(i)
            # pb.setLabelText(f'Deleting {i}/{len(self.lib.missing_files)} Unlinked Entries')
            try:
                id = self.get_entry_id_from_filepath(missing)
                logging.info(f"Removing Entry ID {id}:\n\t{missing}")
                self.remove_entry(id)
                # self.driver.purge_item_from_navigation(ItemType.ENTRY, id)
                deleted.append(missing)
            except KeyError:
                logging.info(
                    f'[LIBRARY][ERROR]: "{id}" was reported as missing, but is not in the file_to_entry_id map.'
                )
            yield (i, id)
        for d in deleted:
            self.missing_files.remove(d)

    def remove_missing_matches(self, fixed_indices: list[int]):
        """Removes a list of fixed Entry indices from the internal missing_matches list."""
        for i in fixed_indices:
            del self.missing_matches[i]

    def fix_missing_files(self):
        """
        Attempts to repair Entries that point to invalid file paths.
        """

        # self.refresh_missing_files()

        # matched_json_filepath = os.path.normpath(
        # 	f'{self.library_dir}/{TS_FOLDER_NAME}/missing_matched.json')
        # # if not os.path.exists(matched_json_filepath):
        # # 	self.match_missing_files()

        self.missing_matches.clear()

        fixed_indices = []
        # if os.path.exists(matched_json_filepath):
        # 	with open(matched_json_filepath, "r", encoding="utf8") as f:
        # 		self.missing_matches = json.load(f)

        # 	self.refresh_missing_files()
        for i, missing in enumerate(self.missing_files):
            print(missing)
            if missing not in self.missing_matches.keys():
                matches = self._match_missing_file(missing)
                if matches:
                    print(f"[LIBRARY] Adding key {missing} with matches {matches}")
                    self.missing_matches[missing] = matches
                    yield (i, True)
                else:
                    yield (i, False)

        # self._purge_empty_missing_entries()

        for i, matches in enumerate(self.missing_matches):
            if len(self.missing_matches[matches]) == 1:
                id = self.get_entry_id_from_filepath(matches)
                self.update_entry_path(id, self.missing_matches[matches][0])
                fixed_indices.append(matches)
                # print(f'Fixed {self.entries[self.get_entry_index_from_filename(i)].filename}')
                print(f"[LIBRARY] Fixed {self.get_entry(id).filename}")
            # (int, str)

        self._map_filenames_to_entry_ids()
        self.remove_missing_matches(fixed_indices)

        # for i in fixed_indices:
        # 	# print(json_dump[i])
        # 	del self.missing_matches[i]

        # with open(matched_json_filepath, "w") as outfile:
        # 	outfile.flush()
        # 	json.dump({}, outfile, indent=4)
        # print(f'Re-saved to disk at {matched_json_filepath}')

    def _match_missing_file(self, file: str) -> list[str]:
        """
        Tries to find missing entry files within the library directory.
        Works if files were just moved to different subfolders and don't have duplicate names.
        """

        # self.refresh_missing_files()

        matches = []

        # for file in self.missing_files:
        head, tail = os.path.split(file)
        for root, dirs, files in os.walk(self.library_dir, topdown=True):
            for f in files:
                # print(f'{tail} --- {f}')
                if tail == f and "$recycle.bin" not in root.lower():
                    # self.fixed_files.append(tail)

                    new_path = str(os.path.relpath(root, self.library_dir))

                    matches.append(new_path)

                    # if file not in matches.keys():
                    # 	matches[file] = []
                    # matches[file].append(new_path)

                    print(
                        f'[LIBRARY] MATCH: {file} \n\t-> {os.path.normpath(self.library_dir + "/" + new_path + "/" + tail)}\n'
                    )

        if not matches:
            print(f"[LIBRARY] No matches found for: {file}")

        return matches

        # with open(
        #     os.path.normpath(
        #         f"{self.library_dir}/{TS_FOLDER_NAME}/missing_matched.json"
        #     ),
        #     "w",
        # ) as outfile:
        #     outfile.flush()
        #     json.dump(matches, outfile, indent=4)
        # print(
        #     f'[LIBRARY] Saved to disk at {os.path.normpath(self.library_dir + "/" + TS_FOLDER_NAME + "/missing_matched.json")}'
        # )

    def add_entry_to_library(self, entry: Entry):
        """Adds a new Entry to the Library."""
        self.entries.append(entry)
        self._map_entry_id_to_index(entry, -1)

    def add_new_files_as_entries(self) -> list[int]:
        """Adds files from the `files_not_in_library` list to the Library as Entries. Returns list of added indices."""
        new_ids: list[int] = []
        for file in self.files_not_in_library:
            path, filename = os.path.split(file)
            # print(os.path.split(file))
            entry = Entry(
                id=self._next_entry_id, filename=filename, path=path, fields=[]
            )
            self._next_entry_id += 1
            self.add_entry_to_library(entry)
            new_ids.append(entry.entry_id)
        self._map_filenames_to_entry_ids()
        self.files_not_in_library.clear()
        return new_ids

        self.files_not_in_library.clear()

    def get_entry(self, entry_id: int) -> Entry:
        """Returns an Entry object given an Entry ID."""
        return self.entries[self._entry_id_to_index_map[int(entry_id)]]

    def get_collation(self, collation_id: int) -> Collation:
        """Returns a Collation object given an Collation ID."""
        return self.collations[self._collation_id_to_index_map[int(collation_id)]]

    # @deprecated('Use new Entry ID system.')
    def get_entry_from_index(self, index: int) -> Entry:
        """Returns a Library Entry object given its index in the unfiltered Entries list."""
        if self.entries:
            return self.entries[int(index)]

    # @deprecated('Use new Entry ID system.')
    def get_entry_id_from_filepath(self, filename):
        """Returns an Entry ID given the full filepath it points to."""
        try:
            if self.entries:
                if os.name == "nt":
                    return self.filename_to_entry_id_map[
                        str(
                            os.path.normpath(
                                os.path.relpath(filename, self.library_dir)
                            )
                        ).lower()
                    ]
                return self.filename_to_entry_id_map[
                    str(os.path.normpath(os.path.relpath(filename, self.library_dir)))
                ]
        except:
            return -1

    def search_library(
        self, query: str = None, entries=True, collations=True, tag_groups=True
    ) -> list[tuple[ItemType, int]]:
        """
        Uses a search query to generate a filtered results list.
        Returns a list of (str, int) tuples consisting of a result type and ID.
        """

        # self.filtered_entries.clear()
        results: list[tuple[ItemType, int]] = []
        collations_added = []

        if query:
            # start_time = time.time()
            query: str = query.strip().lower()
            query_words: list[str] = query.split(" ")
            all_tag_terms: list[str] = []
            only_untagged: bool = "untagged" in query or "no tags" in query
            only_empty: bool = "empty" in query or "no fields" in query
            only_missing: bool = "missing" in query or "no file" in query
            allow_adv: bool = "filename:" in query_words
            tag_only: bool = "tag_id:" in query_words
            if allow_adv:
                query_words.remove("filename:")
            if tag_only:
                query_words.remove("tag_id:")
            # TODO: Expand this to allow for dynamic fields to work.
            only_no_author: bool = "no author" in query or "no artist" in query

            # Preprocess the Tag terms.
            if query_words:
                for i, term in enumerate(query_words):
                    for j, term in enumerate(query_words):
                        if (
                            query_words[i : j + 1]
                            and " ".join(query_words[i : j + 1])
                            in self._tag_strings_to_id_map
                        ):
                            all_tag_terms.append(" ".join(query_words[i : j + 1]))
                # This gets rid of any accidental term inclusions because they were words
                # in another term. Ex. "3d" getting added in "3d art"
                for i, term in enumerate(all_tag_terms):
                    for j, term2 in enumerate(all_tag_terms):
                        if i != j and all_tag_terms[i] in all_tag_terms[j]:
                            # print(
                            #     f'removing {all_tag_terms[i]} because {all_tag_terms[i]} was in {all_tag_terms[j]}')
                            all_tag_terms.remove(all_tag_terms[i])
                            break

            # print(all_tag_terms)

            # non_entry_count = 0
            # Iterate over all Entries =============================================================
            for entry in self.entries:
                allowed_ext: bool = (
                    os.path.splitext(entry.filename)[1][1:].lower()
                    not in self.ignored_extensions
                )
                # try:
                # entry: Entry = self.entries[self.file_to_library_index_map[self._source_filenames[i]]]
                # print(f'{entry}')

                if allowed_ext:
                    # If the entry has tags of any kind, append them to this main tag list.
                    entry_tags: list[int] = []
                    entry_authors: list[str] = []
                    if entry._fields:
                        for field in entry._fields:
                            field_id = list(field.keys())[0]
                            if self.get_field_obj(field_id)["type"] == "tag_box":
                                entry_tags.extend(field[field_id])
                            if self.get_field_obj(field_id)["name"] == "Author":
                                entry_authors.extend(field[field_id])
                            if self.get_field_obj(field_id)["name"] == "Artist":
                                entry_authors.extend(field[field_id])

                    # print(f'Entry Tags: {entry_tags}')

                    # Add Entries from special flags -------------------------------
                    # TODO: Come up with a more user-resistent way to 'archived' and 'favorite' tags.
                    if only_untagged:
                        if not entry_tags:
                            results.append((ItemType.ENTRY, entry.entry_id))
                    elif only_no_author:
                        if not entry_authors:
                            results.append((ItemType.ENTRY, entry.entry_id))
                    elif only_empty:
                        if not entry._fields:
                            results.append((ItemType.ENTRY, entry.entry_id))
                    elif only_missing:
                        if (
                            os.path.normpath(
                                f"{self.library_dir}/{entry.path}/{entry.filename}"
                            )
                            in self.missing_files
                        ):
                            results.append((ItemType.ENTRY, entry.entry_id))

                    # elif query == "archived":
                    #     if entry.tags and self._tag_names_to_tag_id_map[self.archived_word.lower()][0] in entry.tags:
                    #         self.filtered_file_list.append(file)
                    #         pb.value = len(self.filtered_file_list)
                    # elif query in entry.path.lower():

                    # NOTE: This searches path and filenames.
                    if allow_adv:
                        if [q for q in query_words if (q in entry.path.lower())]:
                            results.append((ItemType.ENTRY, entry.entry_id))
                        elif [q for q in query_words if (q in entry.filename.lower())]:
                            results.append((ItemType.ENTRY, entry.entry_id))
                    elif tag_only:
                        if entry.has_tag(self, int(query_words[0])):
                            results.append((ItemType.ENTRY, entry.entry_id))

                    # elif query in entry.filename.lower():
                    # 	self.filtered_entries.append(index)
                    elif entry_tags:
                        # For each verified, extracted Tag term.
                        failure_to_union_terms = False
                        for term in all_tag_terms:
                            # If the term from the previous loop was already verified:
                            if not failure_to_union_terms:
                                cluster: set = set()
                                # Add the immediate associated Tags to the set (ex. Name, Alias hits)
                                # Since this term could technically map to multiple IDs, iterate over it
                                # (You're 99.9999999% likely to just get 1 item)
                                for id in self._tag_strings_to_id_map[term]:
                                    cluster.add(id)
                                    cluster = cluster.union(
                                        set(self.get_tag_cluster(id))
                                    )
                                # print(f'Full Cluster: {cluster}')
                                # For each of the Tag IDs in the term's ID cluster:
                                for t in cluster:
                                    # Assume that this ID from the cluster is not in the Entry.
                                    # Wait to see if proven wrong.
                                    failure_to_union_terms = True
                                    # If the ID actually is in the Entry,
                                    if t in entry_tags:
                                        # There wasn't a failure to find one of the term's cluster IDs in the Entry.
                                        # There is also no more need to keep checking the rest of the terms in the cluster.
                                        failure_to_union_terms = False
                                        # print(f'FOUND MATCH: {t}')
                                        break
                                    # print(f'\tFailure to Match: {t}')
                        # If there even were tag terms to search through AND they all match an entry
                        if all_tag_terms and not failure_to_union_terms:
                            # self.filter_entries.append()
                            # self.filtered_file_list.append(file)
                            # results.append((SearchItemType.ENTRY, entry.id))
                            added = False
                            for f in entry._fields:
                                if self.get_field_attr(f, "type") == "collation":
                                    if (
                                        self.get_field_attr(f, "content")
                                        not in collations_added
                                    ):
                                        results.append(
                                            (
                                                ItemType.COLLATION,
                                                self.get_field_attr(f, "content"),
                                            )
                                        )
                                        collations_added.append(
                                            self.get_field_attr(f, "content")
                                        )
                                    added = True

                            if not added:
                                results.append((ItemType.ENTRY, entry.entry_id))

                # sys.stdout.write(
                #     f'\r[INFO][FILTER]: {len(self.filtered_file_list)} matches found')
                # sys.stdout.flush()

                # except:
                #     # # Put this here to have new non-registered images show up
                #     # if query == "untagged" or query == "no author" or query == "no artist":
                #     #     self.filtered_file_list.append(file)
                #     # non_entry_count = non_entry_count + 1
                #     pass

            # end_time = time.time()
            # print(
            # 	f'[INFO][FILTER]: {len(self.filtered_entries)} matches found ({(end_time - start_time):.3f} seconds)')

            # if non_entry_count:
            # 	print(
            # 		f'[INFO][FILTER]: There are {non_entry_count} new files in {self.source_dir} that do not have entries. These will not appear in most filtered results.')
            # if not self.filtered_entries:
            # 	print("[INFO][FILTER]: Filter returned no results.")
        else:
            for entry in self.entries:
                added = False
                allowed_ext: bool = (
                    os.path.splitext(entry.filename)[1][1:].lower()
                    not in self.ignored_extensions
                )
                if allowed_ext:
                    for f in entry._fields:
                        if self.get_field_attr(f, "type") == "collation":
                            if (
                                self.get_field_attr(f, "content")
                                not in collations_added
                            ):
                                results.append(
                                    (
                                        ItemType.COLLATION,
                                        self.get_field_attr(f, "content"),
                                    )
                                )
                                collations_added.append(
                                    self.get_field_attr(f, "content")
                                )
                            added = True

                    if not added:
                        results.append((ItemType.ENTRY, entry.entry_id))
            # for file in self._source_filenames:
            #     self.filtered_file_list.append(file)
        results.reverse()
        return results

    def search_tags(
        self,
        query: str,
        include_cluster=False,
        ignore_builtin=False,
        threshold: int = 1,
        context: list[str] = None,
    ) -> list[int]:
        """Returns a list of Tag IDs returned from a string query."""
        # tag_ids: list[int] = []
        # if query:
        # 	query = query.lower()
        # 	query_words = query.split(' ')
        # 	all_tag_terms: list[str] = []

        # 	# Preprocess the Tag terms.
        # 	if len(query_words) > 0:
        # 		for i, term in enumerate(query_words):
        # 			for j, term in enumerate(query_words):
        # 				if query_words[i:j+1] and " ".join(query_words[i:j+1]) in self._tag_names_to_tag_id_map:
        # 					all_tag_terms.append(" ".join(query_words[i:j+1]))
        # 		# This gets rid of any accidental term inclusions because they were words
        # 		# in another term. Ex. "3d" getting added in "3d art"
        # 		for i, term in enumerate(all_tag_terms):
        # 			for j, term2 in enumerate(all_tag_terms):
        # 				if i != j and all_tag_terms[i] in all_tag_terms[j]:
        # 					# print(
        # 					#     f'removing {all_tag_terms[i]} because {all_tag_terms[i]} was in {all_tag_terms[j]}')
        # 					all_tag_terms.remove(all_tag_terms[i])
        # 					break

        # 		for term in all_tag_terms:
        # 			for id in self._tag_names_to_tag_id_map[term]:
        # 				if id not in tag_ids:
        # 					tag_ids.append(id)
        # return tag_ids

        # NOTE: I'd expect a blank query to return all with the other implementation, but
        # it misses stuff like Archive (id 0) so here's this as a catch-all.
        query = query.strip()
        if not query:
            all: list[int] = []
            for tag in self.tags:
                if ignore_builtin and tag.id >= 1000:
                    all.append(tag.id)
                elif not ignore_builtin:
                    all.append(tag.id)
            return all

        # Direct port from Version 8 ===========================================
        # TODO: Make this more efficient (if needed)
        # ids: list[int] = []
        id_weights: list[tuple[int, int]] = []
        # partial_id_weights: list[int] = []
        priority_ids: list[int] = []
        # print(f'Query: \"{query}\" -------------------------------------')
        for string in self._tag_strings_to_id_map:  # O(n), n = tags
            exact_match: bool = False
            partial_match: bool = False
            query = strip_punctuation(query).lower()
            string = strip_punctuation(string).lower()

            if query == string:
                exact_match = True
            elif string.startswith(query):
                if len(query) >= (
                    len(string) // (len(string) if threshold == 1 else threshold)
                ):
                    partial_match = True

            if exact_match or partial_match:
                # Avg O(1), usually 1 item
                for tag_id in self._tag_strings_to_id_map[string]:
                    proceed: bool = False
                    if ignore_builtin and tag_id >= 1000:
                        proceed = True
                    elif not ignore_builtin:
                        proceed = True

                    if proceed:
                        if tag_id not in [x[0] for x in id_weights]:
                            if exact_match:
                                # print(f'[{query}] EXACT MATCH:')
                                # print(self.get_tag_from_id(tag_id).display_name(self))
                                # print('')
                                # time.sleep(0.1)
                                priority_ids.append(tag_id)
                                id_weights.append((tag_id, 100000000))
                            else:
                                # print(f'[{query}] Partial Match:')
                                # print(self.get_tag_from_id(tag_id).display_name(self))
                                # print('')
                                # time.sleep(0.1)
                                # ids.append(id)
                                id_weights.append((tag_id, 0))
                        # O(m), m = # of references
                        if include_cluster:
                            for id in self.get_tag_cluster(tag_id):
                                if (id, 0) not in id_weights:
                                    id_weights.append((id, 0))

        # Contextual Weighing
        if context and (
            (len(id_weights) > 1 and len(priority_ids) > 1) or (len(priority_ids) > 1)
        ):
            context_strings: list[str] = [
                s.replace(" ", "")
                .replace("_", "")
                .replace("-", "")
                .replace("'", "")
                .replace("(", "")
                .replace(")", "")
                .replace("[", "")
                .replace("]", "")
                .lower()
                for s in context
            ]
            for term in context:
                if len(term.split(" ")) > 1:
                    context_strings += term.split(" ")
                if len(term.split("_")) > 1:
                    context_strings += term.split("_")
                if len(term.split("-")) > 1:
                    context_strings += term.split("-")
            context_strings = list(set(context_strings))
            # context_strings.sort() # NOTE: TEMP!!!!!!!!!!!!!!!!!!
            # print(f'Context Strings: {context_strings}')
            # time.sleep(3)
            # for term in context:
            # 	context_ids += self.filter_tags(query=term, include_cluster=True, ignore_builtin=ignore_builtin)
            for i, idw in enumerate(id_weights, start=0):
                weight: int = 0
                tag_strings: list[str] = []
                subtag_ids: list[int] = self.get_all_child_tag_ids(idw[0])
                for id in self.get_tag_cluster(idw[0]):
                    subtag_ids += self.get_all_child_tag_ids(id)
                subtag_ids = list(set(subtag_ids))

                for sub_id in subtag_ids:
                    tag_strings += (
                        [self.get_tag(sub_id).name]
                        + [self.get_tag(sub_id).shorthand]
                        + self.get_tag(sub_id).aliases
                    )

                # for id in self.get_tag_cluster(idw[0]):
                # 	tag_strings += [self.get_tag_from_id(id).name] + [self.get_tag_from_id(id).shorthand] + self.get_tag_from_id(id).aliases
                split: list[str] = []
                for ts in tag_strings:
                    if len(ts.split(" ")) > 1:
                        split += ts.split(" ")
                tag_strings += split
                tag_strings = [
                    s.replace(" ", "")
                    .replace("_", "")
                    .replace("-", "")
                    .replace("'", "")
                    .lower()
                    for s in tag_strings
                ]
                while "" in tag_strings:
                    tag_strings.remove("")
                tag_strings = list(set(tag_strings))
                # tag_strings.sort() # NOTE: TEMP!!!!!!!!!!!!!!!!!!
                for ts in tag_strings:
                    weight += context_strings.count(ts)
                id_weights[i] = (idw[0], idw[1] + weight)

                # print(f'Tag Strings for {self.get_tag_from_id(idw[0]).display_name(self)}: {tag_strings}')
                # time.sleep(3)
        id_weights = sorted(id_weights, key=lambda id: id[1], reverse=True)

        # if len(id_weights) > 1:
        # 	print(f'Context Weights: \"{id_weights}\"')

        final: list[int] = []

        # if context and id_weights:
        # 	time.sleep(3)
        [final.append(idw[0]) for idw in id_weights if idw[0] not in final]
        # print(f'Final IDs: \"{[self.get_tag_from_id(id).display_name(self) for id in final]}\"')
        # print('')
        return final

    def get_all_child_tag_ids(self, tag_id: int) -> list[int]:
        """Recursively traverse a Tag's subtags and return a list of all children tags."""
        subtag_ids: list[int] = []
        if self.get_tag(tag_id).subtag_ids:
            for sub_id in self.get_tag(tag_id).subtag_ids:
                if sub_id not in subtag_ids:
                    subtag_ids.append(sub_id)
                    subtag_ids += self.get_all_child_tag_ids(sub_id)
        else:
            return [tag_id]

        return subtag_ids

    def filter_field_templates(self: str, query) -> list[int]:
        """Returns a list of Field Template IDs returned from a string query."""

        matches: list[int] = []
        for ft in self.default_fields:
            if ft["name"].lower().startswith(query.lower()):
                matches.append(ft["id"])

        return matches

    def update_tag(self, tag: Tag) -> None:
        """
        Edits a Tag in the Library.
        This function undoes and redos the following parts of the 'add_tag_to_library()' process:\n
        - Un-maps the old Tag name, shorthand, and aliases from the Tag ID
        and re-maps the new strings to its ID via '_map_tag_names_to_tag_id()'.\n
        - Un
        """
        tag.subtag_ids = [x for x in tag.subtag_ids if x != tag.id]

        # Since the ID stays the same when editing, only the Tag object is needed.
        # Merging Tags is handled in a different function.
        old_tag: Tag = self.get_tag(tag.id)

        # Undo and Redo 'self._map_tag_names_to_tag_id(tag)' ===========================================================
        # got to map[old names] and remove reference to this id.
        # Remember that _tag_names_to_tag_id_map maps strings to a LIST of ids.
        # print(
        #     f'Removing connection from "{old_tag.name.lower()}" to {old_tag.id} in {self._tag_names_to_tag_id_map[old_tag.name.lower()]}')
        old_name: str = strip_punctuation(old_tag.name).lower()
        self._tag_strings_to_id_map[old_name].remove(old_tag.id)
        # Delete the map key if it doesn't point to any other IDs.
        if not self._tag_strings_to_id_map[old_name]:
            del self._tag_strings_to_id_map[old_name]
        if old_tag.shorthand:
            old_sh: str = strip_punctuation(old_tag.shorthand).lower()
            # print(
            #     f'Removing connection from "{old_tag.shorthand.lower()}" to {old_tag.id} in {self._tag_names_to_tag_id_map[old_tag.shorthand.lower()]}')
            self._tag_strings_to_id_map[old_sh].remove(old_tag.id)
            # Delete the map key if it doesn't point to any other IDs.
            if not self._tag_strings_to_id_map[old_sh]:
                del self._tag_strings_to_id_map[old_sh]
        if old_tag.aliases:
            for alias in old_tag.aliases:
                old_a: str = strip_punctuation(alias).lower()
                # print(
                #     f'Removing connection from "{alias.lower()}" to {old_tag.id} in {self._tag_names_to_tag_id_map[alias.lower()]}')
                self._tag_strings_to_id_map[old_a].remove(old_tag.id)
                # Delete the map key if it doesn't point to any other IDs.
                if not self._tag_strings_to_id_map[old_a]:
                    del self._tag_strings_to_id_map[old_a]
        # then add new reference to this id at map[new names]
        # print(f'Mapping new names for "{tag.name.lower()}" (ID: {tag.id})')
        self._map_tag_strings_to_tag_id(tag)

        # Redo 'self.tags.append(tag)' =================================================================================
        # then swap out the tag in the tags list to this one
        # print(f'Swapping {self.tags[self._tag_id_to_index_map[old_tag.id]]} *FOR* {tag} in tags list.')
        self.tags[self._tag_id_to_index_map[old_tag.id]] = tag
        print(f"Edited Tag: {tag}")

        # Undo and Redo 'self._map_tag_id_to_cluster(tag)' =============================================================
        # NOTE: Currently the tag is getting updated outside of this due to python
        # entanglement shenanigans so for now this method will always update the cluster maps.
        # if old_tag.subtag_ids != tag.subtag_ids:
        # TODO: Optimize this by 1,000,000% buy building an inverse recursive map function
        # instead of literally just deleting the whole map and building it again
        # print('Reticulating Splines...')
        self._tag_id_to_cluster_map.clear()
        for tag in self.tags:
            self._map_tag_id_to_cluster(tag)
            # print('Splines Reticulated.')

            self._map_tag_id_to_cluster(tag)

    def remove_tag(self, tag_id: int) -> None:
        """
        Removes a Tag from the Library.
        Disconnects it from all internal lists and maps, then remaps others as needed.
        """
        tag = self.get_tag(tag_id)

        # Step [1/7]:
        # Remove from Entries.
        for e in self.entries:
            if e._fields:
                for f in e._fields:
                    if self.get_field_attr(f, "type") == "tag_box":
                        if tag_id in self.get_field_attr(f, "content"):
                            self.get_field_attr(f, "content").remove(tag.id)

        # Step [2/7]:
        # Remove from Subtags.
        for t in self.tags:
            if t.subtag_ids:
                if tag_id in t.subtag_ids:
                    t.subtag_ids.remove(tag.id)

        # Step [3/7]:
        # Remove ID -> cluster reference.
        if tag_id in self._tag_id_to_cluster_map:
            del self._tag_id_to_cluster_map[tag.id]
        # Remove mentions of this ID in all clusters.
        for key, values in self._tag_id_to_cluster_map.items():
            if tag_id in values:
                values.remove(tag.id)

        # Step [4/7]:
        # Remove mapping of this ID to its index in the tags list.
        if tag.id in self._tag_id_to_index_map:
            del self._tag_id_to_index_map[tag.id]

        # Step [5/7]:
        # Remove this Tag from the tags list.
        self.tags.remove(tag)

        # Step [6/7]:
        # Remap the other Tag IDs to their new indices in the tags list.
        self._tag_id_to_index_map.clear()
        for i, t in enumerate(self.tags):
            self._map_tag_id_to_index(t, i)

        # Step [7/7]:
        # Remap all existing Tag names.
        self._tag_strings_to_id_map.clear()
        for t in self.tags:
            self._map_tag_strings_to_tag_id(t)

    def get_tag_ref_count(self, tag_id: int) -> tuple[int, int]:
        """Returns an int tuple (entry_ref_count, subtag_ref_count) of Tag reference counts."""
        entry_ref_count: int = 0
        subtag_ref_count: int = 0

        for e in self.entries:
            if e._fields:
                for f in e._fields:
                    if self.get_field_attr(f, "type") == "tag_box":
                        if tag_id in self.get_field_attr(f, "content"):
                            entry_ref_count += 1
                            break

        for t in self.tags:
            if t.subtag_ids:
                if tag_id in t.subtag_ids:
                    subtag_ref_count += 1

        # input()
        return (entry_ref_count, subtag_ref_count)

    def update_entry_path(self, entry_id: int, path: str) -> None:
        """Updates an Entry's path."""
        self.get_entry(entry_id).path = path

    def update_entry_filename(self, entry_id: int, filename: str) -> None:
        """Updates an Entry's filename."""
        self.get_entry(entry_id).filename = filename

    def update_entry_field(self, entry_id: int, field_index: int, content, mode: str):
        """Updates an Entry's specific field. Modes: append, remove, replace."""

        field_id: int = list(self.get_entry(entry_id)._fields[field_index].keys())[0]
        if mode.lower() == "append" or mode.lower() == "extend":
            for i in content:
                if i not in self.get_entry(entry_id)._fields[field_index][field_id]:
                    self.get_entry(entry_id)._fields[field_index][field_id].append(i)
        elif mode.lower() == "replace":
            self.get_entry(entry_id)._fields[field_index][field_id] = content
        elif mode.lower() == "remove":
            for i in content:
                self.get_entry(entry_id)._fields[field_index][field_id].remove(i)

    def does_field_content_exist(self, entry_id: int, field_id: int, content) -> bool:
        """Returns whether or not content exists in a specific entry field type."""
        # entry = self.entries[entry_index]
        entry = self.get_entry(entry_id)
        indices = self.get_field_index_in_entry(entry, field_id)
        for i in indices:
            if self.get_field_attr(entry._fields[i], "content") == content:
                return True
        return False

    def add_field_to_entry(self, entry_id: int, field_id: int) -> None:
        """Adds an empty Field, specified by Field ID, to an Entry via its index."""
        # entry = self.entries[entry_index]
        entry = self.get_entry(entry_id)
        field_type = self.get_field_obj(field_id)["type"]
        if field_type in TEXT_FIELDS:
            entry._fields.append({int(field_id): ""})
        elif field_type == "tag_box":
            entry._fields.append({int(field_id): []})
        elif field_type == "datetime":
            entry._fields.append({int(field_id): ""})
        else:
            logging.info(
                f"[LIBRARY][ERROR]: Unknown field id attempted to be added to entry: {field_id}"
            )

    def mirror_entry_fields(self, entry_ids: list[int]) -> None:
        """Combines and mirrors all fields across a list of given Entry IDs."""

        all_fields = []
        all_ids = []  # Parallel to all_fields
        # Extract and merge all fields from all given Entries.
        for id in entry_ids:
            if id:
                entry: Entry = self.get_entry(id)
                if entry and entry._fields:
                    for field in entry._fields:
                        # First checks if their are matching tag_boxes to append to
                        if (
                            self.get_field_attr(field, "type") == "tag_box"
                            and self.get_field_attr(field, "id") in all_ids
                        ):
                            content = self.get_field_attr(field, "content")
                            for i in content:
                                id = int(self.get_field_attr(field, "id"))
                                field_index = all_ids.index(id)
                                if i not in all_fields[field_index][id]:
                                    all_fields[field_index][id].append(i)
                        # If not, go ahead and whichever new field.
                        elif field not in all_fields:
                            all_fields.append(field)
                            all_ids.append(int(self.get_field_attr(field, "id")))

        # Replace each Entry's fields with the new merged ones.
        for id in entry_ids:
            entry: Entry = self.get_entry(id)
            if entry:
                entry._fields = all_fields

                # TODO: Replace this and any in CLI with a proper user-defined
                # field storing method.
                order: list[int] = (
                    [0]
                    + [1, 2]
                    + [9, 17, 18, 19, 20]
                    + [10, 14, 11, 12, 13, 22]
                    + [4, 5]
                    + [8, 7, 6]
                    + [3, 21]
                )

                # NOTE: This code is copied from the sort_fields() method.
                entry._fields = sorted(
                    entry._fields,
                    key=lambda x: order.index(self.get_field_attr(x, "id")),
                )

    def get_field_attr(self, entry_field, attribute: str):
        """Returns the value of a specified attribute inside an Entry field."""
        if attribute.lower() == "id":
            return list(entry_field.keys())[0]
        elif attribute.lower() == "content":
            return entry_field[self.get_field_attr(entry_field, "id")]
        else:
            return self.get_field_obj(self.get_field_attr(entry_field, "id"))[
                attribute.lower()
            ]

    def get_field_obj(self, field_id: int) -> dict:
        """
        Returns a field template object associated with a field ID.
        The objects have "id", "name", and "type" fields.
        """
        if int(field_id) < len(self.default_fields):
            return self.default_fields[int(field_id)]
        else:
            return {"id": -1, "name": "Unknown Field", "type": "unknown"}

    def get_field_index_in_entry(self, entry: Entry, field_id: int) -> list[int]:
        """
        Returns matched indices for the field type in an entry.\n
        Returns an empty list of no field of that type is found in the entry.
        """
        matched = []
        # entry: Entry = self.entries[entry_index]
        # entry = self.get_entry(entry_id)
        if entry._fields:
            for i, field in enumerate(entry._fields):
                if self.get_field_attr(field, "id") == int(field_id):
                    matched.append(i)

        return matched

    def _map_tag_strings_to_tag_id(self, tag: Tag) -> None:
        """
        Maps a Tag's name, shorthand, and aliases to their ID's (in the form of a list).\n
        ⚠️DO NOT USE FOR CONFIDENT DATA REFERENCES!⚠️\n
        This is intended to be used for quick search queries.\n
        Uses name_and_alias_to_tag_id_map.
        """
        # tag_id: int, tag_name: str, tag_aliases: list[str] = []
        name: str = strip_punctuation(tag.name).lower()
        if name not in self._tag_strings_to_id_map:
            self._tag_strings_to_id_map[name] = []
        self._tag_strings_to_id_map[name].append(tag.id)

        shorthand: str = strip_punctuation(tag.shorthand).lower()
        if shorthand not in self._tag_strings_to_id_map:
            self._tag_strings_to_id_map[shorthand] = []
        self._tag_strings_to_id_map[shorthand].append(tag.id)

        for alias in tag.aliases:
            alias: str = strip_punctuation(alias).lower()
            if alias not in self._tag_strings_to_id_map:
                self._tag_strings_to_id_map[alias] = []
            self._tag_strings_to_id_map[alias].append(tag.id)
            # print(f'{alias.lower()} -> {tag.id}')

    def _map_tag_id_to_cluster(self, tag: Tag, subtags: list[Tag] = None) -> None:
        """
        Maps a Tag's subtag's ID's back to it's parent Tag's ID (in the form of a list).
        Uses tag_id_to_cluster_map.\n
        EX: Tag: "Johnny Bravo", Subtags: "Cartoon Network (TV)", "Character".\n
        Maps "Cartoon Network" -> Johnny Bravo, "Character" -> "Johnny Bravo", and "TV" -> Johnny Bravo."
        """
        # If a list of subtags is not provided, the method will revert to a level 1-depth
        # mapping based on the given Tag's own subtags.
        if not subtags:
            subtags = [self.get_tag(sub_id) for sub_id in tag.subtag_ids]
        for subtag in subtags:
            if subtag.id not in self._tag_id_to_cluster_map.keys():
                self._tag_id_to_cluster_map[subtag.id] = []
            # Stops circular references
            if tag.id not in self._tag_id_to_cluster_map[subtag.id]:
                self._tag_id_to_cluster_map[subtag.id].append(tag.id)
                # If the subtag has subtags of it own, recursively link those to the original Tag.
                if subtag.subtag_ids:
                    self._map_tag_id_to_cluster(
                        tag,
                        [
                            self.get_tag(sub_id)
                            for sub_id in subtag.subtag_ids
                            if sub_id != tag.id
                        ],
                    )

    def _map_tag_id_to_index(self, tag: Tag, index: int) -> None:
        """
        Maps a Tag's ID to the Tag's Index in self.tags.
        Uses _tag_id_to_index_map.
        """
        # self._tag_id_to_index_map[tag.id_] = self.tags.index(tag)
        if index < 0:
            index = len(self.tags) + index
        self._tag_id_to_index_map[tag.id] = index
        # print(f'{tag.id} - {self._tag_id_to_index_map[tag.id]}')

    def _map_entry_id_to_index(self, entry: Entry, index: int) -> None:
        """
        Maps an Entry's ID to the Entry's Index in self.entries.
        Uses _entry_id_to_index_map.
        """
        # if index != None:
        if index < 0:
            index = len(self.entries) + index
        self._entry_id_to_index_map[entry.entry_id] = index
        # else:
        # 	self._entry_id_to_index_map[entry.id_] = self.entries.index(entry)

    def _map_collation_id_to_index(self, collation: Collation, index: int) -> None:
        """
        Maps a Collation's ID to the Collation's Index in self.collations.
        Uses _entry_id_to_index_map.
        """
        # if index != None:
        if index < 0:
            index = len(self.collations) + index
        self._collation_id_to_index_map[collation.id] = index

    def add_tag_to_library(self, tag: Tag) -> int:
        """
        Adds a Tag to the Library. ⚠️Only use at runtime! (Cannot reference tags that are not loaded yet)⚠️\n
        For adding Tags from the Library save file, append Tags to the Tags list
        and then map them using map_library_tags().
        """
        tag.subtag_ids = [x for x in tag.subtag_ids if x != tag.id]
        tag.id = self._next_tag_id
        self._next_tag_id += 1

        self._map_tag_strings_to_tag_id(tag)
        self.tags.append(tag)  # Must be appended before mapping the index!
        self._map_tag_id_to_index(tag, -1)
        self._map_tag_id_to_cluster(tag)

        return tag.id

    def get_tag(self, tag_id: int) -> Tag:
        """Returns a Tag object given a Tag ID.
        If not already cached in the Library, fetch from the DataSource."""
        if tag_id in self.tags:
            tag = self.tags[tag_id]
        else:
            tag = self.data_source.get_tag(tag_id)
            self.tags[tag_id] = tag
        return tag

    def get_tag_cluster(self, tag_id: int) -> list[int]:
        """Returns a list of Tag IDs that reference this Tag."""
        return self.get_tag(tag_id).parents
