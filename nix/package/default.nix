{
  buildPythonApplication,
  chardet,
  ffmpeg-headless,
  ffmpeg-python,
  hatchling,
  humanfriendly,
  lib,
  mutagen,
  numpy,
  opencv-python,
  pillow,
  pillow-heif,
  pillow-jxl-plugin,
  pipewire,
  pydub,
  pyside6,
  pytest-qt,
  pytest-xdist,
  pytestCheckHook,
  pythonRelaxDepsHook,
  qt6,
  rawpy,
  send2trash,
  sqlalchemy,
  stdenv,
  structlog,
  syrupy,
  ujson,
  vtf2img,

  withJXLSupport ? false,
}:

let
  pyproject = (lib.importTOML ../../pyproject.toml).project;
in
buildPythonApplication {
  pname = pyproject.name;
  inherit (pyproject) version;
  pyproject = true;

  src = ../../.;

  nativeBuildInputs = [
    pythonRelaxDepsHook
    qt6.wrapQtAppsHook
  ];
  buildInputs = [
    qt6.qtbase
    qt6.qtmultimedia
  ];

  nativeCheckInputs = [
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

  pythonRemoveDeps = true;
  pythonImportsCheck = [ "tagstudio" ];

  build-system = [ hatchling ];
  dependencies = [
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
  ] ++ lib.optional withJXLSupport pillow-jxl-plugin;

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
