# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


import logging
import os
import sys
import traceback
import shutil
import subprocess


def open_file(path: str):
	try:
		if sys.platform == "win32":
			# Windows needs special attention to handle spaces in the file
			# first parameter is for title, NOT filepath
			subprocess.Popen(["start", "", os.path.normpath(path)], shell=True, close_fds=True, creationflags=subprocess.DETACHED_PROCESS)
		else:
			if sys.platform == "darwin":
				command_name = "open"
			else:
				command_name = "xdg-open"
			command = shutil.which(command_name)
			if command is not None:
				subprocess.Popen([command, path], close_fds=True)
			else:
				logging.info(f"Could not find {command_name} on system PATH")
	except:
		traceback.print_exc()