import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

import structlog

from tagstudio.core.library.alchemy.enums import BrowsingState
from tagstudio.core.library.alchemy.library import Library
from tagstudio.core.library.alchemy.models import Entry

logger = structlog.get_logger()


@dataclass
class DupeRegistry:
    """State handler for DupeGuru results."""

    library: Library
    groups: list[list[Entry]] = field(default_factory=list)

    @property
    def groups_count(self) -> int:
        return len(self.groups)

    def refresh_dupe_files(self, results_filepath: str | Path):
        """Refresh the list of duplicate files.

        A duplicate file is defined as an identical or near-identical file as determined
        by a DupeGuru results file.
        """
        library_dir = self.library.library_dir
        if not isinstance(results_filepath, Path):
            results_filepath = Path(results_filepath)

        if not results_filepath.is_file():
            raise ValueError("invalid file path")

        self.groups.clear()
        tree = ET.parse(results_filepath)
        root = tree.getroot()
        for group in root:
            # print(f'-------------------- Match Group {i}---------------------')
            files: list[Entry] = []
            for element in group:
                if element.tag == "file":
                    file_path = Path(element.attrib.get("path"))

                    try:
                        path_relative = file_path.relative_to(library_dir)
                    except ValueError:
                        # The file is not in the library directory
                        continue

                    results = self.library.search_library(
                        BrowsingState.from_path(path_relative), 500
                    )

                    if not results:
                        # file not in library
                        continue

                    files.append(results[0])

                if not len(files) > 1:
                    # only one file in the group, nothing to do
                    continue

            self.groups.append(files)

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
