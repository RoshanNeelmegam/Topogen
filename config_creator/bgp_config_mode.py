from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QGroupBox, QTextEdit
)

class BgpConfigDialog(QDialog):
    def __init__(self, device):
        super().__init__()
        self.setWindowTitle(f"BGP Configuration - {device.name}")
        self.device = device
        self.config_data = {}
        self.setup_ui()

    def setup_ui(self):
        vertical_layout = QVBoxLayout()

        # widgets that carry the state of the device's bgp configs
        vertical_layout.addWidget(QLabel("Router ID:"))
        self.router_id_input = QLineEdit()
        vertical_layout.addWidget(self.router_id_input)
        vertical_layout.addWidget(QLabel("Router ASN:"))
        self.router_as_input = QLineEdit()
        vertical_layout.addWidget(self.router_as_input)
        # widgets for ibgp neighbors
        vertical_layout.addWidget(QLabel("iBGP Neighbors (comma-separated list, format: ip, remote_as, peer_group):"))
        self.ibgp_neighbors_input = QTextEdit()
        self.ibgp_neighbors_input.setPlaceholderText("e.g. 10.10.10.10, 10 , ibgp_mlag_peer")
        vertical_layout.addWidget(self.ibgp_neighbors_input)
        # widgets for ebgp neighbors
        vertical_layout.addWidget(QLabel("eBGP Neighbors (comma-separated list, format: ip, remote_as, peer_group):"))
        self.ebgp_neighbors_input = QTextEdit()
        self.ebgp_neighbors_input.setPlaceholderText("e.g. 100.10.10.1, 1, ebgp_spines")
        vertical_layout.addWidget(self.ebgp_neighbors_input)
        # widgets for evpn neighborships
        evpn_group = QGroupBox("EVPN BGP")
        evpn_layout = QVBoxLayout()
        self.evpn_name_input = QLineEdit()
        self.evpn_name_input.setPlaceholderText("EVPN-overlay")
        self.update_src_input = QLineEdit()
        self.update_src_input.setPlaceholderText("loopback0")
        evpn_layout.addWidget(QLabel("EVPN Peer Group Name:"))
        evpn_layout.addWidget(self.evpn_name_input)
        evpn_layout.addWidget(QLabel("Update Source:"))
        evpn_layout.addWidget(self.update_src_input)
        evpn_layout.addWidget(QLabel("EVPN Neighbors (format: name,ip,remote_as):"))
        self.evpn_neighbors_input = QTextEdit()
        self.evpn_neighbors_input.setPlaceholderText("e.g. spine1, 10.10.10.10,1")
        evpn_layout.addWidget(self.evpn_neighbors_input)
        evpn_group.setLayout(evpn_layout)
        vertical_layout.addWidget(evpn_group)
        # widgets for mac vrfs
        mac_vrf_group = QGroupBox("MAC VRFs")
        mac_layout = QVBoxLayout()
        self.vlan_bundle_input = QLineEdit()
        self.vlan_bundle_input.setPlaceholderText("vlan-aware-bundle range")
        self.vlans_input = QTextEdit()
        self.vlans_input.setPlaceholderText("e.g.\n20, 1:20, 20:20\n30, 1:30, 30:30")
        mac_layout.addWidget(QLabel("VLAN-Aware Bundle:"))
        mac_layout.addWidget(self.vlan_bundle_input)
        mac_layout.addWidget(QLabel("VLANs (name, rd, rt):"))
        mac_layout.addWidget(self.vlans_input)
        mac_vrf_group.setLayout(mac_layout)
        vertical_layout.addWidget(mac_vrf_group)
        # --- Address Families ---
        af_group = QGroupBox("Address Families")
        af_layout = QVBoxLayout()
        self.af_ipv4_advertise_input = QLineEdit()
        af_layout.addWidget(QLabel("IPv4 Advertise Prefixes:"))
        af_layout.addWidget(self.af_ipv4_advertise_input)
        af_group.setLayout(af_layout)
        vertical_layout.addWidget(af_group)
        # defining our buttons
        btns = QHBoxLayout()
        ok = QPushButton("OK")
        cancel = QPushButton("Cancel")
        ok.clicked.connect(self.accept)
        cancel.clicked.connect(self.reject)
        btns.addWidget(ok)
        btns.addWidget(cancel)
        vertical_layout.addLayout(btns)
        self.setLayout(vertical_layout)

    def get_config(self):
        non_evpn_peer_groups = []
        # --- Process basic info ---
        router_id = self.router_id_input.text()
        router_as = int(self.router_as_input.text())

        ibgp_lines = self.ibgp_neighbors_input.toPlainText().strip().splitlines()
        ibgp_neighbors = []
        ibgp_peer_groups = []
        for line in ibgp_lines:
            parts = line.split(',')
            if len(parts) >= 3:
                ibgp_neighbors.append({
                    'ip': parts[0].strip(),
                    'remote_as': int(parts[1].strip()),
                    'peer_group': parts[2].strip(),
                    'max_routes': 12000,
                    'send_community': True
                })
                if parts[2].strip() not in non_evpn_peer_groups:
                    non_evpn_peer_groups.append(parts[2].strip())

        # --- Process eBGP Neighbors ---
        ebgp_lines = self.ebgp_neighbors_input.toPlainText().strip().splitlines()
        ebgp_neighbors = []
        ebgp_peer_groups = []
        for line in ebgp_lines:
            parts = line.split(',')
            if len(parts) >= 3:
                ebgp_neighbors.append({
                    'ip': parts[0].strip(),
                    'remote_as': int(parts[1].strip()),
                    'peer_group': parts[2].strip(),
                    'max_routes': 12000,
                    'send_community': True
                })
                if parts[2].strip() not in non_evpn_peer_groups:
                    non_evpn_peer_groups.append(parts[2].strip())

        # --- Process EVPN BGP ---
        evpn_name = self.evpn_name_input.text()
        update_source = self.update_src_input.text()
        evpn_neighbors_raw = self.evpn_neighbors_input.toPlainText().splitlines()
        evpn_neighbors = []
        for line in evpn_neighbors_raw:
            parts = line.split(',')
            if len(parts) >= 3:
                evpn_neighbors.append({
                    'name': parts[0].strip(),
                    'ip': parts[1].strip(),
                    'remote_as': int(parts[2].strip())
                })

        # --- MAC VRFs ---
        vlan_bundle = self.vlan_bundle_input.text()
        vlans = []
        for vlan in self.vlans_input.toPlainText().splitlines():
            parts = vlan.split(',')
            if len(parts) >= 3:
                vlans.append({
                    'name': parts[0].strip(),
                    'rd': parts[1].strip(),
                    'rt': parts[2].strip(),
                    'redistribute': ['learned']
                })

        # --- Address Families ---
        address_families = [
            {
                'name': 'evpn',
                'to_activate': [{'name': evpn_name}],
                'to_deactivate': [{'name': name} for name in non_evpn_peer_groups]
            },
            {
                'name': 'ipv4',
                'to_activate': [{'name': name} for name in non_evpn_peer_groups],
                'to_deactivate': [{'name': evpn_name}] ,
                'to_advertise': [{'name': prefix.strip()} for prefix in self.af_ipv4_advertise_input.text().split(',') if prefix.strip()]
            }
        ]

        return {
            'router_id': router_id,
            'router_as': router_as,
            'iBGP': None,
            'eBGP': {'neighbors': ebgp_neighbors},
            'evpnBGP': {
                'name': evpn_name,
                'update_source': update_source,
                'neighbors': evpn_neighbors,
                'mac_vrfs': {
                    'vlan-aware-bundle': vlan_bundle,
                    'vlans': vlans
                }
            },
            'address_families': address_families
        }