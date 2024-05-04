# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

"""The core classes and methods of TagStudio."""

import json
import os

from src.core.library import Entry, Library

VERSION: str = "9.2.0"  # Major.Minor.Patch
VERSION_BRANCH: str = "Alpha"  # 'Alpha', 'Beta', or '' for Full Release

# The folder & file names where TagStudio keeps its data relative to a library.
TS_FOLDER_NAME: str = ".TagStudio"
BACKUP_FOLDER_NAME: str = "backups"
COLLAGE_FOLDER_NAME: str = "collages"
LIBRARY_FILENAME: str = "ts_library.json"

# TODO: Turn this whitelist into a user-configurable blacklist.
IMAGE_TYPES: list[str] = [
    "png",
    "jpg",
    "jpeg",
    "jpg_large",
    "jpeg_large",
    "jfif",
    "gif",
    "tif",
    "tiff",
    "heic",
    "heif",
    "webp",
    "bmp",
    "svg",
    "avif",
    "apng",
    "jp2",
    "j2k",
    "jpg2",
]
VIDEO_TYPES: list[str] = [
    "mp4",
    "webm",
    "mov",
    "hevc",
    "mkv",
    "avi",
    "wmv",
    "flv",
    "gifv",
    "m4p",
    "m4v",
    "3gp",
]
AUDIO_TYPES: list[str] = [
    "mp3",
    "mp4",
    "mpeg4",
    "m4a",
    "aac",
    "wav",
    "flac",
    "alac",
    "wma",
    "ogg",
    "aiff",
]
DOC_TYPES: list[str] = ["txt", "rtf", "md", "doc", "docx", "pdf", "tex", "odt", "pages"]
PLAINTEXT_TYPES: list[str] = [
    "txt",
    "md",
    "css",
    "html",
    "xml",
    "json",
    "js",
    "ts",
    "ini",
    "htm",
    "csv",
    "php",
    "sh",
    "bat",
]
SPREADSHEET_TYPES: list[str] = ["csv", "xls", "xlsx", "numbers", "ods"]
PRESENTATION_TYPES: list[str] = ["ppt", "pptx", "key", "odp"]
ARCHIVE_TYPES: list[str] = ["zip", "rar", "tar", "tar.gz", "tgz", "7z"]
PROGRAM_TYPES: list[str] = ["exe", "app"]
SHORTCUT_TYPES: list[str] = ["lnk", "desktop", "url"]

ALL_FILE_TYPES: list[str] = (
    IMAGE_TYPES
    + VIDEO_TYPES
    + AUDIO_TYPES
    + DOC_TYPES
    + SPREADSHEET_TYPES
    + PRESENTATION_TYPES
    + ARCHIVE_TYPES
    + PROGRAM_TYPES
    + SHORTCUT_TYPES
)

BOX_FIELDS = ["tag_box", "text_box"]
TEXT_FIELDS = ["text_line", "text_box"]
DATE_FIELDS = ["datetime"]

TAG_COLORS = [
    "",
    "black",
    "dark gray",
    "gray",
    "light gray",
    "white",
    "light pink",
    "pink",
    "red",
    "red orange",
    "orange",
    "yellow orange",
    "yellow",
    "lime",
    "light green",
    "mint",
    "green",
    "teal",
    "cyan",
    "light blue",
    "blue",
    "blue violet",
    "violet",
    "purple",
    "lavender",
    "berry",
    "magenta",
    "salmon",
    "auburn",
    "dark brown",
    "brown",
    "light brown",
    "blonde",
    "peach",
    "warm gray",
    "cool gray",
    "olive",
]


