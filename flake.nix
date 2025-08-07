{
  description = "TagStudio";

  inputs = {
    flake-parts = {
      url = "github:hercules-ci/flake-parts";
      inputs.nixpkgs-lib.follows = "nixpkgs";
    };

    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

    systems.url = "github:nix-systems/default";
  };

  outputs =
    inputs@{
      flake-parts,
      nixpkgs,
      self,
      ...
    }:
    let
      inherit (nixpkgs) lib;
    in
    flake-parts.lib.mkFlake { inherit inputs; } {
      systems = import inputs.systems;

      perSystem =
        { pkgs, ... }:
        {
          packages =
            let
              python3Packages = pkgs.python312Packages;

              vtf2img = python3Packages.callPackage ./nix/package/vtf2img.nix { };
            in
            rec {
              default = tagstudio;
              tagstudio = pkgs.callPackage ./nix/package {
                # HACK: Remove when PySide6 is bumped to 6.9.x.
                # Sourced from https://github.com/NixOS/nixpkgs/commit/2f9c1ad5e19a6154d541f878774a9aacc27381b7.
                pyside6 =
                  if lib.versionAtLeast python3Packages.pyside6.version "6.9.0" then
                    (python3Packages.pyside6.override {
                      shiboken6 = python3Packages.shiboken6.overrideAttrs {
                        version = "6.8.0.2";

                        src = pkgs.fetchurl {
                          url = "mirror://qt/official_releases/QtForPython/shiboken6/PySide6-6.8.0.2-src/pyside-setup-everywhere-src-6.8.0.tar.xz";
                          hash = "sha256-Ghohmo8yfjQNJYJ1+tOp8mG48EvFcEF0fnPdatJStOE=";
                        };

                        sourceRoot = "pyside-setup-everywhere-src-6.8.0/sources/shiboken6";

                        patches = [ ./nix/package/shiboken6-fix-include-qt-headers.patch ];
                      };
                    }).overrideAttrs
                      { sourceRoot = "pyside-setup-everywhere-src-6.8.0/sources/pyside6"; }
                  else
                    python3Packages.pyside6;

                inherit vtf2img;
              };
              tagstudio-jxl = lib.derivations.warnOnInstantiate 
								"Warning: The jxl fucntionality has been added to the 'tagstudio' package. The 'tagstudio-jxl' package will be removed in a future release." 
								tagstudio;

              inherit vtf2img;
            };

          devShells = rec {
            default = tagstudio;
            tagstudio = import ./nix/shell.nix {
              inherit
                inputs
                lib
                pkgs
                self
                ;
            };
          };

          formatter = pkgs.nixfmt-rfc-style;
        };
    };
}
