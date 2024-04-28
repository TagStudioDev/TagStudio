# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


import logging
import os
import sys
import traceback
import shutil
import subprocess


def open_file(path: str, file_manager: bool = False):
	try:
		if sys.platform == "win32":
			normpath = os.path.normpath(path)
			if file_manager:
				command_name = "explorer"
				command_args = [f"/select,{normpath}"]
			else:
				command_name = "start"
				# first parameter is for title, NOT filepath
				command_args = ["", normpath]
			subprocess.Popen([command_name] + command_args, shell=True, close_fds=True, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_BREAKAWAY_FROM_JOB)
		else:
			if sys.platform == "darwin":
				command_name = "open"
				command_args = [path]
				if file_manager:
					# will reveal in Finder
					command_args.append("-R")
			else:
				if file_manager:
					command_name = "dbus-send"
					# might not be guaranteed to launch default?
					command_args = ["--session", "--dest=org.freedesktop.FileManager1", "--type=method_call",
									"/org/freedesktop/FileManager1", "org.freedesktop.FileManager1.ShowItems",
									f"array:string:file://{path}", "string:"]
				else:
					command_name = "xdg-open"
					command_args = [path]
			command = shutil.which(command_name)
			if command is not None:
				subprocess.Popen([command] + command_args, close_fds=True)
			else:
				logging.info(f"Could not find {command_name} on system PATH")
	except:
		traceback.print_exc()