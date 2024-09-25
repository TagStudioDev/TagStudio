# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio
import subprocess
import sys

"""Implementation of subprocess.Popen that does not spawn console windows or log output."""


def promptless_Popen(  # noqa: N802
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
    restore_signals=True,
    start_new_session=False,
    pass_fds=(),
    *,
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
    """Call subprocess.Popen without creating a console window."""
    creation_flags = 0
    if sys.platform == "win32":
        creation_flags = subprocess.CREATE_NO_WINDOW

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
        env=env,
        universal_newlines=universal_newlines,
        startupinfo=startupinfo,
        creationflags=creation_flags,
        restore_signals=restore_signals,
        start_new_session=start_new_session,
        pass_fds=pass_fds,
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
