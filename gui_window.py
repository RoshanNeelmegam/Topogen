import os, uuid, paramiko, tempfile, subprocess
from PySide6.QtWidgets import QMainWindow, QToolBar, QStatusBar, QInputDialog, QGraphicsScene, QGraphicsView, QGraphicsItemGroup, QComboBox, QDialog, QToolButton, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit, QDialogButtonBox, QApplication, QRadioButton, QLineEdit # built in widgets 
from PySide6.QtGui import QAction, QIcon, QTransform, QPainter # all gui specific 
from PySide6.QtCore import QSize, QPointF, Qt # non gui stuff
from draggable_nodes import DraggableNode
from topology_yaml import topology_yaml_constructor
from links import Link
from device_provisioning import load_device_yaml, save_device_yaml, update_yaml_field
from config_creator.link_config_mode import LinkConfigDialog
from config_creator.mlag_config_mode import MlagConfigDialog
from config_creator.bgp_config_mode import BgpConfigDialog
from config_creator.vxlan_config_mode import VxlanConfigDialog

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
        self.mlag_config_mode = False
        self.bgp_config_mode = False
        self.vxlan_config_mode = False
        self.config_dir = None
        
    def mousePressEvent(self, event):

        if self.link_mode:
            scene_pos = self.mapToScene(event.pos())
            item = self.scene().itemAt(scene_pos, QTransform()) 
            if isinstance(item, DraggableNode) or (item and item.group() and isinstance(item.group(), DraggableNode)):
                # there's a good chance we might click on the free space between the image and the caption or on the image or the caption. The following condition deals with it
                if item.group() != None: # if clicked on child item, then we assign item to the parent (whole draggable node)
                    item = item.group()
                if not self.link_started:
                    self.link_started = True
                    self.start_pos = scene_pos
                    self.start_node = item 
                elif self.link_started and self.end_pos is None:
                    self.end_pos = scene_pos
                    self.end_node = item 
                    if not (self.start_node == self.end_node):
                        # creating a link using a link object
                        link = Link(start_node=self.start_node, end_node=self.end_node)
                        self.scene().addItem(link)
                        self.links.append(link)
                        self.end_pos = None
                        self.start_pos = None
                        self.link_started = False
                        connections_list.append(f'"{self.start_node.name}:eth{self.start_node.no_of_intfs}", "{self.end_node.name}:eth{self.end_node.no_of_intfs}"')
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
                # in case of GraphicsItemsGroup being clicked
                draggable_node = item
            elif item and item.group() and isinstance(item.group(), DraggableNode):
                # in case of GraphicsItem being clicked
                draggable_node = item.group()
            if draggable_node:
                dialog = LinkConfigDialog(draggable_node) # creating a dialog with all the configurable parameters required to configure the link 
                if dialog.exec() == QDialog.Accepted:
                    configs = dialog.get_configurations()
                    self.update_device_config(draggable_node.name, ['configs', 'interfaces'], configs)
                return
        elif self.mlag_config_mode == True:
            scene_pos = self.mapToScene(event.pos())
            item = self.scene().itemAt(scene_pos, QTransform())
            draggable_node = None
            if isinstance(item, DraggableNode):
                # in case of GraphicsItemsGroup being clicked
                draggable_node = item
            elif item and item.group() and isinstance(item.group(), DraggableNode):
                # in case of GraphicsItem being clicked
                draggable_node = item.group()
            if draggable_node:
                dialog = MlagConfigDialog(draggable_node, devices_list)
                if dialog.exec() == QDialog.Accepted:
                    device1_config, device2, device2_config = dialog.get_config()
                    self.update_device_config(draggable_node.name, ['configs', 'mlag'], device1_config) # update device 1 config for mlag
                    self.update_device_config(device2.name, ['configs', 'mlag'], device2_config) # update device 2 config for mlag
                return
        elif self.bgp_config_mode == True:
            scene_pos = self.mapToScene(event.pos())
            item = self.scene().itemAt(scene_pos, QTransform())
            draggable_node = None
            if isinstance(item, DraggableNode):
                # in case of GraphicsItemsGroup being clicked
                draggable_node = item
            elif item and item.group() and isinstance(item.group(), DraggableNode):
                # in case of GraphicsItem being clicked
                draggable_node = item.group()
            dialog = BgpConfigDialog(draggable_node)
            if dialog.exec() == QDialog.Accepted:
                bgp_config = dialog.get_config()
                self.update_device_config(draggable_node.name, ['configs', 'bgp'], bgp_config)
            return
        elif self.vxlan_config_mode == True:
            scene_pos = self.mapToScene(event.pos())
            item = self.scene().itemAt(scene_pos, QTransform())
            draggable_node = None
            if isinstance(item, DraggableNode):
                # in case of GraphicsItemsGroup being clicked
                draggable_node = item
            elif item and item.group() and isinstance(item.group(), DraggableNode):
                # in case of GraphicsItem being clicked
                draggable_node = item.group()
            if draggable_node:
                dialog = VxlanConfigDialog(draggable_node)
                if dialog.exec() == QDialog.Accepted:
                    config = dialog.get_config()
                    self.update_device_config(draggable_node.name, ['configs', 'vxlan'], config)
                return

        super().mousePressEvent(event) # calling base class for other clicks

    def update_device_config(self, device_name, key_path, data_from_dialogue):
        # takes in the data received from the dialouge and adds it to the correcponding key path
        file_path = os.path.join(self.config_dir, f"{device_name}.yml") # getting the device.yml file path
        data = load_device_yaml(file_path) # loading the yaml file
        update_yaml_field(data, key_path, data_from_dialogue) # updating the required key with the values in yaml
        save_device_yaml(file_path, data) 

