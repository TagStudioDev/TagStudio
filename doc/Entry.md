# Entry

A library entry is a one-to-one representation with a file on your system.

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
