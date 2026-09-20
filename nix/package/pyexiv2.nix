# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: MIT

{
  buildPythonPackage,
  exiv2,
  fetchFromGitHub,
  lib,
  pybind11,
  python,
  setuptools,
}:

buildPythonPackage rec {
  pname = "pyexiv2";
  version = "2.16.0";
  pyproject = true;

  src = fetchFromGitHub {
    owner = "LeoHsiao1";
    repo = "pyexiv2";
    tag = "v${version}";
    hash = "sha256-FH5nbbh0vaErJzBl6L2HPh0SQXkQ558abTBml7nSLU8=";
  };

  buildInputs = [ exiv2.dev ];

  build-system = [ setuptools ];
  dependencies = [ pybind11 ];

  postBuild = ''
    lib_dir=$out/${python.sitePackages}/pyexiv2/lib

    mkdir -p "$lib_dir"
    cp -rT ${exiv2.lib}/lib "$lib_dir"
  '';

  pythonImportsCheck = [ "pyexiv2" ];

  meta = {
    description = "Read and write image metadata, including EXIF, IPTC, XMP, ICC Profile";
    homepage = "https://github.com/LeoHsiao1/pyexiv2";
    changelog = "https://github.com/LeoHsiao1/pyexiv2/releases/tag/v${version}";
    license = lib.licenses.gpl3;
    maintainers = with lib.maintainers; [ xarvex ];
    platforms = with lib.platforms; darwin ++ linux ++ windows;
  };
}
