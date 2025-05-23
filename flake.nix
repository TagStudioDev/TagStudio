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
              pythonPackages = pkgs.python312Packages;

              pillow-jxl-plugin = pythonPackages.callPackage ./nix/package/pillow-jxl-plugin.nix {
                inherit (pkgs) cmake;
                inherit pyexiv2;
                inherit (pkgs) rustPlatform;
              };
              pyexiv2 = pythonPackages.callPackage ./nix/package/pyexiv2.nix { inherit (pkgs) exiv2; };
              vtf2img = pythonPackages.callPackage ./nix/package/vtf2img.nix { };
            in
            rec {
              default = tagstudio;
              tagstudio = pythonPackages.callPackage ./nix/package {
                inherit pillow-jxl-plugin vtf2img;
              };
              tagstudio-jxl = tagstudio.override { withJXLSupport = true; };

              inherit pillow-jxl-plugin pyexiv2 vtf2img;
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
