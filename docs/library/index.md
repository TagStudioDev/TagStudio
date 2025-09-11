# :material-database: Library

<!-- prettier-ignore -->
!!! info
    This page is a work in progress and needs to be updated with additional information.

The library is how TagStudio represents your chosen directory, with every file inside being represented by a [file entry](./entry.md). You can have as many or few libraries as you wish, since each libraries' data is stored within a `.TagStudio` folder at its root. From there the library save file itself is stored as `ts_library.sqlite`, with TagStudio versions 9.4 and below using a the legacy `ts_library.json` format.

Note that this means [tags](./tag.md) you create only exist _per-library_. Global tags along with other library structure updates are planned for future releases on the [roadmap](../updates/roadmap.md#library).

---

## Preview Support

TagStudio offers built-in preview and thumbnail support for a wide variety of file types. Files that don't have explicit support can still be added to your library like normal, they will just show a default icon for thumbnails and previews. TagStudio also references the file's [MIME](https://en.wikipedia.org/wiki/Media_type) type in an attempt to render previews for file types that haven't gained explicit support yet.

### :material-image-outline: Images

Images will generate thumbnails the first time they are viewed or since the last time they were modified. Thumbnails are used in the grid view, but not in the Preview Panel. Animated images will play in the Preview Panel.

| Filetype             | Extensions                                         |              Animation              |
| -------------------- | -------------------------------------------------- | :---------------------------------: |
| Animated PNG         | `.apng`                                            | :material-check-circle:{.lg .green} |
| Apple Icon Image     | `.icns`                                            | :material-minus-circle:{.lg .gray}  |
| AVIF                 | `.avif`                                            | :material-minus-circle:{.lg .gray}  |
| Bitmap               | `.bmp`                                             | :material-minus-circle:{.lg .gray}  |
| GIF                  | `.gif`                                             | :material-check-circle:{.lg .green} |
| HEIF                 | `.heif`, `.heic`                                   | :material-minus-circle:{.lg .gray}  |
| JPEG                 | `.jpeg`, `.jpg`, `.jfif`, `.jif`, `.jpg_large`[^1] | :material-minus-circle:{.lg .gray}  |
| JPEG-XL              | `.jxl`                                             |  :material-close-circle:{.lg .red}  |
| OpenEXR              | `.exr`                                             | :material-minus-circle:{.lg .gray}  |
| OpenRaster           | `.ora`                                             | :material-minus-circle:{.lg .gray}  |
| PNG                  | `.png`                                             | :material-minus-circle:{.lg .gray}  |
| SVG                  | `.svg`                                             |  :material-close-circle:{.lg .red}  |
| TIFF                 | `.tiff`, `.tif`                                    | :material-minus-circle:{.lg .gray}  |
| Valve Texture Format | `.vtf`                                             |  :material-close-circle:{.lg .red}  |
| WebP                 | `.webp`                                            | :material-check-circle:{.lg .green} |
| Windows Icon         | `.ico`                                             | :material-minus-circle:{.lg .gray}  |

#### :material-image-outline: RAW Images

| Filetype                         | Extensions             |
| -------------------------------- | ---------------------- |
| Camera Image File Format (Canon) | `.crw`, `.cr2`, `.cr3` |
| Digital Negative                 | `.dng`                 |
| Fuji RAW                         | `.raf`                 |
| Nikon RAW                        | `.nef`, `.nrw`         |
| Olympus RAW                      | `.orf`                 |
| Panasonic RAW                    | `.raw`, `.rw2`         |
| Sony RAW                         | `.arw`                 |

### :material-movie-open: Videos

Video thumbnails will default to the closest viable frame from the middle of the video. Both thumbnail generation and video playback in the Preview Panel requires [FFmpeg](../install.md#third-party-dependencies) installed on your system.

| Filetype              | Extensions              | Dependencies |
| --------------------- | ----------------------- | :----------: |
| 3GP                   | `.3gp`                  |    FFmpeg    |
| AVI                   | `.avi`                  |    FFmpeg    |
| AVIF                  | `.avif`                 |    FFmpeg    |
| FLV                   | `.flv`                  |    FFmpeg    |
| HEVC                  | `.hevc`                 |    FFmpeg    |
| Matroska              | `.mkv`                  |    FFmpeg    |
| MP4                   | `.mp4` , `.m4p`         |    FFmpeg    |
| MPEG Transport Stream | `.ts`                   |    FFmpeg    |
| QuickTime             | `.mov`, `.movie`, `.qt` |    FFmpeg    |
| WebM                  | `.webm`                 |    FFmpeg    |
| WMV                   | `.wmv`                  |    FFmpeg    |

### :material-sine-wave: Audio

Audio thumbnails will default to embedded cover art (if any) andfallback to generated waveform thumbnails. Audio file playback is supported in the Preview Panel if you have [FFmpeg](../install.md#third-party-dependencies) installed on your system. Audio waveforms are currently not cached.

| Filetype            | Extensions               | Dependencies |
| ------------------- | ------------------------ | :----------: |
| AAC                 | `.aac`, `.m4a`           |    FFmpeg    |
| AIFF                | `.aiff`, `.aif`, `.aifc` |    FFmpeg    |
| Apple Lossless[^2]  | `.alac`, `.aac`          |    FFmpeg    |
| FLAC                | `.flac`                  |    FFmpeg    |
| MP3                 | `.mp3`,                  |    FFmpeg    |
| Ogg                 | `.ogg`                   |    FFmpeg    |
| WAVE                | `.wav`, `.wave`          |    FFmpeg    |
| Windows Media Audio | `.wma`                   |    FFmpeg    |

### :material-file-chart: Documents

Preview support for office documents or well-known project file formats varies by the format and whether or not embedded thumbnails are available to be read from. OpenDocument-based files are typically supported.

| Filetype                      | Extensions            | Preview Type                                                               |
| ----------------------------- | --------------------- | -------------------------------------------------------------------------- |
| Blender                       | `.blend`, `.blend<#>` | Embedded thumbnail :material-alert-circle:{ title="If available in file" } |
| Keynote (Apple iWork)         | `.key`                | Embedded thumbnail                                                         |
| Krita[^3]                     | `.kra`, `.krz`        | Embedded thumbnail :material-alert-circle:{ title="If available in file" } |
| MuseScore                     | `.mscz`               | Embedded thumbnail :material-alert-circle:{ title="If available in file" } |
| Numbers (Apple iWork)         | `.numbers`            | Embedded thumbnail                                                         |
| OpenDocument Presentation     | `.odp`, `.fodp`       | Embedded thumbnail                                                         |
| OpenDocument Spreadsheet      | `.ods`, `.fods`       | Embedded thumbnail                                                         |
| OpenDocument Text             | `.odt`, `.fodt`       | Embedded thumbnail                                                         |
| Pages (Apple iWork)           | `.pages`              | Embedded thumbnail                                                         |
| PDF                           | `.pdf`                | First page render                                                          |
| Photoshop                     | `.psd`                | Flattened image render                                                     |
| PowerPoint (Microsoft Office) | `.pptx`, `.ppt`       | Embedded thumbnail :material-alert-circle:{ title="If available in file" } |

### :material-book: eBooks

| Filetype           | Extensions            | Preview Type                 |
| ------------------ | --------------------- | ---------------------------- |
| EPUB               | `.epub`               | Embedded cover               |
| Comic Book Archive | `.cbr`, `.cbt` `.cbz` | Embedded cover or first page |

### :material-cube-outline: 3D Models

<!-- prettier-ignore -->
!!! failure "3D Model Support"
    TagStudio does not currently support previews for 3D model files *(outside of Blender project embedded thumbnails)*. This is on our [roadmap](../updates/roadmap.md#uiux) for future features.

### :material-format-font: Fonts

Font thumbnails will use a "Aa" example preview of the font, with a full alphanumeric of the font available in the Preview Panel.

| Filetype             | Extensions        |
| -------------------- | ----------------- |
| OpenType Font        | `.otf`, `.otc`    |
| TrueType Font        | `.ttf`, `.ttc`    |
| Web Open Font Format | `.woff`, `.woff2` |

### :material-text-box: Text

<!-- prettier-ignore -->
!!! info "Plain Text Support"
    TagStudio supports the *vast* majority of files considered to be "[plain text](https://en.wikipedia.org/wiki/Plain_text)". If an extension or format is not listed here, odds are it's still supported anyway.

Text files render the first 256 bytes of text information to an image preview for thumbnails and the Preview Panel. Improved thumbnails, full scrollable text, and syntax highlighting are on our [roadmap](../updates/roadmap.md#uiux) for future features.

| Filetype   | Extensions                                    |        Syntax Highlighting         |
| ---------- | --------------------------------------------- | :--------------------------------: |
| CSV        | `.csv`                                        | :material-close-circle:{.lg .red}  |
| HTML       | `.html`, `.htm`, `.xhtml`, `.shtml`, `.dhtml` | :material-close-circle:{.lg .red}  |
| JSON       | `.json`, `.jsonc`, `.json5`                   | :material-close-circle:{.lg .red}  |
| Markdown   | `.md`, `.markdown`, `.mkd`, `.rmd`            | :material-close-circle:{.lg .red}  |
| Plain Text | `.txt`, `.text`                               | :material-minus-circle:{.lg .gray} |
| TOML       | `.toml`                                       | :material-close-circle:{.lg .red}  |
| XML        | `.xml`, `.xul`                                | :material-close-circle:{.lg .red}  |
| YAML       | `.yaml`, `.yml`                               | :material-close-circle:{.lg .red}  |

<!-- prettier-ignore-start -->
[^1]:
    The `.jpg_large` extension is unofficial and instead the byproduct of how [Google Chrome used to download images from Twitter](https://fileinfo.com/extension/jpg_large). Since this mangled extension is still in circulation, TagStudio supports it.

[^2]:
    Apple Lossless traditionally uses `.m4a` and `.caf` containers, but may unofficially use the `.alac` extension. The `.m4a` container is also used for separate compressed audio codecs.

[^3]:
    Krita also supports saving projects as OpenRaster `.ora` files. Support for these is listed in the "[Images](#images)" section.

<!-- prettier-ignore-end -->
