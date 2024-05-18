# Welcome to the TagStudio Wiki!

> [!WARNING]
> This documentation is still a work in progress, and is intended to aide with deconstructing and understanding of the core mechanics of TagStudio and how it operates.

![Under Construction](https://i0.wp.com/www.bapl.org/wp-content/uploads/2019/02/old-under-construction-gif.gif)

## Table of Contents

- [Library](/doc/Library.md)
- [Fields](/doc/Field.md)
- [Entries](/doc/Entry.md)
- [Tags](/doc/Tag.md)


##### TODO

## Retrieving Entries based on Tag Cluster

By default when querying Entries, each Entry's `tags` list (stored in the form of Tag `id`s) is compared against the Tag `id`s in a given Tag cluster (list of Tag `id`s) or appended clusters in the case of multi-term queries. The type of comparison depends on the type of query and whether or not it is an inclusive or exclusive query, or a combination of both. This default searching behavior is done in _O(n)_ time, but can be sped up in the future by building indexes on certain search terms. These indexes can be stored on disk and loaded back into memory in future sessions. These indexes will also need to be updated as new Tags and Entries are added or edited.

## Missing File Resolution

1. Refresh missing file list (`refresh missing`) (Automatically run if library has few entries)
2. Fix missing files screen (`fix missing`)

### Fix Missing Files Screen

0. **Match Search** (Determines if entries can be fixed) Scans for filename in library directory
1. **Quick Fixes** (one match found, no existing entry)
2. **Match Selection** (multiple matches found)
3. **Merge Conflict Resolution** (match has existing entry)
   Any remaining missing files can be listed, but they probably really are missing at this point. You can update the path and filename to point to new files if you know where they should actually be pointing to.
