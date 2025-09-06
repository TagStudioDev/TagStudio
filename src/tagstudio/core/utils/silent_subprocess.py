# Copyright (C) 2025
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

# pyright: reportExplicitAny=false

import os
import subprocess
import sys
from collections.abc import Callable, Collection, Iterable
from typing import Any

"""Implementation of subprocess.Popen that does not spawn console windows or log output
and sanitizes pyinstaller environment variables."""


def silent_popen(
    args,
    bufsize: int = -1,
    executable=None,
    stdin=None,
    stdout=None,
    stderr=None,
    preexec_fn: Callable[[], Any] | None = None,
    close_fds: bool = True,
    shell: bool = False,
    cwd=None,
    env=None,
    universal_newlines: bool | None = None,
    startupinfo: Any | None = None,
    creationflags: int = 0,
    restore_signals: bool = True,
    start_new_session: bool = False,
    pass_fds: Collection[int] = (),
    *,
    text: bool | None = None,
    encoding: str | None = None,
    errors: str | None = None,
    user: str | int | None = None,
    group: str | int | None = None,
    extra_groups: Iterable[str | int] | None = None,
    umask: int = -1,
    pipesize: int = -1,
    process_group: int | None = None,
):
    """Call subprocess.Popen without creating a console window."""
    current_env = env

    if sys.platform == "win32":
        creationflags |= subprocess.CREATE_NO_WINDOW
        import ctypes

        ctypes.windll.kernel32.SetDllDirectoryW(None)
    elif (
        sys.platform == "linux"
        or sys.platform.startswith("freebsd")
        or sys.platform.startswith("openbsd")
    ):
        # pass clean environment to the subprocess
        current_env = os.environ
        original_env = current_env.get("LD_LIBRARY_PATH_ORIG")
        current_env["LD_LIBRARY_PATH"] = original_env if original_env else ""

    return subprocess.Popen(
        args=args,
        bufsize=bufsize,
        executable=executable,
        stdin=stdin,
        stdout=stdout,
        stderr=stderr,
        preexec_fn=preexec_fn,
        close_fds=close_fds,
        shell=shell,
        cwd=cwd,
        env=current_env,
        universal_newlines=universal_newlines,
        startupinfo=startupinfo,
        creationflags=creationflags,
        restore_signals=restore_signals,
        start_new_session=start_new_session,
        pass_fds=pass_fds,
        text=text,
        encoding=encoding,
        errors=errors,
        user=user,
        group=group,
        extra_groups=extra_groups,
        umask=umask,
        pipesize=pipesize,
        process_group=process_group,
    )


def silent_run(
    args,
    bufsize=-1,
    executable=None,
    stdin=None,
    stdout=None,
    stderr=None,
    preexec_fn=None,
    close_fds=True,
    shell=False,
    cwd=None,
    env=None,
    universal_newlines=None,
    startupinfo=None,
    creationflags=0,
    restore_signals=True,
    start_new_session=False,
    pass_fds=(),
    *,
    capture_output=False,
    group=None,
    extra_groups=None,
    user=None,
    umask=-1,
    encoding=None,
    errors=None,
    text=None,
    pipesize=-1,
    process_group=None,
):
    """Call subprocess.run without creating a console window."""
    if sys.platform == "win32":
        creationflags |= subprocess.CREATE_NO_WINDOW
        import ctypes

        ctypes.windll.kernel32.SetDllDirectoryW(None)
    elif (
        sys.platform == "linux"
        or sys.platform.startswith("freebsd")
        or sys.platform.startswith("openbsd")
    ):
        # pass clean environment to the subprocess
        env = os.environ
        original_env = env.get("LD_LIBRARY_PATH_ORIG")
        env["LD_LIBRARY_PATH"] = original_env if original_env else ""

    return subprocess.run(
        args=args,
        bufsize=bufsize,
        executable=executable,
        stdin=stdin,
        stdout=stdout,
        stderr=stderr,
        preexec_fn=preexec_fn,
        close_fds=close_fds,
        shell=shell,
        cwd=cwd,
        env=env,
        startupinfo=startupinfo,
        creationflags=creationflags,
        restore_signals=restore_signals,
        start_new_session=start_new_session,
        pass_fds=pass_fds,
        capture_output=capture_output,
        group=group,
        extra_groups=extra_groups,
        user=user,
        umask=umask,
        encoding=encoding,
        errors=errors,
        text=text,
        pipesize=pipesize,
        process_group=process_group,
    )
