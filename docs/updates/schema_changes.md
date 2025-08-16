---
icon: material/database-edit
---

# :material-database-edit: Save Format Changes

This page outlines the various changes made to the TagStudio library save file format over time, sometimes referred to as the "database" or "database file".

---

## JSON

Legacy (JSON) library save format versions were tied to the release version of the program itself. This number was stored in a `version` key inside the JSON file.

### Versions 1.0.0 - 9.4.2

| Used From | Used Until                                                              | Format | Location                                      |
| --------- | ----------------------------------------------------------------------- | ------ | --------------------------------------------- |
| v1.0.0    | [v9.4.2](https://github.com/TagStudioDev/TagStudio/releases/tag/v9.4.2) | JSON   | `<Library Folder>`/.TagStudio/ts_library.json |

The legacy database format for public TagStudio releases [v9.1](https://github.com/TagStudioDev/TagStudio/tree/Alpha-v9.1) through [v9.4.2](https://github.com/TagStudioDev/TagStudio/releases/tag/v9.4.2). Variations of this format had been used privately since v1.0.0.

Replaced by the new SQLite format introduced in TagStudio [v9.5.0 Pre-Release 1](https://github.com/TagStudioDev/TagStudio/releases/tag/v9.5.0-pr1).

---

## SQLite

Starting with TagStudio [v9.5.0-pr1](https://github.com/TagStudioDev/TagStudio/releases/tag/v9.5.0-pr1), the library save format has been moved to a [SQLite](https://sqlite.org) format. Legacy JSON libraries are migrated (with the user's consent) to the new format when opening in current versions of the program. The save format versioning is now separate from the program's versioning number and stored inside a `DB_VERSION` attribute inside the SQLite file.

### Versions 1 - 5

These versions were used while developing the new SQLite file format, outside any official or recommended release. These versions **were never supported** in any official capacity and were actively warned against using for real libraries.

---

### Version 6

| Used From                                                                       | Used Until                                                                      | Format | Location                                        |
| ------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- | ------ | ----------------------------------------------- |
| [v9.5.0-pr1](https://github.com/TagStudioDev/TagStudio/releases/tag/v9.5.0-pr1) | [v9.5.0-pr1](https://github.com/TagStudioDev/TagStudio/releases/tag/v9.5.0-pr1) | SQLite | `<Library Folder>`/.TagStudio/ts_library.sqlite |

The first public version of the SQLite save file format.

Migration from the legacy JSON format is provided via a walkthrough when opening a legacy library in TagStudio [v9.5.0 Pre-Release 1](https://github.com/TagStudioDev/TagStudio/releases/tag/v9.5.0-pr1) or later.

---

### Version 7

| Used From                                                                       | Used Until                                                                      | Format | Location                                        |
| ------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- | ------ | ----------------------------------------------- |
| [v9.5.0-pr2](https://github.com/TagStudioDev/TagStudio/releases/tag/v9.5.0-pr2) | [v9.5.0-pr3](https://github.com/TagStudioDev/TagStudio/releases/tag/v9.5.0-pr3) | SQLite | `<Library Folder>`/.TagStudio/ts_library.sqlite |

-   Repairs "Description" fields to use a TEXT_LINE key instead of a TEXT_BOX key.
-   Repairs tags that may have a disambiguation_id pointing towards a deleted tag.

---

### Version 8

| Used From                                                                       | Used Until                                                              | Format | Location                                        |
| ------------------------------------------------------------------------------- | ----------------------------------------------------------------------- | ------ | ----------------------------------------------- |
| [v9.5.0-pr4](https://github.com/TagStudioDev/TagStudio/releases/tag/v9.5.0-pr4) | [v9.5.1](https://github.com/TagStudioDev/TagStudio/releases/tag/v9.5.1) | SQLite | `<Library Folder>`/.TagStudio/ts_library.sqlite |

-   Adds the `color_border` column to the `tag_colors` table. Used for instructing the [secondary color](../library/tag_color.md#secondary-color) to apply to a tag's border as a new optional behavior.
-   Adds three new default colors: "Burgundy (TagStudio Shades)", "Dark Teal (TagStudio Shades)", and "Dark Lavender (TagStudio Shades)".
-   Updates Neon colors to use the new `color_border` property.

---

### Version 9

| Used From                                                               | Used Until | Format | Location                                        |
| ----------------------------------------------------------------------- | ---------- | ------ | ----------------------------------------------- |
| [v9.5.2](https://github.com/TagStudioDev/TagStudio/releases/tag/v9.5.2) | _Current_  | SQLite | `<Library Folder>`/.TagStudio/ts_library.sqlite |

-   Adds the `filename` column to the `entries` table. Used for sorting entries by filename in search results.
