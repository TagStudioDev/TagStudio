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
        let
          python3 = pkgs.python313;
        in
        {
          packages =
            let
              python3Packages = python3.pkgs;

              pillow-jxl-plugin = python3Packages.callPackage ./nix/package/pillow-jxl-plugin.nix {
                inherit (pkgs) cmake;
                inherit pyexiv2;
              };
              pyexiv2 = python3Packages.callPackage ./nix/package/pyexiv2.nix { inherit (pkgs) exiv2; };
            in
            rec {
              default = tagstudio;
              tagstudio = pkgs.callPackage ./nix/package {
                inherit python3Packages;

                inherit pillow-jxl-plugin;
              };
              tagstudio-jxl = tagstudio.override { withJXLSupport = true; };

              inherit pillow-jxl-plugin pyexiv2;
            };

          devShells = rec {
            default = tagstudio;
            tagstudio = import ./nix/shell.nix {
              inherit
                inputs
                lib
                pkgs
                self

                python3
                ;
            };
          };

          formatter = pkgs.nixfmt-rfc-style;
        };
    };
}
