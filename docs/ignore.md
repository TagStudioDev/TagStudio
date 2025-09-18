---
title: Ignoring Files
icon: material/file-document-remove
---

# :material-file-document-remove: Ignoring Files & Directories

<!-- prettier-ignore -->
!!! warning "Legacy File Extension Ignoring"
    TagStudio versions prior to v9.5.4 use a different, more limited method to exclude or include file extensions from your library and subsequent searches. Opening a pre-exiting library in v9.5.4 or later will non-destructively convert this to the newer, more extensive `.ts_ignore` format.

    If you're still running an older version of TagStudio in the meantime, you can access the legacy system by going to "Edit -> Manage File Extensions" in the menubar.

TagStudio offers the ability to ignore specific files and directories via a `.ts_ignore` file located inside your [library's](libraries.md) `.TagStudio` folder. This file is designed to use very similar [glob](<https://en.wikipedia.org/wiki/Glob_(programming)>)-style pattern matching as the [`.gitignore`](https://git-scm.com/docs/gitignore) file used by Git™[^1]. It can be edited within TagStudio or opened to edit with an external program by going to the "Edit -> Ignore Files" option in the menubar.

This file is only referenced when scanning directories for new files to add to your library, and does not apply to files that have already been added to your library.

<!-- prettier-ignore -->
!!! tip
    If you just want some specific examples of how to achieve common tasks with the ignore patterns (e.g. ignoring a single file type, ignoring a specific folder) then jump to the "[Use Cases](#use-cases)" section!

<!-- prettier-ignore-start -->
=== "Example .ts_ignore file"
```toml title="My Library/.TagStudio/.ts_ignore"
# TagStudio .ts_ignore file.

# Code
__pycache__
.pytest_cache
.venv
.vs

# Projects
Minecraft/**/Metadata
Minecraft/Website
!Minecraft/Website/*.png
!Minecraft/Website/*.css

# Documents
*.doc
*.docx
*.ppt
*.pptx
*.xls
*.xlsx
```
<!-- prettier-ignore-end -->

## Pattern Format

<!-- prettier-ignore -->
!!! note ""
    _This section sourced and adapted from Git's[^1] `.gitignore` [documentation](https://git-scm.com/docs/gitignore)._

### Internal Processes

When scanning your library directories, the `.ts_ignore` file is read by either the [`wcmatch`](https://facelessuser.github.io/wcmatch/glob/) library or [`ripgrep`](https://github.com/BurntSushi/ripgrep) in glob mode depending if you have the later installed on your system and it's detected by TagStudio. Ripgrep is the preferred method for scanning directories due to its improved performance and identical pattern matching to `.gitignore`. This mixture of tools may lead to slight inconsistencies if not using `ripgrep`.

---

### Comments ( `#` )

A `#` symbol at the start of a line indicates that this line is a comment, and match no items. Blank lines are used to enhance readability and also match no items.

-   Can be escaped by putting a backslash ("`\`") in front of the `#` symbol.

<!-- prettier-ignore-start -->
=== "Example comment"
    ```toml
    # This is a comment! I can say whatever I want on this line.
    file_that_is_being_matched.txt

    # file_that_is_NOT_being_matched.png
    file_that_is_being_matched.png
    ```
=== "Organizing with comments"
    ```toml
    # TagStudio .ts_ignore file.

    # Minecraft Stuff
    Minecraft/**/Metadata
    Minecraft/Website
    !Minecraft/Website/*.png
    !Minecraft/Website/*.css

    # Microsoft Office
    *.doc
    *.docx
    *.ppt
    *.pptx
    *.xls
    *.xlsx
    ```
=== "Escape a # symbol"
    ```toml
    # To ensure a file named '#hashtag.jpg' is ignored:
    \#hashtag.jpg
    ```
<!-- prettier-ignore-end -->

---

### Directories ( `/` )

The forward slash "`/`" is used as the directory separator. Separators may occur at the beginning, middle or end of the `.ts_ignore` search pattern.

-   If there is a separator at the beginning or middle (or both) of the pattern, then the pattern is relative to the directory level of the particular `.TagStudio` library folder itself. Otherwise the pattern may also match at any level below the `.TagStudio` folder level.

-   If there is a separator at the end of the pattern then the pattern will only match directories, otherwise the pattern can match both files and directories.

<!-- prettier-ignore-start -->
=== "Example folder pattern"
    ```toml
    # Matches "frotz" and "a/frotz" if they are directories.
    frotz/
    ```
=== "Example nested folder pattern"
    ```toml
    # Matches "doc/frotz" but not "a/doc/frotz".
    doc/frotz/
    ```
<!-- prettier-ignore-end -->

---

### Negation ( `!` )

A `!` prefix before a pattern negates the pattern, allowing any files matched matched by previous patterns to be un-matched.

-   Any matching file excluded by a previous pattern will become included again.
-   **It is not possible to re-include a file if a parent directory of that file is excluded.**

<!-- prettier-ignore-start -->
=== "Example negation"
    ```toml
    # All .jpg files will be ignored, except any located in the 'Photos' folder.
    *.jpg
    Photos/!*.jpg
    ```
=== "Escape a ! Symbol"
    ```toml
    # To ensure a file named '!wowee.jpg' is ignored:
    \!wowee.jpg
    ```
<!-- prettier-ignore-end -->

---

### Wildcards

#### Single Asterisks ( `*` )

An asterisk "`*`" matches anything except a slash.

<!-- prettier-ignore-start -->
=== "File examples"
    ```toml
    # Matches all .png files in the "Images" folder.
    Images/*.png

    # Matches all .png files in all folders
    *.png
    ```
=== "Folder examples"
    ```toml
    # Matches any files or folders directly in "Images/" but not deeper levels.
    #   Matches file "Images/mario.jpg"
    #   Matches folder "Images/Mario"
    #   Does not match file "Images/Mario/cat.jpg"
    Images/*
    ```
<!-- prettier-ignore-end -->

#### Question Marks ( `?` )

The character "`?`" matches any one character except "`/`".

<!-- prettier-ignore-start -->
=== "File examples"
    ```toml
    # Matches any .png file starting with "IMG_" and ending in any four characters.
    #   Matches "IMG_0001.png"
    #   Matches "Photos/IMG_1234.png"
    #   Does not match "IMG_1.png"
    IMG_????.png

    # Same as above, except matches any file extension instead of only .png
    IMG_????.*
    ```
=== "Folder examples"
    ```toml
    # Matches all files in any direct subfolder of "Photos" beginning in "20".
    #   Matches "Photos/2000"
    #   Matches "Photos/2024"
    #   Matches "Photos/2099"
    #   Does not match "Photos/1995"
    Photos/20??/
    ```
<!-- prettier-ignore-end -->

#### Double Asterisks ( `**` )

Two consecutive asterisks ("`**`") in patterns matched against full pathname may have special meaning:

-   A leading "`**`" followed by a slash means matches in all directories.
-   A trailing "`/**`" matches everything inside.
-   A slash followed by two consecutive asterisks then a slash ("`/**/`") matches zero or more directories.
-   Other consecutive asterisks are considered regular asterisks and will match according to the previous rules.

<!-- prettier-ignore-start -->
=== "Leading **"
    ```toml
    # Both match file or directory "foo" anywhere
    **/foo
    foo

    # Matches file or directory "bar" anywhere that is directly under directory "foo"
    **/foo/bar
    ```
=== "Trailing /**"
    ```toml
    # Matches all files inside directory "abc" with infinite depth.
    abc/**
    ```
=== "Middle /**/"
    ```toml
    # Matches "a/b", "a/x/b", "a/x/y/b" and so on.
    a/**/b
    ```
<!-- prettier-ignore-end -->

#### Square Brackets ( `[a-Z]` )

Character sets and ranges are specific and powerful forms of wildcards that use characters inside of brackets (`[]`) to leverage very specific matching. The range notation, e.g. `[a-zA-Z]`, can be used to match one of the characters in a range.

<!-- prettier-ignore -->
!!! tip
    For more in-depth examples and explanations on how to use ranges, please reference the [`glob`](https://man7.org/linux/man-pages/man7/glob.7.html) man page.

<!-- prettier-ignore-start -->
=== "Range examples"
    ```toml
    # Matches all files that start with "IMG_" and end in a single numeric character.
        # Matches "IMG_0.jpg", "IMG_7.png"
        # Does not match "IMG_10.jpg", "IMG_A.jpg"
    IMG_[0-9]

    # Matches all files that start with "IMG_" and end in a single alphabetic character
    IMG_[a-z]
    ```
=== "Set examples"
    ```toml
    # Matches all files that start with "IMG_" and in any character in the set.
        # Matches "draft_a.docx", "draft_b.docx", "draft_c.docx"
        # Does not match "draft_d.docx"
    draft_[abc]

    # Matches all files that start with "IMG_" and end in a single alphabetic character
    IMG_[a-z]
    ```
<!-- prettier-ignore-end -->

---

## Use Cases

### Ignoring Files by Extension

<!-- prettier-ignore -->
=== "Ignore all .jpg files"
    ```toml
    *.jpg
    ```
=== "Ignore all files EXCEPT .jpg files"
    ```toml
    *
    !*.jpg
    ```
=== "Ignore all .jpg files in specific folders"
    ```toml
    ./Photos/Worst Vacation/*.jpg
    Music/Artwork Art/*.jpg
    ```

<!-- prettier-ignore -->
!!! tip "Ensuring Complete Extension Matches"
    For some filetypes, it may be nessisary to specify different casing and alternative spellings in order to match with all possible variations of an extension in your library.

    ```toml title="Ignore (Most) Possible JPEG File Extensions"
    # The JPEG Cinematic Universe
    *.jpg
    *.jpeg
    *.jfif
    *.jpeg_large
    *.JPG
    *.JPEG
    *.JFIF
    *.JPEG_LARGE
    ```

### Ignoring a Folder

<!-- prettier-ignore -->
=== "Ignore all "Cache" folders"
    ```toml
    # Matches any folder called "Cache" no matter where it is in your library.
    cache/
    ```
=== "Ignore a "Downloads" folder"
    ```toml
    # "Downloads" must be a folder on the same level as your ".TagStudio" folder.
    #   Does not match with folders name "Downloads" elsewhere in your library
    #   Does not match with a file called "Downloads"
    /Downloads/
    ```
=== "Ignore .jpg files in specific folders"
    ```toml
    Photos/Worst Vacation/*.jpg
    /Music/Artwork Art/*.jpg
    ```

[^1]: The term "Git" is a licensed trademark of "The Git Project", a member of the Software Freedom Conservancy. Git is released under the [GNU General Public License version 2.0](https://opensource.org/license/GPL-2.0), an open source license. TagStudio is not associated with the Git Project, only including systems based on some therein.
