from PySide6.QtWidgets import QGraphicsLineItem
from PySide6.QtCore import QLineF, Qt, QPointF
from PySide6.QtGui import QPen
import math

class Link(QGraphicsLineItem):

    ''' This class creates a link object derived using the QGraphicsLineItem to draw a line
        between two set points, with a couple other properties/methods as well '''

    def __init__(self, start_node=None, end_node=None):
        super().__init__()
        if start_node == None or end_node == None:
            return ('link creation failed')
        pen = QPen(Qt.black)
        pen.setWidth(1)  
        self.setPen(pen)
        self.start_node = start_node
        self.end_node = end_node
        self.setZValue(-1) # This is to make sure the link is not above the node but rather below the node to create a connection like view
        self.offset = 0
        self.update_position()

    def update_position(self) -> None:
        start = self.start_node.boundingRect().center() + self.start_node.pos()
        end = self.end_node.boundingRect().center() + self.end_node.pos()

        dx = end.x() - start.x()
        dy = end.y() - start.y()
        length = math.hypot(dx, dy)

        if length == 0:
            return  # Avoid divide-by-zero

        # Perpendicular unit vector
        perp_dx = -dy / length
        perp_dy = dx / length

        # Multiply by offset
        offset_vector = QPointF(perp_dx * self.offset, perp_dy * self.offset)

        # Apply offset to both ends
        start += offset_vector
        end += offset_vector

        self.setLine(QLineF(start, end))

    def get_endpoint(self, node) -> str:
        ''' This function returns the endpoint and the interface for a node '''
        if node == self.start_node:
            return f"{self.end_node.name}-{self.end_node.links_name[self]}"
        else:
            return f"{self.start_node.name}-{self.start_node.links_name[self]}"
        
    def get_other_end_device(self, node):
        ''' This function returns the endpoint (draggable node)'''
        if node == self.start_node:
            return self.end_node
        else:
            return self.start_node