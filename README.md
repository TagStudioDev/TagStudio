# TagStudio: A User-Focused Document Management System

[![Translation](https://hosted.weblate.org/widget/tagstudio/strings/svg-badge.svg)](https://hosted.weblate.org/projects/tagstudio/strings/)
[![PyTest](https://github.com/TagStudioDev/TagStudio/actions/workflows/pytest.yaml/badge.svg)](https://github.com/TagStudioDev/TagStudio/actions/workflows/pytest.yaml)
[![MyPy](https://github.com/TagStudioDev/TagStudio/actions/workflows/mypy.yaml/badge.svg)](https://github.com/TagStudioDev/TagStudio/actions/workflows/mypy.yaml)
[![Ruff](https://github.com/TagStudioDev/TagStudio/actions/workflows/ruff.yaml/badge.svg)](https://github.com/TagStudioDev/TagStudio/actions/workflows/ruff.yaml)
[![Downloads](https://img.shields.io/github/downloads/TagStudioDev/TagStudio/total.svg?maxAge=2592001)](https://github.com/TagStudioDev/TagStudio/releases)

<p align="center">
  <img width="60%" src="docs/assets/github_header.png">
</p>

TagStudio is a photo & file organization application with an underlying tag-based system that focuses on giving freedom and flexibility to the user. No proprietary programs or formats, no sea of sidecar files, and no complete upheaval of your filesystem structure. **Read the documentation and more at [docs.tagstud.io](https://docs.tagstud.io)!**

> [!NOTE]
> Thank you for being patient as we've migrated our database backend from JSON to SQL! The previous warnings about the main branch being experimental and unsupported have now been removed, and any pre-existing library save files created with official TagStudio releases are able to be opened and migrated with the new v9.5+ releases!

> [!IMPORTANT]
> This project is still in an early state. There are many missing optimizations and QoL features, as well as the presence of general quirks and occasional jankiness. Making frequent backups of your library save data is **always** important, regardless of what state the program is in.
>
> With this in mind, TagStudio will _NOT:_
>
> -   Touch, move, or mess with your files in any way _(unless explicitly using the "Delete File(s)" feature, which is locked behind a confirmation dialog)_.
> -   Ask you to recreate your tags or libraries after new releases. It's our highest priority to ensure that your data safely and smoothly transfers over to newer versions.
> -   Cause you to suddenly be able to recall your 10 trillion downloaded images that you probably haven't even seen firsthand before. You're in control here, and even tools out there that use machine learning still needed to be verified by human eyes before being deemed accurate.

<p align="center">
  <img width="80%" src="docs/assets/screenshot.png" alt="TagStudio Screenshot">
</p>
<p align="center">
  <i>TagStudio Alpha v9.5.0 running on macOS Sequoia.</i>
</p>

## Contents

-   [Goals](#goals)
-   [Priorities](#priorities)
-   [Current Features](#current-features)
-   [Contributing](#contributing)
-   [Installation](#installation)
-   [Usage](#usage)
-   [FAQ](#faq)

## Goals

-   To achieve a portable, private, extensible, open-format, and feature-rich system of organizing and rediscovering files.
-   To provide powerful methods for organization, notably the concept of tag inheritance, or “taggable tags” _(and in the near future, the combination of composition-based tags)._
-   To create an implementation of such a system that is resilient against a user’s actions outside the program (modifying, moving, or renaming files) while also not burdening the user with mandatory sidecar files or requiring them to change their existing file structures and workflows.
-   To support a wide range of users spanning across different platforms, multi-user setups, and those with large (several terabyte) libraries.
-   To make the dang thing look nice, too. It’s 2025, not 1995.

## Priorities

1. **The concept.** Even if TagStudio as an application fails, I’d hope that the idea lives on in a superior project. The [goals](#goals) outlined above don’t reference TagStudio once - _TagStudio_ is what references the _goals._
2. **The system.** Frontends and implementations can vary, as they should. The core underlying metadata management system is what should be interoperable between different frontends, programs, and operating systems. A standard implementation for this should settle as development continues. This opens up the doors for improved and varied clients, integration with third-party applications, and more.
3. **The application.** If nothing else, TagStudio the application serves as the first (and so far only) implementation for this system of metadata management. This has the responsibility of doing the idea justice and showing just what’s possible when it comes to user file management.
4. (The name.) I think it’s fine for an app or client, but it doesn’t really make sense for a system or standard. I suppose this will evolve with time...

## Contributing

If you're interested in contributing to TagStudio, please take a look at the [contribution guidelines](/CONTRIBUTING.md) for how to get started!

Translation hosting generously provided by [Weblate](https://weblate.org/en/). Check out our [project page](https://hosted.weblate.org/projects/tagstudio/) to help translate TagStudio!

## Current Features

### Libraries

-   Create libraries/vaults centered around a system directory. Libraries contain a series of entries: the representations of your files combined with metadata fields. Each entry represents a file in your library’s directory, and is linked to its location.
-   Address moved, deleted, or otherwise "unlinked" files by using the "Fix Unlinked Entries" option in the Tools menu.

### Tagging + Custom Metadata

-   Add custom powerful tags to your library entries
-   Add metadata to your library entries, including:
    -   Name, Author, Artist (Single-Line Text Fields)
    -   Description, Notes (Multiline Text Fields)
-   Create rich tags composed of a name, color, a list of aliases, and a list of “parent tags” - these being tags in which these tags inherit values from.
-   Copy and paste tags and fields across file entries
-   Automatically organize tags into groups based on parent tags marked as "categories"
-   Generate tags from your existing folder structure with the "Folders to Tags" macro (NOTE: these tags do NOT sync with folders after they are created)

### Search

-   Search for file entries based on tags, file path (`path:`), file types (`filetype:`), and even media types! (`mediatype:`). Path searches currently use [glob](<https://en.wikipedia.org/wiki/Glob_(programming)>) syntax, so you may need to wrap your filename or filepath in asterisks while searching. This will not be strictly necessary in future versions of the program.
-   Use and combine boolean operators (`AND`, `OR`, `NOT`) along with parentheses groups, quotation escaping, and underscore substitution to create detailed search queries
-   Use special search conditions (`special:untagged` and `special:empty`) to find file entries without tags or fields, respectively

### File Entries

-   Nearly all file types are supported in TagStudio libraries - just not all have dedicated thumbnail support.
-   Preview most image file types, animated GIFs, videos, plain text documents, audio files, Blender projects, and more!
-   Open files or file locations by right-clicking on thumbnails and previews and selecting the respective context menu options. You can also click on the preview panel image to open the file, and click the file path label to open its location.
-   Delete files from both your library and drive by right-clicking the thumbnail(s) and selecting the "Move to Trash"/"Move to Recycle Bin" option.

> [!NOTE]
> For more information on the project itself, please see the [FAQ](#faq) section as well as the [documentation](https://docs.tagstud.io/)!

## Installation

To download TagStudio, visit the [Releases](https://github.com/TagStudioDev/TagStudio/releases) section of the GitHub repository and download the latest release for your system under the "Assets" section. TagStudio is available for **Windows**, **macOS** _(Apple Silicon & Intel)_, and **Linux**. Windows and Linux builds are also available in portable versions if you want a more self-contained executable to move around.

**We do not currently publish TagStudio to any package managers. Any TagStudio distributions outside of the GitHub releases page are _unofficial_ and not maintained by us.** Installation support will not be given to users installing from unofficial sources. Use these versions at your own risk.

> [!IMPORTANT]
> On macOS, you may be met with a message saying _""TagStudio" can't be opened because Apple cannot check it for malicious software."_ If you encounter this, then you'll need to go to the "Settings" app, navigate to "Privacy & Security", and scroll down to a section that says _""TagStudio" was blocked from use because it is not from an identified developer."_ Click the "Open Anyway" button to allow TagStudio to run. You should only have to do this once after downloading the application.

> [!IMPORTANT]
> On Linux with non-Qt based Desktop Environments you may be unable to open TagStudio. You need to make sure that "xcb-cursor0" or "libxcb-cursor0" packages are installed. For more info check [Missing linux dependencies](https://github.com/TagStudioDev/TagStudio/discussions/182#discussioncomment-9452896)

### Third-Party Dependencies

-   For video thumbnails and playback, you'll also need [FFmpeg](https://ffmpeg.org/download.html) installed on your system. If you encounter any issues with this, please reference our [FFmpeg Help](/docs/help/ffmpeg.md) guide.

### Optional Arguments

Arguments available to pass to the program, either via the command line or a shortcut.

> `--open <path>` / `-o <path>`
> Path to a TagStudio Library folder to open on start.
>
> `--config-file <path>` / `-c <path>`
> Path to the TagStudio config file to load.

## Usage

### Creating/Opening a Library

With TagStudio opened, start by creating a new library or opening an existing one using File -> Open/Create Library from the menu bar. TagStudio will automatically create a new library from the chosen directory if one does not already exist. Upon creating a new library, TagStudio will automatically scan your folders for files and add those to your library (no files are moved during this process!).

### Refreshing the Library

Libraries under 10,000 files automatically scan for new or modified files when opened. In order to refresh the library manually, select "Refresh Directories" under the File menu.

### Adding Tags to File Entries

Access the "Add Tag" search box by either clicking on the "Add Tag" button at the bottom of the right sidebar, accessing the "Add Tags to Selected" option from the File menu, or by pressing <kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>T</kbd>.

From here you can search for existing tags or create a new one if the one you're looking for doesn't exist. Click the “+” button next to any tags you want to to the currently selected file entries. To quickly add the top result, press the <kbd>Enter</kbd>/<kbd>Return</kbd> key to add the the topmost tag and reset the tag search. Press <kbd>Enter</kbd>/<kbd>Return</kbd> once more to close the dialog box. By using this method, you can quickly add various tags in quick succession just by using the keyboard!

To remove a tag from a file entry, hover over the tag in the preview panel and click on the "-" icon that appears.

### Adding Metadata to File Entries

To add a metadata field to a file entry, start by clicking the “Add Field” button at the bottom of the preview panel. From the dropdown menu, select the type of metadata field you’d like to add to the entry

### Editing Metadata Fields

#### Text Line / Text Box

Hover over the field and click the pencil icon. From there, add or edit text in the dialog box popup.

> [!WARNING]
> Keyboard control and navigation is currently _very_ buggy, but will be improved in future versions.

### Creating Tags

Create a new tag by accessing the "New Tag" option from the Edit menu or by pressing <kbd>Ctrl</kbd>+<kbd>T</kbd>. In the tag creation panel, enter a tag name, optional shorthand name, optional tag aliases, optional parent tags, and an optional color.

-   The tag **name** is the base name of the tag. **_This does NOT have to be unique!_**
-   The tag **shorthand** is a special type of alias that displays in situations where screen space is more valuable, notably with name disambiguation.
-   **Aliases** are alternate names for a tag. These let you search for terms other than the exact tag name in order to find the tag again.
-   **Parent Tags** are tags in which this this tag can substitute for in searches. In other words, tags under this section are parents of this tag.
    -   Parent tags with the disambiguation check next to them will be used to help disambiguate tag names that may not be unique.
    -   For example: If you had a tag for "Freddy Fazbear", you might add "Five Nights at Freddy's" as one of the parent tags. If the disambiguation box is checked next to "Five Nights at Freddy's" parent tag, then the tag "Freddy Fazbear" will display as "Freddy Fazbear (Five Nights at Freddy's)". Furthermore, if the "Five Nights at Freddy's" tag has a shorthand like "FNAF", then the "Freddy Fazbear" tag will display as "Freddy Fazbear (FNAF)".
-   The **color** option lets you select an optional color palette to use for your tag.
-   The **"Is Cagegory"** property lets you treat this tag as a category under which itself and any child tags inheriting from it will be sorted by inside the preview panel.

#### Tag Manager

You can manage your library of tags from opening the "Tag Manager" panel from Edit -> "Tag Manager". From here you can create, search for, edit, and permanently delete any tags you've created in your library.

### Editing Tags

To edit a tag, click on it inside the preview panel or right-click the tag and select “Edit Tag” from the context menu.

### Relinking Moved Files

Inevitably some of the files inside your library will be renamed, moved, or deleted. If a file has been renamed or moved, TagStudio will display the thumbnail as a red broken chain link. To relink moved files or delete these entries, select the "Manage Unlinked Entries" option under the Tools menu. Click the "Refresh" button to scan your library for unlinked entries. Once complete, you can attempt to “Search & Relink” any unlinked file entries to their respective files, or “Delete Unlinked Entries” in the event the original files have been deleted and you no longer wish to keep their entries inside your library.

> [!WARNING]
> There is currently no method to relink entries to files that have been renamed - only moved or deleted. This is a high priority for future releases.

> [!WARNING]
> If multiple matches for a moved file are found (matches are currently defined as files with a matching filename as the original), TagStudio will currently ignore the match groups. Adding a GUI for manual selection, as well as smarter automated relinking, are high priorities for future versions.

### Saving the Library

As of version 9.5, libraries are saved automatically as you go. To save a backup of your library, select File -> Save Library Backup from the menu bar.

### Half-Implemented Features

These features were present in pre-public versions of TagStudio (9.0 and below) and have yet to be fully implemented.

#### Fix Duplicate Files

Load in a .dupeguru file generated by [dupeGuru](https://github.com/arsenetar/dupeguru/) and mirror metadata across entries marked as duplicates. After mirroring, return to dupeGuru to manage deletion of the duplicate files. After deletion, use the “Fix Unlinked Entries” feature in TagStudio to delete the duplicate set of entries for the now-deleted files

> [!CAUTION]
> While this feature is functional, it’s a pretty roundabout process and can be streamlined in the future.

#### Macros

Apply tags and other metadata automatically depending on certain criteria. Set specific macros to run when the files are added to the library. Part of this includes applying tags automatically based on parent folders.

> [!CAUTION]
> Macro options are hardcoded, and there’s currently no way for the user to interface with this (still incomplete) system at all.

#### Gallery-dl Sidecar Importing

Import JSON sidecar data generated by [gallery-dl](https://github.com/mikf/gallery-dl).

> [!CAUTION]
> This feature is not supported or documented in any official capacity whatsoever. It will likely be rolled-in to a larger and more generalized sidecar importing feature in the future.

## Launching/Building From Source

See instructions in the "[Creating Development Environment](/CONTRIBUTING.md/#creating-a-development-environment)" section from the [contribution documentation](/CONTRIBUTING.md).

## FAQ

### What State Is the Project Currently In?

As of writing (Alpha v9.5.0) the project is very usable, however there's some plenty of quirks and missing QoL features. Several additional features and changes are still planned (see: [Feature Roadmap](https://docs.tagstud.io/updates/roadmap/)) that add even more power and flexibility to the tagging and field systems while making it easier to tag in bulk and perform automated operations. Bugfixes and polish are constantly trickling in along with the larger feature releases.

### What Features Are You Planning on Adding?

See the [Feature Roadmap](https://docs.tagstud.io/updates/roadmap/) page for the core features being planned and implemented for TagStudio. For a more up to date look on what's currently being added for upcoming releases, see our GitHub [milestones](https://github.com/TagStudioDev/TagStudio/milestones) for versioned releases.

### Features That Will NOT Be Added

-   Native Cloud Integration
    -   There are plenty of services already (native or third-party) that allow you to mount your cloud drives as virtual drives on your system. Hosting a TagStudio library on one of these mounts should function similarly to what native integration would look like.
    -   Supporting native cloud integrations such as these would be an unnecessary "reinventing the wheel" burden for us that is outside the scope of this project.
-   Native ChatGPT/Non-Local LLM Integration
    -   This could mean different things depending on your intentions. Whether it's trying to use an LLM to replace the native search, or to trying to use a model for image recognition, I'm not interested in hooking people's TagStudio libraries into non-local LLMs such as ChatGPT and/or turn the program into a "chatbot" interface (see: [Goals/Privacy](#goals)). I wouldn't, however, mind using **locally** hosted models to provide the _optional_ ability for additional searching and tagging methods (especially when it comes to facial recognition) - but this would likely take the form of plugins external to the core program anyway.

### Why Is this Already Version 9?

Over the first few years of private development the project went through several major iterations and rewrites. These major version bumps came quickly, and by the time TagStudio was opened-sourced the version number had already reached v9.0. Instead of resetting to "v0.0" or "v1.0" for this public release I decided to keep my v9.x numbering scheme and reserve v10.0 for when all the core features on the [Feature Roadmap](https://docs.tagstud.io/updates/roadmap/) are implemented. I’ve also labeled this version as an "Alpha" and will drop this once either all of the core features are implemented or the project feels stable and feature-rich enough to be considered "Beta" and beyond.
