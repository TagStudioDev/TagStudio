---
icon: material/map-check
---

# :material-map-check: Roadmap

This page outlines the current and planned features required for TagStudio to be considered "feature complete" (v10.0.0). Features and changes are broken up by group in order to better assess the overall state of those features. [Priority levels](#priority-levels) and [version estimates](#version-estimates) are provided in order to give a rough idea of what's planned and when it may release.

This roadmap will update as new features are planned or completed. If there's a feature you'd like to see but is not listed on this page, please check the GitHub [Issues](https://github.com/TagStudioDev/TagStudio/issues) page and submit a feature request if one does not already exist!

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

---

## Core

### :material-database: SQL Library Database

An improved SQLite-based library save file format in which legacy JSON libraries are be migrated to.
Must be finalized or deemed "feature complete" before other core features are developed or finalized.

-   [x] A SQLite-based library save file format **[[v9.5.0](./changelog.md#950-2025-03-03)]**
-   [ ] Cached File Properties Table :material-chevron-triple-up:{ .priority-high title="High Priority" } **[v9.6.0]**
    -   [ ] Date Entry Added to Library :material-chevron-triple-up:{ .priority-high title="High Priority" }
    -   [ ] Date File Created :material-chevron-triple-up:{ .priority-high title="High Priority" }
    -   [ ] Date File Modified :material-chevron-triple-up:{ .priority-high title="High Priority" }
    -   [ ] Date Photo Taken :material-chevron-triple-up:{ .priority-high title="High Priority" }
    -   [ ] Media Duration :material-chevron-triple-up:{ .priority-high title="High Priority" }
    -   [ ] Media Dimensions :material-chevron-double-up:{ .priority-med title="Medium Priority" }
    -   [ ] Word Count :material-chevron-up:{ .priority-low title="Low Priority" }

### :material-database-cog: Core Library + API

A separated, UI agnostic core library that is used to interface with the TagStudio library format. Would host an API for communication from outside the program.

-   [ ] Core Library :material-chevron-triple-up:{ .priority-high title="High Priority" } **[v10.0.0]**
-   [ ] Core Library API :material-chevron-triple-up:{ .priority-high title="High Priority" } **[v10.0.0]**

### :material-clipboard-text: Format Specification

A detailed written specification for the TagStudio tag and/or library format. Intended for used by third-parties to build alternative cores or protocols that can remain interoperable.

-   [ ] Format Specification Established :material-chevron-triple-up:{ .priority-high title="High Priority" } **[v10.0.0]**

---

## Application

### :material-button-cursor: UI/UX

-   [x] Library Grid View
    -   [ ] Explore Filesystem in Grid View :material-chevron-triple-up:{ .priority-high title="High Priority" }
-   [ ] Library List View :material-chevron-triple-up:{ .priority-high title="High Priority" }
    -   [ ] Explore Filesystem in List View :material-chevron-triple-up:{ .priority-high title="High Priority" }
-   [ ] Lightbox View :material-chevron-triple-up:{ .priority-high title="High Priority" }
    -   Similar to List View in concept, but displays one large preview that can cycle back/forth between entries.
    -   [ ] Smaller thumbnails of immediate adjacent entries below :material-chevron-double-up:{ .priority-med title="Medium Priority" }
-   [x] Translations
-   [ ] Search Bar Rework :material-chevron-triple-up:{ .priority-high title="High Priority" } **[v9.7.0]**
    -   [ ] Improved Tag Autocomplete :material-chevron-triple-up:{ .priority-high title="High Priority" }
    -   [ ] Tags appear as widgets in search bar :material-chevron-triple-up:{ .priority-high title="High Priority" }
-   [x] Unified Media Player
    -   [x] Auto-Hiding Player Controls
    -   [x] Play/Pause
    -   [x] Loop
    -   [x] Toggle Autoplay
    -   [x] Volume Control
    -   [x] Toggle Mute
    -   [x] Timeline scrubber
    -   [ ] Fullscreen :material-chevron-double-up:{ .priority-med title="Medium Priority" }
    -   [ ] Fine-Tuned UI/UX :material-chevron-triple-up:{ .priority-high title="High Priority" } **[v9.5.4]**
-   [ ] 3D Model Thumbnails/Previews :material-chevron-triple-up:{ .priority-high title="High Priority" }
    -   [ ] STL File Support
    -   [ ] OBJ File Support
-   [ ] Toggleable Persistent Tagging Panel :material-chevron-triple-up:{ .priority-high title="High Priority" }
    -   [ ] Top Tags
    -   [ ] Recent Tags
    -   [ ] Tag Search
    -   [ ] Pinned Tags
-   [ ] New Tabbed Tag Building UI to Support New Tag Features :material-chevron-triple-up:{ .priority-high title="High Priority" } **[v9.6.0]**
-   [ ] Custom Thumbnail Overrides :material-chevron-double-up:{ .priority-med title="Medium Priority" }
-   [ ] Media Duration Labels :material-chevron-triple-up:{ .priority-high title="High Priority" } **[v9.6.0]**
-   [ ] Word/Line Count Labels :material-chevron-up:{ .priority-low title="Low Priority" }
-   [ ] Custom Tag Badges :material-chevron-up:{ .priority-low title="Low Priority" }
    -   Would serve as an addition/alternative to the Favorite and Archived badges.

### :material-cog: Settings

-   [x] Application Settings
    -   [x] Stored in System User Folder/Designated Folder
    -   [x] Language
    -   [x] Date and Time Format
    -   [x] Theme
-   [x] Configurable Page Size
-   [ ] Library Settings :material-chevron-triple-up:{ .priority-high title="High Priority" }
    -   [ ] Stored in `.TagStudio` folder :material-chevron-triple-up:{ .priority-high title="High Priority" }
-   [ ] Toggle File Extension Label :material-chevron-double-up:{ .priority-med title="Medium Priority" }
-   [ ] Toggle Duration Label :material-chevron-double-up:{ .priority-med title="Medium Priority" }

### :material-puzzle: Plugin Support

Some form of official plugin support for TagStudio, likely with its own API that may connect to or encapsulate part of the the [core library API](#core-library-api).

-   [ ] Plugin Support :material-chevron-triple-up:{ .priority-high title="High Priority" } **[v10.0.0]**

---

## [Library](../library/index.md)

### :material-wrench: Library Mechanics

-   [x] Per-Library Tags
-   [ ] Global Tags :material-chevron-triple-up:{ .priority-high title="High Priority" }
-   [ ] Multiple Root Directories :material-chevron-triple-up:{ .priority-high title="High Priority" } **[v9.6.0]**
-   [ ] Automatic Entry Relinking :material-chevron-triple-up:{ .priority-high title="High Priority" } **[v9.7.0]**
    -   [ ] Detect Renames :material-chevron-triple-up:{ .priority-high title="High Priority" }
    -   [ ] Detect Moves :material-chevron-triple-up:{ .priority-high title="High Priority" }
    -   [ ] Detect Deletions :material-chevron-triple-up:{ .priority-high title="High Priority" }
    -   [ ] Performant :material-chevron-triple-up:{ .priority-high title="High Priority" }
-   [ ] Background File Scanning :material-chevron-triple-up:{ .priority-high title="High Priority" } **[v9.7.0]**
-   [x] Thumbnail Caching **[[v9.5.0](./changelog.md#950-2025-03-03)]**
    -   [ ] Audio Waveform Caching :material-chevron-double-up:{ .priority-med title="Medium Priority" } **[v9.7.0]**

### :material-grid: [Entries](../library/entry.md)

Library representations of files or file-like objects.

-   [x] File Entries **[v1.0.0]**
-   [ ] Folder Entries :material-chevron-triple-up:{ .priority-high title="High Priority" }
-   [ ] URL Entries / Bookmarks :material-chevron-up:{ .priority-low title="Low Priority" }
-   [x] Fields
    -   [x] Text Lines
    -   [x] Text Boxes
    -   [x] Datetimes **[v9.5.4]**
    -   [ ] User-Titled Fields :material-chevron-triple-up:{ .priority-high title="High Priority" } **[v9.6.0]**
    -   [ ] Removal of Deprecated Fields :material-chevron-triple-up:{ .priority-high title="High Priority" } **[v9.6.0]**
-   [ ] Entry Groups :material-chevron-triple-up:{ .priority-high title="High Priority" } **[v9.7.0]**
    -   [ ] Non-exclusive; Entries can be in multiple groups :material-chevron-triple-up:{ .priority-high title="High Priority" }
    -   [ ] Ability to number entries within group :material-chevron-triple-up:{ .priority-high title="High Priority" }
    -   [ ] Ability to set sorting method for group :material-chevron-triple-up:{ .priority-high title="High Priority" }
    -   [ ] Ability to set custom thumbnail for group :material-chevron-triple-up:{ .priority-high title="High Priority" }
    -   [ ] Group is treated as entry with tags and metadata :material-chevron-double-up:{ .priority-med title="Medium Priority" }
    -   [ ] Nested groups :material-chevron-double-up:{ .priority-med title="Medium Priority" }

### :material-tag-text: [Tags](../library/tag.md)

Discrete library objects representing [attributes](<https://en.wikipedia.org/wiki/Property_(philosophy)>). Can be applied to library [entries](../library/entry.md), or applied to other tags to build traversable relationships.

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
    -   [ ] Built-in "Archived" tag has this property by default :material-chevron-triple-up:{ .priority-high title="High Priority" } **[v9.6.0]**
    -   [ ] Checkbox near search bar to show hidden tags in search :material-chevron-triple-up:{ .priority-high title="High Priority" } **[v9.6.0]**
-   [ ] Tag Relationships
    -   [x] [Parent Tags](../library/tag.md#parent-tags) ([Inheritance](<https://en.wikipedia.org/wiki/Inheritance_(object-oriented_programming)>) Relationship) **[v9.0.0]**
    -   [ ] [Component Tags](../library/tag.md#component-tags) ([Composition](https://en.wikipedia.org/wiki/Object_composition) Relationship) :material-chevron-triple-up:{ .priority-high title="High Priority" } **[v9.6.0]**
-   [ ] Multiple Language Support :material-chevron-up:{ .priority-low title="Low Priority" } **[v9.9.0]**
-   [ ] Tag Overrides :material-chevron-double-up:{ .priority-med title="Medium Priority" }
-   [ ] Tag Merging :material-chevron-double-up:{ .priority-med title="Medium Priority" }

### :material-magnify: [Search](../library/library_search.md)

-   [x] Tag Search **[v8.0.0]**
-   [x] Filename Search **[[v9.5.0](./changelog.md#950-2025-03-03)]**
    -   [x] Glob Search **[[v9.5.0](./changelog.md#950-2025-03-03)]**
-   [x] Filetype Search **[[v9.5.0](./changelog.md#950-2025-03-03)]**
    -   [x] Search by Extension (e.g. ".jpg", ".png") **[[v9.5.0](./changelog.md#950-2025-03-03)]**
        -   [x] Optional consolidation of extension synonyms (i.e. ".jpg" can equal ".jpeg") **[[v9.5.0](./changelog.md#950-2025-03-03)]**
    -   [x] Search by media type (e.g. "image", "video", "document") **[[v9.5.0](./changelog.md#950-2025-03-03)]**
-   [ ] Field Content Search :material-chevron-triple-up:{ .priority-high title="High Priority" } **[v9.6.0]**
-   [x] [Boolean Operators](../library/library_search.md) **[[v9.5.0](./changelog.md#950-2025-03-03)]**
    -   [x] `AND` Operator
    -   [x] `OR` Operator
    -   [x] `NOT` Operator
    -   [x] Parenthesis Grouping
    -   [x] Character Escaping
-   [ ] `HAS` Operator (for [Component Tags](../library/tag.md#component-tags)) :material-chevron-triple-up:{ .priority-high title="High Priority" } **[v9.6.0]**
-   [ ] Conditional Search :material-chevron-double-up:{ .priority-med title="Medium Priority" } **[v9.7.0]**
    -   [ ] Compare Dates :material-chevron-double-up:{ .priority-med title="Medium Priority" }
    -   [ ] Compare Durations :material-chevron-double-up:{ .priority-med title="Medium Priority" }
    -   [ ] Compare File Sizes :material-chevron-double-up:{ .priority-med title="Medium Priority" }
    -   [ ] Compare Dimensions :material-chevron-double-up:{ .priority-med title="Medium Priority" }
-   [x] Smartcase Search [[v9.5.0](./changelog.md#950-2025-03-03)]
-   [ ] Search Result Sorting
    -   [x] Sort by Filename **[[v9.5.2](./changelog.md#952-2025-03-31)]**
    -   [x] Sort by Date Entry Added to Library **[[v9.5.2](./changelog.md#952-2025-03-31)]**
    -   [ ] Sort by File Creation Date :material-chevron-triple-up:{ .priority-high title="High Priority" } **[v9.6.0]**
    -   [ ] Sort by File Modification Date :material-chevron-triple-up:{ .priority-high title="High Priority" } **[v9.6.0]**
    -   [ ] Sort by File Modification Date :material-chevron-triple-up:{ .priority-high title="High Priority" }
    -   [ ] Sort by Date Taken (Photos) :material-chevron-triple-up:{ .priority-high title="High Priority" } **[v9.6.0]**
-   [ ] OCR Search :material-chevron-up:{ .priority-low title="Low Priority" }
-   [ ] Fuzzy Search :material-chevron-up:{ .priority-low title="Low Priority" }

### :material-file-cog: [Macros](../utilities/macro.md)

-   [ ] Standard, Human Readable Format (TOML) :material-chevron-triple-up:{ .priority-high title="High Priority" } **[v9.5.4]**
-   [ ] Versioning System :material-chevron-triple-up:{ .priority-high title="High Priority" } **[v9.5.4]**
-   [ ] Triggers **[v9.5.4]**
    -   [ ] On File Added :material-chevron-triple-up:{ .priority-high title="High Priority" }
    -   [ ] On Library Refresh :material-chevron-triple-up:{ .priority-high title="High Priority" }
    -   [ ] [...]
-   [ ] Actions **[v9.5.4]**
    -   [ ] Add Tag(s) :material-chevron-triple-up:{ .priority-high title="High Priority" }
    -   [ ] Add Field(s) :material-chevron-triple-up:{ .priority-high title="High Priority" }
    -   [ ] Set Field Content :material-chevron-triple-up:{ .priority-high title="High Priority" }
    -   [ ] [...]

### :material-table-arrow-right: Sharable Data

Sharable TagStudio library data in the form of data packs (tags, colors, etc.) or other formats.
Packs are intended as an easy way to import and export specific data between libraries and users, while export-only formats are intended to be imported by other programs.

-   [ ] Color Packs :material-chevron-triple-up:{ .priority-high title="High Priority" } **[v9.6.0]**
    -   [ ] Importable
    -   [ ] Exportable
    -   [x] UUIDs + Namespaces :material-chevron-triple-up:{ .priority-high title="High Priority" }
    -   [x] Standard, Human Readable Format (TOML) :material-chevron-triple-up:{ .priority-high title="High Priority" }
    -   [ ] Versioning System :material-chevron-double-up:{ .priority-med title="Medium Priority" }
-   [ ] Tag Packs :material-chevron-triple-up:{ .priority-high title="High Priority" } **[v9.9.0]**
    -   [ ] Importable :material-chevron-triple-up:{ .priority-high title="High Priority" }
    -   [ ] Exportable :material-chevron-triple-up:{ .priority-high title="High Priority" }
    -   [ ] UUIDs + Namespaces :material-chevron-triple-up:{ .priority-high title="High Priority" }
    -   [ ] Standard, Human Readable Format (TOML) :material-chevron-triple-up:{ .priority-high title="High Priority" }
    -   [ ] Versioning System :material-chevron-double-up:{ .priority-med title="Medium Priority" }
-   [ ] Macro Sharing :material-chevron-triple-up:{ .priority-high title="High Priority" } **[v9.6.0]**
    -   [ ] Importable :material-chevron-triple-up:{ .priority-high title="High Priority" }
    -   [ ] Exportable :material-chevron-triple-up:{ .priority-high title="High Priority" }
-   [ ] Sharable Entry Data :material-chevron-double-up:{ .priority-med title="Medium Priority" } **[v9.9.0]**
    -   _Specifics of this are yet to be determined_
-   [ ] Export Library to Human Readable Format :material-chevron-triple-up:{ .priority-high title="High Priority" } **[v10.0.0]**
    -   Intended to give users more flexible options with their data if they wish to migrate away from TagStudio
