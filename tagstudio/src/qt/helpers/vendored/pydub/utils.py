import json
import re
import subprocess

from pydub.utils import (
    _fd_or_path_or_tempfile,
    fsdecode,
    get_extra_info,
)
from src.qt.helpers.silent_popen import silent_Popen
from src.qt.helpers.vendored.ffmpeg import FFPROBE_CMD


def _mediainfo_json(filepath, read_ahead_limit=-1):
    """Return json dictionary with media info(codec, duration, size, bitrate...) from filepath."""
    prober = FFPROBE_CMD
    command_args = [
        "-v",
        "info",
        "-show_format",
        "-show_streams",
    ]
    try:
        command_args += [fsdecode(filepath)]
        stdin_parameter = None
        stdin_data = None
    except TypeError:
        if prober == "ffprobe":
            command_args += ["-read_ahead_limit", str(read_ahead_limit), "cache:pipe:0"]
        else:
            command_args += ["-"]
        stdin_parameter = subprocess.PIPE
        file, close_file = _fd_or_path_or_tempfile(filepath, "rb", tempfile=False)
        file.seek(0)
        stdin_data = file.read()
        if close_file:
            file.close()

    command = [prober, "-of", "json"] + command_args
    # PATCHED
    res = silent_Popen(
        command, stdin=stdin_parameter, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    output, stderr = res.communicate(input=stdin_data)
    output = output.decode("utf-8", "ignore")
    stderr = stderr.decode("utf-8", "ignore")

    try:
        info = json.loads(output)
    except json.decoder.JSONDecodeError:
        # If ffprobe didn't give any information, just return it
        # (for example, because the file doesn't exist)
        return None
    if not info:
        return info

    extra_info = get_extra_info(stderr)

    audio_streams = [x for x in info["streams"] if x["codec_type"] == "audio"]
    if len(audio_streams) == 0:
        return info

    # We just operate on the first audio stream in case there are more
    stream = audio_streams[0]

    def set_property(stream, prop, value):
        if prop not in stream or stream[prop] == 0:
            stream[prop] = value

    for token in extra_info[stream["index"]]:
        m = re.match(r"([su]([0-9]{1,2})p?) \(([0-9]{1,2}) bit\)$", token)
        m2 = re.match(r"([su]([0-9]{1,2})p?)( \(default\))?$", token)
        if m:
            set_property(stream, "sample_fmt", m.group(1))
            set_property(stream, "bits_per_sample", int(m.group(2)))
            set_property(stream, "bits_per_raw_sample", int(m.group(3)))
        elif m2:
            set_property(stream, "sample_fmt", m2.group(1))
            set_property(stream, "bits_per_sample", int(m2.group(2)))
            set_property(stream, "bits_per_raw_sample", int(m2.group(2)))
        elif re.match(r"(flt)p?( \(default\))?$", token):
            set_property(stream, "sample_fmt", token)
            set_property(stream, "bits_per_sample", 32)
            set_property(stream, "bits_per_raw_sample", 32)
        elif re.match(r"(dbl)p?( \(default\))?$", token):
            set_property(stream, "sample_fmt", token)
            set_property(stream, "bits_per_sample", 64)
            set_property(stream, "bits_per_raw_sample", 64)
    return info