class TagStudioCore:
    """
    Instantiate this to establish a TagStudio session.
    Holds all TagStudio session data and provides methods to manage it.
    """

    def __init__(self):
        self.lib: Library = Library()

    def get_gdl_sidecar(self, filepath: str, source: str = "") -> dict:
        """
        Attempts to open and dump a Gallery-DL Sidecar sidecar file for
        the filepath.\n Returns a formatted object with notable values or an
        empty object if none is found.
        """
        json_dump = {}
        info = {}

        # NOTE: This fixes an unknown (recent?) bug in Gallery-DL where Instagram sidecar
        # files may be downloaded with indices starting at 1 rather than 0, unlike the posts.
        # This may only occur with sidecar files that are downloaded separate from posts.
        if source == "instagram":
            if not os.path.isfile(os.path.normpath(filepath + ".json")):
                filepath = filepath[:-16] + "1" + filepath[-15:]

        try:
            with open(os.path.normpath(filepath + ".json"), "r", encoding="utf8") as f:
                json_dump = json.load(f)

                if json_dump:
                    if source == "twitter":
                        info["content"] = json_dump["content"].strip()
                        info["date_published"] = json_dump["date"]
                    elif source == "instagram":
                        info["description"] = json_dump["description"].strip()
                        info["date_published"] = json_dump["date"]
                    elif source == "artstation":
                        info["title"] = json_dump["title"].strip()
                        info["artist"] = json_dump["user"]["full_name"].strip()
                        info["description"] = json_dump["description"].strip()
                        info["tags"] = json_dump["tags"]
                        # info["tags"] = [x for x in json_dump["mediums"]["name"]]
                        info["date_published"] = json_dump["date"]
                    elif source == "newgrounds":
                        # info["title"] = json_dump["title"]
                        # info["artist"] = json_dump["artist"]
                        # info["description"] = json_dump["description"]
                        info["tags"] = json_dump["tags"]
                        info["date_published"] = json_dump["date"]
                        info["artist"] = json_dump["user"].strip()
                        info["description"] = json_dump["description"].strip()
                        info["source"] = json_dump["post_url"].strip()
                    # else:
                    # 	print(
                    # 		f'[INFO]: TagStudio does not currently support sidecar files for "{source}"')

        # except FileNotFoundError:
        except:
            # print(
            # 	f'[INFO]: No sidecar file found at "{os.path.normpath(file_path + ".json")}"')
            pass

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

    def match_conditions(self, entry_id: int) -> None:
        """Matches defined conditions against a file to add Entry data."""

        cond_file = os.path.normpath(
            f"{self.lib.library_dir}/{TS_FOLDER_NAME}/conditions.json"
        )
        # TODO: Make this stored somewhere better instead of temporarily in this JSON file.
        entry: Entry = self.lib.get_entry(entry_id)
        try:
            if os.path.isfile(cond_file):
                with open(cond_file, "r", encoding="utf8") as f:
                    json_dump = json.load(f)
                    for c in json_dump["conditions"]:
                        match: bool = False
                        for path_c in c["path_conditions"]:
                            if os.path.normpath(path_c) in entry.path:
                                match = True
                                break
                        if match:
                            if fields := c.get("fields"):
                                for field in fields:
                                    field_id = self.lib.get_field_attr(field, "id")
                                    content = field[field_id]

                                    if (
                                        self.lib.get_field_obj(int(field_id))["type"]
                                        == "tag_box"
                                    ):
                                        existing_fields: list[int] = (
                                            self.lib.get_field_index_in_entry(
                                                entry, field_id
                                            )
                                        )
                                        if existing_fields:
                                            self.lib.update_entry_field(
                                                entry_id,
                                                existing_fields[0],
                                                content,
                                                "append",
                                            )
                                        else:
                                            self.lib.add_field_to_entry(
                                                entry_id, field_id
                                            )
                                            self.lib.update_entry_field(
                                                entry_id, -1, content, "append"
                                            )

                                    if (
                                        self.lib.get_field_obj(int(field_id))["type"]
                                        in TEXT_FIELDS
                                    ):
                                        if not self.lib.does_field_content_exist(
                                            entry_id, field_id, content
                                        ):
                                            self.lib.add_field_to_entry(
                                                entry_id, field_id
                                            )
                                            self.lib.update_entry_field(
                                                entry_id, -1, content, "replace"
                                            )
        except:
            print("Error in match_conditions...")
            # input()
            pass

    def build_url(self, entry_id: int, source: str) -> str:
        """Tries to rebuild a source URL given a specific filename structure."""

        source = source.lower().replace("-", " ").replace("_", " ")
        if "twitter" in source:
            return self._build_twitter_url(entry_id)
        elif "instagram" in source:
            return self._build_instagram_url(entry_id)

    def _build_twitter_url(self, entry_id: int):
        """
        Builds an Twitter URL given a specific filename structure.
        Method expects filename to be formatted as 'USERNAME_TWEET-ID_INDEX_YEAR-MM-DD'
        """
        try:
            entry = self.lib.get_entry(entry_id)
            stubs = entry.filename.rsplit("_", 3)
            # print(stubs)
            # source, author = os.path.split(entry.path)
            url = f"www.twitter.com/{stubs[0]}/status/{stubs[-3]}/photo/{stubs[-2]}"
            return url
        except:
            return ""

    def _build_instagram_url(self, entry_id: int):
        """
        Builds an Instagram URL given a specific filename structure.
        Method expects filename to be formatted as 'USERNAME_POST-ID_INDEX_YEAR-MM-DD'
        """
        try:
            entry = self.lib.get_entry(entry_id)
            stubs = entry.filename.rsplit("_", 2)
            # stubs[0] = stubs[0].replace(f"{author}_", '', 1)
            # print(stubs)
            # NOTE: Both Instagram usernames AND their ID can have underscores in them,
            # so unless you have the exact username (which can change) on hand to remove,
            # your other best bet is to hope that the ID is only 11 characters long, which
            # seems to more or less be the case... for now...
            url = f"www.instagram.com/p/{stubs[-3][-11:]}"
            return url
        except:
            return ""
