# TagStudio Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [9.4.1] - 2024-09-14

### Added

- Warn user if FFmpeg is not installed
- Support for `.raf` and `.orf` raw image thumbnails and previews

### Fixed

- Use `birthtime` for file creation time on Mac & Windows
- Use audio icon fallback when FFmpeg is not detected
- Retain search query upon directory refresh

### Changed

- Significantly improve file re-scanning performance

## [9.4.0] - 2024-09-04

### Added

- Copy and paste fields
- Add multiple fields at once
- Drag and drop files in/out of the program
  - Files can be shared by dragging them from the thumbnail grid to other programs
  - Files can be added to library folder by dragging them into the program
- Manage Python virtual environment in Nix flake
- Ability to create tag when adding tags
- Blender preview thumbnail support
- File deletion/trashing
  - Added right-click option on thumbnails and preview panel to delete files
  - Added Edit Menu option for deleting files
  - Added <kbd>Delete</kbd> key shortcut for deleting files
- Font preview thumbnail support
  - Short "Aa" previews for thumbnails
  - Full alphabet preview for the preview pane
- Sort tags by alphabetical/color
- File explorer action follows OS naming
- Preview Source Engine files
- Expanded thumbnail and preview features
  - Add album cover art thumbnails
  - Add audio waveform thumbnails for audio files without embedded cover art
  - Add new default file thumbnails, both for generic and specific file types
  - Change the unlinked file icon to better convey its meaning
  - Add dropdown for different thumbnail sizes
- Show File Creation and Modified dates; Restyle file path label

### Fixed

- Backslashes in f-string on file dupe widget
- Tags not shown when none searched
- Avoid error from eagerly grabbing data values
- Correct behavior for tag search options
- Load Gallery-DL sidecar files correctly
- Correct duplicate file matching
- GPU hardware acceleration in Nix flake
- Suppress command prompt windows for FFmpeg in builds

### Internal Changes

- Move type constants to media classes
- Combine open launch arguments
- Revamp Nix flake with devenv/direnv in cb4798b
- Remove impurity of Nix flake when used with direnv in bc38e56

## [9.3.2] - 2024-07-19

### Fixed

- Fix signal log warning
- Fix "Folders to Tags" feature
- Fix search ignoring case of extension list

### Internal Changes

- Add tests into CI by
- Create testing library files ad-hoc
- Refactoring: centralize field IDs
- Update to pyside6 version 6.7.1

## [9.3.1] - 2024-06-13

### Fixed

- Separately pin QT nixpkg version
- Bugfix for #252, don't attempt to read video file if invalid or 0 frames long
- Toggle Mouse Event Transparency on ItemThumbs
- Refactor `video_player.py`

## [9.3.0] - 2024-06-09

### Added

- Added playback previews for video files
- Added Boolean "and/or" search mode selection
- Added ability to scan and fix duplicate entries (not to be confused with duplicate files) from the "Fix Unlinked Entries" menu
- Added “Select All” (<kbd>Ctrl</kbd>+<kbd>A</kbd> / <kbd>⌘ Command</kbd>+<kbd>A</kbd>) hotkey for the library grid view
- Added "Clear Selection" hotkey (<kbd>Esc</kbd>) for the library grid view
- Added the ability to invert the file extension inclusion list into an exclusion list
- Added default landing page when no library is open

### Fixed

- TagStudio will no longer attempt to or allow you to reopen a library from a missing location
- Fixed `PermissionError` when attempting to access files with a higher permission level upon scanning the library directory
- Fixed RAW image previews sometimes not loadingand
- Fixed most non-UTF-8 encoded text files from not being able to be previewed
- Fixed "Refresh Directories"/"Fix Unlinked Entries" creating duplicate entries
- Other miscellaneous fixes

### Changed

- Renamed "Subtags" to "Parent Tags" to help better describe their function
- Increased number of tags shown by default in the "Add Tag" modal from 29 to 100
- Documentation is now split into individual linked files and updated to include future features
- Replaced use of `os.path` with `pathlib`
- `.cr2` files are now included in the list of RAW image file types
- Minimum supported macOS version raised to 12.0

## [9.2.1] - 2024-05-23

### Added

- Basic thumbnail/preview support for RAW images (currently `.raw`, `.dng`, `.rw2`, `.nef`, `.arw`, `.crw`, `.cr3`)
  - NOTE: These previews are currently slow to load given the nature of rendering them. In the future once thumbnail caching is added, this process should only happen once.
- Thumbnail/preview support for HEIF images

### Fixed

- Fixed sidebar not expanding horizontally
- Fixed "Recent Library" list not updating when creating a new library
- Fixed palletized images not loading with alpha channels
- Low resolution images (such as pixel art) now render with crisp edges in thumbnails and previews
- Fixed visual bug where the edit icon would show for incorrect fields

## [9.2.0] - 2024-05-14

### Added

- Full macOS and Linux support
- Ability to apply tags to multiple selections at once
- Right-click context menu for opening files or their locations
- Support for all filetypes inside of the library
- Configurable filetype blacklist
- Option to automatically open last used library on startup
- Tool to convert folder structure to tag tree
- SIGTERM handling in console window
- Keyboard shortcuts for basic functions
- Basic support for plaintext thumbnails
- Default icon for files with no thumbnail support
- Menu action to close library
- All tags now show in the "Add Tag" panel by default
- Modal view to view and manage all library tags
- Build scripts for Windows and macOS
- Help menu option to visit the GitHub repository
- Toggleable "Recent Libraries" list in the entry side panel

### Fixed

- Fixed errors when performing actions with no library open
- Fixed bug where built-in tags were duplicated upon saving
- QThreads are now properly terminated on application exit
- Images with rotational EXIF data are now properly displayed
- Fixed "truncated" images causing errors
- Fixed images with large resolutions causing errors

### Changed

- Updated minimum Python version to 3.12
- Various UI improvements
  - Improved legibility of the Light Theme (still a WIP)
  - Updated Dark Theme
  - Added hand cursor to several clickable elements
- Fixed network paths not being able to load
- Various code cleanup and refactoring
- New application icons

### Known Issues

- Using and editing multiple entry fields of the same type may result in incorrect field(s) being updated
- Adding Favorite or Archived tags via the thumbnail badges may apply the tag(s) to incorrect fields
- Searching for tag names with spaces does not currently function as intended
	- A temporary workaround it to omit spaces in tag names when  searching
- Sorting fields using the "Sort Fields" macro may result in edit icons being shown for incorrect fields

## [9.1.0] - 2024-04-22

### Added

- Initial public release
