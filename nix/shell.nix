{
  inputs,
  lib,
  pkgs,
  ...
}:

let
  qt6Pkgs = import inputs.nixpkgs-qt6 { inherit (pkgs) system; };

  pythonLibraryPath = lib.makeLibraryPath (
    (with pkgs; [
      fontconfig.lib
      freetype
      glib
      stdenv.cc.cc.lib
      zstd
    ])
    ++ (with qt6Pkgs.qt6; [ qtbase ])
    ++ lib.optionals (!pkgs.stdenv.isDarwin) (
      (with pkgs; [
        dbus.lib
        libGL
        libdrm
        libpulseaudio
        libva
        libxkbcommon
        pipewire
        xorg.libX11
        xorg.libXrandr
      ])
      ++ (with qt6Pkgs.qt6; [ qtwayland ])
    )
  );
  libraryPath = "${lib.optionalString pkgs.stdenv.isDarwin "DY"}LD_LIBRARY_PATH";

  python = pkgs.python312;
  pythonWrapped = pkgs.symlinkJoin {
    inherit (python)
      name
      pname
      version
      meta
      ;

    paths = [ python ];

    nativeBuildInputs = (with pkgs; [ makeWrapper ]) ++ (with qt6Pkgs.qt6; [ wrapQtAppsHook ]);
    buildInputs = with qt6Pkgs.qt6; [ qtbase ];

    postBuild = ''
      wrapProgram $out/bin/python3.12 \
        --prefix ${libraryPath} : ${pythonLibraryPath} \
        "''${qtWrapperArgs[@]}"
    '';
  };
in
pkgs.mkShellNoCC {
  nativeBuildInputs = with pkgs; [
    coreutils

    ruff
  ];
  buildInputs = [ pythonWrapped ] ++ (with pkgs; [ ffmpeg-headless ]);

  env.QT_QPA_PLATFORM = "wayland;xcb";

  shellHook =
    let
      python = lib.getExe pythonWrapped;
    in
    # bash
    ''
      if [ ! -f .venv/bin/activate ] || [ "$(readlink -f .venv/bin/python)" != "$(readlink -f ${python})" ]; then
          printf '%s\n' 'Regenerating virtual environment, Python interpreter changed...' >&2
          rm -rf .venv
          ${python} -m venv .venv
      fi

      source .venv/bin/activate

      if [ ! -f .venv/pyproject.toml ] || [ "$(cat .venv/pyproject.toml)" != "$(cat pyproject.toml)" ]; then
          printf '%s\n' 'Installing dependencies, pyproject.toml changed...' >&2
          pip install --quiet --editable '.[mkdocs,mypy,pytest]'
          cp pyproject.toml .venv/pyproject.toml
      fi
    '';

  meta = {
    maintainers = with lib.maintainers; [ xarvex ];
    platforms = lib.platforms.unix;
  };
}
