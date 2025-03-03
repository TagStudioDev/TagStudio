BOX_FIELDS = ["tag_box", "text_box"]
TEXT_FIELDS = ["text_line", "text_box"]
DATE_FIELDS = ["datetime"]


DEFAULT_FIELDS: list[dict] = [
    {"id": 0, "name": "Title", "type": "text_line"},
    {"id": 1, "name": "Author", "type": "text_line"},
    {"id": 2, "name": "Artist", "type": "text_line"},
    {"id": 3, "name": "URL", "type": "text_line"},
    {"id": 4, "name": "Description", "type": "text_box"},
    {"id": 5, "name": "Notes", "type": "text_box"},
    {"id": 6, "name": "Tags", "type": "tag_box"},
    {"id": 7, "name": "Content Tags", "type": "tag_box"},
    {"id": 8, "name": "Meta Tags", "type": "tag_box"},
    {"id": 9, "name": "Collation", "type": "collation"},
    {"id": 10, "name": "Date", "type": "datetime"},
    {"id": 11, "name": "Date Created", "type": "datetime"},
    {"id": 12, "name": "Date Modified", "type": "datetime"},
    {"id": 13, "name": "Date Taken", "type": "datetime"},
    {"id": 14, "name": "Date Published", "type": "datetime"},
    {"id": 15, "name": "Archived", "type": "checkbox"},
    {"id": 16, "name": "Favorite", "type": "checkbox"},
    {"id": 17, "name": "Book", "type": "collation"},
    {"id": 18, "name": "Comic", "type": "collation"},
    {"id": 19, "name": "Series", "type": "collation"},
    {"id": 20, "name": "Manga", "type": "collation"},
    {"id": 21, "name": "Source", "type": "text_line"},
    {"id": 22, "name": "Date Uploaded", "type": "datetime"},
    {"id": 23, "name": "Date Released", "type": "datetime"},
    {"id": 24, "name": "Volume", "type": "collation"},
    {"id": 25, "name": "Anthology", "type": "collation"},
    {"id": 26, "name": "Magazine", "type": "collation"},
    {"id": 27, "name": "Publisher", "type": "text_line"},
    {"id": 28, "name": "Guest Artist", "type": "text_line"},
    {"id": 29, "name": "Composer", "type": "text_line"},
    {"id": 30, "name": "Comments", "type": "text_box"},
]
