# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

import logging
import os
import subprocess
import sys

from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Qt

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
		if not os.path.exists(self.filepath):
			logging.error(f'File not found: {self.filepath}')
			return

		if sys.platform == 'win32':
			os.startfile(self.filepath)
		elif sys.platform == 'linux':
			subprocess.run(['xdg-open', self.filepath])
		elif sys.platform == 'darwin':
			subprocess.run(['open', self.filepath])

	def open_explorer(self):
		if os.path.exists(self.filepath):
			logging.info(f'Opening file: {self.filepath}')
			if os.name == 'nt':  # Windows
				command = f'explorer /select,"{self.filepath}"'
				subprocess.run(command, shell=True)
			elif sys.platform == 'linux':
				command = f'nautilus --select "{self.filepath}"'  # Adjust for your Linux file manager if different
				if subprocess.run(command, shell=True).returncode == 0:
					file_loc = os.path.dirname(self.filepath)
					file_loc = os.path.normpath(file_loc)
					os.startfile(file_loc)
			elif sys.platform == 'darwin':
				command = f'open -R "{self.filepath}"'
				result = subprocess.run(command, shell=True)
				if result.returncode == 0:
					logging.info('Opening file in Finder')
				else:
					logging.error(f'Failed to open file in Finder: {self.filepath}')
		else:
			logging.error(f'File not found: {self.filepath}')


class FileOpenerLabel(QLabel):
	def __init__(self, text, parent=None):
		super().__init__(text, parent)

	def setFilePath(self, filepath):
		self.filepath = filepath

	def mousePressEvent(self, event):
		"""Handle mouse press events.

		On a left click, open the file in the default file explorer. On a right click, show a context menu.
		
		Args:
			event (QMouseEvent): The mouse press event.
		"""
		super().mousePressEvent(event)

		if event.button() == Qt.LeftButton:
			opener = FileOpenerHelper(self.filepath)
			opener.open_explorer()
		elif event.button() == Qt.RightButton:
			# Show context menu
			pass
