# Installation

To download TagStudio, visit the [Releases](https://github.com/TagStudioDev/TagStudio/releases) section of the GitHub repository and download the latest release for your system under the "Assets" section. TagStudio is available for **Windows**, **macOS** _(Apple Silicon & Intel)_, and **Linux**. Windows and Linux builds are also available in portable versions if you want a more self-contained executable to move around.

**We do not currently publish TagStudio to any package managers. Any TagStudio distributions outside of the GitHub releases page are _unofficial_ and not maintained by us.** Installation support will not be given to users installing from unofficial sources. Use these versions at your own risk.

<!-- prettier-ignore -->
!!! info "For macOS Users"
    On macOS, you may be met with a message saying _""TagStudio" can't be opened because Apple cannot check it for malicious software."_ If you encounter this, then you'll need to go to the "Settings" app, navigate to "Privacy & Security", and scroll down to a section that says _""TagStudio" was blocked from use because it is not from an identified developer."_ Click the "Open Anyway" button to allow TagStudio to run. You should only have to do this once after downloading the application.

<!-- prettier-ignore -->
!!! info "For Linux Users"
    On Linux with non-Qt based Desktop Environments you may be unable to open TagStudio. You need to make sure that "xcb-cursor0" or "libxcb-cursor0" packages are installed. For more info check [Missing linux dependencies](https://github.com/TagStudioDev/TagStudio/discussions/182#discussioncomment-9452896)

## Third-Party Dependencies

-   For video thumbnails and playback, you'll also need [FFmpeg](https://ffmpeg.org/download.html) installed on your system. If you encounter any issues with this, please reference our [FFmpeg Help](./help/ffmpeg.md) guide.

## Optional Arguments

Optional arguments to pass to the program:

`--open <path>` / `-o <path>`
: Path to a TagStudio Library folder to open on start.

`--config-file <path>` / `-c <path>`
: Path to the TagStudio config file to load.
