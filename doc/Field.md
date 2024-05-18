# Field

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
