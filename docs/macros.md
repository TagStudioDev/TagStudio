---
icon: material/script-text
---

# :material-script-text: Macros

TagStudio features a configurable macro system which allows you to set up automatic or manually triggered actions to perform a wide array of operations on your [library](libraries.md). Each macro is stored in an individual script file and is created using [TOML](https://toml.io/en/) with a predefined schema described below. Macro files are stored in your library's "`.TagStudio/macros`" folder.

## Schema Version

The `schema_version` key declares which version of the macro schema is currently being used. Current schema version: 1.

```toml
schema_version = 1
```

## Triggers

The `triggers` key declares when a macro may be automatically ran. Macros can still be manually triggered even if they have automatic triggers defined.

-   `on_open`: Run when the TagStudio library is opened.
-   `on_refresh`: Run when the TagStudio library's directories have been refreshed.
-   `on_new_entry`: Run a new [file entry](entries.md) that has been created.

```toml
triggers = ["on_new_entry"]
```

## Actions

Actions are the general task that a macro will perform. They are represented by TOML tables and must have a unique name in your macro file, but the name itself has no importance to the macro. The root table will contain general configuration info about your action, and nested tables (e.g. `[action.task]`) will further define the specifics of your action.

```toml
[newgrounds]
```

Action tables must have an `action` key with one of the following values:

-   [`import_data`](#import-data): Import data from a supported external source.
-   [`add_data`](#add-data): Add data declared inside the macro file.

```toml
[newgrounds]
action = "import_data"
```

### Add Data

The `add_data` action lets you add data to a [file entry](entries.md) given one or more conditional statements. Unlike the [`import_data`](#import-data) action, the `add_data` action adds data declared in the macro itself rather than importing it form a source external to the macro.

### Import Data

The `import_data` action allows you to import external data into your TagStudio library in the form of [tags](tags.md) and [fields](fields.md). While some sources need explicit support (e.g. ID3, EXIF) generic sources such as JSON sidecar files can leverage wide array of data shaping options that allow the underlying data structure to be abstracted from TagStudio's internal data structures. This macro pairs very well with tools such as [gallery-dl](https://github.com/mikf/gallery-dl).

If you're importing from an object or table-like source (i.e. JSON), you'll need to create a nested table with the name format of "`[action.task]`" and provide a [`key`](#key) field filled with the name of the targeted source key. In this case the "task" name does not matter as long as it doesn't conflict with one of the built-in names (i.e. "`map`", "`template`, "`inverse_map`").

<!-- prettier-ignore -->
=== "Importable JSON Data"
    ```json
    {
        "newgrounds": {
            "tags": ["tag1", "tag2"]
        }
    }
    ```
=== "TOML Macro"
    ```toml
    [newgrounds]
    action="import_data"
    [newgrounds.tags]
    key="tags"
    ```

Inside the new table we can now declare additional information about the native data formats and how they should be imported into TagStudio.

### Action Configuration

#### Key

The `key` key is used in conjunction with the [`import_data`](#import-data) action to specify the object/table key to target in your import data. If you're targeting a nested object, separate the names of the keys with a dot.

```toml
[artstation]
action = "import_data"
source_format = "json"
[artstation.tags]
key="tags"
ts_type = "tags"
[artstation.mediums]
key="mediums.name" # Nested key
ts_type = "tags"
```

When importing from the same key multiple times, you have the option to either choose different names for your "task" tables or use the same name with these tables wrapped in an extra pair of brackets.

<!-- prettier-ignore -->
=== "Single Import"
    ```toml
    [newgrounds]
    # Newgrounds table info here
    [newgrounds.artist]
    key="artist"
    ts_type = "tags"
    use_context = false
    on_missing = "create"
    ```
=== "Multiple Imports"
    ```toml
    [newgrounds]
    # Newgrounds table info here
    [newgrounds.artist_tag]
    key="artist"
    ts_type = "tags"
    use_context = false
    on_missing = "skip"
    [newgrounds.artist_text]
    key="artist"
    ts_type = "text_line"
    name = "Artist"
    ```
=== "Multiple Imports (Wrapped)"
    ```toml
    [newgrounds]
    # Newgrounds table info here
    [[newgrounds.artist]]
    key="artist"
    ts_type = "tags"
    use_context = false
    on_missing = "skip"
    [[newgrounds.artist]]
    key="artist"
    ts_type = "text_line"
    name = "Artist"
    ```

#### Source Format

The `source_format` key is used in conjunction with the [`import_data`](#import-data) action to declare what type of source data will be imported from.

```toml
[newgrounds]
action = "import_data"
source_format = "json"
```

-   `exif`: Embedded EXIF metadata
-   `id3`: Embedded ID3 metadata
-   `json`: A JSON formatted file
-   `text`: A plain text file
-   `xml`: An XML formatted file
-   `xmp`: Embedded XMP metadata or an XMP sidecar file

#### Source Location

The `source_location` key is used in conjunction with the `import_data` key to declare where the metadata should be imported from. This can be a relative or absolute path, and can reference the targeted filename with the `{filename}` placeholder.

```toml
[newgrounds]
action = "import_data"
source_format = "json"
source_location = "{filename}.json" # Relative sidecar file
```

<!-- -   `absolute`: An absolute file location
-   `embedded`: Data that's embedded within the targeted file
-   `sidecar`: A sidecar file with a relative file location -->

#### Embedded Metadata

If targeting embedded data, add the `is_embedded` key and set it to `true`. If no `source_location` is used then the file this macro is targeting will be used as a source.

```toml
[newgrounds]
action = "import_data"
source_format = "id3"
is_embedded = true
```

#### Source Filters

`source_filters` are used to declare a glob list of files that are able to be targeted by this action. An entry filepath only needs to fall under one of the given source filters in order for the macro to continue. If not, then the macro will be skipped for this file entry.

<!-- prettier-ignore -->
=== "import_data"
    ```toml
    [newgrounds]
    action = "import_data"
    source_format = "json"
    source_location = "{filename}.json"
    source_filters = ["**/Newgrounds/**"]
    ```
=== "add_data"
    ```toml
    [animated]
    action = "add_data"
    source_filters = ["**/*.gif", "**/*.apng"]
    ```

#### Value

The `value` key is specifically used with the [`add_data`](#add-data) action to define what value should be added to the file entry.

<!-- prettier-ignore -->
=== "Title Field"
    ```toml
    [animated]
    action = "add_data"
    source_filters = ["**/*.gif", "**/*.apng"]
    [animated.title]
    ts_type = "text_line"
    name = "Title"
    value = "Animated Image"
    ```
=== "Tags"
    ```toml
    [animated]
    action = "add_data"
    source_filters = ["**/*.gif", "**/*.apng"]
    [animated.tags]
    ts_type = "tags"
    value = ["Animated"]
    ```

<!-- #### Source Types

The `source_type` key allows for the explicit declaration of the type and/or format of the source data. When this key is omitted, TagStudio will default to the data type that makes the most sense for the destination [TagStudio type](#tagstudio-types).

-   `string`: A character string (text)
-   `integer`: An integer
-   `float`: A floating point number
-   `url`: A string with a special URL formatting pass
-   [`ISO8601`](https://en.wikipedia.org/wiki/ISO_8601) A standard datetime format
-   `list:string`: List of strings (text)
-   `list:integer`: List of integers
-   `list:float`: List of floating point numbers -->

#### TagStudio Types

The required `ts_type` key defines the destination data format inside TagStudio itself. This can be [tags](tags.md) or any [field](fields.md) type.

-   [`tags`](tags.md)
-   [`text_line`](fields.md#text-line)
-   [`text_box`](fields.md#text-box)
-   [`datetime`](fields.md#datetime)

<!-- prettier-ignore -->
=== "Title Field"
    ```toml
    [newgrounds]
    # newgrounds table info here
    [newgrounds.title]
    ts_type = "text_line"
    name = "Title"
    ```
=== "Tags"
    ```toml
    [newgrounds]
    # newgrounds table info here
    [newgrounds.tags]
    ts_type = "tags"
    ```

### Field Specific Keys

#### Name

`name`: The name of the field to import into.

<!-- prettier-ignore -->
=== "text_line"
    ```toml
    [newgrounds.user]
    key="user"
    ts_type = "text_line"
    name = "Author"
    ```
=== "text_box"
    ```toml
    [newgrounds.content]
    key="content"
    ts_type = "text_box"
    name = "Description"
    ```

<!-- prettier-ignore -->
!!! note
    As of writing (v9.5.3) TagStudio fields still do not allow for custom names. The macro system is designed to be forward-thinking with this feature in mind, however only existing TagStudio field names are currently considered valid. Any invalid field names will default to the "Notes" field.

### Tag Specific Keys

Since TagStudio tags are more complex than other traditional tag formats, there are several options for fine-tuning how tags should be imported.

#### Delimiter

`delimiter`: The delimiter between string tags to use.

<!-- prettier-ignore -->
=== "Comma + Space Separation"
    ```toml
    [newgrounds.tags]
    ts_type = "tags"
    delimiter = ", "
    ```
=== "Newline Separation"
    ```toml
    [newgrounds.tags]
    ts_type = "tags"
    delimiter = "\n"
    ```

#### Prefix

`prefix`: An optional prefix to remove.

<!-- prettier-ignore -->
!!! example
    Given a list of tags such as `["#tag1", "#tag2", "#tag3"]`, you may wish to remove the "`#`" prefix.

```toml
[instagram.tags]
ts_type = "tags"
prefix = "#"
```

#### Strict

`strict`: Determines what [names](tags.md#naming-tags) of the TagStudio tags should be used to compare against the source data when matching.

-   `true`: Only match against the TagStudio tag [name](tags.md#name) field.
-   `false` (Default): Match against any TagStudio tag name field including [shorthands](tags.md#shorthand), [aliases](tags.md#aliases), and the [disambiguation name](tags.md#disambiguation).

#### Use Context

`use_context`: Determines if TagStudio should use context clues from other source tags to provide more accurate tag matches.

-   `true` (Default): Use context clue matching (slower, less ambiguous).
-   `false`: Ignore surrounding source tags (faster, more ambiguous).

#### On Missing

`on_missing`: Determines the behavior of how to react to source tags with no match in the library.

-   `"prompt"`: Ask the user if they wish to create, skip, or manually choose an existing tag.
-   `"create"`: Automatically create a new TagStudio tag based on the source tag.
-   `"skip"` (Default): Ignore the unmatched tags.

```toml
[newgrounds.tags]
ts_type = "tags"
strict = false
use_context = true
on_missing = "create"
```

### Manual Tag Mapping

If the results from the standard tag matching system aren't good enough to properly import specific source data into your TagStudio library, you have the option to manually specify mappings between source and destination tags. A table with the `.map` or `.inverse_map` suffixes will be used to map tags in the nearest scope.

<!-- prettier-ignore -->
=== "Global Scope"
    ```toml
    # Applies to all actions in the macro file
    [map]
    ```
=== "Action Scope"
    ```toml
    # Applies to all tag keys in the "newgrounds" action
    [newgrounds.map]
    ```
=== "Key Scope"
    ```toml
    # Only applies to tags within the "ratings" key inside the "newgrounds" action
    [newgrounds.ratings.map]
    ```

-   `map`: Used for [1 to 0](#1-to-0-ignore-matches), [1 to 1](#1-to-1), and [1 to Many](#1-to-many) mappings.
-   `inverse_map`: Used for [Many to 1](#many-to-1-inverse-map) mappings.

#### 1 to 0 (Ignore Matches)

By mapping the key of the source tag name to an empty string, you can ignore that tag when matching with your own library. This is useful if you're importing from a source that uses tags you don't wish to use or create inside your own libraries.

```toml
[newgrounds.tags.map]
# Source Tag Name = Nothing, Ignore Matches
favorite = ""
```

#### 1 to 1

By mapping the key of the source tag name to the name of one of your TagStudio tags, you can directly specify a destination tag while bypassing the matching algorithm.

<!-- prettier-ignore -->
!!! tip
    Consider using tag [aliases](tags.md#aliases) instead of 1 to 1 mapping. This mapping technique is useful if you want to map a specific source tag to a destination tag that you otherwise don't consider to be an alternate name for the destination tag.

```toml
[newgrounds.tags.map]
# Source Tag Name = TagStudio Tag Name
colored_pencil = "Drawing"
```

#### 1 to Many

By mapping the key of the source tag name to a list of your TagStudio tag names, you can cause one source tag to import as more than one of your TagStudio tags.

```toml
[newgrounds.tags.map]
# Source Tag Name = List of TagStudio Tag Names
drawing = ["Drawing (2D)", "Image (Meta Tags)"]
video = ["Animation (2D)", "Animated (Meta Tags)"]
```

#### Many to 1 (Inverse Map)

By mapping a key with the name of one of your TagStudio tags to a list of source tags, you can declare a combination of required source tags that result in a wholly new matched TagStudio tag. This is useful if you use a single tag in your TagStudio library that is represented by multiple separate tags from your source.

```toml
[newgrounds.tags.inverse_map]
# TagStudio Tag Name = List of Source Tag Names
"Animation (2D)" = ["drawing", "video"]
"Animation (3D)" = ["3D", "video"]
```

### Templates

Templates are part of the `input_data` action and allow you to take data from one or more keys of a source and combine them into a single value. Template sub-action tables must begin with the action name and end with `.template` (e.g. `[action.template]`). Source object keys can be embedded in a string value if surrounded by curly braces (`{}`). Nested keys are accessed by separating the keys with a dot (e.g. `{key.nested_key}`).

<!-- prettier-ignore-start -->
=== "Composite Template"
    ```toml
    [bluesky.template]
    template = "https://www.bsky.app/profile/{author.handle}/post/{post_id}"
    ts_type = "text_line"
    name = "Source"
    ```
=== "Multiple Templates per Action"
    ```toml
    [[artstation.template]]
    template = "Original Tags: {tags}"
    ts_type = "text_box"
    name = "Notes"

    [[artstation.template]]
    template = "Original Mediums: {mediums}"
    ts_type = "text_box"
    name = "Notes"
    ```
<!-- prettier-ignore-end -->
