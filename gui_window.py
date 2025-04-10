from PySide6.QtWidgets import QMainWindow, QToolBar, QStatusBar, QInputDialog, QGraphicsScene, QGraphicsView, QGraphicsItemGroup # built in widgets 
from PySide6.QtGui import QAction, QIcon, QTransform # all gui specific 
from PySide6.QtCore import QSize, QPointF # non gui stuff
from draggable_nodes import DraggableNode
from topology_yaml import topology_yaml_constructor
from links import Link

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
        
    def mousePressEvent(self, event):
        if self.link_mode:
            scene_pos = self.mapToScene(event.pos())
            item = self.scene().itemAt(scene_pos, QTransform())
            if isinstance(item, DraggableNode):
                print('mouse pressed')
                if not self.link_started:
                    print('start position is set')
                    self.link_started = True
                    self.start_pos = scene_pos
                    self.start_node = item #Store the start node
                elif self.link_started and self.end_pos is None:
                    print('end position is set')
                    self.end_pos = scene_pos
                    self.end_node = item #Store the end node
                    if not (self.start_node == self.end_node):
                        #Create the link using the nodes positions.
                        start_center = self.start_node.boundingRect().center() + self.start_node.pos()
                        end_center = self.end_node.boundingRect().center() + self.end_node.pos()
                        link = Link(x1=start_center.x(), y1=start_center.y(), x2=end_center.x(), y2=end_center.y())
                        link.setZValue(-1)  # Set the z-value to a lower value
                        self.scene().addItem(link)
                        self.links.append(link)
                        self.end_pos = None
                        self.start_pos = None
                        self.link_started = False
                        connections_list.append(f'"{self.start_node.name}:eth{self.start_node.no_of_intfs}", "{self.end_node.name}:eth{self.end_node.no_of_intfs}"')
                        self.start_node.no_of_intfs +=1
                        self.end_node.no_of_intfs += 1
                        print(connections_list)
                    else: 
                        # This condition is important otherwise, self.end_node will always be self.start_node and loop will continue
                        self.end_node = None
                        self.end_pos = None
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

        # Creating a statusbar to display status related info
        self.statusBar = QStatusBar() # same as QStatusBar(self)
        self.setStatusBar(self.statusBar)
        
        # Topology Creation Toolbar with options like add_routers, add_hosts, etc
        self.TopologyToolBar = QToolBar()
        self.TopologyToolBar.setMovable(False)
        self.TopologyToolBar.setIconSize(QSize(40, 40))
        self.addToolBar(self.TopologyToolBar)

        # Topology Creation Toolbar Options
        add_routers = QAction(QIcon("/Users/roshan/Desktop/Dev/Bits_Project/Main/router-icon.png"), "Add Routers/Switches", self)
        add_routers.setStatusTip("Add Router/Switches into your topology")
        add_routers.triggered.connect(self.add_routers_prompt)
        self.TopologyToolBar.addAction(add_routers)

        add_hosts = QAction(QIcon('/Users/roshan/Desktop/Dev/Bits_Project/Main/server-icon.png'), 'Add Hosts', self)
        add_hosts.setStatusTip('Add Hosts into your topology')
        add_hosts.triggered.connect(self.add_hosts_prompt)
        self.TopologyToolBar.addAction(add_hosts)

        link_mode = QAction('Add links', self)
        link_mode.setStatusTip('Select two devices and add links between them')
        link_mode.triggered.connect(self.link_mode_action)
        self.TopologyToolBar.addAction(link_mode)

        submit_button = QAction('Submit', self)
        submit_button.setStatusTip('Get the topology.yaml file')
        submit_button.triggered.connect(self.generate_topology_file)
        self.TopologyToolBar.addAction(submit_button)

        # Graphics Items are placed in a canvas called scene and the camera or view is placed in front of the scene
        self.scene = QGraphicsScene(self)
        self.view = MyGraphicsView(self.scene, False)
        self.setCentralWidget(self.view)

    def add_routers_prompt(self):
        no_of_routers, ok_status = QInputDialog.getInt(self, "Routers", "Enter the number or routers:", 1, 1, 50)
        if ok_status:
            for i in range(no_of_routers):
                router = DraggableNode(image_path="/Users/roshan/Desktop/Dev/Bits_Project/Main/router.png", name=f"Node{i+1+self.routers_num}", device_type="router", position=QPointF(i * 80, 50))
                self.scene.addItem(router)
                devices_list.append(router)
            self.routers_num += no_of_routers

    def add_hosts_prompt(self):
        no_of_hosts, ok_status = QInputDialog.getInt(self, "Hosts", "Enter the number or hosts:", 1, 1, 50)
        if ok_status:
            for i in range(no_of_hosts):
                host = DraggableNode(image_path="/Users/roshan/Desktop/Dev/Bits_Project/Main/server.png", name=f"Host{i+1+self.hosts_num}",device_type="host", position=QPointF(i * 80, 50))
                self.scene.addItem(host)
                devices_list.append(host)
            self.hosts_num += no_of_hosts

    def link_mode_action(self):
        if self.link_mode == False:
            self.link_mode = True
            for device in devices_list:
                device.setFlags(~QGraphicsItemGroup.ItemIsMovable)
                device.link_mode = True
            self.view.link_mode=True
        else: 
            for device in devices_list:
                device.setFlags(QGraphicsItemGroup.ItemIsMovable | QGraphicsItemGroup.ItemIsSelectable)
                device.link_mode = False
            self.link_mode = False
            self.view.link_mode=False

    def generate_topology_file(self):
        topology = topology_yaml_constructor(connection_list=connections_list, devices_dict=devices_list)
        print(topology.yaml_file_generator())

  


















### 
# Icons Attribution:
# <a href="https://www.flaticon.com/free-icons/hub" title="hub icons">Hub icons created by Freepik - Flaticon</a> 
# <a href="https://www.flaticon.com/free-icons/server" title="server icons">Server icons created by smashingstocks - Flaticon</a>
# <a href="https://www.flaticon.com/free-icons/network-switch" title="network switch icons">Network switch icons created by Chattapat - Flaticon</a>
# <a href="https://www.flaticon.com/free-icons/server" title="server icons">Server icons created by Roundicons - Flaticon</a>
###
