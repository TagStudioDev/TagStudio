# File Entries

File entries are the individual representations of your files inside a TagStudio [library](index.md). Each one corresponds one-to-one to a file on disk, and tracks all of the additional [tags](tag.md) and metadata that you attach to it inside TagStudio.

## Storage

File entry data is storied within the `ts_library.sqlite` file inside each library's `.TagStudio` folder. No modifications are made to your actual files on disk, and nothing like sidecar files are generated for your files.

## Appearance

File entries appear as file previews both inside the thumbnail grid. The preview panel shows a more detailed preview of the file, along with extra file stats and all attached TagStudio tags and fields.

## Unlinked File Entries

If the file that an entry is referencing has been moved, renamed, or deleted on disk, then TagStudio will display a red chain-link icon for the thumbnail image. Certain uncached stats such as the file size and image dimensions will also be unavailable to see in the preview panel when a file becomes unlinked.

To fix file entries that have become unlinked, select the "Fix Unlinked Entries" option from the Tools menu. From there, refresh the unlinked entry count and choose whether to search and relink you files, and/or delete the file entires from your library. This will NOT delete or modify any files on disk.

## Internal Structure

-   `id` (`INTEGER`/`int`, `UNIQUE`, `NOT NULL`, `PRIMARY KEY`)
    -   The ID for the file entry.
    -   Used for guaranteed unique references.
-   `folder` (`INTEGER`/`int`, `NOT NULL`, `FOREIGN KEY`)
    -   _Not currently used, may be removed._
-   `path` (`VARCHAR`/`Path`, `UNIQUE`, `NOT NULL`)
    -   The filename and filepath relative to the root of the library folder.
    -   (E.g. for library "Folder", path = "any_subfolders/filename.txt")
-   `suffix` (`VARCHAR`/`str`, `NOT NULL`)
    -   The filename suffix with no leading dot.
    -   Used for quicker file extension checks.
-   `date_created` (`DATETIME`/`Datetime`)
    -   _Not currently used, will be implemented in an upcoming update._
    -   The creation date of the file (not the entry).
    -   Generates from `st_birthtime` on Windows and Mac, and `st_ctime` on Linux.
-   `date_modified` (`DATETIME`/`Datetime`)
    -   _Not currently used, will be implemented in an upcoming update._
    -   The latest modification date of the file (not the entry).
    -   Generates from `st_mtime`.
-   `date_added` (`DATETIME`/`Datetime`)
    -   The date the file entry was added to the TagStudio library.

### Table Relationships

-   `tag_entries`
    -   A relationship between `entry_id` to `tag_id`s from the `tags` table.
-   `text_fields`
    -   (TODO: determine the relationship for `entry_id`)
-   `datetime_fields`
    -   (TODO: determine the relationship for `entry_id`)
