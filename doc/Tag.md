# Tag

Tags are small data objects that represent an attribute of something. A person, place, thing, concept, you name it! Tags in TagStudio allow for more sophisticated [entry](/doc/Entry.md) organization and searching thanks to their ability to contain alternate names and spellings via aliases, relational organization thanks to parent tags, and more! Tags can be as simple or as powerful as you want to make them, and TagStudio aims to provide as much power to you as possible.

## Tag Object Structure (v9.x.x):

### `id`
ID for the tag.
- Int, Unique, Required
- Used for internal processing
### `name`
The normal name of the tag, with no shortening or specification.
- String, Required
- Doesn't have to be unique
- Used for display, searching, and storing
### `shorthand`
The shorthand name for the tag. Works like an alias but is used for specific display purposes.
- String, Optional
- Doesn't have to be unique
- Used for display and searching
### `aliases`
Alternate names for the tag.
- List of Strings, Optional
- Recommended to be unique to this tag
- Used for searching
### `subtags`
Other Tags that make up properties of this tag. Also called "parent tags".
- List of Strings, Optional
- Used for display (first subtag only) and searching.
### `color`
A color name string for customizing the tag's display color
- String, Optional
- Used for display

## Tag Search Examples:

Using for example, a library of files tagged with the following tags:

| *Tag* | `name` | `shorthand` | `aliases` | `subtags` |
| --- | --- | --- | --- | --- |
| League of Legends | "League of Legends" | "LoL" | ["League"] | ["Game", "Fantasy"] |
| Arcane | "Arcane" | "" | [] | ["League of Legends", "Cartoon"] |
| Jinx (LoL) | "Jinx Piltover" | "Jinx" | ["Jinxy", "Jinxy Poo"] | ["League of Legends", "Arcane", "Character"] |
| Zander (Arcane) | "Zander Zanderson" | "Zander" | [] | ["Arcane", "Character"] |
| Mr. Legend (LoL) | "Mr. Legend" | "" | [] | ["League of Legends", "Character"] |


The query "League of Legends" will display results tagged with:

- League of Legends [because of "League of Legend"'s name]
- Arcane [because of "Arcane"'s subtag]
- Jinx (LoL) [because of "Jinx Piltover"'s subtag]
- Mr. Legend (LoL) [because of "Mr. Legned (LoL)'s subtag"]
- Zander (Arcane) [because of "Zander Zanderson"'s subtag ("Arcane")'s subtag]

The query "LoL" will display results tagged with:

- League of Legends [because of "League of Legend"'s shorthand]
- LoL [because of "League of Legend"'s shorthand]
- Arcane [because of "Arcane"'s subtag]
- Jinx (LoL) [because of "Jinx Piltover"'s subtag]
- Mr. Legend (LoL) [because of "Mr. Legned (LoL)'s subtag"]
- Zander (Arcane) [because of "Zander Zanderson"'s subtag ("Arcane")'s subtag]

The query "Arcane" will display results tagged with:

- Arcane [because of "Arcane"'s name]
- Jinx (LoL) [because of "Jinx Piltover"'s subtag "Arcane"]
- Zander (Arcane) [because of "Zander Zanderson"'s subtag]

# Planned Changes
