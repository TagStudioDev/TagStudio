import os
import logging
from PySide6.QtWidgets import QLabel

class FileOpenerLabel(QLabel):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)

    def setFilePath(self, filepath):
        self.filepath = filepath
    
    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        #open file
        if hasattr(self, 'filepath'):
            if os.path.exists(self.filepath):
                os.startfile(self.filepath)
                logging.info(f'Opening file: {self.filepath}')
            else:
                logging.error(f'File not found: {self.filepath}')