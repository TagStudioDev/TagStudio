# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: MIT

{
  buildPythonPackage,
  cmake,
  fetchPypi,
  lib,
  numpy,
  openexr,
  packaging,
  pillow,
  pyexiv2,
  pytestCheckHook,
  rustPlatform,
}:

buildPythonPackage rec {
  pname = "pillow-jxl-plugin";
  version = "1.3.8";
  pyproject = true;

  src = fetchPypi {
    pname = "pillow_jxl_plugin";
    inherit version;
    hash = "sha256-RDD9d1eJl0IHnFSKfSU31tY88PHTIxgAlbwPbwPZ1Po=";
  };

  cargoDeps = rustPlatform.fetchCargoVendor {
    inherit src;
    hash = "sha256-IiVTlKtKkfZnRXme7QFA5MS8PPiL8+riOYOEoNaHHXc=";
  };

  nativeBuildInputs = [
    cmake
    rustPlatform.cargoSetupHook
    rustPlatform.maturinBuildHook
  ];

  dependencies = [
    packaging
    pillow
  ];

  dontUseCmakeConfigure = true;

  nativeCheckInputs = [
    numpy
    openexr
    pyexiv2
    pytestCheckHook
  ];

  pythonImportsCheck = [ "pillow_jxl" ];

  # Working directory takes precedence in the Python path. Remove
  # `pillow_jxl` to prevent it from being loaded during pytest, rather than the
  # built module, as it includes a `pillow_jxl.pillow_jxl.so` that is imported.
  # See: https://github.com/NixOS/nixpkgs/issues/255262
  # See: https://github.com/NixOS/nixpkgs/pull/255471
  preCheck = ''
    rm -r pillow_jxl
  '';

  meta = {
    description = "Pillow plugin for JPEG-XL, using Rust for bindings";
    homepage = "https://github.com/Isotr0py/pillow-jpegxl-plugin";
    changelog = "https://github.com/Isotr0py/pillow-jpegxl-plugin/releases/tag/v${version}";
    license = lib.licenses.gpl3;
    maintainers = with lib.maintainers; [ xarvex ];
    platforms = lib.platforms.unix;
  };
}
