---
title: Changelog
icon: material/script-text
toc_depth: 2
---

<!-- SPDX-FileCopyrightText: (c) TagStudio Contributors -->
<!-- SPDX-License-Identifier: GPL-3.0-only -->

# :material-script-text: Changelog

## 9.5.7 <small>May 5th, 2026</small>

This update adds several bugfixes and additions that have been sitting on the main branch for quite some time.

### Added

- feat: add hidden tags by @TrigamDev in #1139
- feat: render `.pdn` thumbnails. by @Sola-ris in #1149
- feat: render `.mdp` thumbnails. by @Sola-ris in #1153
- feat: update notification by @Computerdores in #1166
- feat: render `.clip` thumbnails. by @Sola-ris in #1150
- feat: render archive thumbnails by @Sola-ris in #1194

### Fixed

- fix: "Search for Tag" in Tag Manager executes multiple queries by @CallMeHein in #1173
- fix: 'Add Tag to Selected' action fails by @TrigamDev in #1224
- fix: escape dash in URL regex by @TrigamDev in #1255
- fix: running the 'Fix Ignored Entries' tool from the menu bar causes an error in the log by @TrigamDev in #1188
- fix: when deleting tag remove all TagParent rows with it's id by @TheBobBobs in #1250
- fix: remove entry even if deleting it's file failed by @TheBobBobs in #1246
- fix: tab order in build_tag modal by @Computerdores in #1235
- fix: prevent deadlock when wanted mnemonics conflict by @Computerdores in #1200
- fix: call ripgrep with explicit utf-8 encoding. by @Sola-ris in #1199
- fix: persist entry selection across pages and save scroll positions by @TheBobBobs in #1248
- fix: MacOS system theme fix (#999) by @terahidro2003 in #1328
- perf: Bulk insert/delete tag_entries by @TheBobBobs in #1296

### Changed

#### Internal Changes

- fix(nix): replace wrapGAppsHook with wrapGAppsHook3 by @Ambossmann in #1189
- feat: add windows runner for pytest by @Sola-ris in #1201
- chore(thumb_renderer): bump Pillow by @xarvex in #1227
- fix(nix): add requests and semver to nix package by @Ambossmann in #1265
- fix: errors in DupeFilesRegistry by @Computerdores in #1233
- fix: pyright errors in blender_renderer.py by @Computerdores in #1236

#### Translations

- **Cebuano** added by @StartsMercury
- **Chinese (Simpliflied Han Script)** updated by @ngivanyh
- **Chinese (Traditional Han Script)** updated by @ngivanyh
- **Dutch** updated by @timomen
- **French** updated by @kitsumed
- **Finnish** updated by @JonneSaloranta
- **German** updated by @Dariton4000, @HerrChaos
- **Greek** updated by @Gvolexe
- **Hungarian** updated by @smileyhead
- **Icelandic** updated by @kristinnssig
- **Italian** updated by @EdelFlosWeiss
- **Japanese** updated by wany-oh
- **Portugese (Brazil)** updated by José Victor, dmto dmto, @AsmodeumX
- **Spanish** updated by @JCC1998, @JulArr22, @r40s-0
- **Swedish** updated by @vimml
- **Tamil** updated by @TamilNeram
- **Toki Pona** updated by @Math-Bee, Star Athendwyl

### New Contributors

- @Ambossmann made their first contribution in #1189
- @CallMeHein made their first contribution in #1173
- @terahidro2003 made their first contribution in #1328

---

## 9.5.6 <small>October 20th, 2025</small>

### Added

- feat: render .cb7 thumbnails. by @Sola-ris in #1118
- feat: add infinite scrolling, improve page performance by @TheBobBobs in #1119

### Fixed

- fix: process ignore patterns for wcmatch in unlinked registry by @CyanVoxel in #1124
- fix: respect trailing slash patterns in glob by @CyanVoxel in #1127
- fix: always hide duration badge on non video ext by @TheBobBobs in #1134
- fix: update entry cache when toggling tags by @TheBobBobs in #1135
- fix: use absolute path for file opener by @TheBobBobs in #1136
- fix: toggle play only with left mouse button click by @csponge in #1152
- fix: Fix searching `A AND A` returning no results by @TrigamDev in #1138
- fix: add periodic yield to save_new_files by @TheBobBobs in #1040

### Changed

#### Internal Changes

- fix: apply unwrap where necessary by @Computerdores in #1113
- fix: renderer type fixes by @Computerdores in #1114

#### Translations

- **Dutch** updated by @FlannyH
- **French** updated by @kitsumed
- **Hungarian** updated by @smileyhead
- **Italian** added and updated by @OmnipresentW
- **Japanese** updated by wany-oh
- **Norwegian Bokmål** updated by @Neemek
- **Spanish** updated by @JCC1999

---

## 9.5.5 <small>September 8th, 2025</small>

### Added

#### New Settings

- feat(ui): add thumbnail cache size setting to settings panel by @CyanVoxel in #1088
- feat: add cached thumbnail quality and resolution settings by @CyanVoxel in #1101
    - Only available by editing the `cached_thumb_quality` and `cached_thumb_resolution` options in the `settings.toml` config file
- fix: add option to use old Windows 'start' command by @CyanVoxel in #1084
    - Only available by editing the `windows_start_command` option in the `settings.toml` file
    - Fixes niche issue on Windows systems, see #1036
- translations: add Czech, Portuguese (Portugal), and Romanian to settings panel (2db8bed)

#### File Previews

- feat: render .cbr thumbnails by @Sola-ris in #1112
- feat: render .cbt thumbnails by @Sola-ris in #1116

### Fixed

- fix: JSON migration window getting stuck on finishing migration by @CyanVoxel in #1094
- fix: VTF files not rendering on Linux by @CyanVoxel in #1093
- fix: account for leading slash ignore pattern by @CyanVoxel in #1092
- fix: add option to use old Windows 'start' command by @CyanVoxel in #1084
- fix: always show first frame of video; autoplay will always play by @SumithSudheer and @CyanVoxel in #1104
- feat: read epub cover from ComicInfo.xml, if available. by @Sola-ris in #1109 and #1111
- fix: prevent mnemonic removal from removing escaped ampersands by @CyanVoxel in #1110
- fix: properly delete tag_parents row when deleting tag by @CyanVoxel in #1107

### Changed

#### Translations

- **French** updated by @kitsumed , @RustyNova016
- **Hungarian** updated by @smileyhead
- **Russian** updated by @purpletennisball
- **Spanish** updated by @danpg94
- **Toki Pona** updated by @Math-Bee

#### Internal Changes

- refactor: untangle backend and frontend files by @CyanVoxel in #1095
- refactor: fix most pyright issues in `library/alchemy/` by @CyanVoxel in #1103

---

## 9.5.4 <small>September 1st, 2025</small>

### Added

#### `.ts_ignore` File and Folder Ignore System

The previous system for ignoring file extensions has been replaced by a new `.gitignore`-style pattern matching system. This uses a `.ts_ignore` file inside your library's `.TagStudio` folder with glob-like rules to give more power options than what was previously possible. This file can be edited inside within TagStudio or externally, and rules are hot-reloaded in either case. Existing extension rules have been migrated as closely as possible to this new system. For more information on this new system, visit the "[Ignore Files](https://docs.tagstud.io/ignore/)" page on the documentation site.

<img width="764" height="677" alt="Screenshot 2025-08-22 at 14 31 15" src="https://github.com/user-attachments/assets/116d6b71-939c-4aa2-9101-6134e1c22341" />

Along with this system also comes the additional features:

- TagStudio can now traverse symlinks in your library folders
- TagStudio can now leverage [ripgrep](https://github.com/BurntSushi/ripgrep), a rust-based directory search tool, for faster library refreshing
    - ripgrep must be [installed on your system](https://docs.tagstud.io/install/#ripgrep) and able to be located by TagStudio

##### Pull Requests:

- feat: add `.ts_ignore` pattern ignoring system by @CyanVoxel in #897
- feat: replace extension exclusion system with `.ts_ignore` by @CyanVoxel in #1046

#### Library Information Window

A new "Library Information" window has been added and is accessible under the "View" window. This window includes statistics about your currently opened library, as well as convenient access to library cleanup tools. This includes a new tool to cleanup "ignored files", which are files that have been previously added to your library but now no longer meet the ignore pattern rules.

<img width="912" height="620" alt="Screenshot 2025-08-30 at 15 53 08" src="https://github.com/user-attachments/assets/a12b4a2e-8c4a-448b-9e78-d84d39b19e3e" />

##### Pull Requests:

- feat: add LibraryInfoWindow with library statistics by @CyanVoxel in #1056
- feat: add library cleanup screen and 'fix ignored files' window by @CyanVoxel in #1070

#### Other Additions

- feat: add random sorting by @TheBobBobs in #1029
- feat: add exr thumbnail support by @CyanVoxel in #1035
- feat: add thumbnail generation toggle by @ZwodahS in #1057
- feat: cli version argument by @HeikoWasTaken in #1060
- feat: add setting to select splash screen by @CyanVoxel in #1077
    - Includes a new "'95" splash screen originally intended for the [9.5.0](https://github.com/TagStudioDev/TagStudio/releases/tag/v9.5.0) release

<img width="540" height="360" alt="splash_selection_half" src="https://github.com/user-attachments/assets/3cd6562f-0eaf-420d-9d70-d10d1519da84" />

### Fixed

- fix: searching with internal tag ids ignores sorting order by @CyanVoxel in #1038
- fix: folders with names of unlinked entries are linked by @purpletennisball in #1027
- fix: parent tags in tag editor are uneditable by @purpletennisball in #1073
- feat: auto mnemonics by @Computerdores in #1082 and #1083

### Changed

#### Performance

- perf: optimize sql for or queries by @TheBobBobs in #948
- perf: Optimize db queries for preview panel by @TheBobBobs in #942
- fix: add tags to selected entries in bulk not individually by @Computerdores in #1028

#### Translations

- **Chinese** _(Traditional Han Script)_ by @tkiuvvv233
- **French** updated by @Bamowen, @kitsumed
- **German** updated by @Livesi5e
- **Hungarian** updated by @smileyhead
- **Japanese** updated by wany-oh
- **Polish** updated by @FeatherPrince
- **Portuguese** updated by @SantosSi
- **Romanian** updated by @VLTNOgithub
- **Russian** updated by @Dott-rus
- **Spanish** updated by @JCC1998
- **Swedish** updated by konto

#### Internal Changes

- feat: swap IDs in tag_parents table by @HeikoWasTaken in #998
    - fix: swap parent and child logic for TAG_CHILDREN_QUERY by @CyanVoxel in #1064
- fix(nix): fixup and rework, always use nixpkgs PySide/Qt by @xarvex in #1048
- refactor: make cache_manager thread safe by @TheBobBobs in #1039
- ci(tests): fix broken tests and add type hints by @CyanVoxel in #1062
- refactor: store DB version inside `versions` table by @CyanVoxel in #1058
- refactor: unwrap instead of assert not None by @Computerdores in #1068
- chore(thumb_renderer): prepare for pillow_heif removing AVIF support by @xarvex in #1065

---

## 9.5.3 <small>August 7th, 2025</small>

### Added

- Datetime fields by @Computerdores in #921, #946, and #926
- Add date_format and hour_format settings by @JCC1998 in #904
- Invert selection by @zfbx in #909
- Show stems for extension-less files by @CyanVoxel in #899
- Press enter when adding fields by @rsazra in #941
- Option to change tag click behavior by @Computerdores in #945
- Krita/Open Raster thumbnails by @mashed5894 in #985
- Zoom keyboard shortcuts by @purpletennisball in #956
- Clickable links in text fields by @TrigamDev in #924

### Fixed

- Restore page navigation state by @Computerdores in #933
- Proper error on unterminated quoted string by @Computerdores in #936
- Creating new tag now refreshes the menu using the current search text by @purpletennisball in #939
- Preview thumbnails don't scale as large as they could by @Computerdores in #1005
- Add Nix path to FFmpeg locations on macOS by @thibmaek in #990
- Use srctools instead of vtf2img to render vtf files by @CyanVoxel in #1014

### Changed

- Add parent tags to `folders_to_tags` macro and start tagging at root folder by @rsazra in #940
- Optimize page loading by @TheBobBobs in #954
- Add arrow icons for navigation buttons by @CyanVoxel in #1016
- Tweak media player style and behavior by @CyanVoxel in #1025

### Translations

- **Chinese** _(Simplified Han Script)_ added and updated by @tkiuvvv233, Luoyu, @ngivanyh
- **Dutch** updated by @Pheubel
- **Filipino** updated by @searinminecraft
- **French** updated by @kitsumed
- **German** updated by @Livesi5e, @Stereo157E
- **Hungarian** updated by @smileyhead
- **Japanese** updated by wany-oh
- **Norwegian Bokmål** updated by @Neemek
- **Polish** updated by @FeatherPrince
- **Russian** updated by @Dott-rus, Utof, @maximmax42
- **Spanish** updated by @JCC1998, Joan, Sunny, @danpg94
- **Tamil** updated by @TamilNeram
- **Toki Pona** updated by @Math-Bee
- **Viossa** updated by @Nginearing

### Internal Changes

- refactor: type fixes and minor improvements to preview_thumb.py by @VasigaranAndAngel in #906
- fix(test): Fix tests to pass on windows without disrupting other platforms by @zfbx in #903
- chore(pyproject): version bumping/relaxing by @xarvex in #886
- fix: tests were overwriting the settings.toml by @Computerdores in #928
- fix(nix/package): override PySide6 if later version is being used by @xarvex in #917
- refactor: split QtDriver into View and Controller to follow MVC model by @Computerdores in #935
- refactor: resource_manager.py by @VasigaranAndAngel in #958
- Type fixes to folders_to_tags.py, collage_icon.py and item_thumb.py by @VasigaranAndAngel in #959
- Type fixes to preview_panel.py, progress.py, tag.py and tag_box.py by @VasigaranAndAngel in #961
- Type improvements to landing.py and panel.py by @VasigaranAndAngel in #960
- refactor(preview_panel): mvc split by @Computerdores in #952
- refactor(preview_thumb): mvc split by @Computerdores in #978
- refactor: type improvements for main_window.py by @VasigaranAndAngel in #957
- fix(library): get_tag_by_name by @Computerdores in #1006
- fix: ensure initial browsing state uses UI values by @CyanVoxel in #1008
- refactor(tag_box): mvc split by @Computerdores in #1003
- fix(ui): hide empty ProgressWidget cancel button by @CyanVoxel in #1011
- fix(ui): fix audio waveform generation on numpy 2.3 by @CyanVoxel in #1013
- refactor: replace remaining instances of logging with structlog by @CyanVoxel in #1012
- fix: don't fail when posix env var is not present by @Computerdores in #1018
- fix(ui): show correct thumb labels by @CyanVoxel in #1010

### Documentation

- Update CHANGELOG.md by @Math-Bee in #914
- Add QT MVC structure to style guide by @Computerdores in #950
- Fix wrong date on Changelog by @ugurozturk in #966

---

## 9.5.2 <small>March 31st, 2025</small>

### Added

#### Search

- feat(ui): add setting to not display full filepaths by @HermanKassler in #841
- feat: add filename and path sorting by @Computerdores in #842

#### Settings

- feat: new settings menu + settings backend by @Computerdores in #859

#### UI

- feat(ui): merge media controls by @csponge in #805
    - fix: Remove border from video preview top and left by @zfbx in #900
- feat(ui): add more default icons and file type equivalencies by @CyanVoxel in #882
- ui: recent libraries list improvements by @CyanVoxel in #881

#### Misc

- feat: provide a .desktop file by @xarvex in #870

### Fixed

- fix: catch NotImplementedError for Float16 JPEG-XL files by @CyanVoxel in #849
- fix(nix/package): account for GTK platform by @xarvex in #868
- fix: do not set palette for Linux-like systems that offer theming by @xarvex in #869
- fix(flake): remove pinned input, only consume in Nix shell by @xarvex in #872
- fix: stop ffmpeg cmd windows, refactor ffmpeg_checker by @CyanVoxel in #855
- fix: hide mnemonics on macOS by @CyanVoxel in #856
- fix: use UNION instead of UNION ALL by @CyanVoxel in #877
- fix: remove unescaped ampersand from "about.description" by @CyanVoxel in #885
- fix(ui): display 0 frame webp files in preview panel by @CyanVoxel in 64dc88afa90bb11f3c9b74a2522f947370ce21db
- fix: close pdf file object in thumb renderer by @Computerdores in #893
- perf: improve responsiveness of GIF entries by @Computerdores in #894
- fix(ui): seamlessly loop videos by @CyanVoxel in #902

### Internal Changes

- refactor!: change layout; import and build change by @xarvex and @CyanVoxel in #844
- fix: log all problems in translation test by @Computerdores in #839
- refactor: split translation keys for about screen by @CyanVoxel in #845
- feat(ci): development tooling refresh and split documentation by @xarvex in #867
- refactor: type hints and improvements in file_opener.py by @VasigaranAndAngel in #876
- build: update spec file to use proper pathex and datas paths by @Leonard2 in #895
- refactor: fix various missing and broken type hints@VasigaranAndAngel in #901
- refactor: fix type hints and overrides in flowlayout.py by @VasigaranAndAngel in #880

### Documentation

- docs: fix typos and grammar by @Gawidev in #879
- docs: update `ThumbRenderer` source by @emmanuel-ferdman in #896

### Translations

- **Filipino** updated by @searinminecraft
- **French** updated by @kitsumed
- **German** updated by @DontBlameMe99, @Computerdores
- **Hungarian** updated by Szíjártó Levente Pál
- **Japanese** added by @needledetector
- **Portuguese** _(Brazil)_ updated by @viniciushelder
- **Russian** updated by werdi, @Dott-rus
- **Spanish** updated by Joan, @Nginearing
- **Tamil** updated by @TamilNeram
- **Toki Pona** updated by @Math-Bee
- **Turkish** updated by @Nyghl

---

## 9.5.1 <small>March 6th, 2025</small>

### Fixed

- Fixed translations crashing the program and preventing it from being reopened (#827)
    - fix: restore `translate_formatted()` method as `format()` by @CyanVoxel in #830
    - tests: add tests for translations by @Computerdores in #833
    - fix(translations): fix invalid placeholders by @CyanVoxel in #835
- Removed empty parentheses from the "About" screen title
    - fix: separate about screen title from translations by @CyanVoxel in #836

### Translations

- **French** updated by @alessdangelo, @Bamowen, @kitsumed
- **German** updated by @Thesacraft
- **Portuguese** _(Brazil)_ updated by @viniciushelder
- **Russian** updated by werdei
- **Spanish** updated by @JCC1998

### Documentation

- docs: fix category typo by @salem404 in #834

---

## 9.5.0 <small>March 3rd, 2025</small>

<img width="500" src="https://github.com/user-attachments/assets/858f1494-216f-4521-aefe-d0aa4f754b9e" alt="TagStudio 9.5 Banner" />

### Added

#### Overhauled Search Engine

##### Boolean Operators

- feat: implement query language by @Computerdores in #606
- feat: optimize AND queries by @Computerdores in #679

##### Filetype, Mediatype, and Glob Path + Smartcase Searches

- fix: remove wildcard requirement for tags by @Tyrannicodin in #481
- feat: add filetype and mediatype searches by @python357-1 in #575
- feat: make path search use globs by @python357-1 in #582
- feat: implement search equivalence of "jpg" and "jpeg" filetypes by @Computerdores in #649
- feat: add smartcase and globless path searches by @CyanVoxel in #743

##### Sortable Results

- feat: sort by "date added" in library by @Computerdores in #674

##### Autocomplete

- feat: add autocomplete for search engine by @python357-1 in #586

#### Replaced "Tag Fields" with Tag Categories

Instead of tags needing to be added to a tag field type such as "Meta Tags", "Content Tags", or just the "Tags" field, tags are now added directly to file entries with no intermediary step. While tag field types offered a way to further organize tags, it was cumbersome, inflexible, and simply not fully fleshed out. Tag Categories offer all of the previous (intentional) functionality while greatly increasing the ease of use and customization.

- feat!: tag categories by @CyanVoxel in #655

<img width="200" alt="Screenshot 2025-01-04 at 04 23 43" src="https://github.com/user-attachments/assets/0b92eca5-db8f-4e3e-954b-1b4f3795f073" />

#### Thumbnails and File Previews

##### New Thumbnail Support

- feat: add svg thumbnail support (port #442) by @Tyrannicodin and @CyanVoxel in #540
- feat: add pdf thumbnail support (port #378) by @Heiholf and @CyanVoxel in #543
- feat: add ePub thumbnail support (port #387) by @Heiholf and @CyanVoxel in #539
- feat: add OpenDocument thumbnail support (port #366) by @Joshua-Beatty and @CyanVoxel in #545
- feat: add JXL thumbnail and animated APNG + WEBP support (port #344 and partially port #357) by @BPplays and @CyanVoxel in #549
    - fix: catch ImportError for pillow_jxl module by @CyanVoxel in a2f9685bc0d744ea6f5334c6d2926aad3f6d375a

##### Audio Playback

- feat: audio playback by @csponge in #576
    - feat(ui): add audio volume slider by @SkeleyM in #691

##### Thumbnail Caching

- feat(ui): add thumbnail caching by @CyanVoxel in #694

#### Tags

##### Delete Tags _(Finally!)_

- feat: remove and create tags from tag database panel by @DandyDev01 in #569

##### Custom User-Created Tag Colors

Create your own custom tag colors via the new Tag Color Manager! Tag colors are assigned a namespace (group) and include a name, primary color, and optional secondary color. By default the secondary color is used for the tag text color, but this can also be toggled to apply to the border color as well!

- feat(ui)!: user-created tag colors by @CyanVoxel in #801

<img width="300" src="https://github.com/user-attachments/assets/b591f1fe-1c44-4d82-b6e5-d166590aeab1" />
<img width="500" src="https://github.com/user-attachments/assets/96e81b08-6993-4a5e-96d0-3b05b50fbe44" />

##### New Tag Colors + UI

- feat: expanded tag color system by @CyanVoxel in #709
- fix(ui): use correct pink tag color by @CyanVoxel in 431efe4fe93213141c763e59ca9887215766fd42
- fix(ui): use consistent tag outline colors by @CyanVoxel in 020a73d095c74283d6c80426d3c3db8874409952

<img width="250" alt="Screenshot 2025-01-04 at 04 23 43" src="https://github.com/user-attachments/assets/c8f82d89-ad7e-4be6-830e-b91cdc58e4c6" />

##### New Tag Alias UI

- fix: preview panel aliases not staying up to date with database by @DandyDev01 in #641
- fix: subtags/parent tags & aliases update the UI for building a tag by @DandyDev01 in #534

#### Translations

TagStudio now has official translation support! Head to the new settings panel and select from one of the initial languages included. Note that many languages currently have incomplete translations.

Translation hosting generously provided by [Weblate](https://weblate.org/en/). Check out our [project page](https://hosted.weblate.org/projects/tagstudio/) to help translate TagStudio! Thank you to everyone who's helped contribute to the translations so far!

- translations: add string tokens for en.json by @Bamowen in #507
- feat: translations by @Computerdores in #662
- feat(ui): add language setting by @CyanVoxel in #803

Initial Languages:

- **Chinese** _(Traditional Han Script)_ by @brisu
- **Dutch** by @Pheubel
- **Filipino** by @searinminecraft
- **French** by @Bamowen, @alessdangelo, @kitsumed, Obscaeris
- **German** by @Ryussei, @Computerdores, Aaron M, @JoeJoeTV, @Kurty00
- **Hungarian** by @smileyhead
- **Norwegian Bokmål** by @comradekingu
- **Polish** by Anonymous
- **Portuguese** _(Brazil)_ by @LoboMetalurgico, @SpaceFox1, @DaviMarquezeli, @viniciushelder, Alexander Lennart Formiga Johnsson
- **Russian** by @The-Stolas
- **Spanish** by @gallegonovato, @Nginearing, @noceno
- **Swedish** by @adampawelec, @mashed5894
- **Tamil** by @VasigaranAndAngel
- **Toki Pona** by @goldstargloww
- **Turkish** by @Nyghl

#### Miscellaneous

- feat: about section by @mashed5894 in #712
- feat(ui): add configurable splash screens by @CyanVoxel in #703
- feat(ui): show filenames in thumbnail grid by @CyanVoxel in #633
- feat(about): clickable links to docs/discord/etc in about modal by @SkeleyM in #799

### Fixed

- fix(ui): display all tags in panel during empty search by @samuellieberman in #328
- fix: avoid `KeyError` in `add_folders_to_tree()` (fix #346) by @CyanVoxel in #347
- fix: error on closing library by @yedpodtrzitko in #484
- fix: resolution info #550 by @Roc25 in #551
- fix: remove queued thumnail jobs when closing library by @yedpodtrzitko in #583
- fix: use absolute ffprobe path on macos (Fix #511) by @CyanVoxel in #629
- fix(ui): prevent duplicate parent tags in UI by @SkeleyM in #665
- fix: fix -o flag not working if path has whitespace around it by @python357-1 in #670
- fix: better file opening compatibility with non-ascii filenames by @SkeleyM in #667
- fix: restore environment before launching external programs by @mashed5894 in #707
- fix: have pydub use known ffmpeg + ffprobe locations by @CyanVoxel in #724
- fix: add ".DS_Store" to `GLOBAL_IGNORE_SET` by @CyanVoxel in b72a2f233141db4db6aa6be8796b626ebd3f0756
- fix: don't add ".\_" files to libraries by @CyanVoxel in eb1f634d386cd8a5ecee1e6ff6a0b7d8811550fa

### Changed

#### SQLite Save File Format

This was the main focus of this update, and where the majority of development time and resources have been spent since v9.4. These changes include everything that was done to migrate from the JSON format to SQLite starting from the initial SQLite PR, while re-implementing every feature from v9.4 as the initial SQLite PR was based on v9.3.x at the time.

- refactor!: use SQLite and SQLAlchemy for database backend by @yedpodtrzitko in #332
- feat: make search results more ergonomic by @yedpodtrzitko in #498
- feat: store `Entry` suffix separately by @yedpodtrzitko in #503
- feat: port thumbnail (#390) and related features to v9.5 by @CyanVoxel in #522
- fix: don't check db version with new library by @yedpodtrzitko in #536
- fix(ui): update ui when removing fields by @DandyDev01 in #560
- feat(parity): backend for aliases and parent tags by @DandyDev01 in #596
- fix: "open in explorer" opens correct folder by @KirilBourakov in #603
- fix: ui/ux parity fixes for thumbnails and files by @CyanVoxel in #608
- feat(parity): migrate json libraries to sqlite by @CyanVoxel in #604
- fix: clear all setting values when opening a library by @VasigaranAndAngel in #622
- fix: remove/rework windows path tests by @VasigaranAndAngel in #625
- fix: add check to see if library is loaded in filter_items by @Roc25 in #547
- fix: multiple macro errors by @Computerdores in #612
- fix: don't allow blank tag alias values in db by @CyanVoxel in #628
- feat: Reimplement drag drop files on sql migration by @seakrueger in #528
- fix: stop sqlite db from being updated while running tests by @python357-1 in #648
- fix: enter/return adds top result tag by @SkeleyM in #651
- fix: show correct unlinked files count by @SkeleyM in #653
- feat: implement parent tag search by @Computerdores in #673
- fix: only close add tag menu with no search by @SkeleyM in #685
- fix: drag and drop no longer resets by @SkeleyM in #710
- feat(ui): port "create and add tag" to main branch by @SkeleyM in #711
- fix: don't add default title field, use proper phrasing for adding files by @CyanVoxel in #701
- fix: preview panel + main window fixes and optimizations by @CyanVoxel in #700
- fix: sort tag results by @mashed5894 in #721
- fix: restore opening last library on startup by @SkeleyM in #729
- fix(ui): don't always create tag on enter by @SkeleyM in #731
- fix: use tag aliases in tag search by @CyanVoxel in #726
- fix: keep initial id order in `get_entries_full()` by @CyanVoxel in #736
- fix: always catch db mismatch by @CyanVoxel in #738
- fix: relink unlinked entry to existing entry without sql error by @mashed5894 in #730
- fix: refactor and fix bugs with missing_files.py by @CyanVoxel in #739
- fix: dragging files references correct entry IDs @CyanVoxel in 44ff17c0b3f05570e356c112f005dbc14c7cc05d
- ui: port splash screen from Alpha-v9.4 by @CyanVoxel in af760ee61a523c84bab0fb03a68d7465866d0e05
- fix: tags created from tag database now add aliases by @CyanVoxel in 2903dd22c45c02498687073d075bb88886de6b62
- fix: check for tag name parity during JSON migration by @CyanVoxel in #748
- feat(ui): re-implement tag display names on sql by @CyanVoxel in #747
- fix(ui): restore Windows accent color on PySide 6.8.0.1 by @CyanVoxel in #755
- fix(ui): (mostly) fix right-click search option on tags by @CyanVoxel in #756
- feat: copy/paste fields and tags by @mashed5894 in #722
- perf: optimize query methods and reduce preview panel updates by @CyanVoxel in #794
- feat: port file trashing (#409) to v9.5 by @CyanVoxel in #792
- fix: prevent future library versions from being opened by @CyanVoxel in bcf3b2f96bc8b876ca4b0c1d1882ce14a190f249

#### UI/UX

- feat(ui): pre-select default tag name in `BuildTagPanel` by @Cool-Game-Dev in #592
- feat(ui): keyboard navigation for editing tags by @Computerdores in #407
- feat(ui): use tag query as default new tag name by @CyanVoxel in 29c0dfdb2d88e8f473e27c7f1fe7ede6e5bd0feb
- feat(ui): shortcut to add tags to selected entries; change click behavior of tags to edit by @CyanVoxel in #749
- fix(ui): use consistent dark mode colors for all systems by @CyanVoxel in #752
- fix(ui): use camera white balance for raw images by @CyanVoxel in 6ee5304b52f217af0f5df543fcb389649203d6b2
- Mixed field editing has been limited due to various bugs in both the JSON and SQL implementations. This will be re-implemented in a future release.
- fix(ui): improve tagging ux by @CyanVoxel in #633
- fix(ui): hide library actions when no library is open by @CyanVoxel in #787
- refactor(ui): recycle tag list in TagSearchPanel by @CyanVoxel in #788
    - feat(ui): add tag view limit dropdown
- fix(ui): expand usage of esc and enter for modals by @CyanVoxel in #793

#### Performance

- feat: improve performance of "Delete Missing Entries" by @Toby222 and @Computerdores in #696

#### Internal Changes

- refactor: combine open launch args by @UnusualEgg in #364
- feat: add date_created, date_modified, and date_added columns to entries table by @CyanVoxel in #740

---

## 9.5.0-pr4 <small>February 17th, 2025</small>

### Added

#### Custom User-Created Tag Colors (@CyanVoxel in #801)

Create your own custom tag colors via the new Tag Color Manager! Tag colors are assigned a namespace (group) and include a name, primary color, and optional secondary color. By default the secondary color is used for the tag text color, but this can also be toggled to apply to the border color as well!

<img width="300" src="https://github.com/user-attachments/assets/b591f1fe-1c44-4d82-b6e5-d166590aeab1" />
<img width="500" src="https://github.com/user-attachments/assets/96e81b08-6993-4a5e-96d0-3b05b50fbe44" />

#### Translations

TagStudio now has official translation support! Head to the new settings panel and select from one of the initial languages included. Note that many languages currently have incomplete translations.

Translation hosting generously provided by [Weblate](https://weblate.org/en/). Check out our [project page](https://hosted.weblate.org/projects/tagstudio/) to help translate TagStudio! Thank you to everyone who's helped contribute to the translations so far!

- translations: add string tokens for en.json by @Bamowen in #507
- feat: translations by @Computerdores in #662
- feat(ui): add language setting by @CyanVoxel in #803

Initial Languages:

- Chinese (Traditional) (68%)
    - @brisu
- Dutch (35%)
    - @Pheubel
- Filipino (15%)
    - @searinminecraft
- French (89%)
    - @Bamowen, @alessdangelo, @kitsumed, Obscaeris
- German (73%)
    - @Ryussei, @Computerdores, Aaron M
- Hungarian (89%)
    - @smileyhead
- Norwegian Bokmål (16%)
    - @comradekingu
- Polish (76%)
    - Anonymous
- Portuguese (Brazil) (22%)
    - @LoboMetalurgico, @SpaceFox1
- Russian (22%)
    - @The-Stolas
- Spanish (46%)
    - @gallegonovato, @Nginearing, @noceno
- Swedish (24%)
    - @adampawelec, @mashed5894
- Tamil (22%)
    - @VasigaranAndAngel
- Toki Pona (32%)
    - @goldstargloww
- Turkish (22%)
    - @Nyghl

### Fixed

- feat(about): clickable links to docs/discord/etc in about modal by @SkeleyM in #799

### Internal Changes

This release increases the internal `DB_VERSION` to 8. Libraries created with this version of TagStudio can still be opened in earlier v9.5.0 pre-release versions, however the behavior of custom color borders will not be identical to the behavior in this PR. Otherwise it should still be possible to use any custom colors created in this version in these earlier pre-releases (but not really recommended).

---

## 9.5.0-pr3 <small>February 10th, 2025</small>

### Added

##### #743 by @CyanVoxel

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

##### #788 by @CyanVoxel

- Added a "View Limit" dropdown to tag search boxes to limit the number of on-screen tags. Previously this limit was hardcoded to 100, but now options range from 25 to unlimited.
  <img width="350" src="https://github.com/user-attachments/assets/7f7da065-888d-4fe5-a4e7-f99447bcce98" />

### Changed

- fix(ui): expand usage of esc and enter for modals by @CyanVoxel in #793
- perf: optimize query methods and reduce preview panel updates by @CyanVoxel in #794

##### #788 by @CyanVoxel

- Improved performance of tag search boxes, including the tag manager

### Fixed

- fix(ui): hide library actions when no library is open by @CyanVoxel in #787
- feat: port file trashing (#409) to v9.5 by @CyanVoxel in #792

### Docs

- Added references to alternative POSIX shells, as well as pyenv to CONTRIBUTING.md by @ChloeZamorano in #791

---

## 9.5.0-pr2 <small>February 3rd, 2025</small>

### Added

##### #784 by @CyanVoxel

- Add Ctrl+M shortcut to open the "Tag Manager"

### Fixed

- fix: don't wrap field names too early by @CyanVoxel in 2215403201e3b416a43ead0a322688180af6d71b and 90a826d12804b3386a0b9003abb20f23f88ab3be
- fix: save all tag attributes from "Create & Add" modal by @SkeleyM in #762
- fix: allow tag names with colons in search by @SkeleyM in #765
- fix: catch `ParsingError` by @CyanVoxel in #779
- fix: patch incorrect description type & invalid disambiguation_id refs by @CyanVoxel in #782

##### #784 by @CyanVoxel

- Reset tag search box and focus each time a tag search panel is opened
- Include tag parents in tag search results (v9.4 parity)
- Lowercase tag names now get properly sorted with uppercase ones
- Don't include tag display names in "closeness" factor when searching
- Escape "&" characters inside tag names so Qt doesn't treat them as mnemonics
- Set minimum tag width
- Fix "Add Tags" panel missing its window title when accessing from the keyboard shortcut

### Changed

##### #784 by @CyanVoxel

- The "use for disambiguation" button has been moved to the right-hand side of parent tags in order to prevent accidental clicks involving the left-hand "remove tag" button
- Add "Create & Add" button to the bottom of all non-whitespace searches, even if they return some tags
- The awkward "+" button next to tags in the "Add Tags" panel has been removed in favor of clicking on tags themselves
- Improved visual feedback for highlighting, keyboard focusing, and clicking tags
- The clickable area of the "-" button on tags has been increased and has visual feedback when you hover and click it
- You can now tab into the tag search list and add tags with a spacebar press (previously possible but very janky)
- In tag search panels, pressing the Esc key will return your focus to the search bar and highlight your previous query. If the search box is already highlighted, pressing Esc will close the modal
- In modals such as the "Add Tag" and "Edit Tag" panels, pressing Esc will cancel the operation and close the modal

### Internal Changes

- refactor: wrap migration_iterator lambda in a try/except block by @CyanVoxel in #773

### Docs

- docs: update field and library pages by @CyanVoxel in f5ff4d78c1ad53134e9c64698886aee68c0f1dc1
- docs: add information about "tag manager" by @CyanVoxel in 9bdbafa40c4274922f6533b5b5fcee9a4fe43030
- docs: add note about glob searching in the readme by @CyanVoxel in 6e402ac34d2d60e71fbd36ad234fe3914d5eb8e0
- docs: add library_search page by @CyanVoxel in 5be7dfc314b21042c18b2f08893f2b452d12394a
- docs: docs: add more links to index.md by @CyanVoxel in d7958892b7762586837204d686a6a2a993e3c26e
- docs: fix typo for "category" in usage.md by @pinheadtf2 in #760
- fix(docs): fix screenshot sometimes not rendering by @SkeleyM in #775

---

## 9.5.0-pr1 <small>January 31st, 2025</small>

### Added

#### Overhauled Search Engine

##### Boolean Operators

- feat: implement query language by @Computerdores in #606
- feat: optimize AND queries by @Computerdores in #679

##### Filetype, Mediatype, and Glob Path Searches

- fix: remove wildcard requirement for tags by @Tyrannicodin in #481
- feat: add filetype and mediatype searches by @python357-1 in #575
- feat: make path search use globs by @python357-1 in #582
- feat: implement search equivalence of "jpg" and "jpeg" filetypes by @Computerdores in #649

##### Sortable Results

- feat: sort by "date added" in library by @Computerdores in #674

##### Autocomplete

- feat: add autocomplete for search engine by @python357-1 in #586

#### Replaced "Tag Fields" with Tag Categories

Instead of tags needing to be added to a tag field type such as "Meta Tags", "Content Tags", or just the "Tags" field, tags are now added directly to file entries with no intermediary step. While tag field types offered a way to further organize tags, it was cumbersome, inflexible, and simply not fully fleshed out. Tag Categories offer all of the previous (intentional) functionality while greatly increasing the ease of use and customization.

- feat!: tag categories by @CyanVoxel in #655

#### Thumbnails and File Previews

##### New Thumbnail Support

- feat: add svg thumbnail support (port #442) by @Tyrannicodin and @CyanVoxel in #540
- feat: add pdf thumbnail support (port #378) by @Heiholf and @CyanVoxel in #543
- feat: add ePub thumbnail support (port #387) by @Heiholf and @CyanVoxel in #539
- feat: add OpenDocument thumbnail support (port #366) by @Joshua-Beatty and @CyanVoxel in #545
- feat: add JXL thumbnail and animated APNG + WEBP support (port #344 and partially port #357) by @BPplays and @CyanVoxel in #549
    - fix: catch ImportError for pillow_jxl module by @CyanVoxel in a2f9685bc0d744ea6f5334c6d2926aad3f6d375a

##### Audio Playback

- feat: audio playback by @csponge in #576
    - feat(ui): add audio volume slider by @SkeleyM in #691

##### Thumbnail Caching

- feat(ui): add thumbnail caching by @CyanVoxel in #694

#### Tags

##### Delete Tags _(Finally!)_

- feat: remove and create tags from tag database panel by @DandyDev01 in #569

##### New Tag Colors + UI

- feat: expanded tag color system by @CyanVoxel in #709
- fix(ui): use correct pink tag color by @CyanVoxel in 431efe4fe93213141c763e59ca9887215766fd42
- fix(ui): use consistent tag outline colors by @CyanVoxel in 020a73d095c74283d6c80426d3c3db8874409952

##### New Tag Alias UI

- fix: preview panel aliases not staying up to date with database by @DandyDev01 in #641
- fix: subtags/parent tags & aliases update the UI for building a tag by @DandyDev01 in #534

#### Miscellaneous

- feat: about section by @mashed5894 in #712
- feat(ui): add configurable splash screens by @CyanVoxel in #703
- feat(ui): show filenames in thumbnail grid by @CyanVoxel in #633

### Fixed

- fix(ui): display all tags in panel during empty search by @samuellieberman in #328
- fix: avoid `KeyError` in `add_folders_to_tree()` (fix #346) by @CyanVoxel in #347
- fix: error on closing library by @yedpodtrzitko in #484
- fix: resolution info #550 by @Roc25 in #551
- fix: remove queued thumnail jobs when closing library by @yedpodtrzitko in #583
- fix: use absolute ffprobe path on macos (fix #511) by @CyanVoxel in #629
- fix(ui): prevent duplicate parent tags in UI by @SkeleyM in #665
- fix: fix -o flag not working if path has whitespace around it by @python357-1 in #670
- fix: better file opening compatibility with non-ascii filenames by @SkeleyM in #667
- fix: restore environment before launching external programs by @mashed5894 in #707
- fix: have pydub use known ffmpeg + ffprobe locations by @CyanVoxel in #724
- fix: add ".DS_Store" to `GLOBAL_IGNORE_SET` by @CyanVoxel in b72a2f233141db4db6aa6be8796b626ebd3f0756
- fix: don't add ".\_" files to libraries by @CyanVoxel in eb1f634d386cd8a5ecee1e6ff6a0b7d8811550fa

### Changed

#### SQLite Save File Format

This was the main focus of this update, and where the majority of development time and resources have been spent since v9.4. These changes include everything that was done to migrate from the JSON format to SQLite starting from the initial SQLite PR, while re-implementing every feature from v9.4 as the initial SQLite PR was based on v9.3.x at the time.

- refactor!: use SQLite and SQLAlchemy for database backend by @yedpodtrzitko in #332
- feat: make search results more ergonomic by @yedpodtrzitko in #498
- feat: store `Entry` suffix separately by @yedpodtrzitko in #503
- feat: port thumbnail (#390) and related features to v9.5 by @CyanVoxel in #522
- fix: don't check db version with new library by @yedpodtrzitko in #536
- fix(ui): update ui when removing fields by @DandyDev01 in #560
- feat(parity): backend for aliases and parent tags by @DandyDev01 in #596
- fix: "open in explorer" opens correct folder by @KirilBourakov in #603
- fix: ui/ux parity fixes for thumbnails and files by @CyanVoxel in #608
- feat(parity): migrate json libraries to sqlite by @CyanVoxel in #604
- fix: clear all setting values when opening a library by @VasigaranAndAngel in #622
- fix: remove/rework windows path tests by @VasigaranAndAngel in #625
- fix: add check to see if library is loaded in filter_items by @Roc25 in #547
- fix: multiple macro errors by @Computerdores in #612
- fix: don't allow blank tag alias values in db by @CyanVoxel in #628
- feat: Reimplement drag drop files on sql migration by @seakrueger in #528
- fix: stop sqlite db from being updated while running tests by @python357-1 in #648
- fix: enter/return adds top result tag by @SkeleyM in #651
- fix: show correct unlinked files count by @SkeleyM in #653
- feat: implement parent tag search by @Computerdores in #673
- fix: only close add tag menu with no search by @SkeleyM in #685
- fix: drag and drop no longer resets by @SkeleyM in #710
- feat(ui): port "create and add tag" to main branch by @SkeleyM in #711
- fix: don't add default title field, use proper phrasing for adding files by @CyanVoxel in #701
- fix: preview panel + main window fixes and optimizations by @CyanVoxel in #700
- fix: sort tag results by @mashed5894 in #721
- fix: restore opening last library on startup by @SkeleyM in #729
- fix(ui): don't always create tag on enter by @SkeleyM in #731
- fix: use tag aliases in tag search by @CyanVoxel in #726
- fix: keep initial id order in `get_entries_full()` by @CyanVoxel in #736
- fix: always catch db mismatch by @CyanVoxel in #738
- fix: relink unlinked entry to existing entry without sql error by @mashed5894 in #730
- fix: refactor and fix bugs with missing_files.py by @CyanVoxel in #739
- fix: dragging files references correct entry IDs @CyanVoxel in 44ff17c0b3f05570e356c112f005dbc14c7cc05d
- ui: port splash screen from Alpha-v9.4 by @CyanVoxel in af760ee61a523c84bab0fb03a68d7465866d0e05
- fix: tags created from tag database now add aliases by @CyanVoxel in 2903dd22c45c02498687073d075bb88886de6b62
- fix: check for tag name parity during JSON migration by @CyanVoxel in #748
- feat(ui): re-implement tag display names on sql by @CyanVoxel in #747
- fix(ui): restore Windows accent color on PySide 6.8.0.1 by @CyanVoxel in #755
- fix(ui): (mostly) fix right-click search option on tags by @CyanVoxel in #756
- feat: copy/paste fields and tags by @mashed5894 in #722

#### UI/UX

- feat(ui): pre-select default tag name in `BuildTagPanel` by @Cool-Game-Dev in #592
- feat(ui): keyboard navigation for editing tags by @Computerdores in #407
- feat(ui): use tag query as default new tag name by @CyanVoxel in 29c0dfdb2d88e8f473e27c7f1fe7ede6e5bd0feb
- feat(ui): shortcut to add tags to selected entries; change click behavior of tags to edit by @CyanVoxel in #749
- fix(ui): use consistent dark mode colors for all systems by @CyanVoxel in #752
- fix(ui): use camera white balance for raw images by @CyanVoxel in 6ee5304b52f217af0f5df543fcb389649203d6b2
- Mixed field editing has been limited due to various bugs in both the JSON and SQL implementations. This will be re-implemented in a future release.

#### Performance

- feat: improve performance of "Delete Missing Entries" by @Toby222 and @Computerdores in #696

#### Internal Changes

- refactor: combine open launch args by @UnusualEgg in #364
- feat: add date_created, date_modified, and date_added columns to entries table by @CyanVoxel in #740

---

## 9.4.2 <small>December 1st, 2024</small>

### Added/Fixed

- Create auto-backup of library for use in save failures (fix #343) by @CyanVoxel in #554

---

## 9.4.1 <small>September 13th, 2024</small>

### Added

- Warn user if FFmpeg is not installed
- Support for `.raf` and `.orf` raw image thumbnails and previews

### Fixed

- Use `birthtime` for file creation time on Mac & Windows
- Use audio icon fallback when FFmpeg is not detected
- Retain search query upon directory refresh

### Changed

- Significantly improve file re-scanning performance

---

## 9.4.0 <small>September 3rd, 2024</small>

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

## 9.3.2 <small>July 18th, 2024</small>

### Fixed

- Fix signal log warning
- Fix "Folders to Tags" feature
- Fix search ignoring case of extension list

### Internal Changes

- Add tests into CI by
- Create testing library files ad-hoc
- Refactoring: centralize field IDs
- Update to pyside6 version 6.7.1

---

## 9.3.1 <small>June 13th, 2024</small>

### Fixed

- Separately pin QT nixpkg version
- Bugfix for #252, don't attempt to read video file if invalid or 0 frames long
- Toggle Mouse Event Transparency on ItemThumbs
- Refactor `video_player.py`

---

## 9.3.0 <small>June 8th, 2024</small>

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

---

## 9.2.1 <small>May 23rd, 2024</small>

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

---

## 9.2.0 <small>May 14th, 2024</small>

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
    - A temporary workaround it to omit spaces in tag names when searching
- Sorting fields using the "Sort Fields" macro may result in edit icons being shown for incorrect fields

---

## 9.1.0 <small>April 22nd, 2024</small>

### Added

- Initial public release
