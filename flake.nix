# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: MIT

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
        { pkgs, self', ... }:
        let
          python3 = builtins.head python3Versions;
          python3Versions = with pkgs; [ python314 ];
        in
        {
          packages =
            let
              pythonDerivations = lib.genAttrs' python3Versions (
                python3:
                lib.nameValuePair python3.pythonAttr (
                  let
                    python3Packages = python3.pkgs;

                    tagstudio = pkgs.callPackage ./nix/package {
                      inherit python3Packages;

                      inherit pillow-jxl-plugin;
                    };

                    openexr = python3Packages.callPackage ./nix/package/openexr.nix { inherit (pkgs) openexr; };
                    pillow-jxl-plugin = python3Packages.callPackage ./nix/package/pillow-jxl-plugin.nix {
                      inherit (pkgs) cmake;
                      inherit openexr pyexiv2;
                    };
                    pyexiv2 = python3Packages.callPackage ./nix/package/pyexiv2.nix { inherit (pkgs) exiv2; };
                  in
                  {
                    inherit tagstudio;
                    tagstudio-jxl = tagstudio.override { withJXLSupport = true; };

                    inherit openexr pillow-jxl-plugin pyexiv2;
                  }
                )
              );
            in
            (lib.concatMapAttrs (
              pythonAttr: lib.mapAttrs' (name: lib.nameValuePair "${pythonAttr}Packages_${name}")
            ) pythonDerivations)
            // pythonDerivations.${python3.pythonAttr}
            // {
              default = self'.packages.tagstudio;
            };

          devShells = {
            default = self'.devShells.tagstudio;
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
