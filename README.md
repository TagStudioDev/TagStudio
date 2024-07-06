# TagStudio (Alpha): A User-Focused Document Management System

<p align="center">
  <img width="60%" src="github_header.png">
</p>

> [!CAUTION]
> This is still a **_very_** rough personal project of mine in its infancy. I’m open-sourcing it now in order to accept contributors sooner and to better facilitate the direction of the project from an earlier stage.
> There **_are_** bugs, and there will **_very likely_** be breaking changes!

TagStudio is a photo & file organization application with an underlying system that focuses on giving freedom and flexibility to the user. No proprietary programs or formats, no sea of sidecar files, and no complete upheaval of your filesystem structure.

<figure align="center">
  <img width="80%" src="screenshot.jpg" alt="TagStudio Screenshot" align="center">

  <figcaption><i>TagStudio Alpha v9.1.0 running on Windows 10.</i></figcaption>
</figure>

## Contents

- [Goals](#goals)
- [Priorities](#priorities)
- [Current Features](#current-features)
- [Contributing](#contributing)
- [Installation](#installation)
- [Usage](#usage)
- [FAQ](#faq)

## Goals

- To achieve a portable, privacy-oriented, open, extensible, and feature-rich system of organizing and rediscovering files.
- To provide powerful methods for organization, notably the concept of tag composition, or “taggable tags”.
- To create an implementation of such a system that is resilient against a user’s actions outside the program (modifying, moving, or renaming files) while also not burdening the user with mandatory sidecar files or otherwise requiring them to change their existing file structures and workflows.
- To support a wide range of users spanning across different platforms, multi-user setups, and those with large (several terabyte) libraries.
- To make the darn thing look like nice, too. It’s 2024, not 1994.

## Priorities

1. **The concept.** Even if TagStudio as a project or application fails, I’d hope that the idea lives on in a superior project. The [goals](#goals) outlined above don’t reference TagStudio once - _TagStudio_ is what references the _goals._
2. **The system.** Frontends and implementations can vary, as they should. The core underlying metadata management system is what should be interoperable between different frontends, programs, and operating systems. A standard implementation for this should settle as development continues. This opens up the doors for improved and varied clients, integration with third-party applications, and more.
3. **The application.** If nothing else, TagStudio the application serves as the first (and so far only) implementation for this system of metadata management. This has the responsibility of doing the idea justice and showing just what’s possible when it comes to user file management.
4. (The name.) I think it’s fine for an app or client, but it doesn’t really make sense for a system or standard. I suppose this will evolve with time.

## Current Features

- Create libraries/vaults centered around a system directory. Libraries contain a series of entries: the representations of your files combined with metadata fields. Each entry represents a file in your library’s directory, and is linked to its location.
- Add metadata to your library entries, including:
  - Name, Author, Artist (Single-Line Text Fields)
  - Description, Notes (Multiline Text Fields)
  - Tags, Meta Tags, Content Tags (Tag Boxes)
- Create rich tags composed of a name, a list of aliases, and a list of “subtags” - being tags in which these tags inherit values from.
- Search for entries based on tags, ~~metadata~~ (TBA), or filenames/filetypes (using `filename:<query>`)
- Special search conditions for entries that are: `untagged`/`no_tags`, `empty`/`no_fields`, `no_author`/`no_artist`, and `missing`/`no_file`.
- Search for entries using Boolean expressions. (See the [search cheat-sheet](#search-cheat-sheet) section for more)

> [!NOTE]
> For more information on the project itself, please see the [FAQ](#faq) section as well as the [documentation](/doc/index.md).

## Contributing

If you're interested in contributing to TagStudio, please take a look at the [contribution guidelines](/CONTRIBUTING.md) for how to get started!

## Installation

To download TagStudio, visit the [Releases](https://github.com/TagStudioDev/TagStudio/releases) section of the GitHub repository and download the latest release for your system under the "Assets" section. TagStudio is available for **Windows**, **macOS** _(Apple Silicon & Intel)_, and **Linux**. Windows and Linux builds are also available in portable versions if you want a more self-contained executable to move around.

> [!IMPORTANT]
> On macOS, you may be met with a message saying _""TagStudio" can't be opened because Apple cannot check it for malicious software."_ If you encounter this, then you'll need to go to the "Settings" app, navigate to "Privacy & Security", and scroll down to a section that says _""TagStudio" was blocked from use because it is not from an identified developer."_ Click the "Open Anyway" button to allow TagStudio to run. You should only have to do this once after downloading the application.

#### Optional Arguments

Optional arguments to pass to the program.

> `--open <path>` / `-o <path>`
> Path to a TagStudio Library folder to open on start.

> `--config-file <path>` / `-c <path>`
> Path to the TagStudio config file to load.

## Usage

### Creating/Opening a Library

With TagStudio opened, start by creating a new library or opening an existing one using File -> Open/Create Library from the menu bar. TagStudio will automatically create a new library from the chosen directory if one does not already exist. Upon creating a new library, TagStudio will automatically scan your folders for files and add those to your library (no files are moved during this process!).

### Refreshing the Library

In order to scan for new files or file changes, you’ll need to manually go to File -> Refresh Directories.

> [!NOTE]
> In the future, library refreshing will also be automatically done in the background, or additionally on app startup.

### Adding Metadata to Entries

To add a metadata field to a file entry, start by clicking the “Add Field” button under the file preview in the right-hand preview panel. From the dropdown menu, select the type of metadata field you’d like to add to the entry.

### Editing Metadata Fields

#### Text Line / Text Box

Hover over the field and click the pencil icon. From there, add or edit text in the dialog box popup.

#### Tag Box

Click the “+” button at the end of the Tags list, and search for tags to add inside the new dialog popup. Click the “+” button next to whichever tags you want to add. Alternatively, after you search for a tag, press the Enter/Return key to add the add the first item in the list. Press Enter/Return once more to close the dialog box

> [!WARNING]
> Keyboard control and navigation is currently _very_ buggy, but will be improved in future versions.

### Creating Tags

To create a new tag, click on Edit -> New Tag from the menu bar. From there, enter a tag name, shorthand name, any tag aliases separated by newlines, any subtags, and an optional color.

- The tag **shorthand** is a type of alias that displays in situations when screen space is more valuable (ex. as a subtag for other tags).
- **Aliases** are alternate names for a tag. These let you search for terms other than the exact tag name in order to find the tag again.
- **Subtags** are tags in which this tag is a child tag of. In other words, tags under this section are parents of this tag. For example, if you had a tag for a character from a show, you would make the show a subtag of this character. This would display as “Character (Show)” in most areas of the app. The first tag in this list is used as the tag shown in parentheses for specification.
- The **color** dropdown lets you select an optional color for this tag to display as.

### Editing Tags

To edit a tag, right-click the tag in the tag field of the preview pane and select “Edit Tag”

### Relinking Renamed/Moved Files

Inevitably, some of the files inside your library will be renamed, moved, or deleted. If a file has been renamed or moved, TagStudio will display the thumbnail as a red tag with a cross through it _(this icon is also used for items with broken thumbnails)._ To relink moved files or delete these entries, go to Tools -> Manage Unlinked Entries. Click the “Refresh” button to scan your library for unlinked entries. Once complete, you can attempt to “Search & Relink” any unlinked entries to their respective files, or “Delete Unlinked Entries” in the event the original files have been deleted and you no longer wish to keep their metadata entries inside your library.

> [!WARNING]
> There is currently no method to relink entries to files that have been renamed - only moved or deleted. This is a top priority for future releases.

> [!WARNING]
> If multiple matches for a moved file are found (matches are currently defined as files with a matching filename as the original), TagStudio will currently ignore the match groups. Adding a GUI for manual selection, as well as smarter automated relinking, are top priorities for future versions.

### Saving the Library

Libraries are saved upon exiting the program. To manually save, select File -> Save Library from the menu bar. To save a backup of your library, select File -> Save Library Backup from the menu bar.

### Search Cheat-Sheet

#### The Basics

After loading a tagged library, enter your search into the bar that says `Search Entries` at the top of the window. Every tag needs a space after it. If your tag contains spaces between words, substitute underscores _ for the spaces. Capitalization doesn't affect tags and searches. After you have typed your search, press enter or click the `Search` button to the right of the search bar. It may take a moment for the search to complete. After you have made a few searches, you can use the arrows `<` `>` on the left hand side of the search bar to bring back previous searches.
- **dog favorites** searches favorites for any entry tagged "dog"
- **fat_cat dress_up** searches entries for the "fat cat" tag and searches for the "dress up" tag

#### Search Modes

On the right side of the window, just below the search bar, there is a dropdown option to choose the search bar. The options are `And (Includes All Tags)`, and `Or (Includes Any Tag)`. In And mode, if you have a list of search terms in the search bar, your search will try to match entries fitting all the search terms in the list. In Or mode, your search will try to match entries fitting even just one of the search terms.

#### Optional Terms and Partial Match Terms

If you have a search list with many search terms, you may use tilde ~ before a term to mark it as an optional term in And mode, or as a partial match term in Or mode.
- In And mode, an entry with even just one of the tilde ~ marked optional terms can match a search list that uses them, so long as the entry matches all other terms in the list.
  - **costume ~witch ~skeleton** matches all entries tagged costume and witch, and all entries tagged costume and skeleton.
- In Or mode, an entry with all of the tilde ~ marked partial match terms will match a search list that uses them, even if the entry matches no other terms in the list.
  - **lake river ~indoors ~life_vest** matches all entries tagged "lake", tagged "river", or tagged with both "indoors" and "life vest".

> [!NOTE]
> For simplicity, the remaining search examples are written for And mode unless otherwise specified.

#### Exclude Terms

Using minus -, exclamation mark !, or "not" before a term matches when the term doesn't. "not" needs a space after it. Tilde ~ will have no effect unless it comes before the exclude indicator.
- **-golf** matches any entry that doesn't have the "golf" tag.
- **party -birthday** matches any entry that has the "party" tag, but that does not have the "birthday" tag.

#### Parentheses

Surrounding a list of search terms with parentheses () makes it act like a single term, and allows for more complicated nesting of tags. Every parenthesis needs a space after it, or it will be interpreted as being part of a tag. Square brackets \[\] and curly braces {} can be used too.
- **woods -( scary ~weapon ~animal )** matches any entry with the "woods" tag, unless it is also tagged "scary" and "weapon", or "scary" and "animal"

#### Other Operators

It is also possible to use various Boolean operators directly when combining tags instead of relying on tags to be combined automatically. These operators will be evaluated from left to right, after parentheses and exclusion operators, but before the implicit operations in lists of search terms. Every one of these Boolean operators needs a space after it, or it will be interpreted as being part of a tag. Many operators are supported, and many ways of writing the operators are supported. Here is a list: "and", "^", "&", "&&", "or", "v", "|", "||", "nor", "nand", "xor", "!=", "!=\=", "xnor", "=", "=\=", or "=\=\=".
- **sad == dark_clothes and photograph** matches any entry tagged "photograph", but that doesn't have exactly one "sad" or "dark clothes" tag without the other.

#### Metatags

There are some terms that can be matched even without the need to be specifically tagged ahead of time. The following are the supported metatags:
- **untagged**/**no_tags** whether the entry has no tags at all yet.
- **empty**/**no_fields** whether the entry has no fields at all, tag or otherwise. This covers text lines, text boxes, dates, and more.
- **no_author**/**no_artist** whether the "Author" or "Artist" fields aren't present in the entry.
- **filename:** matches any portion of text in the name and subdirectory that the file is located in relative to the library's path. Here are some usage examples:
  - **filename:copy.png** matches any .PNG file whose filename ends with "copy" regardless of directory, such as "shared img \- Copy.png"
  - **filename:subdir1\subdir2** matches any file in subdir2, such as "subdir1\subdir2\subdir3\hidden.gif"
  - **filename:subdir3\photo.jpg** matches any file named photo.jpg in a folder called "subdir3", even if the path to it from the library directory is something like "subdir1\subdir2\subdir3\photo.jpg".
- **tag_id:** matches any entry with a tag whose internal id matches the number. Click on a tag in the preview pane on the right to replace the search with a tag_id expression for that tag.
  - **tag_id:1001** matches any entry tagged with the first custom tag created for the library.
- Hopefully more coming in the future!

#### Escape Characters

If the name of one of your tags overlaps with the search syntax, then put a backslash \\ or a forward slash / just before the tag to ensure it's treated like a tag.
- **~clip_art ~stock_photo \\\~cute~** matches entries tagged "clip art" and "\~cute~" or "stock photo" and "\~cute~". Without the backslash, the tilde ~ at the start of the "\~cute~" tag would mistakenly result in the mandatory "\~cute~" tag being interpreted as an optional "cute~" tag, missing the first tilde.
- **transparent -\\empty -roses** matches entries tagged "transparent", but not tagged "empty" or "roses". Without the backslash, the "empty" tag would be interpreted as a metatag instead of a tag, meaning that the results would mistakenly include entries tagged "empty", since the entry didn't have "no_fields".

### Half-Implemented Features

#### Fix Duplicate Files

Load in a .dupeguru file generated by [dupeGuru](https://github.com/arsenetar/dupeguru/) and mirror metadata across entries marked as duplicates. After mirroring, return to dupeGuru to manage deletion of the duplicate files. After deletion, use the “Fix Unlinked Entries” feature in TagStudio to delete the duplicate set of entries for the now-deleted files

> [!CAUTION]
> While this feature is functional, it’s a pretty roundabout process and can be streamlined in the future.

#### Image Collage

Create an image collage of your photos and videos.

> [!CAUTION]
> Collage sizes and options are hardcoded, and there's no GUI indicating the process of the collage creation.

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

As of writing (Alpha v9.3.0) the project is in a useable state, however it lacks proper testing and quality of life features.

### What Features Are You Planning on Adding?

> [!IMPORTANT]
> See the [Planned Features](/doc/updates/planned_features.md) documentation for the latest feature lists. The lists here are currently being migrated over there with individual pages for larger features.

Of the several features I have planned for the project, these are broken up into “priority” features and “future” features. Priority features were originally intended for the first public release, however are currently absent from the Alpha v9.x.x builds.

#### Priority Features

- Improved search
  - Sortable Search
  - Coexisting Text + Tag Search
  - Searchable File Metadata
- Comprehensive Tag management tab
- Easier ways to apply tags in bulk
  - Tag Search Panel
  - Recent Tags Panel
  - Top Tags Panel
  - Pinned Tags Panel
- Better (stable, performant) library grid view
- Improved entry relinking
- Cached thumbnails
- Tag-like Groups
- Resizable thumbnail grid
- User-defined metadata fields
- Multiple directory support
- SQLite (or similar) save files
- Reading of EXIF and XMP fields
- Improved UI/UX
- Better internal API for accessing Entries, Tags, Fields, etc. from the library.
- Proper testing workflow
- Continued code cleanup and modularization
- Exportable/importable library data including "Tag Packs"

#### Future Features

- Support for multiple simultaneous users/clients
- Draggable files outside the program
- Comprehensive filetype whitelist
- A finished “macro system” for automatic tagging based on predetermined criteria.
- Different library views
- Date and time fields
- Entry linking/referencing
- Audio waveform previews
- 3D object previews
- Additional previews for miscellaneous file types
- Optional global tags and settings, spanning across libraries
- Importing & exporting libraries to/from other programs
- Port to a more performant language and modern frontend (Rust?, Tauri?, etc.)
- Plugin system
- Local OCR search
- Support for local machine learning-based tag suggestions for images
- Mobile version _(FAR future)_

#### Features I Likely Won’t Add/Pull

- Native Cloud Integration
  - There are plenty of services already (native or third-party) that allow you to mount your cloud drives as virtual drives on your system. Pointing TagStudio to one of these mounts should function similarly to what native integration would look like.
- Native ChatGPT/Non-Local LLM Integration
  - This could mean different things depending on what you're intending. Whether it's trying to use an LLM to replace the native search, or to trying to use a model for image recognition, I'm not interested in hooking people's TagStudio libraries into non-local LLMs such as ChatGPT and/or turn the program into a "chatbot" interface (see: [Goals/Privacy](#goals)). I wouldn't, however, mind using **locally** hosted models to provide the _optional_ ability for additional searching and tagging methods (especially when it comes to facial recognition).

### Why Is the Version Already v9?

I’ve been developing this project over several years in private, and have gone through several major iterations and rewrites in that time. This “major version” is just a number at the end of the day, and if I wanted to I couldn’t released this as “Version 0” or “Version 1.0”, but I’ve decided to stick to my original version numbers to avoid needing to go in and change existing documentation and code comments. Version 10 is intended to include all of the “Priority Features” I’ve outlined in the [previous](#what-features-are-you-planning-on-adding) section. I’ve also labeled this version as an Alpha, and will likely reset the numbers when a feature-complete beta is reached.

### Wait, Is There a CLI Version?

As of right now, **no**. However, I _did_ have a CLI version in the recent past before dedicating my efforts to the Qt GUI version. I’ve left in the currently-inoperable CLI code just in case anyone was curious about it. Also yes, it’s just a bunch of glorified print statements (_the outlook for some form of curses on Windows didn’t look great at the time, and I just needed a driver for the newly refactored code...)._
