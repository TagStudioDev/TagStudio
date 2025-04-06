# Installation

TagStudio provides [releases](https://github.com/TagStudioDev/TagStudio/releases) as well as full access to its [source code](https://github.com/TagStudioDev/TagStudio) under the [GPLv3](https://github.com/TagStudioDev/TagStudio/blob/main/LICENSE) license.

## Executables

To download executable builds of TagStudio, visit the [Releases](https://github.com/TagStudioDev/TagStudio/releases) page of the GitHub repository and download the latest release for your system under the "Assets" section at the bottom of the release.

TagStudio has builds for **Windows**, **macOS** _(Apple Silicon & Intel)_, and **Linux**. We also offer portable releases for Windows and Linux which are self-contained and easier to move around.

<!-- prettier-ignore -->
!!! info "Third-Party Dependencies"
    You may need to install [third-party dependencies](#third-party-dependencies) such as [FFmpeg](https://ffmpeg.org/download.html) to use the full feature set of TagStudio.

<!-- prettier-ignore -->
!!! warning "For macOS Users"
    On macOS, you may be met with a message saying "**"TagStudio" can't be opened because Apple cannot check it for malicious software.**" If you encounter this, then you'll need to go to the "Settings" app, navigate to "Privacy & Security", and scroll down to a section that says "**"TagStudio" was blocked from use because it is not from an identified developer.**" Click the "Open Anyway" button to allow TagStudio to run. You should only have to do this once after downloading the application.

---

## Package Managers

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
    pip install -e ".[dev]"
    ```
    _See more under "[Developing](./develop.md)"_

TagStudio can now be launched via the `tagstudio` command in your terminal.

---

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

## Third-Party Dependencies

For audio/video thumbnails and playback you'll need [FFmpeg](https://ffmpeg.org/download.html) installed on your system. If you encounter any issues with this, please reference our [FFmpeg Help](./help/ffmpeg.md) guide.

You can check to see if FFmpeg and FFprobe are correctly located by launching TagStudio and going to "About TagStudio" in the menu bar.
