# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

# SIGTERM handling based on the implementation by Virgil Dupras for dupeGuru:
# https://github.com/arsenetar/dupeguru/blob/master/run.py#L71

"""A Qt driver for TagStudio."""

import ctypes
import logging
import math
import os
import sys
import time
import traceback
import shutil
import subprocess
from types import FunctionType
from datetime import datetime as dt
from pathlib import Path
from queue import Empty, Queue
from time import sleep
from typing import Optional

import cv2
from PIL import Image, ImageChops, UnidentifiedImageError, ImageQt, ImageDraw, ImageFont, ImageEnhance
from PySide6 import QtCore
from PySide6.QtCore import QObject, QThread, Signal, QRunnable, Qt, QThreadPool, QSize, QEvent, QTimer, QSettings
from PySide6.QtGui import (QGuiApplication, QPixmap, QEnterEvent, QMouseEvent, QResizeEvent, QPainter, QColor, QPen,
						   QAction, QStandardItemModel, QStandardItem, QPainterPath, QFontDatabase, QIcon)
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QPlainTextEdit,
							   QLineEdit, QScrollArea, QFrame, QTextEdit, QComboBox, QProgressDialog, QFileDialog,
							   QListView, QSplitter, QSizePolicy, QMessageBox, QBoxLayout, QCheckBox, QSplashScreen,
							   QMenu)
from humanfriendly import format_timespan, format_size

from src.core.library import Collation, Entry, ItemType, Library, Tag
from src.core.palette import ColorType, get_tag_color
from src.core.ts_core import (TagStudioCore, TAG_COLORS, DATE_FIELDS, TEXT_FIELDS, BOX_FIELDS, ALL_FILE_TYPES,
										SHORTCUT_TYPES, PROGRAM_TYPES, ARCHIVE_TYPES, PRESENTATION_TYPES,
										SPREADSHEET_TYPES, TEXT_TYPES, AUDIO_TYPES, VIDEO_TYPES, IMAGE_TYPES,
										LIBRARY_FILENAME, COLLAGE_FOLDER_NAME, BACKUP_FOLDER_NAME, TS_FOLDER_NAME,
										VERSION_BRANCH, VERSION)
from src.core.utils.web import strip_web_protocol
from src.qt.flowlayout import FlowLayout, FlowWidget
from src.qt.main_window import Ui_MainWindow
import src.qt.resources_rc

# SIGQUIT is not defined on Windows
if sys.platform == "win32":
	from signal import signal, SIGINT, SIGTERM
	SIGQUIT = SIGTERM
else:
	from signal import signal, SIGINT, SIGTERM, SIGQUIT

ERROR = f'[ERROR]'
WARNING = f'[WARNING]'
INFO = f'[INFO]'

logging.basicConfig(format="%(message)s", level=logging.INFO)

# Keep settings in ini format in the current working directory.
QSettings.setPath(QSettings.IniFormat, QSettings.UserScope, os.getcwd())


def open_file(path: str):
	try:
		if sys.platform == "win32":
			subprocess.Popen(["start", path], shell=True, close_fds=True, creationflags=subprocess.DETACHED_PROCESS)
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


class NavigationState():
	"""Represents a state of the Library grid view."""

	def __init__(self, contents, scrollbar_pos: int, page_index:int, page_count:int, search_text: str = None, thumb_size=None, spacing=None) -> None:
		self.contents = contents
		self.scrollbar_pos = scrollbar_pos
		self.page_index = page_index
		self.page_count = page_count
		self.search_text = search_text
		self.thumb_size = thumb_size
		self.spacing = spacing


class Consumer(QThread):
	def __init__(self, queue) -> None:
		self.queue = queue
		QThread.__init__(self)

	def run(self):
		while True:
			try:
				job = self.queue.get()
				# print('Running job...')
				# logging.info(*job[1])
				job[0](*job[1])
			except (Empty, RuntimeError):
				pass

	
	def set_page_count(self, count:int):
		self.page_count = count
	
	def jump_to_page(self, index:int):
		pass

	def nav_back(self):
		pass

	def nav_forward(self):
		pass


class FieldContainer(QWidget):
	clipboard_icon_128: Image.Image = Image.open(os.path.normpath(
		f'{Path(__file__).parent.parent.parent}/resources/qt/images/clipboard_icon_128.png')).resize((math.floor(24*1.25),math.floor(24*1.25)))
	clipboard_icon_128.load()

	edit_icon_128: Image.Image = Image.open(os.path.normpath(
		f'{Path(__file__).parent.parent.parent}/resources/qt/images/edit_icon_128.png')).resize((math.floor(24*1.25),math.floor(24*1.25)))
	edit_icon_128.load()

	trash_icon_128: Image.Image = Image.open(os.path.normpath(
		f'{Path(__file__).parent.parent.parent}/resources/qt/images/trash_icon_128.png')).resize((math.floor(24*1.25),math.floor(24*1.25)))
	trash_icon_128.load()
	
	def __init__(self, title:str='Field', inline:bool=True) -> None:
		super().__init__()
		# self.mode:str = mode
		self.setObjectName('fieldContainer')
		# self.item = item
		self.title:str = title
		self.inline:bool = inline
		# self.editable:bool = editable
		self.copy_callback:FunctionType = None
		self.edit_callback:FunctionType = None
		self.remove_callback:FunctionType = None
		button_size = 24
		# self.setStyleSheet('border-style:solid;border-color:#1e1a33;border-radius:8px;border-width:2px;')


		self.root_layout = QVBoxLayout(self)
		self.root_layout.setObjectName('baseLayout')
		self.root_layout.setContentsMargins(0, 0, 0, 0)
		# self.setStyleSheet('background-color:red;')

		self.inner_layout = QVBoxLayout()
		self.inner_layout.setObjectName('innerLayout')
		self.inner_layout.setContentsMargins(0,0,0,0)
		self.inner_layout.setSpacing(0)
		self.inner_container = QWidget()
		self.inner_container.setObjectName('innerContainer')
		self.inner_container.setLayout(self.inner_layout)
		self.root_layout.addWidget(self.inner_container)

		self.title_container = QWidget()
		# self.title_container.setStyleSheet('background:black;')
		self.title_layout = QHBoxLayout(self.title_container)
		self.title_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
		self.title_layout.setObjectName('fieldLayout')
		self.title_layout.setContentsMargins(0,0,0,0)
		self.title_layout.setSpacing(0)
		self.inner_layout.addWidget(self.title_container)

		self.title_widget = QLabel()
		self.title_widget.setMinimumHeight(button_size)
		self.title_widget.setObjectName('fieldTitle')
		self.title_widget.setWordWrap(True)
		self.title_widget.setStyleSheet('font-weight: bold; font-size: 14px;')
		# self.title_widget.setStyleSheet('background-color:orange;')
		self.title_widget.setText(title)
		# self.inner_layout.addWidget(self.title_widget)
		self.title_layout.addWidget(self.title_widget)

		self.title_layout.addStretch(2)


		self.copy_button = QPushButton()
		self.copy_button.setMinimumSize(button_size,button_size)
		self.copy_button.setMaximumSize(button_size,button_size)
		self.copy_button.setFlat(True)
		self.copy_button.setIcon(QPixmap.fromImage(ImageQt.ImageQt(self.clipboard_icon_128)))
		self.copy_button.setCursor(Qt.CursorShape.PointingHandCursor)
		self.title_layout.addWidget(self.copy_button)
		self.copy_button.setHidden(True)

		self.edit_button = QPushButton()
		self.edit_button.setMinimumSize(button_size,button_size)
		self.edit_button.setMaximumSize(button_size,button_size)
		self.edit_button.setFlat(True)
		self.edit_button.setIcon(QPixmap.fromImage(ImageQt.ImageQt(self.edit_icon_128)))
		self.edit_button.setCursor(Qt.CursorShape.PointingHandCursor)
		self.title_layout.addWidget(self.edit_button)
		self.edit_button.setHidden(True)

		self.remove_button = QPushButton()
		self.remove_button.setMinimumSize(button_size,button_size)
		self.remove_button.setMaximumSize(button_size,button_size)
		self.remove_button.setFlat(True)
		self.remove_button.setIcon(QPixmap.fromImage(ImageQt.ImageQt(self.trash_icon_128)))
		self.remove_button.setCursor(Qt.CursorShape.PointingHandCursor)
		self.title_layout.addWidget(self.remove_button)
		self.remove_button.setHidden(True)

		self.field_container = QWidget()
		self.field_container.setObjectName('fieldContainer')
		self.field_layout = QHBoxLayout()
		self.field_layout.setObjectName('fieldLayout')
		self.field_layout.setContentsMargins(0,0,0,0)
		self.field_container.setLayout(self.field_layout)
		# self.field_container.setStyleSheet('background-color:#666600;')
		self.inner_layout.addWidget(self.field_container)

		# self.set_inner_widget(mode)

	def set_copy_callback(self, callback:Optional[FunctionType]):
		try:
			self.copy_button.clicked.disconnect()
		except RuntimeError:
			pass

		self.copy_callback = callback
		self.copy_button.clicked.connect(callback)

	def set_edit_callback(self, callback:Optional[FunctionType]):
		try:
			self.edit_button.clicked.disconnect()
		except RuntimeError:
			pass

		self.edit_callback = callback
		self.edit_button.clicked.connect(callback)

	def set_remove_callback(self, callback:Optional[FunctionType]):
		try:
			self.remove_button.clicked.disconnect()
		except RuntimeError:
			pass

		self.remove_callback = callback
		self.remove_button.clicked.connect(callback)
		
	def set_inner_widget(self, widget:'FieldWidget'):
		# widget.setStyleSheet('background-color:green;')
		# self.inner_container.dumpObjectTree()
		# logging.info('')
		if self.field_layout.itemAt(0):
			# logging.info(f'Removing {self.field_layout.itemAt(0)}')
			# self.field_layout.removeItem(self.field_layout.itemAt(0))
			self.field_layout.itemAt(0).widget().deleteLater()
		self.field_layout.addWidget(widget)
	
	def get_inner_widget(self) -> Optional['FieldWidget']:
		if self.field_layout.itemAt(0):
			return self.field_layout.itemAt(0).widget()
		return None

	def set_title(self, title:str):
		self.title = title
		self.title_widget.setText(title)
	
	def set_inline(self, inline:bool):
		self.inline = inline
	
	# def set_editable(self, editable:bool):
	# 	self.editable = editable
	
	def enterEvent(self, event: QEnterEvent) -> None:
		# if self.field_layout.itemAt(1):
		# 	self.field_layout.itemAt(1).
		# NOTE: You could pass the hover event to the FieldWidget if needed.
		if self.copy_callback:
			self.copy_button.setHidden(False)
		if self.edit_callback:
			self.edit_button.setHidden(False)
		if self.remove_callback:
			self.remove_button.setHidden(False)
		return super().enterEvent(event)

	def leaveEvent(self, event: QEvent) -> None:
		if self.copy_callback:
			self.copy_button.setHidden(True)
		if self.edit_callback:
			self.edit_button.setHidden(True)
		if self.remove_callback:
			self.remove_button.setHidden(True)
		return super().leaveEvent(event)


class FieldWidget(QWidget):
	field = dict
	def __init__(self, title) -> None:
		super().__init__()
		# self.item = item
		self.title = title



class TagBoxWidget(FieldWidget):
	updated = Signal()
	
	def __init__(self, item, title, field_index, library:Library, tags:list[int], driver:'QtDriver') -> None:
		super().__init__(title)
		# QObject.__init__(self)
		self.item = item
		self.lib = library
		self.driver = driver # Used for creating tag click callbacks that search entries for that tag. 
		self.field_index = field_index
		self.tags:list[int] = tags
		self.setObjectName('tagBox')
		self.base_layout = FlowLayout()
		self.base_layout.setGridEfficiency(False)
		self.base_layout.setContentsMargins(0, 0, 0, 0)
		self.setLayout(self.base_layout)

		self.add_button = QPushButton()
		self.add_button.setCursor(Qt.CursorShape.PointingHandCursor)
		self.add_button.setMinimumSize(23, 23)
		self.add_button.setMaximumSize(23, 23)
		self.add_button.setText('+')
		self.add_button.setStyleSheet(
									f'QPushButton{{'
									# f'background: #1E1A33;'
									# f'color: #CDA7F7;'
									f'font-weight: bold;'
									# f"border-color: #2B2547;"
									f'border-radius: 6px;'
									f'border-style:solid;'
									f'border-width:{math.ceil(1*self.devicePixelRatio())}px;'
									# f'padding-top: 1.5px;'
									# f'padding-right: 4px;'
									f'padding-bottom: 5px;'
									# f'padding-left: 4px;'
									f'font-size: 20px;'
									f'}}'
									f'QPushButton::hover'
									f'{{'
									# f'background: #2B2547;'
									f'}}')
		tsp = TagSearchPanel(self.lib)
		tsp.tag_chosen.connect(lambda x: self.add_tag_callback(x))
		self.add_modal = PanelModal(tsp, title, 'Add Tags')
		self.add_button.clicked.connect(self.add_modal.show)

		self.set_tags(tags)
		# self.add_button.setHidden(True)

	def set_item(self, item):
		self.item = item

	def set_tags(self, tags:list[int]):
		logging.info(f'[TAG BOX WIDGET] SET TAGS: T:{tags} for E:{self.item.id}')
		is_recycled = False
		if self.base_layout.itemAt(0):
			# logging.info(type(self.base_layout.itemAt(0).widget()))
			while self.base_layout.itemAt(0) and self.base_layout.itemAt(1):
				# logging.info(f"I'm deleting { self.base_layout.itemAt(0).widget()}")
				self.base_layout.takeAt(0).widget().deleteLater()
			is_recycled = True
		for tag in tags:
			# TODO: Remove space from the special search here (tag_id:x) once that system is finalized.
			# tw = TagWidget(self.lib, self.lib.get_tag(tag), True, True, 
			# 							on_remove_callback=lambda checked=False, t=tag: (self.lib.get_entry(self.item.id).remove_tag(self.lib, t, self.field_index), self.updated.emit()), 
			# 							on_click_callback=lambda checked=False, q=f'tag_id: {tag}': (self.driver.main_window.searchField.setText(q), self.driver.filter_items(q)),
			# 							on_edit_callback=lambda checked=False, t=tag: (self.edit_tag(t))
			# 							)
			tw = TagWidget(self.lib, self.lib.get_tag(tag), True, True)
			tw.on_click.connect(lambda checked=False, q=f'tag_id: {tag}': (self.driver.main_window.searchField.setText(q), self.driver.filter_items(q)))
			tw.on_remove.connect(lambda checked=False, t=tag: (self.remove_tag(t)))
			tw.on_edit.connect(lambda checked=False, t=tag: (self.edit_tag(t)))
			self.base_layout.addWidget(tw)
		self.tags = tags

		# Move or add the '+' button.
		if is_recycled:
			self.base_layout.addWidget(self.base_layout.takeAt(0).widget())
		else:
			self.base_layout.addWidget(self.add_button)
	
		# Handles an edge case where there are no more tags and the '+' button
		# doesn't move all the way to the left.
		if self.base_layout.itemAt(0) and not self.base_layout.itemAt(1):
			self.base_layout.update()


	def edit_tag(self, tag_id:int):
		btp = BuildTagPanel(self.lib, tag_id)
		# btp.on_edit.connect(lambda x: self.edit_tag_callback(x))
		self.edit_modal = PanelModal(btp, 
							   self.lib.get_tag(tag_id).display_name(self.lib), 
							   'Edit Tag',
							   done_callback=(self.driver.preview_panel.update_widgets),
							   has_save=True)
		# self.edit_modal.widget.update_display_name.connect(lambda t: self.edit_modal.title_widget.setText(t))
		panel: BuildTagPanel = self.edit_modal.widget
		self.edit_modal.saved.connect(lambda: self.lib.update_tag(btp.build_tag()))
		# panel.tag_updated.connect(lambda tag: self.lib.update_tag(tag))
		self.edit_modal.show()


	def add_tag_callback(self, tag_id):
		# self.base_layout.addWidget(TagWidget(self.lib, self.lib.get_tag(tag), True))
		# self.tags.append(tag)
		logging.info(f'[TAG BOX WIDGET] ADD TAG CALLBACK: T:{tag_id} to E:{self.item.id}')
		logging.info(f'[TAG BOX WIDGET] SELECTED T:{self.driver.selected}')
		id = list(self.field.keys())[0]
		for x in self.driver.selected:
				self.driver.lib.get_entry(x[1]).add_tag(self.driver.lib, tag_id, field_id=id, field_index=-1)
				self.updated.emit()
		if tag_id == 0 or tag_id == 1:
			self.driver.update_badges()

		# if type((x[0]) == ThumbButton):
		# 	# TODO: Remove space from the special search here (tag_id:x) once that system is finalized.
			# logging.info(f'I want to add tag ID {tag_id} to entry {self.item.filename}')
			# self.updated.emit()
			# if tag_id not in self.tags:
			# 	self.tags.append(tag_id)
			# self.set_tags(self.tags)
		# elif type((x[0]) == ThumbButton):

	
	def edit_tag_callback(self, tag:Tag):
		self.lib.update_tag(tag)
		
	def remove_tag(self, tag_id):
		logging.info(f'[TAG BOX WIDGET] SELECTED T:{self.driver.selected}')
		id = list(self.field.keys())[0]
		for x in self.driver.selected:
			index = self.driver.lib.get_field_index_in_entry(self.driver.lib.get_entry(x[1]),id)
			self.driver.lib.get_entry(x[1]).remove_tag(self.driver.lib, tag_id,field_index=index[0])
			self.updated.emit()
		if tag_id == 0 or tag_id == 1:
			self.driver.update_badges()

	# def show_add_button(self, value:bool):
	# 	self.add_button.setHidden(not value)


class TextWidget(FieldWidget):

	def __init__(self, title, text:str) -> None:
		super().__init__(title)
		# self.item = item
		self.setObjectName('textBox')
		# self.setStyleSheet('background-color:purple;')
		self.base_layout = QHBoxLayout()
		self.base_layout.setContentsMargins(0, 0, 0, 0)
		self.setLayout(self.base_layout)
		self.text_label = QLabel()
		# self.text_label.textFormat(Qt.TextFormat.RichText)
		self.text_label.setStyleSheet('font-size: 12px')
		self.text_label.setWordWrap(True)
		self.text_label.setTextInteractionFlags(
			Qt.TextInteractionFlag.TextSelectableByMouse)
		self.base_layout.addWidget(self.text_label)
		self.set_text(text)

	def set_text(self, text:str):
		self.text_label.setText(text)


class TagWidget(QWidget):
	edit_icon_128: Image.Image = Image.open(os.path.normpath(
		f'{Path(__file__).parent.parent.parent}/resources/qt/images/edit_icon_128.png')).resize((math.floor(14*1.25),math.floor(14*1.25)))
	edit_icon_128.load()
	on_remove = Signal()
	on_click = Signal()
	on_edit = Signal()

	def __init__(self, library:Library, tag:Tag, has_edit:bool, has_remove:bool, on_remove_callback:FunctionType=None, on_click_callback:FunctionType=None, on_edit_callback:FunctionType=None) -> None:
		super().__init__()
		self.lib = library
		self.tag = tag
		self.has_edit:bool = has_edit
		self.has_remove:bool = has_remove
		# self.bg_label = QLabel()
		# self.setStyleSheet('background-color:blue;')
		
		# if on_click_callback:
		self.setCursor(Qt.CursorShape.PointingHandCursor)
		self.base_layout = QVBoxLayout(self)
		self.base_layout.setObjectName('baseLayout')
		self.base_layout.setContentsMargins(0, 0, 0, 0)

		self.bg_button = QPushButton(self)
		self.bg_button.setFlat(True)
		self.bg_button.setText(tag.display_name(self.lib).replace('&', '&&'))
		if has_edit:
			edit_action = QAction('Edit', self)
			edit_action.triggered.connect(on_edit_callback)
			edit_action.triggered.connect(self.on_edit.emit)
			self.bg_button.addAction(edit_action)
		# if on_click_callback:
		self.bg_button.setContextMenuPolicy(Qt.ContextMenuPolicy.ActionsContextMenu)
		# if has_remove:
		# 	remove_action = QAction('Remove', self)
		# 	# remove_action.triggered.connect(on_remove_callback)
		# 	remove_action.triggered.connect(self.on_remove.emit())
		# 	self.bg_button.addAction(remove_action)
		search_for_tag_action = QAction('Search for Tag', self)
		# search_for_tag_action.triggered.connect(on_click_callback)
		search_for_tag_action.triggered.connect(self.on_click.emit)
		self.bg_button.addAction(search_for_tag_action)
		add_to_search_action = QAction('Add to Search', self)
		self.bg_button.addAction(add_to_search_action)

		self.inner_layout = QHBoxLayout()
		self.inner_layout.setObjectName('innerLayout')
		self.inner_layout.setContentsMargins(2, 2, 2, 2)
		# self.inner_layout.setAlignment(Qt.AlignmentFlag.AlignRight)
		
		# self.inner_container = QWidget()
		# self.inner_container.setLayout(self.inner_layout)
		# self.base_layout.addWidget(self.inner_container)
		self.bg_button.setLayout(self.inner_layout)
		self.bg_button.setMinimumSize(math.ceil(22*1.5), 22)

		# self.bg_button.setStyleSheet(
		# 	f'QPushButton {{'
		# 	f'border: 2px solid #8f8f91;'
		# 	f'border-radius: 6px;'
		# 	f'background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,stop: 0 {ColorType.PRIMARY}, stop: 1 {ColorType.BORDER});'
		# 	f'min-width: 80px;}}')

		self.bg_button.setStyleSheet(
									# f'background: {get_tag_color(ColorType.PRIMARY, tag.color)};'
									f'QPushButton{{'
										f'background: {get_tag_color(ColorType.PRIMARY, tag.color)};'
										# f'background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {get_tag_color(ColorType.PRIMARY, tag.color)}, stop:1.0 {get_tag_color(ColorType.BORDER, tag.color)});'
										# f"border-color:{get_tag_color(ColorType.PRIMARY, tag.color)};"
										f"color: {get_tag_color(ColorType.TEXT, tag.color)};"
										f'font-weight: 600;'
										f"border-color:{get_tag_color(ColorType.BORDER, tag.color)};"
										f'border-radius: 6px;'
										f'border-style:solid;'
										f'border-width: {math.ceil(1*self.devicePixelRatio())}px;'
										# f'border-top:2px solid {get_tag_color(ColorType.LIGHT_ACCENT, tag.color)};'
										# f'border-bottom:2px solid {get_tag_color(ColorType.BORDER, tag.color)};'
										# f'border-left:2px solid {get_tag_color(ColorType.BORDER, tag.color)};'
										# f'border-right:2px solid {get_tag_color(ColorType.BORDER, tag.color)};'
										# f'padding-top: 0.5px;'
										f'padding-right: 4px;'
										f'padding-bottom: 1px;'
										f'padding-left: 4px;'
										f'font-size: 13px'
										f'}}'
										f'QPushButton::hover{{'
										# f'background: {get_tag_color(ColorType.LIGHT_ACCENT, tag.color)};'
										# f'background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {get_tag_color(ColorType.PRIMARY, tag.color)}, stop:1.0 {get_tag_color(ColorType.BORDER, tag.color)});'
										# f"border-color:{get_tag_color(ColorType.PRIMARY, tag.color)};"
										# f"color: {get_tag_color(ColorType.TEXT, tag.color)};"
										f"border-color:{get_tag_color(ColorType.LIGHT_ACCENT, tag.color)};"
										f'}}')

		# self.renderer = ThumbRenderer()
		# self.renderer.updated.connect(lambda ts, i, s, ext: (self.update_thumb(ts, image=i),
		# 													 self.update_size(
		# 														 ts, size=s),
		# 													 self.set_extension(ext)))
		
		# self.bg_button.setLayout(self.base_layout)
		
		self.base_layout.addWidget(self.bg_button)
		# self.setMinimumSize(self.bg_button.size())

		# logging.info(tag.color)
		if has_remove:
			self.remove_button = QPushButton(self)
			self.remove_button.setFlat(True)
			self.remove_button.setText('–')
			self.remove_button.setHidden(True)
			self.remove_button.setStyleSheet(f'color: {get_tag_color(ColorType.PRIMARY, tag.color)};'
										f"background: {get_tag_color(ColorType.TEXT, tag.color)};"
										# f"color: {'black' if color not in ['black', 'gray', 'dark gray', 'cool gray', 'warm gray', 'blue', 'purple', 'violet'] else 'white'};"
										# f"border-color: {get_tag_color(ColorType.BORDER, tag.color)};"
										f'font-weight: 800;'
										# f"border-color:{'black' if color not in [
										# 'black', 'gray', 'dark gray', 
										# 'cool gray', 'warm gray', 'blue', 
										# 'purple', 'violet'] else 'white'};"
										f'border-radius: 4px;'
										# f'border-style:solid;'
										f'border-width:0;'
										# f'padding-top: 1.5px;'
										# f'padding-right: 4px;'
										f'padding-bottom: 4px;'
										# f'padding-left: 4px;'
										f'font-size: 14px')
			self.remove_button.setMinimumSize(19,19)
			self.remove_button.setMaximumSize(19,19)
			# self.remove_button.clicked.connect(on_remove_callback)
			self.remove_button.clicked.connect(self.on_remove.emit)

		# NOTE: No more edit button! Just make it a right-click option.
		# self.edit_button = QPushButton(self)
		# self.edit_button.setFlat(True)
		# self.edit_button.setText('Edit')
		# self.edit_button.setIcon(QPixmap.fromImage(ImageQt.ImageQt(self.edit_icon_128)))
		# self.edit_button.setIconSize(QSize(14,14))
		# self.edit_button.setHidden(True)
		# self.edit_button.setStyleSheet(f'color: {color};'
		# 						    f"background: {'black' if color not in ['black', 'gray', 'dark gray', 'cool gray', 'warm gray', 'blue', 'purple', 'violet'] else 'white'};"
		# 							# f"color: {'black' if color not in ['black', 'gray', 'dark gray', 'cool gray', 'warm gray', 'blue', 'purple', 'violet'] else 'white'};"
		# 							f"border-color: {'black' if color not in ['black', 'gray', 'dark gray', 'cool gray', 'warm gray', 'blue', 'purple', 'violet'] else 'white'};"
		# 							f'font-weight: 600;'
		# 							# f"border-color:{'black' if color not in [
		# 							# 'black', 'gray', 'dark gray', 
		# 							# 'cool gray', 'warm gray', 'blue', 
		# 							# 'purple', 'violet'] else 'white'};"
		# 							# f'QPushButton{{border-image: url(:/images/edit_icon_128.png);}}'
		# 							# f'QPushButton{{border-image: url(:/images/edit_icon_128.png);}}'
		# 							f'border-radius: 4px;'
		# 							# f'border-style:solid;'
		# 							# f'border-width:1px;'
		# 							f'padding-top: 1.5px;'
		# 							f'padding-right: 4px;'
		# 							f'padding-bottom: 3px;'
		# 							f'padding-left: 4px;'
		# 							f'font-size: 14px')
		# self.edit_button.setMinimumSize(18,18)
		# # self.edit_button.setMaximumSize(18,18)


		# self.inner_layout.addWidget(self.edit_button)
		if has_remove:
			self.inner_layout.addWidget(self.remove_button)
		self.inner_layout.addStretch(1)
		

		# NOTE: Do this if you don't want the tag to stretch, like in a search.
		# self.bg_button.setMaximumWidth(self.bg_button.sizeHint().width())
		
		# self.set_click(on_click_callback)
		self.bg_button.clicked.connect(self.on_click.emit)

		# self.setMinimumSize(50,20)

	# def set_name(self, name:str):
	# 	self.bg_label.setText(str)

	# def on_remove(self):
	# 	if self.item and self.item[0] == ItemType.ENTRY:
	# 		if self.field_index >= 0:
	# 			self.lib.get_entry(self.item[1]).remove_tag(self.tag.id, self.field_index)
	# 		else:
	# 			self.lib.get_entry(self.item[1]).remove_tag(self.tag.id)

	# def set_click(self, callback):
	# 	try:
	# 		self.bg_button.clicked.disconnect()
	# 	except RuntimeError:
	# 		pass
	# 	if callback:
	# 		self.bg_button.clicked.connect(callback)

	# def set_click(self, function):
	# 	try:
	# 		self.bg.clicked.disconnect()
	# 	except RuntimeError:
	# 		pass
	# 	# self.bg.clicked.connect(lambda checked=False, filepath=filepath: open_file(filepath))
	# 	# self.bg.clicked.connect(function)
	
	def enterEvent(self, event: QEnterEvent) -> None:
		if self.has_remove:
			self.remove_button.setHidden(False)
		# self.edit_button.setHidden(False)
		self.update()
		return super().enterEvent(event)

	def leaveEvent(self, event: QEvent) -> None:
		if self.has_remove:
			self.remove_button.setHidden(True)
		# self.edit_button.setHidden(True)
		self.update()
		return super().leaveEvent(event)

