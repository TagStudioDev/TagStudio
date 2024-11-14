# Roadmap

This checklist details the current and remaining features required at a minimum for TagStudio to be considered “Feature Complete”. This list is _not_ a definitive list for additional feature requests and PRs as they come in, but rather an outline of my personal core feature set intended for TagStudio.

## Priorities

Features are broken up into the following priority levels, with nested priorities referencing their relative priority for the overall feature (i.e. A [LOW] priority feature can have a [HIGH] priority element but it otherwise still a [LOW] priority item overall):

-   [HIGH] - Core feature
-   [MEDIUM] - Important but not necessary
-   [LOW] - Just nice to have

## Core Feature List

-   [ ] Tags [HIGH]
    -   [x] ID-based, not string based [HIGH]
    -   [x] Tag name [HIGH]
    -   [x] Tag alias list, aka alternate names [HIGH]
    -   [x] Tag shorthand (specific short alias for displaying) [HIGH]
    -   [x] Parent/Inheritance subtags [HIGH]
    -   [ ] Composition/HAS subtags [HIGH]
    -   [ ] Deleting Tags [HIGH] [#148](https://github.com/TagStudioDev/TagStudio/issues/148)
    -   [ ] Merging Tags [HIGH] [#12](https://github.com/TagStudioDev/TagStudio/issues/12)
    -   [ ] Tag Icons [HIGH] [#195](https://github.com/TagStudioDev/TagStudio/issues/195)
        -   [ ] Small Icons [HIGH]
        -   [ ] Large Icons for Profiles [MEDIUM]
        -   [ ] Built-in Icon Packs (i.e. Boxicons) [HIGH]
        -   [ ] User Defined Icons [HIGH]
    -   [ ] Multiple Languages for Tag Strings [MEDIUM]
    -   [ ] User-defined tag colors [HIGH] [#264](https://github.com/TagStudioDev/TagStudio/issues/264)
        -   [ ] ID based, not string or hex [HIGH]
        -   [ ] Color name [HIGH]
        -   [ ] Color value (hex) [HIGH]
        -   [ ] Existing colors are now a set of base colors [HIGH]
            -   [ ] Editable [MEDIUM]
            -   [ ] Non-removable [HIGH]
    -   [ ] [Tag Categories](../library/tag_categories.md) [HIGH]
        -   [ ] Property available for tags that allow the tag and any inheriting from it to be displayed separately in the preview panel under a title [HIGH]
        -   [ ] Title is tag name [HIGH]
        -   [ ] Title has tag color [MEDIUM]
        -   [ ] Tag marked as category does not display as a tag itself [HIGH]
    -   [ ] [Tag Overrides](../library/tag_overrides.md) [MEDIUM]
        -   [ ] Per-file overrides of subtags [HIGH]
-   [ ] Tag Packs [MEDIUM] [#3](https://github.com/TagStudioDev/TagStudio/issues/3)
    -   [ ] Human-readable (i.e. JSON) files containing tag data [HIGH]
    -   [ ] Importable [HIGH]
    -   [ ] Exportable [HIGH]
    -   [ ] Conflict resolution [HIGH]
    -   [ ] Color Packs [MEDIUM]
        -   [ ] Human-readable (i.e. JSON) files containing tag data [HIGH]
        -   [ ] Importable [HIGH]
        -   [ ] Exportable [HIGH]
-   [ ] Exportable Library Data [HIGH] [#47](https://github.com/TagStudioDev/TagStudio/issues/47)
    -   [ ] Standard notation format (i.e. JSON) contacting all library data [HIGH]
-   [ ] [Macros](../utilities/macro.md) [HIGH]
    -   [ ] Sharable Macros [MEDIUM]
        -   [ ] Standard notation format (i.e. JSON) contacting macro instructions [HIGH]
        -   [ ] Exportable [HIGH]
        -   [ ] Importable [HIGH]
    -   [ ] Triggers [HIGH]
        -   [ ] On new file [HIGH]
        -   [ ] On library refresh [HIGH]
        -   [...]
    -   [ ] Actions [HIGH]
        -   [ ] Add tag(s) [HIGH]
        -   [ ] Add field(s) [HIGH]
        -   [ ] Set field content [HIGH]
        -   [ ] [...]
-   [ ] Settings Menu [HIGH]
    -   [ ] Application Settings [HIGH]
        -   [ ] Stored in system user folder/designated folder [HIGH]
    -   [ ] Library Settings [HIGH]
        -   [ ] Stored in `.TagStudio` folder [HIGH]
-   [ ] Multiple Root Directories per Library [HIGH] [#295](https://github.com/TagStudioDev/TagStudio/issues/295)
-   [ ] [Entry groups](../library/entry_groups.md) [HIGH]
    -   [ ] Groups for files/entries where the same entry can be in multiple groups [HIGH]
    -   [ ] Ability to number entries within group [HIGH]
    -   [ ] Ability to set sorting method for group [HIGH]
    -   [ ] Ability to set custom thumbnail for group [HIGH]
    -   [ ] Group is treated as entry with tags and metadata [HIGH]
    -   [ ] Nested groups [MEDIUM]
-   [ ] Fields [HIGH]
    -   [x] Text Boxes [HIGH]
    -   [x] Text Lines [HIGH]
    -   [ ] Dates [HIGH] [#213](https://github.com/TagStudioDev/TagStudio/issues/213)
    -   [ ] GPS Location [LOW]
    -   [ ] Custom field names [HIGH] [#18](https://github.com/TagStudioDev/TagStudio/issues/18)
-   [ ] Search engine [HIGH] [#325](https://github.com/TagStudioDev/TagStudio/issues/325)
    -   [ ] Boolean operators [HIGH] [#225](https://github.com/TagStudioDev/TagStudio/issues/225), [#314](https://github.com/TagStudioDev/TagStudio/issues/314)
    -   [ ] Tag objects + autocomplete [HIGH] [#476 (Autocomplete)](https://github.com/TagStudioDev/TagStudio/issues/476)
    -   [ ] Filename search [HIGH]
    -   [ ] Filetype search [HIGH]
        -   [ ] Search by extension (e.g. ".jpg", ".png") [HIGH]
            -   [ ] Optional consolidation of extension synonyms (i.e. ".jpg" can equal ".jpeg") [LOW]
        -   [ ] Search by media type (e.g. "image", "video", "document") [MEDIUM]
    -   [ ] Field content search [HIGH] [#272](https://github.com/TagStudioDev/TagStudio/issues/272)
    -   [ ] HAS operator for composition tags [HIGH]
    -   [ ] OCR search [LOW]
    -   [ ] Fuzzy Search [LOW] [#400](https://github.com/TagStudioDev/TagStudio/issues/400)
    -   [ ] Sortable results [HIGH] [#68](https://github.com/TagStudioDev/TagStudio/issues/68)
        -   [ ] Sort by relevance [HIGH]
        -   [ ] Sort by date created [HIGH]
        -   [ ] Sort by date modified [HIGH]
        -   [ ] Sort by date taken (photos) [MEDIUM]
        -   [ ] Sort by file size [HIGH]
        -   [ ] Sort by file dimension (images/video) [LOW]
-   [ ] Automatic Entry Relinking [HIGH] [#36](https://github.com/TagStudioDev/TagStudio/issues/36)
    -   [ ] Detect Renames [HIGH]
    -   [ ] Detect Moves [HIGH]
    -   [ ] Detect Deletions [HIGH]
-   [ ] Image Collages [LOW] [#91](https://github.com/TagStudioDev/TagStudio/issues/91)
    -   [ ] UI [HIGH]
-   [ ] Tagging Panel [HIGH]
    -   [ ] Top Tags [HIGH]
    -   [ ] Recent Tags [HIGH]
    -   [ ] Tag Search [HIGH]
    -   [ ] Pinned Tags [HIGH]
-   [ ] Configurable Thumbnails [MEDIUM]
    -   [ ] Custom thumbnail override [HIGH]
    -   [ ] Toggle File Extension Label [MEDIUM]
    -   [ ] Toggle Duration Label [MEDIUM]
    -   [ ] Custom Tag Badges [LOW]
-   [ ] Thumbnails [HIGH]
    -   [ ] File Duration Label [HIGH]
    -   [ ] 3D Model Previews [LOW]
        -   [ ] STL Previews [HIGH] [#351](https://github.com/TagStudioDev/TagStudio/issues/351)
-   [x] Drag and Drop [HIGH]
    -   [x] Drag files _to_ other programs [HIGH]
    -   [x] Drag files _to_ file explorer windows [MEDIUM]
    -   [x] Drag files _from_ file explorer windows [MEDIUM]
    -   [x] Drag files _from_ other programs [LOW]
-   [ ] File Preview Panel [HIGH]
    -   [ ] Video Playback [HIGH]
        -   [x] Play/Pause [HIGH]
        -   [x] Loop [HIGH]
        -   [x] Toggle Autoplay [MEDIUM]
        -   [ ] Volume Control [HIGH]
        -   [x] Toggle Mute [HIGH]
        -   [ ] Timeline scrubber [HIGH]
        -   [ ] Fullscreen [MEDIUM]
    -   [ ] Audio Playback [HIGH] [#450](https://github.com/TagStudioDev/TagStudio/issues/450)
        -   [ ] Play/Pause [HIGH]
        -   [ ] Loop [HIGH]
        -   [ ] Toggle Autoplay [MEDIUM]
        -   [ ] Volume Control [HIGH]
        -   [ ] Toggle Mute [HIGH]
        -   [x] Timeline scrubber [HIGH]
        -   [ ] Fullscreen [MEDIUM]
-   [ ] Optimizations [HIGH]
    -   [ ] Thumbnail caching [HIGH] [#104](https://github.com/TagStudioDev/TagStudio/issues/104)
    -   [ ] File property indexes [HIGH]

## Version Milestones

These version milestones are rough estimations for when the previous core features will be added. For a more definitive idea for when features are coming, please reference the current GitHub [milestones](https://github.com/TagStudioDev/TagStudio/milestones).

### 9.5 (Alpha)

-   [ ] SQL backend [HIGH]
-   [ ] Translations _(Any applicable)_ [MEDIUM]
-   [ ] Multiple Root Directories per Library [HIGH]
-   [ ] Tags [HIGH]
    -   [ ] Deleting Tags [HIGH]
    -   [ ] Merging Tags [HIGH]
    -   [ ] User-defined tag colors [HIGH]
        -   [ ] ID based, not string or hex [HIGH]
        -   [ ] Color name [HIGH]
        -   [ ] Color value (hex) [HIGH]
        -   [ ] Existing colors are now a set of base colors [HIGH]
            -   [ ] Editable [MEDIUM]
            -   [ ] Non-removable [HIGH]
-   [ ] Search engine [HIGH]
    -   [ ] Boolean operators [HIGH]
    -   [ ] Tag objects + autocomplete [HIGH]
    -   [ ] Filename search [HIGH]
    -   [ ] Filetype search [HIGH]
    -   [ ] Field content search [HIGH]
    -   [ ] Sortable results [HIGH]
        -   [ ] Sort by relevance [HIGH]
        -   [ ] Sort by date created [HIGH]
        -   [ ] Sort by date modified [HIGH]
        -   [ ] Sort by date taken (photos) [MEDIUM]
        -   [ ] Sort by file size [HIGH]
        -   [ ] Sort by file dimension (images/video) [LOW]
-   [ ] Settings Menu [HIGH]
    -   [ ] Application Settings [HIGH]
        -   [ ] Stored in system user folder/designated folder [HIGH]
    -   [ ] Library Settings [HIGH]
        -   [ ] Stored in `.TagStudio` folder [HIGH]
-   [ ] Optimizations [HIGH]
    -   [ ] Thumbnail caching [HIGH]

### 9.6 (Alpha)

-   [ ] Tags [HIGH]
    -   [ ] Composition/HAS subtags [HIGH]
    -   [ ] Tag Icons [HIGH]
        -   [ ] Small Icons [HIGH]
        -   [ ] Large Icons for Profiles [MEDIUM]
        -   [ ] Built-in Icon Packs (i.e. Boxicons) [HIGH]
        -   [ ] User Defined Icons [HIGH]
    -   [ ] Multiple Languages for Tag Strings [MEDIUM]
    -   [ ] [Tag Categories](../library/tag_categories.md) [HIGH]
        -   [ ] Property available for tags that allow the tag and any inheriting from it to be displayed separately in the preview panel under a title [HIGH]
        -   [ ] Title is tag name [HIGH]
        -   [ ] Title has tag color [MEDIUM]
        -   [ ] Tag marked as category does not display as a tag itself [HIGH]
    -   [ ] [Tag Overrides](../library/tag_overrides.md) [MEDIUM]
        -   [ ] Per-file overrides of subtags [HIGH]
-   [ ] Fields [HIGH]
    -   [ ] Dates [HIGH]
    -   [ ] Custom field names [HIGH]

### 9.7 (Alpha)

-   [ ] Configurable Thumbnails [MEDIUM]
    -   [ ] Toggle File Extension Label [MEDIUM]
    -   [ ] Toggle Duration Label [MEDIUM]
    -   [ ] Custom Tag Badges [LOW]
-   [ ] Thumbnails [HIGH]
    -   [ ] File Duration Label [HIGH]
-   [ ] [Entry groups](../library/entry_groups.md) [HIGH]
    -   [ ] Groups for files/entries where the same entry can be in multiple groups [HIGH]
    -   [ ] Ability to number entries within group [HIGH]
    -   [ ] Ability to set sorting method for group [HIGH]
    -   [ ] Ability to set custom thumbnail for group [HIGH]
    -   [ ] Group is treated as entry with tags and metadata [HIGH]
    -   [ ] Nested groups [MEDIUM]
-   [ ] Tagging Panel [HIGH]
    -   [ ] Top Tags [HIGH]
    -   [ ] Recent Tags [HIGH]
    -   [ ] Tag Search [HIGH]
    -   [ ] Pinned Tags [HIGH]

### 9.8 (Possible Beta)

-   [ ] Automatic Entry Relinking [HIGH]
    -   [ ] Detect Renames [HIGH]
    -   [ ] Detect Moves [HIGH]
    -   [ ] Detect Deletions [HIGH]
-   [ ] [Macros](../utilities/macro.md) [HIGH]
    -   [ ] Sharable Macros [MEDIUM]
        -   [ ] Standard notation format (i.e. JSON) contacting macro instructions [HIGH]
        -   [ ] Exportable [HIGH]
        -   [ ] Importable [HIGH]
    -   [ ] Triggers [HIGH]
        -   [ ] On new file [HIGH]
        -   [ ] On library refresh [HIGH]
        -   [...]
    -   [ ] Actions [HIGH]
        -   [ ] Add tag(s) [HIGH]
        -   [ ] Add field(s) [HIGH]
        -   [ ] Set field content [HIGH]
        -   [ ] [...]

### 9.9 (Possible Beta)

-   [ ] Tag Packs [MEDIUM]
    -   [ ] Human-readable (i.e. JSON) files containing tag data [HIGH]
    -   [ ] Importable [HIGH]
    -   [ ] Exportable [HIGH]
    -   [ ] Conflict resolution [HIGH]
    -   [ ] Color Packs [MEDIUM]
        -   [ ] Human-readable (i.e. JSON) files containing tag data [HIGH]
        -   [ ] Importable [HIGH]
        -   [ ] Exportable [HIGH]
-   [ ] Exportable Library Data [HIGH]
    -   [ ] Standard notation format (i.e. JSON) contacting all library data [HIGH]

### 10.0 (Possible Beta/Full Release)

-   [ ] All remaining [HIGH] and optional [MEDIUM] features

### Post 10.0

-   [ ] Core Library/API
-   [ ] Plugin Support
