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
from types import FunctionType
from datetime import datetime as dt
from pathlib import Path
from queue import Empty, Queue
from typing import Optional

import cv2
from PIL import Image, UnidentifiedImageError, ImageQt
from PySide6 import QtCore
from PySide6.QtCore import QObject, QThread, Signal, Qt, QThreadPool, QSize, QEvent, QTimer, QSettings
from PySide6.QtGui import (QGuiApplication, QPixmap, QEnterEvent, QMouseEvent, QResizeEvent, QColor, QAction,
						   QFontDatabase, QIcon)
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
							   QScrollArea, QFrame, QFileDialog, QSplitter, QSizePolicy, QMessageBox,
							   QBoxLayout, QCheckBox, QSplashScreen, QMenu)
from humanfriendly import format_timespan, format_size

from src.core.library import Entry, ItemType, Library
from src.core.ts_core import (PLAINTEXT_TYPES, TagStudioCore, TAG_COLORS, DATE_FIELDS, TEXT_FIELDS, BOX_FIELDS, ALL_FILE_TYPES,
										SHORTCUT_TYPES, PROGRAM_TYPES, ARCHIVE_TYPES, PRESENTATION_TYPES,
										SPREADSHEET_TYPES, DOC_TYPES, AUDIO_TYPES, VIDEO_TYPES, IMAGE_TYPES,
										LIBRARY_FILENAME, COLLAGE_FOLDER_NAME, BACKUP_FOLDER_NAME, TS_FOLDER_NAME,
										VERSION_BRANCH, VERSION)
from src.core.utils.web import strip_web_protocol
from src.qt.flowlayout import FlowLayout, FlowWidget
from src.qt.main_window import Ui_MainWindow
from src.qt.helpers import open_file, FileOpenerHelper, FileOpenerLabel, FunctionIterator, CustomRunnable
from src.qt.widgets import (FieldContainer, CollageIconRenderer, ThumbButton, ThumbRenderer, PanelModal, EditTextBox,
							EditTextLine, ProgressWidget, TagBoxWidget, TextWidget)
