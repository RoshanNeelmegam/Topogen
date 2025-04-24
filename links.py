from PySide6.QtWidgets import QGraphicsLineItem
from PySide6.QtCore import QLineF, Qt
from PySide6.QtGui import QPen

class Link(QGraphicsLineItem):
    def __init__(self, start_node=None, end_node=None):
        super().__init__()
        if start_node == None or end_node == None:
            return ('link creation failed')
        pen = QPen(Qt.black)
        pen.setWidth(1)  
        self.setPen(pen)
        self.start_node = start_node
        self.end_node = end_node
        self.setZValue(-1) # this is to make sure the link is not above the node but rather below the node to create a connection like view
        self.update_position()

    def update_position(self):
        line = QLineF(self.start_node.boundingRect().center() + self.start_node.pos(), self.end_node.boundingRect().center() + self.end_node.pos())
        self.setLine(line) # draws the line between the set points 

    def get_endpoint(self, node):
        # returns the opposite endpoint and its connected interface
        if node == self.start_node:
            return f"{self.end_node.name}-{self.end_node.links_name[self]}"
        else:
            return f"{self.start_node.name}-{self.start_node.links_name[self]}"