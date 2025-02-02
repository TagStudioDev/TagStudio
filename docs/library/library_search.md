# Library Search

## Boolean Operators

TagStudio allows you to use common [boolean search](https://en.wikipedia.org/wiki/Full-text_search#Boolean_queries) operators when searching your library, along with [grouping](#grouping-and-nesting), [nesting](#grouping-and-nesting), and [character escaping](#escaping-characters). Note that you may need to use grouping in order to get the desired results you're looking for.

### AND

The `AND` operator will only return results that match **both** sides of the operator. `AND` is used implicitly when no boolean operators are given. To use the `AND` operator explicitly, simply type "and" (case insensitive) in-between items of your search.

> For example, searching for "Tag1 Tag2" will be treated the same as "Tag1 `AND` Tag2" and will only return results that contain both Tag1 and Tag2.

### OR

The `OR` operator will return results that match **either** the left or right side of the operator. To use the `OR` operator simply type "or" (case insensitive) in-between items of your search.

> For example, searching for "Tag1 `OR` Tag2" will return results that contain either "Tag1", "Tag2", or both.

### NOT

The `NOT` operator will returns results where the condition on the right is **false.** To use the `NOT` operator simply type "not" (case insensitive) in-between items of your search. You can also begin your search with `NOT` to only view results that do not contain the next term that follows.

> For example, searching for "Tag1 `NOT` Tag2" will only return results that contain "Tag1" while also not containing "Tag2".

### Grouping and Nesting

Searches can be grouped and nested by using parentheses to surround parts of your search query.

> For example, searching for "(Tag1 `OR` Tag2) `AND` Tag3" will return results any results that contain Tag3, plus one or the other (or both) of Tag1 and Tag2.

### Escaping Characters

Sometimes search queries have ambiguous characters and need to be "escaped". This is most common with tag names which contain spaces, or overlap with existing search keywords such as "[path:](#filename--filepath) of exile". To escape most search terms, surround the section of your search in plain quotes. Alternatively, spaces in tag names can be replaced by underscores.

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

### Filename + Filepath

Currently (v9.5.0-PR1) the filepath search uses [glob](<https://en.wikipedia.org/wiki/Glob_(programming)>) syntax, meaning you'll likely have to wrap your filename or partial filepath inside asterisks for results to appear. This search is also currently case sensitive. Use the `path:` keyword prefix followed by the filename or path, with asterisks surrounding partial names.

#### Examples

Given a file "artwork/piece.jpg", these searches will return results with it:

-   `path: artwork/piece.jpg` _(Note how no asterisks are required if the full path is given)_
-   `path: *piece.jpg*`
-   `path: *artwork*`
-   `path: *rtwor*`
-   `path: *ece.jpg*`
-   `path: *iec*`

And these (currently) won't:

-   `path: piece.jpg`
-   `path: piece.jpg`
-   `path: artwork`
-   `path: rtwor`
-   `path: ece.jpg`
-   `path: iec`

## Special Searches

"Special" searches use the `special:` keyword prefix and give quick results for certain special search queries.

### Untagged

To see all your file entries which don't contain any tags, use the `special:untagged` search.

### Empty

**_NOTE:_** _Currently unavailable in v9.5.0-PR1_

To see all your file entries which don't contain any tags _and_ any fields, use the `special:empty` search.
