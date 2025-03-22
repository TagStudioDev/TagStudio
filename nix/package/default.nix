{
  ffmpeg-headless,
  lib,
  pipewire,
  python3Packages,
  qt6,
  stdenv,
  wrapGAppsHook,

  pillow-jxl-plugin,
  vtf2img,

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

    # INFO: Should be unnecessary once PR is pulled.
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

  makeWrapperArgs =
    [ "--prefix PATH : ${lib.makeBinPath [ ffmpeg-headless ]}" ]
    ++ lib.optional stdenv.hostPlatform.isLinux "--prefix LD_LIBRARY_PATH : ${
      lib.makeLibraryPath [ pipewire ]
    }";

  pythonRemoveDeps = lib.optional (!withJXLSupport) [ "pillow_jxl" ];
  pythonRelaxDeps = [
    "numpy"
    "pillow"
    "pillow-heif"
    "pillow-jxl-plugin"
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
      pillow-heif
      pydub
      pyside6
      rawpy
      send2trash
      sqlalchemy
      structlog
      ujson
      vtf2img
    ]
    ++ lib.optional withJXLSupport pillow-jxl-plugin;

  # INFO: These tests require modifications to a library, which does not work
  # in a read-only environment.
  disabledTests = [
    "test_build_tag_panel_add_alias_callback"
    "test_build_tag_panel_add_aliases"
    "test_build_tag_panel_add_sub_tag_callback"
    "test_build_tag_panel_build_tag"
    "test_build_tag_panel_remove_alias_callback"
    "test_build_tag_panel_remove_subtag_callback"
    "test_build_tag_panel_set_aliases"
    "test_build_tag_panel_set_parent_tags"
    "test_build_tag_panel_set_tag"
    "test_json_migration"
    "test_library_migrations"
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
