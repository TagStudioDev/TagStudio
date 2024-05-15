# TagStudio Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
