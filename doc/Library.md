# Library

The library is how TagStudio represents your chosen directory. In this vault-like system, all files within this directory are represented by [entries](/doc/Entry.md), which then contain metadata fields. All TagStudio data for a Library is stored within a `.TagStudio` folder at the root of the library's directory.

Internal Library objects include:
- [Fields](/doc/Field.md) (v9+)
  - Text Line (Title, Author, Artist, URL)
  - Text Box (Description, Notes)
  - Tag Box (Tags, Content Tags, Meta Tags)
  - Datetime (Date Created, Date Modified, Date Taken)
  - Collation (Collation)
  - Checkbox (Archive, Favorite)
  - Drop Down (Group of Tags to select one from)
- [Entries](/doc/Entry.md) (v1+)
- [Tags](/doc/Tag.md) (v7+)
- Macros (v9/10+)