from src.qt.modals import (BuildTagPanel, TagDatabasePanel, AddFieldModal, FileExtensionModal, FixUnlinkedEntriesModal,
						   FixDupeFilesModal, FoldersToTagsModal)
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

		self.preview_img.setContextMenuPolicy(Qt.ContextMenuPolicy.ActionsContextMenu)
		self.opener = FileOpenerHelper('')
		self.open_file_action = QAction('Open file', self)
		self.open_explorer_action = QAction('Open file in explorer', self)

		self.preview_img.addAction(self.open_file_action)
		self.preview_img.addAction(self.open_explorer_action)
		self.tr = ThumbRenderer()
		self.tr.updated.connect(lambda ts, i, s: (self.preview_img.setIcon(i)))
		self.tr.updated_ratio.connect(lambda ratio: (self.set_image_ratio(ratio), 
											   self.update_image_size((self.image_container.size().width(), self.image_container.size().height()), ratio)))

		splitter.splitterMoved.connect(lambda: self.update_image_size((self.image_container.size().width(), self.image_container.size().height())))
		splitter.addWidget(self.image_container)

		image_layout.addWidget(self.preview_img)
		image_layout.setAlignment(self.preview_img, Qt.AlignmentFlag.AlignCenter)

		self.file_label = FileOpenerLabel('Filename')
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
				self.file_label.setFilePath('')
				self.dimensions_label.setText("")
				self.preview_img.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
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
					self.file_label.setFilePath(filepath)
					window_title = filepath
					ratio: float = self.devicePixelRatio()
					self.tr.render_big(time.time(), filepath, (512, 512), ratio)
					self.file_label.setText("\u200b".join(filepath))

					self.preview_img.setContextMenuPolicy(Qt.ContextMenuPolicy.ActionsContextMenu)
					self.opener = FileOpenerHelper(filepath)
					self.open_file_action.triggered.connect(self.opener.open_file)
					self.open_explorer_action.triggered.connect(self.opener.open_explorer)

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
				self.file_label.setFilePath('')
				self.dimensions_label.setText("")
				self.preview_img.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
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

		self.thumb_button.setContextMenuPolicy(Qt.ContextMenuPolicy.ActionsContextMenu)
		self.opener = FileOpenerHelper('')
		open_file_action = QAction('Open file', self)
		open_file_action.triggered.connect(self.opener.open_file)
		open_explorer_action = QAction('Open file in explorer', self)
		open_explorer_action.triggered.connect(self.opener.open_explorer)
		self.thumb_button.addAction(open_file_action)
		self.thumb_button.addAction(open_explorer_action)

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
		'''
		also sets the filepath for the file opener
		'''
		self.item_id = id
		if(id == -1):
			return
		entry = self.lib.get_entry(self.item_id)
		filepath = os.path.normpath(f'{self.lib.library_dir}/{entry.path}/{entry.filename}')
		self.opener.set_filepath(filepath)

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
		if dir not in (None, ''):
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
		open_library_action.setShortcut(QtCore.QKeyCombination(QtCore.Qt.KeyboardModifier(QtCore.Qt.KeyboardModifier.ControlModifier), QtCore.Qt.Key.Key_O))
		open_library_action.setToolTip("Ctrl+O")
		file_menu.addAction(open_library_action)

		save_library_action = QAction('&Save Library', menu_bar)
		save_library_action.triggered.connect(lambda: self.callback_library_needed_check(self.save_library))
		save_library_action.setShortcut(QtCore.QKeyCombination(QtCore.Qt.KeyboardModifier(QtCore.Qt.KeyboardModifier.ControlModifier), QtCore.Qt.Key.Key_S))
		save_library_action.setStatusTip("Ctrl+S")
		file_menu.addAction(save_library_action)
	
		save_library_backup_action = QAction('&Save Library Backup', menu_bar)
		save_library_backup_action.triggered.connect(lambda: self.callback_library_needed_check(self.backup_library))
		save_library_backup_action.setShortcut(QtCore.QKeyCombination(QtCore.Qt.KeyboardModifier(QtCore.Qt.KeyboardModifier.ControlModifier | QtCore.Qt.KeyboardModifier.ShiftModifier), QtCore.Qt.Key.Key_S))
		save_library_backup_action.setStatusTip("Ctrl+Shift+S")
		file_menu.addAction(save_library_backup_action)

		file_menu.addSeparator()

		# refresh_lib_action = QAction('&Refresh Directories', self.main_window)
		# refresh_lib_action.triggered.connect(lambda: self.lib.refresh_dir())
		add_new_files_action = QAction('&Refresh Directories', menu_bar)
		add_new_files_action.triggered.connect(lambda: self.callback_library_needed_check(self.add_new_files_callback))
		add_new_files_action.setShortcut(QtCore.QKeyCombination(QtCore.Qt.KeyboardModifier(QtCore.Qt.KeyboardModifier.ControlModifier), QtCore.Qt.Key.Key_R))
		add_new_files_action.setStatusTip("Ctrl+R")
		# file_menu.addAction(refresh_lib_action)
		file_menu.addAction(add_new_files_action)

		file_menu.addSeparator()

		file_menu.addAction(QAction('&Close Library', menu_bar))

		# Edit Menu ============================================================
		new_tag_action = QAction('New &Tag', menu_bar)
		new_tag_action.triggered.connect(lambda: self.add_tag_action_callback())
		new_tag_action.setShortcut(QtCore.QKeyCombination(QtCore.Qt.KeyboardModifier(QtCore.Qt.KeyboardModifier.ControlModifier), QtCore.Qt.Key.Key_T))
		new_tag_action.setToolTip('Ctrl+T')
		edit_menu.addAction(new_tag_action)

		edit_menu.addSeparator()

		manage_file_extensions_action = QAction('Ignore File Extensions', menu_bar)
		manage_file_extensions_action.triggered.connect(lambda: self.show_file_extension_modal())
		edit_menu.addAction(manage_file_extensions_action)

		tag_database_action = QAction('Tag Database', menu_bar)
		tag_database_action.triggered.connect(lambda: self.show_tag_database())
		edit_menu.addAction(tag_database_action)

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

		self.sort_fields_action = QAction('&Sort Fields', menu_bar)
		self.sort_fields_action.triggered.connect(lambda: (self.run_macros('sort-fields', [x[1] for x in self.selected if x[0] == ItemType.ENTRY]), self.preview_panel.update_widgets()))
		self.sort_fields_action.setShortcut(QtCore.QKeyCombination(QtCore.Qt.KeyboardModifier(QtCore.Qt.KeyboardModifier.AltModifier), QtCore.Qt.Key.Key_S))
		self.sort_fields_action.setToolTip('Alt+S')
		macros_menu.addAction(self.sort_fields_action)

		folders_to_tags_action = QAction('Folders to Tags', menu_bar)
		ftt_modal = FoldersToTagsModal(self.lib, self)
		folders_to_tags_action.triggered.connect(lambda:ftt_modal.show())
		macros_menu.addAction(folders_to_tags_action)

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
	
	def show_tag_database(self):
		self.modal = PanelModal(TagDatabasePanel(self.lib),'Tag Database', 'Tag Database', has_save=False)
		self.modal.show()
	
	def show_file_extension_modal(self):
		# self.modal = FileExtensionModal(self.lib)
		panel = FileExtensionModal(self.lib)
		self.modal = PanelModal(panel, 'Ignored File Extensions', 'Ignored File Extensions', has_save=True)
		self.modal.saved.connect(lambda: (panel.save(), self.filter_items('')))
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
	
	def run_macros(self, name: str, entry_ids: list[int]):
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
			if frame_content is not None:
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
		elif frame_content is not None:
			# If the current page is empty, don't include it in the new stack.
			if self.nav_frames and not self.nav_frames[self.cur_frame_idx].contents:
				self.nav_frames.pop()
				trimmed = True
			self.nav_frames.append(NavigationState(frame_content, 0, page_index, page_count, search_text))
			# logging.info(f'Saving Text: {search_text}')
			self.nav_frames[self.cur_frame_idx].scrollbar_pos = sb_pos
			self.cur_frame_idx += 1 if not trimmed else 0

		# if self.nav_stack[self.cur_page_idx].contents:
		if (self.cur_frame_idx != original_pos) or (frame_content is not None):
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

	def get_frame_contents(self, index=0, query: str = None):
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