class PanelModal(QWidget):
	saved = Signal()
	# TODO: Separate callbacks from the buttons you want, and just generally
	# figure out what you want from this.
	def __init__(self, widget:'PanelWidget', title:str, window_title:str, 
				 done_callback:FunctionType=None, 
				#  cancel_callback:FunctionType=None,
				 save_callback:FunctionType=None,has_save:bool=False):
		# [Done]
		# - OR -
		# [Cancel] [Save]
		super().__init__()
		self.widget = widget
		self.setWindowTitle(window_title)
		self.setWindowModality(Qt.WindowModality.ApplicationModal)
		self.root_layout = QVBoxLayout(self)
		self.root_layout.setContentsMargins(6,0,6,6)

		self.title_widget = QLabel()
		self.title_widget.setObjectName('fieldTitle')
		self.title_widget.setWordWrap(True)
		self.title_widget.setStyleSheet(
										# 'background:blue;'
								 		# 'text-align:center;'
										'font-weight:bold;'
										'font-size:14px;'
										'padding-top: 6px'
										'')
		self.title_widget.setText(title)
		self.title_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
		

		self.button_container = QWidget()
		self.button_layout = QHBoxLayout(self.button_container)
		self.button_layout.setContentsMargins(6,6,6,6)
		self.button_layout.addStretch(1)

		# self.cancel_button = QPushButton()
		# self.cancel_button.setText('Cancel')

		if not (save_callback or has_save):
			self.done_button = QPushButton()
			self.done_button.setText('Done')
			self.done_button.setAutoDefault(True)
			self.done_button.clicked.connect(self.hide)
			if done_callback:
				self.done_button.clicked.connect(done_callback)
			self.button_layout.addWidget(self.done_button)

		if (save_callback or has_save):
			self.cancel_button = QPushButton()
			self.cancel_button.setText('Cancel')
			self.cancel_button.clicked.connect(self.hide)
			self.cancel_button.clicked.connect(widget.reset)
			# self.cancel_button.clicked.connect(cancel_callback)
			self.button_layout.addWidget(self.cancel_button)
		
		if (save_callback or has_save):
			self.save_button = QPushButton()
			self.save_button.setText('Save')
			self.save_button.setAutoDefault(True)
			self.save_button.clicked.connect(self.hide)
			self.save_button.clicked.connect(self.saved.emit)
			if done_callback:
				self.save_button.clicked.connect(done_callback)
			if save_callback:
				self.save_button.clicked.connect(lambda: save_callback(widget.get_content()))
			self.button_layout.addWidget(self.save_button)
		
		widget.done.connect(lambda: save_callback(widget.get_content()))
		
		self.root_layout.addWidget(self.title_widget)
		self.root_layout.addWidget(widget)
		self.root_layout.setStretch(1,2)
		self.root_layout.addWidget(self.button_container)

class PanelWidget(QWidget):
	"""
	Used for widgets that go in a modal panel, ex. for editing or searching.
	"""
	done = Signal()
	def __init__(self):
		super().__init__()
	def get_content(self)-> str:
		pass
	def reset(self):
		pass

class EditTextBox(PanelWidget):
	def __init__(self, text):
		super().__init__()
		# self.setLayout()
		self.setMinimumSize(480, 480)
		self.root_layout = QVBoxLayout(self)
		self.root_layout.setContentsMargins(6,0,6,0)
		self.text = text
		self.text_edit = QPlainTextEdit()
		self.text_edit.setPlainText(text)
		self.root_layout.addWidget(self.text_edit)
	
	def get_content(self)-> str:
		return self.text_edit.toPlainText()
	
	def reset(self):
		self.text_edit.setPlainText(self.text)

class EditTextLine(PanelWidget):
	def __init__(self, text):
		super().__init__()
		# self.setLayout()
		self.setMinimumWidth(480)
		self.root_layout = QVBoxLayout(self)
		self.root_layout.setContentsMargins(6,0,6,0)
		self.text = text
		self.text_edit = QLineEdit()
		self.text_edit.setText(text)
		self.text_edit.returnPressed.connect(self.done.emit)
		self.root_layout.addWidget(self.text_edit)
	
	def get_content(self)-> str:
		return self.text_edit.text()
	
	def reset(self):
		self.text_edit.setText(self.text)

class TagSearchPanel(PanelWidget):
	tag_chosen = Signal(int)
	def __init__(self, library):
		super().__init__()
		self.lib: Library = library
		# self.callback = callback
		self.first_tag_id = -1
		self.tag_limit = 30
		# self.selected_tag: int = 0
		self.setMinimumSize(300, 400)
		self.root_layout = QVBoxLayout(self)
		self.root_layout.setContentsMargins(6,0,6,0)

		self.search_field = QLineEdit()
		self.search_field.setObjectName('searchField')
		self.search_field.setMinimumSize(QSize(0, 32))
		self.search_field.setPlaceholderText('Search Tags')
		self.search_field.textEdited.connect(lambda x=self.search_field.text(): self.update_tags(x))
		self.search_field.returnPressed.connect(lambda checked=False: self.on_return(self.search_field.text()))

		# self.content_container = QWidget()
		# self.content_layout = QHBoxLayout(self.content_container)

		self.scroll_contents = QWidget()
		self.scroll_layout = QVBoxLayout(self.scroll_contents)
		self.scroll_layout.setContentsMargins(6,0,6,0)
		self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

		self.scroll_area = QScrollArea()
		# self.scroll_area.setStyleSheet('background: #000000;')
		self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
		# self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
		self.scroll_area.setWidgetResizable(True)
		self.scroll_area.setFrameShadow(QFrame.Shadow.Plain)
		self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
		# sa.setMaximumWidth(self.preview_size[0])
		self.scroll_area.setWidget(self.scroll_contents)

		# self.add_button = QPushButton()
		# self.root_layout.addWidget(self.add_button)
		# self.add_button.setText('Add Tag')
		# # self.done_button.clicked.connect(lambda checked=False, x=1101: (callback(x), self.hide()))
		# self.add_button.clicked.connect(lambda checked=False, x=1101: callback(x))
		# # self.setLayout(self.root_layout)

		self.root_layout.addWidget(self.search_field)
		self.root_layout.addWidget(self.scroll_area)

	# def reset(self):
	# 	self.search_field.setText('')
	# 	self.update_tags('')
	# 	self.search_field.setFocus()
	
	def on_return(self, text:str):
		if text and self.first_tag_id >= 0:
			# callback(self.first_tag_id)
			self.tag_chosen.emit(self.first_tag_id)
			self.search_field.setText('')
			self.update_tags('')
		else:
			self.search_field.setFocus()
			self.parentWidget().hide()

	def update_tags(self, query:str):
		# for c in self.scroll_layout.children():
		# 	c.widget().deleteLater()
		while self.scroll_layout.itemAt(0):
			# logging.info(f"I'm deleting { self.scroll_layout.itemAt(0).widget()}")
			self.scroll_layout.takeAt(0).widget().deleteLater()
		
		if query:
			first_id_set = False
			for tag_id in self.lib.search_tags(query, include_cluster=True)[:self.tag_limit-1]:
				if not first_id_set:
					self.first_tag_id = tag_id
					first_id_set = True

				c = QWidget()
				l = QHBoxLayout(c)
				l.setContentsMargins(0,0,0,0)
				l.setSpacing(3)
				tw = TagWidget(self.lib, self.lib.get_tag(tag_id), False, False)
				ab = QPushButton()
				ab.setMinimumSize(23, 23)
				ab.setMaximumSize(23, 23)
				ab.setText('+')
				ab.setStyleSheet(
								f'QPushButton{{'
									f'background: {get_tag_color(ColorType.PRIMARY, self.lib.get_tag(tag_id).color)};'
									# f'background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {get_tag_color(ColorType.PRIMARY, tag.color)}, stop:1.0 {get_tag_color(ColorType.BORDER, tag.color)});'
									# f"border-color:{get_tag_color(ColorType.PRIMARY, tag.color)};"
									f"color: {get_tag_color(ColorType.TEXT, self.lib.get_tag(tag_id).color)};"
									f'font-weight: 600;'
									f"border-color:{get_tag_color(ColorType.BORDER, self.lib.get_tag(tag_id).color)};"
									f'border-radius: 6px;'
									f'border-style:solid;'
									f'border-width: {math.ceil(1*self.devicePixelRatio())}px;'
									# f'padding-top: 1.5px;'
									# f'padding-right: 4px;'
									f'padding-bottom: 5px;'
									# f'padding-left: 4px;'
									f'font-size: 20px;'
									f'}}'
									f'QPushButton::hover'
									f'{{'
									f"border-color:{get_tag_color(ColorType.LIGHT_ACCENT, self.lib.get_tag(tag_id).color)};"
									f"color: {get_tag_color(ColorType.DARK_ACCENT, self.lib.get_tag(tag_id).color)};"
									f'background: {get_tag_color(ColorType.LIGHT_ACCENT, self.lib.get_tag(tag_id).color)};'
									f'}}')

				ab.clicked.connect(lambda checked=False, x=tag_id: self.tag_chosen.emit(x))

				l.addWidget(tw)
				l.addWidget(ab)
				self.scroll_layout.addWidget(c)
		else:
			self.first_tag_id = -1

		self.search_field.setFocus()
	
	# def enterEvent(self, event: QEnterEvent) -> None:
	# 	self.search_field.setFocus()
	# 	return super().enterEvent(event)
	# 	self.focusOutEvent

class BuildTagPanel(PanelWidget):
	on_edit = Signal(Tag)
	def __init__(self, library, tag_id:int=-1):
		super().__init__()
		self.lib: Library = library
		# self.callback = callback
		# self.tag_id = tag_id
		self.tag = None
		self.setMinimumSize(300, 400)
		self.root_layout = QVBoxLayout(self)
		self.root_layout.setContentsMargins(6,0,6,0)
		self.root_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

		# Name -----------------------------------------------------------------
		self.name_widget = QWidget()
		self.name_layout = QVBoxLayout(self.name_widget)
		self.name_layout.setStretch(1, 1)
		self.name_layout.setContentsMargins(0,0,0,0)
		self.name_layout.setSpacing(0)
		self.name_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
		self.name_title = QLabel()
		self.name_title.setText('Name')
		self.name_layout.addWidget(self.name_title)
		self.name_field = QLineEdit()
		self.name_layout.addWidget(self.name_field)

		# Shorthand ------------------------------------------------------------
		self.shorthand_widget = QWidget()
		self.shorthand_layout = QVBoxLayout(self.shorthand_widget)
		self.shorthand_layout.setStretch(1, 1)
		self.shorthand_layout.setContentsMargins(0,0,0,0)
		self.shorthand_layout.setSpacing(0)
		self.shorthand_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
		self.shorthand_title = QLabel()
		self.shorthand_title.setText('Shorthand')
		self.shorthand_layout.addWidget(self.shorthand_title)
		self.shorthand_field = QLineEdit()
		self.shorthand_layout.addWidget(self.shorthand_field)

		# Aliases --------------------------------------------------------------
		self.aliases_widget = QWidget()
		self.aliases_layout = QVBoxLayout(self.aliases_widget)
		self.aliases_layout.setStretch(1, 1)
		self.aliases_layout.setContentsMargins(0,0,0,0)
		self.aliases_layout.setSpacing(0)
		self.aliases_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
		self.aliases_title = QLabel()
		self.aliases_title.setText('Aliases')
		self.aliases_layout.addWidget(self.aliases_title)
		self.aliases_field = QTextEdit()
		self.aliases_field.setAcceptRichText(False)
		self.aliases_field.setMinimumHeight(40)
		self.aliases_layout.addWidget(self.aliases_field)

		# Subtags ------------------------------------------------------------
		self.subtags_widget = QWidget()
		self.subtags_layout = QVBoxLayout(self.subtags_widget)
		self.subtags_layout.setStretch(1, 1)
		self.subtags_layout.setContentsMargins(0,0,0,0)
		self.subtags_layout.setSpacing(0)
		self.subtags_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
		self.subtags_title = QLabel()
		self.subtags_title.setText('Subtags')
		self.subtags_layout.addWidget(self.subtags_title)

		self.scroll_contents = QWidget()
		self.scroll_layout = QVBoxLayout(self.scroll_contents)
		self.scroll_layout.setContentsMargins(6,0,6,0)
		self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

		self.scroll_area = QScrollArea()
		# self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
		self.scroll_area.setWidgetResizable(True)
		self.scroll_area.setFrameShadow(QFrame.Shadow.Plain)
		self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
		self.scroll_area.setWidget(self.scroll_contents)
		# self.scroll_area.setMinimumHeight(60)

		self.subtags_layout.addWidget(self.scroll_area)

		self.subtags_add_button = QPushButton()
		self.subtags_add_button.setText('+')
		tsp = TagSearchPanel(self.lib)
		tsp.tag_chosen.connect(lambda x: self.add_subtag_callback(x))
		self.add_tag_modal = PanelModal(tsp, 'Add Subtags', 'Add Subtags')
		self.subtags_add_button.clicked.connect(self.add_tag_modal.show)
		self.subtags_layout.addWidget(self.subtags_add_button)

		# self.subtags_field = TagBoxWidget()
		# self.subtags_field.setMinimumHeight(60)
		# self.subtags_layout.addWidget(self.subtags_field)

		# Shorthand ------------------------------------------------------------
		self.color_widget = QWidget()
		self.color_layout = QVBoxLayout(self.color_widget)
		self.color_layout.setStretch(1, 1)
		self.color_layout.setContentsMargins(0,0,0,0)
		self.color_layout.setSpacing(0)
		self.color_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
		self.color_title = QLabel()
		self.color_title.setText('Color')
		self.color_layout.addWidget(self.color_title)
		self.color_field = QComboBox()
		self.color_field.setEditable(False)
		self.color_field.setMaxVisibleItems(10)
		self.color_field.setStyleSheet('combobox-popup:0;')
		for color in TAG_COLORS:
			self.color_field.addItem(color.title())
		# self.color_field.setProperty("appearance", "flat")
		self.color_field.currentTextChanged.connect(lambda c: self.color_field.setStyleSheet(f'''combobox-popup:0;									
																					   font-weight:600;
																					   color:{get_tag_color(ColorType.TEXT, c.lower())};
																					   background-color:{get_tag_color(ColorType.PRIMARY, c.lower())};
																					   '''))
		self.color_layout.addWidget(self.color_field)


		# Add Widgets to Layout ================================================
		self.root_layout.addWidget(self.name_widget)
		self.root_layout.addWidget(self.shorthand_widget)
		self.root_layout.addWidget(self.aliases_widget)
		self.root_layout.addWidget(self.subtags_widget)
		self.root_layout.addWidget(self.color_widget)
		# self.parent().done.connect(self.update_tag)

		if tag_id >= 0:
			self.tag = self.lib.get_tag(tag_id)
		else:
			self.tag = Tag(-1, 'New Tag', '', [], [], '')
		self.set_tag(self.tag)
		
	
	def add_subtag_callback(self, tag_id:int):
		logging.info(f'adding {tag_id}')
		# tag = self.lib.get_tag(self.tag_id)
		# TODO: Create a single way to update tags and refresh library data
		# new = self.build_tag()
		self.tag.add_subtag(tag_id)
		# self.tag = new
		# self.lib.update_tag(new)
		self.set_subtags()
		# self.on_edit.emit(self.build_tag())
	
	def remove_subtag_callback(self, tag_id:int):
		logging.info(f'removing {tag_id}')
		# tag = self.lib.get_tag(self.tag_id)
		# TODO: Create a single way to update tags and refresh library data
		# new = self.build_tag()
		self.tag.remove_subtag(tag_id)
		# self.tag = new
		# self.lib.update_tag(new)
		self.set_subtags()
		# self.on_edit.emit(self.build_tag())
	
	def set_subtags(self):
		while self.scroll_layout.itemAt(0):
			self.scroll_layout.takeAt(0).widget().deleteLater()
		logging.info(f'Setting {self.tag.subtag_ids}')
		c = QWidget()
		l = QVBoxLayout(c)
		l.setContentsMargins(0,0,0,0)
		l.setSpacing(3)
		for tag_id in self.tag.subtag_ids:
			tw = TagWidget(self.lib, self.lib.get_tag(tag_id), False, True)
			tw.on_remove.connect(lambda checked=False, t=tag_id: self.remove_subtag_callback(t))
			l.addWidget(tw)
		self.scroll_layout.addWidget(c)

	def set_tag(self, tag:Tag):
		# tag = self.lib.get_tag(tag_id)
		self.name_field.setText(tag.name)
		self.shorthand_field.setText(tag.shorthand)
		self.aliases_field.setText('\n'.join(tag.aliases))
		self.set_subtags()
		self.color_field.setCurrentIndex(TAG_COLORS.index(tag.color.lower()))
		# self.tag_id = tag.id
		
	def build_tag(self) -> Tag:
		# tag: Tag = self.tag
		# if self.tag_id >= 0:
		# 	tag = self.lib.get_tag(self.tag_id)
		# else:
		# 	tag = Tag(-1, '', '', [], [], '')
		new_tag: Tag = Tag(
				id=self.tag.id,
				name=self.name_field.text(),
				shorthand=self.shorthand_field.text(),
				aliases=self.aliases_field.toPlainText().split('\n'),
				subtags_ids=self.tag.subtag_ids,
				color=self.color_field.currentText().lower())
		logging.info(f'built {new_tag}')
		return new_tag
		
		# NOTE: The callback and signal do the same thing, I'm currently
		# transitioning from using callbacks to the Qt method of using signals.
		# self.tag_updated.emit(new_tag)
		# self.callback(new_tag)
	
	# def on_return(self, callback, text:str):
	# 	if text and self.first_tag_id >= 0:
	# 		callback(self.first_tag_id)
	# 		self.search_field.setText('')
	# 		self.update_tags('')
	# 	else:
	# 		self.search_field.setFocus()
	# 		self.parentWidget().hide()


class FunctionIterator(QObject):
	"""Iterates over a yielding function and emits progress as the 'value' signal.\n\nThread-Safe Guarantee™"""
	value = Signal(object)
	def __init__(self, function: FunctionType):
		super().__init__()
		self.iterable = function

	def run(self):
		for i in self.iterable():
			self.value.emit(i)
	

class ProgressWidget(QWidget):
	"""Prebuilt thread-safe progress bar widget."""
	def __init__(self, window_title:str, label_text:str, cancel_button_text:Optional[str], minimum:int, maximum:int):
		super().__init__()
		self.root = QVBoxLayout(self)
		self.pb = QProgressDialog(
			labelText=label_text, 
			minimum=minimum, 
			cancelButtonText=cancel_button_text, 
			maximum=maximum
			)
		self.root.addWidget(self.pb)
		self.setFixedSize(432, 112)
		self.setWindowFlags(self.pb.windowFlags() & ~Qt.WindowType.WindowCloseButtonHint)
		self.setWindowTitle(window_title)
		self.setWindowModality(Qt.WindowModality.ApplicationModal)
	
	def update_label(self, text:str):
		self.pb.setLabelText(text)

	def update_progress(self, value:int):
		self.pb.setValue(value)

