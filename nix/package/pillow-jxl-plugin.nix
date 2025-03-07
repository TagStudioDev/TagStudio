{
  buildPythonPackage,
  cmake,
  fetchPypi,
  lib,
  numpy,
  packaging,
  pillow,
  pyexiv2,
  pytestCheckHook,
  rustPlatform,
}:

buildPythonPackage rec {
  pname = "pillow-jxl-plugin";
  version = "1.3.2";
  pyproject = true;

  src = fetchPypi {
    pname = builtins.replaceStrings [ "-" ] [ "_" ] pname;
    inherit version;
    hash = "sha256-efBoek8yUFR+ArhS55lm9F2XhkZ7/I3GsScQEe8U/2I=";
  };

  cargoDeps = rustPlatform.fetchCargoVendor {
    inherit src;
    hash = "sha256-vZHrwGfgo3fIIOY7p0vy4XIKiHoddPDdJggkBen+w/A=";
  };

  nativeBuildInputs = [
    cmake
    rustPlatform.cargoSetupHook
    rustPlatform.maturinBuildHook
  ];

  nativeCheckInputs = [
    numpy
    pyexiv2
    pytestCheckHook
  ];

  # INFO: Working directory takes precedence in the Python path. Remove
  # `pillow_jxl` to prevent it from being loaded during pytest, rather than the
  # built module, as it includes a `pillow_jxl.pillow_jxl` .so that is imported.
  # See: https://github.com/NixOS/nixpkgs/issues/255262
  # See: https://github.com/NixOS/nixpkgs/pull/255471
  preCheck = ''
    rm -r pillow_jxl
  '';

  dontUseCmakeConfigure = true;

  pythonImportsCheck = [ "pillow_jxl" ];

  dependencies = [
    packaging
    pillow
  ];

  meta = {
    description = "Pillow plugin for JPEG-XL, using Rust for bindings.";
    homepage = "https://github.com/Isotr0py/pillow-jpegxl-plugin";
    license = lib.licenses.gpl3;
    maintainers = with lib.maintainers; [ xarvex ];
    platforms = lib.platforms.unix;
  };
}
