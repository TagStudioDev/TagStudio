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

Actions are broad categories of operations that your macro will perform. They are represented by TOML tables and must have a unique name in your macro file, but the name itself has no importance to the macro. A single macro file can contain multiple actions and each action can contain multiple tasks.

An action table with a name of your choosing (e.g. `[action]`) will contain the general configuration for your action, and nested task tables (e.g. `[action.task]`) will define the specifics of your action's tasks.

Action tables must have an `action` key with one of the following valid action values:

-   [`import_data`](#import-data): Import data from a supported external source.
-   [`add_data`](#add-data): Add data declared inside the macro file.

```toml
[newgrounds]
action = "import_data"
```

Most of the configuration of actions comes at the [task configuration](#task-configuration) level. This is where you will build out exactly how your action will translate data and instructions into results for your TagStudio library.

---

### Add Data

The `add_data` action lets you add data to a [file entry](entries.md) given one or more conditional statements. Unlike the [`import_data`](#import-data) action, the `add_data` action adds data declared in the macro itself rather than importing it form a source external to the macro.

Compatible Keys:

-   [`source_filters`](#source_filters)
-   [`value`](#value)

---

### Import Data

The `import_data` action allows you to import external data into your TagStudio library in the form of [tags](tags.md) and [fields](fields.md). While some sources need explicit support (e.g. ID3, EXIF) generic sources such as JSON sidecar files can leverage a wide array of data shaping options that allow the underlying data structure to be abstracted from TagStudio's internal data structures. This macro pairs very well with tools that download sidecar files for data such as [gallery-dl](https://github.com/mikf/gallery-dl).

Compatible Keys:

-   [`key`](#key)
-   [`source_location`](#source_location)
-   [`source_format`](#source_format)
-   [`is_embedded`](#is_embedded)

If you're importing from an object-like source (e.g. JSON), you'll need to create a nested task table with the format `[action.task]` and provide a [`key`](#key) field filled with the name of the targeted source key. In this case the task name does not matter as long as it doesn't conflict with one of the built-in task names (i.e. "`map`", "`inverse_map`, "`template`").

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

---

### Action Configuration

#### `source_format`

<!-- prettier-ignore -->
!!! note ""
    Compatible Actions: [`import_data`](#import-data)

The `source_format` key is used to declare what type of source data will be imported from.

```toml
[newgrounds]
action = "import_data"
source_format = "json"
```

-   `exif`: Embedded EXIF metadata
-   `id3`: Embedded ID3 metadata
-   `json`: A JSON formatted file
-   `text`: A plaintext file
-   `xml`: An XML formatted file
-   `xmp`: Embedded XMP metadata or an XMP sidecar file

---

#### `source_location`

<!-- prettier-ignore -->
!!! note ""
    Compatible Actions: [`import_data`](#import-data)

The `source_location` key is used to declare where the metadata should be imported from. This can be a relative or absolute path, and can reference the targeted filename with the `{filename}` placeholder.

```toml
[newgrounds]
action = "import_data"
source_format = "json"
source_location = "{filename}.json" # Relative sidecar file
```

<!-- -   `absolute`: An absolute file location
-   `embedded`: Data that's embedded within the targeted file
-   `sidecar`: A sidecar file with a relative file location -->

---

#### `is_embedded`

<!-- prettier-ignore -->
!!! note ""
    Compatible Actions: [`import_data`](#import-data)

If targeting embedded data, add the `is_embedded` key and set it to `true`. If no `source_location` is used then the file this macro is targeting will be used as a source.

```toml
[newgrounds]
action = "import_data"
source_format = "id3"
is_embedded = true
```

---

#### `source_filters`

<!-- prettier-ignore -->
!!! note ""
    Compatible Actions:  [`add_data`](#add-data), [`import_data`](#import-data)

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

<!-- ### Source Types

The `source_type` key allows for the explicit declaration of the type and/or format of the source data. When this key is omitted, TagStudio will default to the data type that makes the most sense for the destination [TagStudio type](#tagstudio-types).

-   `string`: A character string (text)
-   `integer`: An integer
-   `float`: A floating point number
-   `url`: A string with a special URL formatting pass
-   [`ISO8601`](https://en.wikipedia.org/wiki/ISO_8601) A standard datetime format
-   `list:string`: List of strings (text)
-   `list:integer`: List of integers
-   `list:float`: List of floating point numbers -->

---

## Task Configuration

An [action's](#actions) tasks need to be configured using the built-in keys available to each action. These keys may be specific to certain actions, required or optional, or expect other specific formatting. The actions section will list each action's available keys, and the following list of keys will likewise list which actions they are compatible with along with any other rules.

Along with generally defining your own custom tasks, there are a few built-in tasks that have reserved names and offer extra functionality on top of your own tasks. These currently include:

-   [`.inverse-map`](#many-to-1-inverse-map) (Inverse Tag Maps)
-   [`.map`](#manual-tag-mapping) (Tag Maps)
-   [`.template`](#templates) (Templates)

---

### `key`

<!-- prettier-ignore -->
!!! note ""
    Compatible Actions: [`import_data`](#import-data)

The `key` key is used to specify the object key to target in your data source. If you're targeting a nested object, separate the names of the keys with a dot.

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

When importing from the same key multiple times, you have the option to either choose different names for your task tables or use the same name with these tables wrapped in an extra pair of brackets.

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

---

### `ts_type`

<!-- prettier-ignore -->
!!! note ""
    Compatible Actions: [`add_data`](#add-data), [`import_data`](#import-data)

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

#### Field Specific Keys

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

#### Tag Specific Keys

Since TagStudio tags are more complex than other traditional tag formats, there are several options for fine-tuning how tags should be imported.

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

`prefix`: An optional prefix to remove.

<!-- prettier-ignore -->
!!! example
    Given a list of tags such as `["#tag1", "#tag2", "#tag3"]`, you may wish to remove the "`#`" prefix.

```toml
[instagram.tags]
ts_type = "tags"
prefix = "#"
```

`strict`: A flag that determines what [names](tags.md#naming-tags) of the TagStudio tags should be used to compare against the source data when matching.

-   `true`: Only match against the TagStudio tag [name](tags.md#name) field.
-   `false` (Default): Match against any TagStudio tag name field including [shorthands](tags.md#shorthand), [aliases](tags.md#aliases), and the [disambiguation name](tags.md#disambiguation).

`use_context`: A flag that determines if TagStudio should use context clues from other source tags to provide more accurate tag matches.

-   `true` (Default): Use context clue matching (slower, less ambiguous).
-   `false`: Ignore surrounding source tags (faster, more ambiguous).
    \*\*

---

### `value`

<!-- prettier-ignore -->
!!! note ""
    Compatible Actions: [`add_data`](#add-data)

The `value` key is use specifically with the [`add_data`](#add-data) action to define what value should be added to the file entry.

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

---

### Manual Tag Mapping

If the automatic tag matching system isn't enough to import tags the way you'd like, you can manually specify mappings between source and destination tags. Tables with the `.map` or `.inverse_map` task suffixes will be used to map tags in the nearest scope.

<!-- prettier-ignore -->
=== "Global Scope"
    ```toml
    # Applies to all actions in the macro file
    [map]
    ```
=== "Action Scope"
    ```toml
    # Applies to all tasks in the "newgrounds" action
    [newgrounds.map]
    ```
=== "Key Scope"
    ```toml
    # Only applies to the "ratings" task inside the "newgrounds" action
    [newgrounds.ratings.map]
    ```

-   `map`: Used for "[1 to 0](#1-to-0-ignore-matches)", "[1 to 1](#1-to-1)", and "[1 to many](#1-to-many)" mappings
-   `inverse_map`: Used for "[many to 1](#many-to-1-inverse-map)" mappings

---

#### 1 to 0 (Ignore Matches)

By mapping the key of the source tag name to an empty string, you can ignore that tag when matching with your own tags. This is useful if you're importing from a source that uses tags you don't wish to use or create inside your own libraries.

```toml
[newgrounds.tags.map]
# Source Tag Name = Nothing, Ignore Matches
favorite = ""
```

---

#### 1 to 1

By mapping the key or quoted string of a source tag to one of your TagStudio tags, you can directly specify a destination tag while bypassing the matching algorithm.

<!-- prettier-ignore -->
!!! tip
    Consider using tag [aliases](tags.md#aliases) instead of 1 to 1 mapping. This mapping technique is useful if you want to map a specific source tag to a destination tag that you otherwise don't consider to be an alternate name for the destination tag.

```toml
[newgrounds.tags.map]
# Source Tag Name = TagStudio Tag Name
colored_pencil = "Drawing"
"Colored Pencil" = "Drawing"
```

---

#### 1 to Many

By mapping the key or quoted string of a source tag to a **list of your TagStudio tags**, you can cause one source tag to import as more than one of your TagStudio tags.

```toml
[newgrounds.tags.map]
# Source Tag Name = List of TagStudio Tag Names
drawing = ["Drawing (2D)", "Image (Meta Tags)"]
video = ["Animation (2D)", "Animated (Meta Tags)"]
```

---

#### Many to 1 (Inverse Map)

By mapping the key or quoted string of one of your TagStudio tags to a **list of source tags**, you can declare a combination of required source tags that result in a wholly new matched TagStudio tag. This is useful if you use a single tag in your TagStudio library that is represented by multiple separate tags from your source.

```toml
[newgrounds.tags.inverse_map]
# TagStudio Tag Name = List of Source Tag Names
"Animation (2D)" = ["drawing", "video"]
"Animation (3D)" = ["3D", "video"]
```

---

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
