from PySide6.QtWidgets import QHBoxLayout, QPushButton
from src.qt.widgets.fields import FieldWidget

class RatingWidget(FieldWidget):
    def __init__(self, title):
        super().__init__(title)
        self.layout = QHBoxLayout()
        self.layout.setSpacing(0)
        self.setLayout(self.layout)
        self.setObjectName("ratingBox")
        self.setStyleSheet("QPushButton{ color: gray; background-color: transparent; border: none;}")
        self.stars = []
        for star in range(5):
            star = QPushButton("⭐")
            star.setCheckable(True)
            star.clicked.connect(self.set_rating)
            star.setStyleSheet("font-size: 30px;") 
            star.setFixedSize(24, 24)
            self.stars.append(star)
            self.layout.addWidget(star)
    def set_rating(self, rating_index: int = None):
        rating_index = rating_index if rating_index is None else self.stars.index(self.sender())
        for star in range(rating_index + 1):
            self.stars[star].setStyleSheet("font-weight: bold; font-size: 20px;")
        for star in range(rating_index + 1, len(self.stars)):
            self.stars[star].setStyleSheet("font-size: 30px;") 
        rating_indexs += 1
    # def modify_stars(self, totalstars):
        # for star in self.stars:
            # star.deleteLater()
        # self.stars.clear()
        # for star in range(totalstars):
            # star = QPushButton("⭐")
            # star.setCheckable(True)
            # star.clicked.connect(self.set_rating)
            # star.setStyleSheet("font-size: 30px;")
            # star.setFixedSize(24, 24)
            # self.stars.append(star)
            # self.layout.addWidget(star)
    # Used to change amount of stars to a 10 star system
