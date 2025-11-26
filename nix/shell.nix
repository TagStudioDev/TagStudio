{
  lib,
  pkgs,

  python3,
  ...
}:

let
  pythonLibraryPath =
    with pkgs;
    lib.makeLibraryPath (
      [
        fontconfig
        freetype
        glib
        qt6.qtbase
        stdenv.cc.cc
        zstd
      ]
      ++ lib.optionals (!stdenv.isDarwin) [
        dbus
        libGL
        libdrm
        libpulseaudio
        libva
        libxkbcommon
        pipewire
        qt6.qtwayland
        xorg.libX11
        xorg.libXrandr
      ]
    );

  libraryPath = "${lib.optionalString pkgs.stdenv.isDarwin "DY"}LD_LIBRARY_PATH";

  python3Wrapped = pkgs.symlinkJoin {
    inherit (python3)
      name
      pname
      version
      meta
      ;

    paths = [ python3 ];

    nativeBuildInputs = with pkgs; [
      makeWrapper
      qt6.wrapQtAppsHook

      # Should be unnecessary once PR is pulled.
      # PR: https://github.com/NixOS/nixpkgs/pull/271037
      # Issue: https://github.com/NixOS/nixpkgs/issues/149812
      wrapGAppsHook3
    ];
    buildInputs = with pkgs.qt6; [
      qtbase
      qtmultimedia
    ];

    postBuild = ''
      wrapProgram $out/bin/${python3.meta.mainProgram} \
        --suffix ${libraryPath} : ${pythonLibraryPath} \
        "''${gappsWrapperArgs[@]}" \
        "''${qtWrapperArgs[@]}"
    '';

    dontWrapGApps = true;
    dontWrapQtApps = true;
  };
in
pkgs.mkShellNoCC {
  nativeBuildInputs = with pkgs; [
    coreutils
    uv

    ruff
  ];
  buildInputs = [
    python3Wrapped
  ]
  ++ (with pkgs; [
    ffmpeg-headless
    ripgrep
  ]);

  env = {
    QT_QPA_PLATFORM = "wayland;xcb";

    UV_NO_SYNC = 1;
    UV_PYTHON_DOWNLOADS = "never";
  };

  shellHook =
    let
      python = lib.getExe python3Wrapped;

      # PySide/Qt are very particular about matching versions. Override with nixpkgs package.
      pythonPath = lib.makeSearchPathOutput "lib" python3.sitePackages (
        with python3.pkgs; [ pyside6 ] ++ pyside6.propagatedBuildInputs or [ ]
      );
    in
    # bash
    ''
      venv=''${UV_PROJECT_ENVIRONMENT:-.venv}

      if [ ! -f "''${venv}"/bin/activate ] || [ "$(readlink -f "''${venv}"/bin/python)" != "$(readlink -f ${python})" ]; then
          printf '%s\n' 'Regenerating virtual environment, Python interpreter changed...' >&2
          rm -rf "''${venv}"
          uv venv --python ${python} "''${venv}"
      fi

      source "''${venv}"/bin/activate
      PYTHONPATH=${pythonPath}''${PYTHONPATH:+:''${PYTHONPATH}}
      export PYTHONPATH

      if [ ! -f "''${venv}"/pyproject.toml ] || ! diff --brief pyproject.toml "''${venv}"/pyproject.toml >/dev/null; then
          printf '%s\n' 'Installing dependencies, pyproject.toml changed...' >&2
          uv pip install --quiet --editable '.[mkdocs,mypy,pre-commit,pytest]'
          cp pyproject.toml "''${venv}"/pyproject.toml
      fi

      pre-commit install
    '';

  meta = {
    maintainers = with lib.maintainers; [ xarvex ];
    platforms = lib.platforms.unix;
  };
}
