# Feature Roadmap

This checklist details the current and remaining features required at a minimum for TagStudio to be considered "Feature Complete". This list is _not_ a definitive list for additional feature requests and PRs as they come in, but rather an outline of my personal core feature set intended for TagStudio.

## Priorities

Features are broken up into the following priority levels, with nested priorities referencing their relative priority for the overall feature (i.e. A [LOW] priority feature can have a [HIGH] priority element but it otherwise still a [LOW] priority item overall):

-   [HIGH] - Core feature
-   [MEDIUM] - Important but not necessary
-   [LOW] - Just nice to have

## Version Milestones

These version milestones are rough estimations for when the previous core features will be added. For a more definitive idea for when features are coming, please reference the current GitHub [milestones](https://github.com/TagStudioDev/TagStudio/milestones).

<!-- prettier-ignore -->
!!! note
    This list was created after the release of version 9.4

### v9.5

#### Core

-   [x] SQL backend [HIGH]

#### Tags

-   [x] Deleting Tags [HIGH]
-   [ ] User-defined tag colors [HIGH]
    -   [x] ID based, not string or hex [HIGH]
    -   [x] Color name [HIGH]
    -   [x] Color value (hex) [HIGH]
    -   [x] Existing colors are now a set of base colors [HIGH]
-   [x] [Tag Categories](../library/tag_categories.md) [HIGH]
    -   [x] Property available for tags that allow the tag and any inheriting from it to be displayed separately in the preview panel under a title [HIGH]

#### Search

-   [x] Boolean operators [HIGH]
-   [x] Filename search [HIGH]
-   [x] File type search [HIGH]
    -   [x] Search by extension (e.g. ".jpg", ".png") [HIGH]
        -   [x] Optional consolidation of extension synonyms (i.e. ".jpg" can equal ".jpeg") [LOW]
    -   [x] Search by media type (e.g. "image", "video", "document") [MEDIUM]
-   [x] Sort by date added [HIGH]

#### UI

-   [x] Translations _(Any applicable)_ [MEDIUM]
-   [x] Unified Media Player [HIGH]
    -   [x] Auto-hiding player controls
    -   [x] Play/Pause [HIGH]
    -   [x] Loop [HIGH]
    -   [x] Toggle Autoplay [MEDIUM]
    -   [x] Volume Control [HIGH]
    -   [x] Toggle Mute [HIGH]
    -   [x] Timeline scrubber [HIGH]
    -   [ ] Fullscreen [MEDIUM]
-   [x] Configurable page size [HIGH]

#### Performance

-   [x] Thumbnail caching [HIGH]

### v9.6

#### Core

-   [ ] Cached file property table (media duration, word count, dimensions, etc.) [MEDIUM]

#### Library

-   [ ] Multiple Root Directories per Library [HIGH]
-   [ ] `.ts_ignore` (`.gitignore`-style glob ignoring) [HIGH]
-   [ ] Sharable Color Packs [MEDIUM]
    -   [ ] Human-readable (TOML) files containing tag data [HIGH]
    -   [ ] Importable [HIGH]
    -   [ ] Exportable [HIGH]

#### Tags

-   [ ] Merging Tags [HIGH]
-   [ ] [Component/HAS](../library/tag.md#component-tags) subtags [HIGH]
-   [ ] Tag Icons [HIGH]
    -   [ ] Small Icons [HIGH]
    -   [ ] Large Icons for Profiles [MEDIUM]
    -   [ ] Built-in Icon Packs (i.e. Boxicons) [HIGH]
    -   [ ] User Defined Icons [HIGH]
-   [ ] Multiple Languages for Tag Strings [MEDIUM]
    -   [ ] Title is tag name [HIGH]
    -   [ ] Title has tag color [MEDIUM]
    -   [ ] Tag marked as category does not display as a tag itself [HIGH]
-   [ ] [Tag Overrides](../library/tag_overrides.md) [MEDIUM]
    -   [ ] Per-file overrides of subtags [HIGH]

#### Fields

-   [ ] Datetime fields [HIGH]
-   [ ] Custom field names [HIGH]

#### Search

-   [ ] Field content search [HIGH]
-   [ ] Sort by date created [HIGH]
-   [ ] Sort by date modified [HIGH]
-   [x] Sort by filename [HIGH]
-   [ ] HAS operator for composition tags [HIGH]
-   [ ] Search bar rework
    -   [ ] Improved tag autocomplete [HIGH]
    -   [ ] Tags appear as widgets in search bar [HIGH]

#### UI

-   [ ] File duration on video thumbnails [HIGH]
-   [ ] 3D Model Previews [MEDIUM]
    -   [ ] STL Previews [HIGH]
-   [ ] Word count/line count on text thumbnails [LOW]
-   [x] Settings Menu [HIGH]
-   [x] Application Settings [HIGH]
    -   [x] Stored in system user folder/designated folder [HIGH]
-   [ ] Library Settings [HIGH]
    -   [ ] Stored in `.TagStudio` folder [HIGH]
-   [ ] Tagging Panel [HIGH]

    Toggleable persistent main window panel or pop-out. Replaces the current tag manager.

    -   [ ] Top Tags [HIGH]
    -   [ ] Recent Tags [HIGH]
    -   [ ] Tag Search [HIGH]
    -   [ ] Pinned Tags [HIGH]

-   [ ] New tabbed tag building UI to support the new tag features [HIGH]

### v9.7

#### Library

-   [ ] [Entry groups](../library/entry_groups.md) [HIGH]
    -   [ ] Groups for files/entries where the same entry can be in multiple groups [HIGH]
    -   [ ] Ability to number entries within group [HIGH]
    -   [ ] Ability to set sorting method for group [HIGH]
    -   [ ] Ability to set custom thumbnail for group [HIGH]
    -   [ ] Group is treated as entry with tags and metadata [HIGH]
    -   [ ] Nested groups [MEDIUM]

#### Search

-   [ ] Sort by relevance [HIGH]
-   [ ] Sort by date taken (photos) [MEDIUM]
-   [ ] Sort by file size [HIGH]
-   [ ] Sort by file dimension (images/video) [LOW]

#### [Macros](../utilities/macro.md)

-   [ ] Sharable Macros [MEDIUM]
    -   [ ] Standard notation format (TOML) contacting macro instructions [HIGH]
    -   [ ] Exportable [HIGH]
    -   [ ] Importable [HIGH]
-   [ ] Triggers [HIGH]
    -   [ ] On new file [HIGH]
    -   [ ] On library refresh [HIGH]
    -   [ ] [...]
-   [ ] Actions [HIGH]
    -   [ ] Add tag(s) [HIGH]
    -   [ ] Add field(s) [HIGH]
    -   [ ] Set field content [HIGH]
    -   [ ] [...]

#### UI

-   [ ] Custom thumbnail overrides [MEDIUM]
-   [ ] Toggle File Extension Label [MEDIUM]
-   [ ] Toggle Duration Label [MEDIUM]
-   [ ] Custom Tag Badges [LOW]
-   [ ] Library list view [HIGH]

### v9.8

#### Library

-   [ ] Automatic Entry Relinking [HIGH]
    -   [ ] Detect Renames [HIGH]
    -   [ ] Detect Moves [HIGH]
    -   [ ] Detect Deletions [HIGH]

#### Search

-   [ ] OCR search [LOW]
-   [ ] Fuzzy Search [LOW]

### v9.9

#### Library

-   [ ] Exportable Library Data [HIGH]
    -   [ ] Standard notation format (i.e. JSON) contacting all library data [HIGH]

#### Tags

-   [ ] Tag Packs [MEDIUM]
    -   [ ] Human-readable (TOML) files containing tag data [HIGH]
    -   [ ] Multiple Languages for Tag Strings [MEDIUM]
    -   [ ] Importable [HIGH]
    -   [ ] Exportable [HIGH]
    -   [ ] Conflict resolution [HIGH]

### v10.0

-   [ ] All remaining [HIGH] and optional [MEDIUM] features

### Post v10.0

#### Core

-   [ ] Core Library/API
-   [ ] Plugin Support
