# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

"""The core classes and methods of TagStudio."""

import json
from pathlib import Path

from src.core.constants import TS_FOLDER_NAME
from src.core.library import Entry, Library
from src.core.library.alchemy.fields import _FieldID
from src.core.utils.missing_files import logger


class TagStudioCore:
    def __init__(self):
        self.lib: Library = Library()

    @classmethod
    def get_gdl_sidecar(cls, filepath: Path, source: str = "") -> dict:
        """Attempt to open and dump a Gallery-DL Sidecar file for the filepath.

        Return a formatted object with notable values or an empty object if none is found.
        """
        info = {}
        _filepath = filepath.parent / (filepath.name + ".json")

        # NOTE: This fixes an unknown (recent?) bug in Gallery-DL where Instagram sidecar
        # files may be downloaded with indices starting at 1 rather than 0, unlike the posts.
        # This may only occur with sidecar files that are downloaded separate from posts.
        if source == "instagram" and not _filepath.is_file():
            newstem = _filepath.stem[:-16] + "1" + _filepath.stem[-15:]
            _filepath = _filepath.parent / (newstem + ".json")

        logger.info("get_gdl_sidecar", filepath=filepath, source=source, sidecar=_filepath)

        try:
            with open(_filepath, encoding="utf8") as f:
                json_dump = json.load(f)
                if not json_dump:
                    return {}

                if source == "twitter":
                    info[_FieldID.DESCRIPTION] = json_dump["content"].strip()
                    info[_FieldID.DATE_PUBLISHED] = json_dump["date"]
                elif source == "instagram":
                    info[_FieldID.DESCRIPTION] = json_dump["description"].strip()
                    info[_FieldID.DATE_PUBLISHED] = json_dump["date"]
                elif source == "artstation":
                    info[_FieldID.TITLE] = json_dump["title"].strip()
                    info[_FieldID.ARTIST] = json_dump["user"]["full_name"].strip()
                    info[_FieldID.DESCRIPTION] = json_dump["description"].strip()
                    info[_FieldID.TAGS] = json_dump["tags"]
                    # info["tags"] = [x for x in json_dump["mediums"]["name"]]
                    info[_FieldID.DATE_PUBLISHED] = json_dump["date"]
                elif source == "newgrounds":
                    # info["title"] = json_dump["title"]
                    # info["artist"] = json_dump["artist"]
                    # info["description"] = json_dump["description"]
                    info[_FieldID.TAGS] = json_dump["tags"]
                    info[_FieldID.DATE_PUBLISHED] = json_dump["date"]
                    info[_FieldID.ARTIST] = json_dump["user"].strip()
                    info[_FieldID.DESCRIPTION] = json_dump["description"].strip()
                    info[_FieldID.SOURCE] = json_dump["post_url"].strip()

        except Exception:
            logger.exception("Error handling sidecar file.", path=_filepath)

        return info

    # def scrape(self, entry_id):
    # 	entry = self.lib.get_entry(entry_id)
    # 	if entry.fields:
    # 		urls: list[str] = []
    # 		if self.lib.get_field_index_in_entry(entry, 21):
    # 			urls.extend([self.lib.get_field_attr(entry.fields[x], 'content')
    # 						for x in self.lib.get_field_index_in_entry(entry, 21)])
    # 		if self.lib.get_field_index_in_entry(entry, 3):
    # 			urls.extend([self.lib.get_field_attr(entry.fields[x], 'content')
    # 						for x in self.lib.get_field_index_in_entry(entry, 3)])
    # 	# try:
    # 	if urls:
    # 		for url in urls:
    # 			url = "https://" + url if 'https://' not in url else url
    # 			html_doc = requests.get(url).text
    # 			soup = bs(html_doc, "html.parser")
    # 			print(soup)
    # 			input()

    # 	# except:
    # 	# 	# print("Could not resolve URL.")
    # 	# 	pass

    @classmethod
    def match_conditions(cls, lib: Library, entry_id: int) -> bool:
        """Match defined conditions against a file to add Entry data."""
        # TODO - what even is this file format?
        # TODO: Make this stored somewhere better instead of temporarily in this JSON file.
        cond_file = lib.library_dir / TS_FOLDER_NAME / "conditions.json"
        if not cond_file.is_file():
            return False

        entry: Entry = lib.get_entry(entry_id)

        try:
            with open(cond_file, encoding="utf8") as f:
                json_dump = json.load(f)
                for c in json_dump["conditions"]:
                    match: bool = False
                    for path_c in c["path_conditions"]:
                        if Path(path_c).is_relative_to(entry.path):
                            match = True
                            break

                    if not match:
                        return False

                    if not c.get("fields"):
                        return False

                    fields = c["fields"]
                    entry_field_types = {field.type_key: field for field in entry.fields}

                    for field in fields:
                        is_new = field["id"] not in entry_field_types
                        field_key = field["id"]
                        if is_new:
                            lib.add_field_to_entry(entry.id, field_key, field["value"])
                        else:
                            lib.update_entry_field(entry.id, field_key, field["value"])

        except Exception:
            logger.exception("Error matching conditions.", entry=entry)

        return False

    @classmethod
    def build_url(cls, entry: Entry, source: str):
        """Try to rebuild a source URL given a specific filename structure."""
        source = source.lower().replace("-", " ").replace("_", " ")
        if "twitter" in source:
            return cls._build_twitter_url(entry)
        elif "instagram" in source:
            return cls._build_instagram_url(entry)

    @classmethod
    def _build_twitter_url(cls, entry: Entry):
        """Build a Twitter URL given a specific filename structure.

        Method expects filename to be formatted as 'USERNAME_TWEET-ID_INDEX_YEAR-MM-DD'
        """
        try:
            stubs = str(entry.path.name).rsplit("_", 3)
            url = f"www.twitter.com/{stubs[0]}/status/{stubs[-3]}/photo/{stubs[-2]}"
            return url
        except Exception:
            logger.exception("Error building Twitter URL.", entry=entry)
            return ""

    @classmethod
    def _build_instagram_url(cls, entry: Entry):
        """Build an Instagram URL given a specific filename structure.

        Method expects filename to be formatted as 'USERNAME_POST-ID_INDEX_YEAR-MM-DD'
        """
        try:
            stubs = str(entry.path.name).rsplit("_", 2)
            # stubs[0] = stubs[0].replace(f"{author}_", '', 1)
            # print(stubs)
            # NOTE: Both Instagram usernames AND their ID can have underscores in them,
            # so unless you have the exact username (which can change) on hand to remove,
            # your other best bet is to hope that the ID is only 11 characters long, which
            # seems to more or less be the case... for now...
            url = f"www.instagram.com/p/{stubs[-3][-11:]}"
            return url
        except Exception:
            logger.exception("Error building Instagram URL.", entry=entry)
            return ""
