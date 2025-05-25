# 📘 TopoGen

**TopoGen** is a GUI based tool that allows you to visually design, configure, and deploy network topologies of your choice using ContainerLab. Whether you’re a Network Engineer replicating real world production setups or customer specific scenarios, or a learner building lab environments for hands on practice, TopoGen simplifies and accelerates the entire process. Instead of manually configuring each device or writing scripts from scratch, you can intuitively build topologies, define protocol level configurations (like BGP, VXLAN, etc), and launch containerized network labs all from a user-friendly interface.

---

## 🚀 Features

- 🖱️ **Visual Topology Design**  
  Drag and drop routers, switches, and hosts to create your network topology in a canvas-based GUI.

- 🐳 **Containerlab Integration**  
  Instantly convert your visual topology into a ContainerLab friendly topology file and deploy the lab either manually or automatically.

- 🔗 **Provisioning**  
  Set up L2/L3 interface configurations, add/configure necessary protcol specific configurations for BGP, Vxlan, etc easily through dialog windows.

- 📄 **YAML & Jinja2 Support**  
  Automatically generate device specific yaml files per node and convert them into CLI configs using Jinja2 templates.

- ⚙️ **Ansible Automation**  
  Push device configurations using Ansible playbooks directly from the GUI.

---

## 📦 Installation

```bash
git clone https://github.com/RoshanNeelmegam/Topogen
cd Topogen
pip install -r requirements.txt
```

---

## ▶️ Usage

1. **Run the GUI**  
   ```bash
   python3 main.py
   ```

2. **Design the Topology**  
   Add devices, links, and configure interfaces via the toolbar.
   
   ![designing-topology](https://github.com/RoshanNeelmegam/Topogen/blob/main/Images/toplogy-design.gif)

4. **Provision Devices**  
   Add BGP, MLAG, VXLAN settings from the provisioning menu.

5. **Generate Configs**  
   Use the built-in Jinja2 templates to convert YAML to CLI configs.

6. **Deploy Lab via Ansible**  
   Push inventory and host_vars to a remote server and run:

---

## 📁 Directory Structure

```bash
.
├── README.md
├── requirements.txt
├── main.py
├── icons/                     
│   ├── *.png
├── core/                       
│   ├── gui_window.py
│   ├── draggable_nodes.py
│   ├── links.py
│   ├── topology_yaml.py
│   └── device_provisioning.py
├── config_modes/              
│   ├── bgp_config_mode.py
│   ├── mlag_config_mode.py
│   ├── vxlan_config_mode.py
│   ├── link_config_mode.py
│   └── get_configs.py
└── templates/                
    └── configs.j2
```

---

## 📚 Future Enhancements

- Support for multi-vendor templates (Cisco, Juniper, Nokia, etc. Currently Arista EOS is supported)
- Configuration validation before deployment

---