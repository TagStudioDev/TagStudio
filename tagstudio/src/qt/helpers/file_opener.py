# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

import logging
import os
import subprocess
import sys
from os.path import isfile

from PySide6.QtWidgets import QLabel

ERROR = f'[ERROR]'
WARNING = f'[WARNING]'
INFO = f'[INFO]'

logging.basicConfig(format="%(message)s", level=logging.INFO)


def file_open(filepath: str, check_first: bool = True):
	if check_first and not os.path.isfile(filepath):
		logging.error(f'File not found: {filepath}')
		return False

	if os.name == 'nt':
		os.startfile(filepath)
	elif sys.platform == 'darwin':
		subprocess.Popen(['open', filepath])
	else:
		subprocess.call(["xdg-open", filepath])


class FileOpenerHelper:
	def __init__(self, filepath:str):
		self.filepath = filepath

	def set_filepath(self, filepath:str):
		self.filepath = filepath

	def open_file(self):
		logging.info(f'Opening file: {self.filepath}')
		file_open(self.filepath)

	def open_explorer(self):
		if not os.path.exists(self.filepath):
			logging.error(f'File not found: {self.filepath}')
			return

		logging.info(f'Opening file: {self.filepath}')
		if os.name == 'nt':  # Windows
			command = f'explorer /select,"{self.filepath}"'
			subprocess.run(command, shell=True)
		elif sys.platform == 'darwin':
			subprocess.Popen(['open', '-R', self.filepath])
		else:  # macOS and Linux
			command = f'nautilus --select "{self.filepath}"'  # Adjust for your Linux file manager if different
			if subprocess.run(command, shell=True).returncode == 0:
				file_loc = os.path.dirname(self.filepath)
				file_loc = os.path.normpath(file_loc)
				os.startfile(file_loc)


class FileOpenerLabel(QLabel):
	def __init__(self, text, parent=None):
		super().__init__(text, parent)

	def setFilePath(self, filepath):
		self.filepath = filepath

	def mousePressEvent(self, event):
		super().mousePressEvent(event)
		opener = FileOpenerHelper(self.filepath)
		opener.open_explorer()
