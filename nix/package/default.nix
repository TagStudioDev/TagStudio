{
  ffmpeg-headless,
  lib,
  pipewire,
  python3Packages,
  qt6,
  ripgrep,
  stdenv,
  wrapGAppsHook,

  pillow-jxl-plugin,

  withJXLSupport ? false,
}:

let
  pyproject = (lib.importTOML ../../pyproject.toml).project;
in
python3Packages.buildPythonApplication {
  pname = pyproject.name;
  inherit (pyproject) version;
  pyproject = true;

  src = ../../.;

  nativeBuildInputs = [
    python3Packages.pythonRelaxDepsHook
    qt6.wrapQtAppsHook

    # Should be unnecessary once PR is pulled.
    # PR: https://github.com/NixOS/nixpkgs/pull/271037
    # Issue: https://github.com/NixOS/nixpkgs/issues/149812
    wrapGAppsHook
  ];
  buildInputs = [
    qt6.qtbase
    qt6.qtmultimedia
  ];

  nativeCheckInputs = with python3Packages; [
    pytest-qt
    pytest-xdist
    pytestCheckHook
    syrupy
  ];

  # TODO: Install more icon resolutions when available.
  preInstall = ''
    mkdir -p $out/share/applications $out/share/icons/hicolor/512x512/apps

    cp $src/src/tagstudio/resources/tagstudio.desktop $out/share/applications
    cp $src/src/tagstudio/resources/icon.png $out/share/icons/hicolor/512x512/apps/tagstudio.png
  '';

  dontWrapGApps = true;
  dontWrapQtApps = true;
  makeWrapperArgs = [
    "--suffix PATH : ${
      lib.makeBinPath [
        ffmpeg-headless
        ripgrep
      ]
    }"
  ]
  ++ lib.optional stdenv.hostPlatform.isLinux "--suffix LD_LIBRARY_PATH : ${
    lib.makeLibraryPath [ pipewire ]
  }"
  ++ [
    "\${gappsWrapperArgs[@]}"
    "\${qtWrapperArgs[@]}"
  ];

  pythonRemoveDeps = lib.optional (!withJXLSupport) [ "pillow_jxl" ];
  pythonRelaxDeps = [
    "numpy"
    "pillow"
    "pillow-avif-plugin"
    "pillow-heif"
    "pillow-jxl-plugin"
    "py7zr"
    "pyside6"
    "rarfile"
    "structlog"
    "typing-extensions"
  ];
  pythonImportsCheck = [ "tagstudio" ];

  build-system = with python3Packages; [ hatchling ];
  dependencies =
    with python3Packages;
    [
      chardet
      ffmpeg-python
      humanfriendly
      mutagen
      numpy
      opencv-python
      pillow
      pillow-avif-plugin
      pillow-heif
      py7zr
      pydantic
      pydub
      pyside6
      rarfile
      rawpy
      send2trash
      sqlalchemy
      srctools
      structlog
      toml
      ujson
      wcmatch
    ]
    ++ lib.optional withJXLSupport pillow-jxl-plugin;

  # These tests require modifications to a library, which does not work
  # in a read-only environment.
  disabledTests = [
    "test_badge_visual_state"
    "test_browsing_state_update"
    "test_close_library" # TODO: Look into segfault.
    "test_flow_layout_happy_path"
    "test_get" # TODO: Look further into, might be possible to run.
    "test_json_migration"
    "test_library_migrations"
    "test_update_tags"
  ];
  disabledTestPaths = [
    "tests/qt/test_build_tag_panel.py"
    "tests/qt/test_field_containers.py"
    "tests/qt/test_file_path_options.py"
    "tests/qt/test_preview_panel.py"
    "tests/qt/test_tag_panel.py"
    "tests/qt/test_tag_search_panel.py"
    "tests/test_library.py"
  ];

  meta = {
    inherit (pyproject) description;
    homepage = "https://docs.tagstud.io/";
    license = lib.licenses.gpl3Only;
    maintainers = with lib.maintainers; [ xarvex ];
    mainProgram = "tagstudio";
    platforms = lib.platforms.unix;
  };
}
