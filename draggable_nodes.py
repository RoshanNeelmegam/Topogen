from PySide6.QtWidgets import QGraphicsItemGroup, QGraphicsPixmapItem, QGraphicsTextItem, QInputDialog
from PySide6.QtGui import QPixmap, QMouseEvent
from PySide6.QtCore import Qt

class DraggableNode(QGraphicsItemGroup):

    ''' This class utilizes QGraphicsItemGroup which essential groups itself 
        and all the children items as one. This is useful here since we want 
        therouter/host image grouped with the caption at all times '''
    
    def __init__(self, image_path, name, device_type, position):
        super().__init__()
        # Making sure the Graphics group is movable and selectable
        self.setFlags(QGraphicsItemGroup.ItemIsMovable | QGraphicsItemGroup.ItemIsSelectable)
        self.setAcceptHoverEvents(True)  
        self.setAcceptedMouseButtons(Qt.NoButton)
        self.link_mode = False
        self.name = name
        self.device_type = device_type
        self.no_of_intfs = 1
        self.links = []

        # Image that either represets a router or a host
        self.image_item = QGraphicsPixmapItem(QPixmap(image_path).scaled(60, 60))

        # Caption 
        self.text_item = QGraphicsTextItem(self.name)
        self.text_item.setDefaultTextColor(Qt.black)

        # Get bounding rectangle of the image to determine its size and position the text below the image accordingly
        image_rect = self.image_item.boundingRect()
        self.text_item.setPos(image_rect.width() / 2 - self.text_item.boundingRect().width() / 2, image_rect.height() + 5)

       # Adding both the Graphics items to the group
        self.addToGroup(self.image_item)
        self.addToGroup(self.text_item)

        # Set an initial position that's random
        self.setPos(position)


    def mouseDoubleClickEvent(self, event):
        if self.link_mode is False:
            ''' Open a dialog to rename the node when double-clicked '''
            new_name, ok = QInputDialog.getText(None, "Rename Device", "Enter new device name:")
            if ok and new_name:
                self.text_item.setPlainText(new_name)  # updating the caption
                image_rect = self.image_item.boundingRect()
                self.text_item.setPos(image_rect.width() / 2 - self.text_item.boundingRect().width() / 2, image_rect.height() + 5)
                self.name = new_name


    def mouseReleaseEvent(self, event):
        ''' On mouse release after dragging, update the links position which are connected to this device
            which makes sure when the nodes move, the links connected to it moves as well'''
        super().mouseReleaseEvent(event)
        for link in self.links:
            link.update_position()   

