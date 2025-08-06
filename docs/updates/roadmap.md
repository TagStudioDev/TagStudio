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

Features are given rough estimations for which version they will be completed in, and are listed next to their names (e.g. Feature **[v9.0.0]**). They are eventually replaced with links to the version changelog in which they were completed in, if applicable.

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

### [Library](../library/index.md)

<div class="grid cards" markdown>
- #### :material-tag-text: [Tags](../library/tag.md)
Discrete library objects representing [attributes](https://en.wikipedia.org/wiki/Property_(philosophy)). Can be applied to library [entries](../library/entry.md), or applied to other tags to build traversable relationships.

    ---
    -   [x] Create and Edit Tags **[v8.0.0]**
    -   [x] Delete Tags **[[v9.5.0](./changelog.md#950-2025-03-03)]**
    -   [x] Tag Name **[v8.0.0]**
    -   [x] Tag Shorthand Name **[v8.0.0]**
    -   [x] Tag Aliases List **[v8.0.0]**
    -   [x] Tag Color **[v8.0.0]**
    -   [ ] Tag Description :material-chevron-double-up:{ .priority-med title="Medium Priority" } **[v9.6.0]**
    -   [x] Tag Colors
        -   [x] Built-in Color Palette **[v8.0.0]**
        -   [x] User-Defined Colors **[[v9.5.0](./changelog.md#950-2025-03-03)]**
        -   [x] Primary and Secondary Colors **[[v9.5.0](./changelog.md#950-2025-03-03)]**
    -   [ ] Tag Icons :material-chevron-triple-up:{ .priority-high title="High Priority" } **[v9.6.0]**
        -   [ ] Small Icons :material-chevron-triple-up:{ .priority-high title="High Priority" } **[v9.6.0]**
        -   [ ] Large Icons for Profiles :material-chevron-double-up:{ .priority-med title="Medium Priority" } **[v9.6.0]**
        -   [ ] Built-in Icon Packs (i.e. Boxicons) :material-chevron-triple-up:{ .priority-high title="High Priority" } **[v9.6.0]**
        -   [ ] User-Defined Icons :material-chevron-triple-up:{ .priority-high title="High Priority" } **[v9.6.0]**
    -   [x] [Category Property](../library/tag_categories.md) **[[v9.5.0](./changelog.md#950-2025-03-03)]**
        -   [x] Property available for tags that allow the tag and any inheriting from it to be displayed separately in the preview panel under a title
        -   [ ] Fine-tuned exclusion from categories :material-chevron-triple-up:{ .priority-high title="High Priority" } **[v9.6.0]**
    -   [ ] Hidden Property :material-chevron-triple-up:{ .priority-high title="High Priority" } **[v9.6.0]**
        - [ ] Built-in "Archived" tag has this property by default :material-chevron-triple-up:{ .priority-high title="High Priority" } **[v9.6.0]**
        - [ ] Checkbox near search bar to show hidden tags in search :material-chevron-triple-up:{ .priority-high title="High Priority" } **[v9.6.0]**
    -   [ ] Tag Relationships
        -   [x] [Parent Tags](../library/tag.md#parent-tags) ([Inheritance](<https://en.wikipedia.org/wiki/Inheritance_(object-oriented_programming)>) Relationship) **[v9.0.0]**
        -   [ ] [Component Tags](../library/tag.md#component-tags) ([Composition](https://en.wikipedia.org/wiki/Object_composition) Relationship) :material-chevron-triple-up:{ .priority-high title="High Priority" } **[v9.6.0]**
    -   [ ] Multiple Language Support :material-chevron-up:{ .priority-low title="Low Priority" } **[v9.9.0]**
    -   [ ] [Tag Overrides](../library/tag_overrides.md) :material-chevron-double-up:{ .priority-med title="Medium Priority" }
    -   [ ] Tag Merging :material-chevron-double-up:{ .priority-med title="Medium Priority" }

</div>

<div class="grid cards" markdown>
- #### :material-tag-multiple: Sharable Data
Sharable TagStudio library data in the form of data packs (tags, colors, etc.) or other formats.
Packs are intended as an easy way to import and export specific data between libraries and users, while export-only formats are intended to be imported by other programs.

    ---
    -   [ ] Color Packs **[v9.6.0]**
        -   [ ] Importable :material-chevron-triple-up:{ .priority-high title="High Priority" }
        -   [ ] Exportable :material-chevron-triple-up:{ .priority-high title="High Priority" }
        -   [x] UUIDs + Namespaces :material-chevron-triple-up:{ .priority-high title="High Priority" }
        -   [x] Standard, human readable format (TOML) :material-chevron-triple-up:{ .priority-high title="High Priority" }
        -   [ ] Versioning System :material-chevron-double-up:{ .priority-med title="Medium Priority" }
    -   [ ] Tag Packs **[v9.9.0]**
        -   [ ] Importable :material-chevron-triple-up:{ .priority-high title="High Priority" }
        -   [ ] Exportable :material-chevron-triple-up:{ .priority-high title="High Priority" }
        -   [ ] UUIDs + Namespaces :material-chevron-triple-up:{ .priority-high title="High Priority" }
        -   [ ] Standard, human readable format (TOML) :material-chevron-triple-up:{ .priority-high title="High Priority" }
        -   [ ] Versioning System :material-chevron-double-up:{ .priority-med title="Medium Priority" }
    -   [ ] Export Library to Human Readable Format :material-chevron-triple-up:{ .priority-high title="High Priority" } **[v10.0.0]**
        -   Intended to give users more flexible options with their data if they wish to migrate away from TagStudio

</div>

#### Library

-   [ ] Multiple Root Directories per Library [HIGH]

### v9.5

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
