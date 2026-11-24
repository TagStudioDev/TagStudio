---
title: Searching
icon: material/magnify
---

<!-- SPDX-FileCopyrightText: (c) TagStudio Contributors -->
<!-- SPDX-License-Identifier: GPL-3.0-only -->

<!-- prettier-ignore -->
!!! info "Upcoming Search Bar Rework"
    The search bar interface will receive a major overhaul in the near future, which will hide the complex syntax used by some queries behind a more approachable interface.

# :material-magnify: Searching

TagStudio provides various methods to search your library, ranging from TagStudio data such as tags to inherent file data such as paths or media types.

## Boolean Operators

TagStudio allows you to use common [Boolean search](https://en.wikipedia.org/wiki/Full-text_search#Boolean_queries) operators when searching your library, along with [grouping](#grouping-and-nesting), [nesting](#grouping-and-nesting), and [character escaping](#escaping-characters). Note that you may need to use grouping in order to get the desired results you're looking for.

### AND

The `AND` operator will only return results that match **both** sides of the operator. `AND` is used implicitly when no Boolean operators are given. To use the `AND` operator explicitly, simply type "and" (case insensitive) in-between items of your search.

<!-- prettier-ignore -->
!!! example
    Searching for "Tag1 Tag2" will be treated the same as "Tag1 `AND` Tag2" and will only return results that contain both Tag1 and Tag2.

### OR

The `OR` operator will return results that match **either** the left or right side of the operator. To use the `OR` operator simply type "or" (case insensitive) in-between items of your search.

<!-- prettier-ignore -->
!!! example
    Searching for "Tag1 `OR` Tag2" will return results that contain either "Tag1", "Tag2", or both.

### NOT

The `NOT` operator will returns results where the condition on the right is **false.** To use the `NOT` operator simply type "not" (case insensitive) in-between items of your search. You can also begin your search with `NOT` to only view results that do not contain the next term that follows.

<!-- prettier-ignore -->
!!! example
    Searching for "Tag1 `NOT` Tag2" will only return results that contain "Tag1" while also not containing "Tag2".

### Grouping and Nesting

Searches can be grouped and nested by using parentheses to surround parts of your search query.

<!-- prettier-ignore -->
!!! example
    Searching for "(Tag1 `OR` Tag2) `AND` Tag3" will return any results that contain Tag3, plus one or the other (or both) of Tag1 and Tag2.

### Escaping Characters

Sometimes search queries have ambiguous characters and need to be "escaped". This is most common with tag names which contain spaces, or overlap with existing search keywords such as "[path:](#filename-and-path) of exile". To escape most search terms, surround the section of your search in plain quotes. Alternatively, spaces in tag names can be replaced by underscores.

#### Valid Escaped Tag Searches

- "Tag Name With Spaces"
- Tag_Name_With_Spaces

#### Invalid Escaped Tag Searches

- Tag Name With Spaces
    - Reason: Ambiguity between a tag named "Tag Name With Spaces" and four individual tags called "Tag", "Name", "With", "Spaces".

---

## Tags

[Tag](#tags) search is the default mode of file entry search in TagStudio. No keyword prefix is required, however using `tag:` will also work. The tag search attempts to match tag [names](tags.md#name), [shorthands](tags.md#shorthand), [aliases](tags.md#aliases), as well as allows for tags to [substitute](tags.md#intuition-via-substitution) in for any of their [parent tags](tags.md#parent-tags).

You may also see the `tag_id:` prefix keyword show up when using the right-click "Search for Tag" option on tags. This is meant for internal use, and eventually will not be displayed or accessible to the user.

---

## Fields

[Fields](fields.md) are searchable using the `field:` keyword, which searches the contents of every [text](fields.md#text) and [datetime](fields.md#datetime) field across entries. For example, `field: holmes` will return results for any entries with any text fields containing the text "holmes" (not the field name itself). Searches that include spaces need to be escaped using quotes, for example `field: "sherlock holmes"`. Field searches are case-insensitive and match any part of a field's contents.

To search for fields that have a specific name, add the name in square brackets after the search term. For example, `field: holmes[name=title]` only searches fields named "Title". Field names are case-insensitive, and names containing spaces need to be surrounded in quotes, such as `field: holmes[name="series title"]`.

### Dates

Datetime fields are currently searchable using the `YYYY-MM-DD HH:MM:SS` format (regardless of the date format set in your settings). For example, given a "Date Taken" field:

- `field: 2024[name="date taken"]` returns dates in 2024
- `field: 2024-05[name="date taken"]` returns dates in May 2024
- `field: 2024-05-01[name="date taken"]` returns dates on May 1st, 2024

---

## File Entry Search

### Filename and Path

Filename and path search is available via the `path:` keyword and comes in a few different styles. By default, any string that follows the `path:` keyword will be searched as a substring inside a file's complete filepath. This means that given a file `folder/my_file.txt`, searching for `path: my_file` or `path: folder` will both return results for that file.

#### Case Sensitivity

TagStudio uses a "[smartcase](https://neovim.io/doc/user/options.html#'smartcase')"-like system for case sensitivity. This means that a search term typed in `lowercase` will be treated as **case-insensitive**, while a term typed in any `MixedCase` will be treated as **case-sensitive**. This makes it quicker to type searches when case sensitivity isn't required, while also providing a simple option to leverage case sensitivity when desired. Note that this means there's technically no way to currently search for a lowercase term while respecting case sensitivity.

#### Glob Syntax

Optionally, you may use [glob](<https://en.wikipedia.org/wiki/Glob_(programming)>) syntax to search filepaths.

#### Examples

Given a file "Artwork/Piece.jpg", the following searches will return results for it:

- `path: artwork/piece.jpg`
- `path: Artwork/Piece.jpg`
- `path: piece.jpg`
- `path: Piece.jpg`
- `path: artwork`
- `path: rtwor`
- `path: ece.jpg`
- `path: iec`
- `path: artwork/*`
- `path: Artwork/*`
- `path: *piece.jpg*`
- `path: *Piece.jpg*`
- `path: *artwork*`
- `path: *Artwork*`
- `path: *rtwor*`
- `path: *ece.jpg*`
- `path: *iec*`
- `path: *.jpg`

While the following searches will **NOT:**

- `path: ARTWORK/Piece.jpg` _(Reason: Mismatched case)_
- `path: *aRtWoRk/Piece*` _(Reason: Mismatched case)_
- `path: PieCe.jpg` _(Reason: Mismatched case)_
- `path: *PieCe.jpg*` _(Reason: Mismatched case)_

---

### File Types

File types/extensions can be searched for using the `filetype:` keyword, which returns file entries with a specific file extension. The search is case-insensitive, and a leading dot for the extension is optional. For example, `filetype: png`, `filetype: .png`, and `filetype: PNG` will all return the same results.

Some extensions are treated as equivalent, so searching for one also returns the others. For example, `filetype: jpg` also returns ".jpeg" and ".jfif" files, and vice versa.

Multi-part extensions such as ".tar.gz" can be searched in full or by their first part. `filetype: tar.gz` only returns ".tar.gz" files, while `filetype: tar` returns ".tar" files along with ".tar.gz", ".tar.xz", and other compressed tar files.

---

### Media Types

You can search for broad media types that can consist of multiple file extensions by using the `mediatype:` keyword, such as `mediatype: image` or `mediatype: video`. Media type names are case-insensitive, and names containing spaces need to be surrounded in quotes, for example `mediatype: "raw image"`.

Many media types have several aliases that can be used interchangeably, such as "Adobe Photoshop"/"Photoshop", "Microsoft Word"/"Word", or "Microsoft Office"/"MS Office"/"Office 365" _("Office" by itself is a broader group that can include non-Microsoft files)_.

Some common media types include:

| Media Type        | Included Extensions                                                                               |
| ----------------- | ------------------------------------------------------------------------------------------------- |
| 3D Model          | `.3ds`, `.3mf`, `.fbx`, `.obj`, `.stl`                                                            |
| Archive           | `.7z`, `.rar`, `.tar`, `.tar.gz`, `.zip`, and more                                                |
| Audio             | `.aac`, `.aiff`, `.flac`, `.m4a`, `.mid`, `.mp3`, `.ogg`, `.wav`, `.wma`, and more                |
| Blender           | `.blend`, `.blend1` through `.blend32`, `.blen_tc`                                                |
| Clip Studio Paint | `.clip`, `.cmc`, `.lip`                                                                           |
| Font              | `.fon`, `.otf`, `.ttc`, `.ttf`, `.woff`, `.woff2`                                                 |
| Krita             | `.kra`, `.krz`, `.ora`                                                                            |
| Paint.NET         | `.pdn`                                                                                            |
| Program           | `.apk`, `.apkm`, `.apks`, `.app`, `.appx`, `.bin`, `.exe`, `.msi`, `.msix`, `.pkg`, `.xapk`       |
| Python            | `.ipynb`, `.py`, `.pyc`, `.pyd`, `.pyi`, `.pyo`, `.sip`                                           |
| Plaintext         | `.cfg`, `.css`, `.html`, `.ini`, `.js`, `.json`, `.log`, `.md`, `.txt`, `.xml`, `.yaml`, and more |
| Video             | `.3gp`, `.avi`, `.flv`, `.gifv`, `.hevc`, `.m4v`, `.mkv`, `.mov`, `.mp4`, `.webm`, `.wmv`         |

Some media types are groups that also include other media types and/or groups:

| Media Type   | Includes                                                                                                 |
| ------------ | -------------------------------------------------------------------------------------------------------- |
| Archive      | Comic Book Archive, RAR Archive, tar Archive, Zip Archive                                                |
| Document     | Adobe Acrobat, Apple Pages, LaTeX, Microsoft Word, OpenDocument text files, Typesetting, Typst           |
| eBook        | Apple Books, Comic Book Archive                                                                          |
| Image        | Animated Image, Icon, Raster Image, Raw Image, Vector Image                                              |
| Raster Image | Animated Image, Icon, Raw Image                                                                          |
| Office       | Adobe Acrobat, iWork, Microsoft Office, OpenDocument                                                     |
| Plaintext    | C, C#, C++, CSS, HTML, JavaScript, JSON, Lua, Markdown, PHP, Rust, TOML, TypeScript, XML, YAML, and more |
| Presentation | Apple Keynote, Microsoft PowerPoint, OpenDocument presentations                                          |
| Spreadsheet  | Apple Numbers, Microsoft Excel, OpenDocument spreadsheets                                                |
| Typesetting  | LaTeX, Typst                                                                                             |

Media types also exist for many programs and their file formats, such as Photoshop (`mediatype: photoshop`), Microsoft Office (`mediatype: "microsoft office"`), or Blender (`mediatype: blender`). Some common ones include:

| Media Type       | Includes                                                                       |
| ---------------- | ------------------------------------------------------------------------------ |
| Adobe            | Adobe Acrobat, Adobe Illustrator, Adobe Photoshop                              |
| Affinity         | Affinity Designer, Affinity Photo, Affinity Publisher                          |
| Apple            | Apple Books, Apple Creator Studio, Apple Pixelmator Pro, iWork                 |
| iWork            | Apple Keynote, Apple Numbers, Apple Pages                                      |
| Microsoft Office | Microsoft Access, Microsoft Excel, Microsoft PowerPoint, Microsoft Word        |
| OpenDocument     | OpenDocument presentations, OpenDocument spreadsheets, OpenDocument text files |

---

## Special Searches

Some predefined searches use the `special:` keyword prefix and give quick results for certain special search queries.

### Untagged

To see all your file entries which don't contain any tags, use the `special: untagged` search.

### Empty

**_NOTE:_** _Currently unavailable in v9.5.0_

To see all your file entries which don't contain any tags _and_ any fields, use the `special: empty` search.
