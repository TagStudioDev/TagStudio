{
  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";

    qt6Nixpkgs = {
      # Commit bumping to qt6.6.3
      url = "github:NixOS/nixpkgs/f862bd46d3020bcfe7195b3dad638329271b0524"; 
    };
  };

  outputs = { self, nixpkgs, qt6Nixpkgs }:
  let
    pkgs = nixpkgs.legacyPackages.x86_64-linux;

    qt6Pkgs = qt6Nixpkgs.legacyPackages.x86_64-linux;
  in {
    devShells.x86_64-linux.default = pkgs.mkShell {
      LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [
        pkgs.gcc-unwrapped
        pkgs.zlib
        pkgs.libglvnd
        pkgs.glib
        pkgs.stdenv.cc.cc
        pkgs.fontconfig
        pkgs.libxkbcommon
        pkgs.xorg.libxcb
        pkgs.freetype
        pkgs.dbus
        pkgs.zstd
        # For PySide6 Multimedia
        pkgs.libpulseaudio
        pkgs.libkrb5

        qt6Pkgs.qt6.qtwayland
        qt6Pkgs.qt6.full
        qt6Pkgs.qt6.qtbase
      ];
      buildInputs = with pkgs; [
        cmake
        gdb
        zstd
        python312Packages.pip
        python312Full
        python312Packages.virtualenv # run virtualenv .
        python312Packages.pyusb # fixes the pyusb 'No backend available' when installed directly via pip

        libgcc
        makeWrapper
        bashInteractive
        glib
        libxkbcommon
        freetype
        binutils
        dbus
        coreutils
        libGL
        libGLU
        fontconfig
        xorg.libxcb

        # this is for the shellhook portion
        makeWrapper
        bashInteractive
      ] ++ [
        qt6Pkgs.qt6.qtbase
        qt6Pkgs.qt6.full
        qt6Pkgs.qt6.qtwayland
        qt6Pkgs.qtcreator

        # this is for the shellhook portion
        qt6Pkgs.qt6.wrapQtAppsHook
      ];
      # set the environment variables that Qt apps expect
      shellHook = ''
        export QT_QPA_PLATFORM=wayland
        export LIBRARY_PATH=/usr/lib:/usr/lib64:$LIBRARY_PATH
        # export LD_LIBRARY_PATH=${pkgs.stdenv.cc.cc.lib}/lib/:/run/opengl-driver/lib/
        export QT_PLUGIN_PATH=${pkgs.qt6.qtbase}/${pkgs.qt6.qtbase.qtPluginPrefix}
        bashdir=$(mktemp -d)
        makeWrapper "$(type -p bash)" "$bashdir/bash" "''${qtWrapperArgs[@]}"
        exec "$bashdir/bash"
      '';
    };
  };
}
