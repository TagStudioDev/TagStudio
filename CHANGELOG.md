# TagStudio Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [9.5.2] - 2024-03-06

### Added

#### Search

- feat(ui): add setting to not display full filepaths by [@HermanKassler](https://github.com/HermanKassler) in [#841](https://github.com/TagStudioDev/TagStudio/pull/841)
- feat: add filename and path sorting by [@Computerdores](https://github.com/Computerdores) in [#842](https://github.com/TagStudioDev/TagStudio/pull/842)

#### Settings

- feat: new settings menu + settings backend by [@Computerdores](https://github.com/Computerdores) in [#859](https://github.com/TagStudioDev/TagStudio/pull/859)

#### UI

- feat(ui): merge media controls by [@csponge](https://github.com/csponge) in [#805](https://github.com/TagStudioDev/TagStudio/pull/805)
    - fix: Remove border from video preview top and left by [@zfbx](https://github.com/zfbx) in [#900](https://github.com/TagStudioDev/TagStudio/pull/900)
- feat(ui): add more default icons and file type equivalencies by [@CyanVoxel](https://github.com/CyanVoxel) in [#882](https://github.com/TagStudioDev/TagStudio/pull/882)
- ui: recent libraries list improvements by [@CyanVoxel](https://github.com/CyanVoxel) in [#881](https://github.com/TagStudioDev/TagStudio/pull/881)

#### Misc

- feat: provide a .desktop file by [@xarvex](https://github.com/xarvex) in [#870](https://github.com/TagStudioDev/TagStudio/pull/870)

### Fixed

- fix: catch NotImplementedError for Float16 JPEG-XL files by [@CyanVoxel](https://github.com/CyanVoxel) in [#849](https://github.com/TagStudioDev/TagStudio/pull/849)
- fix(nix/package): account for GTK platform by [@xarvex](https://github.com/xarvex) in [#868](https://github.com/TagStudioDev/TagStudio/pull/868)
- fix: do not set palette for Linux-like systems that offer theming by [@xarvex](https://github.com/xarvex) in [#869](https://github.com/TagStudioDev/TagStudio/pull/869)
- fix(flake): remove pinned input, only consume in Nix shell by [@xarvex](https://github.com/xarvex) in [#872](https://github.com/TagStudioDev/TagStudio/pull/872)
- fix: stop ffmpeg cmd windows, refactor ffmpeg_checker by [@CyanVoxel](https://github.com/CyanVoxel) in [#855](https://github.com/TagStudioDev/TagStudio/pull/855)
- fix: hide mnemonics on macOS by [@CyanVoxel](https://github.com/CyanVoxel) in [#856](https://github.com/TagStudioDev/TagStudio/pull/856)
- fix: use UNION instead of UNION ALL by [@CyanVoxel](https://github.com/CyanVoxel) in [#877](https://github.com/TagStudioDev/TagStudio/pull/877)
- fix: remove unescaped ampersand from "about.description" by [@CyanVoxel](https://github.com/CyanVoxel) in [#885](https://github.com/TagStudioDev/TagStudio/pull/885)
- fix(ui): display 0 frame webp files in preview panel by [@CyanVoxel](https://github.com/CyanVoxel) in [64dc88a](https://github.com/TagStudioDev/TagStudio/commit/64dc88afa90bb11f3c9b74a2522f947370ce21db)
- fix: close pdf file object in thumb renderer by [@Computerdores](https://github.com/Computerdores) in [#893](https://github.com/TagStudioDev/TagStudio/pull/893)
- perf: improve responsiveness of GIF entries by [@Computerdores](https://github.com/Computerdores) in [#894](https://github.com/TagStudioDev/TagStudio/pull/894)
- fix(ui): seamlessly loop videos by [@CyanVoxel](https://github.com/CyanVoxel) in [#902](https://github.com/TagStudioDev/TagStudio/pull/902)

### Internal Changes

- refactor!: change layout; import and build change by [@xarvex](https://github.com/xarvex) and [@CyanVoxel](https://github.com/CyanVoxel) in [#844](https://github.com/TagStudioDev/TagStudio/pull/844)
- fix: log all problems in translation test by [@Computerdores](https://github.com/Computerdores) in [#839](https://github.com/TagStudioDev/TagStudio/pull/839)
- refactor: split translation keys for about screen by [@CyanVoxel](https://github.com/CyanVoxel) in [#845](https://github.com/TagStudioDev/TagStudio/pull/845)
- feat(ci): development tooling refresh and split documentation by [@xarvex](https://github.com/xarvex) in [#867](https://github.com/TagStudioDev/TagStudio/pull/867)
- refactor: type hints and improvements in file_opener.py by [@VasigaranAndAngel](https://github.com/VasigaranAndAngel) in [#876](https://github.com/TagStudioDev/TagStudio/pull/876)
- build: update spec file to use proper pathex and datas paths by [@Leonard2](https://github.com/Leonard2) in [#895](https://github.com/TagStudioDev/TagStudio/pull/895)
- refactor: fix various missing and broken type hints@VasigaranAndAngel in [#901](https://github.com/TagStudioDev/TagStudio/pull/901)
- refactor: fix type hints and overrides in flowlayout.py by [@VasigaranAndAngel](https://github.com/VasigaranAndAngel) in [#880](https://github.com/TagStudioDev/TagStudio/pull/880)

### Documentation

- docs: fix typos and grammar by [@Gawidev](https://github.com/Gawidev) in [#879](https://github.com/TagStudioDev/TagStudio/pull/879)
- docs: update `ThumbRenderer` source by [@emmanuel-ferdman](https://github.com/emmanuel-ferdman) in [#896](https://github.com/TagStudioDev/TagStudio/pull/896)

### Translations

- Added Japanese (50%)
    - [@needledetector](https://github.com/needledetector)
- Updated Turkish (93%)
    - [@Nyghl](https://github.com/Nyghl)
- Updated Filipino (57%)
    - [@searinminecraft](https://github.com/searinminecraft)
- Updated Tamil (92%)
    - [@TamilNeram](https://github.com/TamilNeram)
- Updated Portuguese (Brazil) (83%)
    - [@viniciushelder](https://github.com/viniciushelder)
- Updated German (95%)
    - [@DontBlameMe99](https://github.com/DontBlameMe99), [@Computerdores](https://github.com/Computerdores)
- Updated Russian (85%)
    - werdi, [@Dott-rus](https://github.com/Dott-rus)
- Updated Hungarian (100%)
    - Szíjártó Levente Pál
- Updated Spanish (96%)
    - Joan, [@Nginearing](https://github.com/Nginearing)
- Updated French (100%)
    - [@kitsumed](https://github.com/kitsumed)
- Updated Toki Pona (80%)
    - [@Math-Bee](https://github.com/Math-Bee)

## [9.5.1] - 2024-03-06

### Fixed

- Fixed translations crashing the program and preventing it from being reopened ([#827](https://github.com/TagStudioDev/TagStudio/issues/827))
    - fix: restore `translate_formatted()` method as `format()` by [@CyanVoxel](https://github.com/CyanVoxel) in [#830](https://github.com/TagStudioDev/TagStudio/pull/830)
    - tests: add tests for translations by [@Computerdores](https://github.com/Computerdores) in [#833](https://github.com/TagStudioDev/TagStudio/pull/833)
    - fix(translations): fix invalid placeholders by [@CyanVoxel](https://github.com/CyanVoxel) in [#835](https://github.com/TagStudioDev/TagStudio/pull/835)
- Removed empty parentheses from the "About" screen title
    - fix: separate about screen title from translations by [@CyanVoxel](https://github.com/CyanVoxel) in [#836](https://github.com/TagStudioDev/TagStudio/pull/836)

### Translations

- Updated French (99%)
    - [@alessdangelo](https://github.com/alessdangelo), [@Bamowen](https://github.com/Bamowen), [@kitsumed](https://github.com/kitsumed)
- Updated German (98%)
    - [@Thesacraft](https://github.com/Thesacraft)
- Updated Portuguese (Brazil) (88%)
    - [@viniciushelder](https://github.com/viniciushelder)
- Updated Russian (73%)
    - werdei
- Updated Spanish (95%)
    - [@JCC1998](https://github.com/JCC1998)

### Documentation

- docs: fix category typo by [@salem404](https://github.com/salem404) in [#834](https://github.com/TagStudioDev/TagStudio/pull/834)

## [9.5.0] - 2024-03-03

### Added

#### Overhauled Search Engine

##### Boolean Operators

- feat: implement query language by [@Computerdores](https://github.com/Computerdores) in [#606](https://github.com/TagStudioDev/TagStudio/pull/606)
- feat: optimize AND queries by [@Computerdores](https://github.com/Computerdores) in [#679](https://github.com/TagStudioDev/TagStudio/pull/679)

##### Filetype, Mediatype, and Glob Path + Smartcase Searches

- fix: remove wildcard requirement for tags by [@Tyrannicodin](https://github.com/Tyrannicodin) in [#481](https://github.com/TagStudioDev/TagStudio/pull/481)
- feat: add filetype and mediatype searches by [@python357-1](https://github.com/python357-1) in [#575](https://github.com/TagStudioDev/TagStudio/pull/575)
- feat: make path search use globs by [@python357-1](https://github.com/python357-1) in [#582](https://github.com/TagStudioDev/TagStudio/pull/582)
- feat: implement search equivalence of "jpg" and "jpeg" filetypes by [@Computerdores](https://github.com/Computerdores) in [#649](https://github.com/TagStudioDev/TagStudio/pull/649)
- feat: add smartcase and globless path searches by [@CyanVoxel](https://github.com/CyanVoxel) in [#743](https://github.com/TagStudioDev/TagStudio/pull/743)

##### Sortable Results

- feat: sort by "date added" in library by [@Computerdores](https://github.com/Computerdores) in [#674](https://github.com/TagStudioDev/TagStudio/pull/674)

##### Autocomplete

- feat: add autocomplete for search engine by [@python357-1](https://github.com/python357-1) in [#586](https://github.com/TagStudioDev/TagStudio/pull/586)

#### Replaced "Tag Fields" with Tag Categories

Instead of tags needing to be added to a tag field type such as "Meta Tags", "Content Tags", or just the "Tags" field, tags are now added directly to file entries with no intermediary step. While tag field types offered a way to further organize tags, it was cumbersome, inflexible, and simply not fully fleshed out. Tag Categories offer all of the previous (intentional) functionality while greatly increasing the ease of use and customization.

- feat!: tag categories by [@CyanVoxel](https://github.com/CyanVoxel) in [#655](https://github.com/TagStudioDev/TagStudio/pull/655)
    
    [![Screenshot 2025-01-04 at 04 23 43](https://private-user-images.githubusercontent.com/46939827/400138597-0b92eca5-db8f-4e3e-954b-1b4f3795f073.png?jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3NDY2NTU5ODIsIm5iZiI6MTc0NjY1NTY4MiwicGF0aCI6Ii80NjkzOTgyNy80MDAxMzg1OTctMGI5MmVjYTUtZGI4Zi00ZTNlLTk1NGItMWI0ZjM3OTVmMDczLnBuZz9YLUFtei1BbGdvcml0aG09QVdTNC1ITUFDLVNIQTI1NiZYLUFtei1DcmVkZW50aWFsPUFLSUFWQ09EWUxTQTUzUFFLNFpBJTJGMjAyNTA1MDclMkZ1cy1lYXN0LTElMkZzMyUyRmF3czRfcmVxdWVzdCZYLUFtei1EYXRlPTIwMjUwNTA3VDIyMDgwMlomWC1BbXotRXhwaXJlcz0zMDAmWC1BbXotU2lnbmF0dXJlPWY4ZWEzOWRkZjkwOGZmYjZmZDUzMjU1MjJhNDNkNzYzZmM4YjZkMTUyNWIzMjNhMGY1NWNhYmU4ODNiNzlhMzYmWC1BbXotU2lnbmVkSGVhZGVycz1ob3N0In0.cE_WO9AHsigusAbtaQV0QtN4FjYJz0lyHLLwFFDBO-0)](https://private-user-images.githubusercontent.com/46939827/400138597-0b92eca5-db8f-4e3e-954b-1b4f3795f073.png?jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3NDY2NTU5ODIsIm5iZiI6MTc0NjY1NTY4MiwicGF0aCI6Ii80NjkzOTgyNy80MDAxMzg1OTctMGI5MmVjYTUtZGI4Zi00ZTNlLTk1NGItMWI0ZjM3OTVmMDczLnBuZz9YLUFtei1BbGdvcml0aG09QVdTNC1ITUFDLVNIQTI1NiZYLUFtei1DcmVkZW50aWFsPUFLSUFWQ09EWUxTQTUzUFFLNFpBJTJGMjAyNTA1MDclMkZ1cy1lYXN0LTElMkZzMyUyRmF3czRfcmVxdWVzdCZYLUFtei1EYXRlPTIwMjUwNTA3VDIyMDgwMlomWC1BbXotRXhwaXJlcz0zMDAmWC1BbXotU2lnbmF0dXJlPWY4ZWEzOWRkZjkwOGZmYjZmZDUzMjU1MjJhNDNkNzYzZmM4YjZkMTUyNWIzMjNhMGY1NWNhYmU4ODNiNzlhMzYmWC1BbXotU2lnbmVkSGVhZGVycz1ob3N0In0.cE_WO9AHsigusAbtaQV0QtN4FjYJz0lyHLLwFFDBO-0)

#### Thumbnails and File Previews

##### New Thumbnail Support

- feat: add svg thumbnail support (port [#442](https://github.com/TagStudioDev/TagStudio/pull/442)) by [@Tyrannicodin](https://github.com/Tyrannicodin) and [@CyanVoxel](https://github.com/CyanVoxel) in [#540](https://github.com/TagStudioDev/TagStudio/pull/540)
- feat: add pdf thumbnail support (port [#378](https://github.com/TagStudioDev/TagStudio/pull/378)) by [@Heiholf](https://github.com/Heiholf) and [@CyanVoxel](https://github.com/CyanVoxel) in [#543](https://github.com/TagStudioDev/TagStudio/pull/543)
- feat: add ePub thumbnail support (port [#387](https://github.com/TagStudioDev/TagStudio/pull/387)) by [@Heiholf](https://github.com/Heiholf) and [@CyanVoxel](https://github.com/CyanVoxel) in [#539](https://github.com/TagStudioDev/TagStudio/pull/539)
- feat: add OpenDocument thumbnail support (port [#366](https://github.com/TagStudioDev/TagStudio/pull/366)) by [@Joshua-Beatty](https://github.com/Joshua-Beatty) and [@CyanVoxel](https://github.com/CyanVoxel) in [#545](https://github.com/TagStudioDev/TagStudio/pull/545)
- feat: add JXL thumbnail and animated APNG + WEBP support (port [#344](https://github.com/TagStudioDev/TagStudio/pull/344) and partially port [#357](https://github.com/TagStudioDev/TagStudio/pull/357)) by [@BPplays](https://github.com/BPplays) and [@CyanVoxel](https://github.com/CyanVoxel) in [#549](https://github.com/TagStudioDev/TagStudio/pull/549)
    - fix: catch ImportError for pillow_jxl module by [@CyanVoxel](https://github.com/CyanVoxel) in [a2f9685](https://github.com/TagStudioDev/TagStudio/commit/a2f9685bc0d744ea6f5334c6d2926aad3f6d375a)

##### Audio Playback

- feat: audio playback by [@csponge](https://github.com/csponge) in [#576](https://github.com/TagStudioDev/TagStudio/pull/576)
    - feat(ui): add audio volume slider by [@SkeleyM](https://github.com/SkeleyM) in [#691](https://github.com/TagStudioDev/TagStudio/pull/691)

##### Thumbnail Caching

- feat(ui): add thumbnail caching by [@CyanVoxel](https://github.com/CyanVoxel) in [#694](https://github.com/TagStudioDev/TagStudio/pull/694)

#### Tags

##### Delete Tags _(Finally!)_

- feat: remove and create tags from tag database panel by [@DandyDev01](https://github.com/DandyDev01) in [#569](https://github.com/TagStudioDev/TagStudio/pull/569)

##### Custom User-Created Tag Colors

Create your own custom tag colors via the new Tag Color Manager! Tag colors are assigned a namespace (group) and include a name, primary color, and optional secondary color. By default the secondary color is used for the tag text color, but this can also be toggled to apply to the border color as well!

- feat(ui)!: user-created tag colors@CyanVoxel in [#801](https://github.com/TagStudioDev/TagStudio/pull/801)

[![](https://private-user-images.githubusercontent.com/46939827/413668576-b591f1fe-1c44-4d82-b6e5-d166590aeab1.png?jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3NDY2NTU5ODIsIm5iZiI6MTc0NjY1NTY4MiwicGF0aCI6Ii80NjkzOTgyNy80MTM2Njg1NzYtYjU5MWYxZmUtMWM0NC00ZDgyLWI2ZTUtZDE2NjU5MGFlYWIxLnBuZz9YLUFtei1BbGdvcml0aG09QVdTNC1ITUFDLVNIQTI1NiZYLUFtei1DcmVkZW50aWFsPUFLSUFWQ09EWUxTQTUzUFFLNFpBJTJGMjAyNTA1MDclMkZ1cy1lYXN0LTElMkZzMyUyRmF3czRfcmVxdWVzdCZYLUFtei1EYXRlPTIwMjUwNTA3VDIyMDgwMlomWC1BbXotRXhwaXJlcz0zMDAmWC1BbXotU2lnbmF0dXJlPTdiZjM4NzczYTFhYmFhNjgwMWJlYjgwNTkzYjA3ZWFlNTkwNzBiYTlhNTAzM2Y0MWM1MWQ0MzY1YmEyNmE4NjAmWC1BbXotU2lnbmVkSGVhZGVycz1ob3N0In0.EOEVWLDMx5CT-Gg5UhBmdMIYT49IZPKrrA9VL7N-pBQ)](https://private-user-images.githubusercontent.com/46939827/413668576-b591f1fe-1c44-4d82-b6e5-d166590aeab1.png?jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3NDY2NTU5ODIsIm5iZiI6MTc0NjY1NTY4MiwicGF0aCI6Ii80NjkzOTgyNy80MTM2Njg1NzYtYjU5MWYxZmUtMWM0NC00ZDgyLWI2ZTUtZDE2NjU5MGFlYWIxLnBuZz9YLUFtei1BbGdvcml0aG09QVdTNC1ITUFDLVNIQTI1NiZYLUFtei1DcmVkZW50aWFsPUFLSUFWQ09EWUxTQTUzUFFLNFpBJTJGMjAyNTA1MDclMkZ1cy1lYXN0LTElMkZzMyUyRmF3czRfcmVxdWVzdCZYLUFtei1EYXRlPTIwMjUwNTA3VDIyMDgwMlomWC1BbXotRXhwaXJlcz0zMDAmWC1BbXotU2lnbmF0dXJlPTdiZjM4NzczYTFhYmFhNjgwMWJlYjgwNTkzYjA3ZWFlNTkwNzBiYTlhNTAzM2Y0MWM1MWQ0MzY1YmEyNmE4NjAmWC1BbXotU2lnbmVkSGVhZGVycz1ob3N0In0.EOEVWLDMx5CT-Gg5UhBmdMIYT49IZPKrrA9VL7N-pBQ) [![](https://private-user-images.githubusercontent.com/46939827/413668612-96e81b08-6993-4a5e-96d0-3b05b50fbe44.png?jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3NDY2NTU5ODIsIm5iZiI6MTc0NjY1NTY4MiwicGF0aCI6Ii80NjkzOTgyNy80MTM2Njg2MTItOTZlODFiMDgtNjk5My00YTVlLTk2ZDAtM2IwNWI1MGZiZTQ0LnBuZz9YLUFtei1BbGdvcml0aG09QVdTNC1ITUFDLVNIQTI1NiZYLUFtei1DcmVkZW50aWFsPUFLSUFWQ09EWUxTQTUzUFFLNFpBJTJGMjAyNTA1MDclMkZ1cy1lYXN0LTElMkZzMyUyRmF3czRfcmVxdWVzdCZYLUFtei1EYXRlPTIwMjUwNTA3VDIyMDgwMlomWC1BbXotRXhwaXJlcz0zMDAmWC1BbXotU2lnbmF0dXJlPWJkNTUxODJiMDZhN2I2MDAxYzZlNzIyOTAzYTgwZDg3ZDFlYWM3ODM1YWY0Mzg5MDJjNDY0NzJhYjU4ZTAzMmEmWC1BbXotU2lnbmVkSGVhZGVycz1ob3N0In0.rqM3YOwrYdBCiwbBbEvalj7Tsfl-XWqgD1K9PeE46tI)](https://private-user-images.githubusercontent.com/46939827/413668612-96e81b08-6993-4a5e-96d0-3b05b50fbe44.png?jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3NDY2NTU5ODIsIm5iZiI6MTc0NjY1NTY4MiwicGF0aCI6Ii80NjkzOTgyNy80MTM2Njg2MTItOTZlODFiMDgtNjk5My00YTVlLTk2ZDAtM2IwNWI1MGZiZTQ0LnBuZz9YLUFtei1BbGdvcml0aG09QVdTNC1ITUFDLVNIQTI1NiZYLUFtei1DcmVkZW50aWFsPUFLSUFWQ09EWUxTQTUzUFFLNFpBJTJGMjAyNTA1MDclMkZ1cy1lYXN0LTElMkZzMyUyRmF3czRfcmVxdWVzdCZYLUFtei1EYXRlPTIwMjUwNTA3VDIyMDgwMlomWC1BbXotRXhwaXJlcz0zMDAmWC1BbXotU2lnbmF0dXJlPWJkNTUxODJiMDZhN2I2MDAxYzZlNzIyOTAzYTgwZDg3ZDFlYWM3ODM1YWY0Mzg5MDJjNDY0NzJhYjU4ZTAzMmEmWC1BbXotU2lnbmVkSGVhZGVycz1ob3N0In0.rqM3YOwrYdBCiwbBbEvalj7Tsfl-XWqgD1K9PeE46tI)

##### New Tag Colors + UI

- feat: expanded tag color system by [@CyanVoxel](https://github.com/CyanVoxel) in [#709](https://github.com/TagStudioDev/TagStudio/pull/709)
- fix(ui): use correct pink tag color by [@CyanVoxel](https://github.com/CyanVoxel) in [431efe4](https://github.com/TagStudioDev/TagStudio/commit/431efe4fe93213141c763e59ca9887215766fd42)
- fix(ui): use consistent tag outline colors by [@CyanVoxel](https://github.com/CyanVoxel) in [020a73d](https://github.com/TagStudioDev/TagStudio/commit/020a73d095c74283d6c80426d3c3db8874409952)

[![Screenshot 2025-01-04 at 04 23 43](https://private-user-images.githubusercontent.com/46939827/408753168-c8f82d89-ad7e-4be6-830e-b91cdc58e4c6.png?jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3NDY2NTU5ODIsIm5iZiI6MTc0NjY1NTY4MiwicGF0aCI6Ii80NjkzOTgyNy80MDg3NTMxNjgtYzhmODJkODktYWQ3ZS00YmU2LTgzMGUtYjkxY2RjNThlNGM2LnBuZz9YLUFtei1BbGdvcml0aG09QVdTNC1ITUFDLVNIQTI1NiZYLUFtei1DcmVkZW50aWFsPUFLSUFWQ09EWUxTQTUzUFFLNFpBJTJGMjAyNTA1MDclMkZ1cy1lYXN0LTElMkZzMyUyRmF3czRfcmVxdWVzdCZYLUFtei1EYXRlPTIwMjUwNTA3VDIyMDgwMlomWC1BbXotRXhwaXJlcz0zMDAmWC1BbXotU2lnbmF0dXJlPTk1OWNhZGNkOTRiZGJhNGQxNGU1MjJhYTViYTc0OTNiNTA4NDUxODA4OTYxZDUwNzYxZDhmYWZkNzM4NTE3N2QmWC1BbXotU2lnbmVkSGVhZGVycz1ob3N0In0.HLnwHyp3BYg8vXo3BtvqBoOqtpQTI1eykqa-L3chLUk)](https://private-user-images.githubusercontent.com/46939827/408753168-c8f82d89-ad7e-4be6-830e-b91cdc58e4c6.png?jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3NDY2NTU5ODIsIm5iZiI6MTc0NjY1NTY4MiwicGF0aCI6Ii80NjkzOTgyNy80MDg3NTMxNjgtYzhmODJkODktYWQ3ZS00YmU2LTgzMGUtYjkxY2RjNThlNGM2LnBuZz9YLUFtei1BbGdvcml0aG09QVdTNC1ITUFDLVNIQTI1NiZYLUFtei1DcmVkZW50aWFsPUFLSUFWQ09EWUxTQTUzUFFLNFpBJTJGMjAyNTA1MDclMkZ1cy1lYXN0LTElMkZzMyUyRmF3czRfcmVxdWVzdCZYLUFtei1EYXRlPTIwMjUwNTA3VDIyMDgwMlomWC1BbXotRXhwaXJlcz0zMDAmWC1BbXotU2lnbmF0dXJlPTk1OWNhZGNkOTRiZGJhNGQxNGU1MjJhYTViYTc0OTNiNTA4NDUxODA4OTYxZDUwNzYxZDhmYWZkNzM4NTE3N2QmWC1BbXotU2lnbmVkSGVhZGVycz1ob3N0In0.HLnwHyp3BYg8vXo3BtvqBoOqtpQTI1eykqa-L3chLUk)

##### New Tag Alias UI

- fix: preview panel aliases not staying up to date with database by [@DandyDev01](https://github.com/DandyDev01) in [#641](https://github.com/TagStudioDev/TagStudio/pull/641)
- fix: subtags/parent tags & aliases update the UI for building a tag by [@DandyDev01](https://github.com/DandyDev01) in [#534](https://github.com/TagStudioDev/TagStudio/pull/534)

#### Translations

TagStudio now has official translation support! Head to the new settings panel and select from one of the initial languages included. Note that many languages currently have incomplete translations.

Translation hosting generously provided by [Weblate](https://weblate.org/en/). Check out our [project page](https://hosted.weblate.org/projects/tagstudio/) to help translate TagStudio! Thank you to everyone who's helped contribute to the translations so far!

- translations: add string tokens for en.json by [@Bamowen](https://github.com/Bamowen) in [#507](https://github.com/TagStudioDev/TagStudio/pull/507)
- feat: translations by [@Computerdores](https://github.com/Computerdores) in [#662](https://github.com/TagStudioDev/TagStudio/pull/662)
- feat(ui): add language setting by [@CyanVoxel](https://github.com/CyanVoxel) in [#803](https://github.com/TagStudioDev/TagStudio/pull/803)

Initial Languages:

- Chinese (Traditional) (68%)
    - [@brisu](https://github.com/brisu)
- Dutch (35%)
    - [@Pheubel](https://github.com/Pheubel)
- Filipino (43%)
    - [@searinminecraft](https://github.com/searinminecraft)
- French (100%)
    - [@Bamowen](https://github.com/Bamowen), [@alessdangelo](https://github.com/alessdangelo), [@kitsumed](https://github.com/kitsumed), Obscaeris
- German (98%)
    - [@Ryussei](https://github.com/Ryussei), [@Computerdores](https://github.com/Computerdores), Aaron M, [@JoeJoeTV](https://github.com/JoeJoeTV), [@Kurty00](https://github.com/Kurty00)
- Hungarian (100%)
    - [@smileyhead](https://github.com/smileyhead)
- Norwegian Bokmål (16%)
    - [@comradekingu](https://github.com/comradekingu)
- Polish (97%)
    - Anonymous
- Portuguese (Brazil) (64%)
    - [@LoboMetalurgico](https://github.com/LoboMetalurgico), [@SpaceFox1](https://github.com/SpaceFox1), [@DaviMarquezeli](https://github.com/DaviMarquezeli), [@viniciushelder](https://github.com/viniciushelder), Alexander Lennart Formiga Johnsson
- Russian (22%)
    - [@The-Stolas](https://github.com/The-Stolas)
- Spanish (57%)
    - [@gallegonovato](https://github.com/gallegonovato), [@Nginearing](https://github.com/Nginearing), [@noceno](https://github.com/noceno)
- Swedish (24%)
    - [@adampawelec](https://github.com/adampawelec), [@mashed5894](https://github.com/mashed5894)
- Tamil (22%)
    - [@VasigaranAndAngel](https://github.com/VasigaranAndAngel)
- Toki Pona (32%)
    - [@goldstargloww](https://github.com/goldstargloww)
- Turkish (22%)
    - [@Nyghl](https://github.com/Nyghl)

#### Miscellaneous

- feat: about section by [@mashed5894](https://github.com/mashed5894) in [#712](https://github.com/TagStudioDev/TagStudio/pull/712)
- feat(ui): add configurable splash screens by [@CyanVoxel](https://github.com/CyanVoxel) in [#703](https://github.com/TagStudioDev/TagStudio/pull/703)
- feat(ui): show filenames in thumbnail grid by [@CyanVoxel](https://github.com/CyanVoxel) in [#633](https://github.com/TagStudioDev/TagStudio/pull/633)
- feat(about): clickable links to docs/discord/etc in about modal by [@SkeleyM](https://github.com/SkeleyM) in [#799](https://github.com/TagStudioDev/TagStudio/pull/799)

### Fixed

- fix(ui): display all tags in panel during empty search by [@samuellieberman](https://github.com/samuellieberman) in [#328](https://github.com/TagStudioDev/TagStudio/pull/328)
- fix: avoid `KeyError` in `add_folders_to_tree()` (fix [#346](https://github.com/TagStudioDev/TagStudio/issues/346)) by [@CyanVoxel](https://github.com/CyanVoxel) in [#347](https://github.com/TagStudioDev/TagStudio/pull/347)
- fix: error on closing library by [@yedpodtrzitko](https://github.com/yedpodtrzitko) in [#484](https://github.com/TagStudioDev/TagStudio/pull/484)
- fix: resolution info [#550](https://github.com/TagStudioDev/TagStudio/issues/550) by [@Roc25](https://github.com/Roc25) in [#551](https://github.com/TagStudioDev/TagStudio/pull/551)
- fix: remove queued thumnail jobs when closing library by [@yedpodtrzitko](https://github.com/yedpodtrzitko) in [#583](https://github.com/TagStudioDev/TagStudio/pull/583)
- fix: use absolute ffprobe path on macos (Fix [#511](https://github.com/TagStudioDev/TagStudio/issues/511)) by [@CyanVoxel](https://github.com/CyanVoxel) in [#629](https://github.com/TagStudioDev/TagStudio/pull/629)
- fix(ui): prevent duplicate parent tags in UI by [@SkeleyM](https://github.com/SkeleyM) in [#665](https://github.com/TagStudioDev/TagStudio/pull/665)
- fix: fix -o flag not working if path has whitespace around it by [@python357-1](https://github.com/python357-1) in [#670](https://github.com/TagStudioDev/TagStudio/pull/670)
- fix: better file opening compatibility with non-ascii filenames by [@SkeleyM](https://github.com/SkeleyM) in [#667](https://github.com/TagStudioDev/TagStudio/pull/667)
- fix: restore environment before launching external programs by [@mashed5894](https://github.com/mashed5894) in [#707](https://github.com/TagStudioDev/TagStudio/pull/707)
- fix: have pydub use known ffmpeg + ffprobe locations by [@CyanVoxel](https://github.com/CyanVoxel) in [#724](https://github.com/TagStudioDev/TagStudio/pull/724)
- fix: add ".DS_Store" to `GLOBAL_IGNORE_SET` by [@CyanVoxel](https://github.com/CyanVoxel) in [b72a2f2](https://github.com/TagStudioDev/TagStudio/commit/b72a2f233141db4db6aa6be8796b626ebd3f0756)
- fix: don't add "._" files to libraries by [@CyanVoxel](https://github.com/CyanVoxel) in [eb1f634](https://github.com/TagStudioDev/TagStudio/commit/eb1f634d386cd8a5ecee1e6ff6a0b7d8811550fa)

### Changed

#### SQLite Save File Format

This was the main focus of this update, and where the majority of development time and resources have been spent since v9.4. These changes include everything that was done to migrate from the JSON format to SQLite starting from the initial SQLite PR, while re-implementing every feature from v9.4 as the initial SQLite PR was based on v9.3.x at the time.

- refactor!: use SQLite and SQLAlchemy for database backend by [@yedpodtrzitko](https://github.com/yedpodtrzitko) in [#332](https://github.com/TagStudioDev/TagStudio/pull/332)
- feat: make search results more ergonomic by [@yedpodtrzitko](https://github.com/yedpodtrzitko) in [#498](https://github.com/TagStudioDev/TagStudio/pull/498)
- feat: store `Entry` suffix separately by [@yedpodtrzitko](https://github.com/yedpodtrzitko) in [#503](https://github.com/TagStudioDev/TagStudio/pull/503)
- feat: port thumbnail ([#390](https://github.com/TagStudioDev/TagStudio/pull/390)) and related features to v9.5 by [@CyanVoxel](https://github.com/CyanVoxel) in [#522](https://github.com/TagStudioDev/TagStudio/pull/522)
- fix: don't check db version with new library by [@yedpodtrzitko](https://github.com/yedpodtrzitko) in [#536](https://github.com/TagStudioDev/TagStudio/pull/536)
- fix(ui): update ui when removing fields by [@DandyDev01](https://github.com/DandyDev01) in [#560](https://github.com/TagStudioDev/TagStudio/pull/560)
- feat(parity): backend for aliases and parent tags by [@DandyDev01](https://github.com/DandyDev01) in [#596](https://github.com/TagStudioDev/TagStudio/pull/596)
- fix: "open in explorer" opens correct folder by [@KirilBourakov](https://github.com/KirilBourakov) in [#603](https://github.com/TagStudioDev/TagStudio/pull/603)
- fix: ui/ux parity fixes for thumbnails and files by [@CyanVoxel](https://github.com/CyanVoxel) in [#608](https://github.com/TagStudioDev/TagStudio/pull/608)
- feat(parity): migrate json libraries to sqlite by [@CyanVoxel](https://github.com/CyanVoxel) in [#604](https://github.com/TagStudioDev/TagStudio/pull/604)
- fix: clear all setting values when opening a library by [@VasigaranAndAngel](https://github.com/VasigaranAndAngel) in [#622](https://github.com/TagStudioDev/TagStudio/pull/622)
- fix: remove/rework windows path tests by [@VasigaranAndAngel](https://github.com/VasigaranAndAngel) in [#625](https://github.com/TagStudioDev/TagStudio/pull/625)
- fix: add check to see if library is loaded in filter_items by [@Roc25](https://github.com/Roc25) in [#547](https://github.com/TagStudioDev/TagStudio/pull/547)
- fix: multiple macro errors by [@Computerdores](https://github.com/Computerdores) in [#612](https://github.com/TagStudioDev/TagStudio/pull/612)
- fix: don't allow blank tag alias values in db by [@CyanVoxel](https://github.com/CyanVoxel) in [#628](https://github.com/TagStudioDev/TagStudio/pull/628)
- feat: Reimplement drag drop files on sql migration by [@seakrueger](https://github.com/seakrueger) in [#528](https://github.com/TagStudioDev/TagStudio/pull/528)
- fix: stop sqlite db from being updated while running tests by [@python357-1](https://github.com/python357-1) in [#648](https://github.com/TagStudioDev/TagStudio/pull/648)
- fix: enter/return adds top result tag by [@SkeleyM](https://github.com/SkeleyM) in [#651](https://github.com/TagStudioDev/TagStudio/pull/651)
- fix: show correct unlinked files count by [@SkeleyM](https://github.com/SkeleyM) in [#653](https://github.com/TagStudioDev/TagStudio/pull/653)
- feat: implement parent tag search by [@Computerdores](https://github.com/Computerdores) in [#673](https://github.com/TagStudioDev/TagStudio/pull/673)
- fix: only close add tag menu with no search by [@SkeleyM](https://github.com/SkeleyM) in [#685](https://github.com/TagStudioDev/TagStudio/pull/685)
- fix: drag and drop no longer resets by [@SkeleyM](https://github.com/SkeleyM) in [#710](https://github.com/TagStudioDev/TagStudio/pull/710)
- feat(ui): port "create and add tag" to main branch by [@SkeleyM](https://github.com/SkeleyM) in [#711](https://github.com/TagStudioDev/TagStudio/pull/711)
- fix: don't add default title field, use proper phrasing for adding files by [@CyanVoxel](https://github.com/CyanVoxel) in [#701](https://github.com/TagStudioDev/TagStudio/pull/701)
- fix: preview panel + main window fixes and optimizations by [@CyanVoxel](https://github.com/CyanVoxel) in [#700](https://github.com/TagStudioDev/TagStudio/pull/700)
- fix: sort tag results by [@mashed5894](https://github.com/mashed5894) in [#721](https://github.com/TagStudioDev/TagStudio/pull/721)
- fix: restore opening last library on startup by [@SkeleyM](https://github.com/SkeleyM) in [#729](https://github.com/TagStudioDev/TagStudio/pull/729)
- fix(ui): don't always create tag on enter by [@SkeleyM](https://github.com/SkeleyM) in [#731](https://github.com/TagStudioDev/TagStudio/pull/731)
- fix: use tag aliases in tag search by [@CyanVoxel](https://github.com/CyanVoxel) in [#726](https://github.com/TagStudioDev/TagStudio/pull/726)
- fix: keep initial id order in `get_entries_full()` by [@CyanVoxel](https://github.com/CyanVoxel) in [#736](https://github.com/TagStudioDev/TagStudio/pull/736)
- fix: always catch db mismatch by [@CyanVoxel](https://github.com/CyanVoxel) in [#738](https://github.com/TagStudioDev/TagStudio/pull/738)
- fix: relink unlinked entry to existing entry without sql error by [@mashed5894](https://github.com/mashed5894) in [#730](https://github.com/TagStudioDev/TagStudio/issues/730)
- fix: refactor and fix bugs with missing_files.py by [@CyanVoxel](https://github.com/CyanVoxel) in [#739](https://github.com/TagStudioDev/TagStudio/pull/739)
- fix: dragging files references correct entry IDs [@CyanVoxel](https://github.com/CyanVoxel) in [44ff17c](https://github.com/TagStudioDev/TagStudio/commit/44ff17c0b3f05570e356c112f005dbc14c7cc05d)
- ui: port splash screen from Alpha-v9.4 by [@CyanVoxel](https://github.com/CyanVoxel) in [af760ee](https://github.com/TagStudioDev/TagStudio/commit/af760ee61a523c84bab0fb03a68d7465866d0e05)
- fix: tags created from tag database now add aliases by [@CyanVoxel](https://github.com/CyanVoxel) in [2903dd2](https://github.com/TagStudioDev/TagStudio/commit/2903dd22c45c02498687073d075bb88886de6b62)
- fix: check for tag name parity during JSON migration by [@CyanVoxel](https://github.com/CyanVoxel) in [#748](https://github.com/TagStudioDev/TagStudio/pull/748)
- feat(ui): re-implement tag display names on sql by [@CyanVoxel](https://github.com/CyanVoxel) in [#747](https://github.com/TagStudioDev/TagStudio/pull/747)
- fix(ui): restore Windows accent color on PySide 6.8.0.1 by [@CyanVoxel](https://github.com/CyanVoxel) in [#755](https://github.com/TagStudioDev/TagStudio/pull/755)
- fix(ui): (mostly) fix right-click search option on tags by [@CyanVoxel](https://github.com/CyanVoxel) in [#756](https://github.com/TagStudioDev/TagStudio/pull/756)
- feat: copy/paste fields and tags by [@mashed5894](https://github.com/mashed5894) in [#722](https://github.com/TagStudioDev/TagStudio/pull/722)
- perf: optimize query methods and reduce preview panel updates by [@CyanVoxel](https://github.com/CyanVoxel) in [#794](https://github.com/TagStudioDev/TagStudio/pull/794)
- feat: port file trashing ([#409](https://github.com/TagStudioDev/TagStudio/pull/409)) to v9.5 by [@CyanVoxel](https://github.com/CyanVoxel) in [#792](https://github.com/TagStudioDev/TagStudio/pull/792)
- fix: prevent future library versions from being opened by [@CyanVoxel](https://github.com/CyanVoxel) in [bcf3b2f](https://github.com/TagStudioDev/TagStudio/commit/bcf3b2f96bc8b876ca4b0c1d1882ce14a190f249)

#### UI/UX

- feat(ui): pre-select default tag name in `BuildTagPanel` by [@Cool-Game-Dev](https://github.com/Cool-Game-Dev) in [#592](https://github.com/TagStudioDev/TagStudio/pull/592)
- feat(ui): keyboard navigation for editing tags by [@Computerdores](https://github.com/Computerdores) in [#407](https://github.com/TagStudioDev/TagStudio/pull/407)
- feat(ui): use tag query as default new tag name by [@CyanVoxel](https://github.com/CyanVoxel) in [29c0dfd](https://github.com/TagStudioDev/TagStudio/commit/29c0dfdb2d88e8f473e27c7f1fe7ede6e5bd0feb)
- feat(ui): shortcut to add tags to selected entries; change click behavior of tags to edit by [@CyanVoxel](https://github.com/CyanVoxel) in [#749](https://github.com/TagStudioDev/TagStudio/pull/749)
- fix(ui): use consistent dark mode colors for all systems by [@CyanVoxel](https://github.com/CyanVoxel) in [#752](https://github.com/TagStudioDev/TagStudio/pull/752)
- fix(ui): use camera white balance for raw images by [@CyanVoxel](https://github.com/CyanVoxel) in [6ee5304](https://github.com/TagStudioDev/TagStudio/commit/6ee5304b52f217af0f5df543fcb389649203d6b2)
- Mixed field editing has been limited due to various bugs in both the JSON and SQL implementations. This will be re-implemented in a future release.
- fix(ui): improve tagging ux by [@CyanVoxel](https://github.com/CyanVoxel) in [#633](https://github.com/TagStudioDev/TagStudio/pull/633)
- fix(ui): hide library actions when no library is open by [@CyanVoxel](https://github.com/CyanVoxel) in [#787](https://github.com/TagStudioDev/TagStudio/pull/787)
- refactor(ui): recycle tag list in TagSearchPanel by [@CyanVoxel](https://github.com/CyanVoxel) in [#788](https://github.com/TagStudioDev/TagStudio/pull/788)
    - feat(ui): add tag view limit dropdown
- fix(ui): expand usage of esc and enter for modals by [@CyanVoxel](https://github.com/CyanVoxel) in [#793](https://github.com/TagStudioDev/TagStudio/pull/793)

#### Performance

- feat: improve performance of "Delete Missing Entries" by [@Toby222](https://github.com/Toby222) and [@Computerdores](https://github.com/Computerdores) in [#696](https://github.com/TagStudioDev/TagStudio/pull/696)

#### Internal Changes

- refactor: combine open launch args by [@UnusualEgg](https://github.com/UnusualEgg) in [#364](https://github.com/TagStudioDev/TagStudio/pull/364)
- feat: add date_created, date_modified, and date_added columns to entries table by [@CyanVoxel](https://github.com/CyanVoxel) in [#740](https://github.com/TagStudioDev/TagStudio/pull/740)

## [9.5.0 Pre-Release 4] - 2025-02-17

### Added

#### Custom User-Created Tag Colors ([@CyanVoxel](https://github.com/CyanVoxel) in [#801](https://github.com/TagStudioDev/TagStudio/pull/801))

Create your own custom tag colors via the new Tag Color Manager! Tag colors are assigned a namespace (group) and include a name, primary color, and optional secondary color. By default the secondary color is used for the tag text color, but this can also be toggled to apply to the border color as well!

[![Screenshot 2025-02-16 at 17 34 22](https://private-user-images.githubusercontent.com/46939827/413668576-b591f1fe-1c44-4d82-b6e5-d166590aeab1.png?jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3NDY2NTQ3MTYsIm5iZiI6MTc0NjY1NDQxNiwicGF0aCI6Ii80NjkzOTgyNy80MTM2Njg1NzYtYjU5MWYxZmUtMWM0NC00ZDgyLWI2ZTUtZDE2NjU5MGFlYWIxLnBuZz9YLUFtei1BbGdvcml0aG09QVdTNC1ITUFDLVNIQTI1NiZYLUFtei1DcmVkZW50aWFsPUFLSUFWQ09EWUxTQTUzUFFLNFpBJTJGMjAyNTA1MDclMkZ1cy1lYXN0LTElMkZzMyUyRmF3czRfcmVxdWVzdCZYLUFtei1EYXRlPTIwMjUwNTA3VDIxNDY1NlomWC1BbXotRXhwaXJlcz0zMDAmWC1BbXotU2lnbmF0dXJlPTBhYzUwZmExZjRlMWI4YzJjZTZmNDRiMjFiN2ZlZjg4ZjE3MWM4NzBkNmJlZWNjMzg2OWU5YTE2OWVmZTA2YTEmWC1BbXotU2lnbmVkSGVhZGVycz1ob3N0In0.nEs6bk1euKTEkIqDipNJBrXHbHegb3PHWoW3tKI02_8)](https://private-user-images.githubusercontent.com/46939827/413668576-b591f1fe-1c44-4d82-b6e5-d166590aeab1.png?jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3NDY2NTQ3MTYsIm5iZiI6MTc0NjY1NDQxNiwicGF0aCI6Ii80NjkzOTgyNy80MTM2Njg1NzYtYjU5MWYxZmUtMWM0NC00ZDgyLWI2ZTUtZDE2NjU5MGFlYWIxLnBuZz9YLUFtei1BbGdvcml0aG09QVdTNC1ITUFDLVNIQTI1NiZYLUFtei1DcmVkZW50aWFsPUFLSUFWQ09EWUxTQTUzUFFLNFpBJTJGMjAyNTA1MDclMkZ1cy1lYXN0LTElMkZzMyUyRmF3czRfcmVxdWVzdCZYLUFtei1EYXRlPTIwMjUwNTA3VDIxNDY1NlomWC1BbXotRXhwaXJlcz0zMDAmWC1BbXotU2lnbmF0dXJlPTBhYzUwZmExZjRlMWI4YzJjZTZmNDRiMjFiN2ZlZjg4ZjE3MWM4NzBkNmJlZWNjMzg2OWU5YTE2OWVmZTA2YTEmWC1BbXotU2lnbmVkSGVhZGVycz1ob3N0In0.nEs6bk1euKTEkIqDipNJBrXHbHegb3PHWoW3tKI02_8)

[![Screenshot 2025-02-16 at 17 32 56](https://private-user-images.githubusercontent.com/46939827/413668612-96e81b08-6993-4a5e-96d0-3b05b50fbe44.png?jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3NDY2NTQ3MTYsIm5iZiI6MTc0NjY1NDQxNiwicGF0aCI6Ii80NjkzOTgyNy80MTM2Njg2MTItOTZlODFiMDgtNjk5My00YTVlLTk2ZDAtM2IwNWI1MGZiZTQ0LnBuZz9YLUFtei1BbGdvcml0aG09QVdTNC1ITUFDLVNIQTI1NiZYLUFtei1DcmVkZW50aWFsPUFLSUFWQ09EWUxTQTUzUFFLNFpBJTJGMjAyNTA1MDclMkZ1cy1lYXN0LTElMkZzMyUyRmF3czRfcmVxdWVzdCZYLUFtei1EYXRlPTIwMjUwNTA3VDIxNDY1NlomWC1BbXotRXhwaXJlcz0zMDAmWC1BbXotU2lnbmF0dXJlPTlhOGU2NjA2ZjRhMjNjZGYxZDE1ZWYzZmVjN2RjM2Q0YzA1NTcwZGE5OGFkMjc2MDIzMTk1YTFlYjY2NTQxNmImWC1BbXotU2lnbmVkSGVhZGVycz1ob3N0In0.VD2trGcVKQVKUpzVog1UhZUM0JRcEHUhwGCiHpZ8zF0)](https://private-user-images.githubusercontent.com/46939827/413668612-96e81b08-6993-4a5e-96d0-3b05b50fbe44.png?jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3NDY2NTQ3MTYsIm5iZiI6MTc0NjY1NDQxNiwicGF0aCI6Ii80NjkzOTgyNy80MTM2Njg2MTItOTZlODFiMDgtNjk5My00YTVlLTk2ZDAtM2IwNWI1MGZiZTQ0LnBuZz9YLUFtei1BbGdvcml0aG09QVdTNC1ITUFDLVNIQTI1NiZYLUFtei1DcmVkZW50aWFsPUFLSUFWQ09EWUxTQTUzUFFLNFpBJTJGMjAyNTA1MDclMkZ1cy1lYXN0LTElMkZzMyUyRmF3czRfcmVxdWVzdCZYLUFtei1EYXRlPTIwMjUwNTA3VDIxNDY1NlomWC1BbXotRXhwaXJlcz0zMDAmWC1BbXotU2lnbmF0dXJlPTlhOGU2NjA2ZjRhMjNjZGYxZDE1ZWYzZmVjN2RjM2Q0YzA1NTcwZGE5OGFkMjc2MDIzMTk1YTFlYjY2NTQxNmImWC1BbXotU2lnbmVkSGVhZGVycz1ob3N0In0.VD2trGcVKQVKUpzVog1UhZUM0JRcEHUhwGCiHpZ8zF0)

#### Translations

TagStudio now has official translation support! Head to the new settings panel and select from one of the initial languages included. Note that many languages currently have incomplete translations.

Translation hosting generously provided by [Weblate](https://weblate.org/en/). Check out our [project page](https://hosted.weblate.org/projects/tagstudio/) to help translate TagStudio! Thank you to everyone who's helped contribute to the translations so far!

- translations: add string tokens for en.json by [@Bamowen](https://github.com/Bamowen) in [#507](https://github.com/TagStudioDev/TagStudio/pull/507)
- feat: translations by [@Computerdores](https://github.com/Computerdores) in [#662](https://github.com/TagStudioDev/TagStudio/pull/662)
- feat(ui): add language setting by [@CyanVoxel](https://github.com/CyanVoxel) in [#803](https://github.com/TagStudioDev/TagStudio/pull/803)

Initial Languages:

- Chinese (Traditional) (68%)
    - [@brisu](https://github.com/brisu)
- Dutch (35%)
    - [@Pheubel](https://github.com/Pheubel)
- Filipino (15%)
    - [@searinminecraft](https://github.com/searinminecraft)
- French (89%)
    - [@Bamowen](https://github.com/Bamowen), [@alessdangelo](https://github.com/alessdangelo), [@kitsumed](https://github.com/kitsumed), Obscaeris
- German (73%)
    - [@Ryussei](https://github.com/Ryussei), [@Computerdores](https://github.com/Computerdores), Aaron M
- Hungarian (89%)
    - [@smileyhead](https://github.com/smileyhead)
- Norwegian Bokmål (16%)
    - [@comradekingu](https://github.com/comradekingu)
- Polish (76%)
    - Anonymous
- Portuguese (Brazil) (22%)
    - [@LoboMetalurgico](https://github.com/LoboMetalurgico), [@SpaceFox1](https://github.com/SpaceFox1)
- Russian (22%)
    - [@The-Stolas](https://github.com/The-Stolas)
- Spanish (46%)
    - [@gallegonovato](https://github.com/gallegonovato), [@Nginearing](https://github.com/Nginearing), [@noceno](https://github.com/noceno)
- Swedish (24%)
    - [@adampawelec](https://github.com/adampawelec), [@mashed5894](https://github.com/mashed5894)
- Tamil (22%)
    - [@VasigaranAndAngel](https://github.com/VasigaranAndAngel)
- Toki Pona (32%)
    - [@goldstargloww](https://github.com/goldstargloww)
- Turkish (22%)
    - [@Nyghl](https://github.com/Nyghl)

### Fixed

- feat(about): clickable links to docs/discord/etc in about modal by [@SkeleyM](https://github.com/SkeleyM) in [#799](https://github.com/TagStudioDev/TagStudio/pull/799)

### Internal Changes

This release increases the internal `DB_VERSION` to 8. Libraries created with this version of TagStudio can still be opened in earlier v9.5.0 pre-release versions, however the behavior of custom color borders will not be identical to the behavior in this PR. Otherwise it should still be possible to use any custom colors created in this version in these earlier pre-releases (but not really recommended).

## [9.5.0 Pre-Release 3] - 2025-02-10

### Added

##### [#743](https://github.com/TagStudioDev/TagStudio/pull/743) by [@CyanVoxel](https://github.com/CyanVoxel)

Added "Smartcase" and Globless Path Search

- `path: temp`: Returns all paths that have "temp" **(Case insensitive)** somewhere in the name.
    
- `path: Temp`: Returns all paths that have "Temp" **(Case sensitive)** somewhere in the name.
    

Glob Patterns w/ Smartcase

- `path: *temp*`: Returns all paths that have "temp" **(Case insensitive)** somewhere in the name.
    
- `path: *Temp*`: Returns all paths that have "Temp" **(Case sensitive)** somewhere in the name.
    
- `path: temp*`: Returns all paths that start with "temp" **(Case insensitive)** somewhere in the name.
    
- `path: Temp*`: Returns all paths that start with "Temp" **(Case sensitive)** somewhere in the name.
    
- `path: *temp`: Returns all paths that end with "temp" **(Case insensitive)** somewhere in the name.
    
- `path: *TEmP`: Returns all paths that end with "TEmP" **(Case sensitive)** somewhere in the name.
    

##### [#788](https://github.com/TagStudioDev/TagStudio/pull/788) by [@CyanVoxel](https://github.com/CyanVoxel)

- Added a "View Limit" dropdown to tag search boxes to limit the number of on-screen tags. Previously this limit was hardcoded to 100, but now options range from 25 to unlimited.  
    [![](https://private-user-images.githubusercontent.com/46939827/411701461-7f7da065-888d-4fe5-a4e7-f99447bcce98.png?jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3NDY2NTQ3MTYsIm5iZiI6MTc0NjY1NDQxNiwicGF0aCI6Ii80NjkzOTgyNy80MTE3MDE0NjEtN2Y3ZGEwNjUtODg4ZC00ZmU1LWE0ZTctZjk5NDQ3YmNjZTk4LnBuZz9YLUFtei1BbGdvcml0aG09QVdTNC1ITUFDLVNIQTI1NiZYLUFtei1DcmVkZW50aWFsPUFLSUFWQ09EWUxTQTUzUFFLNFpBJTJGMjAyNTA1MDclMkZ1cy1lYXN0LTElMkZzMyUyRmF3czRfcmVxdWVzdCZYLUFtei1EYXRlPTIwMjUwNTA3VDIxNDY1NlomWC1BbXotRXhwaXJlcz0zMDAmWC1BbXotU2lnbmF0dXJlPWVlZjVhZjYyNWQwY2FmMjhmMWI1MzI5ZDdjYWMxMmM0N2M0Nzc4MmY1YjE0NWY4MjVhZmIyMDI1NzQzY2M0YmQmWC1BbXotU2lnbmVkSGVhZGVycz1ob3N0In0.a3xUaH5r3HsDgOb6-lo3T-xSRRSy7dDOrln5i62KFP8)](https://private-user-images.githubusercontent.com/46939827/411701461-7f7da065-888d-4fe5-a4e7-f99447bcce98.png?jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3NDY2NTQ3MTYsIm5iZiI6MTc0NjY1NDQxNiwicGF0aCI6Ii80NjkzOTgyNy80MTE3MDE0NjEtN2Y3ZGEwNjUtODg4ZC00ZmU1LWE0ZTctZjk5NDQ3YmNjZTk4LnBuZz9YLUFtei1BbGdvcml0aG09QVdTNC1ITUFDLVNIQTI1NiZYLUFtei1DcmVkZW50aWFsPUFLSUFWQ09EWUxTQTUzUFFLNFpBJTJGMjAyNTA1MDclMkZ1cy1lYXN0LTElMkZzMyUyRmF3czRfcmVxdWVzdCZYLUFtei1EYXRlPTIwMjUwNTA3VDIxNDY1NlomWC1BbXotRXhwaXJlcz0zMDAmWC1BbXotU2lnbmF0dXJlPWVlZjVhZjYyNWQwY2FmMjhmMWI1MzI5ZDdjYWMxMmM0N2M0Nzc4MmY1YjE0NWY4MjVhZmIyMDI1NzQzY2M0YmQmWC1BbXotU2lnbmVkSGVhZGVycz1ob3N0In0.a3xUaH5r3HsDgOb6-lo3T-xSRRSy7dDOrln5i62KFP8)

### Changed

- fix(ui): expand usage of esc and enter for modals by [@CyanVoxel](https://github.com/CyanVoxel) in [#793](https://github.com/TagStudioDev/TagStudio/pull/793)
- perf: optimize query methods and reduce preview panel updates by [@CyanVoxel](https://github.com/CyanVoxel) in [#794](https://github.com/TagStudioDev/TagStudio/pull/794)

##### [#788](https://github.com/TagStudioDev/TagStudio/pull/788) by [@CyanVoxel](https://github.com/CyanVoxel)

- Improved performance of tag search boxes, including the tag manager

### Fixed

- fix(ui): hide library actions when no library is open by [@CyanVoxel](https://github.com/CyanVoxel) in [#787](https://github.com/TagStudioDev/TagStudio/pull/787)
- feat: port file trashing ([#409](https://github.com/TagStudioDev/TagStudio/pull/409)) to v9.5 by [@CyanVoxel](https://github.com/CyanVoxel) in [#792](https://github.com/TagStudioDev/TagStudio/pull/792)

### Docs

- Added references to alternative POSIX shells, as well as pyenv to CONTRIBUTING.md by [@ChloeZamorano](https://github.com/ChloeZamorano) in [#791](https://github.com/TagStudioDev/TagStudio/pull/791)
## [9.5.0 Pre-Release 2] - 2025-02-03

### Added

##### [#784](https://github.com/TagStudioDev/TagStudio/pull/784) by [@CyanVoxel](https://github.com/CyanVoxel)

- Add Ctrl+M shortcut to open the "Tag Manager"

### Fixed

- fix: don't wrap field names too early by [@CyanVoxel](https://github.com/CyanVoxel) in [2215403](https://github.com/TagStudioDev/TagStudio/commit/2215403201e3b416a43ead0a322688180af6d71b) and [90a826d](https://github.com/TagStudioDev/TagStudio/commit/90a826d12804b3386a0b9003abb20f23f88ab3be)
- fix: save all tag attributes from "Create & Add" modal by [@SkeleyM](https://github.com/SkeleyM) in [#762](https://github.com/TagStudioDev/TagStudio/pull/762)
- fix: allow tag names with colons in search by [@SkeleyM](https://github.com/SkeleyM) in [#765](https://github.com/TagStudioDev/TagStudio/pull/765)
- fix: catch `ParsingError` by [@CyanVoxel](https://github.com/CyanVoxel) in [#779](https://github.com/TagStudioDev/TagStudio/pull/779)
- fix: patch incorrect description type & invalid disambiguation_id refs by [@CyanVoxel](https://github.com/CyanVoxel) in [#782](https://github.com/TagStudioDev/TagStudio/pull/782)

##### [#784](https://github.com/TagStudioDev/TagStudio/pull/784) by [@CyanVoxel](https://github.com/CyanVoxel)

- Reset tag search box and focus each time a tag search panel is opened
- Include tag parents in tag search results (v9.4 parity)
- Lowercase tag names now get properly sorted with uppercase ones
- Don't include tag display names in "closeness" factor when searching
- Escape "&" characters inside tag names so Qt doesn't treat them as mnemonics
- Set minimum tag width
- Fix "Add Tags" panel missing its window title when accessing from the keyboard shortcut

### Changed

##### [#784](https://github.com/TagStudioDev/TagStudio/pull/784) by [@CyanVoxel](https://github.com/CyanVoxel)

- The "use for disambiguation" button has been moved to the right-hand side of parent tags in order to prevent accidental clicks involving the left-hand "remove tag" button
- Add "Create & Add" button to the bottom of all non-whitespace searches, even if they return some tags
- The awkward "+" button next to tags in the "Add Tags" panel has been removed in favor of clicking on tags themselves
- Improved visual feedback for highlighting, keyboard focusing, and clicking tags
- The clickable area of the "-" button on tags has been increased and has visual feedback when you hover and click it
- You can now tab into the tag search list and add tags with a spacebar press (previously possible but very janky)
- In tag search panels, pressing the Esc key will return your focus to the search bar and highlight your previous query. If the search box is already highlighted, pressing Esc will close the modal
- In modals such as the "Add Tag" and "Edit Tag" panels, pressing Esc will cancel the operation and close the modal

### Internal Changes

- refactor: wrap migration_iterator lambda in a try/except block by [@CyanVoxel](https://github.com/CyanVoxel) in [#773](https://github.com/TagStudioDev/TagStudio/pull/773)

### Docs

- docs: update field and library pages by [@CyanVoxel](https://github.com/CyanVoxel) in [f5ff4d7](https://github.com/TagStudioDev/TagStudio/commit/f5ff4d78c1ad53134e9c64698886aee68c0f1dc1)
- docs: add information about "tag manager" by [@CyanVoxel](https://github.com/CyanVoxel) in [9bdbafa](https://github.com/TagStudioDev/TagStudio/commit/9bdbafa40c4274922f6533b5b5fcee9a4fe43030)
- docs: add note about glob searching in the readme by [@CyanVoxel](https://github.com/CyanVoxel) in [6e402ac](https://github.com/TagStudioDev/TagStudio/commit/6e402ac34d2d60e71fbd36ad234fe3914d5eb8e0)
- docs: add library_search page by [@CyanVoxel](https://github.com/CyanVoxel) in [5be7dfc](https://github.com/TagStudioDev/TagStudio/commit/5be7dfc314b21042c18b2f08893f2b452d12394a)
- docs: docs: add more links to index.md by [@CyanVoxel](https://github.com/CyanVoxel) in [d795889](https://github.com/TagStudioDev/TagStudio/commit/d7958892b7762586837204d686a6a2a993e3c26e)
- docs: fix typo for "category" in usage.md by [@pinheadtf2](https://github.com/pinheadtf2) in [#760](https://github.com/TagStudioDev/TagStudio/pull/760)
- fix(docs): fix screenshot sometimes not rendering by [@SkeleyM](https://github.com/SkeleyM) in [#775](https://github.com/TagStudioDev/TagStudio/pull/775)
## [9.5.0 Pre-Release 1] - 2025-01-31

### Added

#### Overhauled Search Engine

##### Boolean Operators

- feat: implement query language by [@Computerdores](https://github.com/Computerdores) in [#606](https://github.com/TagStudioDev/TagStudio/pull/606)
- feat: optimize AND queries by [@Computerdores](https://github.com/Computerdores) in [#679](https://github.com/TagStudioDev/TagStudio/pull/679)

##### Filetype, Mediatype, and Glob Path Searches

- fix: remove wildcard requirement for tags by [@Tyrannicodin](https://github.com/Tyrannicodin) in [#481](https://github.com/TagStudioDev/TagStudio/pull/481)
- feat: add filetype and mediatype searches by [@python357-1](https://github.com/python357-1) in [#575](https://github.com/TagStudioDev/TagStudio/pull/575)
- feat: make path search use globs by [@python357-1](https://github.com/python357-1) in [#582](https://github.com/TagStudioDev/TagStudio/pull/582)
- feat: implement search equivalence of "jpg" and "jpeg" filetypes by [@Computerdores](https://github.com/Computerdores) in [#649](https://github.com/TagStudioDev/TagStudio/pull/649)

##### Sortable Results

- feat: sort by "date added" in library by [@Computerdores](https://github.com/Computerdores) in [#674](https://github.com/TagStudioDev/TagStudio/pull/674)

##### Autocomplete

- feat: add autocomplete for search engine by [@python357-1](https://github.com/python357-1) in [#586](https://github.com/TagStudioDev/TagStudio/pull/586)

#### Replaced "Tag Fields" with Tag Categories

Instead of tags needing to be added to a tag field type such as "Meta Tags", "Content Tags", or just the "Tags" field, tags are now added directly to file entries with no intermediary step. While tag field types offered a way to further organize tags, it was cumbersome, inflexible, and simply not fully fleshed out. Tag Categories offer all of the previous (intentional) functionality while greatly increasing the ease of use and customization.

- feat!: tag categories by [@CyanVoxel](https://github.com/CyanVoxel) in [#655](https://github.com/TagStudioDev/TagStudio/pull/655)
    
    [![Screenshot 2025-01-04 at 04 23 43](https://private-user-images.githubusercontent.com/46939827/400138597-0b92eca5-db8f-4e3e-954b-1b4f3795f073.png?jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3NDY2NTUwODcsIm5iZiI6MTc0NjY1NDc4NywicGF0aCI6Ii80NjkzOTgyNy80MDAxMzg1OTctMGI5MmVjYTUtZGI4Zi00ZTNlLTk1NGItMWI0ZjM3OTVmMDczLnBuZz9YLUFtei1BbGdvcml0aG09QVdTNC1ITUFDLVNIQTI1NiZYLUFtei1DcmVkZW50aWFsPUFLSUFWQ09EWUxTQTUzUFFLNFpBJTJGMjAyNTA1MDclMkZ1cy1lYXN0LTElMkZzMyUyRmF3czRfcmVxdWVzdCZYLUFtei1EYXRlPTIwMjUwNTA3VDIxNTMwN1omWC1BbXotRXhwaXJlcz0zMDAmWC1BbXotU2lnbmF0dXJlPTM1M2EwNGFjYmJiM2QwZjg2YzNmNTVjMGYwZDJkZGJkZTg5NjZjNDFhNTYyNDE0OGNlOWFhNzRkMzE3MjBkNzEmWC1BbXotU2lnbmVkSGVhZGVycz1ob3N0In0.B5NRZmHygdHlMy2ZnZtHjfOs83jjEliwfxoe3eMBnEQ)](https://private-user-images.githubusercontent.com/46939827/400138597-0b92eca5-db8f-4e3e-954b-1b4f3795f073.png?jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3NDY2NTUwODcsIm5iZiI6MTc0NjY1NDc4NywicGF0aCI6Ii80NjkzOTgyNy80MDAxMzg1OTctMGI5MmVjYTUtZGI4Zi00ZTNlLTk1NGItMWI0ZjM3OTVmMDczLnBuZz9YLUFtei1BbGdvcml0aG09QVdTNC1ITUFDLVNIQTI1NiZYLUFtei1DcmVkZW50aWFsPUFLSUFWQ09EWUxTQTUzUFFLNFpBJTJGMjAyNTA1MDclMkZ1cy1lYXN0LTElMkZzMyUyRmF3czRfcmVxdWVzdCZYLUFtei1EYXRlPTIwMjUwNTA3VDIxNTMwN1omWC1BbXotRXhwaXJlcz0zMDAmWC1BbXotU2lnbmF0dXJlPTM1M2EwNGFjYmJiM2QwZjg2YzNmNTVjMGYwZDJkZGJkZTg5NjZjNDFhNTYyNDE0OGNlOWFhNzRkMzE3MjBkNzEmWC1BbXotU2lnbmVkSGVhZGVycz1ob3N0In0.B5NRZmHygdHlMy2ZnZtHjfOs83jjEliwfxoe3eMBnEQ)

#### Thumbnails and File Previews

##### New Thumbnail Support

- feat: add svg thumbnail support (port [#442](https://github.com/TagStudioDev/TagStudio/pull/442)) by [@Tyrannicodin](https://github.com/Tyrannicodin) and [@CyanVoxel](https://github.com/CyanVoxel) in [#540](https://github.com/TagStudioDev/TagStudio/pull/540)
- feat: add pdf thumbnail support (port [#378](https://github.com/TagStudioDev/TagStudio/pull/378)) by [@Heiholf](https://github.com/Heiholf) and [@CyanVoxel](https://github.com/CyanVoxel) in [#543](https://github.com/TagStudioDev/TagStudio/pull/543)
- feat: add ePub thumbnail support (port [#387](https://github.com/TagStudioDev/TagStudio/pull/387)) by [@Heiholf](https://github.com/Heiholf) and [@CyanVoxel](https://github.com/CyanVoxel) in [#539](https://github.com/TagStudioDev/TagStudio/pull/539)
- feat: add OpenDocument thumbnail support (port [#366](https://github.com/TagStudioDev/TagStudio/pull/366)) by [@Joshua-Beatty](https://github.com/Joshua-Beatty) and [@CyanVoxel](https://github.com/CyanVoxel) in [#545](https://github.com/TagStudioDev/TagStudio/pull/545)
- feat: add JXL thumbnail and animated APNG + WEBP support (port [#344](https://github.com/TagStudioDev/TagStudio/pull/344) and partially port [#357](https://github.com/TagStudioDev/TagStudio/pull/357)) by [@BPplays](https://github.com/BPplays) and [@CyanVoxel](https://github.com/CyanVoxel) in [#549](https://github.com/TagStudioDev/TagStudio/pull/549)
    - fix: catch ImportError for pillow_jxl module by [@CyanVoxel](https://github.com/CyanVoxel) in [a2f9685](https://github.com/TagStudioDev/TagStudio/commit/a2f9685bc0d744ea6f5334c6d2926aad3f6d375a)

##### Audio Playback

- feat: audio playback by [@csponge](https://github.com/csponge) in [#576](https://github.com/TagStudioDev/TagStudio/pull/576)
    - feat(ui): add audio volume slider by [@SkeleyM](https://github.com/SkeleyM) in [#691](https://github.com/TagStudioDev/TagStudio/pull/691)

##### Thumbnail Caching

- feat(ui): add thumbnail caching by [@CyanVoxel](https://github.com/CyanVoxel) in [#694](https://github.com/TagStudioDev/TagStudio/pull/694)

#### Tags

##### Delete Tags _(Finally!)_

- feat: remove and create tags from tag database panel by [@DandyDev01](https://github.com/DandyDev01) in [#569](https://github.com/TagStudioDev/TagStudio/pull/569)

##### New Tag Colors + UI

- feat: expanded tag color system by [@CyanVoxel](https://github.com/CyanVoxel) in [#709](https://github.com/TagStudioDev/TagStudio/pull/709)
- fix(ui): use correct pink tag color by [@CyanVoxel](https://github.com/CyanVoxel) in [431efe4](https://github.com/TagStudioDev/TagStudio/commit/431efe4fe93213141c763e59ca9887215766fd42)
- fix(ui): use consistent tag outline colors by [@CyanVoxel](https://github.com/CyanVoxel) in [020a73d](https://github.com/TagStudioDev/TagStudio/commit/020a73d095c74283d6c80426d3c3db8874409952)

[![Screenshot 2025-01-04 at 04 23 43](https://private-user-images.githubusercontent.com/46939827/408753168-c8f82d89-ad7e-4be6-830e-b91cdc58e4c6.png?jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3NDY2NTUwODcsIm5iZiI6MTc0NjY1NDc4NywicGF0aCI6Ii80NjkzOTgyNy80MDg3NTMxNjgtYzhmODJkODktYWQ3ZS00YmU2LTgzMGUtYjkxY2RjNThlNGM2LnBuZz9YLUFtei1BbGdvcml0aG09QVdTNC1ITUFDLVNIQTI1NiZYLUFtei1DcmVkZW50aWFsPUFLSUFWQ09EWUxTQTUzUFFLNFpBJTJGMjAyNTA1MDclMkZ1cy1lYXN0LTElMkZzMyUyRmF3czRfcmVxdWVzdCZYLUFtei1EYXRlPTIwMjUwNTA3VDIxNTMwN1omWC1BbXotRXhwaXJlcz0zMDAmWC1BbXotU2lnbmF0dXJlPWI3ZDk2MDg5ODVjYzA2ZGU2Njc1ODE5M2U4OWU4ZGMwY2MxNzUzM2M2YmM2ZmRiMTdlOTkyNGM3MjlhMWNiOWUmWC1BbXotU2lnbmVkSGVhZGVycz1ob3N0In0.0RYUWgVW8VFvu2unzdWHtDCE4USYM77OcMvWeZkd8Hs)](https://private-user-images.githubusercontent.com/46939827/408753168-c8f82d89-ad7e-4be6-830e-b91cdc58e4c6.png?jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3NDY2NTUwODcsIm5iZiI6MTc0NjY1NDc4NywicGF0aCI6Ii80NjkzOTgyNy80MDg3NTMxNjgtYzhmODJkODktYWQ3ZS00YmU2LTgzMGUtYjkxY2RjNThlNGM2LnBuZz9YLUFtei1BbGdvcml0aG09QVdTNC1ITUFDLVNIQTI1NiZYLUFtei1DcmVkZW50aWFsPUFLSUFWQ09EWUxTQTUzUFFLNFpBJTJGMjAyNTA1MDclMkZ1cy1lYXN0LTElMkZzMyUyRmF3czRfcmVxdWVzdCZYLUFtei1EYXRlPTIwMjUwNTA3VDIxNTMwN1omWC1BbXotRXhwaXJlcz0zMDAmWC1BbXotU2lnbmF0dXJlPWI3ZDk2MDg5ODVjYzA2ZGU2Njc1ODE5M2U4OWU4ZGMwY2MxNzUzM2M2YmM2ZmRiMTdlOTkyNGM3MjlhMWNiOWUmWC1BbXotU2lnbmVkSGVhZGVycz1ob3N0In0.0RYUWgVW8VFvu2unzdWHtDCE4USYM77OcMvWeZkd8Hs)

##### New Tag Alias UI

- fix: preview panel aliases not staying up to date with database by [@DandyDev01](https://github.com/DandyDev01) in [#641](https://github.com/TagStudioDev/TagStudio/pull/641)
- fix: subtags/parent tags & aliases update the UI for building a tag by [@DandyDev01](https://github.com/DandyDev01) in [#534](https://github.com/TagStudioDev/TagStudio/pull/534)

#### Miscellaneous

- feat: about section by [@mashed5894](https://github.com/mashed5894) in [#712](https://github.com/TagStudioDev/TagStudio/pull/712)
- feat(ui): add configurable splash screens by [@CyanVoxel](https://github.com/CyanVoxel) in [#703](https://github.com/TagStudioDev/TagStudio/pull/703)
- feat(ui): show filenames in thumbnail grid by [@CyanVoxel](https://github.com/CyanVoxel) in [#633](https://github.com/TagStudioDev/TagStudio/pull/633)

### Fixed

- fix(ui): display all tags in panel during empty search by [@samuellieberman](https://github.com/samuellieberman) in [#328](https://github.com/TagStudioDev/TagStudio/pull/328)
- fix: avoid `KeyError` in `add_folders_to_tree()` (fix [#346](https://github.com/TagStudioDev/TagStudio/issues/346)) by [@CyanVoxel](https://github.com/CyanVoxel) in [#347](https://github.com/TagStudioDev/TagStudio/pull/347)
- fix: error on closing library by [@yedpodtrzitko](https://github.com/yedpodtrzitko) in [#484](https://github.com/TagStudioDev/TagStudio/pull/484)
- fix: resolution info [#550](https://github.com/TagStudioDev/TagStudio/issues/550) by [@Roc25](https://github.com/Roc25) in [#551](https://github.com/TagStudioDev/TagStudio/pull/551)
- fix: remove queued thumnail jobs when closing library by [@yedpodtrzitko](https://github.com/yedpodtrzitko) in [#583](https://github.com/TagStudioDev/TagStudio/pull/583)
- fix: use absolute ffprobe path on macos (Fix [#511](https://github.com/TagStudioDev/TagStudio/issues/511)) by [@CyanVoxel](https://github.com/CyanVoxel) in [#629](https://github.com/TagStudioDev/TagStudio/pull/629)
- fix(ui): prevent duplicate parent tags in UI by [@SkeleyM](https://github.com/SkeleyM) in [#665](https://github.com/TagStudioDev/TagStudio/pull/665)
- fix: fix -o flag not working if path has whitespace around it by [@python357-1](https://github.com/python357-1) in [#670](https://github.com/TagStudioDev/TagStudio/pull/670)
- fix: better file opening compatibility with non-ascii filenames by [@SkeleyM](https://github.com/SkeleyM) in [#667](https://github.com/TagStudioDev/TagStudio/pull/667)
- fix: restore environment before launching external programs by [@mashed5894](https://github.com/mashed5894) in [#707](https://github.com/TagStudioDev/TagStudio/pull/707)
- fix: have pydub use known ffmpeg + ffprobe locations by [@CyanVoxel](https://github.com/CyanVoxel) in [#724](https://github.com/TagStudioDev/TagStudio/pull/724)
- fix: add ".DS_Store" to `GLOBAL_IGNORE_SET` by [@CyanVoxel](https://github.com/CyanVoxel) in [b72a2f2](https://github.com/TagStudioDev/TagStudio/commit/b72a2f233141db4db6aa6be8796b626ebd3f0756)
- fix: don't add "._" files to libraries by [@CyanVoxel](https://github.com/CyanVoxel) in [eb1f634](https://github.com/TagStudioDev/TagStudio/commit/eb1f634d386cd8a5ecee1e6ff6a0b7d8811550fa)

### Changed

#### SQLite Save File Format

This was the main focus of this update, and where the majority of development time and resources have been spent since v9.4. These changes include everything that was done to migrate from the JSON format to SQLite starting from the initial SQLite PR, while re-implementing every feature from v9.4 as the initial SQLite PR was based on v9.3.x at the time.

- refactor!: use SQLite and SQLAlchemy for database backend by [@yedpodtrzitko](https://github.com/yedpodtrzitko) in [#332](https://github.com/TagStudioDev/TagStudio/pull/332)
- feat: make search results more ergonomic by [@yedpodtrzitko](https://github.com/yedpodtrzitko) in [#498](https://github.com/TagStudioDev/TagStudio/pull/498)
- feat: store `Entry` suffix separately by [@yedpodtrzitko](https://github.com/yedpodtrzitko) in [#503](https://github.com/TagStudioDev/TagStudio/pull/503)
- feat: port thumbnail ([#390](https://github.com/TagStudioDev/TagStudio/pull/390)) and related features to v9.5 by [@CyanVoxel](https://github.com/CyanVoxel) in [#522](https://github.com/TagStudioDev/TagStudio/pull/522)
- fix: don't check db version with new library by [@yedpodtrzitko](https://github.com/yedpodtrzitko) in [#536](https://github.com/TagStudioDev/TagStudio/pull/536)
- fix(ui): update ui when removing fields by [@DandyDev01](https://github.com/DandyDev01) in [#560](https://github.com/TagStudioDev/TagStudio/pull/560)
- feat(parity): backend for aliases and parent tags by [@DandyDev01](https://github.com/DandyDev01) in [#596](https://github.com/TagStudioDev/TagStudio/pull/596)
- fix: "open in explorer" opens correct folder by [@KirilBourakov](https://github.com/KirilBourakov) in [#603](https://github.com/TagStudioDev/TagStudio/pull/603)
- fix: ui/ux parity fixes for thumbnails and files by [@CyanVoxel](https://github.com/CyanVoxel) in [#608](https://github.com/TagStudioDev/TagStudio/pull/608)
- feat(parity): migrate json libraries to sqlite by [@CyanVoxel](https://github.com/CyanVoxel) in [#604](https://github.com/TagStudioDev/TagStudio/pull/604)
- fix: clear all setting values when opening a library by [@VasigaranAndAngel](https://github.com/VasigaranAndAngel) in [#622](https://github.com/TagStudioDev/TagStudio/pull/622)
- fix: remove/rework windows path tests by [@VasigaranAndAngel](https://github.com/VasigaranAndAngel) in [#625](https://github.com/TagStudioDev/TagStudio/pull/625)
- fix: add check to see if library is loaded in filter_items by [@Roc25](https://github.com/Roc25) in [#547](https://github.com/TagStudioDev/TagStudio/pull/547)
- fix: multiple macro errors by [@Computerdores](https://github.com/Computerdores) in [#612](https://github.com/TagStudioDev/TagStudio/pull/612)
- fix: don't allow blank tag alias values in db by [@CyanVoxel](https://github.com/CyanVoxel) in [#628](https://github.com/TagStudioDev/TagStudio/pull/628)
- feat: Reimplement drag drop files on sql migration by [@seakrueger](https://github.com/seakrueger) in [#528](https://github.com/TagStudioDev/TagStudio/pull/528)
- fix: stop sqlite db from being updated while running tests by [@python357-1](https://github.com/python357-1) in [#648](https://github.com/TagStudioDev/TagStudio/pull/648)
- fix: enter/return adds top result tag by [@SkeleyM](https://github.com/SkeleyM) in [#651](https://github.com/TagStudioDev/TagStudio/pull/651)
- fix: show correct unlinked files count by [@SkeleyM](https://github.com/SkeleyM) in [#653](https://github.com/TagStudioDev/TagStudio/pull/653)
- feat: implement parent tag search by [@Computerdores](https://github.com/Computerdores) in [#673](https://github.com/TagStudioDev/TagStudio/pull/673)
- fix: only close add tag menu with no search by [@SkeleyM](https://github.com/SkeleyM) in [#685](https://github.com/TagStudioDev/TagStudio/pull/685)
- fix: drag and drop no longer resets by [@SkeleyM](https://github.com/SkeleyM) in [#710](https://github.com/TagStudioDev/TagStudio/pull/710)
- feat(ui): port "create and add tag" to main branch by [@SkeleyM](https://github.com/SkeleyM) in [#711](https://github.com/TagStudioDev/TagStudio/pull/711)
- fix: don't add default title field, use proper phrasing for adding files by [@CyanVoxel](https://github.com/CyanVoxel) in [#701](https://github.com/TagStudioDev/TagStudio/pull/701)
- fix: preview panel + main window fixes and optimizations by [@CyanVoxel](https://github.com/CyanVoxel) in [#700](https://github.com/TagStudioDev/TagStudio/pull/700)
- fix: sort tag results by [@mashed5894](https://github.com/mashed5894) in [#721](https://github.com/TagStudioDev/TagStudio/pull/721)
- fix: restore opening last library on startup by [@SkeleyM](https://github.com/SkeleyM) in [#729](https://github.com/TagStudioDev/TagStudio/pull/729)
- fix(ui): don't always create tag on enter by [@SkeleyM](https://github.com/SkeleyM) in [#731](https://github.com/TagStudioDev/TagStudio/pull/731)
- fix: use tag aliases in tag search by [@CyanVoxel](https://github.com/CyanVoxel) in [#726](https://github.com/TagStudioDev/TagStudio/pull/726)
- fix: keep initial id order in `get_entries_full()` by [@CyanVoxel](https://github.com/CyanVoxel) in [#736](https://github.com/TagStudioDev/TagStudio/pull/736)
- fix: always catch db mismatch by [@CyanVoxel](https://github.com/CyanVoxel) in [#738](https://github.com/TagStudioDev/TagStudio/pull/738)
- fix: relink unlinked entry to existing entry without sql error by [@mashed5894](https://github.com/mashed5894) in [#730](https://github.com/TagStudioDev/TagStudio/issues/730)
- fix: refactor and fix bugs with missing_files.py by [@CyanVoxel](https://github.com/CyanVoxel) in [#739](https://github.com/TagStudioDev/TagStudio/pull/739)
- fix: dragging files references correct entry IDs [@CyanVoxel](https://github.com/CyanVoxel) in [44ff17c](https://github.com/TagStudioDev/TagStudio/commit/44ff17c0b3f05570e356c112f005dbc14c7cc05d)
- ui: port splash screen from Alpha-v9.4 by [@CyanVoxel](https://github.com/CyanVoxel) in [af760ee](https://github.com/TagStudioDev/TagStudio/commit/af760ee61a523c84bab0fb03a68d7465866d0e05)
- fix: tags created from tag database now add aliases by [@CyanVoxel](https://github.com/CyanVoxel) in [2903dd2](https://github.com/TagStudioDev/TagStudio/commit/2903dd22c45c02498687073d075bb88886de6b62)
- fix: check for tag name parity during JSON migration by [@CyanVoxel](https://github.com/CyanVoxel) in [#748](https://github.com/TagStudioDev/TagStudio/pull/748)
- feat(ui): re-implement tag display names on sql by [@CyanVoxel](https://github.com/CyanVoxel) in [#747](https://github.com/TagStudioDev/TagStudio/pull/747)
- fix(ui): restore Windows accent color on PySide 6.8.0.1 by [@CyanVoxel](https://github.com/CyanVoxel) in [#755](https://github.com/TagStudioDev/TagStudio/pull/755)
- fix(ui): (mostly) fix right-click search option on tags by [@CyanVoxel](https://github.com/CyanVoxel) in [#756](https://github.com/TagStudioDev/TagStudio/pull/756)
- feat: copy/paste fields and tags by [@mashed5894](https://github.com/mashed5894) in [#722](https://github.com/TagStudioDev/TagStudio/pull/722)

#### UI/UX

- feat(ui): pre-select default tag name in `BuildTagPanel` by [@Cool-Game-Dev](https://github.com/Cool-Game-Dev) in [#592](https://github.com/TagStudioDev/TagStudio/pull/592)
- feat(ui): keyboard navigation for editing tags by [@Computerdores](https://github.com/Computerdores) in [#407](https://github.com/TagStudioDev/TagStudio/pull/407)
- feat(ui): use tag query as default new tag name by [@CyanVoxel](https://github.com/CyanVoxel) in [29c0dfd](https://github.com/TagStudioDev/TagStudio/commit/29c0dfdb2d88e8f473e27c7f1fe7ede6e5bd0feb)
- feat(ui): shortcut to add tags to selected entries; change click behavior of tags to edit by [@CyanVoxel](https://github.com/CyanVoxel) in [#749](https://github.com/TagStudioDev/TagStudio/pull/749)
- fix(ui): use consistent dark mode colors for all systems by [@CyanVoxel](https://github.com/CyanVoxel) in [#752](https://github.com/TagStudioDev/TagStudio/pull/752)
- fix(ui): use camera white balance for raw images by [@CyanVoxel](https://github.com/CyanVoxel) in [6ee5304](https://github.com/TagStudioDev/TagStudio/commit/6ee5304b52f217af0f5df543fcb389649203d6b2)
- Mixed field editing has been limited due to various bugs in both the JSON and SQL implementations. This will be re-implemented in a future release.

#### Performance

- feat: improve performance of "Delete Missing Entries" by [@Toby222](https://github.com/Toby222) and [@Computerdores](https://github.com/Computerdores) in [#696](https://github.com/TagStudioDev/TagStudio/pull/696)

#### Internal Changes

- refactor: combine open launch args by [@UnusualEgg](https://github.com/UnusualEgg) in [#364](https://github.com/TagStudioDev/TagStudio/pull/364)
- feat: add date_created, date_modified, and date_added columns to entries table by [@CyanVoxel](https://github.com/CyanVoxel) in [#740](https://github.com/TagStudioDev/TagStudio/pull/740)

## [9.4.2] - 2024-12-01

### Added/Fixed

- Create auto-backup of library for use in save failures (Fix [#343](https://github.com/TagStudioDev/TagStudio/issues/343)) by [@CyanVoxel](https://github.com/CyanVoxel) in [#554](https://github.com/TagStudioDev/TagStudio/pull/554)

## [9.4.1] - 2024-09-14

### Added

- Warn user if FFmpeg is not installed
- Support for `.raf` and `.orf` raw image thumbnails and previews

### Fixed

- Use `birthtime` for file creation time on Mac & Windows
- Use audio icon fallback when FFmpeg is not detected
- Retain search query upon directory refresh

### Changed

- Significantly improve file re-scanning performance

## [9.4.0] - 2024-09-04

### Added

- Copy and paste fields
- Add multiple fields at once
- Drag and drop files in/out of the program
  - Files can be shared by dragging them from the thumbnail grid to other programs
  - Files can be added to library folder by dragging them into the program
- Manage Python virtual environment in Nix flake
- Ability to create tag when adding tags
- Blender preview thumbnail support
- File deletion/trashing
  - Added right-click option on thumbnails and preview panel to delete files
  - Added Edit Menu option for deleting files
  - Added <kbd>Delete</kbd> key shortcut for deleting files
- Font preview thumbnail support
  - Short "Aa" previews for thumbnails
  - Full alphabet preview for the preview pane
- Sort tags by alphabetical/color
- File explorer action follows OS naming
- Preview Source Engine files
- Expanded thumbnail and preview features
  - Add album cover art thumbnails
  - Add audio waveform thumbnails for audio files without embedded cover art
  - Add new default file thumbnails, both for generic and specific file types
  - Change the unlinked file icon to better convey its meaning
  - Add dropdown for different thumbnail sizes
- Show File Creation and Modified dates; Restyle file path label

### Fixed

- Backslashes in f-string on file dupe widget
- Tags not shown when none searched
- Avoid error from eagerly grabbing data values
- Correct behavior for tag search options
- Load Gallery-DL sidecar files correctly
- Correct duplicate file matching
- GPU hardware acceleration in Nix flake
- Suppress command prompt windows for FFmpeg in builds

### Internal Changes

- Move type constants to media classes
- Combine open launch arguments
- Revamp Nix flake with devenv/direnv in cb4798b
- Remove impurity of Nix flake when used with direnv in bc38e56

## [9.3.2] - 2024-07-19

### Fixed

- Fix signal log warning
- Fix "Folders to Tags" feature
- Fix search ignoring case of extension list

### Internal Changes

- Add tests into CI by
- Create testing library files ad-hoc
- Refactoring: centralize field IDs
- Update to pyside6 version 6.7.1

## [9.3.1] - 2024-06-13

### Fixed

- Separately pin QT nixpkg version
- Bugfix for #252, don't attempt to read video file if invalid or 0 frames long
- Toggle Mouse Event Transparency on ItemThumbs
- Refactor `video_player.py`

## [9.3.0] - 2024-06-09

### Added

- Added playback previews for video files
- Added Boolean "and/or" search mode selection
- Added ability to scan and fix duplicate entries (not to be confused with duplicate files) from the "Fix Unlinked Entries" menu
- Added “Select All” (<kbd>Ctrl</kbd>+<kbd>A</kbd> / <kbd>⌘ Command</kbd>+<kbd>A</kbd>) hotkey for the library grid view
- Added "Clear Selection" hotkey (<kbd>Esc</kbd>) for the library grid view
- Added the ability to invert the file extension inclusion list into an exclusion list
- Added default landing page when no library is open

### Fixed

- TagStudio will no longer attempt to or allow you to reopen a library from a missing location
- Fixed `PermissionError` when attempting to access files with a higher permission level upon scanning the library directory
- Fixed RAW image previews sometimes not loadingand
- Fixed most non-UTF-8 encoded text files from not being able to be previewed
- Fixed "Refresh Directories"/"Fix Unlinked Entries" creating duplicate entries
- Other miscellaneous fixes

### Changed

- Renamed "Subtags" to "Parent Tags" to help better describe their function
- Increased number of tags shown by default in the "Add Tag" modal from 29 to 100
- Documentation is now split into individual linked files and updated to include future features
- Replaced use of `os.path` with `pathlib`
- `.cr2` files are now included in the list of RAW image file types
- Minimum supported macOS version raised to 12.0

## [9.2.1] - 2024-05-23

### Added

- Basic thumbnail/preview support for RAW images (currently `.raw`, `.dng`, `.rw2`, `.nef`, `.arw`, `.crw`, `.cr3`)
  - NOTE: These previews are currently slow to load given the nature of rendering them. In the future once thumbnail caching is added, this process should only happen once.
- Thumbnail/preview support for HEIF images

### Fixed

- Fixed sidebar not expanding horizontally
- Fixed "Recent Library" list not updating when creating a new library
- Fixed palletized images not loading with alpha channels
- Low resolution images (such as pixel art) now render with crisp edges in thumbnails and previews
- Fixed visual bug where the edit icon would show for incorrect fields

## [9.2.0] - 2024-05-14

### Added

- Full macOS and Linux support
- Ability to apply tags to multiple selections at once
- Right-click context menu for opening files or their locations
- Support for all filetypes inside of the library
- Configurable filetype blacklist
- Option to automatically open last used library on startup
- Tool to convert folder structure to tag tree
- SIGTERM handling in console window
- Keyboard shortcuts for basic functions
- Basic support for plaintext thumbnails
- Default icon for files with no thumbnail support
- Menu action to close library
- All tags now show in the "Add Tag" panel by default
- Modal view to view and manage all library tags
- Build scripts for Windows and macOS
- Help menu option to visit the GitHub repository
- Toggleable "Recent Libraries" list in the entry side panel

### Fixed

- Fixed errors when performing actions with no library open
- Fixed bug where built-in tags were duplicated upon saving
- QThreads are now properly terminated on application exit
- Images with rotational EXIF data are now properly displayed
- Fixed "truncated" images causing errors
- Fixed images with large resolutions causing errors

### Changed

- Updated minimum Python version to 3.12
- Various UI improvements
  - Improved legibility of the Light Theme (still a WIP)
  - Updated Dark Theme
  - Added hand cursor to several clickable elements
- Fixed network paths not being able to load
- Various code cleanup and refactoring
- New application icons

### Known Issues

- Using and editing multiple entry fields of the same type may result in incorrect field(s) being updated
- Adding Favorite or Archived tags via the thumbnail badges may apply the tag(s) to incorrect fields
- Searching for tag names with spaces does not currently function as intended
	- A temporary workaround it to omit spaces in tag names when  searching
- Sorting fields using the "Sort Fields" macro may result in edit icons being shown for incorrect fields

## [9.1.0] - 2024-04-22

### Added

- Initial public release
