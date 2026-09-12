# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: MIT

{
  lib,
  numpy,
  openexr,
  pybind11,
  pytest,
  python,
  pythonImportsCheckHook,
  toPythonModule,
}:

toPythonModule (
  openexr.overrideAttrs (o: {
    buildInputs = o.buildInputs or [ ] ++ [ pybind11 ];

    cmakeFlags = o.cmakeFlags or [ ] ++ [ (lib.cmakeBool "OPENEXR_BUILD_PYTHON" true) ];

    # `python.sitePackages` replacement can be removed once Python install path is inherited from sysconfig.
    # Currently on main, but not part of a release.
    # See: https://github.com/AcademySoftwareFoundation/openexr/commit/30345db72944b38926f13b5114b9a01b4b553890
    postPatch = o.postPatch or "" + /* bash */ ''
      substituteInPlace src/wrappers/python/CMakeLists.txt \
          --replace-warn python/OpenEXR ${python.sitePackages} \
          --replace-fail 'PYTHONPATH=''${CMAKE_CURRENT_BINARY_DIR}' 'PYTHONPATH=''${CMAKE_CURRENT_BINARY_DIR}:'"$PYTHONPATH"
    '';

    nativeCheckInputs = o.nativeCheckInputs or [ ] ++ [
      numpy
      pythonImportsCheckHook
    ];
    checkInputs = o.checkInputs or [ ] ++ [ pytest ];

    pythonImportsCheck = o.pythonImportsCheck or [ ] ++ [ "OpenEXR" ];
  })
)
