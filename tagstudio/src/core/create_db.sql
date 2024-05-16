/* reset the database to a blank slate */
drop table if exists location;
drop table if exists color;
drop table if exists entry;
drop table if exists tag;
drop table if exists tag_relation;
drop table if exists entry_attribute;
drop table if exists alias;
drop table if exists entry_page;
drop table if exists ignored_extension;


create table location
(
    id INTEGER
        CONSTRAINT location_pk
        PRIMARY KEY AUTOINCREMENT,
    path TEXT NOT NULL UNIQUE,
    name TEXT
) STRICT;

-- create table color
-- (
--     id           INTEGER
--                     CONSTRAINT color_pk
--                     PRIMARY KEY AUTOINCREMENT,
--     name         TEXT not null,
--     color        TEXT not null,
--     text         TEXT,
--     border       TEXT,
--     light_accent TEXT,
--     dark_accent  TEXT
-- );

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

-- insert into color values ('DEFAULT', '#1E1A33', '#CDA7F7', '#2B2547', '#CDA7F7', '#1E1A33'),
--                          ('BLACK', '#111018', '#B7B6BE', '#18171E', '#B7B6BE', '#03020A'),
--                          ('DARK GRAY', '#24232A', '#BDBCC4', '#2A2930', '#BDBCC4', '#07060E'),
--                          ('GRAY', '#53525A', '#CBCAD2', '#5B5A62', '#CBCAD2', '#191820'),
--                          ('LIGHT GRAY', '#AAA9B0', '#191820', '#B6B4BC', '#CBCAD2', '#191820'),
--                          ('WHITE', '#F2F1F8', '#302F36', '#FEFEFF', '#FFFFFF', '#302F36'),
--                          ('LIGHT PINK', '#FF99C4', '#6C2E3B', '#FFAAD0', '#FFCBE7', '#6C2E3B'),
--                          ('PINK', '#FF99C4', '#6C2E3B', '#FFAAD0', '#FFCBE7', '#6C2E3B'),
--                          ('MAGENTA', '#F6466F', '#61152F', '#F7587F', '#FBA4BF', '#61152F'),
--                          ('RED', '#E22C3C', '#440D12', '#B21F2D', '#F39CAA', '#440D12'),
--                          ('RED ORANGE', '#E83726', '#61120B', '#EA4B3B', '#F5A59D', '#61120B'),
--                          ('SALMON', '#F65848', '#6F1B16', '#F76C5F', '#FCADAA', '#6F1B16'),
--                          ('ORANGE', '#ED6022', '#551E0A', '#EF7038', '#F7B79B', '#551E0A'),
--                          ('YELLOW ORANGE', '#FA9A2C', '#66330D', '#FBA94B', '#FDD7AB', '#66330D'),
--                          ('YELLOW', '#FFD63D', '#754312', '#E8AF31', '#FFF3C4', '#754312'),
--                          ('MINT', '#4AED90', '#164F3E', '#79F2B1', '#C8FBE9', '#164F3E'),
--                          ('LIME', '#92E649', '#405516', '#B2ED72', '#E9F9B7', '#405516'),
--                          ('LIGHT GREEN', '#85EC76', '#2B5524', '#A3F198', '#E7FBE4', '#2B5524'),
--                          ('GREEN', '#28BB48', '#0D3828', '#43C568', '#93E2C8', '#0D3828'),
--                          ('TEAL', '#1AD9B2', '#08424B', '#4DE3C7', '#A0F3E8', '#08424B'),
--                          ('CYAN', '#49E4D5', '#0F4246', '#76EBDF', '#BFF5F0', '#0F4246'),
--                          ('LIGHT BLUE', '#55BBF6', '#122541', '#70C6F7', '#BBE4FB', '#122541'),
--                          ('BLUE', '#3B87F0', '#AEDBFA', '#4E95F2', '#AEDBFA', '#122948'),
--                          ('BLUE VIOLET', '#5948F2', '#9CB8FB', '#6258F3', '#9CB8FB', '#1B1649'),
--                          ('VIOLET', '#874FF5', '#C9B0FA', '#9360F6', '#C9B0FA', '#3A1860'),
--                          ('PURPLE', '#BB4FF0', '#531862', '#C364F2', '#DDA7F7', '#531862'),
--                          ('PEACH', '#F1C69C', '#613F2F', '#F4D4B4', '#FBEEE1', '#613F2F'),
--                          ('BROWN', '#823216', '#CD9D83', '#8A3E22', '#CD9D83', '#3A1804'),
--                          ('LAVENDER', '#AD8EEF', '#492B65', '#B99EF2', '#D5C7FA', '#492B65'),
--                          ('BLONDE', '#EFC664', '#6D461E', '#F3D387', '#FAEBC6', '#6D461E'),
--                          ('AUBURN', '#A13220', '#D98A7F', '#AA402F', '#D98A7F', '#3D100A'),
--                          ('LIGHT BROWN', '#BE5B2D', '#4C290E', '#C4693D', '#E5B38C', '#4C290E'),
--                          ('DARK BROWN', '#4C2315', '#B78171', '#542A1C', '#B78171', '#211006'),
--                          ('COOL GRAY', '#515768', '#9EA1C3', '#5B6174', '#9EA1C3', '#181A37'),
--                          ('WARM GRAY', '#625550', '#C0A392', '#6C5E57', '#C0A392', '#371D18'),
--                          ('OLIVE', '#4C652E', '#B4C17A', '#586F36', '#B4C17A', '#23300E'),
--                          ('BERRY', '#9F2AA7', '#CC8FDC', '#AA43B4', '#CC8FDC', '#41114A');

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



-- select t.name as name, t2.name as category from tag as t left join tag as t2 on t.category = t2.id;