class FixDupeFilesModal(QWidget):
	# done = Signal(int)
	def __init__(self, library:'Library', driver:'QtDriver'):
		super().__init__()
		self.lib = library
		self.driver:QtDriver = driver
		self.count = -1
		self.filename = ''
		self.setWindowTitle(f'Fix Duplicate Files')
		self.setWindowModality(Qt.WindowModality.ApplicationModal)
		self.setMinimumSize(400, 300)
		self.root_layout = QVBoxLayout(self)
		self.root_layout.setContentsMargins(6,6,6,6)

		self.desc_widget = QLabel()
		self.desc_widget.setObjectName('descriptionLabel')
		self.desc_widget.setWordWrap(True)
		self.desc_widget.setStyleSheet(
										# 'background:blue;'
								 		'text-align:left;'
										# 'font-weight:bold;'
										# 'font-size:14px;'
										# 'padding-top: 6px'
										'')
		self.desc_widget.setText('''TagStudio supports importing DupeGuru results to manage duplicate files.''')
		self.desc_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)

		self.dupe_count = QLabel()
		self.dupe_count.setObjectName('dupeCountLabel')
		self.dupe_count.setStyleSheet(
										# 'background:blue;'
								 		# 'text-align:center;'
										'font-weight:bold;'
										'font-size:14px;'
										# 'padding-top: 6px'
										'')
		self.dupe_count.setAlignment(Qt.AlignmentFlag.AlignCenter)

		self.file_label = QLabel()
		self.file_label.setObjectName('fileLabel')
		# self.file_label.setStyleSheet(
		# 								# 'background:blue;'
		# 						 		# 'text-align:center;'
		# 								'font-weight:bold;'
		# 								'font-size:14px;'
		# 								# 'padding-top: 6px'
		# 								'')
		# self.file_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
		self.file_label.setText('No DupeGuru File Selected')
		

		self.open_button = QPushButton()
		self.open_button.setText('&Load DupeGuru File')
		self.open_button.clicked.connect(lambda: self.select_file())

		self.mirror_button = QPushButton()
		self.mirror_modal = MirrorEntriesModal(self.lib, self.driver)
		self.mirror_modal.done.connect(lambda: self.refresh_dupes())
		self.mirror_button.setText('&Mirror Entries')
		self.mirror_button.clicked.connect(lambda: self.mirror_modal.show())
		self.mirror_desc = QLabel()
		self.mirror_desc.setWordWrap(True)
		self.mirror_desc.setText("""Mirror the Entry data across each duplicate match set, combining all data while not removing or duplicating fields. This operation will not delete any files or data.""")

		# self.mirror_delete_button = QPushButton()
		# self.mirror_delete_button.setText('Mirror && Delete')

		self.advice_label = QLabel()
		self.advice_label.setWordWrap(True)
		self.advice_label.setText("""After mirroring, you're free to use DupeGuru to delete the unwanted files. Afterwards, use TagStudio's "Fix Unlinked Entries" feature in the Tools menu in order to delete the unlinked Entries.""")
		
		self.button_container = QWidget()
		self.button_layout = QHBoxLayout(self.button_container)
		self.button_layout.setContentsMargins(6,6,6,6)
		self.button_layout.addStretch(1)
	
		self.done_button = QPushButton()
		self.done_button.setText('&Done')
		# self.save_button.setAutoDefault(True)
		self.done_button.setDefault(True)
		self.done_button.clicked.connect(self.hide)
		# self.done_button.clicked.connect(lambda: self.done.emit(self.combo_box.currentIndex()))
		# self.save_button.clicked.connect(lambda: save_callback(widget.get_content()))
		self.button_layout.addWidget(self.done_button)

		# self.returnPressed.connect(lambda: self.done.emit(self.combo_box.currentIndex()))
		
		# self.done.connect(lambda x: callback(x))
		
		self.root_layout.addWidget(self.desc_widget)
		self.root_layout.addWidget(self.dupe_count)
		self.root_layout.addWidget(self.file_label)
		self.root_layout.addWidget(self.open_button)
		# self.mirror_delete_button.setHidden(True)

		self.root_layout.addWidget(self.mirror_button)
		self.root_layout.addWidget(self.mirror_desc)
		# self.root_layout.addWidget(self.mirror_delete_button)
		self.root_layout.addWidget(self.advice_label)
		# self.root_layout.setStretch(1,2)
		self.root_layout.addStretch(1)
		self.root_layout.addWidget(self.button_container)

		self.set_dupe_count(self.count)
	
	def select_file(self):
		qfd = QFileDialog(self, 
					'Open DupeGuru Results File', 
					os.path.normpath(self.lib.library_dir))
		qfd.setFileMode(QFileDialog.FileMode.ExistingFile)
		qfd.setNameFilter("DupeGuru Files (*.dupeguru)")
		filename = []
		if qfd.exec_():
			filename = qfd.selectedFiles()
			if len(filename) > 0:
				self.set_filename(filename[0])
	
	def set_filename(self, filename:str):
		if filename:
			self.file_label.setText(filename)
		else:
			self.file_label.setText('No DupeGuru File Selected')
		self.filename = filename
		self.refresh_dupes()
		self.mirror_modal.refresh_list()
	
	def refresh_dupes(self):
		self.lib.refresh_dupe_files(self.filename)
		self.set_dupe_count(len(self.lib.dupe_files))

	def set_dupe_count(self, count:int):
		self.count = count
		if self.count < 0:
			self.mirror_button.setDisabled(True)
			self.dupe_count.setText(f'Duplicate File Matches: N/A')
		elif self.count == 0:
			self.mirror_button.setDisabled(True)
			self.dupe_count.setText(f'Duplicate File Matches: {count}')
		else:
			self.mirror_button.setDisabled(False)
			self.dupe_count.setText(f'Duplicate File Matches: {count}')


class MirrorEntriesModal(QWidget):
	done = Signal()
	def __init__(self, library:'Library', driver:'QtDriver'):
		super().__init__()
		self.lib = library
		self.driver:QtDriver = driver
		self.setWindowTitle(f'Mirror Entries')
		self.setWindowModality(Qt.WindowModality.ApplicationModal)
		self.setMinimumSize(500, 400)
		self.root_layout = QVBoxLayout(self)
		self.root_layout.setContentsMargins(6,6,6,6)

		self.desc_widget = QLabel()
		self.desc_widget.setObjectName('descriptionLabel')
		self.desc_widget.setWordWrap(True)
		self.desc_widget.setText(f'''
		Are you sure you want to mirror the following {len(self.lib.dupe_files)} Entries?
		''')
		self.desc_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)

		self.list_view = QListView()
		self.model = QStandardItemModel()
		self.list_view.setModel(self.model)
		
		self.button_container = QWidget()
		self.button_layout = QHBoxLayout(self.button_container)
		self.button_layout.setContentsMargins(6,6,6,6)
		self.button_layout.addStretch(1)

		self.cancel_button = QPushButton()
		self.cancel_button.setText('&Cancel')
		self.cancel_button.setDefault(True)
		self.cancel_button.clicked.connect(self.hide)
		self.button_layout.addWidget(self.cancel_button)
	
		self.mirror_button = QPushButton()
		self.mirror_button.setText('&Mirror')
		self.mirror_button.clicked.connect(self.hide)
		self.mirror_button.clicked.connect(lambda: self.mirror_entries())
		self.button_layout.addWidget(self.mirror_button)
		
		self.root_layout.addWidget(self.desc_widget)
		self.root_layout.addWidget(self.list_view)
		self.root_layout.addWidget(self.button_container)
	
	def refresh_list(self):
		self.desc_widget.setText(f'''
		Are you sure you want to mirror the following {len(self.lib.dupe_files)} Entries?
		''')

		self.model.clear()
		for i in self.lib.dupe_files:
			self.model.appendRow(QStandardItem(str(i)))

	def mirror_entries(self):
		# pb = QProgressDialog('', None, 0, len(self.lib.dupe_files))
		# # pb.setMaximum(len(self.lib.missing_files))
		# pb.setFixedSize(432, 112)
		# pb.setWindowFlags(pb.windowFlags() & ~Qt.WindowType.WindowCloseButtonHint)
		# pb.setWindowTitle('Mirroring Entries')
		# pb.setWindowModality(Qt.WindowModality.ApplicationModal)
		# pb.show()

		# r = CustomRunnable(lambda: self.mirror_entries_runnable(pb))
		# r.done.connect(lambda: self.done.emit())
		# r.done.connect(lambda: self.driver.preview_panel.refresh())
		# # r.done.connect(lambda: self.model.clear())
		# # QThreadPool.globalInstance().start(r)
		# r.run()

		iterator = FunctionIterator(self.mirror_entries_runnable)
		pw = ProgressWidget(
			window_title='Mirroring Entries', 
			label_text=f'Mirroring 1/{len(self.lib.dupe_files)} Entries...', 
			cancel_button_text=None, 
			minimum=0,
			maximum=len(self.lib.dupe_files)
			)
		pw.show()
		iterator.value.connect(lambda x: pw.update_progress(x+1))
		iterator.value.connect(lambda x: pw.update_label(f'Mirroring {x+1}/{len(self.lib.dupe_files)} Entries...'))
		r = CustomRunnable(lambda:iterator.run())
		QThreadPool.globalInstance().start(r)
		r.done.connect(lambda: (
							pw.hide(), 
							pw.deleteLater(), 
							self.driver.preview_panel.update_widgets(),
							self.done.emit()
							))
	
	def mirror_entries_runnable(self):
		mirrored = []
		for i, dupe in enumerate(self.lib.dupe_files):
			# pb.setValue(i)
			# pb.setLabelText(f'Mirroring {i}/{len(self.lib.dupe_files)} Entries')
			entry_id_1 = self.lib.get_entry_id_from_filepath(
				dupe[0])
			entry_id_2 = self.lib.get_entry_id_from_filepath(
				dupe[1])
			self.lib.mirror_entry_fields([entry_id_1, entry_id_2])
			sleep(0.005)
			yield i
		for d in mirrored:
			self.lib.dupe_files.remove(d)
		# self.driver.filter_items('')
		# self.done.emit()


class FixUnlinkedEntriesModal(QWidget):
	# done = Signal(int)
	def __init__(self, library:'Library', driver:'QtDriver'):
		super().__init__()
		self.lib = library
		self.driver:QtDriver = driver
		self.count = -1
		self.setWindowTitle(f'Fix Unlinked Entries')
		self.setWindowModality(Qt.WindowModality.ApplicationModal)
		self.setMinimumSize(400, 300)
		self.root_layout = QVBoxLayout(self)
		self.root_layout.setContentsMargins(6,6,6,6)

		self.desc_widget = QLabel()
		self.desc_widget.setObjectName('descriptionLabel')
		self.desc_widget.setWordWrap(True)
		self.desc_widget.setStyleSheet(
										# 'background:blue;'
								 		'text-align:left;'
										# 'font-weight:bold;'
										# 'font-size:14px;'
										# 'padding-top: 6px'
										'')
		self.desc_widget.setText('''Each library entry is linked to a file in one of your directories. If a file linked to an entry is moved or deleted outside of TagStudio, it is then considered unlinked.
		Unlinked entries may be automatically relinked via searching your directories, manually relinked by the user, or deleted if desired.''')
		self.desc_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)

		self.missing_count = QLabel()
		self.missing_count.setObjectName('missingCountLabel')
		self.missing_count.setStyleSheet(
										# 'background:blue;'
								 		# 'text-align:center;'
										'font-weight:bold;'
										'font-size:14px;'
										# 'padding-top: 6px'
										'')
		self.missing_count.setAlignment(Qt.AlignmentFlag.AlignCenter)
		# self.missing_count.setText('Missing Files: N/A')
		

		self.refresh_button = QPushButton()
		self.refresh_button.setText('&Refresh')
		self.refresh_button.clicked.connect(lambda: self.refresh_missing_files())

		self.search_button = QPushButton()
		self.search_button.setText('&Search && Relink')
		self.relink_class = RelinkUnlinkedEntries(self.lib, self.driver)
		self.relink_class.done.connect(lambda: self.refresh_missing_files())
		self.relink_class.done.connect(lambda: self.driver.update_thumbs())
		self.search_button.clicked.connect(lambda: self.relink_class.repair_entries())

		self.manual_button = QPushButton()
		self.manual_button.setText('&Manual Relink')

		self.delete_button = QPushButton()
		self.delete_modal = DeleteUnlinkedEntriesModal(self.lib, self.driver)
		self.delete_modal.done.connect(lambda: self.set_missing_count(len(self.lib.missing_files)))
		self.delete_modal.done.connect(lambda: self.driver.update_thumbs())
		self.delete_button.setText('De&lete Unlinked Entries')
		self.delete_button.clicked.connect(lambda: self.delete_modal.show())
		
		# self.combo_box = QComboBox()
		# self.combo_box.setEditable(False)
		# # self.combo_box.setMaxVisibleItems(5)
		# self.combo_box.setStyleSheet('combobox-popup:0;')
		# self.combo_box.view().setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
		# for df in self.lib.default_fields:
		# 	self.combo_box.addItem(f'{df["name"]} ({df["type"].replace("_", " ").title()})')
		

		self.button_container = QWidget()
		self.button_layout = QHBoxLayout(self.button_container)
		self.button_layout.setContentsMargins(6,6,6,6)
		self.button_layout.addStretch(1)
	
		self.done_button = QPushButton()
		self.done_button.setText('&Done')
		# self.save_button.setAutoDefault(True)
		self.done_button.setDefault(True)
		self.done_button.clicked.connect(self.hide)
		# self.done_button.clicked.connect(lambda: self.done.emit(self.combo_box.currentIndex()))
		# self.save_button.clicked.connect(lambda: save_callback(widget.get_content()))
		self.button_layout.addWidget(self.done_button)

		# self.returnPressed.connect(lambda: self.done.emit(self.combo_box.currentIndex()))
		
		# self.done.connect(lambda x: callback(x))
		
		self.root_layout.addWidget(self.desc_widget)
		self.root_layout.addWidget(self.missing_count)
		self.root_layout.addWidget(self.refresh_button)
		self.root_layout.addWidget(self.search_button)
		self.manual_button.setHidden(True)
		self.root_layout.addWidget(self.manual_button)
		self.root_layout.addWidget(self.delete_button)
		# self.root_layout.setStretch(1,2)
		self.root_layout.addStretch(1)
		self.root_layout.addWidget(self.button_container)

		self.set_missing_count(self.count)

	def refresh_missing_files(self):
		logging.info(f'Start RMF: {QThread.currentThread()}')
		# pb = QProgressDialog(f'Scanning Library for Unlinked Entries...', None, 0,len(self.lib.entries))
		# pb.setFixedSize(432, 112)
		# pb.setWindowFlags(pb.windowFlags() & ~Qt.WindowType.WindowCloseButtonHint)
		# pb.setWindowTitle('Scanning Library')
		# pb.setWindowModality(Qt.WindowModality.ApplicationModal)
		# pb.show()

		iterator = FunctionIterator(self.lib.refresh_missing_files)
		pw = ProgressWidget(
			window_title='Scanning Library', 
			label_text=f'Scanning Library for Unlinked Entries...', 
			cancel_button_text=None, 
			minimum=0,
			maximum=len(self.lib.entries)
			)
		pw.show()
		iterator.value.connect(lambda v: pw.update_progress(v+1))
		# rmf.value.connect(lambda v: pw.update_label(f'Progress: {v}'))
		r = CustomRunnable(lambda:iterator.run())
		QThreadPool.globalInstance().start(r)
		r.done.connect(lambda: (pw.hide(), pw.deleteLater(), 
						  self.set_missing_count(len(self.lib.missing_files)), 
						  						self.delete_modal.refresh_list()))

		# r = CustomRunnable(lambda: self.lib.refresh_missing_files(lambda v: self.update_scan_value(pb, v)))
		# r.done.connect(lambda: (pb.hide(), pb.deleteLater(), self.set_missing_count(len(self.lib.missing_files)), self.delete_modal.refresh_list()))
		# QThreadPool.globalInstance().start(r)
		# # r.run()
		# pass

	# def update_scan_value(self, pb:QProgressDialog, value=int):
	# 	# pb.setLabelText(f'Scanning Library for Unlinked Entries ({value}/{len(self.lib.entries)})...')
	# 	pb.setValue(value)

	def set_missing_count(self, count:int):
		self.count = count
		if self.count < 0:
			self.search_button.setDisabled(True)
			self.delete_button.setDisabled(True)
			self.missing_count.setText(f'Unlinked Entries: N/A')
		elif self.count == 0:
			self.search_button.setDisabled(True)
			self.delete_button.setDisabled(True)
			self.missing_count.setText(f'Unlinked Entries: {count}')
		else:
			self.search_button.setDisabled(False)
			self.delete_button.setDisabled(False)
			self.missing_count.setText(f'Unlinked Entries: {count}')


class DeleteUnlinkedEntriesModal(QWidget):
	done = Signal()
	def __init__(self, library:'Library', driver:'QtDriver'):
		super().__init__()
		self.lib = library
		self.driver:QtDriver = driver
		self.setWindowTitle(f'Delete Unlinked Entries')
		self.setWindowModality(Qt.WindowModality.ApplicationModal)
		self.setMinimumSize(500, 400)
		self.root_layout = QVBoxLayout(self)
		self.root_layout.setContentsMargins(6,6,6,6)

		self.desc_widget = QLabel()
		self.desc_widget.setObjectName('descriptionLabel')
		self.desc_widget.setWordWrap(True)
		self.desc_widget.setText(f'''
		Are you sure you want to delete the following {len(self.lib.missing_files)} entries?
		''')
		self.desc_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)

		self.list_view = QListView()
		self.model = QStandardItemModel()
		self.list_view.setModel(self.model)
		
		self.button_container = QWidget()
		self.button_layout = QHBoxLayout(self.button_container)
		self.button_layout.setContentsMargins(6,6,6,6)
		self.button_layout.addStretch(1)

		self.cancel_button = QPushButton()
		self.cancel_button.setText('&Cancel')
		self.cancel_button.setDefault(True)
		self.cancel_button.clicked.connect(self.hide)
		self.button_layout.addWidget(self.cancel_button)
	
		self.delete_button = QPushButton()
		self.delete_button.setText('&Delete')
		self.delete_button.clicked.connect(self.hide)
		self.delete_button.clicked.connect(lambda: self.delete_entries())
		self.button_layout.addWidget(self.delete_button)
		
		self.root_layout.addWidget(self.desc_widget)
		self.root_layout.addWidget(self.list_view)
		self.root_layout.addWidget(self.button_container)

	def refresh_list(self):
		self.desc_widget.setText(f'''
		Are you sure you want to delete the following {len(self.lib.missing_files)} entries?
		''')

		self.model.clear()
		for i in self.lib.missing_files:
			self.model.appendRow(QStandardItem(i))

	def delete_entries(self):
		# pb = QProgressDialog('', None, 0, len(self.lib.missing_files))
		# # pb.setMaximum(len(self.lib.missing_files))
		# pb.setFixedSize(432, 112)
		# pb.setWindowFlags(pb.windowFlags() & ~Qt.WindowType.WindowCloseButtonHint)
		# pb.setWindowTitle('Deleting Entries')
		# pb.setWindowModality(Qt.WindowModality.ApplicationModal)
		# pb.show()

		# r = CustomRunnable(lambda: self.lib.ref(pb))
		# r.done.connect(lambda: self.done.emit())
		# # r.done.connect(lambda: self.model.clear())
		# QThreadPool.globalInstance().start(r)
		# # r.run()



		iterator = FunctionIterator(self.lib.remove_missing_files)

		pw = ProgressWidget(
			window_title='Deleting Entries', 
			label_text='', 
			cancel_button_text=None, 
			minimum=0,
			maximum=len(self.lib.missing_files)
			)
		pw.show()
		
		iterator.value.connect(lambda x: pw.update_progress(x[0]+1))
		iterator.value.connect(lambda x: pw.update_label(f'Deleting {x[0]+1}/{len(self.lib.missing_files)} Unlinked Entries'))
		iterator.value.connect(lambda x: self.driver.purge_item_from_navigation(ItemType.ENTRY, x[1]))

		r = CustomRunnable(lambda:iterator.run())
		QThreadPool.globalInstance().start(r)
		r.done.connect(lambda: (pw.hide(), pw.deleteLater(), self.done.emit()))
	
	# def delete_entries_runnable(self):
	# 	deleted = []
	# 	for i, missing in enumerate(self.lib.missing_files):
	# 		# pb.setValue(i)
	# 		# pb.setLabelText(f'Deleting {i}/{len(self.lib.missing_files)} Unlinked Entries')
	# 		try:
	# 			id = self.lib.get_entry_id_from_filepath(missing)
	# 			logging.info(f'Removing Entry ID {id}:\n\t{missing}')
	# 			self.lib.remove_entry(id)
	# 			self.driver.purge_item_from_navigation(ItemType.ENTRY, id)
	# 			deleted.append(missing)
	# 		except KeyError:
	# 			logging.info(
	# 				f'{ERROR} \"{id}\" was reported as missing, but is not in the file_to_entry_id map.')
	# 		yield i
	# 	for d in deleted:
	# 		self.lib.missing_files.remove(d)
	# 	# self.driver.filter_items('')
	# 	# self.done.emit()


class RelinkUnlinkedEntries(QObject):
	done = Signal()
	def __init__(self, library:'Library', driver:'QtDriver'):
		super().__init__()
		self.lib = library
		self.driver:QtDriver = driver
		self.fixed = 0

	def repair_entries(self):
		# pb = QProgressDialog('', None, 0, len(self.lib.missing_files))
		# # pb.setMaximum(len(self.lib.missing_files))
		# pb.setFixedSize(432, 112)
		# pb.setWindowFlags(pb.windowFlags() & ~Qt.WindowType.WindowCloseButtonHint)
		# pb.setWindowTitle('Relinking Entries')
		# pb.setWindowModality(Qt.WindowModality.ApplicationModal)
		# pb.show()

		# r = CustomRunnable(lambda: self.repair_entries_runnable(pb))
		# r.done.connect(lambda: self.done.emit())
		# # r.done.connect(lambda: self.model.clear())
		# QThreadPool.globalInstance().start(r)
		# # r.run()




		iterator = FunctionIterator(self.lib.fix_missing_files)

		pw = ProgressWidget(
			window_title='Relinking Entries', 
			label_text='', 
			cancel_button_text=None, 
			minimum=0,
			maximum=len(self.lib.missing_files)
			)
		pw.show()

		iterator.value.connect(lambda x: pw.update_progress(x[0]+1))
		iterator.value.connect(lambda x: (self.increment_fixed() if x[1] else (), pw.update_label(f'Attempting to Relink {x[0]+1}/{len(self.lib.missing_files)} Entries, {self.fixed} Successfully Relinked')))
		# iterator.value.connect(lambda x: self.driver.purge_item_from_navigation(ItemType.ENTRY, x[1]))

		r = CustomRunnable(lambda:iterator.run())
		r.done.connect(lambda: (pw.hide(), pw.deleteLater(), self.done.emit(), self.reset_fixed()))
		QThreadPool.globalInstance().start(r)
	
	def increment_fixed(self):
		self.fixed += 1
	
	def reset_fixed(self):
		self.fixed = 0

	# def repair_entries_runnable(self, pb: QProgressDialog):
	# 	fixed = 0
	# 	for i in self.lib.fix_missing_files():
	# 		if i[1]:
	# 			fixed += 1
	# 		pb.setValue(i[0])
	# 		pb.setLabelText(f'Attempting to Relink {i[0]+1}/{len(self.lib.missing_files)} Entries, {fixed} Successfully Relinked')

		# for i, missing in enumerate(self.lib.missing_files):
		# 	pb.setValue(i)
		# 	pb.setLabelText(f'Relinking {i}/{len(self.lib.missing_files)} Unlinked Entries')
		# 	self.lib.fix_missing_files()
		# 	try:
		# 		id = self.lib.get_entry_id_from_filepath(missing)
		# 		logging.info(f'Removing Entry ID {id}:\n\t{missing}')
		# 		self.lib.remove_entry(id)
		# 		self.driver.purge_item_from_navigation(ItemType.ENTRY, id)
		# 		deleted.append(missing)
		# 	except KeyError:
		# 		logging.info(
		# 			f'{ERROR} \"{id}\" was reported as missing, but is not in the file_to_entry_id map.')
		# for d in deleted:
		# 	self.lib.missing_files.remove(d)


