<a id="readme-top"></a>

<!-- PROJECT SHIELDS -->
<!--
*** I'm using markdown "reference style" links for readability.
*** Reference links are enclosed in brackets [ ] instead of parentheses ( ).
*** See the bottom of this document for the declaration of the reference variables
*** for contributors-url, forks-url, etc. This is an optional, concise syntax you may use.
*** https://www.markdownguide.org/basic-syntax/#reference-style-links
-->
[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![License][license-shield]][license-url]

<br />
<div align="center">
  <a href="https://github.com/TagStudioDev/TagStudio">
    <img src="github_header.png" alt="TagStudioAlpha">
  </a>

<h1 align="center">TagStudio</h1>

  <p align="center">
    A User-Focused Photo & File Organizing System
    <br />
    <a href="https://discord.gg/hRNnVKhF2G"><strong>Join The Discord</strong></a> or <a href="https://github.com/TagStudioDev/TagStudio/wiki"><strong>View The Documentation</strong></a>
    <br />
    <br />
    <a href="https://github.com/TagStudioDev/TagStudio/releases">Releases</a>
    ·
    <a href="https://github.com/TagStudioDev/TagStudio/issues/new?template=bug_report.yml&projects=&title=%5BBug%5D:+&labels=Type:+Bug&assignees=">Report Bug</a>
    ·
    <a href="https://github.com/TagStudioDev/TagStudio/issues/new?assignees=&labels=Type%3A+Enhancement&projects=&template=feature_request.yml&title=%5BFeature+Request%5D%3A+">Request Feature</a>
  </p>
</div>

<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
      <ul>
        <li><a href="#built-with">Built With</a></li>
        <li>
      <a href="#philosophy">Philosophy</a><ul><li><a href="#goals">Goals</a></li><li><a href="#priorities">Priorities</a></li></ul></li>
      </ul>
    </li>
        <li><a href="#features">Features</a>
        <ul>
        <li><a href="#current-features">Current Features</a></li>
        <li>
      <a href="#planned-features">Planned Features</a><ul>
        <li><a href="#priority-features">Priority</a></li>
        <li>
      <a href="#future-features">Future</a></li><li><a href="#features-off-the-table">Off The Table</a></li></ul></li></ul>
        </li>
        <li><a href="#installation">Installation</a><ul><li><a href="#prerequisites">Prerequisites</a></li><li><a href="#downloading-and-setup">Downloading And Setup</a></li></ul></li>
    </li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#social--contact">Social & Contact</a></li>
    <li><a href="#acknowledgments">Acknowledgments</a></li>
  </ol>
</details>

## About The Project

