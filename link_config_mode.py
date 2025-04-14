from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QRadioButton, QPushButton, QGroupBox, QWidget
)

class LinkConfigDialog(QDialog):
    def __init__(self, interfaces):
        super().__init__()
        self.setWindowTitle("Link Configuration")
        self.interfaces = list(interfaces.values())
        self.interface_widgets_states = {} # stores all the states of the widgets which will help construct the configurations
        self.initialize_ui()

    def initialize_ui(self):
        layout = QVBoxLayout() # whole layout

        # interface configuration sections
        for interface in self.interfaces:
            interface_group = QGroupBox(f"Interface: {interface}")
            interface_layout = QVBoxLayout()
            # Switchport Mode
            port_type_layout = QHBoxLayout()
            switchport_radio = QRadioButton("Switchport")
            no_switchport_radio = QRadioButton("No Switchport")
            port_type_layout.addWidget(switchport_radio)
            port_type_layout.addWidget(no_switchport_radio)
            # if switchport then user needs to determine if interface is access or trunk port
            switchport_type_container = QWidget()
            vlan_layout = QHBoxLayout(switchport_type_container)
            access_radio = QRadioButton("Access")
            trunk_radio = QRadioButton("Trunk")
            vlan_layout.addWidget(access_radio)
            vlan_layout.addWidget(trunk_radio)
            switchport_type_container.setVisible(False)
            # if no switchport, user needs to input ip address
            ip_label = QLabel("IP Address:")
            ip_input = QLineEdit()
            ip_label.setVisible(False)
            ip_input.setVisible(False)
            # if switchport and access port, user needs to input the vlan id otherwise if it's a switchport and a trunk, user needs to input allowed vlans
            vlan_label = QLabel("Vlan ID:")
            vlan_input = QLineEdit()
            trunk_allowed_vlans_label = QLabel("Allowed Vlans:")
            trunk_allowed_vlans_input = QLineEdit()
            vlan_label.setVisible(False)
            vlan_input.setVisible(False)
            trunk_allowed_vlans_label.setVisible(False)
            trunk_allowed_vlans_input.setVisible(False)
            # putting together the layouts
            interface_layout.addLayout(port_type_layout) # switchport or no-switchport
            interface_layout.addWidget(ip_label) # ip address in case of no-switchport
            interface_layout.addWidget(ip_input) 
            interface_layout.addWidget(switchport_type_container) # access or trunk in case of switchport
            interface_layout.addWidget(vlan_label) # vlan id in case of access port
            interface_layout.addWidget(vlan_input)
            interface_layout.addWidget(trunk_allowed_vlans_label) # allowed vlans list in case of trunk port
            interface_layout.addWidget(trunk_allowed_vlans_input)
            # adding the layout to the interface group
            interface_group.setLayout(interface_layout)
            layout.addWidget(interface_group)

            # saving the state of the widgets as in if they are triggered or not
            self.interface_widgets_states[interface] = {
    "switchport_radio": switchport_radio,
    "no_switchport_radio": no_switchport_radio,
    "access_radio": access_radio,
    "trunk_radio": trunk_radio,
    "vlan_input": vlan_input,
    "allowed_vlans_input": trunk_allowed_vlans_input,
    "ip_input": ip_input
}
            # making sure the next set of widgets are shown only when appropriate options are selected
            switchport_radio.toggled.connect(lambda checked, switchport_type_container=switchport_type_container : (
                switchport_type_container.setVisible(checked)))
            no_switchport_radio.toggled.connect(lambda checked, ip_lbl=ip_label, ip_in=ip_input, vlan_lbl=vlan_label, vlan_in=vlan_input, allow_lbl=trunk_allowed_vlans_label, allow_in=trunk_allowed_vlans_input: (
                ip_lbl.setVisible(checked), ip_in.setVisible(checked), vlan_lbl.setVisible(False), vlan_in.setVisible(False), allow_lbl.setVisible(False), allow_in.setVisible(False)))
            access_radio.toggled.connect(lambda checked, vlan_lbl=vlan_label, vlan_in=vlan_input: (
                vlan_lbl.setVisible(checked), vlan_in.setVisible(checked)))
            trunk_radio.toggled.connect(lambda checked, allow_lbl=trunk_allowed_vlans_label, allow_in=trunk_allowed_vlans_input: (
                allow_lbl.setVisible(checked), allow_in.setVisible(checked)))

        # buttons
        button_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        cancel_button = QPushButton("Cancel")
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        self.setLayout(layout)
        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)

    def get_configurations(self):
        configurations = {}
        for interface, widgets in self.interface_widgets_states.items():
            config = {
                "mode": "switchport" if widgets["switchport_radio"].isChecked() else "no switchport",
                "ip": widgets["ip_input"].text() if widgets["no_switchport_radio"].isChecked() else None,
                "vlan_mode": "access" if widgets["access_radio"].isChecked() else "trunk" if widgets["trunk_radio"].isChecked() else None,
                "vlan_id": widgets["vlan_input"].text() if widgets["access_radio"].isChecked() else None,
                "allowed_vlans": widgets["allowed_vlans_input"].text() if widgets["trunk_radio"].isChecked() else None
            }
            configurations[interface] = config
        return configurations