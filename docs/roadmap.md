---
title: Roadmap
icon: material/map-check
---

<!-- SPDX-FileCopyrightText: (c) TagStudio Contributors -->
<!-- SPDX-License-Identifier: GPL-3.0-only -->

# :material-map-check: Roadmap

This page outlines the current and planned features required for TagStudio to be considered "feature complete" (v10.0.0). Features and changes are broken up by group in order to better assess the overall state of those features. [Priority levels](#priority-levels) and [version estimates](#version-estimates) are provided in order to give a rough idea of what's planned and when it may release.

This roadmap will update as new features are planned or completed. If there's a feature you'd like to see but is not listed on this page, please check the GitHub [Issues](https://github.com/TagStudioDev/TagStudio/issues) page and submit a feature request if one does not already exist!

## :material-chevron-triple-up: Priority Levels

Planned features and changes are assigned **priority levels** to signify how important they are to the feature-complete version of TagStudio and to serve as a general guide for what should be worked on first, along with [version estimates](#version-estimates). When features are completed, their priority level icons are removed.

<!-- prettier-ignore -->
!!! info "Priority Level Icons"
    - :material-chevron-triple-up:{ .priority-high title="High Priority" } **High Priority** - Core features
    - :material-chevron-double-up:{ .priority-med title="Medium Priority" } **Medium Priority** - Important, but not necessary
    - :material-chevron-up:{ .priority-low title="Low Priority" } **Low Priority** - Just nice to have

## :material-map-clock: Version Estimates

Features are given rough estimations for which version they will be completed in listed next to their names (e.g. Feature **[v9.0.0]**). When the feature is completed they're linked to their respective changelog release, if applicable.

| Version Cycle        | Goals                                                                                                                     |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| ~~**Alpha v9.5.x**~~ | ~~Migrate from JSON to SQLite database format~~                                                                           |
| **Alpha v9.6.x**     | Necessary database changes for upcoming features ([fields](#entries), [file metadata](#sql-based-library-database), etc.) |
| **Alpha v9.7.x**     | Implement currently solidified features ([entry groups](#entries), etc.)                                                  |
| **Beta v9.8.x**      | Solidify remaining features and implementations ([component tags](#tags), etc.)                                           |
| **Beta v9.9.x**      | Make any additions and fixes from earlier release cycles                                                                  |
| **v10.0.x**          | Feature complete, versioning switches to [semver](https://semver.org/)                                                    |

<!-- prettier-ignore -->
!!! tip
    For a more definitive and up-to-date list of features planned for near-future updates, please reference the current GitHub [Milestones](https://github.com/TagStudioDev/TagStudio/milestones)!

## :material-engine: Core

### :material-database: SQL-Based Library Database

A SQLite database file used as the [library](./libraries.md) save file format. Legacy JSON libraries are migrated to this improved format.

<!-- prettier-ignore -->
!!! note
    See the "[Library](#library)" section for features related to the library database rather than the underlying schema.

- [x] A SQLite-based library save file format **[[v9.5.0](changelog.md#950-march-3rd-2025)]**
- [ ] Cached File Properties Table :material-chevron-triple-up:{ .priority-high title="High Priority" } **[v9.6.1]**
    - [x] Date Entry Added to Library
    - [ ] Date File Created :material-chevron-triple-up:{ .priority-high title="High Priority" }
    - [ ] Date File Modified :material-chevron-triple-up:{ .priority-high title="High Priority" }
    - [ ] Date Photo Taken :material-chevron-double-up:{ .priority-med title="Medium Priority" }
    - [ ] Media Duration :material-chevron-double-up:{ .priority-med title="Medium Priority" }
    - [ ] Media Dimensions :material-chevron-up:{ .priority-low title="Low Priority" }
    - [ ] Word Count :material-chevron-up:{ .priority-low title="Low Priority" }

### :material-database-cog: Core Library + CLI

A separated, UI agnostic core library that would be used to interface with the TagStudio library format. Would come with a CLI to allow for interfacing with scripts and external programs, and to make bulk operations easier. This would be licensed under the more permissive [MIT](https://en.wikipedia.org/wiki/MIT_License) license to foster wider adoption compared to the TagStudio GUI application source code.

- [ ] Core Library :material-chevron-double-up:{ .priority-med title="Medium Priority" } **[v9.9.0]**
- [ ] CLI :material-chevron-triple-up:{ .priority-high title="High Priority" } **[v9.9.0]**
- [ ] MIT License :material-chevron-triple-up:{ .priority-high title="High Priority" } **[v9.9.0]**

### :material-clipboard-text: Format Specification

A detailed written specification for the TagStudio tag and/or library format. Intended for used by third-parties to build alternative cores or protocols that can remain interoperable.

- [ ] Format Specification Established :material-chevron-double-up:{ .priority-med title="Medium Priority" } **[v10.0.0]**

---

## :material-application-outline: Application

### :material-button-cursor: UI/UX

- [x] Library Grid View
    - [ ] Explore Filesystem in Grid View :material-chevron-double-up:{ .priority-med title="Medium Priority" }
    - [x] Infinite Scrolling **[[v9.5.6](changelog.md#956-october-20th-2025)]**
- [ ] Library List View :material-chevron-double-up:{ .priority-med title="Medium Priority" }
    - [ ] Explore Filesystem in List View :material-chevron-double-up:{ .priority-med title="Medium Priority" }
- [ ] Lightbox View :material-chevron-double-up:{ .priority-med title="Medium Priority" }
    - Similar to List View in concept, but displays one large preview that can cycle back/forth between entries.
    - [ ] Smaller thumbnails of immediate adjacent entries below :material-chevron-double-up:{ .priority-med title="Medium Priority" }
- [x] Library Statistics Screen **[[v9.5.4](changelog.md#954-september-1st-2025)]**
- [x] Unified Library Health/Cleanup Screen **[[v9.5.4](changelog.md#954-september-1st-2025)]**
    - [x] Fix Unlinked Entries
    - [ ] Fix Duplicate Files <small>(Regression)</small> **[v9.6.x]**
    - [x] ~~Fix Duplicate Entries~~
    - [x] Remove Ignored Entries **[[v9.5.4](changelog.md#954-september-1st-2025)]**
    - [x] Delete Old Backups **[[v9.5.4](changelog.md#954-september-1st-2025)]**
    - [x] Delete Legacy JSON File **[[v9.5.4](changelog.md#954-september-1st-2025)]**
- [x] Translations
- [ ] Search Bar Rework :material-chevron-triple-up:{ .priority-high title="High Priority" } **[v9.6.x]**
    - [ ] Improved Tag Autocomplete :material-chevron-triple-up:{ .priority-high title="High Priority" }
    - [ ] Tags appear as widgets in search bar :material-chevron-triple-up:{ .priority-high title="High Priority" }
- [x] Unified Media Player
    - [x] Auto-Hiding Player Controls
    - [x] Play/Pause
    - [x] Loop
    - [x] Toggle Autoplay
    - [x] Volume Control
    - [x] Toggle Mute
    - [x] Timeline Scrubber
    - [ ] Fullscreen Mode :material-chevron-double-up:{ .priority-med title="Medium Priority" }
    - [ ] Fine-Tuned UI/UX :material-chevron-triple-up:{ .priority-high title="High Priority" }
- [ ] 3D Model Thumbnails/Previews :material-chevron-triple-up:{ .priority-high title="High Priority" } _(See Discussion #1231)_
    - [ ] STL File Support
    - [ ] OBJ File Support
- [ ] Plaintext Thumbnails/Previews
    - [x] Basic Support
    - [ ] Full File Preview :material-chevron-triple-up:{ .priority-high title="High Priority" } **[v9.6.x]**
    - [ ] Syntax Highlighting :material-chevron-double-up:{ .priority-med title="Medium Priority" } **[v9.6.x]**
- [ ] Toggleable Persistent Tagging Panel :material-chevron-triple-up:{ .priority-high title="High Priority" } **[v9.8.x]**
    - [ ] Top Tags
    - [ ] Recent Tags
    - [ ] Tag Search
    - [ ] Pinned Tags
- [ ] New Tabbed Tag Building UI to Support New Tag Features :material-chevron-triple-up:{ .priority-high title="High Priority" } **[v9.8.x]**
- [ ] Custom Thumbnail Overrides :material-chevron-double-up:{ .priority-med title="Medium Priority" } **[v9.7.x]**
- [ ] Media Duration Labels :material-chevron-triple-up:{ .priority-high title="High Priority" } **[v9.6.x]**
- [ ] Word/Line Count Labels :material-chevron-up:{ .priority-low title="Low Priority" }
- [ ] Custom Tag Badges :material-chevron-up:{ .priority-low title="Low Priority" }
    - Would serve as an addition/alternative to the Favorite and Archived badges.

### :material-cog: Settings

- [x] Application Settings
    - [x] Stored in System User Folder/Designated Folder
    - [x] Language
    - [x] Date and Time Format
    - [x] Theme
    - [x] Thumbnail Generation **[[v9.5.4](changelog.md#954-september-1st-2025)]**
- [x] Configurable Page Size
- [ ] Library Settings :material-chevron-triple-up:{ .priority-high title="High Priority" } **[v9.6.x]**
    - [ ] Stored in `.TagStudio` folder :material-chevron-triple-up:{ .priority-high title="High Priority" }
- [ ] Toggle File Extension Label :material-chevron-double-up:{ .priority-med title="Medium Priority" }
- [ ] Toggle Duration Label :material-chevron-double-up:{ .priority-med title="Medium Priority" }

---

## :material-database: Library

### :material-wrench: Library Mechanics

- [x] Per-Library Tags
- [ ] Global Tags :material-chevron-double-up:{ .priority-med title="Medium Priority" } **[v9.8.x]**
- [ ] Multiple Root Directories :material-chevron-triple-up:{ .priority-high title="High Priority" } **[v9.6.x]**
    - [ ] Ability to store TagStudio data folder separate from library content folder(s) :material-chevron-triple-up:{ .priority-high title="High Priority" } **[v9.6.x]**
- [ ] Automatic Entry Relinking :material-chevron-triple-up:{ .priority-high title="High Priority" } **[v9.8.x]**
    - [ ] Detect Renames :material-chevron-triple-up:{ .priority-high title="High Priority" }
    - [ ] Detect Moves :material-chevron-triple-up:{ .priority-high title="High Priority" }
    - [ ] Detect Deletions :material-chevron-triple-up:{ .priority-high title="High Priority" }
    - [ ] Performant :material-chevron-triple-up:{ .priority-high title="High Priority" }
- [ ] Background File Scanning :material-chevron-triple-up:{ .priority-high title="High Priority" }
- [x] Thumbnail Caching **[[v9.5.0](changelog.md#950-march-3rd-2025)]**
    - [ ] Audio Waveform Caching :material-chevron-double-up:{ .priority-med title="Medium Priority" } **[v9.7.x]**
    - [ ] Large Image Caching :material-chevron-double-up:{ .priority-med title="Medium Priority" } **[v9.7.x]**

### :material-grid: Entries

File or file-like [entries](entries.md) stored in the library.

- [x] File Entries **[v1.0.0]**
- [ ] URL Entries / Bookmarks :material-chevron-up:{ .priority-low title="Low Priority" } **[v9.6.x]**
- [x] Fields
    - [x] Text Lines
    - [x] Text Boxes
    - [x] Datetimes **[[v9.5.4](changelog.md#954-september-1st-2025)]**
    - [ ] Numeric Fields :material-chevron-double-up:{ .priority-med title="Medium Priority" } **[v9.6.x]**
        - [ ] Optional Units (e.g. inches, cm, height notation, degrees, bytes, etc.) :material-chevron-double-up:{ .priority-med title="Medium Priority" }
    - [ ] Custom Field Names :material-chevron-triple-up:{ .priority-high title="High Priority" } **[v9.6.x]**
        - [x] Removal of Deprecated Fields **[v9.6.0]**
- [ ] Entry Groups :material-chevron-triple-up:{ .priority-high title="High Priority" } **[v9.7.x]**
    - [ ] Non-exclusive; Entries can be in multiple groups :material-chevron-triple-up:{ .priority-high title="High Priority" }
    - [ ] Ability to number entries within group :material-chevron-triple-up:{ .priority-high title="High Priority" }
    - [ ] Ability to set sorting method for group :material-chevron-triple-up:{ .priority-high title="High Priority" }
    - [ ] Ability to set custom thumbnail for group :material-chevron-triple-up:{ .priority-high title="High Priority" }
    - [ ] Group is treated as entry with tags and metadata :material-chevron-double-up:{ .priority-med title="Medium Priority" }
    - [ ] Nested groups :material-chevron-double-up:{ .priority-med title="Medium Priority" }

### :material-tag-text: Tags

Discrete library objects representing [attributes](<https://en.wikipedia.org/wiki/Property_(philosophy)>). Can be applied to library [entries](entries.md), or applied to other tags to build traversable relationships.

- [x] Tag Name **[v8.0.0]**
- [x] Tag Shorthand Name **[v8.0.0]**
- [x] Tag Aliases List **[v8.0.0]**
- [x] Tag Color **[v8.0.0]**
- [ ] Tag Description :material-chevron-double-up:{ .priority-med title="Medium Priority" } **[v9.7.x]**
- [x] Tag Colors
    - [x] Built-in Color Palette **[v8.0.0]**
    - [x] User-Defined Colors **[[v9.5.0](changelog.md#950-march-3rd-2025)]**
    - [x] Primary and Secondary Colors **[[v9.5.0](changelog.md#950-march-3rd-2025)]**
- [ ] Tag Icons :material-chevron-triple-up:{ .priority-high title="High Priority" } **[v9.7.x]**
    - [ ] Small Icons :material-chevron-triple-up:{ .priority-high title="High Priority" } **[v9.7.x]**
    - [ ] Large Icons for Profiles :material-chevron-double-up:{ .priority-med title="Medium Priority" } **[v9.7.x]**
    - [ ] Built-in Icon Packs (e.g. Boxicons) :material-chevron-triple-up:{ .priority-high title="High Priority" } **[v9.7.x]**
    - [ ] User-Defined Icons :material-chevron-triple-up:{ .priority-high title="High Priority" } **[v9.7.x]**
    - [ ] Tint Icons with Text Color :material-chevron-triple-up:{ .priority-high title="High Priority" } **[v9.7.x]**
- [x] [Category Property](tags.md#is-category) **[[v9.5.0](changelog.md#950-march-3rd-2025)]**
    - [x] Property available for tags that allow the tag and any inheriting from it to be displayed separately in the preview panel under a title
    - [ ] Fine-tuned exclusion from categories :material-chevron-triple-up:{ .priority-high title="High Priority" } **[v9.6.x]**
- [x] Hidden Property **[[v9.5.7](changelog.md#957-may-5th-2026)]**
    - [x] Built-in "Archived" tag has this property by default **[[v9.5.7](changelog.md#957-may-5th-2026)]**
    - [x] Checkbox near search bar to show hidden tags in search **[[v9.5.7](changelog.md#957-may-5th-2026)]**
- [ ] Tag Relationships
    - [x] [Parent Tags](tags.md#parent-tags) ([Inheritance](<https://en.wikipedia.org/wiki/Inheritance_(object-oriented_programming)>) Relationship) **[v9.0.0]**
    - [ ] [Component Tags](tags.md#component-tags) ([Composition](https://en.wikipedia.org/wiki/Object_composition) Relationship) :material-chevron-triple-up:{ .priority-high title="High Priority" } **[v9.8.x]**
- [ ] Multiple Language Support :material-chevron-up:{ .priority-low title="Low Priority" } **[v9.9.x]**
- [ ] Tag Overrides :material-chevron-double-up:{ .priority-med title="Medium Priority" } **[v9.8.x]**
- [ ] Tag Merging :material-chevron-double-up:{ .priority-med title="Medium Priority" } **[v9.9.x]**

### :material-magnify: Search

- [x] Tag Search **[v8.0.0]**
- [x] Filename Search **[[v9.5.0](changelog.md#950-march-3rd-2025)]**
    - [x] Glob Search **[[v9.5.0](changelog.md#950-march-3rd-2025)]**
- [x] Filetype Search **[[v9.5.0](changelog.md#950-march-3rd-2025)]**
    - [x] Search by Extension (e.g. ".jpg", ".png") **[[v9.5.0](changelog.md#950-march-3rd-2025)]**
        - [x] Optional consolidation of extension synonyms (e.g. ".jpg" can equal ".jpeg") **[[v9.5.0](changelog.md#950-march-3rd-2025)]**
    - [x] Search by media type (e.g. "image", "video", "document") **[[v9.5.0](changelog.md#950-march-3rd-2025)]**
- [ ] Field Content Search :material-chevron-triple-up:{ .priority-high title="High Priority" }
- [x] [Boolean Operators](search.md) **[[v9.5.0](changelog.md#950-march-3rd-2025)]**
    - [x] `AND` Operator
    - [x] `OR` Operator
    - [x] `NOT` Operator
    - [x] Parenthesis Grouping
    - [x] Character Escaping
- [ ] `HAS` Operator (for [Component Tags](tags.md#component-tags)) :material-chevron-triple-up:{ .priority-high title="High Priority" } **[v9.8.x]**
- [ ] Conditional Search :material-chevron-double-up:{ .priority-med title="Medium Priority" } **[v9.7.x]**
    - [ ] Compare Dates :material-chevron-double-up:{ .priority-med title="Medium Priority" }
    - [ ] Compare Durations :material-chevron-double-up:{ .priority-med title="Medium Priority" }
    - [ ] Compare File Sizes :material-chevron-double-up:{ .priority-med title="Medium Priority" }
    - [ ] Compare Dimensions :material-chevron-double-up:{ .priority-med title="Medium Priority" }
- [x] Smartcase Search **[[v9.5.0](changelog.md#950-march-3rd-2025)]**
- [ ] Search Result Sorting
    - [x] Sort by Filename **[[v9.5.2](changelog.md#952-march-31st-2025)]**
    - [x] Sort by Date Entry Added to Library **[[v9.5.2](changelog.md#952-march-31st-2025)]**
    - [ ] Sort by File Creation Date :material-chevron-triple-up:{ .priority-high title="High Priority" } **[v9.6.x]**
    - [ ] Sort by File Modification Date :material-chevron-triple-up:{ .priority-high title="High Priority" } **[v9.6.x]**
    - [ ] Sort by Date Taken (Photos) :material-chevron-double-up:{ .priority-med title="Medium Priority" } **[v9.6.x]**
    - [x] Random/Shuffle Sort
- [ ] OCR Search :material-chevron-up:{ .priority-low title="Low Priority" }
- [ ] Fuzzy Search :material-chevron-up:{ .priority-low title="Low Priority" }

### :material-file-cog: Macros

- [ ] Standard, Human Readable Format (TOML) :material-chevron-triple-up:{ .priority-high title="High Priority" } **[v9.7.x]**
- [ ] Versioning System :material-chevron-triple-up:{ .priority-high title="High Priority" } **[v9.7.x]**
- [ ] Triggers **[v9.7.x]**
    - [ ] On File Added :material-chevron-triple-up:{ .priority-high title="High Priority" }
    - [ ] On Library Refresh :material-chevron-triple-up:{ .priority-high title="High Priority" }
    - [ ] [...]
- [ ] Actions **[v9.7.x]**
    - [ ] Add Tag(s) :material-chevron-triple-up:{ .priority-high title="High Priority" }
    - [ ] Add Field(s) :material-chevron-triple-up:{ .priority-high title="High Priority" }
    - [ ] Set Field Content :material-chevron-triple-up:{ .priority-high title="High Priority" }
    - [ ] [...]

### :material-table-arrow-right: Sharable Data

Sharable TagStudio library data in the form of data packs (tags, colors, etc.) or other formats.
Packs are intended as an easy way to import and export specific data between libraries and users, while export-only formats are intended to be imported by other programs.

- [ ] Color Packs :material-chevron-triple-up:{ .priority-high title="High Priority" } **[v9.6.x]**
    - [ ] Importable
    - [ ] Exportable
    - [x] UUIDs + Namespaces :material-chevron-triple-up:{ .priority-high title="High Priority" }
    - [x] Standard, Human Readable Format (TOML) :material-chevron-triple-up:{ .priority-high title="High Priority" }
    - [ ] Versioning System :material-chevron-double-up:{ .priority-med title="Medium Priority" }
- [ ] Tag Packs :material-chevron-triple-up:{ .priority-high title="High Priority" } **[v9.8.x]**
    - [ ] Importable :material-chevron-triple-up:{ .priority-high title="High Priority" }
    - [ ] Exportable :material-chevron-triple-up:{ .priority-high title="High Priority" }
    - [ ] UUIDs + Namespaces :material-chevron-triple-up:{ .priority-high title="High Priority" }
    - [ ] Standard, Human Readable Format (TOML) :material-chevron-triple-up:{ .priority-high title="High Priority" }
    - [ ] Versioning System :material-chevron-double-up:{ .priority-med title="Medium Priority" }
- [ ] Macro Sharing :material-chevron-triple-up:{ .priority-high title="High Priority" } **[v9.7.x]**
    - [ ] Importable :material-chevron-triple-up:{ .priority-high title="High Priority" }
    - [ ] Exportable :material-chevron-triple-up:{ .priority-high title="High Priority" }
- [ ] Sharable Entry Data :material-chevron-up:{ .priority-low title="Low Priority" }
    - _Specifics of this are yet to be determined_
- [ ] Export Library to Human Readable Format :material-chevron-triple-up:{ .priority-high title="High Priority" } **[v10.0.0]**
    - Intended to give users more flexible options with their data if they wish to migrate away from TagStudio