> [!WARNING]
> __**Low Budget Ad Warning**__ <br />
> Hey Hey Hey! We also have a **Rust** fork, that is planned to eventually phase out the current upstream python version. Soon we will be accepting contributions. [Learn more here](https://github.com/TagStudioDev/TagStudioRusted)

> [!CAUTION]
> This started as a **_very_** rough personal project of mine, and it was open sourced due to the community. It is still in its infancy. Open sourcing also helps accept contributors sooner and to better facilitate the direction of the project from an earlier stage.
> There **_are_** bugs, and there will **_very likely_** be breaking changes!

[![Product Name Screen Shot][product-screenshot]](https://example.com)
<p align="right"><i>TagStudio Alpha v9.1.0 running on Windows 10.</i></p>

TagStudio is a photo & file organization application with an underlying system that focuses on giving freedom and flexibility to the user. No proprietary programs or formats, no sea of sidecar files, and no complete upheaval of your filesystem structure.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Built With

* [![Python][python]][python-url]
* [![Qt for Python][qt]][qt-url]
* [![SQLite][sqlite]][sqlite-url]

<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Philosophy

TagStudio is not a product. It is an *idea*. Here are the boundaries that define it.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

#### Goals

> [!NOTE]
> **TLDR:** Portable. Private. Open. Extensible. Feature-rich. Powerful. Fast. Reliable. Lightweight. Scalable. Cross-platform. Beautiful. Tags. Lots of em.
>
>  Neat, right?

- To achieve a portable, privacy-oriented, open, extensible, and feature-rich system of organizing and rediscovering files.
- To provide powerful methods for organization, notably the concept of tag composition, or “taggable tags”.
- To create an implementation of such a system that is resilient against a user’s actions outside the program (modifying, moving, or renaming files) while also not burdening the user with mandatory sidecar files or otherwise requiring them to change their existing file structures and workflows.
- To support a wide range of users spanning across different platforms, multi-user setups, and those with large (several terabyte) libraries.
- To make the darn thing look like nice, too. It’s 2024, not 1994.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

#### Priorities

1. **The concept.** Even if TagStudio as a project or application fails, I’d hope that the idea lives on in a superior project. The [goals](#goals) outlined above don’t reference TagStudio once - _TagStudio_ is what references the _goals._
2. **The system.** Frontends and implementations can vary, as they should. The core underlying metadata management system is what should be interoperable between different frontends, programs, and operating systems. A standard implementation for this should settle as development continues. This opens up the doors for improved and varied clients, integration with third-party applications, and more.
3. **The application.** If nothing else, TagStudio the application serves as the first (and so far only) implementation for this system of metadata management. This has the responsibility of doing the idea justice and showing just what’s possible when it comes to user file management.
4. (The name.) I think it’s fine for an app or client, but it doesn’t really make sense for a system or standard. I suppose this will evolve with time.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Features

This section lists the current and furure featureset TagStudio operates or will operate with.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Current Features

> [!NOTE]
> These are the currently available features, if you download the lates available preview build. There are a lot more planned features.

- Create libraries/vaults centered around a system directory. Libraries contain a series of entries: the representations of your files combined with metadata fields. Each entry represents a file in your library’s directory, and is linked to its location.
- Add metadata to your library entries, including:
  - Name, Author, Artist (Single-Line Text Fields)
  - Description, Notes (Multiline Text Fields)
  - Tags, Meta Tags, Content Tags (Tag Boxes)
- Create rich tags composed of a name, a list of aliases, and a list of “subtags” - being tags in which these tags inherit values from.
- Search for entries based on tags, ~~metadata~~ (TBA), or filenames/filetypes (using `filename: <query>`)
- Special search conditions for entries that are: `untagged`/`no tags` and `empty`/`no fields`.

> [!TIP]
> For more information on the project itself, please see the [FAQ](#faq) section as well as the [documentation](/doc/index.md).

<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Planned Features

> [!IMPORTANT]
> See the [Planned Features](/doc/updates/planned_features.md) documentation for the latest feature lists. The lists here are currently being migrated over there with individual pages for larger features.

Of the several features planned for the project, these are broken up into “priority” features and “future” features. Priority features were originally intended for the first public release, however are currently absent from the Alpha v9.x.x builds.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

#### Priority Features

- Improved search
  - Sortable Search
  - Boolean Search
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

<p align="right">(<a href="#readme-top">back to top</a>)</p>

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

<p align="right">(<a href="#readme-top">back to top</a>)</p>

#### Features Off The Table

- Native Cloud Integration
  - There are plenty of services already (native or third-party) that allow you to mount your cloud drives as virtual drives on your system. Pointing TagStudio to one of these mounts should function similarly to what native integration would look like.
- Native ChatGPT/Non-Local LLM Integration
  - This could mean different things depending on what you're intending. Whether it's trying to use an LLM to replace the native search, or to trying to use a model for image recognition, we're not interested in hooking people's TagStudio libraries into non-local LLMs such as ChatGPT and/or turn the program into a "chatbot" interface (see: [Goals/Privacy](#goals)). We wouldn't, however, mind using **locally** hosted models to provide the _optional_ ability for additional searching and tagging methods (especially when it comes to facial recognition).

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Installation

This section will guide you through the requirements and installation of TagStudio.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Prerequisites

System Support:

|        | [![Windows][win]][win-url] | [![Mac][macos]][macos-url]| [![Linux][linux]][linux-url] |
| :----: | :-------------: | :-----------: | :-------------: |
| x86_64 |  ✅ | ✅ | ✅ |
| ARM | ❌ | ✅ | ❌ |
| Portable | ✅ | ❌ | ✅ |

Feel free to build the project for the architecture and OS you need.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

#### Launching/Building From Source

See instructions in the "[Creating Development Environment](/CONTRIBUTING.md/#creating-a-development-environment)" section from the [contribution documentation](/CONTRIBUTING.md).

<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Downloading and Setup

To download TagStudio, visit the [Releases](https://github.com/TagStudioDev/TagStudio/releases) section of the GitHub repository and download the latest release for your system under the "Assets" section.

> [!IMPORTANT]
> On macOS, you may be met with a message saying __""TagStudio" can't be opened because Apple cannot check it for malicious software."__ If you encounter this, then you'll need to go to the "Settings" app, navigate to "Privacy & Security", and scroll down to a section that says __""TagStudio" was blocked from use because it is not from an identified developer."__ Click the "Open Anyway" button to allow TagStudio to run. You should only have to do this once after downloading the application.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

#### Optional Arguments

Optional arguments to pass to the program.

> `--open <path>` / `-o <path>`
> Path to a TagStudio Library folder to open on start.

> `--config-file <path>` / `-c <path>`
> Path to the TagStudio config file to load.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Usage

### Creating/Opening a Library

With TagStudio opened, start by creating a new library or opening an existing one using File -> Open/Create Library from the menu bar. TagStudio will automatically create a new library from the chosen directory if one does not already exist. Upon creating a new library, TagStudio will automatically scan your folders for files and add those to your library (no files are moved during this process!).

<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Refreshing the Library

In order to scan for new files or file changes, you’ll need to manually go to File -> Refresh Directories.

> [!NOTE]
> In the future, library refreshing will also be automatically done in the background, or additionally on app startup.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Adding Metadata to Entries

To add a metadata field to a file entry, start by clicking the “Add Field” button under the file preview in the right-hand preview panel. From the dropdown menu, select the type of metadata field you’d like to add to the entry.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Editing Metadata Fields

#### Text Line / Text Box

Hover over the field and click the pencil icon. From there, add or edit text in the dialog box popup.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

#### Tag Box

Click the “+” button at the end of the Tags list, and search for tags to add inside the new dialog popup. Click the “+” button next to whichever tags you want to add. Alternatively, after you search for a tag, press the Enter/Return key to add the add the first item in the list. Press Enter/Return once more to close the dialog box

> [!WARNING]
> Keyboard control and navigation is currently _very_ buggy, but will be improved in future versions.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Creating Tags

To create a new tag, click on Edit -> New Tag from the menu bar. From there, enter a tag name, shorthand name, any tag aliases separated by newlines, any subtags, and an optional color.

- The tag **shorthand** is a type of alias that displays in situations when screen space is more valuable (ex. as a subtag for other tags).
- **Aliases** are alternate names for a tag. These let you search for terms other than the exact tag name in order to find the tag again.
- **Subtags** are tags in which this tag is a child tag of. In other words, tags under this section are parents of this tag. For example, if you had a tag for a character from a show, you would make the show a subtag of this character. This would display as “Character (Show)” in most areas of the app. The first tag in this list is used as the tag shown in parentheses for specification.
- The **color** dropdown lets you select an optional color for this tag to display as.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Editing Tags

To edit a tag, right-click the tag in the tag field of the preview pane and select “Edit Tag”

<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Relinking Renamed/Moved Files

Inevitably, some of the files inside your library will be renamed, moved, or deleted. If a file has been renamed or moved, TagStudio will display the thumbnail as a red tag with a cross through it _(this icon is also used for items with broken thumbnails)._ To relink moved files or delete these entries, go to Tools -> Manage Unlinked Entries. Click the “Refresh” button to scan your library for unlinked entries. Once complete, you can attempt to “Search & Relink” any unlinked entries to their respective files, or “Delete Unlinked Entries” in the event the original files have been deleted and you no longer wish to keep their metadata entries inside your library.

> [!WARNING]
> There is currently no method to relink entries to files that have been renamed - only moved or deleted. This is a top priority for future releases.

> [!WARNING]
> If multiple matches for a moved file are found (matches are currently defined as files with a matching filename as the original), TagStudio will currently ignore the match groups. Adding a GUI for manual selection, as well as smarter automated relinking, are top priorities for future versions.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Saving the Library

Libraries are saved upon exiting the program. To manually save, select File -> Save Library from the menu bar. To save a backup of your library, select File -> Save Library Backup from the menu bar.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Half-Implemented Features

#### Fix Duplicate Files

Load in a .dupeguru file generated by [dupeGuru](https://github.com/arsenetar/dupeguru/) and mirror metadata across entries marked as duplicates. After mirroring, return to dupeGuru to manage deletion of the duplicate files. After deletion, use the “Fix Unlinked Entries” feature in TagStudio to delete the duplicate set of entries for the now-deleted files

> [!CAUTION]
> While this feature is functional, it’s a pretty roundabout process and can be streamlined in the future.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

#### Image Collage

Create an image collage of your photos and videos.

> [!CAUTION]
> Collage sizes and options are hardcoded, and there's no GUI indicating the process of the collage creation.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

#### Macros

Apply tags and other metadata automatically depending on certain criteria. Set specific macros to run when the files are added to the library. Part of this includes applying tags automatically based on parent folders.

> [!CAUTION]
> Macro options are hardcoded, and there’s currently no way for the user to interface with this (still incomplete) system at all.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

#### Gallery-dl Sidecar Importing

Import JSON sidecar data generated by [gallery-dl](https://github.com/mikf/gallery-dl).

> [!CAUTION]
> This feature is not supported or documented in any official capacity whatsoever. It will likely be rolled-in to a larger and more generalized sidecar importing feature in the future.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Contributing

If you're interested in contributing to TagStudio, please take a look at the [contribution guidelines](/CONTRIBUTING.md) for how to get started!

<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Top contributors
<h3 align="center">They are the ❤️ of our Project</h3> <br />
<a href="https://github.com/TagStudioDev/TagStudio/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=TagStudioDev/TagStudio" alt="TagStudio Top Contributors" />
</a>

## License

Distributed under the GPL-3.0 License. See `LICENSE.txt` for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Social & Contact

* [![Discord][discord]][discord-url]
* [![CyanVoxelYT][cyanyt]][cyanyt-url]

Project Link: [https://github.com/TagStudioDev/TagStudio](https://github.com/TagStudioDev/TagStudio)

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Acknowledgments

* [othneildrew's Readme Template](https://github.com/othneildrew/best-readme-template/)
* [CyanVoxel's absolute banger video](https://youtu.be/wTQeMkYRMcw?si=NEooVj0zsfHoSQJt)
* Mario 😼

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->

[win]: https://img.shields.io/badge/Windows-blue?style=for-the-badge&logo=data:image/svg+xml;base64,PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0idXRmLTgiPz48IS0tIFVwbG9hZGVkIHRvOiBTVkcgUmVwbywgd3d3LnN2Z3JlcG8uY29tLCBHZW5lcmF0b3I6IFNWRyBSZXBvIE1peGVyIFRvb2xzIC0tPgo8c3ZnIHdpZHRoPSI4MDBweCIgaGVpZ2h0PSI4MDBweCIgdmlld0JveD0iMCAwIDM2IDM2IiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHhtbG5zOnhsaW5rPSJodHRwOi8vd3d3LnczLm9yZy8xOTk5L3hsaW5rIiBhcmlhLWhpZGRlbj0idHJ1ZSIgcm9sZT0iaW1nIiBjbGFzcz0iaWNvbmlmeSBpY29uaWZ5LS10d2Vtb2ppIiBwcmVzZXJ2ZUFzcGVjdFJhdGlvPSJ4TWlkWU1pZCBtZWV0Ij48cGF0aCBmaWxsPSIjQkY2OTUyIiBkPSJNMzMuNTQxIDIzLjE5OGMuMzY0LTEuNTc4LjI0My0zLjI2Ni0uNDU4LTQuOTQ2YTguMDE4IDguMDE4IDAgMCAwLTMuMjcxLTMuNzczYy4zMTgtMS4xOTIuMjM0LTIuNDc1LS4zMjQtMy43NWMtLjg0MS0xLjkyLTIuNjYtMy4yMDEtNC43MTItMy41NjJjLjI0OS0uNTcyLjMyOS0xLjI4OS4wMzYtMi4xNjdjLTEtMy01LTEtOC00Ljk5OWMtMi40NCAxLjQ2NC0yLjk3IDMuNjQtMi44NzggNS40ODdjLTIuNDIxLjQxMi0zLjguOTM2LTMuOC45MzZ2LjAwMmEzLjcxMyAzLjcxMyAwIDAgMC0yLjMyMiAzLjQ0MmMwIC44NzkuMzE4IDEuNjc2LjgyOCAyLjMxMmwtLjY5Mi4yNThsLjAwMS4wMDNjLTIuMzMuODcxLTMuOTc1IDIuOTc2LTMuOTc1IDUuNDM5YzAgMS4wNDcuMyAyLjAyNy44MiAyLjg3OEMxLjk3MSAyMi4wMjcgMCAyNC43ODEgMCAyOGMwIDQuNDE4IDMuNjkxIDggOC4yNDQgOGMzLjI2OSAwIDYuNTU5LS43MDMgOS41MzEtMS42NjVDMjAuMDE4IDM1LjM3NSAyMy40NyAzNiAyOC42NjcgMzZBNy4zMzMgNy4zMzMgMCAwIDAgMzYgMjguNjY3YTcuMzEgNy4zMSAwIDAgMC0yLjQ1OS01LjQ2OXoiPjwvcGF0aD48ZWxsaXBzZSBmaWxsPSIjRjVGOEZBIiBjeD0iMTMuNSIgY3k9IjE1LjUiIHJ4PSIzLjUiIHJ5PSI0LjUiPjwvZWxsaXBzZT48ZWxsaXBzZSBmaWxsPSIjRjVGOEZBIiBjeD0iMjMuNSIgY3k9IjE1LjUiIHJ4PSIzLjUiIHJ5PSI0LjUiPjwvZWxsaXBzZT48ZWxsaXBzZSBmaWxsPSIjMjkyRjMzIiBjeD0iMTQiIGN5PSIxNS41IiByeD0iMiIgcnk9IjIuNSI+PC9lbGxpcHNlPjxlbGxpcHNlIGZpbGw9IiMyOTJGMzMiIGN4PSIyMyIgY3k9IjE1LjUiIHJ4PSIyIiByeT0iMi41Ij48L2VsbGlwc2U+PHBhdGggZmlsbD0iIzI5MkYzMyIgZD0iTTkuNDQ3IDI0Ljg5NUM5LjIwMSAyNC40MDIgOS40NSAyNCAxMCAyNGgxOGMuNTUgMCAuNzk5LjQwMi41NTMuODk1QzI4LjU1MyAyNC44OTUgMjYgMzAgMTkgMzBzLTkuNTUzLTUuMTA1LTkuNTUzLTUuMTA1eiI+PC9wYXRoPjxwYXRoIGZpbGw9IiNGMkFCQkEiIGQ9Ik0xOSAyNmMtMi43NzEgMC01LjE1Ny45MjItNi4yOTIgMi4yNTZDMTQuMiAyOS4yMTEgMTYuMjUzIDMwIDE5IDMwczQuODAxLS43ODkgNi4yOTItMS43NDRDMjQuMTU3IDI2LjkyMiAyMS43NzEgMjYgMTkgMjZ6Ij48L3BhdGg+PC9zdmc+
[win-url]: https://youtu.be/toTtunvlqE4?si=5yJDWt9QkzAIbbYG
[macos]: https://img.shields.io/badge/MacOS-000000?style=for-the-badge&logo=apple&logoColor=white
[macos-url]: https://youtu.be/aE9_olxc-cA?si=K2pIs7CfkLD71qVv
[linux]: https://img.shields.io/badge/Linux-000000?style=for-the-badge&logo=linux&logoColor=yellow
[linux-url]: https://en.wikipedia.org/wiki/Linux

[discord]: https://img.shields.io/badge/Discord_Server-5865F2?style=for-the-badge&logo=discord&logoColor=white
[discord-url]: https://discord.gg/hRNnVKhF2G
[cyanyt]: https://img.shields.io/badge/CyanVoxel's_YouTube_Channel-red?style=for-the-badge&logo=youtube&logoColor=white
[cyanyt-url]: https://youtube.com/@cyanvoxel


[contributors-shield]: https://img.shields.io/github/contributors/TagStudioDev/TagStudio.svg?style=for-the-badge
[contributors-url]: https://github.com/TagStudioDev/TagStudio/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/TagStudioDev/TagStudio.svg?style=for-the-badge
[forks-url]: https://github.com/TagStudioDev/TagStudio/network/members
[stars-shield]: https://img.shields.io/github/stars/TagStudioDev/TagStudio.svg?style=for-the-badge
[stars-url]: https://github.com/TagStudioDev/TagStudio/stargazers
[issues-shield]: https://img.shields.io/github/issues/TagStudioDev/TagStudio.svg?style=for-the-badge
[issues-url]: https://github.com/TagStudioDev/TagStudio/issues
[license-shield]: https://img.shields.io/github/license/TagStudioDev/TagStudio.svg?style=for-the-badge
[license-url]: https://github.com/TagStudioDev/TagStudio/blob/master/LICENSE.txt
[product-screenshot]: screenshot.jpg
[qt]: https://img.shields.io/badge/Qt_For_Python-000000?style=for-the-badge&logo=qt&logoColor=white
[qt-url]: https://doc.qt.io/qtforpython-6/
[python-url]: https://python.org/
[python]: https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=Python&logoColor=ffc331
[sqlite]: https://img.shields.io/badge/Sqlite-f2f2f2?style=for-the-badge&logo=sqlite&logoColor=003B57
[sqlite-url]: https://sqlite.org/
