{
  description = "TagStudio";

  inputs = {
    devenv.url = "github:cachix/devenv";

    devenv-root = {
      url = "file+file:///dev/null";
      flake = false;
    };

    flake-parts = {
      url = "github:hercules-ci/flake-parts";
      inputs.nixpkgs-lib.follows = "nixpkgs";
    };

    nix2container = {
      url = "github:nlewo/nix2container";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";

    # Pinned to Qt version 6.7.1
    nixpkgs-qt6.url = "github:NixOS/nixpkgs/e6cea36f83499eb4e9cd184c8a8e823296b50ad5";

    systems.url = "github:nix-systems/default-linux";
  };

  outputs =
    {
      flake-parts,
      nixpkgs,
      nixpkgs-qt6,
      self,
      systems,
      ...
    }@inputs:
    flake-parts.lib.mkFlake { inherit inputs; } {
      imports = [ inputs.devenv.flakeModule ];

      systems = import systems;

      perSystem =
        {
          config,
          pkgs,
          system,
          ...
        }:
        let
          inherit (nixpkgs) lib;

          qt6Pkgs = import nixpkgs-qt6 { inherit system; };
        in
        {
          formatter = pkgs.nixfmt-rfc-style;

          devenv.shells = rec {
            default = tagstudio;

            tagstudio =
              let
                cfg = config.devenv.shells.tagstudio;
              in
              {
                # NOTE: many things were simply transferred over from previous,
                # there must be additional work in ensuring all relevant dependencies
                # are in place (and no extraneous). I have already spent much
                # work making this in the first place and just need to get it out
                # there, especially after my promises. Would appreciate any help
                # (possibly PRs!) on taking care of this. Otherwise, just expect
                # this to get ironed out over time.
                #
                # Thank you! -Xarvex

                devenv.root =
                  let
                    devenvRoot = builtins.readFile inputs.devenv-root.outPath;
                  in
                  # If not overriden (/dev/null), --impure is necessary.
                  pkgs.lib.mkIf (devenvRoot != "") devenvRoot;

                name = "TagStudio";

                # Derived from previous flake iteration.
                packages =
                  (with pkgs; [
                    cmake
                    binutils
                    coreutils
                    dbus
                    fontconfig
                    freetype
                    gdb
                    glib
                    libGL
                    libGLU
                    libgcc
                    libxkbcommon
                    mypy
                    ruff
                    xorg.libxcb
                    xorg.libX11
                    zstd
                  ])
                  ++ (with qt6Pkgs; [
                    qt6.full
                    qt6.qtbase
                    qt6.qtwayland
                    qtcreator
                  ]);

                enterShell =
                  let
                    setQtEnv =
                      pkgs.runCommand "set-qt-env"
                        {
                          buildInputs = with qt6Pkgs.qt6; [
                            qtbase
                          ];

                          nativeBuildInputs =
                            (with pkgs; [
                              makeShellWrapper
                            ])
                            ++ (with qt6Pkgs.qt6; [
                              wrapQtAppsHook
                            ]);
                        }
                        ''
                          makeShellWrapper "$(type -p sh)" "$out" "''${qtWrapperArgs[@]}"
                          sed "/^exec/d" -i "$out"
                        '';
                  in
                  ''
                    source ${setQtEnv}
                  '';

                scripts.tagstudio.exec = ''
                  python ${cfg.devenv.root}/tagstudio/tag_studio.py
                '';

                env = {
                  QT_QPA_PLATFORM = "wayland;xcb";

                  # Derived from previous flake iteration.
                  # Not desired given LD_LIBRARY_PATH pollution.
                  # See supposed alternative below, further research required.
                  LD_LIBRARY_PATH = lib.makeLibraryPath (
                    (with pkgs; [
                      dbus
                      fontconfig
                      freetype
                      gcc-unwrapped
                      glib
                      libglvnd
                      libkrb5
                      libpulseaudio
                      libva
                      libxkbcommon
                      openssl
                      stdenv.cc.cc.lib
                      wayland
                      xorg.libxcb
                      xorg.libX11
                      xorg.libXrandr
                      zlib
                      zstd
                    ])
                    ++ (with qt6Pkgs.qt6; [
                      qtbase
                      qtwayland
                      full
                    ])
                  );
                };

                languages.python = {
                  enable = true;
                  venv = {
                    enable = true;
                    quiet = true;
                    requirements =
                      let
                        excludeDeps =
                          req: deps:
                          builtins.concatStringsSep "\n" (
                            builtins.filter (line: !(lib.any (elem: lib.hasPrefix elem line) deps)) (lib.splitString "\n" req)
                          );
                      in
                      ''
                        ${builtins.readFile ./requirements.txt}
                        ${excludeDeps (builtins.readFile ./requirements-dev.txt) [
                          "mypy"
                          "ruff"
                        ]}
                      '';
                  };

                  # Should be able to replace LD_LIBRARY_PATH?
                  # Was not quite able to get working,
                  # will be consulting cachix community. -Xarvex
                  # libraries = with pkgs; [ ];
                };
              };
          };
        };
    };
}