class AddFieldModal(QWidget):
	done = Signal(int)
	def __init__(self, library:'Library'):
		# [Done]
		# - OR -
		# [Cancel] [Save]
		super().__init__()
		self.lib = library
		self.setWindowTitle(f'Add Field')
		self.setWindowModality(Qt.WindowModality.ApplicationModal)
		self.setMinimumSize(400, 300)
		self.root_layout = QVBoxLayout(self)
		self.root_layout.setContentsMargins(6,6,6,6)

		self.title_widget = QLabel()
		self.title_widget.setObjectName('fieldTitle')
		self.title_widget.setWordWrap(True)
		self.title_widget.setStyleSheet(
										# 'background:blue;'
								 		# 'text-align:center;'
										'font-weight:bold;'
										'font-size:14px;'
										'padding-top: 6px'
										'')
		self.title_widget.setText('Add Field')
		self.title_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
		
		self.combo_box = QComboBox()
		self.combo_box.setEditable(False)
		# self.combo_box.setMaxVisibleItems(5)
		self.combo_box.setStyleSheet('combobox-popup:0;')
		self.combo_box.view().setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
		for df in self.lib.default_fields:
			self.combo_box.addItem(f'{df["name"]} ({df["type"].replace("_", " ").title()})')

		self.button_container = QWidget()
		self.button_layout = QHBoxLayout(self.button_container)
		self.button_layout.setContentsMargins(6,6,6,6)
		self.button_layout.addStretch(1)

		# self.cancel_button = QPushButton()
		# self.cancel_button.setText('Cancel')

		self.cancel_button = QPushButton()
		self.cancel_button.setText('Cancel')
		self.cancel_button.clicked.connect(self.hide)
		# self.cancel_button.clicked.connect(widget.reset)
		self.button_layout.addWidget(self.cancel_button)
	
		self.save_button = QPushButton()
		self.save_button.setText('Add')
		# self.save_button.setAutoDefault(True)
		self.save_button.setDefault(True)
		self.save_button.clicked.connect(self.hide)
		self.save_button.clicked.connect(lambda: self.done.emit(self.combo_box.currentIndex()))
		# self.save_button.clicked.connect(lambda: save_callback(widget.get_content()))
		self.button_layout.addWidget(self.save_button)

		# self.returnPressed.connect(lambda: self.done.emit(self.combo_box.currentIndex()))
		
		# self.done.connect(lambda x: callback(x))
		
		self.root_layout.addWidget(self.title_widget)
		self.root_layout.addWidget(self.combo_box)
		# self.root_layout.setStretch(1,2)
		self.root_layout.addStretch(1)
		self.root_layout.addWidget(self.button_container)

