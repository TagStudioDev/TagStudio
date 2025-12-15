---
icon: material/image-check
---

# :material-image-check: Supported Previews

TagStudio offers built-in preview and thumbnail support for a wide variety of file types. Files that don't have explicit support can still be added to your library like normal, they will just show a default icon for thumbnails and previews. TagStudio also references the file's [MIME](https://en.wikipedia.org/wiki/Media_type) type in an attempt to render previews for file types that haven't gained explicit support yet.

### :material-image-outline: Images

Images will generate thumbnails the first time they are viewed or since the last time they were modified. Thumbnails are used in the grid view, but not in the Preview Panel. Animated images will play in the Preview Panel.

| Filetype             | Extensions                                                                              | Animation                           |
|----------------------|-----------------------------------------------------------------------------------------|-------------------------------------|
| Animated PNG         | `.apng`                                                                                 | :material-check-circle:{.lg .green} |
| Apple Icon Image     | `.icns`                                                                                 | :material-minus-circle:{.lg .gray}  |
| AVIF                 | `.avif`                                                                                 | :material-minus-circle:{.lg .gray}  |
| Bitmap               | `.bmp`                                                                                  | :material-minus-circle:{.lg .gray}  |
| GIF                  | `.gif`                                                                                  | :material-check-circle:{.lg .green} |
| HEIF                 | `.heif`, `.heic`                                                                        | :material-minus-circle:{.lg .gray}  |
| JPEG                 | `.jpeg`, `.jpg`, `.jpe`, `.jif`, `.jfif`, `.jfi`, `.jpeg_large`[^1]`, `.jpg_large`[^1], | :material-minus-circle:{.lg .gray}  |
| JPEG 2000            | `.jp2`, `.j2k`, `.jpf`, `.jpm`, `.jpg2`, `.j2c`, `.jpc`, `.jpx`, `.mj2`                 | :material-minus-circle:{.lg .gray}  |
| JPEG-XL              | `.jxl`                                                                                  | :material-close-circle:{.lg .red}   |
| OpenEXR              | `.exr`                                                                                  | :material-minus-circle:{.lg .gray}  |
| OpenRaster           | `.ora`                                                                                  | :material-minus-circle:{.lg .gray}  |
| PNG                  | `.png`                                                                                  | :material-minus-circle:{.lg .gray}  |
| SVG                  | `.svg`                                                                                  | :material-close-circle:{.lg .red}   |
| TIFF                 | `.tiff`, `.tif`                                                                         | :material-minus-circle:{.lg .gray}  |
| Valve Texture Format | `.vtf`                                                                                  | :material-close-circle:{.lg .red}   |
| WebP                 | `.webp`                                                                                 | :material-check-circle:{.lg .green} |
| Windows Icon         | `.ico`                                                                                  | :material-minus-circle:{.lg .gray}  |

#### :material-image-outline: RAW Images

| Filetype                         | Extensions                             |
|----------------------------------|----------------------------------------|
| Aptus RAW                        | `.mos`                                 |
| Camera Image File Format (Canon) | `.crw`, `.cr2`, `.cr3`                 |
| Digital Negative                 | `.dng`                                 |
| Epson RAW                        | `.erf`                                 |
| Fuji RAW                         | `.raf`                                 |
| Hasselblad RAW                   | `.3fr`                                 |
| Kodak RAW                        | `.dcs`, `.dcr`, `.drf`, `.k25`, `.kdc` |
| Mamiya RAW                       | `.mef`                                 |
| Minolta RAW                      | `.mrw`, `.mdc`                         |
| Nikon RAW                        | `.nef`, `.nrw`                         |
| Olympus RAW                      | `.orf`                                 |
| Panasonic RAW                    | `.raw`, `.rw2`                         |
| Pentax RAW                       | `.pef`                                 |
| Samsung RAW                      | `.srw`                                 |
| Sigma RAW                        | `.x3f`                                 |
| Sony RAW                         | `.arw`, `.srf`, `.srf2`, `.sr2`        |

### :material-movie-open: Videos

Video thumbnails will default to the closest viable frame from the middle of the video. Both thumbnail generation and video playback in the Preview Panel requires [FFmpeg](install.md#third-party-dependencies) installed on your system.

| Filetype              | Extensions              | Dependencies |
|-----------------------|-------------------------|--------------|
| 3GP                   | `.3gp`                  | FFmpeg       |
| AVI                   | `.avi`                  | FFmpeg       |
| AVIF                  | `.avif`                 | FFmpeg       |
| FLV                   | `.flv`                  | FFmpeg       |
| GIFV                  | `.gifv`                 | FFmpeg       |
| HEVC                  | `.hevc`                 | FFmpeg       |
| Matroska              | `.mkv`                  | FFmpeg       |
| M4V                   | `.m4v`                  | FFmpeg       |
| MP4                   | `.mp4` , `.m4p`         | FFmpeg       |
| MPEG Transport Stream | `.ts`                   | FFmpeg       |
| QuickTime             | `.mov`, `.movie`, `.qt` | FFmpeg       |
| WebM                  | `.webm`                 | FFmpeg       |
| WMV                   | `.wmv`                  | FFmpeg       |

### :material-sine-wave: Audio

Audio thumbnails will default to embedded cover art (if any) and fallback to generated waveform thumbnails. Audio file playback is supported in the Preview Panel if you have [FFmpeg](install.md#third-party-dependencies) installed on your system. Audio waveforms are currently not cached.

| Filetype            | Extensions               | Dependencies   |
|---------------------|--------------------------|----------------|
| AAC                 | `.aac`, `.m4a`           | FFmpeg         |
| AIFF                | `.aiff`, `.aif`, `.aifc` | FFmpeg         |
| Apple Lossless[^2]  | `.alac`, `.aac`, `.caf`  | FFmpeg         |
| FLAC                | `.flac`                  | FFmpeg         |
| MP3                 | `.mp3`                   | FFmpeg         |
| Ogg                 | `.ogg`                   | FFmpeg         |
| WAVE                | `.wav`, `.wave`          | FFmpeg         |
| Windows Media Audio | `.wma`                   | FFmpeg         |

### :material-file-chart: Documents

Preview support for office documents or well-known project file formats varies by the format and whether or not embedded thumbnails are available to be read from. OpenDocument-based files are typically supported.

| Filetype                      | Extensions            | Preview Type                                                               |
|-------------------------------|-----------------------|----------------------------------------------------------------------------|
| Keynote (Apple iWork)         | `.key`                | Embedded thumbnail                                                         |
| MuseScore                     | `.mscz`               | Embedded thumbnail :material-alert-circle:{ title="If available in file" } |
| Numbers (Apple iWork)         | `.numbers`            | Embedded thumbnail                                                         |
| OpenDocument Presentation     | `.odp`, `.fodp`       | Embedded thumbnail                                                         |
| OpenDocument Spreadsheet      | `.ods`, `.fods`       | Embedded thumbnail                                                         |
| OpenDocument Text             | `.odt`, `.fodt`       | Embedded thumbnail                                                         |
| Pages (Apple iWork)           | `.pages`              | Embedded thumbnail                                                         |
| PDF                           | `.pdf`                | First page render                                                          |
| PowerPoint (Microsoft Office) | `.pptx`, `.ppt`       | Embedded thumbnail :material-alert-circle:{ title="If available in file" } |

### :material-book: eBooks

| Filetype           | Extensions                    | Preview Type                 |
| ------------------ | ----------------------------- | ---------------------------- |
| EPUB               | `.epub`                       | Embedded cover               |
| Comic Book Archive | `.cbr`, `.cbt` `.cbz`, `.cb7` | Embedded cover or first page |

### :material-cube-outline: 3D Models

<!-- prettier-ignore -->
!!! failure "3D Model Support"
    TagStudio does not currently support previews for 3D model files *(outside of Blender project embedded thumbnails)*. This is on our [roadmap](roadmap.md#uiux) for a future release.

| Filetype        | Extensions                        | Preview Type                                                               |
|-----------------|-----------------------------------|----------------------------------------------------------------------------|
| Blender         | `.blend`, `.blend<#>`, `.blen_tc` | Embedded thumbnail :material-alert-circle:{ title="If available in file" } |

### :material-layers: Project

| Filetype                             | Extensions     | Preview Type                                                               |
|--------------------------------------|----------------|----------------------------------------------------------------------------|
| Krita[^3]                            | `.kra`, `.krz` | Embedded thumbnail :material-alert-circle:{ title="If available in file" } |
| Photoshop                            | `.psd`, `.psb` | Flattened image render                                                     |
| Clip Studio Paint                    | `.clip`        | Embedded thumbnail                                                         |
| Mdipack (FireAlpaca, Medibang Paint) | `.mdp`         | Embedded thumbnail                                                         |
| Paint.NET                            | `.pdn`         | Embedded thumbnail                                                         |

### :material-format-font: Fonts

Font thumbnails will use a "Aa" example preview of the font, with a full alphanumeric of the font available in the Preview Panel.

| Filetype             | Extensions        |
|----------------------|-------------------|
| OpenType Font        | `.otf`, `.otc`    |
| TrueType Font        | `.ttf`, `.ttc`    |
| Web Open Font Format | `.woff`, `.woff2` |

### :material-text-box: Text

<!-- prettier-ignore -->
!!! info "Plain Text Support"
    TagStudio supports the *vast* majority of files considered to be "[plain text](https://en.wikipedia.org/wiki/Plain_text)". If an extension or format is not listed here, odds are it's still supported anyway.

Text files render the first 256 bytes of text information to an image preview for thumbnails and the Preview Panel. Improved thumbnails, full scrollable text, and syntax highlighting are on our [roadmap](roadmap.md#uiux) for future features.

| Filetype   | Extensions                                    | Syntax Highlighting                 |
|------------|-----------------------------------------------|-------------------------------------|
| CSV        | `.csv`                                        | :material-close-circle:{.lg .red}   |
| HTML       | `.html`, `.htm`, `.xhtml`, `.shtml`, `.dhtml` | :material-close-circle:{.lg .red}   |
| JSON       | `.json`, `.jsonc`, `.json5`                   | :material-close-circle:{.lg .red}   |
| Markdown   | `.md`, `.markdown`, `.mkd`, `.rmd`            | :material-close-circle:{.lg .red}   |
| Plain Text | `.txt`, `.text`                               | :material-minus-circle:{.lg .gray}  |
| TOML       | `.toml`                                       | :material-close-circle:{.lg .red}   |
| XML        | `.xml`, `.xul`                                | :material-close-circle:{.lg .red}   |
| YAML       | `.yaml`, `.yml`                               | :material-close-circle:{.lg .red}   |

<!-- prettier-ignore-start -->
[^1]:
    The `.jpg_large` and `.jpeg_large` extensions are unofficial and instead the byproduct of how [Google Chrome used to download images from Twitter](https://fileinfo.com/extension/jpg_large). Since these mangled extensions are still in circulation, TagStudio supports them.

[^2]:
    Apple Lossless traditionally uses `.m4a` and `.caf` containers, but may unofficially use the `.alac` extension. The `.m4a` container is also used for separate compressed audio codecs.

[^3]:
    Krita also supports saving projects as OpenRaster `.ora` files. Support for these is listed in the "[Images](#images)" section.

<!-- prettier-ignore-end -->
