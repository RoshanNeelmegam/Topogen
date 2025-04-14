from PySide6.QtWidgets import QMainWindow, QToolBar, QStatusBar, QInputDialog, QGraphicsScene, QGraphicsView, QGraphicsItemGroup, QCheckBox, QDialog, QToolButton # built in widgets 
from PySide6.QtGui import QAction, QIcon, QTransform # all gui specific 
from PySide6.QtCore import QSize, QPointF, Qt # non gui stuff
from draggable_nodes import DraggableNode
from topology_yaml import topology_yaml_constructor
from links import Link
from link_config_mode import LinkConfigDialog

connections_list = [] # keeps track of all the connections eg: node1:et1 - node2:et1
devices_list = [] # keeps track of all the devices in the topology

class MyGraphicsView(QGraphicsView):
    global connections_list

    def __init__(self, scene, is_link_mode_on):
        super().__init__(scene)
        self.setScene(scene)
        self.link_mode = is_link_mode_on
        self.link_started = False
        self.start_pos = None
        self.end_pos = None
        self.links = []
        self.link_config_mode = False
        
    def mousePressEvent(self, event):
        if self.link_mode:
            scene_pos = self.mapToScene(event.pos())
            item = self.scene().itemAt(scene_pos, QTransform())  # Use scene's itemAt
            if isinstance(item, DraggableNode) or (item and item.group() and isinstance(item.group(), DraggableNode)):
                # there's a good chance we might click on the free space between the image and the caption or on the image or the caption. The following condition deals with it
                if item.group() != None: # if clicked on child item, then we assign item to the parent (whole draggable node)
                    item = item.group()
                # print('mouse pressed')
                if not self.link_started:
                    # print('start position is set')
                    self.link_started = True
                    self.start_pos = scene_pos
                    self.start_node = item #Store the start node
                elif self.link_started and self.end_pos is None:
                    # print('end position is set')
                    self.end_pos = scene_pos
                    self.end_node = item #Store the end node
                    if not (self.start_node == self.end_node):
                        # creating a link using a link object
                        link = Link(start_node=self.start_node, end_node=self.end_node)
                        self.scene().addItem(link)
                        self.links.append(link)
                        self.end_pos = None
                        self.start_pos = None
                        self.link_started = False
                        connections_list.append(f'"{self.start_node.name}:eth{self.start_node.no_of_intfs}", "{self.end_node.name}:eth{self.end_node.no_of_intfs}"')
                        # print(connections_list)
                        self.start_node.links.append(link)
                        self.end_node.links.append(link)
                        self.start_node.links_name[link] = f"eth{self.start_node.no_of_intfs}" 
                        self.end_node.links_name[link] = f"eth{self.end_node.no_of_intfs}"
                        self.start_node.no_of_intfs +=1
                        self.end_node.no_of_intfs += 1
                    else: 
                        # this condition is important otherwise, self.end_node will always be self.start_node and loop will continue
                        self.end_node = None
                        self.end_pos = None
                return 
        elif self.link_config_mode == True:
            scene_pos = self.mapToScene(event.pos())
            item = self.scene().itemAt(scene_pos, QTransform())
            draggable_node = None
            if isinstance(item, DraggableNode):
                draggable_node = item
            elif item and item.group() and isinstance(item.group(), DraggableNode):
                draggable_node = item.group()
            if draggable_node:
                print(f"Clicked on device for link config: {draggable_node.name}")
                self.clicked_device_for_config = draggable_node
                dialog = LinkConfigDialog(draggable_node.links_name) # Instantiate the dialog
                if dialog.exec() == QDialog.Accepted:
                    configs = dialog.get_configurations()
                    print(configs)
                    print("Link configuration completed.")
                    # Retrieve configuration data from the dialog (implement methods in LinkConfigDialog)
                else:
                    print("Link configuration cancelled.")
                # self.main_window.link_config_mode = False
                self.clicked_device_for_config = None
                return


        super().mousePressEvent(event) # Call base class for other clicks

