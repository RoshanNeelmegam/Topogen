# from PySide6.QtWidgets import (
#     QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
#     QComboBox, QPushButton
# )

# class MlagConfigDialog(QDialog):
#     def __init__(self, current_device, all_devices):
#         super().__init__()
#         self.setWindowTitle("MLAG Configuration")
#         self.current_device = current_device
#         self.all_devices = [dev for dev in all_devices if dev != current_device]  # exclude self
#         self.mlag_config = {}
#         self.setup_ui()

#     def setup_ui(self):
#         layout = QVBoxLayout()

#         # 1. Peer Link Interfaces (on current device)
#         self.peer_interfaces_input = QLineEdit()
#         self.peer_interfaces_input.setPlaceholderText("e.g., eth1, eth2")
#         layout.addWidget(QLabel(f"Peer Link Interfaces for {self.current_device.name}:"))
#         layout.addWidget(self.peer_interfaces_input)

#         # 2. Neighbor Device selection
#         self.neighbor_selector = QComboBox()
#         self.neighbor_selector.addItems([dev.name for dev in self.all_devices])
#         layout.addWidget(QLabel("Select Neighbor Device:"))
#         layout.addWidget(self.neighbor_selector)

#         # 3. Interfaces on Neighbor
#         self.neighbor_interfaces_input = QLineEdit()
#         self.neighbor_interfaces_input.setPlaceholderText("e.g., eth3, eth4")
#         layout.addWidget(QLabel("Interfaces on Neighbor Device (for peer link):"))
#         layout.addWidget(self.neighbor_interfaces_input)

#         # 4. Buttons
#         button_layout = QHBoxLayout()
#         ok_btn = QPushButton("OK")
#         cancel_btn = QPushButton("Cancel")
#         ok_btn.clicked.connect(self.accept)
#         cancel_btn.clicked.connect(self.reject)
#         button_layout.addWidget(ok_btn)
#         button_layout.addWidget(cancel_btn)
#         layout.addLayout(button_layout)

#         self.setLayout(layout)

#     def get_config(self):
#         return {
#             "device": self.current_device.name,
#             "peer_link_interfaces": [intf.strip() for intf in self.peer_interfaces_input.text().split(",") if intf.strip()],
#             "neighbor": self.neighbor_selector.currentText(),
#             "neighbor_peer_link_interfaces": [intf.strip() for intf in self.neighbor_interfaces_input.text().split(",") if intf.strip()]
#         }


from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QPushButton
)

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
        # Get selected neighbor device
        neighbor_name = self.neighbor_selector.currentText()
        neighbor_device = next((d for d in self.all_devices if d.name == neighbor_name), None)

        # Parse interfaces
        dev1_intfs = [intf.strip() for intf in self.peer_link_input.text().split(',') if intf.strip()]
        dev2_intfs = [intf.strip() for intf in self.neighbor_link_input.text().split(',') if intf.strip()]

        description = self.description_input.text()

        # Build configs for both devices
        dev1_config = {
            "peer_link": dev1_intfs,
            "mlag_peer": neighbor_name,
            "description": description if description else None
        }

        dev2_config = {
            "peer_link": dev2_intfs,
            "mlag_peer": self.current_device.name,
            "description": description if description else None
        }

        return dev1_config, neighbor_device, dev2_config