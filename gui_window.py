from PySide6.QtWidgets import QMainWindow, QToolBar, QStatusBar, QInputDialog, QGraphicsScene, QGraphicsView, QGraphicsItemGroup, QComboBox, QDialog, QToolButton, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit, QDialogButtonBox, QApplication, QRadioButton, QLineEdit # built in widgets 
from PySide6.QtGui import QAction, QIcon, QTransform # all gui specific 
from PySide6.QtCore import QSize, QPointF, Qt # non gui stuff
import tempfile, subprocess
import paramiko
import os
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

        # creating a statusbar to display status related info
        self.statusBar = QStatusBar() # same as QStatusBar(self)
        self.setStatusBar(self.statusBar)
        
        # topology creation toolbar with options like add_routers, add_hosts, etc
        self.TopologyToolBar = QToolBar()
        self.TopologyToolBar.setMovable(False)
        self.TopologyToolBar.setIconSize(QSize(40, 40))
        self.addToolBar(self.TopologyToolBar)

        # topology creation toolbar Options
        self.add_routers_action = QAction(QIcon("./router-icon.png"), "Add Routers/Switches", self)
        self.add_routers_action.setStatusTip("Add Router/Switches into your topology")
        self.add_routers_action.triggered.connect(self.add_routers_handler)
        self.TopologyToolBar.addAction(self.add_routers_action)

        self.add_hosts_action = QAction(QIcon('./server-icon.png'), 'Add Hosts', self)
        self.add_hosts_action.setStatusTip('Add Hosts into your topology')
        self.add_hosts_action.triggered.connect(self.add_hosts_handler)
        self.TopologyToolBar.addAction(self.add_hosts_action)

        self.link_mode_action = QAction(QIcon('./connection-icon.png'), 'Link Mode', self)
        self.link_mode_action.setStatusTip('Select two devices and add links between them')
        self.link_mode_action.triggered.connect(self.link_mode_action_handler)
        self.TopologyToolBar.addAction(self.link_mode_action)

        self.select_os_action = QAction(QIcon('./os-icon.png'), 'Select-OS', self)
        self.select_os_action.setStatusTip('Select the image to run on the devices')
        self.select_os_action.triggered.connect(self.select_os_handler)
        self.TopologyToolBar.addAction(self.select_os_action)

        self.get_yaml_file_action = QAction(QIcon('./yaml.png'), 'Submit', self)
        self.get_yaml_file_action.setStatusTip('Get the topology.yaml file')
        self.get_yaml_file_action.triggered.connect(self.generate_topology_file)
        self.TopologyToolBar.addAction(self.get_yaml_file_action)
        
        self.deploy_action = QAction(QIcon('./deploy_lab_icon.png'), 'Deploy', self)
        self.deploy_action.setStatusTip('Deploy topology locally or remotely')
        self.deploy_action.triggered.connect(self.deploy_lab_handler)
        self.TopologyToolBar.addAction(self.deploy_action)

        self.save_config_action = QAction(QIcon('./save_config.png'), 'Save Config', self)
        self.save_config_action.setStatusTip('Save Configs (saves on the remote server)')
        self.save_config_action.triggered.connect(self.save_config_handler)
        self.TopologyToolBar.addAction(self.save_config_action)

        self.destroy_action = QAction(QIcon('./destroy_lab_icon.png'), 'Deploy', self)  
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
# <a href="https://www.flaticon.com/free-icons/cpu-tower" title="cpu tower icons">Cpu tower icons created by Freepik - Flaticon</a>
# <a href="https://www.flaticon.com/free-icons/os" title="OS icons">OS icons created by juicy_fish - Flaticon</a>
# <a href="https://www.flaticon.com/free-icons/yaml" title="yaml icons">Yaml icons created by Muhammad Andy - Flaticon</a>
# <a href="https://www.flaticon.com/free-icons/save" title="save icons">Save icons created by Freepik - Flaticon</a>
###