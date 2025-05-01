from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QPushButton
)
import random

class MlagConfigDialog(QDialog):
    def __init__(self, current_device, all_devices):
        super().__init__()
        self.setWindowTitle("MLAG Configuration")
        self.current_device = current_device
        self.all_devices = [dev for dev in all_devices if dev != current_device]
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Peer Link Interfaces for current device
        self.peer_link_input = QLineEdit()
        self.peer_link_input.setPlaceholderText("e.g., eth1, eth2")
        layout.addWidget(QLabel(f"Peer Link Interfaces for {self.current_device.name}:"))
        layout.addWidget(self.peer_link_input)

        # Neighbor device selector
        self.neighbor_selector = QComboBox()
        self.neighbor_selector.addItems([d.name for d in self.all_devices])
        layout.addWidget(QLabel("Select Neighbor Device:"))
        layout.addWidget(self.neighbor_selector)

        # Peer Link Interfaces for neighbor
        self.neighbor_link_input = QLineEdit()
        self.neighbor_link_input.setPlaceholderText("e.g., eth3, eth4")
        layout.addWidget(QLabel("Peer Link Interfaces for Neighbor:"))
        layout.addWidget(self.neighbor_link_input)

        # Description (optional)
        self.description_input = QLineEdit()
        self.description_input.setPlaceholderText("MLAG description (optional)")
        layout.addWidget(QLabel("Description (optional):"))
        layout.addWidget(self.description_input)

        # OK / Cancel buttons
        buttons = QHBoxLayout()
        ok = QPushButton("OK")
        cancel = QPushButton("Cancel")
        ok.clicked.connect(self.accept)
        cancel.clicked.connect(self.reject)
        buttons.addWidget(ok)
        buttons.addWidget(cancel)

        layout.addLayout(buttons)
        self.setLayout(layout)

    def get_config(self):
        # selected device
        neighbor_name = self.neighbor_selector.currentText()
        neighbor_device = next((d for d in self.all_devices if d.name == neighbor_name), None)

        # parsing interfaces
        dev1_intfs = [intf.strip() for intf in self.peer_link_input.text().split(',') if intf.strip()]
        dev2_intfs = [intf.strip() for intf in self.neighbor_link_input.text().split(',') if intf.strip()]

        description = self.description_input.text()

        # configuring ips
        base_subnet = f"{random.randint(180, 189)}.{random.randint(0, 255)}.{random.randint(0,255)}"
        mlag_ip = f"{base_subnet}.0/31"
        mlag_peer_ip = f"{base_subnet}.1/31"

        # Build configs for both devices
        dev1_config = {
            "peer_link": dev1_intfs,
            "mlag_peer": neighbor_name,
            "mlag_ip": mlag_ip,
            "mlag_peer_ip": mlag_peer_ip,
            "description": description if description else None
        }

        dev2_config = {
            "peer_link": dev2_intfs,
            "mlag_peer": self.current_device.name,
            "mlag_ip": mlag_peer_ip,
            "mlag_peer_ip": mlag_ip,
            "description": description if description else None
        }

        return dev1_config, neighbor_device, dev2_config