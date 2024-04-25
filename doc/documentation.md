# TagStudio Documentation (Alpha v9.1.0)

## _A User-Focused Document Management System_

> [!WARNING]
> This documentation is still a work in progress, and is intended to aide with deconstructing and understanding of the core mechanics of TagStudio and how it operates.

## Contents
- [Library](#library)
- [Fields](#fields)
- [Entries](#entries)
- [Tags](#tags)
- [Retrieving Entries](#retrieving-entries-based-on-tag-cluster)
- [Missing File Resolution](#missing-file-resolution)

## Library

The Library is how TagStudio represents your chosen directory. In this Library or Vault system, all files within this directory are represented by Entries, which then contain metadata Fields. All TagStudio data for a Library is stored within a `.TagStudio` folder at the root of the Library's directory. Internal Library objects include:

- Fields (v9+)
  - Text Line (Title, Author, Artist, URL)
  - Text Box (Description, Notes)
  - Tag Box (Tags, Content Tags, Meta Tags)
  - Datetime (Date Created, Date Modified, Date Taken) [WIP]
  - Collation (Collation) [WIP]
    - `name: str`: Collation Name
    - `page: int`: Page #
  - Checkbox (Archive, Favorite) [WIP]
  - Drop Down (Group of Tags to select one from) [WIP]
- Entries (v1+)
- Tags (v7+)
- Macros (v9/10+)

## Fields

Fields are the building blocks of metadata stored in Entires. Fields have several base types for representing different types of information, including:

- `text_line`
  - A string of text, displayed as a single line.
  - Useful for Titles, Authors, URLs, etc.
- `text_box`
  - A long string of text displayed as a box of text.
  - Useful for descriptions, notes, etc.
- `datetime` [WIP]
  - A date and time value.
- `tag_box`
  - A box of tags added by the user.
  - Multiple tag boxes can be used to separate classifications of tags, ex. 'Content Tags' and 'Meta Tags'.
- `checkbox` [WIP]
  - A two-state checkbox.
  - Can be associated with a tag for quick organization.
- `collation` [WIP]
  - A collation is a collection of files that are intended to be displayed and retrieved together. Examples may include pages of a book or document that are spread out across several individual files. If you're intention is to associate files across multiple 'collations', use Tags instead!

## Entries

Entries are the representations of your files within the Library. They consist of a reference to the file on your drive, as well as the metadata associated with it.

### Entry Object Structure (v9):

- `id`:
  - ID for the Entry.
    - Int, Unique, Required
    - Used for internal processing
- `filename`:
  - The filename with extension of the referenced media file.
    - String, Required
- `path`:
  - The folder path in which the media file is located in.
    - String, Required, OS Agnostic
- `fields`:
  - A list of Field ID/Value dicts.
    - List of dicts, Optional

NOTE: _Entries currently have several unused optional fields intended for later features._

## Tags

**Tags** are small data objects that represent an attribute of something. A person, place, thing, concept, you name it! Tags in TagStudio allow for more sophisticated Entry organization and searching thanks to their ability to contain alternate names and spellings via `aliases`, relational organization thanks to inherent `subtags`, and more! Tags can be as simple or as powerful as you want to make them, and TagStudio aims to provide as much power to you as possible.

### Tag Object Structure (v9):

- `id`:
  - ID for the Tag.
    - Int, Unique, Required
    - Used for internal processing
- `name`:
  - The normal name of the Tag, with no shortening or specification.
    - String, Required
    - Doesn't have to be unique
    - Each word analyzed individually
    - Used for display, searching, and storing
- `shorthand`:
  - The shorthand name for the Tag.
    - String, Optional
    - Doesn't have to be unique
    - Entire string analyzed as-is
    - Used for display and searching
- `aliases`:
  - Alternate names for the Tag.
    - List of Strings, Optional
    - Recommended to be unique to this Tag
    - Entire string analyzed as-is
    - Used for searching
- `subtags`:
  - Other Tags that make up properties of this Tag.
    - List of Strings, Optional
    - Used for display (first subtag only) and searching.
- `color`:
  - A hex code value for customizing the Tag's display color
    - String, Optional
    - Used for display

### Tag Examples:

#### League of Legends

- `name`: "League of Legends"
- `shorthand`: "LoL"
- `aliases`: ["League"]
- `subtags`: ["Game", "Fantasy"]

#### Arcane

- `name`: "Arcane"
- `shorthand`: ""
- `aliases`: []
- `subtags`: ["League of Legends", "Cartoon"]

#### Jinx (LoL)

- `name`: "Jinx Piltover"
- `shorthand`: "Jinx"
- `aliases`: ["Jinxy", "Jinxy Poo"]
- `subtags`: ["League of Legends", "Arcane", "Character"]

#### Zander (Arcane)

- `name`: "Zander Zanderson"
- `shorthand`: "Zander"
- `aliases`: []
- `subtags`: ["Arcane", "Character"]

#### Mr. Legend (LoL)

- `name`: "Mr. Legend"
- `shorthand`: ""
- `aliases`: []
- `subtags`: ["League of Legends", "Character"]

### Query "League of Legends" returns results for:

- League of Legends [because of "League of Legend"'s name]
- Arcane [because of "Arcane"'s subtag]
- Jinx (LoL) [because of "Jinx Piltover"'s subtag]
- Mr. Legend (LoL) [because of "Mr. Legned (LoL)'s subtag"]
- Zander (Arcane) [because of "Zander Zanderson"'s subtag ("Arcane")'s subtag]

### Query "LoL" returns results for:

- League of Legends [because of "League of Legend"'s shorthand]
- LoL [because of "League of Legend"'s shorthand]
- Arcane [because of "Arcane"'s subtag]
- Jinx (LoL) [because of "Jinx Piltover"'s subtag]
- Mr. Legend (LoL) [because of "Mr. Legned (LoL)'s subtag"]
- Zander (Arcane) [because of "Zander Zanderson"'s subtag ("Arcane")'s subtag]

### Query "Arcane" returns results for:

- Arcane [because of "Arcane"'s name]
- Jinx (LoL) [because of "Jinx Piltover"'s subtag "Arcane"]
- Zander (Arcane) [because of "Zander Zanderson"'s subtag]

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
