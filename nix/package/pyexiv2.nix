{
  autoPatchelfHook,
  buildPythonPackage,
  exiv2,
  fetchFromGitHub,
  lib,
  setuptools,
}:

buildPythonPackage rec {
  pname = "pyexiv2";
  version = "2.15.3";
  pyproject = true;

  src = fetchFromGitHub {
    owner = "LeoHsiao1";
    repo = "pyexiv2";
    tag = "v${version}";
    hash = "sha256-83bFMaoXncvhRJNcCgkkC7B29wR5pjuLO/EdkQdqxxo=";
  };

  nativeBuildInputs = [ autoPatchelfHook ];
  buildInputs = [ exiv2.lib ];

  pythonImportsCheck = [ "pyexiv2" ];

  build-system = [ setuptools ];

  meta = {
    description = "Read and write image metadata, including EXIF, IPTC, XMP, ICC Profile";
    homepage = "https://github.com/LeoHsiao1/pyexiv2";
    changelog = "https://github.com/LeoHsiao1/pyexiv2/releases/tag/v${version}";
    license = lib.licenses.gpl3;
    maintainers = with lib.maintainers; [ xarvex ];
    platforms = with lib.platforms; darwin ++ linux ++ windows;
  };
}
