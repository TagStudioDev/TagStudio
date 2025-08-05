# Roadmap

This page outlines the current and planned features required for TagStudio to be considered "feature complete" (v10.0.0). Features and changes are broken up by group in order to better assess the overall state of those features. [Priority levels](#priority-levels) and [version estimates](#version-estimates) are provided in order to give a rough idea of what's planned and when it may release.

This page will update as new features are planned or completed. If there's a feature you'd like to see but is not listed on this page, please check the GitHub [Issues](https://github.com/TagStudioDev/TagStudio/issues) page and submit a feature request if one does not already exist!

## Priority Levels

Planned features and changes are assigned **priority levels** to signify how important they are to the feature-complete version of TagStudio and to serve as a general guide for what should be worked on first, along with [version estimates](#version-estimates). When features are completed, their priority level icons are removed.

<!-- prettier-ignore -->
!!! info "Priority Level Icons"
    -   :material-chevron-triple-up:{ .priority-high title="High Priority" } **High Priority** - Core features
    -   :material-chevron-double-up:{ .priority-med title="Medium Priority" } **Medium Priority** - Important, but not necessary
    -   :material-chevron-up:{ .priority-low title="Low Priority" } **Low Priority** - Just nice to have

## Version Estimates

Features are given rough estimations for which version they will be completed in, and are listed next to their names (e.g. Feature **[v9.0.0]**). They are eventually replaced with links to the version changelog in which they were completed in.

<!-- prettier-ignore -->
!!! tip
    For a more definitive and up-to-date list of features planned for near-future updates, please reference the current GitHub [Milestones](https://github.com/TagStudioDev/TagStudio/milestones)!

## Features

### Core

<div class="grid cards" markdown>
- #### :material-database: SQL Library Format
An improved library save file format in which legacy JSON libraries will be migrated to.
Must be finalized or deemed "feature complete" before other core features are developed or finalized.

    ---
    - [x] A SQLite-based library save file format **[[v9.5.0](./changelog.md#950-2025-03-03)]**
    - [ ] Cached File Properties Table :material-chevron-triple-up:{ .priority-high title="High Priority" } **[v9.6.0]**
        - [ ] File Date Created :material-chevron-triple-up:{ .priority-high title="High Priority" }
        - [ ] File Date Modified :material-chevron-triple-up:{ .priority-high title="High Priority" }
        - [ ] Entry Added to Library :material-chevron-triple-up:{ .priority-high title="High Priority" }
        - [ ] Media Duration :material-chevron-triple-up:{ .priority-high title="High Priority" }
        - [ ] Image Resolution :material-chevron-double-up:{ .priority-med title="Medium Priority" }
        - [ ] Word Count :material-chevron-up:{ .priority-low  title="Low Priority" }

</div>

<div class="grid cards" markdown>
- #### :material-database-cog: Core Library + API
A separated, UI agnostic core library that's used to interface with the TagStudio library format. Would host an API for communication from outside the program.

    ---
    - [ ] Core Library :material-chevron-triple-up:{ .priority-high title="High Priority" } **[v10.0.0]**
    - [ ] Core Library API :material-chevron-triple-up:{ .priority-high title="High Priority" } **[v10.0.0]**

</div>

<div class="grid cards" markdown>
- #### :material-puzzle: Plugin Support
Some form of official plugin support for TagStudio, likely with its own API that may or may not connect to or share attributes with the core library API.

    ---
    - [ ] Plugin Support :material-chevron-triple-up:{ .priority-high title="High Priority" } **[v10.0.0]**

</div>

<div class="grid cards" markdown>
- #### :material-clipboard-text: TagStudio Format Specification
    A detailed written specification for the TagStudio tag and/or library format. Intended for use by third-parties to build alternative cores or protocols that can interoperate between one another.

    ---
    - [ ] "TAGSPEC" Specification Established :material-chevron-triple-up:{ .priority-high title="High Priority" } **[v10.0.0]**

</div>

### v9.5

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

#### Library

-   [ ] Multiple Root Directories per Library [HIGH]

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
