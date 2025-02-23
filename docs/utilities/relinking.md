# File and Entry Relinking

Tools and macros are features that serve to create a more fluid [library](../library/index.md)-managing process, or provide some extra functionality. Please note that some are still in active development and will be fleshed out in future updates.

## Tools

### Fix Unlinked Entries

This tool displays the number of unlinked [entries](../library/entry.md), and some options for their resolution.

Refresh
: Scans through the library and updates the unlinked entry count.

Search & Relink
: Attempts to automatically find and reassign missing files.

Delete Unlinked Entries
: Displays a confirmation prompt containing the list of all missing files to be deleted before committing to or cancelling the operation.

### Fix Duplicate Files

This tool allows for management of duplicate files in the library using a [DupeGuru](https://dupeguru.voltaicideas.net/) file.

Load DupeGuru File
: load the "results" file created from a DupeGuru scan

Mirror Entries
: Duplicate entries will have their contents mirrored across all instances. This allows for duplicate files to then be deleted with DupeGuru as desired, without losing the [field](../library/field.md) data that has been assigned to either. (Once deleted, the "Fix Unlinked Entries" tool can be used to clean up the duplicates)

### Create Collage

This tool is a preview of an upcoming feature. When selected, TagStudio will generate a collage of all the contents in a Library, which can be found in the Library folder ("/your-folder/.TagStudio/collages/"). Note that this feature is still in early development, and doesn't yet offer any customization options.