class GuiWindow(QMainWindow):
    global connections_list, devices_list

    def __init__(self):
        super().__init__()
        self.setWindowTitle('Topology and Configuration Orchestrator')
        self.resize(1400, 800)
        # setting certain parameters useful for tracking
        self.routers_num = 0
        self.hosts_num = 0
        self.link_mode = False
        self.link_config_mode = False
        self.switch_image = "ceosimage:4.32.2F" # setting default os version for switch and host
        self.host_image = "ceosimage:4.32.2F"
        self.server_ip = '192.168.1.16'
        self.server_user = 'root'
        self.server_password = 'root$#123'
        self.server_port = '8888'
        self.provisioning_dir_created = False

        # creating a statusbar to display status related info
        self.statusBar = QStatusBar() # same as QStatusBar(self)
        self.setStatusBar(self.statusBar)
        
        # topology creation toolbar with options like add_routers, add_hosts, etc
        self.TopologyToolBar = QToolBar()
        self.TopologyToolBar.setMovable(False)
        self.TopologyToolBar.setIconSize(QSize(40, 40))
        self.TopologyToolBar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon) 
        self.addToolBar(self.TopologyToolBar)

        # topology creation toolbar Options
        self.add_routers_action = QAction(QIcon("Main/icons/router-icon.png"), "Add Routers", self)
        self.add_routers_action.setStatusTip("Add Router/Switches into your topology")
        self.add_routers_action.triggered.connect(self.add_routers_handler)
        self.TopologyToolBar.addAction(self.add_routers_action)

        self.add_hosts_action = QAction(QIcon('Main/icons/server-icon.png'), 'Add Hosts', self)
        self.add_hosts_action.setStatusTip('Add Hosts into your topology')
        self.add_hosts_action.triggered.connect(self.add_hosts_handler)
        self.TopologyToolBar.addAction(self.add_hosts_action)

        self.link_mode_action = QAction(QIcon('Main/icons/connection-icon.png'), 'Link Mode', self)
        self.link_mode_action.setStatusTip('Select two devices and add links between them')
        self.link_mode_action.triggered.connect(self.link_mode_action_handler)
        self.TopologyToolBar.addAction(self.link_mode_action)

        self.select_os_action = QAction(QIcon('Main/icons/os-selector-icon.png'), 'Select Image', self)
        self.select_os_action.setStatusTip('Select the image to run on the devices')
        self.select_os_action.triggered.connect(self.select_os_handler)
        self.TopologyToolBar.addAction(self.select_os_action)

        self.get_yaml_file_action = QAction(QIcon('Main/icons/get-file.png'), 'Get Toplogy File', self)
        self.get_yaml_file_action.setStatusTip('Get the topology.yaml file')
        self.get_yaml_file_action.triggered.connect(self.generate_topology_file)
        self.TopologyToolBar.addAction(self.get_yaml_file_action)
        
        self.deploy_action = QAction(QIcon('Main/icons/deploy-lab-icon.png'), 'Deploy Lab', self)
        self.deploy_action.setStatusTip('Deploy topology locally or remotely')
        self.deploy_action.triggered.connect(self.deploy_lab_handler)
        self.TopologyToolBar.addAction(self.deploy_action)

        self.save_config_action = QAction(QIcon('Main/icons/save-config.png'), 'Save Config', self)
        self.save_config_action.setStatusTip('Save Configs (saves on the remote server)')
        self.save_config_action.triggered.connect(self.save_config_handler)
        self.TopologyToolBar.addAction(self.save_config_action)

        self.destroy_action = QAction(QIcon('Main/icons/destroy-lab-icon.png'), 'Destroy Lab', self)  
        self.destroy_action.setStatusTip('Destroy the deployed lab (currenly works only for remote deployment)')
        self.destroy_action.triggered.connect(self.destroy_lab_handler)
        self.TopologyToolBar.addAction(self.destroy_action)

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
        self.provision_toggle_button.toggled.connect(self.provision_toolbar_toggle_handler)
        self.TopologyToolBar.addWidget(self.provision_toggle_button)

        # provisioning toobar 
        self.ProvisionToolBar = QToolBar()
        self.ProvisionToolBar.setMovable(False)
        self.ProvisionToolBar.setIconSize(QSize(40, 40))
        self.addToolBarBreak(Qt.TopToolBarArea)
        self.ProvisionToolBar.setVisible(False)
        self.addToolBar(Qt.TopToolBarArea, self.ProvisionToolBar)

        # link config button
        self.link_config_btn = self.create_provision_button("Link Config", self.handle_link_config)
        self.ProvisionToolBar.addWidget(self.link_config_btn)

        # mlag config button
        self.mlag_config_btn = self.create_provision_button("Mlag Config", self.handle_mlag_config)
        self.ProvisionToolBar.addWidget(self.mlag_config_btn)

        # bgp config button
        self.bgp_config_btn = self.create_provision_button("BGP Config", self.handle_bgp_config)
        self.ProvisionToolBar.addWidget(self.bgp_config_btn)

        # vxlan config button
        self.vxlan_config_btn = self.create_provision_button("Vxlan Config", self.handle_vxlan_config)
        self.ProvisionToolBar.addWidget(self.vxlan_config_btn)

         # Graphics Items are placed in a canvas called scene and the camera or view is placed in front of the scene
        self.scene = QGraphicsScene(self)
        self.view = MyGraphicsView(self.scene, False)
        self.view.setRenderHint(QPainter.Antialiasing)
        self.setCentralWidget(self.view)

    def create_provision_button(self, name, handler):
        button = QToolButton()
        button.setText(name)
        button.setCheckable(True)
        button.setAutoExclusive(False)  # Set True if you want only one button active at a time
        button.setStyleSheet("""
            QToolButton {
                background-color: lightgray;
                padding: 6px 12px;
                border: 1px solid #aaa;
                border-radius: 5px;
            }
            QToolButton:checked {
                background-color: #0078d7;
                color: white;
            }
        """)
        button.clicked.connect(handler)
        return button

    def add_routers_handler(self):
        no_of_routers, ok_status = QInputDialog.getInt(self, "Routers", "Enter the number or routers:", 1, 1, 50)
        if ok_status:
            for i in range(no_of_routers):
                router = DraggableNode(image_path="Main/icons/router.png", name=f"Node{i+1+self.routers_num}", device_type="router", position=QPointF(i * 80, 50))
                self.scene.addItem(router)
                devices_list.append(router)
            self.routers_num += no_of_routers

    def add_hosts_handler(self):
        no_of_hosts, ok_status = QInputDialog.getInt(self, "Hosts", "Enter the number or hosts:", 1, 1, 50)
        if ok_status:
            for i in range(no_of_hosts):
                host = DraggableNode(image_path="Main/icons/server.png", name=f"Host{i+1+self.hosts_num}",device_type="host", position=QPointF(i * 80, 50))
                self.scene.addItem(host)
                devices_list.append(host)
            self.hosts_num += no_of_hosts

    def link_mode_action_handler(self):
        if self.link_mode == False:
            self.link_mode = True
            # change icon if triggered
            self.link_mode_action.setIcon(QIcon('Main/icons/connection-icon-colored.png'))
            for device in devices_list:
                device.setFlags(~QGraphicsItemGroup.ItemIsMovable)
                device.link_mode = True
            self.view.link_mode=True
        else: 
            for device in devices_list:
                device.setFlags(QGraphicsItemGroup.ItemIsMovable | QGraphicsItemGroup.ItemIsSelectable)
                device.link_mode = False
            self.link_mode = False
            self.link_mode_action.setIcon(QIcon('Main/icons/connection-icon.png'))
            self.view.link_mode=False

    def select_os_handler(self):
        popup_window = QDialog(self)
        popup_window.setWindowTitle("Select Image")
        vertical_layout = QVBoxLayout()
        # adding the dropdown 
        self.node_os_dropdown = QComboBox()
        self.node_os_dropdown.addItems(["ceosimage:4.32.2F", "ceosimage:4.33.2F"])
        self.node_os_dropdown.setFixedWidth(150)
        self.host_os_dropdown = QComboBox()
        self.host_os_dropdown.addItems(["ceosimage:4.32.2F", "ceosimage:4.33.2F", "linux:alpine", "ubuntu:22.04", "debian:latest"])
        self.host_os_dropdown.setFixedWidth(150)
        vertical_layout.addWidget(QLabel("Switch OS:"))
        vertical_layout.addWidget(self.node_os_dropdown)
        vertical_layout.addWidget(QLabel("Host OS:"))
        vertical_layout.addWidget(self.host_os_dropdown)       
        popup_window.setLayout(vertical_layout)
        # adding the ok and cancel button
        button_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        cancel_button = QPushButton("Cancel")
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        vertical_layout.addLayout(button_layout)
        popup_window.setLayout(vertical_layout)
        ok_button.clicked.connect(popup_window.accept)
        cancel_button.clicked.connect(popup_window.reject)
        if popup_window.exec() == QDialog.Accepted:
            self.switch_image = self.node_os_dropdown.currentText()
            self.host_image = self.host_os_dropdown.currentText()

    def generate_topology_file(self):
        topology = topology_yaml_constructor(
            connection_list=connections_list,
            devices_dict=devices_list,
            switch_image=self.switch_image,
            host_image=self.host_image
        )
        self.yaml_output = topology.yaml_file_generator()

        # Create popup dialog
        popup = QDialog(self)
        popup.setWindowTitle("Generated Topology YAML")
        popup.resize(600, 500)
        layout = QVBoxLayout(popup)
        # adding a text box with the yaml output
        text_edit = QTextEdit()
        text_edit.setText(self.yaml_output)
        layout.addWidget(text_edit)
        # creating a copy button
        button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        copy_button = QPushButton("Copy")
        layout.addWidget(copy_button)
        layout.addWidget(button_box)
        # copying to clipboard functionality
        copy_button.clicked.connect(lambda: QApplication.clipboard().setText(text_edit.toPlainText()))
        button_box.accepted.connect(popup.accept)
        popup.setLayout(layout)
        popup.exec()

    def provision_toolbar_toggle_handler(self, checked):
        self.ProvisionToolBar.setVisible(checked)
        # turning off link mode if left out accidently, otherwise would lead to issues
        self.link_mode = False
        self.view.link_mode=False
        self.link_mode_action.setIcon(QIcon('Main/icons/connection-icon.png'))
        for device in devices_list:
            device.setFlags(QGraphicsItemGroup.ItemIsMovable | QGraphicsItemGroup.ItemIsSelectable)
            device.link_mode = False
        if checked:
            for device in devices_list:
                device.setFlags(~QGraphicsItemGroup.ItemIsMovable)
                device.link_mode = True
            if self.provisioning_dir_created == False:
                # creating a unique folder if it not exits for the current session
                session_id = str(uuid.uuid4())[:8]
                self.config_dir = f"device_configs_{session_id}"
                self.view.config_dir = self.config_dir
                os.makedirs(self.config_dir, exist_ok=True)
                self.statusBar.showMessage(f"Provisioning started, configs saved to {self.config_dir}", 5000)
                self.provisioning_dir_created = True
            # creating a base yaml file for each device in the topology if not created already
            for device in devices_list:
                if device.base_yaml_file_created == False:
                    device_file = os.path.join(self.config_dir, f"{device.name}.yml") # joins our file name with the directory path
                    base_yaml = {
                        'name': device.name,
                        'type': device.device_type,
                        'configs': {
                            'interfaces': [],
                            'mlag': {},
                            'bgp': {},
                            'vxlan': {}
                        }
                    }
                    save_device_yaml(device_file, base_yaml)
                    device.base_yaml_file_created = True
        elif not checked:
            self.view.link_config_mode = False
            self.view.mlag_config_mode = False
            self.view.bgp_config_mode = False
            self.view.vxlan_config_mode = False
            for device in devices_list:
                device.setFlags(QGraphicsItemGroup.ItemIsMovable | QGraphicsItemGroup.ItemIsSelectable)
                device.link_mode = False
            self.statusBar.showMessage("Provisioning toolbar hidden", 3000)

    def deploy_lab_handler(self):
        popup = QDialog(self)
        popup.setWindowTitle("Deploy Topology")
        layout = QVBoxLayout()
        # radio buttons for local and remote deployment options
        local_radio = QRadioButton("Local")
        remote_radio = QRadioButton("Remote")
        local_radio.setChecked(True)
        radio_layout = QHBoxLayout()
        radio_layout.addWidget(local_radio)
        radio_layout.addWidget(remote_radio)
        layout.addLayout(radio_layout)
        # if remote deployment is selected, need to get the following parameters from users
        remote_ip = QLineEdit()
        remote_user = QLineEdit()
        remote_password = QLineEdit()
        remote_password.setEchoMode(QLineEdit.Password)
        remote_port = QLineEdit()
        # placeholders in the input box
        remote_ip.setPlaceholderText("Server IP")
        remote_user.setPlaceholderText("Username")
        remote_password.setPlaceholderText("Password")
        remote_port.setPlaceholderText("Port")

        # ---------------------------------------------
        # Pre-mentioning some paramters for local testing
        remote_ip.setText(self.server_ip)
        remote_user.setText(self.server_user)
        remote_password.setText(self.server_password)
        remote_port.setText(self.server_port)
        # ---------------------------------------------
        
        # hidiing the remote parameters unless users selecs remote deployment
        layout.addWidget(remote_ip)
        layout.addWidget(remote_user)
        layout.addWidget(remote_password)
        layout.addWidget(remote_port)
        remote_ip.hide()
        remote_user.hide()
        remote_password.hide()
        remote_port.hide()
        # deploy button
        deploy_button = QPushButton("Deploy")
        deployment_status = QLabel(text="Deployment Started")
        deployment_status.setVisible(False)
        layout.addWidget(deploy_button)
        layout.addWidget(deployment_status)
        popup.setLayout(layout)
        # togging remote parameteres based on what users selects

        def toggle_remote_fields():
            show = remote_radio.isChecked()
            remote_ip.setVisible(show)
            remote_user.setVisible(show)
            remote_password.setVisible(show)
            remote_port.setVisible(show)
       
        def perform_deploy():
            global connections_list, devices_list
            # creating the topology yaml file
            topology = topology_yaml_constructor(
                connection_list=connections_list,
                devices_dict=devices_list,
                switch_image=self.switch_image,
                host_image=self.host_image
            )
            self.yaml_output = topology.yaml_file_generator()

            if local_radio.isChecked():
                # in case of local deployment
                temp_dir = tempfile.mkdtemp()
                yaml_path = os.path.join(temp_dir, "topology.yml")
                with open(yaml_path, "w") as f:
                    f.write(self.yaml_output)
                try:
                    subprocess.run(["clab", "deploy", "-t", yaml_path], check=True)
                    self.statusBar.showMessage("*** Deployment complete ***", 5000)
                except Exception as e:
                    self.statusBar.showMessage(f"Error: {e}", 5000)
            else:
                # in case of remote deployment
                deployment_status.setVisible(True)
                self.server_ip = remote_ip.text()
                self.server_user = remote_user.text()
                self.server_password = remote_password.text()
                self.server_port = remote_port.text()
                try:
                    client = paramiko.SSHClient() # creating a paramiko client 
                    client.set_missing_host_key_policy(paramiko.AutoAddPolicy()) # if connecting to a new server, paramiko makes sure the add the host keys and continue to connect
                    client.connect(self.server_ip, username=self.server_user, password=self.server_password, port=self.server_port) # connecting to the client
                    sftp = client.open_sftp() # opening an sftp session and creating a dir and copying the yaml file to the dir
                    try:
                        sftp.mkdir("/tmp/remote_deploy")
                    except IOError:
                        pass
                    remote_yaml_path = "/tmp/remote_deploy/topology.yml"
                    with sftp.open(remote_yaml_path, "wb") as f:
                        f.write(self.yaml_output)
                    """ now that the file is written, we can proceed with executing clab to deploy the containers
                        if we just use "sudo -S clab deploy -t topology.yml", its not working as it's requiring a TTY session
                        hence given clab is not working in non-interactive shell, making the shell interactive aka a TTY session using "bash -lc" option """
                    command = f'echo "{self.server_password}" | sudo -S -p "" bash -lc "clab deploy -t {remote_yaml_path}"'
                    stdin, stdout, stderr = client.exec_command(command, get_pty=True)
                    # print("STDERR:", stderr.read().decode())
                    print("STDOUT:", stdout.read().decode())
                    if stderr.read().decode() == "sudo: deploy: command not found":
                        command = f'bash -lc "clab deploy -t {remote_yaml_path}"'
                        # print("STDERR:", stderr.read().decode())
                        print("STDOUT:", stdout.read().decode())
                    popup.accept()
                    self.statusBar.showMessage("*** Deployment Successful ***", 10000)
                    client.close()
                except Exception as error:
                    self.statusBar.showMessage(f"Error: {error}", 10000)
        
        local_radio.toggled.connect(toggle_remote_fields)
        remote_radio.toggled.connect(toggle_remote_fields)
        deploy_button.clicked.connect(perform_deploy)
        popup.exec()

    def destroy_lab_handler(self):
        popup_window = QDialog(self)
        layout = QVBoxLayout()
        disclaimer=QLabel(text="Are you sure you want to destroy the lab?")
        buttons_layout = QHBoxLayout()
        yes_button = QPushButton("Yes")
        no_button = QPushButton("No")
        buttons_layout.addWidget(yes_button)
        buttons_layout.addWidget(no_button)
        layout.addWidget(disclaimer)
        layout.addLayout(buttons_layout)
        popup_window.setLayout(layout)
        yes_button.clicked.connect(popup_window.accept)
        no_button.clicked.connect(popup_window.reject)
        if popup_window.exec() == QDialog.Accepted:
            try:
                client = paramiko.SSHClient() # creating a paramiko client 
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy()) # if connecting to a new server, paramiko makes sure the add the host keys and continue to connect
                client.connect(self.server_ip, username=self.server_user, password=self.server_password, port=self.server_port) # connecting to the client
                remote_yaml_path = "/tmp/remote_deploy/topology.yml"
                command = f'echo "{self.server_password}" | sudo -S bash -lc "clab destroy -t {remote_yaml_path}"' 
                stdin, stdout, stderr = client.exec_command(command)
                # print("STDERR:", stderr.read().decode())
                # print("STDOUT:", stdout.read().decode())
                if stderr.read().decode() == "sudo: destroy: command not found":
                    command = f'bash -lc "clab deploy -t {remote_yaml_path}"'
                    stdin, stdout, stderr = client.exec_command(command)
                    # print("STDERR:", stderr.read().decode())
                    # print("STDOUT:", stdout.read().decode())
                self.statusBar.showMessage("*** Lab Destroyed Successfully ***", 10000)
                client.close()
            except Exception as error:
                self.statusBar.showMessage(f"Error: {error}", 10000)

    def save_config_handler(self):
        try:
            client = paramiko.SSHClient() # creating a paramiko client 
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy()) # if connecting to a new server, paramiko makes sure the add the host keys and continue to connect
            client.connect(self.server_ip, username=self.server_user, password=self.server_password, port=self.server_port) # connecting to the client
            remote_yaml_path = "/tmp/remote_deploy/topology.yml"
            command = f'echo "{self.server_password}" | sudo -S bash -lc "clab save -t {remote_yaml_path}"' 
            stdin, stdout, stderr = client.exec_command(command)
            print("STDERR:", stderr.read().decode())
            print("STDOUT:", stdout.read().decode())
            if stderr.read().decode() == "sudo: save: command not found":
                command = f'bash -lc "clab save -t {remote_yaml_path}"'
                stdin, stdout, stderr = client.exec_command(command)
                print("STDERR:", stderr.read().decode())
                print("STDOUT:", stdout.read().decode())
            self.statusBar.showMessage("*** Configs Saved ***", 10000)
            client.close()
        except Exception as error:
            self.statusBar.showMessage(f"Error: {error}", 10000)
        
    def handle_link_config(self):
        if self.link_config_mode == False:
            self.view.link_config_mode=True
            self.view.mlag_config_mode = False
            self.view.bgp_config_mode = False
            self.view.vxlan_config_mode = False
        else:
            self.view.link_config_mode = False

    def handle_mlag_config(self):
        if self.view.mlag_config_mode == False:
            self.view.mlag_config_mode = True
            self.view.link_config_mode = False
            self.view.bgp_config_mode = False
            self.view.vxlan_config_mode = False
        else:
            self.view.mlag_config_mode == False

    def handle_bgp_config(self):
        if self.view.bgp_config_mode == False:
            self.view.bgp_config_mode = True
            self.view.link_config_mode = False
            self.view.mlag_config_mode = False
            self.view.vxlan_config_mode = False
        else:
            self.view.bgp_config_mode == False

    def handle_vxlan_config(self):
        if self.view.vxlan_config_mode == False:
            self.view.vxlan_config_mode = True
            self.view.link_config_mode = False
            self.view.mlag_config_mode = False
            self.view.bgp_config_mode = False
        else:
            self.view.vxlan_config_mode == False

### 
# Icons Attribution:
# <a href="https://www.flaticon.com/free-icons/hub" title="hub icons">Hub icons created by Freepik - Flaticon</a> 
# <a href="https://www.flaticon.com/free-icons/server" title="server icons">Server icons created by smashingstocks - Flaticon</a>
# <a href="https://www.flaticon.com/free-icons/network-switch" title="network switch icons">Network switch icons created by Chattapat - Flaticon</a>
# <a href="https://www.flaticon.com/free-icons/server" title="server icons">Server icons created by Roundicons - Flaticon</a>
# <a href="https://www.flaticon.com/free-icons/no-connection" title="no connection icons">No connection icons created by Freepik - Flaticon</a>
# <a href="https://www.flaticon.com/free-icons/cpu-tower" title="cpu tower icons">Cpu tower icons created by Freepik - Flaticon</a>
# <a href="https://www.flaticon.com/free-icons/os" title="OS icons">OS icons created by juicy_fish - Flaticon</a>
# <a href="https://www.flaticon.com/free-icons/yaml" title="yaml icons">Yaml icons created by Muhammad Andy - Flaticon</a>
# <a href="https://www.flaticon.com/free-icons/save" title="save icons">Save icons created by Freepik - Flaticon</a>
###