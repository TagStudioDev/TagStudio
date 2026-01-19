# Command-Line Library Refresh

## Overview

TagStudio now supports refreshing libraries from the command line without launching the GUI. This is particularly useful for setting up automated background refreshes on large libraries.

## Usage

### Basic Syntax

```bash
tagstudio --refresh /path/to/library
```

Or using the short form:

```bash
tagstudio -r /path/to/library
```

### Examples

#### Refresh a library on your Desktop

```bash
tagstudio --refresh ~/Desktop/my-media-library
```

#### Refresh a library and capture the output

```bash
tagstudio --refresh /mnt/large-drive/photos/ > refresh.log
```

#### Set up automatic background refresh (Linux/macOS)

Using cron to refresh a library every night at 2 AM:

```bash
0 2 * * * /usr/local/bin/tagstudio --refresh ~/media/library
```

#### Set up automatic background refresh (Windows)

Using Task Scheduler:

1. Create a new basic task
2. Set the trigger to your desired time
3. Set the action to: `C:\path\to\python.exe -m tagstudio.main -r C:\path\to\library`

## Output

The command will display the following information upon completion:

```
Refresh complete: scanned 5000 files, added 25 new entries
```

The exit code will be:

- `0` if the refresh completed successfully
- `1` if an error occurred (invalid path, corrupted library, etc.)

## Error Handling

If an error occurs, the command will display an error message and exit with code 1. Common errors include:

- **Library path does not exist**: Verify the path is correct and accessible
- **Failed to open library**: The library may be corrupted or not a valid TagStudio library
- **Library requires JSON to SQLite migration**: Open the library in the GUI to complete the migration

## Notes

- The refresh process scans the library directory for new files that are not yet in the database
- Only new files are added; existing entries are not modified
- Large libraries may take several minutes to refresh depending on the number of files
- The command will report the number of files scanned and new entries added
