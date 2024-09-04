FFmpeg is required for thumbnail previews and playback features on audio and video files. FFmpeg is a free Open Source project dedicated to the handling of multimedia (video, audio, etc) files.

# Installation on Windows
---
## Prebuilt Binaries
Pre-built binaries from trusted sources are available on the [FFmpeg website](https://www.ffmpeg.org/download.html#build-windows).

To install:
1. Download 7z or zip file and extract it (right click > Extract All)
2. Move extracted contents to a unique folder (i.e; `c:\ffmpeg` or `c:\Program Files\ffmpeg`)
3. Add FFmpeg to your PATH
    a. Go to "Edit the system environment variables"
    b. Under "User Variables", select "Path" then edit
    c. Click new and add `<Your folder>\bin` (e.g; `c:\ffmpeg\bin` or `c:\Program Files\ffmpeg\bin`)
    d. Click okay

## Package Managers
FFmpeg is also available from:

1. WinGet (`winget install ffmpeg)
2. Scoop (`scoop install main/ffmpeg`)
3. Chocolatey (`choco install ffmpeg-full`)

# Installation on Mac
---
## Homebrew
FFmpeg is available via Homebrew and can be installed via;

`brew install ffmpeg`

# Installation on Linux
---
## Package Managers
FFmpeg may be installed by default on some Linux distrobutions, but if not, it is available via your distro's package manager of choice

1. Debian/Ubuntu (`sudo apt install ffmpeg`)
2. Fedora (`sudo dnf install ffmpeg-free`)
3. Arch (`sudo pacman -S ffmpeg`)

# Help
---
For additional help, please create an Issue on the [GitHub repository](https://github.com/TagStudioDev/TagStudio) or join the [Discord]()
