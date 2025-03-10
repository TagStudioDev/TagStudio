# Installation

## Releases

TagStudio provides executable [releases](https://github.com/TagStudioDev/TagStudio/releases) as well as full access to its [source code](https://github.com/TagStudioDev/TagStudio) under the [GPLv3](https://github.com/TagStudioDev/TagStudio/blob/main/LICENSE) license.

To download executable builds of TagStudio, visit the [Releases](https://github.com/TagStudioDev/TagStudio/releases) page of the GitHub repository and download the latest release for your system under the "Assets" section at the bottom of the release.

TagStudio has builds for **Windows**, **macOS** _(Apple Silicon & Intel)_, and **Linux**. We also offer portable releases for Windows and Linux which are self-contained and easier to move around.

<!-- prettier-ignore -->
!!! info "For macOS Users"
    On macOS, you may be met with a message saying "**"TagStudio" can't be opened because Apple cannot check it for malicious software.**" If you encounter this, then you'll need to go to the "Settings" app, navigate to "Privacy & Security", and scroll down to a section that says "**"TagStudio" was blocked from use because it is not from an identified developer.**" Click the "Open Anyway" button to allow TagStudio to run. You should only have to do this once after downloading the application.

### Package Managers

<!-- prettier-ignore -->
!!! danger "Unofficial Releases"
    **We do not currently publish TagStudio to _remote_ package repositories. Any TagStudio distributions outside of the [GitHub repository](https://github.com/TagStudioDev/TagStudio) are _unofficial_ and not maintained by us!**

    Installation support will not be given to users installing from unofficial sources. Use these versions at your own risk!

### Installing with PIP

TagStudio is installable via [PIP](https://pip.pypa.io/). Note that since we don't currently distribute on PyPI, the repository needs to be cloned and installed locally. Make sure you have Python 3.12 and PIP installed if you choose to install using this method.

The repository can be cloned/downloaded via `git` in your terminal, or by downloading the zip file from the "Code" button on the [repository page](https://github.com/TagStudioDev/TagStudio).

```sh
git clone https://github.com/TagStudioDev/TagStudio.git
```

Once cloned or downloaded, you can install TagStudio with the following PIP command:

```sh
pip install .
```

<!-- prettier-ignore -->
!!! note "Developer Dependencies"
    If you wish to create an editable install with the additional dependencies required for developing TagStudio, use this modified PIP command instead:
    ```sh
    pip install -e .[dev]
    ```
    _See more under "[Creating a Development Environment](#creating-a-development-environment)"_

TagStudio can now be launched via the `tagstudio` command in your terminal.

### Linux

Some external dependencies are required for TagStudio to execute. Below is a table of known packages that will be necessary.

<!-- prettier-ignore -->
| Package | Reason |
|--------------- | --------------- |
| [dbus](https://repology.org/project/dbus) | required for Qt; opening desktop applications |
| [ffmpeg](https://repology.org/project/ffmpeg) | audio/video playback |
| libstdc++ | required for Qt |
| [libva](https://repology.org/project/libva) | hardware rendering with [VAAPI](https://www.freedesktop.org/wiki/Software/vaapi) |
| [libvdpau](https://repology.org/project/libvdpau) | hardware rendering with [VDPAU](https://www.freedesktop.org/wiki/Software/VDPAU) |
| [libx11](https://repology.org/project/libx11) | required for Qt |
| libxcb-cursor OR [xcb-util-cursor](https://repology.org/project/xcb-util-cursor) | required for Qt |
| [libxkbcommon](https://repology.org/project/libxkbcommon) | required for Qt |
| [libxrandr](https://repology.org/project/libxrandr) | hardware rendering |
| [pipewire](https://repology.org/project/pipewire) | PipeWire audio support |
| [qt](https://repology.org/project/qt) | required |
| [qt-multimedia](https://repology.org/project/qt) | required |
| [qt-wayland](https://repology.org/project/qt) | Wayland support |

### Nix(OS)

For [Nix(OS)](https://nixos.org/), the TagStudio repository includes a [flake](https://wiki.nixos.org/wiki/Flakes) that provides some outputs such as a development shell and package.

Two packages are provided: `tagstudio` and `tagstudio-jxl`. The distinction was made because `tagstudio-jxl` has an extra compilation step for [JPEG-XL](https://jpeg.org/jpegxl) image support. To give either of them a test run, you can execute `nix run github:TagStudioDev/TagStudio#tagstudio`. If you are in a cloned repository and wish to run a package with the context of the repository, you can simply use `nix run` with no arguments.

`nix build` can be used in place of `nix run` if you only want to build. **The packages will only build if tests pass.**

<!-- prettier-ignore -->
!!! info "Nix Support"
    Support for Nix is handled on a best-effort basis by one of our maintainers. Issues related to Nix may be slower to resolve, and could require further details.

Want to add TagStudio into your configuration?

This can be done by first adding the flake input into your `flake.nix`:

```nix title="flake.nix"
{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

    tagstudio = {
      url = "github:TagStudioDev/TagStudio";
      inputs.nixpkgs.follows = "nixpkgs"; # Use the same package set as your flake.
    };
  };
}
```

Then, make sure you add the `inputs` context to your configuration:

<!-- prettier-ignore-start -->
=== "NixOS with Home Manager"
    ```nix title="flake.nix"
    {
      outputs =
        inputs@{ home-manager, nixpkgs, ... }:
          {
            nixosConfigurations.HOSTNAME = nixpkgs.lib.nixosSystem {
              system = "x86_64-linux";

              specialArgs = { inherit inputs; };
              modules = [
                ./configuration.nix

                home-manager.nixosModules.home-manager
                {
                  home-manager = {
                    useGlobalPkgs = true;
                    useUserPackages = true;

                    extraSpecialArgs = { inherit inputs; };
                    users.USER.imports = [
                      ./home.nix
                    ];
                  };
                }
              ];
            };
          };
    }
    ```
<!-- prettier-ignore-end -->

<!-- prettier-ignore-start -->
=== "NixOS"
    ```nix title="flake.nix"
    {
      outputs =
        inputs@{ nixpkgs, ... }:
          {
            nixosConfigurations.HOSTNAME = nixpkgs.lib.nixosSystem {
              system = "x86_64-linux";

              specialArgs = { inherit inputs; };
              modules = [
                ./configuration.nix
              ];
            };
          };
    }
    ```
=== "Home Manager (standalone)"
    ```nix title="flake.nix"
    {
      outputs =
        inputs@{ home-manager, nixpkgs, ... }:
        let
          pkgs = import nixpkgs {
            system = "x86_64-linux";
          };
        in
        {
          homeConfigurations.USER = home-manager.lib.homeManagerConfiguration {
            inherit pkgs;

            extraSpecialArgs = { inherit inputs; };
            modules = [
              ./home.nix
            ];
          };
        };
    }
    ```
<!-- prettier-ignore-end -->

Finally, `inputs` can be used in a module to add the package to your packages list:

<!-- prettier-ignore-start -->
=== "Home Manager module"
    ```nix title="home.nix"
    { inputs, pkgs, ... }:

    {
      home.packages = [
        inputs.tagstudio.packages.${pkgs.stdenv.hostPlatform.system}.tagstudio
      ];
    }
    ```
<!-- prettier-ignore-end -->

<!-- prettier-ignore-start -->
=== "NixOS module"
    ```nix title="configuration.nix"
    { inputs, pkgs, ... }:

    {
      environment.systemPackages = [
        inputs.tagstudio.packages.${pkgs.stdenv.hostPlatform.system}.tagstudio
      ];
    }
    ```
<!-- prettier-ignore-end -->

Don't forget to rebuild!

## Creating a Development Environment

If you wish to develop for TagStudio, you'll need to create a development environment by installing the required dependencies. You have a number of options depending on your level of experience and familiarly with existing Python toolchains.

<!-- prettier-ignore -->
!!! tip "Contributing"
    If you wish to contribute to TagStudio's development, please read our [CONTRIBUTING.md](https://github.com/TagStudioDev/TagStudio/blob/main/CONTRIBUTING.md)!

### Install Python

Python [3.12](https://www.python.org/downloads/) is required to develop for TagStudio. Any version matching "Python 3.12.x" should work, with "x" being any number. Alternatively you can use a tool such as [pyenv](https://github.com/pyenv/pyenv/) to install this version of Python without affecting any existing Python installations on your system.

<!-- prettier-ignore -->
!!! info "Python Aliases"
    Depending on your system, Python may be called `python`, `py`, `python3`, or `py3`. These instructions use the alias `python` for consistency.

If you already have Python installed on your system, you can check the version by running the following command:

```sh
python --version
```

#### Installing with pyenv

If you choose to install Python using pyenv, please refer to the following instructions:

1. Follow pyenv's [install instructions](https://github.com/pyenv/pyenv/?tab=readme-ov-file#installation) for your system.
2. Install the appropriate Python version with pyenv by running `pyenv install 3.12` (This will **not** mess with your existing Python installation).
3. Navigate to the repository root folder in your terminal and run `pyenv local 3.12`. You could alternatively use `pyenv shell 3.12` or `pyenv global 3.12` instead to set the Python version for the current terminal session or the entire system respectively, however using `local` is recommended.

### Installing Dependencies

To install the required dependencies, you can use a dependency manager such as [uv](https://docs.astral.sh/uv) or [Poetry 2.0](https://python-poetry.org). Alternatively you can create a virtual environment and manually install the dependencies yourself.

#### Installing with uv

If using [uv](https://docs.astral.sh/uv), you can install the dependencies for TagStudio with the following command:

```sh
uv pip install -e .[dev]
```

#### Installing with Poetry

If using [Poetry](https://python-poetry.org), you can install the dependencies for TagStudio with the following command:

```sh
poetry install --with dev
```

#### Installing with Nix

If using [Nix](https://nixos.org/), there is a development environment already provided in the [flake](https://wiki.nixos.org/wiki/Flakes) that is accessible with the following command:

```sh
nix develop
```

You can automatically enter this development shell, and keep your user shell, with a tool like [direnv](https://direnv.net/). A reference `.envrc` is provided in the repository; to use it:

```sh
ln -s .envrc.recommended .envrc
```

You will have to allow usage of it.

<!-- prettier-ignore -->
!!! warning "`.envrc` Security"
    These files are generally a good idea to check, as they execute commands on directory load. direnv has a security framework to only run `.envrc` files you have allowed, and does keep track on if it has changed. So, with that being said, the file may need to be allowed again if modifications are made.

```sh
cat .envrc # You are checking them, right?
direnv allow
```

#### Manual Installation

If you choose to manually set up a virtual environment and install dependencies instead of using a dependency manager, please refer to the following instructions:

<!-- prettier-ignore -->
!!! tip "Virtual Environments"
    Learn more about setting up a virtual environment with Python's [official tutorial](https://docs.python.org/3/tutorial/venv.html).

1.  In the root repository directory, create a python virtual environment:

    ```sh
    python -m venv .venv
    ```

2.  Activate your environment:

    -   Windows w/Powershell: `.venv\Scripts\Activate.ps1`
    -   Windows w/Command Prompt: `.venv\Scripts\activate.bat`
    -   Linux/macOS: `source .venv/bin/activate`

    <!-- prettier-ignore -->
    !!! info "Supported Shells"
        Depending on your system, the regular activation script _might_ not work on alternative shells. In this case, refer to the table below for supported shells:

        |      Shell | Script                    |
        | ---------: | :------------------------ |
        |   Bash/ZSH | `.venv/bin/activate`      |
        |       Fish | `.venv/bin/activate.fish` |
        |   CSH/TCSH | `.venv/bin/activate.csh`  |
        | PowerShell | `.venv/bin/activate.ps1`  |

3.  Use the following PIP command to create an editable installation and install the required development dependencies:

    ```sh
    pip install -e .[dev]
    ```

### Launching

The entry point for TagStudio is `src/tagstudio/main.py`. You can target this file from your IDE to run or connect a debug session. The example(s) below show off example launch scripts for different IDEs. Here you can also take advantage of [launch arguments](#launch-arguments) to pass your own test [libraries](./library/index.md) to use while developing.

<!-- prettier-ignore -->
=== "VS Code"
    ```json title=".vscode/launch.json"
    {
        // Use IntelliSense to learn about possible attributes.
        // Hover to view descriptions of existing attributes.
        // For more information, visit: https://go.microsoft.com/fwlink/?linkid=830387
        "version": "0.2.0",
        "configurations": [
            {
                "name": "TagStudio",
                "type": "python",
                "request": "launch",
                "program": "${workspaceRoot}/src/tagstudio/main.py",
                "console": "integratedTerminal",
                "justMyCode": true,
                "args": ["-o", "~/Documents/Example"]
            }
        ]
    }
    ```

## Building

To build your own executables of TagStudio, first follow the steps in "[Installing with PIP](#installing-with-pip)" including the developer dependencies step. Once that's complete, run the following PyInstaller command:

```
pyinstaller tagstudio.spec
```

If you're on Windows or Linux and wish to build a portable executable, then pass the following flag:

```
pyinstaller tagstudio.spec -- --portable
```

The resulting executable file(s) will be located in a new folder named "dist".

## Third-Party Dependencies

For audio/video thumbnails and playback you'll also need [FFmpeg](https://ffmpeg.org/download.html) installed on your system. If you encounter any issues with this, please reference our [FFmpeg Help](./help/ffmpeg.md) guide.

You can check to see if FFmpeg and FFprobe are correctly located by launching TagStudio and going to "About TagStudio" in the menu bar.

## Launch Arguments

There are a handful of launch arguments you can pass to TagStudio via the command line or a desktop shortcut.

| Argument               | Short | Description                                          |
| ---------------------- | ----- | ---------------------------------------------------- |
| `--open <path>`        | `-o`  | Path to a TagStudio Library folder to open on start. |
| `--config-file <path>` | `-c`  | Path to the TagStudio config file to load.           |