class PreviewPanel(QWidget):
	"""The Preview Panel Widget."""
	tags_updated = Signal()

	def __init__(self, library: Library, driver:'QtDriver'):
		super().__init__()
		self.lib = library
		self.driver:QtDriver = driver
		self.initialized = False
		self.isOpen: bool = False
		# self.filepath = None
		# self.item = None # DEPRECATED, USE self.selected
		self.common_fields = []
		self.mixed_fields = []
		self.selected: list[tuple[ItemType, int]] = [] # New way of tracking items
		self.tag_callback = None
		self.containers: list[QWidget] = []

		self.img_button_size: tuple[int, int] = (266, 266)
		self.image_ratio: float = 1.0

		root_layout = QHBoxLayout(self)
		root_layout.setContentsMargins(0, 0, 0, 0)
		
		self.image_container = QWidget()
		image_layout = QHBoxLayout(self.image_container)
		image_layout.setContentsMargins(0, 0, 0, 0)

		splitter = QSplitter()
		splitter.setOrientation(Qt.Orientation.Vertical)
		splitter.setHandleWidth(12)
		
		self.preview_img = QPushButton()
		self.preview_img.setMinimumSize(*self.img_button_size)
		self.preview_img.setFlat(True)
		self.tr = ThumbRenderer()
		self.tr.updated.connect(lambda ts, i, s: (self.preview_img.setIcon(i)))
		self.tr.updated_ratio.connect(lambda ratio: (self.set_image_ratio(ratio), 
											   self.update_image_size((self.image_container.size().width(), self.image_container.size().height()), ratio)))

		splitter.splitterMoved.connect(lambda: self.update_image_size((self.image_container.size().width(), self.image_container.size().height())))
		splitter.addWidget(self.image_container)

		image_layout.addWidget(self.preview_img)
		image_layout.setAlignment(self.preview_img, Qt.AlignmentFlag.AlignCenter)

		self.file_label = QLabel('Filename')
		self.file_label.setWordWrap(True)
		self.file_label.setTextInteractionFlags(
			Qt.TextInteractionFlag.TextSelectableByMouse)
		self.file_label.setStyleSheet('font-weight: bold; font-size: 12px')

		self.dimensions_label = QLabel('Dimensions')
		self.dimensions_label.setWordWrap(True)
		# self.dim_label.setTextInteractionFlags(
		# 	Qt.TextInteractionFlag.TextSelectableByMouse)
		self.dimensions_label.setStyleSheet(ItemThumb.small_text_style)
		
	# 	small_text_style = (
	# 	f'background-color:rgba(17, 15, 27, 192);'
	# 	f'font-family:Oxanium;'
	# 	f'font-weight:bold;'
	# 	f'font-size:12px;'
	# 	f'border-radius:3px;'
	# 	f'padding-top: 4px;'
	# 	f'padding-right: 1px;'
	# 	f'padding-bottom: 1px;'
	# 	f'padding-left: 1px;'
	# )

		self.scroll_layout = QVBoxLayout()
		self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
		self.scroll_layout.setContentsMargins(6,1,6,6)

		scroll_container: QWidget = QWidget()
		scroll_container.setObjectName('entryScrollContainer')
		scroll_container.setLayout(self.scroll_layout)
		# scroll_container.setStyleSheet('background:#080716; border-radius:12px;')
		scroll_container.setStyleSheet(
			'background:#00000000;'
			'border-style:none;'
			f'QScrollBar::{{background:red;}}'
			)
		

		info_section = QWidget()
		info_layout = QVBoxLayout(info_section)
		info_layout.setContentsMargins(0,0,0,0)
		info_layout.setSpacing(6)
		self.setStyleSheet(
			'background:#00000000;'
			f'QScrollBar::{{background:red;}}'
			)

		scroll_area = QScrollArea()
		scroll_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
		scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
		scroll_area.setWidgetResizable(True)
		scroll_area.setFrameShadow(QFrame.Shadow.Plain)
		scroll_area.setFrameShape(QFrame.Shape.NoFrame)
		scroll_area.setStyleSheet(
			'background:#55000000;' 
			'border-radius:12px;'
			'border-style:solid;'
			'border-width:1px;'
			'border-color:#11FFFFFF;'
			# f'QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{border: none;background: none;}}'
			# f'QScrollBar::left-arrow:horizontal, QScrollBar::right-arrow:horizontal, QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{border: none;background: none;color: none;}}'
			f'QScrollBar::{{background:red;}}'
			)
		scroll_area.setWidget(scroll_container)

		info_layout.addWidget(self.file_label)
		info_layout.addWidget(self.dimensions_label)
		info_layout.addWidget(scroll_area)
		splitter.addWidget(info_section)

		root_layout.addWidget(splitter)
		splitter.setStretchFactor(1, 2)
		
		self.afb_container = QWidget()
		self.afb_layout = QVBoxLayout(self.afb_container)
		self.afb_layout.setContentsMargins(0,12,0,0)

		self.add_field_button = QPushButton()
		self.add_field_button.setCursor(Qt.CursorShape.PointingHandCursor)
		self.add_field_button.setMinimumSize(96, 28)
		self.add_field_button.setMaximumSize(96, 28)
		self.add_field_button.setText('Add Field')
		self.add_field_button.setStyleSheet(
									f'QPushButton{{'
									# f'background: #1E1A33;'
									# f'color: #CDA7F7;'
									f'font-weight: bold;'
									# f"border-color: #2B2547;"
									f'border-radius: 6px;'
									f'border-style:solid;'
									# f'border-width:{math.ceil(1*self.devicePixelRatio())}px;'
									'background:#55000000;' 
									'border-width:1px;'
									'border-color:#11FFFFFF;'
									# f'padding-top: 1.5px;'
									# f'padding-right: 4px;'
									# f'padding-bottom: 5px;'
									# f'padding-left: 4px;'
									f'font-size: 13px;'
									f'}}'
									f'QPushButton::hover'
									f'{{'
									f'background: #333333;'
									f'}}')
		self.afb_layout.addWidget(self.add_field_button)
		self.afm = AddFieldModal(self.lib)
		self.place_add_field_button()
		self.update_image_size((self.image_container.size().width(), self.image_container.size().height()))

	def resizeEvent(self, event: QResizeEvent) -> None:
		self.update_image_size((self.image_container.size().width(), self.image_container.size().height()))
		return super().resizeEvent(event)
	
	def get_preview_size(self) -> tuple[int, int]:
		return (self.image_container.size().width(), self.image_container.size().height())

	def set_image_ratio(self, ratio:float):
		# logging.info(f'Updating Ratio to: {ratio} #####################################################')
		self.image_ratio = ratio
		
	def update_image_size(self, size:tuple[int, int], ratio:float = None):
		if ratio:
			self.set_image_ratio(ratio)
		# self.img_button_size = size
		# logging.info(f'')
		# self.preview_img.setMinimumSize(64,64)

		adj_width = size[0]
		adj_height = size[1]
		# Landscape
		if self.image_ratio > 1:
			# logging.info('Landscape')
			adj_height = size[0] * (1/self.image_ratio)
		# Portrait
		elif self.image_ratio <= 1:
			# logging.info('Portrait')
			adj_width = size[1] * self.image_ratio
		
		if adj_width > size[0]:
			adj_height = adj_height * (size[0]/adj_width)
			adj_width = size[0]
		elif adj_height > size[1]:
			adj_width = adj_width * (size[1]/adj_height)
			adj_height = size[1]
		
		# adj_width = min(adj_width, self.image_container.size().width())
		# adj_height = min(adj_width, self.image_container.size().height())

		# self.preview_img.setMinimumSize(s)
		# self.preview_img.setMaximumSize(s_max)
		adj_size = QSize(adj_width, adj_height)
		self.img_button_size = (adj_width, adj_height)
		self.preview_img.setMaximumSize(adj_size)
		self.preview_img.setIconSize(adj_size)
		# self.preview_img.setMinimumSize(adj_size)

		# if self.preview_img.iconSize().toTuple()[0] < self.preview_img.size().toTuple()[0] + 10:
		# 	if type(self.item) == Entry:
		# 		filepath = os.path.normpath(f'{self.lib.library_dir}/{self.item.path}/{self.item.filename}')
		# 		self.tr.render_big(time.time(), filepath, self.preview_img.size().toTuple(), self.devicePixelRatio())
		
		# logging.info(f' Img Aspect Ratio: {self.image_ratio}')
		# logging.info(f'  Max Button Size: {size}')
		# logging.info(f'Container Size: {(self.image_container.size().width(), self.image_container.size().height())}')
		# logging.info(f'Final Button Size: {(adj_width, adj_height)}')
		# logging.info(f'')
		# logging.info(f'  Icon Size: {self.preview_img.icon().actualSize().toTuple()}')
		# logging.info(f'Button Size: {self.preview_img.size().toTuple()}')
		
	def place_add_field_button(self):
		self.scroll_layout.addWidget(self.afb_container)
		self.scroll_layout.setAlignment(self.afb_container, Qt.AlignmentFlag.AlignHCenter)

		try:
			self.afm.done.disconnect()
			self.add_field_button.clicked.disconnect()
		except RuntimeError:
			pass

		# self.afm.done.connect(lambda f: (self.lib.add_field_to_entry(self.selected[0][1], f), self.update_widgets()))
		self.afm.done.connect(lambda f: (self.add_field_to_selected(f), self.update_widgets()))
		self.add_field_button.clicked.connect(self.afm.show)
	
	def add_field_to_selected(self, field_id: int):
		"""Adds an entry field to one or more selected items."""
		added = set()
		for item_pair in self.selected:
			if item_pair[0] == ItemType.ENTRY and item_pair[1] not in added:
				self.lib.add_field_to_entry(item_pair[1], field_id)
				added.add(item_pair[1])
		

	# def update_widgets(self, item: Union[Entry, Collation, Tag]):
	def update_widgets(self):
		"""
		Renders the panel's widgets with the newest data from the Library.
		"""
		logging.info(f'[ENTRY PANEL] UPDATE WIDGETS ({self.driver.selected})' )
		self.isOpen = True
		# self.tag_callback = tag_callback if tag_callback else None
		window_title = ''
		
		# 0 Selected Items
		if len(self.driver.selected) == 0:
			if len(self.selected) != 0 or not self.initialized:
				self.file_label.setText(f"No Items Selected")
				self.dimensions_label.setText("")
				ratio: float = self.devicePixelRatio()
				self.tr.render_big(time.time(), '', (512, 512), ratio, True)
				try:
					self.preview_img.clicked.disconnect()
				except RuntimeError:
					pass
				for i, c in enumerate(self.containers):
					c.setHidden(True)

			self.selected = list(self.driver.selected)
			self.add_field_button.setHidden(True)
		
		# 1 Selected Item
		elif len(self.driver.selected) == 1:

			# 1 Selected Entry
			if self.driver.selected[0][0] == ItemType.ENTRY:
				item: Entry = self.lib.get_entry(self.driver.selected[0][1])
				# If a new selection is made, update the thumbnail and filepath.
				if (len(self.selected) == 0 
						or self.selected != self.driver.selected):
					filepath = os.path.normpath(f'{self.lib.library_dir}/{item.path}/{item.filename}')
					window_title = filepath
					ratio: float = self.devicePixelRatio()
					self.tr.render_big(time.time(), filepath, (512, 512), ratio)
					self.file_label.setText("\u200b".join(filepath))

					# TODO: Do this somewhere else, this is just here temporarily.
					extension = os.path.splitext(filepath)[1][1:].lower()
					try:
						image = None
						if extension in IMAGE_TYPES:
							image = Image.open(filepath)
							if image.mode == 'RGBA':
								new_bg = Image.new('RGB', image.size, color='#222222')
								new_bg.paste(image, mask=image.getchannel(3))
								image = new_bg
							if image.mode != 'RGB':
								image = image.convert(mode='RGB')
						elif extension in VIDEO_TYPES:
							video = cv2.VideoCapture(filepath)
							video.set(cv2.CAP_PROP_POS_FRAMES,
									(video.get(cv2.CAP_PROP_FRAME_COUNT) // 2))
							success, frame = video.read()
							if not success:
								# Depending on the video format, compression, and frame
								# count, seeking halfway does not work and the thumb
								# must be pulled from the earliest available frame.
								video.set(cv2.CAP_PROP_POS_FRAMES, 0)
								success, frame = video.read()
							frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
							image = Image.fromarray(frame)

						# Stats for specific file types are displayed here.
						if extension in (IMAGE_TYPES + VIDEO_TYPES):
							self.dimensions_label.setText(f"{extension.upper()}  •  {format_size(os.stat(filepath).st_size)}\n{image.width} x {image.height} px")
						else:
							self.dimensions_label.setText(f"{extension.upper()}")

						if not image:
							self.dimensions_label.setText(f"{extension.upper()}  •  {format_size(os.stat(filepath).st_size)}")
							raise UnidentifiedImageError
						
					except (UnidentifiedImageError, FileNotFoundError, cv2.error):
						pass

					

					try:
						self.preview_img.clicked.disconnect()
					except RuntimeError:
						pass
					self.preview_img.clicked.connect(
						lambda checked=False, filepath=filepath: open_file(filepath))
				
				self.selected = list(self.driver.selected)
				for i, f in enumerate(item.fields):
					self.write_container(i, f)

				# Hide leftover containers
				if len(self.containers) > len(item.fields):
					for i, c in enumerate(self.containers):
						if i > (len(item.fields) - 1):
							c.setHidden(True)
				
				self.add_field_button.setHidden(False)

			# 1 Selected Collation
			elif self.driver.selected[0][0] == ItemType.COLLATION:
				pass

			# 1 Selected Tag
			elif self.driver.selected[0][0] == ItemType.TAG_GROUP:
				pass

		# Multiple Selected Items
		elif len(self.driver.selected) > 1:
			if self.selected != self.driver.selected:
				self.file_label.setText(f"{len(self.driver.selected)} Items Selected")
				self.dimensions_label.setText("")
				ratio: float = self.devicePixelRatio()
				self.tr.render_big(time.time(), '', (512, 512), ratio, True)
				try:
					self.preview_img.clicked.disconnect()
				except RuntimeError:
					pass

			self.common_fields = []
			self.mixed_fields = []
			for i, item_pair in enumerate(self.driver.selected):
				if item_pair[0] == ItemType.ENTRY:
					item = self.lib.get_entry(item_pair[1])
					if i == 0:
						for f in item.fields:
							self.common_fields.append(f)
					else:
						common_to_remove = []
						for f in self.common_fields:
							# Common field found (Same ID, identical content)
							if f not in item.fields:
								common_to_remove.append(f)
						
								# Mixed field found (Same ID, different content)
								if self.lib.get_field_index_in_entry(item, self.lib.get_field_attr(f, 'id')):
									# if self.lib.get_field_attr(f, 'type') == ('tag_box'):
									# 	pass
									# logging.info(f)
									# logging.info(type(f))
									f_stripped = {self.lib.get_field_attr(f, 'id'):None}
									if f_stripped not in self.mixed_fields and (f not in self.common_fields or f in common_to_remove):
										#  and (f not in self.common_fields or f in common_to_remove)
										self.mixed_fields.append(f_stripped)
						self.common_fields = [f for f in self.common_fields if f not in common_to_remove]
			order: list[int] = (
				[0] + 
				[1, 2] + 
				[9, 17, 18, 19, 20] + 
				[8, 7, 6] + 
				[4] + 
				[3, 21] +
				[10, 14, 11, 12, 13, 22] +
				[5]
				)
			self.mixed_fields = sorted(self.mixed_fields, key=lambda x: order.index(self.lib.get_field_attr(x, 'id')))

						
								
			self.selected = list(self.driver.selected)
			for i, f in enumerate(self.common_fields):
				logging.info(f'ci:{i}, f:{f}')
				self.write_container(i, f)
			for i, f in enumerate(self.mixed_fields, start = len(self.common_fields)):
				logging.info(f'mi:{i}, f:{f}')
				self.write_container(i, f, mixed=True)
			
			# Hide leftover containers
			if len(self.containers) > len(self.common_fields) + len(self.mixed_fields):
				for i, c in enumerate(self.containers):
					if i > (len(self.common_fields) + len(self.mixed_fields) - 1):
						c.setHidden(True)
			
			self.add_field_button.setHidden(False)
		
		self.initialized = True


		# # Uninitialized or New Item:
		# if not self.item or self.item.id != item.id:
		# 	# logging.info(f'Uninitialized or New Item ({item.id})')
		# 	if type(item) == Entry:
		# 		# New Entry: Render preview and update filename label
		# 		filepath = os.path.normpath(f'{self.lib.library_dir}/{item.path}/{item.filename}')
		# 		window_title = filepath
		# 		ratio: float = self.devicePixelRatio()
		# 		self.tr.render_big(time.time(), filepath, (512, 512), ratio)
		# 		self.file_label.setText("\u200b".join(filepath))

		# 		# TODO: Deal with this later. 
		# 		# https://stackoverflow.com/questions/64252654/pyqt5-drag-and-drop-into-system-file-explorer-with-delayed-encoding
		# 		# https://doc.qt.io/qtforpython-5/PySide2/QtCore/QMimeData.html#more
		# 		# drag = QDrag(self.preview_img)
		# 		# mime = QMimeData()
		# 		# mime.setUrls([filepath])
		# 		# drag.setMimeData(mime)
		# 		# drag.exec_(Qt.DropAction.CopyAction)

		# 		try:
		# 			self.preview_img.clicked.disconnect()
		# 		except RuntimeError:
		# 			pass
		# 		self.preview_img.clicked.connect(
		# 			lambda checked=False, filepath=filepath: open_file(filepath))
				
		# 		for i, f in enumerate(item.fields):
		# 			self.write_container(item, i, f)

		# 		self.item = item

		# 		# try:
		# 		# 	self.tags_updated.disconnect()
		# 		# except RuntimeError:
		# 		# 	pass
		# 		# if self.tag_callback:
		# 		# 	# logging.info(f'[UPDATE CONTAINER] Updating Callback for {item.id}: {self.tag_callback}')
		# 		# 	self.tags_updated.connect(self.tag_callback)

				

		# # Initialized, Updating:
		# elif self.item and self.item.id == item.id:
		# 	# logging.info(f'Initialized Item, Updating! ({item.id})')
		# 	for i, f in enumerate(item.fields):
		# 		self.write_container(item, i, f)
		
		# # Hide leftover containers
		# if len(self.containers) > len(self.item.fields):
		# 	for i, c in enumerate(self.containers):
		# 		if i > (len(self.item.fields) - 1):
		# 			c.setHidden(True)

		

		self.setWindowTitle(window_title)
		self.show()

	def set_tags_updated_slot(self, slot: object):
		"""
		Replacement for tag_callback.
		"""
		try:
			self.tags_updated.disconnect()
		except RuntimeError:
			pass
		logging.info(f'[UPDATE CONTAINER] Setting tags updated slot')
		self.tags_updated.connect(slot)

	# def write_container(self, item:Union[Entry, Collation, Tag], index, field):
	def write_container(self, index, field, mixed=False):
		"""Updates/Creates data for a FieldContainer."""
		# logging.info(f'[ENTRY PANEL] WRITE CONTAINER')
		# Remove 'Add Field' button from scroll_layout, to be re-added later.
		self.scroll_layout.takeAt(self.scroll_layout.count()-1).widget()
		container: FieldContainer = None
		if len(self.containers) < (index + 1):
			container = FieldContainer()
			self.containers.append(container)
			self.scroll_layout.addWidget(container)
		else:
			container = self.containers[index]
			# container.inner_layout.removeItem(container.inner_layout.itemAt(1))
			# container.setHidden(False)
		if self.lib.get_field_attr(field, 'type') == 'tag_box':
			# logging.info(f'WRITING TAGBOX FOR ITEM {item.id}')
			container.set_title(self.lib.get_field_attr(field, 'name'))
			# container.set_editable(False)
			container.set_inline(False)
			title = f"{self.lib.get_field_attr(field, 'name')} (Tag Box)"
			if not mixed:
				item = self.lib.get_entry(self.selected[0][1]) # TODO TODO TODO: TEMPORARY
				if type(container.get_inner_widget()) == TagBoxWidget:
					inner_container: TagBoxWidget = container.get_inner_widget()
					inner_container.set_item(item)
					inner_container.set_tags(self.lib.get_field_attr(field, 'content'))
					try:
						inner_container.updated.disconnect()
					except RuntimeError:
						pass
					# inner_container.updated.connect(lambda f=self.filepath, i=item: self.write_container(item, index, field))
				else:
					inner_container = TagBoxWidget(item, title, index, self.lib, self.lib.get_field_attr(field, 'content'), self.driver)
					
					container.set_inner_widget(inner_container)
				inner_container.field = field
				inner_container.updated.connect(lambda: (self.write_container(index, field), self.tags_updated.emit()))
				# if type(item) == Entry:
				# NOTE: Tag Boxes have no Edit Button (But will when you can convert field types)
				# f'Are you sure you want to remove this \"{self.lib.get_field_attr(field, "name")}\" field?'
				# container.set_remove_callback(lambda: (self.lib.get_entry(item.id).fields.pop(index), self.update_widgets(item)))
				prompt=f'Are you sure you want to remove this \"{self.lib.get_field_attr(field, "name")}\" field?'
				callback = lambda: (self.remove_field(field), self.update_widgets())
				container.set_remove_callback(lambda: self.remove_message_box(
					prompt=prompt,
					callback=callback))
				container.set_copy_callback(None)
				container.set_edit_callback(None)
			else:
				text = '<i>Mixed Data</i>'
				title = f"{self.lib.get_field_attr(field, 'name')} (Wacky Tag Box)"
				inner_container = TextWidget(title, text)
				container.set_inner_widget(inner_container)
				container.set_copy_callback(None)
				container.set_edit_callback(None)
				container.set_remove_callback(None)
			
			
			self.tags_updated.emit()
			# self.dynamic_widgets.append(inner_container)
		elif self.lib.get_field_attr(field, 'type') in 'text_line':
			# logging.info(f'WRITING TEXTLINE FOR ITEM {item.id}')
			container.set_title(self.lib.get_field_attr(field, 'name'))
			# container.set_editable(True)
			container.set_inline(False)
			# Normalize line endings in any text content.
			text: str = ''
			if not mixed: 
				text = self.lib.get_field_attr(
					field, 'content').replace('\r', '\n')
			else:
				text = '<i>Mixed Data</i>'
			title = f"{self.lib.get_field_attr(field, 'name')} (Text Line)"
			inner_container = TextWidget(title, text)
			container.set_inner_widget(inner_container)
			# if type(item) == Entry:
			if not mixed:
				modal = PanelModal(EditTextLine(self.lib.get_field_attr(field, 'content')), 
												title=title,
												window_title=f'Edit {self.lib.get_field_attr(field, "name")}',
												save_callback=(lambda content: (self.update_field(field, content), self.update_widgets()))
												)
				container.set_edit_callback(modal.show)
				prompt=f'Are you sure you want to remove this \"{self.lib.get_field_attr(field, "name")}\" field?'
				callback = lambda: (self.remove_field(field), self.update_widgets())
				container.set_remove_callback(lambda: self.remove_message_box(
					prompt=prompt,
					callback=callback))
				container.set_copy_callback(None)
			else:
				container.set_edit_callback(None)
				container.set_copy_callback(None)
				container.set_remove_callback(None)
			# container.set_remove_callback(lambda: (self.lib.get_entry(item.id).fields.pop(index), self.update_widgets(item)))
			
		elif self.lib.get_field_attr(field, 'type') in 'text_box':
			# logging.info(f'WRITING TEXTBOX FOR ITEM {item.id}')
			container.set_title(self.lib.get_field_attr(field, 'name'))
			# container.set_editable(True)
			container.set_inline(False)
			# Normalize line endings in any text content.
			text: str = ''
			if not mixed:
				text = self.lib.get_field_attr(
					field, 'content').replace('\r', '\n')
			else:
				text = '<i>Mixed Data</i>'
			title = f"{self.lib.get_field_attr(field, 'name')} (Text Box)"
			inner_container = TextWidget(title, text)
			container.set_inner_widget(inner_container)
			# if type(item) == Entry:
			if not mixed:
				container.set_copy_callback(None)
				modal = PanelModal(EditTextBox(self.lib.get_field_attr(field, 'content')), 
												title=title,
												window_title=f'Edit {self.lib.get_field_attr(field, "name")}',
												save_callback=(lambda content: (self.update_field(field, content), self.update_widgets()))
												)
				container.set_edit_callback(modal.show)
				prompt=f'Are you sure you want to remove this \"{self.lib.get_field_attr(field, "name")}\" field?'
				callback = lambda: (self.remove_field(field), self.update_widgets())
				container.set_remove_callback(lambda: self.remove_message_box(
					prompt=prompt,
					callback=callback))
			else:
				container.set_edit_callback(None)
				container.set_copy_callback(None)
				container.set_remove_callback(None)
		elif self.lib.get_field_attr(field, 'type') == 'collation':
			# logging.info(f'WRITING COLLATION FOR ITEM {item.id}')
			container.set_title(self.lib.get_field_attr(field, 'name'))
			# container.set_editable(True)
			container.set_inline(False)
			collation = self.lib.get_collation(self.lib.get_field_attr(field, 'content'))
			title = f"{self.lib.get_field_attr(field, 'name')} (Collation)"
			text: str = (f'{collation.title} ({len(collation.e_ids_and_pages)} Items)')
			if len(self.selected) == 1:
				text += f' - Page {collation.e_ids_and_pages[[x[0] for x in collation.e_ids_and_pages].index(self.selected[0][1])][1]}'
			inner_container = TextWidget(title, text)
			container.set_inner_widget(inner_container)
			# if type(item) == Entry:
			container.set_copy_callback(None)
			# container.set_edit_callback(None)
			# container.set_remove_callback(lambda: (self.lib.get_entry(item.id).fields.pop(index), self.update_widgets(item)))
			prompt=f'Are you sure you want to remove this \"{self.lib.get_field_attr(field, "name")}\" field?'
			callback = lambda: (self.remove_field(field), self.update_widgets())
			container.set_remove_callback(lambda: self.remove_message_box(
				prompt=prompt,
				callback=callback))
		elif self.lib.get_field_attr(field, 'type') == 'datetime':
			# logging.info(f'WRITING DATETIME FOR ITEM {item.id}')
			if not mixed:
				try:
					container.set_title(self.lib.get_field_attr(field, 'name'))
					# container.set_editable(False)
					container.set_inline(False)
					# TODO: Localize this and/or add preferences.
					date = dt.strptime(self.lib.get_field_attr(
						field, 'content'), '%Y-%m-%d %H:%M:%S')
					title = f"{self.lib.get_field_attr(field, 'name')} (Date)"
					inner_container = TextWidget(title, date.strftime('%D - %r'))
					container.set_inner_widget(inner_container)
				except:
					container.set_title(self.lib.get_field_attr(field, 'name'))
					# container.set_editable(False)
					container.set_inline(False)
					title = f"{self.lib.get_field_attr(field, 'name')} (Date) (Unknown Format)"
					inner_container = TextWidget(title, str(self.lib.get_field_attr(field, 'content')))
				# if type(item) == Entry:
				container.set_copy_callback(None)
				container.set_edit_callback(None)
				# container.set_remove_callback(lambda: (self.lib.get_entry(item.id).fields.pop(index), self.update_widgets(item)))
				prompt=f'Are you sure you want to remove this \"{self.lib.get_field_attr(field, "name")}\" field?'
				callback = lambda: (self.remove_field(field), self.update_widgets())
				container.set_remove_callback(lambda: self.remove_message_box(
					prompt=prompt,
					callback=callback))
			else:
				text = '<i>Mixed Data</i>'
				title = f"{self.lib.get_field_attr(field, 'name')} (Wacky Date)"
				inner_container = TextWidget(title, text)
				container.set_inner_widget(inner_container)
				container.set_copy_callback(None)
				container.set_edit_callback(None)
				container.set_remove_callback(None)
		else:
			# logging.info(f'[ENTRY PANEL] Unknown Type: {self.lib.get_field_attr(field, "type")}')
			container.set_title(self.lib.get_field_attr(field, 'name'))
			# container.set_editable(False)
			container.set_inline(False)
			title = f"{self.lib.get_field_attr(field, 'name')} (Unknown Field Type)"
			inner_container = TextWidget(title, str(self.lib.get_field_attr(field, 'content')))
			container.set_inner_widget(inner_container)
			# if type(item) == Entry:
			container.set_copy_callback(None)
			container.set_edit_callback(None)
			# container.set_remove_callback(lambda: (self.lib.get_entry(item.id).fields.pop(index), self.update_widgets(item)))
			prompt=f'Are you sure you want to remove this \"{self.lib.get_field_attr(field, "name")}\" field?'
			callback = lambda: (self.remove_field(field), self.update_widgets())
			# callback = lambda: (self.lib.get_entry(item.id).fields.pop(index), self.update_widgets())
			container.set_remove_callback(lambda: self.remove_message_box(
				prompt=prompt,
				callback=callback))
		container.setHidden(False)
		self.place_add_field_button()
	
	def remove_field(self, field:object):
		"""Removes a field from all selected Entries, given a field object."""
		for item_pair in self.selected:
			if item_pair[0] == ItemType.ENTRY:
				entry = self.lib.get_entry(item_pair[1])
				try:
					index = entry.fields.index(field)
					updated_badges = False
					if 8 in entry.fields[index].keys() and (1 in entry.fields[index][8] or 0 in entry.fields[index][8]):
						updated_badges = True
					# TODO: Create a proper Library/Entry method to manage fields.
					entry.fields.pop(index)
					if updated_badges:
						self.driver.update_badges()
				except ValueError:
					logging.info(f'[PREVIEW PANEL][ERROR?] Tried to remove field from Entry ({entry.id}) that never had it')
					pass
	
	def update_field(self, field:object, content):
		"""Removes a field from all selected Entries, given a field object."""
		field = dict(field)
		for item_pair in self.selected:
			if item_pair[0] == ItemType.ENTRY:
				entry = self.lib.get_entry(item_pair[1])
				try:
					logging.info(field)
					index = entry.fields.index(field)
					self.lib.update_entry_field(entry.id, index, content, 'replace')
				except ValueError:
					logging.info(f'[PREVIEW PANEL][ERROR] Tried to update field from Entry ({entry.id}) that never had it')
					pass

	def remove_message_box(self, prompt:str, callback:FunctionType) -> int:
		remove_mb = QMessageBox()
		remove_mb.setText(prompt)
		remove_mb.setWindowTitle('Remove Field')
		remove_mb.setIcon(QMessageBox.Icon.Warning)
		cancel_button = remove_mb.addButton('&Cancel', QMessageBox.ButtonRole.DestructiveRole)
		remove_button = remove_mb.addButton('&Remove', QMessageBox.ButtonRole.RejectRole)
		# remove_mb.setStandardButtons(QMessageBox.StandardButton.Cancel)
		remove_mb.setDefaultButton(cancel_button)
		result = remove_mb.exec_()
		# logging.info(result)
		if result == 1:
			callback()
	

class ItemThumb(FlowWidget):
	"""
	The thumbnail widget for a library item (Entry, Collation, Tag Group, etc.).
	"""

	update_cutoff: float = time.time()

	collation_icon_128: Image.Image = Image.open(os.path.normpath(
		f'{Path(__file__).parent.parent.parent}/resources/qt/images/collation_icon_128.png'))
	collation_icon_128.load()

	tag_group_icon_128: Image.Image = Image.open(os.path.normpath(
		f'{Path(__file__).parent.parent.parent}/resources/qt/images/tag_group_icon_128.png'))
	tag_group_icon_128.load()

	small_text_style = (
		f'background-color:rgba(0, 0, 0, 128);'
		f'font-family:Oxanium;'
		f'font-weight:bold;'
		f'font-size:12px;'
		f'border-radius:3px;'
		f'padding-top: 4px;'
		f'padding-right: 1px;'
		f'padding-bottom: 1px;'
		f'padding-left: 1px;'
	)

	med_text_style = (
		f'background-color:rgba(17, 15, 27, 192);'
		f'font-family:Oxanium;'
		f'font-weight:bold;'
		f'font-size:18px;'
		f'border-radius:3px;'
		f'padding-top: 4px;'
		f'padding-right: 1px;'
		f'padding-bottom: 1px;'
		f'padding-left: 1px;'
	)

	def __init__(self, mode: Optional[ItemType], library: Library, panel: PreviewPanel, thumb_size: tuple[int, int]):
		"""Modes: entry, collation, tag_group"""
		super().__init__()
		self.lib = library
		self.panel = panel
		self.mode = mode
		self.item_id: int = -1
		self.isFavorite: bool = False
		self.isArchived: bool = False
		self.thumb_size:tuple[int,int]= thumb_size
		self.setMinimumSize(*thumb_size)
		self.setMaximumSize(*thumb_size)
		check_size = 24
		# self.setStyleSheet('background-color:red;')

		# +----------+
		# |   ARC FAV| Top Right: Favorite & Archived Badges
		# |          |
		# |          |
		# |EXT      #| Lower Left: File Type, Tag Group Icon, or Collation Icon
		# +----------+ Lower Right: Collation Count, Video Length, or Word Count

		# Thumbnail ============================================================

		# +----------+
		# |*--------*|
		# ||        ||
		# ||        ||
		# |*--------*|
		# +----------+
		self.base_layout = QVBoxLayout(self)
		self.base_layout.setObjectName('baseLayout')
		# self.base_layout.setRowStretch(1, 2)
		self.base_layout.setContentsMargins(0, 0, 0, 0)

		# +----------+
		# |[~~~~~~~~]|
		# |          |
		# |          |
		# |          |
		# +----------+
		self.top_layout = QHBoxLayout()
		self.top_layout.setObjectName('topLayout')
		# self.top_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
		# self.top_layout.setColumnStretch(1, 2)
		self.top_layout.setContentsMargins(6, 6, 6, 6)
		self.top_container = QWidget()
		self.top_container.setLayout(self.top_layout)
		self.base_layout.addWidget(self.top_container)

		# +----------+
		# |[~~~~~~~~]|
		# |     ^    |
		# |     |    |
		# |     v    |
		# +----------+
		self.base_layout.addStretch(2)

		# +----------+
		# |[~~~~~~~~]|
		# |     ^    |
		# |     v    |
		# |[~~~~~~~~]|
		# +----------+
		self.bottom_layout = QHBoxLayout()
		self.bottom_layout.setObjectName('bottomLayout')
		# self.bottom_container.setAlignment(Qt.AlignmentFlag.AlignBottom)
		# self.bottom_layout.setColumnStretch(1, 2)
		self.bottom_layout.setContentsMargins(6, 6, 6, 6)
		self.bottom_container = QWidget()
		self.bottom_container.setLayout(self.bottom_layout)
		self.base_layout.addWidget(self.bottom_container)

		# self.root_layout = QGridLayout(self)
		# self.root_layout.setObjectName('rootLayout')
		# self.root_layout.setColumnStretch(1, 2)
		# self.root_layout.setRowStretch(1, 2)
		# self.root_layout.setContentsMargins(6,6,6,6)
		# # root_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)

		self.thumb_button = ThumbButton(self, thumb_size)
		self.renderer = ThumbRenderer()
		self.renderer.updated.connect(lambda ts, i, s, ext: (self.update_thumb(ts, image=i),
															 self.update_size(
																 ts, size=s),
															 self.set_extension(ext)))
		self.thumb_button.setFlat(True)

		# self.bg_button.setStyleSheet('background-color:blue;')
		# self.bg_button.setLayout(self.root_layout)
		self.thumb_button.setLayout(self.base_layout)
		# self.bg_button.setMinimumSize(*thumb_size)
		# self.bg_button.setMaximumSize(*thumb_size)

		# Static Badges ========================================================

		# Item Type Badge ------------------------------------------------------
		# Used for showing the Tag Group / Collation icons.
		# Mutually exclusive with the File Extension Badge.
		self.item_type_badge = QLabel()
		self.item_type_badge.setObjectName('itemBadge')
		self.item_type_badge.setPixmap(QPixmap.fromImage(ImageQt.ImageQt(
			ItemThumb.collation_icon_128.resize((check_size, check_size), Image.Resampling.BILINEAR))))
		self.item_type_badge.setMinimumSize(check_size, check_size)
		self.item_type_badge.setMaximumSize(check_size, check_size)
		# self.root_layout.addWidget(self.item_type_badge, 2, 0)
		self.bottom_layout.addWidget(self.item_type_badge)

		# File Extension Badge -------------------------------------------------
		# Mutually exclusive with the File Extension Badge.
		self.ext_badge = QLabel()
		self.ext_badge.setObjectName('extBadge')
		# self.ext_badge.setText('MP4')
		# self.ext_badge.setAlignment(Qt.AlignmentFlag.AlignVCenter)
		self.ext_badge.setStyleSheet(ItemThumb.small_text_style)
		# self.type_badge.setAlignment(Qt.AlignmentFlag.AlignRight)
		# self.root_layout.addWidget(self.ext_badge, 2, 0)
		self.bottom_layout.addWidget(self.ext_badge)
		# self.type_badge.setHidden(True)
		# bl_layout.addWidget(self.type_badge)

		self.bottom_layout.addStretch(2)

		# Count Badge ----------------------------------------------------------
		# Used for Tag Group + Collation counts, video length, word count, etc.
		self.count_badge = QLabel()
		self.count_badge.setObjectName('countBadge')
		# self.count_badge.setMaximumHeight(17)
		self.count_badge.setText('-:--')
		# self.count_badge.setAlignment(Qt.AlignmentFlag.AlignVCenter)
		self.count_badge.setStyleSheet(ItemThumb.small_text_style)
		# self.count_badge.setAlignment(Qt.AlignmentFlag.AlignBottom)
		# self.root_layout.addWidget(self.count_badge, 2, 2)
		self.bottom_layout.addWidget(
			self.count_badge, alignment=Qt.AlignmentFlag.AlignBottom)

		self.top_layout.addStretch(2)

		# Intractable Badges ===================================================
		self.cb_container = QWidget()
		# check_badges.setStyleSheet('background-color:cyan;')
		self.cb_layout = QHBoxLayout()
		self.cb_layout.setDirection(QBoxLayout.Direction.RightToLeft)
		self.cb_layout.setContentsMargins(0, 0, 0, 0)
		self.cb_layout.setSpacing(6)
		self.cb_container.setLayout(self.cb_layout)
		# self.cb_container.setHidden(True)
		# self.root_layout.addWidget(self.check_badges, 0, 2)
		self.top_layout.addWidget(self.cb_container)

		# Favorite Badge -------------------------------------------------------
		self.favorite_badge = QCheckBox()
		self.favorite_badge.setObjectName('favBadge')
		self.favorite_badge.setToolTip('Favorite')
		self.favorite_badge.setStyleSheet(f'QCheckBox::indicator{{width: {check_size}px;height: {check_size}px;}}'
										  f'QCheckBox::indicator::unchecked{{image: url(:/images/star_icon_empty_128.png)}}'
										  f'QCheckBox::indicator::checked{{image: url(:/images/star_icon_filled_128.png)}}'
										  #  f'QCheckBox{{background-color:yellow;}}'
										  )
		self.favorite_badge.setMinimumSize(check_size, check_size)
		self.favorite_badge.setMaximumSize(check_size, check_size)
		self.favorite_badge.stateChanged.connect(
			lambda x=self.favorite_badge.isChecked(): self.on_favorite_check(bool(x)))

		# self.fav_badge.setContentsMargins(0,0,0,0)
		# tr_layout.addWidget(self.fav_badge)
		# root_layout.addWidget(self.fav_badge, 0, 2)
		self.cb_layout.addWidget(self.favorite_badge)
		self.favorite_badge.setHidden(True)

		# Archive Badge --------------------------------------------------------
		self.archived_badge = QCheckBox()
		self.archived_badge.setObjectName('archiveBadge')
		self.archived_badge.setToolTip('Archive')
		self.archived_badge.setStyleSheet(f'QCheckBox::indicator{{width: {check_size}px;height: {check_size}px;}}'
										  f'QCheckBox::indicator::unchecked{{image: url(:/images/box_icon_empty_128.png)}}'
										  f'QCheckBox::indicator::checked{{image: url(:/images/box_icon_filled_128.png)}}'
										  #  f'QCheckBox{{background-color:red;}}'
										  )
		self.archived_badge.setMinimumSize(check_size, check_size)
		self.archived_badge.setMaximumSize(check_size, check_size)
		# self.archived_badge.clicked.connect(lambda x: self.assign_archived(x))
		self.archived_badge.stateChanged.connect(
			lambda x=self.archived_badge.isChecked(): self.on_archived_check(bool(x)))

		# tr_layout.addWidget(self.archive_badge)
		self.cb_layout.addWidget(self.archived_badge)
		self.archived_badge.setHidden(True)
		# root_layout.addWidget(self.archive_badge, 0, 2)
		# self.dumpObjectTree()

		self.set_mode(mode)

	def set_mode(self, mode: Optional[ItemType]) -> None:
		if mode is None:
			self.unsetCursor()
			self.thumb_button.setHidden(True)
			# self.check_badges.setHidden(True)
			# self.ext_badge.setHidden(True)
			# self.item_type_badge.setHidden(True)
			pass
		elif mode == ItemType.ENTRY and self.mode != ItemType.ENTRY:
			self.setCursor(Qt.CursorShape.PointingHandCursor)
			self.thumb_button.setHidden(False)
			self.cb_container.setHidden(False)
			# Count Badge depends on file extension (video length, word count)
			self.item_type_badge.setHidden(True)
			self.count_badge.setStyleSheet(ItemThumb.small_text_style)
			self.count_badge.setHidden(True)
			self.ext_badge.setHidden(True)
		elif mode == ItemType.COLLATION and self.mode != ItemType.COLLATION:
			self.setCursor(Qt.CursorShape.PointingHandCursor)
			self.thumb_button.setHidden(False)
			self.cb_container.setHidden(True)
			self.ext_badge.setHidden(True)
			self.count_badge.setStyleSheet(ItemThumb.med_text_style)
			self.count_badge.setHidden(False)
			self.item_type_badge.setHidden(False)
		elif mode == ItemType.TAG_GROUP and self.mode != ItemType.TAG_GROUP:
			self.setCursor(Qt.CursorShape.PointingHandCursor)
			self.thumb_button.setHidden(False)
			# self.cb_container.setHidden(True)
			self.ext_badge.setHidden(True)
			self.count_badge.setHidden(False)
			self.item_type_badge.setHidden(False)
		self.mode = mode
		# logging.info(f'Set Mode To: {self.mode}')

	# def update_(self, thumb: QPixmap, size:QSize, ext:str, badges:list[QPixmap]) -> None:
	# 	"""Updates the ItemThumb's visuals."""
	# 	if thumb:
	# 		pass

	def set_extension(self, ext: str) -> None:
		if ext and ext not in IMAGE_TYPES or ext in ['gif', 'apng']:
			self.ext_badge.setHidden(False)
			self.ext_badge.setText(ext.upper())
			if ext in VIDEO_TYPES + AUDIO_TYPES:
				self.count_badge.setHidden(False)
		else:
			if self.mode == ItemType.ENTRY:
				self.ext_badge.setHidden(True)
				self.count_badge.setHidden(True)

	def set_count(self, count: str) -> None:
		if count:
			self.count_badge.setHidden(False)
			self.count_badge.setText(count)
		else:
			if self.mode == ItemType.ENTRY:
				self.ext_badge.setHidden(True)
				self.count_badge.setHidden(True)

	def update_thumb(self, timestamp: float, image: QPixmap = None):
		"""Updates attributes of a thumbnail element."""
		# logging.info(f'[GUI] Updating Thumbnail for element {id(element)}: {id(image) if image else None}')
		if timestamp > ItemThumb.update_cutoff:
			self.thumb_button.setIcon(image if image else QPixmap())
			# element.repaint()

	def update_size(self, timestamp: float, size: QSize):
		"""Updates attributes of a thumbnail element."""
		# logging.info(f'[GUI] Updating size for element {id(element)}:  {size.__str__()}')
		if timestamp > ItemThumb.update_cutoff:
			if self.thumb_button.iconSize != size:
				self.thumb_button.setIconSize(size)
				self.thumb_button.setMinimumSize(size)
				self.thumb_button.setMaximumSize(size)

	def update_clickable(self, clickable: FunctionType = None):
		"""Updates attributes of a thumbnail element."""
		# logging.info(f'[GUI] Updating Click Event for element {id(element)}: {id(clickable) if clickable else None}')
		try:
			self.thumb_button.clicked.disconnect()
		except RuntimeError:
			pass
		if clickable:
			self.thumb_button.clicked.connect(clickable)
	
	def update_badges(self):
		if self.mode == ItemType.ENTRY:
			# logging.info(f'[UPDATE BADGES] ENTRY: {self.lib.get_entry(self.item_id)}')
			# logging.info(f'[UPDATE BADGES] ARCH: {self.lib.get_entry(self.item_id).has_tag(self.lib, 0)}, FAV: {self.lib.get_entry(self.item_id).has_tag(self.lib, 1)}')
			self.assign_archived(self.lib.get_entry(self.item_id).has_tag(self.lib, 0))
			self.assign_favorite(self.lib.get_entry(self.item_id).has_tag(self.lib, 1))


	def set_item_id(self, id: int):
		self.item_id = id

	def assign_favorite(self, value: bool):
		# Switching mode to None to bypass mode-specific operations when the
		# checkbox's state changes.
		mode = self.mode
		self.mode = None
		self.isFavorite = value
		self.favorite_badge.setChecked(value)
		if not self.thumb_button.underMouse():
			self.favorite_badge.setHidden(not self.isFavorite)
		self.mode = mode

	def assign_archived(self, value: bool):
		# Switching mode to None to bypass mode-specific operations when the
		# checkbox's state changes.
		mode = self.mode
		self.mode = None
		self.isArchived = value
		self.archived_badge.setChecked(value)
		if not self.thumb_button.underMouse():
			self.archived_badge.setHidden(not self.isArchived)
		self.mode = mode

	def show_check_badges(self, show: bool):
		if self.mode != ItemType.TAG_GROUP:
			self.favorite_badge.setHidden(
				True if (not show and not self.isFavorite) else False)
			self.archived_badge.setHidden(
				True if (not show and not self.isArchived) else False)

	def enterEvent(self, event: QEnterEvent) -> None:
		self.show_check_badges(True)
		return super().enterEvent(event)

	def leaveEvent(self, event: QEvent) -> None:
		self.show_check_badges(False)
		return super().leaveEvent(event)

	def on_archived_check(self, value: bool):
		# logging.info(f'Archived Check: {value}, Mode: {self.mode}')
		if self.mode == ItemType.ENTRY:
			self.isArchived = value
			DEFAULT_META_TAG_FIELD = 8
			temp = (ItemType.ENTRY,self.item_id)
			if list(self.panel.driver.selected).count(temp) > 0: # Is the archived badge apart of the selection?
				# Yes, then add archived tag to all selected.
				for x in self.panel.driver.selected:
					e = self.lib.get_entry(x[1])
					if value:
						self.archived_badge.setHidden(False)
						e.add_tag(self.panel.driver.lib, 0, field_id=DEFAULT_META_TAG_FIELD, field_index=-1)
					else:
						e.remove_tag(self.panel.driver.lib, 0)
			else:
				# No, then add archived tag to the entry this badge is on.
				e = self.lib.get_entry(self.item_id)
				if value:
					self.favorite_badge.setHidden(False)
					e.add_tag(self.panel.driver.lib, 0, field_id=DEFAULT_META_TAG_FIELD, field_index=-1)
				else:
					e.remove_tag(self.panel.driver.lib, 0)
			if self.panel.isOpen:
				self.panel.update_widgets()
			self.panel.driver.update_badges()


	# def on_archived_uncheck(self):
	# 	if self.mode == SearchItemType.ENTRY:
	# 		self.isArchived = False
	# 		e = self.lib.get_entry(self.item_id)

	def on_favorite_check(self, value: bool):
		# logging.info(f'Favorite Check: {value}, Mode: {self.mode}')
		if self.mode == ItemType.ENTRY:
			self.isFavorite = value
			DEFAULT_META_TAG_FIELD = 8
			temp = (ItemType.ENTRY,self.item_id)
			if list(self.panel.driver.selected).count(temp) > 0: # Is the favorite badge apart of the selection?
				# Yes, then add favorite tag to all selected.
				for x in self.panel.driver.selected:
					e = self.lib.get_entry(x[1])
					if value:
						self.favorite_badge.setHidden(False)
						e.add_tag(self.panel.driver.lib, 1, field_id=DEFAULT_META_TAG_FIELD, field_index=-1)
					else:
						e.remove_tag(self.panel.driver.lib, 1)
			else:
				# No, then add favorite tag to the entry this badge is on.
				e = self.lib.get_entry(self.item_id)
				if value:
					self.favorite_badge.setHidden(False)
					e.add_tag(self.panel.driver.lib, 1, field_id=DEFAULT_META_TAG_FIELD, field_index=-1)
				else:
					e.remove_tag(self.panel.driver.lib, 1)
			if self.panel.isOpen:
				self.panel.update_widgets()
			self.panel.driver.update_badges()
				

	# def on_favorite_uncheck(self):
	# 	if self.mode == SearchItemType.ENTRY:
	# 		self.isFavorite = False
	# 		e = self.lib.get_entry(self.item_id)
	# 		e.remove_tag(1)

class ThumbButton(QPushButton):
	def __init__(self, parent:QWidget, thumb_size:tuple[int,int]) -> None:
		super().__init__(parent)
		self.thumb_size:tuple[int,int] = thumb_size
		self.hovered = False
		self.selected = False

		# self.clicked.connect(lambda checked: self.set_selected(True))
	
	def paintEvent(self, event:QEvent) -> None:
		super().paintEvent(event)
		if self.hovered or self.selected:
			painter = QPainter()
			painter.begin(self)
			painter.setRenderHint(QPainter.RenderHint.Antialiasing)
			# painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
			path = QPainterPath()
			width = 3
			radius = 6
			path.addRoundedRect(QtCore.QRectF(width/2,width/2,self.thumb_size[0]-width, self.thumb_size[1]-width), radius, radius)

			# color = QColor('#bb4ff0') if self.selected else QColor('#55bbf6')
			# pen = QPen(color, width)
			# painter.setPen(pen)
			# # brush.setColor(fill)
			# painter.drawPath(path)

			if self.selected:
				painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_HardLight)
				color = QColor('#bb4ff0')
				color.setAlphaF(0.5)
				pen = QPen(color, width)
				painter.setPen(pen)
				painter.fillPath(path, color)
				painter.drawPath(path)

				painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
				color = QColor('#bb4ff0') if not self.hovered else QColor('#55bbf6')
				pen = QPen(color, width)
				painter.setPen(pen)
				painter.drawPath(path)
			elif self.hovered:
				painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
				color = QColor('#55bbf6')
				pen = QPen(color, width)
				painter.setPen(pen)
				painter.drawPath(path)
			painter.end()
	
	def enterEvent(self, event: QEnterEvent) -> None:
		self.hovered = True
		self.repaint()
		return super().enterEvent(event)

	def leaveEvent(self, event: QEvent) -> None:
		self.hovered = False
		self.repaint()
		return super().leaveEvent(event)

	def set_selected(self, value:bool) -> None:
		self.selected = value
		self.repaint()

class CollageIconRenderer(QObject):
	rendered = Signal(Image.Image)
	done = Signal()

	def __init__(self, library:Library):
		QObject.__init__(self)
		self.lib = library
	
	def render(self, entry_id, size:tuple[int,int], data_tint_mode, data_only_mode, keep_aspect):
		entry = self.lib.get_entry(entry_id)
		filepath = os.path.normpath(f'{self.lib.library_dir}/{entry.path}/{entry.filename}')
		file_type = os.path.splitext(filepath)[1].lower()[1:]
		color: str = ''

		try:
			if data_tint_mode or data_only_mode:
				color = '#000000' # Black (Default)
				
				if entry.fields:
					has_any_tags:bool = False
					has_content_tags:bool = False
					has_meta_tags:bool = False
					for field in entry.fields:
						if self.lib.get_field_attr(field, 'type') == 'tag_box':
							if self.lib.get_field_attr(field, 'content'):
								has_any_tags = True
								if self.lib.get_field_attr(field, 'id') == 7:
									has_content_tags = True
								elif self.lib.get_field_attr(field, 'id') == 8:
									has_meta_tags = True
					if has_content_tags and has_meta_tags:
						color = '#28bb48' # Green
					elif has_any_tags:
						color = '#ffd63d' # Yellow
						# color = '#95e345' # Yellow-Green
					else:
						# color = '#fa9a2c' # Yellow-Orange
						color = '#ed8022' # Orange
				else:
					color = '#e22c3c' # Red

				if data_only_mode:
					pic: Image = Image.new('RGB', size, color)
					# collage.paste(pic, (y*thumb_size, x*thumb_size))
					self.rendered.emit(pic)
			if not data_only_mode:
				logging.info(f'\r{INFO} Combining [ID:{entry_id}/{len(self.lib.entries)}]: {self.get_file_color(file_type)}{entry.path}{os.sep}{entry.filename}\033[0m')
				# sys.stdout.write(f'\r{INFO} Combining [{i+1}/{len(self.lib.entries)}]: {self.get_file_color(file_type)}{entry.path}{os.sep}{entry.filename}{RESET}')
				# sys.stdout.flush()
				if file_type in IMAGE_TYPES:
					with Image.open(os.path.normpath(f'{self.lib.library_dir}/{entry.path}/{entry.filename}')) as pic:
						if keep_aspect:
							pic.thumbnail(size)
						else:
							pic = pic.resize(size)
						if data_tint_mode and color:
							pic = pic.convert(mode='RGB')
							pic = ImageChops.hard_light(pic, Image.new('RGB', size, color))
						# collage.paste(pic, (y*thumb_size, x*thumb_size))
						self.rendered.emit(pic)
				elif file_type in VIDEO_TYPES:
					video = cv2.VideoCapture(filepath)
					video.set(cv2.CAP_PROP_POS_FRAMES,
							(video.get(cv2.CAP_PROP_FRAME_COUNT) // 2))
					success, frame = video.read()
					if not success:
						# Depending on the video format, compression, and frame
						# count, seeking halfway does not work and the thumb
						# must be pulled from the earliest available frame.
						video.set(cv2.CAP_PROP_POS_FRAMES, 0)
						success, frame = video.read()
					frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
					with Image.fromarray(frame, mode='RGB') as pic:
						if keep_aspect:
							pic.thumbnail(size)
						else:
							pic = pic.resize(size)
						if data_tint_mode and color:
							pic = ImageChops.hard_light(pic, Image.new('RGB', size, color))
						# collage.paste(pic, (y*thumb_size, x*thumb_size))
						self.rendered.emit(pic)
		except (UnidentifiedImageError, FileNotFoundError):
			logging.info(f'\n{ERROR} Couldn\'t read {entry.path}{os.sep}{entry.filename}')
			with Image.open(os.path.normpath(f'{Path(__file__).parent.parent.parent}/resources/qt/images/thumb_broken_512.png')) as pic:
				pic.thumbnail(size)
				if data_tint_mode and color:
					pic = pic.convert(mode='RGB')
					pic = ImageChops.hard_light(pic, Image.new('RGB', size, color))
				# collage.paste(pic, (y*thumb_size, x*thumb_size))
				self.rendered.emit(pic)
		except KeyboardInterrupt:
			# self.quit(save=False, backup=True)
			run = False
			# clear()
			logging.info('\n')
			logging.info(f'{INFO} Collage operation cancelled.')
			clear_scr=False
		except:
			logging.info(f'{ERROR} {entry.path}{os.sep}{entry.filename}')
			traceback.print_exc()
			logging.info('Continuing...')
		
		self.done.emit()
		# logging.info('Done!')
	
	def get_file_color(self, ext: str):
		if ext.lower().replace('.','',1) == 'gif':
			return '\033[93m'
		if ext.lower().replace('.','',1) in IMAGE_TYPES:
			return '\033[37m'
		elif ext.lower().replace('.','',1) in VIDEO_TYPES:
			return '\033[96m'
		elif ext.lower().replace('.','',1) in TEXT_TYPES:
			return '\033[92m'
		else:
			return '\033[97m'

class ThumbRenderer(QObject):
	# finished = Signal()
	updated = Signal(float, QPixmap, QSize, str)
	updated_ratio = Signal(float)
	# updatedImage = Signal(QPixmap)
	# updatedSize = Signal(QSize)

	thumb_mask_512: Image.Image = Image.open(os.path.normpath(
		f'{Path(__file__).parent.parent.parent}/resources/qt/images/thumb_mask_512.png'))
	thumb_mask_512.load()

	thumb_mask_hl_512: Image.Image = Image.open(os.path.normpath(
		f'{Path(__file__).parent.parent.parent}/resources/qt/images/thumb_mask_hl_512.png'))
	thumb_mask_hl_512.load()

	thumb_loading_512: Image.Image = Image.open(os.path.normpath(
		f'{Path(__file__).parent.parent.parent}/resources/qt/images/thumb_loading_512.png'))
	thumb_loading_512.load()

	thumb_broken_512: Image.Image = Image.open(os.path.normpath(
		f'{Path(__file__).parent.parent.parent}/resources/qt/images/thumb_broken_512.png'))
	thumb_broken_512.load()

	# thumb_debug: Image.Image = Image.open(os.path.normpath(
	# 	f'{Path(__file__).parent.parent.parent}/resources/qt/images/temp.jpg'))
	# thumb_debug.load()

	# TODO: Make dynamic font sized given different pixel ratios
	font_pixel_ratio: float = 1
	ext_font = ImageFont.truetype(os.path.normpath(
		f'{Path(__file__).parent.parent.parent}/resources/qt/fonts/Oxanium-Bold.ttf'), math.floor(12*font_pixel_ratio))

	def __init__(self):
		QObject.__init__(self)

	def render(self, timestamp: float, filepath, base_size: tuple[int, int], pixelRatio: float, isLoading=False):
		"""Renders an entry/element thumbnail for the GUI."""
		adj_size: int = 1
		image = None
		pixmap = None
		final = None
		extension: str = None
		broken_thumb = False
		# adj_font_size = math.floor(12 * pixelRatio)
		if ThumbRenderer.font_pixel_ratio != pixelRatio:
			ThumbRenderer.font_pixel_ratio = pixelRatio
			ThumbRenderer.ext_font = ImageFont.truetype(os.path.normpath(
				f'{Path(__file__).parent.parent.parent}/resources/qt/fonts/Oxanium-Bold.ttf'), math.floor(12*ThumbRenderer.font_pixel_ratio))

		if isLoading or filepath:
			adj_size = math.ceil(base_size[0] * pixelRatio)

		if isLoading:
			li: Image.Image = ThumbRenderer.thumb_loading_512.resize(
				(adj_size, adj_size), resample=Image.Resampling.BILINEAR)
			qim = ImageQt.ImageQt(li)
			pixmap = QPixmap.fromImage(qim)
			pixmap.setDevicePixelRatio(pixelRatio)
		elif filepath:
			mask: Image.Image = ThumbRenderer.thumb_mask_512.resize(
				(adj_size, adj_size), resample=Image.Resampling.BILINEAR).getchannel(3)
			hl: Image.Image = ThumbRenderer.thumb_mask_hl_512.resize(
				(adj_size, adj_size), resample=Image.Resampling.BILINEAR)

			extension = os.path.splitext(filepath)[1][1:].lower()

			try:
				if extension in IMAGE_TYPES:
					image = Image.open(filepath)
					# image = self.thumb_debug
					if image.mode == 'RGBA':
						# logging.info(image.getchannel(3).tobytes())
						new_bg = Image.new('RGB', image.size, color='#222222')
						new_bg.paste(image, mask=image.getchannel(3))
						image = new_bg
					if image.mode != 'RGB':
						image = image.convert(mode='RGB')
						# raise ValueError
				# except (UnidentifiedImageError, FileNotFoundError):
				# 	image = Image.open(os.path.normpath(f'{Path(__file__).parent.parent.parent}/resources/cli/images/no_preview.png'))
				# image.thumbnail((adj_size,adj_size))

				elif extension in VIDEO_TYPES:
					video = cv2.VideoCapture(filepath)
					video.set(cv2.CAP_PROP_POS_FRAMES,
							  (video.get(cv2.CAP_PROP_FRAME_COUNT) // 2))
					success, frame = video.read()
					if not success:
						# Depending on the video format, compression, and frame
						# count, seeking halfway does not work and the thumb
						# must be pulled from the earliest available frame.
						video.set(cv2.CAP_PROP_POS_FRAMES, 0)
						success, frame = video.read()
					frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
					image = Image.fromarray(frame)
			
				# TODO: Create placeholder thumbnails for non-media files.
				# else:
				# 	image: Image.Image = ThumbRenderer.thumb_loading_512.resize(
				# 		(adj_size, adj_size), resample=Image.Resampling.BILINEAR)

				if not image:
					raise UnidentifiedImageError

				orig_x, orig_y = image.size
				new_x, new_y = (adj_size, adj_size)
				
				if orig_x > orig_y:
					new_x = adj_size
					new_y = math.ceil(adj_size * (orig_y / orig_x))
				elif orig_y > orig_x:
					new_y = adj_size
					new_x = math.ceil(adj_size * (orig_x / orig_y))

				img_ratio = new_x / new_y
				# logging.info(f'[TR] {(new_x / new_y)}')
				# self.updated_ratio.emit(new_x / new_y)
				image = image.resize(
					(new_x, new_y), resample=Image.Resampling.BILINEAR)

				if image.size != (adj_size, adj_size):
					# Old 1 color method.
					# bg_col = image.copy().resize((1, 1)).getpixel((0,0))
					# bg = Image.new(mode='RGB',size=(adj_size,adj_size),color=bg_col)
					# bg.thumbnail((1, 1))
					# bg = bg.resize((adj_size,adj_size), resample=Image.Resampling.NEAREST)

					# Small gradient background. Looks decent, and is only a one-liner.
					# bg = image.copy().resize((2, 2), resample=Image.Resampling.BILINEAR).resize((adj_size,adj_size),resample=Image.Resampling.BILINEAR)

					# Four-Corner Gradient Background.
					# Not exactly a one-liner, but it's (subjectively) really cool.
					tl = image.getpixel((0, 0))
					tr = image.getpixel(((image.size[0]-1), 0))
					bl = image.getpixel((0, (image.size[1]-1)))
					br = image.getpixel(((image.size[0]-1), (image.size[1]-1)))
					bg = Image.new(mode='RGB', size=(2, 2))
					bg.paste(tl, (0, 0, 2, 2))
					bg.paste(tr, (1, 0, 2, 2))
					bg.paste(bl, (0, 1, 2, 2))
					bg.paste(br, (1, 1, 2, 2))
					bg = bg.resize((adj_size, adj_size),
								   resample=Image.Resampling.BICUBIC)

					bg.paste(image, box=(
							(adj_size-image.size[0])//2, (adj_size-image.size[1])//2))

					bg.putalpha(mask)
					final = bg

				else:
					image.putalpha(mask)
					final = image

				hl_soft = hl.copy()
				hl_soft.putalpha(ImageEnhance.Brightness(
					hl.getchannel(3)).enhance(.5))
				final.paste(ImageChops.soft_light(final, hl_soft),
							mask=hl_soft.getchannel(3))

				# hl_add = hl.copy()
				# hl_add.putalpha(ImageEnhance.Brightness(hl.getchannel(3)).enhance(.25))
				# final.paste(hl_add, mask=hl_add.getchannel(3))

			except (UnidentifiedImageError, FileNotFoundError, cv2.error):
				broken_thumb = True
				final = ThumbRenderer.thumb_broken_512.resize(
					(adj_size, adj_size), resample=Image.Resampling.BILINEAR)

			# if file_type in VIDEO_TYPES + ['gif', 'apng'] or broken_thumb:
			# 	idk = ImageDraw.Draw(final)
			# 	# idk.textlength(file_type)
			# 	ext_offset_x = idk.textlength(
			# 		text=file_type.upper(), font=ThumbRenderer.ext_font) / 2
			# 	ext_offset_x = math.floor(ext_offset_x * (1/pixelRatio))
			# 	x_margin = math.floor(
			# 		(adj_size-((base_size[0]//6)+ext_offset_x) * pixelRatio))
			# 	y_margin = math.floor(
			# 		(adj_size-((base_size[0]//8)) * pixelRatio))
			# 	stroke_width = round(2 * pixelRatio)
			# 	fill = 'white' if not broken_thumb else '#E32B41'
			# 	idk.text((x_margin, y_margin), file_type.upper(
			# 	), fill=fill, font=ThumbRenderer.ext_font, stroke_width=stroke_width, stroke_fill=(0, 0, 0))

			qim = ImageQt.ImageQt(final)
			if image:
				image.close()
			pixmap = QPixmap.fromImage(qim)
			pixmap.setDevicePixelRatio(pixelRatio)

		if pixmap:
			self.updated.emit(timestamp, pixmap, QSize(*base_size), extension)

		else:
			self.updated.emit(timestamp, QPixmap(),
							  QSize(*base_size), extension)

	def render_big(self, timestamp: float, filepath, base_size: tuple[int, int], pixelRatio: float, isLoading=False):
		"""Renders a large, non-square entry/element thumbnail for the GUI."""
		adj_size: int = 1
		image: Image.Image = None
		pixmap: QPixmap = None
		final: Image.Image = None
		extension: str = None
		broken_thumb = False
		img_ratio = 1
		# adj_font_size = math.floor(12 * pixelRatio)
		if ThumbRenderer.font_pixel_ratio != pixelRatio:
			ThumbRenderer.font_pixel_ratio = pixelRatio
			ThumbRenderer.ext_font = ImageFont.truetype(os.path.normpath(
				f'{Path(__file__).parent.parent.parent}/resources/qt/fonts/Oxanium-Bold.ttf'), math.floor(12*ThumbRenderer.font_pixel_ratio))

		if isLoading or filepath:
			adj_size = math.ceil(max(base_size[0], base_size[1]) * pixelRatio)

		if isLoading:
			adj_size = math.ceil((512 * pixelRatio))
			final: Image.Image = ThumbRenderer.thumb_loading_512.resize(
				(adj_size, adj_size), resample=Image.Resampling.BILINEAR)
			qim = ImageQt.ImageQt(final)
			pixmap = QPixmap.fromImage(qim)
			pixmap.setDevicePixelRatio(pixelRatio)
			self.updated_ratio.emit(1)
			
		elif filepath:
			# mask: Image.Image = ThumbRenderer.thumb_mask_512.resize(
			# 	(adj_size, adj_size), resample=Image.Resampling.BILINEAR).getchannel(3)
			# hl: Image.Image = ThumbRenderer.thumb_mask_hl_512.resize(
			# 	(adj_size, adj_size), resample=Image.Resampling.BILINEAR)

			extension = os.path.splitext(filepath)[1][1:].lower()

			try:
				if extension in IMAGE_TYPES:
					image = Image.open(filepath)
					# image = self.thumb_debug
					if image.mode == 'RGBA':
						# logging.info(image.getchannel(3).tobytes())
						new_bg = Image.new('RGB', image.size, color='#222222')
						new_bg.paste(image, mask=image.getchannel(3))
						image = new_bg
					if image.mode != 'RGB':
						image = image.convert(mode='RGB')
						# raise ValueError
				# except (UnidentifiedImageError, FileNotFoundError):
				# 	image = Image.open(os.path.normpath(f'{Path(__file__).parent.parent.parent}/resources/cli/images/no_preview.png'))
				# image.thumbnail((adj_size,adj_size))

				elif extension in VIDEO_TYPES:
					video = cv2.VideoCapture(filepath)
					video.set(cv2.CAP_PROP_POS_FRAMES,
							  (video.get(cv2.CAP_PROP_FRAME_COUNT) // 2))
					success, frame = video.read()
					if not success:
						# Depending on the video format, compression, and frame
						# count, seeking halfway does not work and the thumb
						# must be pulled from the earliest available frame.
						video.set(cv2.CAP_PROP_POS_FRAMES, 0)
						success, frame = video.read()
					frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
					image = Image.fromarray(frame)

				if not image:
					raise UnidentifiedImageError

				orig_x, orig_y = image.size
				if orig_x < adj_size and orig_y < adj_size:
					new_x, new_y = (adj_size, adj_size)
					if orig_x > orig_y:
						new_x = adj_size
						new_y = math.ceil(adj_size * (orig_y / orig_x))
					elif orig_y > orig_x:
						new_y = adj_size
						new_x = math.ceil(adj_size * (orig_x / orig_y))
				else:
					new_x, new_y = (adj_size, adj_size)
					if orig_x > orig_y:
						new_x = adj_size
						new_y = math.ceil(adj_size * (orig_y / orig_x))
					elif orig_y > orig_x:
						new_y = adj_size
						new_x = math.ceil(adj_size * (orig_x / orig_y))

				self.updated_ratio.emit(new_x / new_y)
				image = image.resize(
					(new_x, new_y), resample=Image.Resampling.BILINEAR)

				# image = image.resize(
				# 	(new_x, new_y), resample=Image.Resampling.BILINEAR)

				# if image.size != (adj_size, adj_size):
				# 	# Old 1 color method.
				# 	# bg_col = image.copy().resize((1, 1)).getpixel((0,0))
				# 	# bg = Image.new(mode='RGB',size=(adj_size,adj_size),color=bg_col)
				# 	# bg.thumbnail((1, 1))
				# 	# bg = bg.resize((adj_size,adj_size), resample=Image.Resampling.NEAREST)

				# 	# Small gradient background. Looks decent, and is only a one-liner.
				# 	# bg = image.copy().resize((2, 2), resample=Image.Resampling.BILINEAR).resize((adj_size,adj_size),resample=Image.Resampling.BILINEAR)

				# 	# Four-Corner Gradient Background.
				# 	# Not exactly a one-liner, but it's (subjectively) really cool.
				# 	tl = image.getpixel((0, 0))
				# 	tr = image.getpixel(((image.size[0]-1), 0))
				# 	bl = image.getpixel((0, (image.size[1]-1)))
				# 	br = image.getpixel(((image.size[0]-1), (image.size[1]-1)))
				# 	bg = Image.new(mode='RGB', size=(2, 2))
				# 	bg.paste(tl, (0, 0, 2, 2))
				# 	bg.paste(tr, (1, 0, 2, 2))
				# 	bg.paste(bl, (0, 1, 2, 2))
				# 	bg.paste(br, (1, 1, 2, 2))
				# 	bg = bg.resize((adj_size, adj_size),
				# 				   resample=Image.Resampling.BICUBIC)

				# 	bg.paste(image, box=(
				# 		(adj_size-image.size[0])//2, (adj_size-image.size[1])//2))

				# 	bg.putalpha(mask)
				# 	final = bg

				# else:
				# 	image.putalpha(mask)
				# 	final = image

				# hl_soft = hl.copy()
				# hl_soft.putalpha(ImageEnhance.Brightness(
				# 	hl.getchannel(3)).enhance(.5))
				# final.paste(ImageChops.soft_light(final, hl_soft),
				# 			mask=hl_soft.getchannel(3))

				# hl_add = hl.copy()
				# hl_add.putalpha(ImageEnhance.Brightness(hl.getchannel(3)).enhance(.25))
				# final.paste(hl_add, mask=hl_add.getchannel(3))
				scalar = 4
				rec: Image.Image = Image.new('RGB', tuple(
					[d * scalar for d in image.size]), 'black')
				draw = ImageDraw.Draw(rec)
				draw.rounded_rectangle(
					(0, 0)+rec.size, (base_size[0]//32) * scalar * pixelRatio, fill='red')
				rec = rec.resize(
					tuple([d // scalar for d in rec.size]), resample=Image.Resampling.BILINEAR)
				# final = image
				final = Image.new('RGBA', image.size, (0, 0, 0, 0))
				# logging.info(rec.size)
				# logging.info(image.size)
				final.paste(image, mask=rec.getchannel(0))

			except (UnidentifiedImageError, FileNotFoundError, cv2.error):
				broken_thumb = True
				self.updated_ratio.emit(1)
				final = ThumbRenderer.thumb_broken_512.resize(
					(adj_size, adj_size), resample=Image.Resampling.BILINEAR)

			# if extension in VIDEO_TYPES + ['gif', 'apng'] or broken_thumb:
			# 	idk = ImageDraw.Draw(final)
			# 	# idk.textlength(file_type)
			# 	ext_offset_x = idk.textlength(
			# 		text=extension.upper(), font=ThumbRenderer.ext_font) / 2
			# 	ext_offset_x = math.floor(ext_offset_x * (1/pixelRatio))
			# 	x_margin = math.floor(
			# 		(adj_size-((base_size[0]//6)+ext_offset_x) * pixelRatio))
			# 	y_margin = math.floor(
			# 		(adj_size-((base_size[0]//8)) * pixelRatio))
			# 	stroke_width = round(2 * pixelRatio)
			# 	fill = 'white' if not broken_thumb else '#E32B41'
			# 	idk.text((x_margin, y_margin), extension.upper(
			# 	), fill=fill, font=ThumbRenderer.ext_font, stroke_width=stroke_width, stroke_fill=(0, 0, 0))

			qim = ImageQt.ImageQt(final)
			if image:
				image.close()
			pixmap = QPixmap.fromImage(qim)
			pixmap.setDevicePixelRatio(pixelRatio)

		if pixmap:
			# logging.info(final.size)
			# self.updated.emit(pixmap, QSize(*final.size))
			self.updated.emit(timestamp, pixmap, QSize(math.ceil(
				adj_size * 1/pixelRatio), math.ceil(final.size[1] * 1/pixelRatio)), extension)

		else:
			self.updated.emit(timestamp, QPixmap(),
							  QSize(*base_size), extension)

class CustomRunnable(QRunnable, QObject):
	done = Signal()
	def __init__(self, function) -> None:
		QRunnable.__init__(self)
		QObject.__init__(self)
		self.function = function
	
	def run(self):
		self.function()
		self.done.emit()

class QtDriver(QObject):
	"""A Qt GUI frontend driver for TagStudio."""

	SIGTERM = Signal()

	def __init__(self, core, args):
		super().__init__()
		self.core: TagStudioCore = core
		self.lib = self.core.lib
		self.args = args

		# self.main_window = None
		# self.main_window = Ui_MainWindow()

		self.branch: str = (' ('+VERSION_BRANCH +
							')') if VERSION_BRANCH else ''
		self.base_title: str = f'TagStudio {VERSION}{self.branch}'
		# self.title_text: str = self.base_title
		# self.buffer = {}
		self.thumb_job_queue: Queue = Queue()
		self.thumb_threads = []
		self.thumb_cutoff: float = time.time()
		# self.selected: list[tuple[int,int]] = [] # (Thumb Index, Page Index)
		self.selected: list[tuple[ItemType,int]] = [] # (Item Type, Item ID)

		self.SIGTERM.connect(self.handleSIGTERM)

		self.settings = QSettings(QSettings.IniFormat, QSettings.UserScope, 'tagstudio', 'TagStudio')


		max_threads = os.cpu_count()
		for i in range(max_threads):
			# thread = threading.Thread(target=self.consumer, name=f'ThumbRenderer_{i}',args=(), daemon=True)
			# thread.start()
			thread = Consumer(self.thumb_job_queue)
			thread.setObjectName(f'ThumbRenderer_{i}')
			self.thumb_threads.append(thread)
			thread.start()
	
	def open_library_from_dialog(self):
		dir = QFileDialog.getExistingDirectory(None, 
												'Open/Create Library',
												'/', 
												QFileDialog.ShowDirsOnly)
		if dir != None and dir != '':
			self.open_library(dir)

	def signal_handler(self, sig, frame):
		if sig in (SIGINT, SIGTERM, SIGQUIT):
			self.SIGTERM.emit()
	
	def setup_signals(self):
		signal(SIGINT, self.signal_handler)
		signal(SIGTERM, self.signal_handler)
		signal(SIGQUIT, self.signal_handler)

	def start(self):
		"""Launches the main Qt window."""

		loader = QUiLoader()
		if os.name == 'nt':
			sys.argv += ['-platform', 'windows:darkmode=2']
		app = QApplication(sys.argv)
		app.setStyle('Fusion')
		# pal: QPalette = app.palette()
		# pal.setColor(QPalette.ColorGroup.Active,
		# 			 QPalette.ColorRole.Highlight, QColor('#6E4BCE'))
		# pal.setColor(QPalette.ColorGroup.Normal,
		# 			 QPalette.ColorRole.Window, QColor('#110F1B'))
		# app.setPalette(pal)
		home_path = os.path.normpath(f'{Path(__file__).parent}/ui/home.ui')
		icon_path = os.path.normpath(
			f'{Path(__file__).parent.parent.parent}/resources/icon.png')
		
		# Handle OS signals
		self.setup_signals()
		timer = QTimer()
		timer.start(500)
		timer.timeout.connect(lambda: None)

		# self.main_window = loader.load(home_path)
		self.main_window = Ui_MainWindow()
		self.main_window.setWindowTitle(self.base_title)
		self.main_window.mousePressEvent = self.mouse_navigation
		# self.main_window.setStyleSheet(
		# 	f'QScrollBar::{{background:red;}}'
		# 	)

		# # self.main_window.windowFlags() & 
		# # self.main_window.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
		# self.main_window.setWindowFlag(Qt.WindowType.NoDropShadowWindowHint, True)
		# self.main_window.setWindowFlag(Qt.WindowType.WindowTransparentForInput, False)
		# self.main_window.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

		# self.windowFX = WindowEffect()
		# self.windowFX.setAcrylicEffect(self.main_window.winId())

		splash_pixmap = QPixmap(':/images/splash.png')
		splash_pixmap.setDevicePixelRatio(self.main_window.devicePixelRatio())
		self.splash = QSplashScreen(splash_pixmap)
		# self.splash.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
		self.splash.show()

		menu_bar = self.main_window.menuBar()
		menu_bar.setNativeMenuBar(False)
		# menu_bar.setStyleSheet('background:#00000000;')
		file_menu = QMenu('&File', menu_bar)
		edit_menu = QMenu('&Edit', menu_bar)
		tools_menu = QMenu('&Tools', menu_bar)
		macros_menu = QMenu('&Macros', menu_bar)
		help_menu = QMenu('&Help', menu_bar)

		# File Menu ============================================================
		# file_menu.addAction(QAction('&New Library', menu_bar))
		# file_menu.addAction(QAction('&Open Library', menu_bar))

		open_library_action = QAction('&Open/Create Library', menu_bar)
		open_library_action.triggered.connect(lambda: self.open_library_from_dialog())
		file_menu.addAction(open_library_action)

		save_library_action = QAction('&Save Library', menu_bar)
		save_library_action.triggered.connect(lambda: self.callback_library_needed_check(self.save_library))
		file_menu.addAction(save_library_action)
	
		save_library_backup_action = QAction('Save Library &Backup', menu_bar)
		save_library_backup_action.triggered.connect(lambda: self.callback_library_needed_check(self.backup_library))
		file_menu.addAction(save_library_backup_action)

		file_menu.addSeparator()

		# refresh_lib_action = QAction('&Refresh Directories', self.main_window)
		# refresh_lib_action.triggered.connect(lambda: self.lib.refresh_dir())
		add_new_files_action = QAction('&Refresh Directories', menu_bar)
		add_new_files_action.triggered.connect(lambda: self.callback_library_needed_check(self.add_new_files_callback))
		# file_menu.addAction(refresh_lib_action)
		file_menu.addAction(add_new_files_action)

		file_menu.addSeparator()

		file_menu.addAction(QAction('&Close Library', menu_bar))

		# Edit Menu ============================================================
		new_tag_action = QAction('New Tag', menu_bar)
		new_tag_action.triggered.connect(lambda: self.add_tag_action_callback())
		edit_menu.addAction(new_tag_action)

		# Tools Menu ===========================================================
		fix_unlinked_entries_action = QAction('Fix &Unlinked Entries', menu_bar)
		fue_modal = FixUnlinkedEntriesModal(self.lib, self)
		fix_unlinked_entries_action.triggered.connect(lambda: fue_modal.show())
		tools_menu.addAction(fix_unlinked_entries_action)

		fix_dupe_files_action = QAction('Fix Duplicate &Files', menu_bar)
		fdf_modal = FixDupeFilesModal(self.lib, self)
		fix_dupe_files_action.triggered.connect(lambda: fdf_modal.show())
		tools_menu.addAction(fix_dupe_files_action)
	
		create_collage_action = QAction('Create Collage', menu_bar)
		create_collage_action.triggered.connect(lambda: self.create_collage())
		tools_menu.addAction(create_collage_action)

		# Macros Menu ==========================================================
		self.autofill_action = QAction('Autofill', menu_bar)
		self.autofill_action.triggered.connect(lambda: (self.run_macros('autofill', [x[1] for x in self.selected if x[0] == ItemType.ENTRY]), self.preview_panel.update_widgets()))
		macros_menu.addAction(self.autofill_action)

		self.sort_fields_action = QAction('Sort Fields', menu_bar)
		self.sort_fields_action.triggered.connect(lambda: (self.run_macros('sort-fields', [x[1] for x in self.selected if x[0] == ItemType.ENTRY]), self.preview_panel.update_widgets()))
		macros_menu.addAction(self.sort_fields_action)

		self.set_macro_menu_viability()

		menu_bar.addMenu(file_menu)
		menu_bar.addMenu(edit_menu)
		menu_bar.addMenu(tools_menu)
		menu_bar.addMenu(macros_menu)
		menu_bar.addMenu(help_menu)

		# self.main_window.setMenuBar(menu_bar)
		# self.main_window.centralWidget().layout().addWidget(menu_bar, 0,0,1,1)
		# self.main_window.tb_layout.addWidget(menu_bar)

		icon = QIcon()
		icon.addFile(icon_path)
		self.main_window.setWindowIcon(icon)

		self.preview_panel = PreviewPanel(self.lib, self)
		l: QHBoxLayout = self.main_window.splitter
		l.addWidget(self.preview_panel)
		# self.preview_panel.update_widgets()
		# l.setEnabled(False)
		# self.entry_panel.setWindowIcon(icon)

		if os.name == 'nt':
			appid = "cyanvoxel.tagstudio.9"
			ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
				appid)
		app.setWindowIcon(icon)

		QFontDatabase.addApplicationFont(os.path.normpath(
			f'{Path(__file__).parent.parent.parent}/resources/qt/fonts/Oxanium-Bold.ttf'))
		
		self.thumb_size = 128
		self.max_results = 500
		self.item_thumbs: list[ItemThumb] = []
		self.thumb_renderers: list[ThumbRenderer] = []
		self.collation_thumb_size = math.ceil(self.thumb_size * 2)
		# self.filtered_items: list[tuple[SearchItemType, int]] = []

		self._init_thumb_grid()

		# TODO: Put this into its own method that copies the font file(s) into memory
		# so the resource isn't being used, then store the specific size variations
		# in a global dict for methods to access for different DPIs.
		# adj_font_size = math.floor(12 * self.main_window.devicePixelRatio())
		# self.ext_font = ImageFont.truetype(os.path.normpath(f'{Path(__file__).parent.parent.parent}/resources/qt/fonts/Oxanium-Bold.ttf'), adj_font_size)

		search_button: QPushButton = self.main_window.searchButton
		search_button.clicked.connect(
			lambda: self.filter_items(self.main_window.searchField.text()))
		search_field: QLineEdit = self.main_window.searchField
		search_field.returnPressed.connect(
			lambda: self.filter_items(self.main_window.searchField.text()))

		back_button: QPushButton = self.main_window.backButton
		back_button.clicked.connect(self.nav_back)
		forward_button: QPushButton = self.main_window.forwardButton
		forward_button.clicked.connect(self.nav_forward)

		self.frame_dict = {}
		self.main_window.pagination.index.connect(lambda i:(self.nav_forward(*self.get_frame_contents(i, self.nav_frames[self.cur_frame_idx].search_text)), logging.info(f'emitted {i}')))

		

		self.nav_frames: list[NavigationState] = []
		self.cur_frame_idx: int = -1
		self.cur_query: str = ''
		self.filter_items()
		# self.update_thumbs()

		# self.render_times: list = []
		# self.main_window.setWindowFlag(Qt.FramelessWindowHint)

		# NOTE: Putting this early will result in a white non-responsive
		# window until everything is loaded. Consider adding a splash screen
		# or implementing some clever loading tricks.
		self.main_window.show()
		self.main_window.activateWindow()
		# self.main_window.raise_()
		self.splash.finish(self.main_window)
		self.preview_panel.update_widgets()

		# Check if a library should be opened on startup, args should override last_library
		# TODO: check for behavior (open last, open default, start empty)
		if self.args.open or self.settings.contains("last_library"):
			if self.args.open:
				lib = self.args.open
			elif self.settings.value("last_library"):
				lib = self.settings.value("last_library")
			self.splash.showMessage(f'Opening Library "{lib}"...', int(Qt.AlignmentFlag.AlignBottom|Qt.AlignmentFlag.AlignHCenter), QColor('#9782ff'))
			self.open_library(lib)

		app.exec_()

		self.shutdown()


	def callback_library_needed_check(self,func):
		#Check if loaded library has valid path before executing the button function
		if self.lib.library_dir:
			func()


	def handleSIGTERM(self):
		self.shutdown()
		
	def shutdown(self):
		# Save Library on Application Exit
		if self.lib.library_dir:
			self.save_library()
			self.settings.setValue("last_library", self.lib.library_dir)
			self.settings.sync()
		QApplication.quit()
	
	
	def save_library(self):
		logging.info(f'Saving Library...')
		self.main_window.statusbar.showMessage(f'Saving Library...')
		start_time = time.time()
		self.lib.save_library_to_disk()
		end_time = time.time()
		self.main_window.statusbar.showMessage(f'Library Saved! ({format_timespan(end_time - start_time)})')

	def backup_library(self):
		logging.info(f'Backing Up Library...')
		self.main_window.statusbar.showMessage(f'Saving Library...')
		start_time = time.time()
		fn = self.lib.save_library_backup_to_disk()
		end_time = time.time()
		self.main_window.statusbar.showMessage(f'Library Backup Saved at: "{os.path.normpath(os.path.normpath(f"{self.lib.library_dir}/{TS_FOLDER_NAME}/{BACKUP_FOLDER_NAME}/{fn}"))}" ({format_timespan(end_time - start_time)})')
	
	def add_tag_action_callback(self):
		self.modal = PanelModal(BuildTagPanel(self.lib), 
								'New Tag', 
								'Add Tag',
								has_save=True)
		# self.edit_modal.widget.update_display_name.connect(lambda t: self.edit_modal.title_widget.setText(t))
		panel: BuildTagPanel = self.modal.widget
		self.modal.saved.connect(lambda: (self.lib.add_tag_to_library(panel.build_tag()), self.modal.hide()))
		# panel.tag_updated.connect(lambda tag: self.lib.update_tag(tag))
		self.modal.show()
	
	def add_new_files_callback(self):
		"""Runs when user initiates adding new files to the Library."""
		# # if self.lib.files_not_in_library:
		# # 	mb = QMessageBox()
		# # 	mb.setText(f'Would you like to refresh the directory before adding {len(self.lib.files_not_in_library)} new files to the library?\nThis will add any additional files that have been moved to the directory since the last refresh.')
		# # 	mb.setWindowTitle('Refresh Library')
		# # 	mb.setIcon(QMessageBox.Icon.Information)
		# # 	mb.setStandardButtons(QMessageBox.StandardButton.No)
		# # 	refresh_button = mb.addButton('Refresh', QMessageBox.ButtonRole.AcceptRole)
		# # 	mb.setDefaultButton(refresh_button)
		# # 	result = mb.exec_()
		# # 	# logging.info(result)
		# # 	if result == 0:
		# # 		self.main_window.statusbar.showMessage(f'Refreshing Library...', 3)
		# # 		self.lib.refresh_dir()
		# # else:
		# pb = QProgressDialog('Scanning Directories for New Files...\nPreparing...', None, 0,0)
		
		# pb.setFixedSize(432, 112)
		# pb.setWindowFlags(pb.windowFlags() & ~Qt.WindowType.WindowCloseButtonHint)
		# # pb.setLabelText('Scanning Directories...')
		# pb.setWindowTitle('Scanning Directories')
		# pb.setWindowModality(Qt.WindowModality.ApplicationModal)
		# # pb.setMinimum(0)
		# # pb.setMaximum(0)
		# # pb.setValue(0)
		# pb.show()
		# self.main_window.statusbar.showMessage(f'Refreshing Library...', 3)
		# # self.lib.refresh_dir()
		# r = CustomRunnable(lambda: self.runnable(pb))
		# logging.info(f'Main: {QThread.currentThread()}')
		# r.done.connect(lambda: (pb.hide(), pb.deleteLater(), self.add_new_files_runnable()))
		# QThreadPool.globalInstance().start(r)
		# # r.run()
			
		# # new_ids: list[int] = self.lib.add_new_files_as_entries()
		# # # logging.info(f'{INFO} Running configured Macros on {len(new_ids)} new Entries...')
		# # # self.main_window.statusbar.showMessage(f'Running configured Macros on {len(new_ids)} new Entries...', 3)
		# # # for id in new_ids:
		# # # 	self.run_macro('autofill', id)
		
		# # self.main_window.statusbar.showMessage('', 3)
		# # self.filter_entries('')


		iterator = FunctionIterator(self.lib.refresh_dir)
		pw = ProgressWidget(
			window_title='Refreshing Directories', 
			label_text='Scanning Directories for New Files...\nPreparing...', 
			cancel_button_text=None, 
			minimum=0,
			maximum=0
			)
		pw.show()
		iterator.value.connect(lambda x: pw.update_progress(x+1))
		iterator.value.connect(lambda x: pw.update_label(f'Scanning Directories for New Files...\n{x+1} File{"s" if x+1 != 1 else ""} Searched, {len(self.lib.files_not_in_library)} New Files Found'))
		r = CustomRunnable(lambda:iterator.run())
		r.done.connect(lambda: (pw.hide(), pw.deleteLater(), self.add_new_files_runnable()))
		QThreadPool.globalInstance().start(r)
		
	
	# def runnable(self, pb:QProgressDialog):
	# 	for i in self.lib.refresh_dir():
	# 		pb.setLabelText(f'Scanning Directories for New Files...\n{i} File{"s" if i != 1 else ""} Searched, {len(self.lib.files_not_in_library)} New Files Found')
			
	
	def add_new_files_runnable(self):
		"""
		Threaded method that adds any known new files to the library and
		initiates running default macros on them.
		"""
		# logging.info(f'Start ANF: {QThread.currentThread()}')
		new_ids: list[int] = self.lib.add_new_files_as_entries()
		# pb = QProgressDialog(f'Running Configured Macros on 1/{len(new_ids)} New Entries', None, 0,len(new_ids))
		# pb.setFixedSize(432, 112)
		# pb.setWindowFlags(pb.windowFlags() & ~Qt.WindowType.WindowCloseButtonHint)
		# pb.setWindowTitle('Running Macros')
		# pb.setWindowModality(Qt.WindowModality.ApplicationModal)
		# pb.show()
		
		# r = CustomRunnable(lambda: self.new_file_macros_runnable(pb, new_ids))
		# r.done.connect(lambda: (pb.hide(), pb.deleteLater(), self.filter_items('')))
		# r.run()
		# # QThreadPool.globalInstance().start(r)
		
		# # logging.info(f'{INFO} Running configured Macros on {len(new_ids)} new Entries...')
		# # self.main_window.statusbar.showMessage(f'Running configured Macros on {len(new_ids)} new Entries...', 3)
		
		# # pb.hide()



		iterator = FunctionIterator(lambda:self.new_file_macros_runnable(new_ids))
		pw = ProgressWidget(
			window_title='Running Macros on New Entries', 
			label_text=f'Running Configured Macros on 1/{len(new_ids)} New Entries', 
			cancel_button_text=None, 
			minimum=0,
			maximum=0
			)
		pw.show()
		iterator.value.connect(lambda x: pw.update_progress(x+1))
		iterator.value.connect(lambda x: pw.update_label(f'Running Configured Macros on {x+1}/{len(new_ids)} New Entries'))
		r = CustomRunnable(lambda:iterator.run())
		r.done.connect(lambda: (pw.hide(), pw.deleteLater(), self.filter_items('')))
		QThreadPool.globalInstance().start(r)

	def new_file_macros_runnable(self,  new_ids):
		"""Threaded method that runs macros on a set of Entry IDs."""
		# sleep(1)
		logging.info(f'ANFR: {QThread.currentThread()}')
		for i, id in enumerate(new_ids):
			# pb.setValue(i)
			# pb.setLabelText(f'Running Configured Macros on {i}/{len(new_ids)} New Entries')
			# self.run_macro('autofill', id)
			yield i
		
		# self.main_window.statusbar.showMessage('', 3)
		
		# sleep(5)
		# pb.deleteLater()
	
	def run_macros(self, name: str, entry_ids: int):
		"""Runs a specific Macro on a group of given entry_ids."""
		for id in entry_ids:
			self.run_macro(name, id)
	
	def run_macro(self, name: str, entry_id: int):
		"""Runs a specific Macro on an Entry given a Macro name."""
		entry = self.lib.get_entry(entry_id)
		path = os.path.normpath(
			f'{self.lib.library_dir}/{entry.path}/{entry.filename}')
		source = path.split(os.sep)[1].lower()
		if name == 'sidecar':
			self.lib.add_generic_data_to_entry(
				self.core.get_gdl_sidecar(path, source), entry_id)
		elif name == 'autofill':
			self.run_macro('sidecar', entry_id)
			self.run_macro('build-url', entry_id)
			self.run_macro('match', entry_id)
			self.run_macro('clean-url', entry_id)
			self.run_macro('sort-fields', entry_id)
		elif name == 'build-url':
			data = {'source': self.core.build_url(entry_id, source)}
			self.lib.add_generic_data_to_entry(data, entry_id)
		elif name == 'sort-fields':
			order: list[int] = (
				[0] + 
				[1, 2] + 
				[9, 17, 18, 19, 20] + 
				[8, 7, 6] + 
				[4] + 
				[3, 21] +
				[10, 14, 11, 12, 13, 22] +
				[5]
				)
			self.lib.sort_fields(entry_id, order)
		elif name == 'match':
			self.core.match_conditions(entry_id)
		# elif name == 'scrape':
		# 	self.core.scrape(entry_id)
		elif name == 'clean-url':
			# entry = self.lib.get_entry_from_index(entry_id)
			if entry.fields:
				for i, field in enumerate(entry.fields, start=0):
					if self.lib.get_field_attr(field, 'type') == 'text_line':
						self.lib.update_entry_field(
							entry_id=entry_id,
							field_index=i,
							content=strip_web_protocol(
								self.lib.get_field_attr(field, 'content')),
							mode='replace')

	def mouse_navigation(self, event: QMouseEvent):
		# print(event.button())
		if event.button() == Qt.MouseButton.ForwardButton:
			self.nav_forward()
		elif event.button() == Qt.MouseButton.BackButton:
			self.nav_back()

	def nav_forward(self, frame_content: Optional[list[tuple[ItemType, int]]] = None, page_index:int=0, page_count:int = 0):
		"""Navigates a step further into the navigation stack."""
		logging.info(f'Calling NavForward with Content:{False if not frame_content else frame_content[0]}, Index:{page_index}, PageCount:{page_count}')

		# Ex. User visits | A ->[B]     |
		#                 | A    B ->[C]|
		#                 | A   [B]<- C |
		#                 |[A]<- B    C |  Previous routes still exist
		#                 | A ->[D]     |  Stack is cut from [:A] on new route

		# Moving forward (w/ or wo/ new content) in the middle of the stack
		original_pos = self.cur_frame_idx
		sb: QScrollArea = self.main_window.scrollArea
		sb_pos = sb.verticalScrollBar().value()
		search_text = self.main_window.searchField.text()

		trimmed = False
		if len(self.nav_frames) > self.cur_frame_idx + 1:
			if (frame_content != None):
				# Trim the nav stack if user is taking a new route.
				self.nav_frames = self.nav_frames[:self.cur_frame_idx+1]
				if self.nav_frames and not self.nav_frames[self.cur_frame_idx].contents:
					self.nav_frames.pop()
					trimmed = True
				self.nav_frames.append(NavigationState(frame_content, 0, page_index, page_count, search_text))
				# logging.info(f'Saving Text: {search_text}')
			# Update the last frame's scroll_pos
			self.nav_frames[self.cur_frame_idx].scrollbar_pos = sb_pos
			self.cur_frame_idx += 1 if not trimmed else 0
		# Moving forward at the end of the stack with new content
		elif (frame_content != None):
			# If the current page is empty, don't include it in the new stack.
			if self.nav_frames and not self.nav_frames[self.cur_frame_idx].contents:
				self.nav_frames.pop()
				trimmed = True
			self.nav_frames.append(NavigationState(frame_content, 0, page_index, page_count, search_text))
			# logging.info(f'Saving Text: {search_text}')
			self.nav_frames[self.cur_frame_idx].scrollbar_pos = sb_pos
			self.cur_frame_idx += 1 if not trimmed else 0

		# if self.nav_stack[self.cur_page_idx].contents:
		if (self.cur_frame_idx != original_pos) or (frame_content != None):
			self.update_thumbs()
			sb.verticalScrollBar().setValue(
				self.nav_frames[self.cur_frame_idx].scrollbar_pos)
			self.main_window.searchField.setText(self.nav_frames[self.cur_frame_idx].search_text)
			self.main_window.pagination.update_buttons(self.nav_frames[self.cur_frame_idx].page_count, self.nav_frames[self.cur_frame_idx].page_index, emit=False)
			# logging.info(f'Setting Text: {self.nav_stack[self.cur_page_idx].search_text}')
		# else:
		# 	self.nav_stack.pop()
		# 	self.cur_page_idx -= 1
		# 	self.update_thumbs()
		# 	sb.verticalScrollBar().setValue(self.nav_stack[self.cur_page_idx].scrollbar_pos)

		# logging.info(f'Forward: {[len(x.contents) for x in self.nav_stack]}, Index {self.cur_page_idx}, SB {self.nav_stack[self.cur_page_idx].scrollbar_pos}')

	def nav_back(self):
		"""Navigates a step backwards in the navigation stack."""

		original_pos = self.cur_frame_idx
		sb: QScrollArea = self.main_window.scrollArea
		sb_pos = sb.verticalScrollBar().value()

		if self.cur_frame_idx > 0:
			self.nav_frames[self.cur_frame_idx].scrollbar_pos = sb_pos
			self.cur_frame_idx -= 1
			if self.cur_frame_idx != original_pos:
				self.update_thumbs()
				sb.verticalScrollBar().setValue(
					self.nav_frames[self.cur_frame_idx].scrollbar_pos)
				self.main_window.searchField.setText(self.nav_frames[self.cur_frame_idx].search_text)
				self.main_window.pagination.update_buttons(self.nav_frames[self.cur_frame_idx].page_count, self.nav_frames[self.cur_frame_idx].page_index, emit=False)
				# logging.info(f'Setting Text: {self.nav_stack[self.cur_page_idx].search_text}')
		# logging.info(f'Back: {[len(x.contents) for x in self.nav_stack]}, Index {self.cur_page_idx}, SB {self.nav_stack[self.cur_page_idx].scrollbar_pos}')

	def refresh_frame(self, frame_content: list[tuple[ItemType, int]], page_index:int=0, page_count:int = 0):
		"""
		Refreshes the current navigation contents without altering the 
		navigation stack order.
		"""
		if self.nav_frames:
			self.nav_frames[self.cur_frame_idx] = NavigationState(frame_content, 0, self.nav_frames[self.cur_frame_idx].page_index, self.nav_frames[self.cur_frame_idx].page_count, self.main_window.searchField.text())
		else:
			self.nav_forward(frame_content, page_index, page_count)
		self.update_thumbs()
		# logging.info(f'Refresh: {[len(x.contents) for x in self.nav_stack]}, Index {self.cur_page_idx}')
	
	def purge_item_from_navigation(self, type:ItemType, id:int):
		# logging.info(self.nav_frames)
		for i, frame in enumerate(self.nav_frames, start=0):
			while (type, id) in frame.contents:
				logging.info(f'Removing {id} from nav stack frame {i}')
				frame.contents.remove((type, id))
		
		for i, key in enumerate(self.frame_dict.keys(), start=0):
			for frame in self.frame_dict[key]:
				while (type, id) in frame:
					logging.info(f'Removing {id} from frame dict item {i}')
					frame.remove((type, id))
		
		while (type, id) in self.selected:
			logging.info(f'Removing {id} from frame selected')
			self.selected.remove((type, id))


	def _init_thumb_grid(self):
		# logging.info('Initializing Thumbnail Grid...')
		layout = FlowLayout()
		layout.setGridEfficiency(True)
		# layout.setContentsMargins(0,0,0,0)
		layout.setSpacing(min(self.thumb_size//10, 12))
		# layout = QHBoxLayout()
		# layout.setSizeConstraint(QLayout.SizeConstraint.SetMaximumSize)
		# layout = QListView()
		# layout.setViewMode(QListView.ViewMode.IconMode)

		col_size = 28
		for i in range(0, self.max_results):
			item_thumb = ItemThumb(None, self.lib, self.preview_panel,
							 (self.thumb_size, self.thumb_size))
			layout.addWidget(item_thumb)
			self.item_thumbs.append(item_thumb)

		self.flow_container: QWidget = QWidget()
		self.flow_container.setObjectName('flowContainer')
		self.flow_container.setLayout(layout)
		layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
		sa: QScrollArea = self.main_window.scrollArea
		sa.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
		sa.setWidgetResizable(True)
		sa.setWidget(self.flow_container)

	def select_item(self, type:int, id:int, append:bool, bridge:bool):
		"""Selects one or more items in the Thumbnail Grid."""
		if append:
			# self.selected.append((thumb_index, page_index))
			if ((type, id)) not in self.selected:
				self.selected.append((type, id))
				for it in self.item_thumbs:
					if it.mode == type and it.item_id == id:
						it.thumb_button.set_selected(True)
			else:
				self.selected.remove((type, id))
				for it in self.item_thumbs:
					if it.mode == type and it.item_id == id:
						it.thumb_button.set_selected(False)
			# self.item_thumbs[thumb_index].thumb_button.set_selected(True)
			
		elif bridge and self.selected:
			logging.info(f'Last Selected: {self.selected[-1]}')
			contents = self.nav_frames[self.cur_frame_idx].contents
			last_index = self.nav_frames[self.cur_frame_idx].contents.index(self.selected[-1])
			current_index = self.nav_frames[self.cur_frame_idx].contents.index((type, id))
			index_range: list = contents[min(last_index, current_index):max(last_index, current_index)+1]
			# Preserve bridge direction for correct appending order.
			if last_index < current_index:
				index_range.reverse()
			
			# logging.info(f'Current Frame Contents: {len(self.nav_frames[self.cur_frame_idx].contents)}')
			# logging.info(f'Last Selected Index: {last_index}')
			# logging.info(f'Current Selected Index: {current_index}')
			# logging.info(f'Index Range: {index_range}')

			for c_type, c_id in index_range:
				for it in self.item_thumbs:
					if it.mode == c_type and it.item_id == c_id:
						it.thumb_button.set_selected(True)
						if ((c_type, c_id)) not in self.selected:
							self.selected.append((c_type, c_id))
		else:
			# for i in self.selected:
			# 	if i[1] == self.cur_frame_idx:
			# 		self.item_thumbs[i[0]].thumb_button.set_selected(False)
			self.selected.clear()
			# self.selected.append((thumb_index, page_index))
			self.selected.append((type, id))
			# self.item_thumbs[thumb_index].thumb_button.set_selected(True)
			for it in self.item_thumbs:
				if it.mode == type and it.item_id == id:
					it.thumb_button.set_selected(True)
				else:
					it.thumb_button.set_selected(False)
		
		# NOTE: By using the preview panel's "set_tags_updated_slot" method,
		# only the last of multiple identical item selections are connected.
		# If attaching the slot to multiple duplicate selections is needed,
		# just bypass the method and manually disconnect and connect the slots.
		if len(self.selected) == 1:
			for it in self.item_thumbs:
				if it.mode == type and it.item_id == id:
					self.preview_panel.set_tags_updated_slot(it.update_badges)
		
		self.set_macro_menu_viability()
		self.preview_panel.update_widgets()
		
	def set_macro_menu_viability(self):
		if len([x[1] for x in self.selected if x[0] == ItemType.ENTRY]) == 0:
			self.autofill_action.setDisabled(True)
			self.sort_fields_action.setDisabled(True)
		else:
			self.autofill_action.setDisabled(False)
			self.sort_fields_action.setDisabled(False)

	def update_thumbs(self):
		"""Updates search thumbnails."""
		# start_time = time.time()
		# logging.info(f'Current Page: {self.cur_page_idx}, Stack Length:{len(self.nav_stack)}')
		with self.thumb_job_queue.mutex:
			# Cancels all thumb jobs waiting to be started
			self.thumb_job_queue.queue.clear()
			self.thumb_job_queue.all_tasks_done.notify_all()
			self.thumb_job_queue.not_full.notify_all()
			# Stops in-progress jobs from finishing
			ItemThumb.update_cutoff = time.time()

		ratio: float = self.main_window.devicePixelRatio()
		base_size: tuple[int, int] = (self.thumb_size, self.thumb_size)

		for i, item_thumb in enumerate(self.item_thumbs, start=0):
			
			if i < len(self.nav_frames[self.cur_frame_idx].contents):
				# Set new item type modes
				# logging.info(f'[UPDATE] Setting Mode To: {self.nav_stack[self.cur_page_idx].contents[i][0]}')
				item_thumb.set_mode(self.nav_frames[self.cur_frame_idx].contents[i][0])
				item_thumb.ignore_size = False
				# logging.info(f'[UPDATE] Set Mode To: {item.mode}')
				# Set thumbnails to loading (will always finish if rendering)
				self.thumb_job_queue.put(
					(item_thumb.renderer.render, (sys.float_info.max, '',
											base_size, ratio, True)))
				# # Restore Selected Borders
				# if (item_thumb.mode, item_thumb.item_id) in self.selected:
				# 	item_thumb.thumb_button.set_selected(True)
				# else:
				# 	item_thumb.thumb_button.set_selected(False)
			else:
				item_thumb.ignore_size = True
				item_thumb.set_mode(None)
				item_thumb.set_item_id(-1)
				item_thumb.thumb_button.set_selected(False)

		# scrollbar: QScrollArea = self.main_window.scrollArea
		# scrollbar.verticalScrollBar().setValue(scrollbar_pos)
		self.flow_container.layout().update()
		self.main_window.update()

		for i, item_thumb in enumerate(self.item_thumbs, start=0):
			if i < len(self.nav_frames[self.cur_frame_idx].contents):
				filepath = ''
				if self.nav_frames[self.cur_frame_idx].contents[i][0] == ItemType.ENTRY:
					entry = self.lib.get_entry(
						self.nav_frames[self.cur_frame_idx].contents[i][1])
					filepath = os.path.normpath(
						f'{self.lib.library_dir}/{entry.path}/{entry.filename}')
					
					item_thumb.set_item_id(entry.id)
					item_thumb.assign_archived(entry.has_tag(self.lib, 0))
					item_thumb.assign_favorite(entry.has_tag(self.lib, 1))
					# ctrl_down = True if QGuiApplication.keyboardModifiers() else False
					# TODO: Change how this works. The click function
					# for collations a few lines down should NOT be allowed during modifier keys.
					item_thumb.update_clickable(clickable=(
						lambda checked=False, entry=entry: 
							self.select_item(ItemType.ENTRY, entry.id, 
						append=True if QGuiApplication.keyboardModifiers() == Qt.KeyboardModifier.ControlModifier else False,
						bridge=True if QGuiApplication.keyboardModifiers() == Qt.KeyboardModifier.ShiftModifier else False)))
					# item_thumb.update_clickable(clickable=(
					# 	lambda checked=False, filepath=filepath, entry=entry, 
					# 		   item_t=item_thumb, i=i, page=self.cur_frame_idx: (
					# 		self.preview_panel.update_widgets(entry), 
					# 		self.select_item(ItemType.ENTRY, entry.id, 
					# 	append=True if QGuiApplication.keyboardModifiers() == Qt.KeyboardModifier.ControlModifier else False,
					# 	bridge=True if QGuiApplication.keyboardModifiers() == Qt.KeyboardModifier.ShiftModifier else False))))
					# item.dumpObjectTree()
				elif self.nav_frames[self.cur_frame_idx].contents[i][0] == ItemType.COLLATION:
					collation = self.lib.get_collation(
						self.nav_frames[self.cur_frame_idx].contents[i][1])
					cover_id = collation.cover_id if collation.cover_id >= 0 else collation.e_ids_and_pages[
						0][0]
					cover_e = self.lib.get_entry(cover_id)
					filepath = os.path.normpath(
						f'{self.lib.library_dir}/{cover_e.path}/{cover_e.filename}')
					item_thumb.set_count(str(len(collation.e_ids_and_pages)))
					item_thumb.update_clickable(clickable=(lambda checked=False, filepath=filepath, entry=cover_e, collation=collation: (
						self.expand_collation(collation.e_ids_and_pages))))
				# item.setHidden(False)

				# Restore Selected Borders
				if (item_thumb.mode, item_thumb.item_id) in self.selected:
					item_thumb.thumb_button.set_selected(True)
				else:
					item_thumb.thumb_button.set_selected(False)

				self.thumb_job_queue.put(
					(item_thumb.renderer.render, (time.time(), filepath, base_size, ratio, False)))
			else:
				# item.setHidden(True)
				pass
				# update_widget_clickable(widget=item.bg_button, clickable=())
				# self.thumb_job_queue.put(
				# 	(item.renderer.render, ('', base_size, ratio, False)))

		# end_time = time.time()
		# logging.info(
		# 	f'[MAIN] Elements thumbs updated in {(end_time - start_time):.3f} seconds')

	def update_badges(self):
		for i, item_thumb in enumerate(self.item_thumbs, start=0):
			item_thumb.update_badges()

	def expand_collation(self, collation_entries: list[tuple[int, int]]):
		self.nav_forward([(ItemType.ENTRY, x[0])
						 for x in collation_entries])
		# self.update_thumbs()

	def get_frame_contents(self, index=0, query=str):
		return ([] if not self.frame_dict[query] else self.frame_dict[query][index], index, len(self.frame_dict[query]))

	def filter_items(self, query=''):
		if self.lib:

			# logging.info('Filtering...')
			self.main_window.statusbar.showMessage(
				f'Searching Library for \"{query}\"...')
			self.main_window.statusbar.repaint()
			start_time = time.time()

			# self.filtered_items = self.lib.search_library(query)
			# 73601 Entries at 500 size should be 246
			all_items = self.lib.search_library(query)
			frames = []
			frame_count = math.ceil(len(all_items)/self.max_results)
			for i in range(0, frame_count):
				frames.append(all_items[min(len(all_items)-1, (i)*self.max_results):min(len(all_items), (i+1)*self.max_results)])
			for i, f in enumerate(frames):
				logging.info(f'Query:{query}, Frame: {i},  Length: {len(f)}')
			self.frame_dict[query] = frames
			# self.frame_dict[query] = [all_items]

			if self.cur_query == query:
				# self.refresh_frame(self.lib.search_library(query))
				# NOTE: Trying to refresh instead of navigating forward here
				# now creates a bug when the page counts differ on refresh.
				# If refreshing is absolutely desired, see how to update
				# page counts where they need to be updated.
				self.nav_forward(*self.get_frame_contents(0, query))
			else:
				# self.nav_forward(self.lib.search_library(query))
				self.nav_forward(*self.get_frame_contents(0, query))
			self.cur_query = query

			end_time = time.time()
			if query:
				self.main_window.statusbar.showMessage(
					f'{len(all_items)} Results Found for \"{query}\" ({format_timespan(end_time - start_time)})')
			else:
				self.main_window.statusbar.showMessage(
					f'{len(all_items)} Results ({format_timespan(end_time - start_time)})')
			# logging.info(f'Done Filtering! ({(end_time - start_time):.3f}) seconds')

			# self.update_thumbs()

	def open_library(self, path):
		"""Opens a TagStudio library."""
		if self.lib.library_dir:
			self.save_library()
			self.lib.clear_internal_vars()

		self.main_window.statusbar.showMessage(f'Opening Library {path}', 3)
		return_code = self.lib.open_library(path)
		if return_code == 1:
			# if self.args.external_preview:
			# 	self.init_external_preview()

			# if len(self.lib.entries) <= 1000:
			# 	print(f'{INFO} Checking for missing files in Library \'{self.lib.library_dir}\'...')
			# 	self.lib.refresh_missing_files()
			# title_text = f'{self.base_title} - Library \'{self.lib.library_dir}\''
			# self.main_window.setWindowTitle(title_text)
			pass

		else:
			logging.info(f'{ERROR} No existing TagStudio library found at \'{path}\'. Creating one.')
			print(f'Library Creation Return Code: {self.lib.create_library(path)}')
			self.add_new_files_callback()
		
		title_text = f'{self.base_title} - Library \'{self.lib.library_dir}\''
		self.main_window.setWindowTitle(title_text)

		self.nav_frames: list[NavigationState] = []
		self.cur_frame_idx: int = -1
		self.cur_query: str = ''
		self.selected.clear()
		self.preview_panel.update_widgets()
		self.filter_items()

	def create_collage(self) -> None:
		"""Generates and saves an image collage based on Library Entries."""

		run: bool = True
		keep_aspect: bool = False
		data_only_mode: bool = False
		data_tint_mode: bool = False

		self.main_window.statusbar.showMessage(f'Creating Library Collage...')
		self.collage_start_time = time.time()

		# mode:int = self.scr_choose_option(subtitle='Choose Collage Mode(s)',
		# 	choices=[
		# 	('Normal','Creates a standard square image collage made up of Library media files.'),
		# 	('Data Tint','Tints the collage with a color representing data about the Library Entries/files.'),
		# 	('Data Only','Ignores media files entirely and only outputs a collage of Library Entry/file data.'),
		# 	('Normal & Data Only','Creates both Normal and Data Only collages.'),
		# 	], prompt='', required=True)
		mode = 0
	
		if mode == 1:
			data_tint_mode = True
		
		if mode == 2:
			data_only_mode = True
		
		if mode in [0, 1, 3]:
			# keep_aspect = self.scr_choose_option(
			# 	subtitle='Choose Aspect Ratio Option',
			# 	choices=[
			# 	('Stretch to Fill','Stretches the media file to fill the entire collage square.'),
			# 	('Keep Aspect Ratio','Keeps the original media file\'s aspect ratio, filling the rest of the square with black bars.')
			# 	], prompt='', required=True)
			keep_aspect = 0
		
		if mode in [1, 2, 3]:
			# TODO: Choose data visualization options here.
			pass
		
		full_thumb_size: int = 1

		if mode in [0, 1, 3]:
			# full_thumb_size = self.scr_choose_option(
			# 	subtitle='Choose Thumbnail Size',
			# 	choices=[
			# 	('Tiny (32px)',''),
			# 	('Small (64px)',''),
			# 	('Medium (128px)',''),
			# 	('Large (256px)',''),
			# 	('Extra Large (512px)','')
			# 	], prompt='', required=True)
			full_thumb_size = 0
		
		thumb_size: int = (32 if (full_thumb_size == 0) 
						else 64 if (full_thumb_size == 1) 
						else 128 if (full_thumb_size == 2) 
						else 256 if (full_thumb_size == 3) 
						else 512 if (full_thumb_size == 4) 
						else 32)
		thumb_size = 16

		# if len(com) > 1 and com[1] == 'keep-aspect':
		# 	keep_aspect = True
		# elif len(com) > 1 and com[1] == 'data-only':
		# 	data_only_mode = True
		# elif len(com) > 1 and com[1] == 'data-tint':
		# 	data_tint_mode = True
		grid_size = math.ceil(math.sqrt(len(self.lib.entries)))**2
		grid_len = math.floor(math.sqrt(grid_size))
		thumb_size = thumb_size if not data_only_mode else 1
		img_size = thumb_size * grid_len
		
		logging.info(f'Creating collage for {len(self.lib.entries)} Entries.\nGrid Size: {grid_size} ({grid_len}x{grid_len})\nIndividual Picture Size: ({thumb_size}x{thumb_size})')
		if keep_aspect:
			logging.info('Keeping original aspect ratios.')
		if data_only_mode:
			logging.info('Visualizing Entry Data')
		
		if not data_only_mode:
			time.sleep(5)

		self.collage = Image.new('RGB', (img_size,img_size))
		i = 0
		self.completed = 0
		for x in range(0, grid_len):
			for y in range(0, grid_len):
				if i < len(self.lib.entries) and run:
				# if i < 5 and run:

					entry_id = self.lib.entries[i].id
					renderer = CollageIconRenderer(self.lib)
					renderer.rendered.connect(lambda image, x=x, y=y: self.collage.paste(image, (y*thumb_size, x*thumb_size)))
					renderer.done.connect(lambda: self.try_save_collage(True))
					self.thumb_job_queue.put((renderer.render, 
						(
						entry_id, 
						(thumb_size, thumb_size), 
						data_tint_mode, 
						data_only_mode, 
						keep_aspect
						)))
				i = i+1

	def try_save_collage(self, increment_progress:bool):
		if increment_progress:
			self.completed += 1
		# logging.info(f'threshold:{len(self.lib.entries}, completed:{self.completed}')
		if self.completed == len(self.lib.entries):
			filename = os.path.normpath(f'{self.lib.library_dir}/{TS_FOLDER_NAME}/{COLLAGE_FOLDER_NAME}/collage_{dt.utcnow().strftime("%F_%T").replace(":", "")}.png')
			self.collage.save(filename)
			self.collage = None

			end_time = time.time()
			self.main_window.statusbar.showMessage(f'Collage Saved at "{filename}" ({format_timespan(end_time - self.collage_start_time)})')
			logging.info(f'Collage Saved at "{filename}" ({format_timespan(end_time - self.collage_start_time)})')
