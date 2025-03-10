{
  autoPatchelfHook,
  buildPythonPackage,
  exiv2,
  fetchFromGitHub,
  lib,
}:

buildPythonPackage rec {
  pname = "pyexiv2";
  version = "2.15.3";

  src = fetchFromGitHub {
    owner = "LeoHsiao1";
    repo = pname;
    rev = "v${version}";
    hash = "sha256-83bFMaoXncvhRJNcCgkkC7B29wR5pjuLO/EdkQdqxxo=";
  };

  nativeBuildInputs = [ autoPatchelfHook ];
  buildInputs = [ exiv2.lib ];

  pythonImportsCheck = [ "pyexiv2" ];

  meta = {
    description = "Read and write image metadata, including EXIF, IPTC, XMP, ICC Profile.";
    homepage = "https://github.com/LeoHsiao1/pyexiv2";
    license = lib.licenses.gpl3;
    maintainers = with lib.maintainers; [ xarvex ];
    platforms = with lib.platforms; darwin ++ linux ++ windows;
  };
}
