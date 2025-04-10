from PySide6.QtWidgets import QGraphicsLineItem
from PySide6.QtCore import QLineF

class Link(QGraphicsLineItem):
    def __init__(self, x1, y1, x2, y2):
        super().__init__()
        self.setLine(QLineF(x1, y1, x2, y2))