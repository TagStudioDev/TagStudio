/* reset the database to a blank slate */
drop table if exists location;
drop table if exists entry;
drop table if exists tag;
drop table if exists tag_relation;
drop table if exists entry_attribute;
drop table if exists alias;
drop table if exists entry_page;

PRAGMA user_version = 1; /* TagStudio v9.2.0 - Current */

create table location
(
    id INTEGER
        CONSTRAINT location_pk
        PRIMARY KEY AUTOINCREMENT,
    path TEXT NOT NULL UNIQUE,
    name TEXT
) STRICT;

create table entry
(
    id        INTEGER NOT NULL
        CONSTRAINT entry_pk
            PRIMARY KEY AUTOINCREMENT,
    path      TEXT    NOT NULL ,
    hash      BLOB NOT NULL,
    location INTEGER
        CONSTRAINT entry_location_fk
        REFERENCES location DEFAULT 0
) STRICT;

create table tag
(
    id       INTEGER
        CONSTRAINT tag_pk
            PRIMARY KEY AUTOINCREMENT,
    name     TEXT NOT NULL,
    shorthand TEXT,
    color    TEXT default '',
    icon     TEXT,
    preference INTEGER
        constraint tag_category_fk
            references tag
            on update cascade on update set null,
    field    INTEGER DEFAULT 0, /* Boolean False */
    system   INTEGER DEFAULT 0  /* Boolean False */
) STRICT;


create table tag_relation
(
    tag    INTEGER NOT NULL
        CONSTRAINT tag_relation_tag_id_fk
            REFERENCES tag
            ON UPDATE CASCADE ON DELETE CASCADE,
    parent INTEGER NOT NULL
        CONSTRAINT tag_relation_tag_id_fk_2
            REFERENCES tag
            ON UPDATE CASCADE ON DELETE CASCADE,
    negate INTEGER NOT NULL
        DEFAULT 0,
    CONSTRAINT tag_relation_pk
        PRIMARY KEY (tag, parent)
) STRICT, WITHOUT ROWID;

create table entry_attribute
(
    entry     INTEGER NOT NULL
        CONSTRAINT field_entry_id_fk
            REFERENCES entry
            ON UPDATE CASCADE ON DELETE CASCADE,
    title_tag INTEGER NOT NULL
        CONSTRAINT field_tag_id_fk_2
            REFERENCES tag
            ON UPDATE CASCADE ON DELETE CASCADE,
    tag    INTEGER
        CONSTRAINT field_tag_id_fk
            REFERENCES tag
            ON UPDATE CASCADE ON DELETE CASCADE,
    text      TEXT,
    number    REAL,
    datetime  TEXT,
    constraint field_pk
        primary key (entry, title_tag)
    /* field can have ONE of its non primary key values */
) STRICT;

create table alias
(
    name TEXT
        constraint  alias_pk
            primary key,
    tag  INTEGER
        constraint alias_tag_id_fk
            references tag
            on update cascade on delete cascade
) STRICT;

create table entry_page
(
    entry INTEGER NOT NULL
        CONSTRAINT entry_page_entry_fk
            REFERENCES entry
            ON UPDATE CASCADE ON DELETE CASCADE,
    tag INTEGER NOT NULL
        CONSTRAINT entry_page_tag_fk2
            REFERENCES tag
            ON UPDATE CASCADE ON DELETE CASCADE,
    page INTEGER,
    CONSTRAINT entry_page_pk
        primary key (entry, page)
) STRICT, WITHOUT ROWID;

insert into location (path, name) values ('.', 'DEFAULT');

insert into tag (name, color, system, field) VALUES ('Meta Tags', 'DEFAULT', 1, 1),
                                                    ('Title', 'DEFAULT', 1, 1),
                                                    ('Author', 'DEFAULT', 1, 1),
                                                    ('Artist', 'DEFAULT', 1, 1),
                                                    ('URL', 'DEFAULT', 1, 1),
                                                    ('Description', 'DEFAULT', 1, 1),
                                                    ('Notes', 'DEFAULT', 1, 1),
                                                    ('Tags', 'DEFAULT', 1, 1),
                                                    ('Content Tags', 'DEFAULT', 1, 1),
                                                    ('Meta Tags', 'DEFAULT', 1, 1),
                                                    ('Collation', 'DEFAULT', 1, 1),
                                                    ('Date', 'DEFAULT', 1, 1),
                                                    ('Date Created', 'DEFAULT', 1, 1),
                                                    ('Date Modified', 'DEFAULT', 1, 1),
                                                    ('Date Taken', 'DEFAULT', 1, 1),
                                                    ('Date Published', 'DEFAULT', 1, 1),
                                                    ('Archived', 'DEFAULT', 1, 1),
                                                    ('Favorite', 'DEFAULT', 1, 1),
                                                    ('Book', 'DEFAULT', 1, 1),
                                                    ('Comic', 'DEFAULT', 1, 1),
                                                    ('Series', 'DEFAULT', 1, 1),
                                                    ('Manga', 'DEFAULT', 1, 1),
                                                    ('Source', 'DEFAULT', 1, 1),
                                                    ('Date Uploaded', 'DEFAULT', 1, 1),
                                                    ('Date Released', 'DEFAULT', 1, 1),
                                                    ('Volume', 'DEFAULT', 1, 1),
                                                    ('Anthology', 'DEFAULT', 1, 1),
                                                    ('Magazine', 'DEFAULT', 1, 1),
                                                    ('Publisher', 'DEFAULT', 1, 1),
                                                    ('Guest Artist', 'DEFAULT', 1, 1),
                                                    ('Composer', 'DEFAULT', 1, 1),
                                                    ('Comments', 'DEFAULT', 1, 1);


insert into tag (name, color, system, preference) values ('Favorite', 'RED', 1, 1),
                                                       ('Archived', 'YELLOW', 1, 1);


insert into alias (tag, name) values (1, 'Favorited'), (1, 'Favorites'), (2, 'Archive');
