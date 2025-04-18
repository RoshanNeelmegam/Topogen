import random
import re

awesome_names = ['Hendrix','Cayson','Petronilla','Phaidra','Osbert','Logen','Gelina','Eraqus','Olivero','Fosca','Serkr','Martti','MJ','Ihrin','Puleleiite','Rizalino','Vixen','Bower','Fonsie']

class topology_yaml_constructor:

    ''' This class is responsible for getting the inputs from the topology creator 
        pane (like the nodes, hosts, links and os_info). Post getting the info, we 
        call the topology_yaml_file_generator method to just construct the yaml 
        contents and return the same '''
    
    def __init__(self, connection_list, devices_dict, switch_image, host_image):
        self.switch_image = switch_image
        self.host_image = host_image
        self.ip = 10
        self.lab_name = f'{random.choice(awesome_names)}{random.randint(0, 1000)}'
        self.connection_list = connection_list
        self.devices_dict = devices_dict
        self.contents = ''
        if re.match(r"ceos.*", self.switch_image):
            self.switch_kind = 'ceos'
        if re.match(r"ceos.*", self.host_image):
            self.host_kind = 'ceos'
        elif re.match(r"linux.*", self.host_image):
            self.host_kind = 'linux'

    def yaml_file_generator(self):
        self.ipv4_mgmt_subnet = f"172.{random.randint(0,255)}.{random.randint(0,255)}.0/24"
        self.mgmt_network_part = re.findall(r'(\d+\.\d+\.\d+)\.\d+.+', self.ipv4_mgmt_subnet)[0]
        self.contents = f"""name: {self.lab_name}
topology:
  kinds:
    {self.switch_kind}:
      image: {self.switch_image}\n"""
        if self.host_kind != self.switch_kind:
            self.contents += f"""    {self.host_kind}:
      image: {self.host_image}\n"""
        self.contents += """  nodes:"""
        for device in self.devices_dict:
            if device.device_type == 'router':
                self.contents += f"""
    {device.name}:
        kind: {self.switch_kind}
        mgmt-ipv4: {self.mgmt_network_part}.{self.ip}"""
                self.ip += 1
            elif device.device_type == 'host':
                self.contents += f"""
    {device.name}:
        kind: {self.host_kind}
        mgmt-ipv4: {self.mgmt_network_part}.{self.ip}"""
                self.ip += 1
        self.contents += """  
  links:"""
        for connections in self.connection_list:
            self.contents += f"""
    - endpoints: [{connections}]"""
        self.contents += f"""
mgmt:
  network: lab_{self.lab_name}_network
  ipv4-subnet: {self.ipv4_mgmt_subnet}"""
        return(self.contents)