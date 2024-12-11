#!/usr/bin/env python
# License: GPL v3 Copyright: 2021, Kovid Goyal <kovid@kovidgoyal.net>
# Created for calibre: https://github.com/kovidgoyal/calibre

from importlib import import_module

import structlog

logger = structlog.get_logger(__name__)


def dynamic_load(name, name_map, already_imported, qt_modules, module_names=()):
    ans = already_imported.get(name, already_imported)
    if ans is not already_imported:
        return ans
    mod_name = name_map.get(name)
    if mod_name is not None:
        mod = qt_modules.get(mod_name)
        if mod is None:
            try:
                mod = qt_modules[mod_name] = import_module(mod_name)
            except ImportError as err:
                mod = qt_modules[mod_name] = False
                logger.error(f"Failed to import PySide6 module: {mod_name} with error: {err}")
        if mod is not False:
            if name in module_names:
                q = mod
            else:
                q = getattr(mod, name, qt_modules)
            if q is not qt_modules:
                already_imported[name] = q
                return q
    raise AttributeError(f"The object {name} is not a known Qt object")
