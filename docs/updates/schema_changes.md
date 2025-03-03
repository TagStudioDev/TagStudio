# Save Format Changes

This page outlines the various changes made the TagStudio save file format over time, sometimes referred to as the "database" or "database file".

## JSON

| First Used | Last Used                                                               | Format | Location                                      |
| ---------- | ----------------------------------------------------------------------- | ------ | --------------------------------------------- |
| v1.0.0     | [v9.4.2](https://github.com/TagStudioDev/TagStudio/releases/tag/v9.4.2) | JSON   | `<Library Folder>`/.TagStudio/ts_library.json |

The legacy database format for public TagStudio releases [v9.1](https://github.com/TagStudioDev/TagStudio/tree/Alpha-v9.1) through [v9.4.2](https://github.com/TagStudioDev/TagStudio/releases/tag/v9.4.2). Variations of this format had been used privately since v1.0.0.

Replaced by the new SQLite format introduced in TagStudio [v9.5.0 Pre-Release 1](https://github.com/TagStudioDev/TagStudio/releases/tag/v9.5.0-pr1).

## DB_VERSION 6

| First Used                                                                      | Last Used                                                                       | Format | Location                                        |
| ------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- | ------ | ----------------------------------------------- |
| [v9.5.0-PR1](https://github.com/TagStudioDev/TagStudio/releases/tag/v9.5.0-pr1) | [v9.5.0-PR1](https://github.com/TagStudioDev/TagStudio/releases/tag/v9.5.0-pr1) | SQLite | `<Library Folder>`/.TagStudio/ts_library.sqlite |

The first public version of the SQLite save file format.

Migration from the legacy JSON format is provided via a walkthrough when opening a legacy library in TagStudio [v9.5.0 Pre-Release 1](https://github.com/TagStudioDev/TagStudio/releases/tag/v9.5.0-pr1) or later.

## DB_VERSION 7

| First Used                                                                      | Last Used                                                                       | Format | Location                                        |
| ------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- | ------ | ----------------------------------------------- |
| [v9.5.0-PR2](https://github.com/TagStudioDev/TagStudio/releases/tag/v9.5.0-pr2) | [v9.5.0-PR3](https://github.com/TagStudioDev/TagStudio/releases/tag/v9.5.0-pr3) | SQLite | `<Library Folder>`/.TagStudio/ts_library.sqlite |

### Changes

-   Repairs "Description" fields to use a TEXT_LINE key instead of a TEXT_BOX key.
-   Repairs tags that may have a disambiguation_id pointing towards a deleted tag.

## DB_VERSION 8

| First Used                                                                      | Last Used | Format | Location                                        |
| ------------------------------------------------------------------------------- | --------- | ------ | ----------------------------------------------- |
| [v9.5.0-PR4](https://github.com/TagStudioDev/TagStudio/releases/tag/v9.5.0-pr4) | _Current_ | SQLite | `<Library Folder>`/.TagStudio/ts_library.sqlite |

### Changes

-   Adds the `color_border` column to `tag_colors` table. Used for instructing the [secondary color](../library/tag_color.md#secondary-color) to apply to a tag's border as a new optional behavior.
-   Adds three new default colors: "Burgundy (TagStudio Shades)", "Dark Teal (TagStudio Shades)", and "Dark Lavender (TagStudio Shades)".
-   Updates Neon colors to use the the new `color_border` property.
