# Library

The library is how TagStudio represents your chosen directory, with every file inside being represented by a [file entry](entry.md). You can have as many or few libraries as you wish, since each libraries' data is stored within a `.TagStudio` folder at its root. From there the library save file itself is stored as `ts_library.sqlite`, with TagStudio versions 9.4 and below using a the legacy `ts_library.json` format.

Note that this means [tags](tag.md) you create only exist _per-library_.
