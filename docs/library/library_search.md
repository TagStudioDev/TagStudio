# Library Search

TagStudio provides various methods to search your library, ranging from TagStudio data such as tags to inherent file data such as paths or media types.

## Boolean Operators

TagStudio allows you to use common [boolean search](https://en.wikipedia.org/wiki/Full-text_search#Boolean_queries) operators when searching your library, along with [grouping](#grouping-and-nesting), [nesting](#grouping-and-nesting), and [character escaping](#escaping-characters). Note that you may need to use grouping in order to get the desired results you're looking for.

### AND

The `AND` operator will only return results that match **both** sides of the operator. `AND` is used implicitly when no boolean operators are given. To use the `AND` operator explicitly, simply type "and" (case insensitive) in-between items of your search.

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
    Searching for "(Tag1 `OR` Tag2) `AND` Tag3" will return results any results that contain Tag3, plus one or the other (or both) of Tag1 and Tag2.

### Escaping Characters

Sometimes search queries have ambiguous characters and need to be "escaped". This is most common with tag names which contain spaces, or overlap with existing search keywords such as "[path:](#filename-and-path) of exile". To escape most search terms, surround the section of your search in plain quotes. Alternatively, spaces in tag names can be replaced by underscores.

#### Valid Escaped Tag Searches

-   "Tag Name With Spaces"
-   Tag_Name_With_Spaces

#### Invalid Escaped Tag Searches

-   Tag Name With Spaces
    -   Reason: Ambiguity between a tag named "Tag Name With Spaces" and four individual tags called "Tag", "Name", "With", "Spaces".

## Tags

[Tag](#tags) search is the default mode of file entry search in TagStudio. No keyword prefix is required, however using `tag:` will also work. The tag search attempts to match tag [names](tag.md#name), [shorthands](tag.md#shorthand), [aliases](tag.md#aliases), as well as allows for tags to [substitute](tag.md#intuition-via-substitution) in for any of their [parent tags](tag.md#parent-tags).

You may also see the `tag_id:` prefix keyword show up with using the right-click "Search for Tag" option on tags. This is meant for internal use, and eventually will not be displayed or accessible to the user.

## Fields

_[Field](field.md) search is currently not in the program, however is coming in a future version._

## File Entry Search

### Filename and Path

Filename and path search is available via the `path:` keyword and comes in a few different styles. By default, any string that follows the `path:` keyword will be searched as a substring inside a file's complete filepath. This means that given a file `folder/my_file.txt`, searching for `path: my_file` or `path: folder` will both return results for that file.

#### Case Sensitivity

TagStudio uses a "[smartcase](https://neovim.io/doc/user/options.html#'smartcase')"-like system for case sensitivity. This means that a search term typed in `lowercase` will be treated as **case-insensitive**, while a term typed in any `MixedCase` will be treated as **case-sensitive**. This makes it quicker to type searches when case sensitivity isn't required, while also providing a simple option to leverage case sensitivity when desired. Note that this means there's technically no way to currently search for a lowercase term while respecting case sensitivity.

#### Glob Syntax

Optionally, you may use [glob](<https://en.wikipedia.org/wiki/Glob_(programming)>) syntax to search filepaths.

#### Examples

Given a file "Artwork/Piece.jpg", the following searches will return results for it:

-   `path: artwork/piece.jpg`
-   `path: Artwork/Piece.jpg`
-   `path: piece.jpg`
-   `path: Piece.jpg`
-   `path: artwork`
-   `path: rtwor`
-   `path: ece.jpg`
-   `path: iec`
-   `path: artwork/*`
-   `path: Artwork/*`
-   `path: *piece.jpg*`
-   `path: *Piece.jpg*`
-   `path: *artwork*`
-   `path: *Artwork*`
-   `path: *rtwor*`
-   `path: *ece.jpg*`
-   `path: *iec*`
-   `path: *.jpg`

While the following searches will **NOT:**

-   `path: ARTWORK/Piece.jpg` _(Reason: Mismatched case)_
-   `path: *aRtWoRk/Piece*` _(Reason: Mismatched case)_
-   `path: PieCe.jpg` _(Reason: Mismatched case)_
-   `path: *PieCe.jpg*` _(Reason: Mismatched case)_

## Special Searches

Some predefined searches use the `special:` keyword prefix and give quick results for certain special search queries.

### Untagged

To see all your file entries which don't contain any tags, use the `special: untagged` search.

### Empty

**_NOTE:_** _Currently unavailable in v9.5.0_

To see all your file entries which don't contain any tags _and_ any fields, use the `special: empty` search.
