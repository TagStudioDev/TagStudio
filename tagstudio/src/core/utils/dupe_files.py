import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

import structlog
from src.core.library import Entry, Library
from src.core.library.alchemy.enums import FilterState

logger = structlog.get_logger()


@dataclass
class DupeRegistry:
    """State handler for DupeGuru results."""

    library: Library
    groups: list[list[Entry]] = field(default_factory=list)

    @property
    def groups_count(self) -> int:
        return len(self.groups)

    def refresh_dupe_files(self, dupe_results: str | Path):
        """Refresh the list of duplicate files.

        A duplicate file is defined as an identical or near-identical file as determined
        by a DupeGuru results file.
        """
        if not isinstance(dupe_results, Path):
            dupe_results = Path(dupe_results)

        if not dupe_results.is_file():
            raise ValueError("invalid file path")

        self.groups.clear()
        tree = ET.parse(dupe_results)
        root = tree.getroot()
        folders = self.library.get_folders()

        for group in root:
            files: dict = {}
            for element in group:
                if element.tag != "file":
                    continue

                file_path = Path(element.attrib.get("path"))
                for folder in folders:
                    if file_path.is_relative_to(folder.path):
                        path_relative = file_path.relative_to(folder.path)
                        results = self.library.search_library(
                            FilterState(
                                include_folders={folder.id},
                                path=path_relative,
                            ),
                        )

                        if results:
                            for item in results.items:
                                files[item.path] = item
                            break
                else:
                    continue

            if not len(files) > 1:
                # only one file in the group, nothing to do
                continue

            self.groups.append(list(files.values()))

    def merge_dupe_entries(self):
        """Merge the duplicate Entry items.

        A duplicate Entry is defined as an Entry pointing to a file
        that one or more other Entries are also pointing to
        """
        logger.info(
            "Consolidating Entries... (This may take a while for larger libraries)",
            groups=len(self.groups),
        )

        for i, entries in enumerate(self.groups):
            remove_ids = [x.id for x in entries[1:]]
            logger.info("Removing entries group", ids=remove_ids)
            self.library.remove_entries(remove_ids)
            yield i - 1  # The -1 waits for the next step to finish
