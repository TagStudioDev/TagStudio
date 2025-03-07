{
  buildPythonPackage,
  fetchPypi,
  lib,
  pillow,
}:

buildPythonPackage rec {
  pname = "vtf2img";
  version = "0.1.0";

  src = fetchPypi {
    inherit pname version;
    hash = "sha256-YmWs8673d72wH4nTOXP4AFGs2grIETln4s1MD5PfE0A=";
  };

  pythonImportsCheck = [ "vtf2img" ];

  dependencies = [ pillow ];

  meta = {
    description = "A Python library to convert Valve Texture Format (VTF) files to images.";
    homepage = "https://github.com/julienc91/vtf2img";
    license = lib.licenses.mit;
    maintainers = with lib.maintainers; [ xarvex ];
    mainProgram = "vtf2img";
    platforms = lib.platforms.unix;
  };
}
