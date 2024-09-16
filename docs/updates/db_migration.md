# Database Migration

The database migration is an upcoming refactor to TagStudio's library data storage system. The database will be migrated from a JSON-based one to a SQLite-based one. Part of this migration will include a reworked schema, which will allow for several new features and changes to how [tags](../library/tag.md) and [fields](../library/field.md) operate.

## Schema

![Database Schema](../assets/db_schema.png){ width="600" }

### `alias` Table

_Description TBA_

### `entry` Table

_Description TBA_

### `entry_attribute` Table

_Description TBA_

### `entry_page` Table

_Description TBA_

### `location` Table

_Description TBA_

### `tag` Table

_Description TBA_

### `tag_relation` Table

_Description TBA_

## Resulting New Features and Changes

- Multiple Directory Support
- [Tag Categories](../library/tag_categories.md) (Replaces [Tag Fields](../library/field.md#tag_box))
- [Tag Overrides](../library/tag_overrides.md)
- User-Defined [Fields](../library/field.md)
- Tag Icons
