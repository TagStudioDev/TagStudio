# Search Syntax
For a more detailed explanation of search syntax, check [the documentation](https://docs.tagstud.io/search/).

## Boolean Operators

Search for entries that have Tag1 **AND** Tag2
- Tag1 Tag2
- Tag1 `AND` Tag2

Search for entries that have Tag1 **OR** Tag2
- Tag1 `OR` Tag2

Search for entries that **don't** have Tag1
- `NOT` Tag1

Searches can be grouped and nested by using parentheses to surround parts of your search query.
- (Tag1 `OR` Tag2) `AND` Tag3

## Escaping Characters

To escape most search terms, surround the section of your search in plain quotes or replace spaces in tag names with underscores.
- "Tag Name With Spaces"
- Tag_Name_With_Spaces

## Tags

Search for entries that have the tag Tag1
- Tag1
- tag: Tag1

Search for entries that have the tag with ID 1
- tag_id: 1

## Path

Search for a file named `file.jpg`
- path: file.jpg

Search for any `.jpg` file
- path: *.jpg

Search for any file that ends in a number
- path: \*2.\*

Search for a file located at `folder/file.jpg`
- path: folder/file.jpg

Search for any file inside `folder/`
- path: folder/*

## File/Media Type

Search for videos
- mediatype: video

Search for `.mp4` files
- filetype: mp4

## Special Searches

Search for entries that don't contain any tags
- special: untagged