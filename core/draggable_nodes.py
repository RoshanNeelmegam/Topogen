from PySide6.QtWidgets import QGraphicsItemGroup, QGraphicsPixmapItem, QGraphicsTextItem, QInputDialog
from PySide6.QtGui import QPixmap, QMouseEvent
from PySide6.QtCore import Qt

class DraggableNode(QGraphicsItemGroup):

    ''' This class utilizes QGraphicsItemGroup which essential groups itself 
        and all the children items as one. This is useful here since we want 
        the router/host image grouped with the caption at all times '''
    
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
        self.links_name = {}
        self.base_yaml_file_created = False

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
                self.text_item.setPlainText(new_name)  # Updating the caption
                image_rect = self.image_item.boundingRect()
                self.text_item.setPos(image_rect.width() / 2 - self.text_item.boundingRect().width() / 2, image_rect.height() + 5)
                self.name = new_name

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        for link in self.links:
            link.update_position()

    def delete_connection(self, connection) -> None:
        # Removing the link from the links_name dict and the links list
        self.links_name.pop(connection)
        self.links.remove(connection)
        # Updating the new value for the no of interfaces the device has post deleting the links
        self.no_of_intfs = len(list(self.links_name.keys())) + 1
        # Reassining the interaace numbers to ensure uniformity and ascending order
        intf_num = 1
        for link in self.links_name:
            self.links_name[link] = intf_num
            intf_num += 1

        