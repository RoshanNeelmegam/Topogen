from ruamel.yaml import YAML
import os

yaml = YAML()
yaml.indent(mapping=2, sequence=4, offset=2)

def load_device_yaml(file_path):
    # if there's a yaml file with contents already in the file path
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return yaml.load(f)
    else:
        print("Creating new structure")
        return {
            'name': None,
            'type': None,
            'configs': {
                'interfaces': [],
                'mlag': {},
                'bgp': {},
                'vxlan': {}
            }
        }

def save_device_yaml(file_path, data):
    # saving the dict as yaml data in the the device.yml file
    with open(file_path, 'w') as f:
        yaml.dump(data, f)

def update_yaml_field(data, path, value):
    current = data
    for key in path[:-1]:
        if isinstance(key, int):
            print('nahoo')
            # Ensure the list has enough length
            while len(current) <= key:
                current.append({})
            current = current[key]
        else:
            print('cahoo')
            if key not in current or current[key] is None:
                current[key] = {}
            current = current[key]

    last_key = path[-1]
    if isinstance(current, list) and isinstance(last_key, int):
        print('kahoo')
        while len(current) <= last_key:
            current.append({})
        current[last_key] = value
    else:
        print('yahoo')
        current[last_key] = value