# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

import logging
import os
import subprocess

from PySide6.QtWidgets import QLabel

ERROR = f'[ERROR]'
WARNING = f'[WARNING]'
INFO = f'[INFO]'

logging.basicConfig(format="%(message)s", level=logging.INFO)


class FileOpenerHelper():
	def __init__(self, filepath:str):
		self.filepath = filepath

	def set_filepath(self, filepath:str):
		self.filepath = filepath

	def open_file(self):
		if os.path.exists(self.filepath):
			os.startfile(self.filepath)
			logging.info(f'Opening file: {self.filepath}')
		else:
			logging.error(f'File not found: {self.filepath}')

	def open_explorer(self):
		if os.path.exists(self.filepath):
				logging.info(f'Opening file: {self.filepath}')
				if os.name == 'nt':  # Windows
					command = f'explorer /select,"{self.filepath}"'
					subprocess.run(command, shell=True)
				else:  # macOS and Linux
					command = f'nautilus --select "{self.filepath}"'  # Adjust for your Linux file manager if different
					if subprocess.run(command, shell=True).returncode == 0:
						file_loc = os.path.dirname(self.filepath)
						file_loc = os.path.normpath(file_loc)
						os.startfile(file_loc)
		else:
			logging.error(f'File not found: {self.filepath}')


class FileOpenerLabel(QLabel):
	def __init__(self, text, parent=None):
		super().__init__(text, parent)

	def setFilePath(self, filepath):
		self.filepath = filepath

	def mousePressEvent(self, event):
		super().mousePressEvent(event)
		opener = FileOpenerHelper(self.filepath)
		opener.open_explorer()
