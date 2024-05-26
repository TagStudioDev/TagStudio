from PySide6.QtWidgets import QPushButton


class CustomQPushButton(QPushButton):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_connected = False
