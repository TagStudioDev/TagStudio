# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only

from tagstudio.core.utils.silent_subprocess import sanitized_subprocess_env


def test_sanitized_subprocess_env_restores_original_library_path():
    env = {
        "LD_LIBRARY_PATH": "/tmp/_MEI12345",
        "LD_LIBRARY_PATH_ORIG": "/usr/lib",
        "PATH": "/usr/bin",
    }

    clean_env = sanitized_subprocess_env(env)

    assert clean_env["LD_LIBRARY_PATH"] == "/usr/lib"
    assert env["LD_LIBRARY_PATH"] == "/tmp/_MEI12345"


def test_sanitized_subprocess_env_removes_bundled_qt_paths():
    env = {
        "LD_LIBRARY_PATH": "/tmp/_MEI12345",
        "QT_PLUGIN_PATH": "/tmp/_MEI12345/PySide6/Qt/plugins",
        "QT_QPA_PLATFORM_PLUGIN_PATH": "/tmp/_MEI12345/PySide6/Qt/plugins/platforms",
        "QML2_IMPORT_PATH": "/tmp/_MEI12345/PySide6/Qt/qml",
        "PATH": "/usr/bin",
    }

    clean_env = sanitized_subprocess_env(env)

    assert "LD_LIBRARY_PATH" not in clean_env
    assert "QT_PLUGIN_PATH" not in clean_env
    assert "QT_QPA_PLATFORM_PLUGIN_PATH" not in clean_env
    assert "QML2_IMPORT_PATH" not in clean_env
    assert clean_env["PATH"] == "/usr/bin"
