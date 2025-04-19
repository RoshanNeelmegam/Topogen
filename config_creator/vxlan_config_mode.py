from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QGroupBox)

class VxlanConfigDialog(QDialog):
    def __init__(self, device):
        super().__init__()
        self.setWindowTitle(f"Vxlan Configuration - {device.name}")
        self.device = device
        self.config_data = {}
        self.setup_ui()

    def setup_ui(self):
        self.vertical_layout = QVBoxLayout()
        # source interface for vxlan
        self.src_intf = QLineEdit()
        self.src_intf.setPlaceholderText('loopback0')
        # grouping all vxlan vlan to vni mappings
        self.vxlan_vlan_vni_options_group = QGroupBox("")
        self.vxlan_vlan_vni_options_vertical_layout = QVBoxLayout()
        self.vxlan_vlan_vni_options_vertical_layout.addLayout(self.add_vlan_options())
        self.vxlan_vlan_vni_options_group.setLayout(self.vxlan_vlan_vni_options_vertical_layout)
        # an add button to add more vlan to vni mappings
        add_vlan = QPushButton('Add more vlan to vni mappings')
        add_vlan.setStyleSheet("background-color: #0078D7; color: white;")
        add_vlan.setAutoDefault(False)
        add_vlan.setDefault(False)
        add_vlan.clicked.connect(self.add_widgets_to_vlan_group)

        # grouping all vxlan vrf to vni mappings 
        self.vxlan_vrf_vni_options_group = QGroupBox("")
        self.vxlan_vrf_vni_options_vertical_layout = QVBoxLayout()
        self.vxlan_vrf_vni_options_vertical_layout.addLayout(self.add_vrf_options())
        self.vxlan_vrf_vni_options_group.setLayout(self.vxlan_vrf_vni_options_vertical_layout)
        # an add button to add more vlan to vrf mappings
        add_vrf = QPushButton('Add more vrf to vni mappings')
        add_vrf.setStyleSheet("background-color: #0078D7; color: white;")
        add_vrf.setAutoDefault(False)
        add_vrf.setDefault(False)
        add_vrf.clicked.connect(self.add_widgets_to_vrf_group)

        # adding everything to the vertical layout
        self.vertical_layout.addWidget(QLabel('Source Interface:'))
        self.vertical_layout.addWidget(self.src_intf)
        self.vertical_layout.addWidget(self.vxlan_vlan_vni_options_group)
        self.vertical_layout.addWidget(add_vlan)
        self.vertical_layout.addWidget(self.vxlan_vrf_vni_options_group)
        self.vertical_layout.addWidget(add_vrf)
        # defining our buttons
        btns = QHBoxLayout()
        ok = QPushButton("OK")
        cancel = QPushButton("Cancel")
        ok.clicked.connect(self.accept)
        cancel.clicked.connect(self.reject)
        btns.addWidget(ok)
        btns.addWidget(cancel)
        self.vertical_layout.addLayout(btns)
        # setting the layout of QDialog so that it dislays the whole set of widgets w
        self.setLayout(self.vertical_layout)

    def add_vlan_options(self):
        horizontal_layout = QHBoxLayout()
        vlan = QLineEdit()
        vni = QLineEdit()
        horizontal_layout.addWidget(QLabel("Vxlan vlan"))
        horizontal_layout.addWidget(vlan)
        horizontal_layout.addWidget(QLabel("vni"))
        horizontal_layout.addWidget(vni)
        return horizontal_layout

    def add_vrf_options(self):
        horizontal_layout = QHBoxLayout()
        vrf = QLineEdit()
        vni = QLineEdit()
        horizontal_layout.addWidget(QLabel("Vxlan vrf"))
        horizontal_layout.addWidget(vrf)
        horizontal_layout.addWidget(QLabel("vni"))
        horizontal_layout.addWidget(vni)
        return horizontal_layout
    
    def add_widgets_to_vlan_group(self):
        self.vxlan_vlan_vni_options_vertical_layout.addLayout(self.add_vlan_options())

    def add_widgets_to_vrf_group(self):
        self.vxlan_vrf_vni_options_vertical_layout.addLayout(self.add_vrf_options())

    def get_config(self):
        vlan_vni_mappings = {}
        for i in range(self.vxlan_vlan_vni_options_vertical_layout.count()):
            layout = self.vxlan_vlan_vni_options_vertical_layout.itemAt(i).layout()
            if layout is not None:
                vlan_input = layout.itemAt(1).widget()
                vni_input = layout.itemAt(3).widget()
                if vlan_input and vni_input:
                    vlan_text = vlan_input.text().strip()
                    vni_text = vni_input.text().strip()
                    if vlan_text.isdigit() and vni_text.isdigit():
                        vlan_vni_mappings[int(vlan_text)] = int(vni_text)

        vrf_vni_mappings = {}
        for i in range(self.vxlan_vrf_vni_options_vertical_layout.count()):
            layout = self.vxlan_vrf_vni_options_vertical_layout.itemAt(i).layout()
            if layout is not None:
                vrf_input = layout.itemAt(1).widget()
                vni_input = layout.itemAt(3).widget()
                if vrf_input and vni_input:
                    vrf_text = vrf_input.text().strip()
                    vni_text = vni_input.text().strip()
                    if vrf_text and vni_text.isdigit():
                        vrf_vni_mappings[vrf_text] = int(vni_text)

        return {
            "source-interface": self.src_intf.text().strip(),
            "vlan-vni-mappings": vlan_vni_mappings,
            "vrf-vni-mappings": vrf_vni_mappings
        }