class GuiWindow(QMainWindow):
    global connections_list, devices_list

    def __init__(self):
        super().__init__()
        self.setWindowTitle('Topology and Configuration Orchestrator')
        self.resize(1400, 800)
        # setting certain parameters useful for tracking
        # self.devices = []
        self.routers_num = 0
        self.hosts_num = 0
        self.link_mode = False
        self.link_config_mode = False

        # creating a statusbar to display status related info
        self.statusBar = QStatusBar() # same as QStatusBar(self)
        self.setStatusBar(self.statusBar)
        
        # topology creation toolbar with options like add_routers, add_hosts, etc
        self.TopologyToolBar = QToolBar()
        self.TopologyToolBar.setMovable(False)
        self.TopologyToolBar.setIconSize(QSize(40, 40))
        self.addToolBar(self.TopologyToolBar)

        # topology creation toolbar Options
        self.add_routers_action = QAction(QIcon("/Users/roshan/Desktop/Dev/Bits_Project/Main/router-icon.png"), "Add Routers/Switches", self)
        self.add_routers_action.setStatusTip("Add Router/Switches into your topology")
        self.add_routers_action.triggered.connect(self.add_routers_handler)
        self.TopologyToolBar.addAction(self.add_routers_action)

        self.add_hosts_action = QAction(QIcon('/Users/roshan/Desktop/Dev/Bits_Project/Main/server-icon.png'), 'Add Hosts', self)
        self.add_hosts_action.setStatusTip('Add Hosts into your topology')
        self.add_hosts_action.triggered.connect(self.add_hosts_handler)
        self.TopologyToolBar.addAction(self.add_hosts_action)

        self.link_mode_action = QAction(QIcon('/Users/roshan/Desktop/Dev/Bits_Project/Main/connection-icon.png'), 'Link Mode', self)
        self.link_mode_action.setStatusTip('Select two devices and add links between them')
        self.link_mode_action.triggered.connect(self.link_mode_action_handler)
        self.TopologyToolBar.addAction(self.link_mode_action)

        self.submit_button = QAction(QIcon('/Users/roshan/Desktop/Dev/Bits_Project/Main/submit-icon.png'), 'Submit', self)
        self.submit_button.setStatusTip('Get the topology.yaml file')
        self.submit_button.triggered.connect(self.generate_topology_file)
        self.TopologyToolBar.addAction(self.submit_button)

        self.provision_toggle_button = QToolButton()
        self.provision_toggle_button.setCheckable(True)
        self.provision_toggle_button.setText("Provision Devices")
        self.provision_toggle_button.setStyleSheet("""
            QToolButton {
                background-color: lightgray;
                border: 1px solid gray;
                border-radius: 5px;
                padding: 5px 10px;
            }
            QToolButton:checked {
                background-color: green;
                color: white;
            }
        """)
        self.provision_toggle_button.toggled.connect(self.toggle_switched)
        self.TopologyToolBar.addWidget(self.provision_toggle_button)

        # provisioning toobar 
        self.ProvisionToolBar = QToolBar()
        self.ProvisionToolBar.setMovable(False)
        self.ProvisionToolBar.setIconSize(QSize(40, 40))
        self.addToolBarBreak(Qt.TopToolBarArea)
        self.ProvisionToolBar.setVisible(False)
        self.addToolBar(Qt.TopToolBarArea, self.ProvisionToolBar)

        # link-config action
        self.link_config_action = QAction("Link Config", self)
        self.link_config_action.triggered.connect(self.handle_link_config)
        self.ProvisionToolBar.addAction(self.link_config_action)
        
         # Graphics Items are placed in a canvas called scene and the camera or view is placed in front of the scene
        self.scene = QGraphicsScene(self)
        self.view = MyGraphicsView(self.scene, False)
        self.setCentralWidget(self.view)

    def add_routers_handler(self):
        no_of_routers, ok_status = QInputDialog.getInt(self, "Routers", "Enter the number or routers:", 1, 1, 50)
        if ok_status:
            for i in range(no_of_routers):
                router = DraggableNode(image_path="/Users/roshan/Desktop/Dev/Bits_Project/Main/router.png", name=f"Node{i+1+self.routers_num}", device_type="router", position=QPointF(i * 80, 50))
                self.scene.addItem(router)
                devices_list.append(router)
            self.routers_num += no_of_routers

    def add_hosts_handler(self):
        no_of_hosts, ok_status = QInputDialog.getInt(self, "Hosts", "Enter the number or hosts:", 1, 1, 50)
        if ok_status:
            for i in range(no_of_hosts):
                host = DraggableNode(image_path="/Users/roshan/Desktop/Dev/Bits_Project/Main/server.png", name=f"Host{i+1+self.hosts_num}",device_type="host", position=QPointF(i * 80, 50))
                self.scene.addItem(host)
                devices_list.append(host)
            self.hosts_num += no_of_hosts

    def link_mode_action_handler(self):
        if self.link_mode == False:
            self.link_mode = True
            # change icon if triggered
            self.link_mode_action.setIcon(QIcon('/Users/roshan/Desktop/Dev/Bits_Project/Main/connection-icon-colored.png'))
            for device in devices_list:
                device.setFlags(~QGraphicsItemGroup.ItemIsMovable)
                device.link_mode = True
            self.view.link_mode=True
        else: 
            for device in devices_list:
                device.setFlags(QGraphicsItemGroup.ItemIsMovable | QGraphicsItemGroup.ItemIsSelectable)
                device.link_mode = False
            self.link_mode = False
            self.link_mode_action.setIcon(QIcon('/Users/roshan/Desktop/Dev/Bits_Project/Main/connection-icon.png'))
            self.view.link_mode=False

    def generate_topology_file(self):
        topology = topology_yaml_constructor(connection_list=connections_list, devices_dict=devices_list)
        print(topology.yaml_file_generator())

    def toggle_switched(self, checked):
        self.ProvisionToolBar.setVisible(checked)
        print('ProvisionToolBar shown' if checked else 'ProvisionToolBar hidden')

    def handle_link_config(self):
        if self.link_config_mode == False:
            self.link_config_mode = True
            self.view.link_config_mode=True
            for device in devices_list:
                device.setFlags(~QGraphicsItemGroup.ItemIsMovable)
                device.link_mode = True
        else:
            self.link_config_mode = False
            self.view.link_config_mode = False
            for device in devices_list:
                device.setFlags(QGraphicsItemGroup.ItemIsMovable | QGraphicsItemGroup.ItemIsSelectable)
                device.link_mode = False



### 
# Icons Attribution:
# <a href="https://www.flaticon.com/free-icons/hub" title="hub icons">Hub icons created by Freepik - Flaticon</a> 
# <a href="https://www.flaticon.com/free-icons/server" title="server icons">Server icons created by smashingstocks - Flaticon</a>
# <a href="https://www.flaticon.com/free-icons/network-switch" title="network switch icons">Network switch icons created by Chattapat - Flaticon</a>
# <a href="https://www.flaticon.com/free-icons/server" title="server icons">Server icons created by Roundicons - Flaticon</a>
# <a href="https://www.flaticon.com/free-icons/no-connection" title="no connection icons">No connection icons created by Freepik - Flaticon</a>
###