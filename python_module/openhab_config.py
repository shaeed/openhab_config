
"""Config generator for openHAB"""

from openhab_things import create_bridge_and_things
from openhab_items import create_items, create_groups
from openhab_sitemap import create_sitemap
from openhab_ds import OHBase
from configs import read_yaml_file
from typing import List, Union
from functools import reduce
import os


flag_write_to_file = False
flag_oh_folders = True


def get_my_devices(file_path: str) -> dict:
    return read_yaml_file(file_path)


def write_to_file(content: Union[List[OHBase], OHBase], output_file_path):
    if isinstance(content, OHBase):
        lines = content.convert_to_string()
    else:
        content_str = map(lambda x: x.convert_to_string(), content)
        lines = reduce(lambda x, y: x + y, content_str)

    # add new line character
    lines = map(lambda x: x + '\n', lines)
    if flag_write_to_file:
        with open(output_file_path, 'w') as out:
            out.writelines(lines)
    else:
        print('################################################################')
        print(output_file_path)
        print()
        print(''.join(lines))
        print('################################################################')


def get_oh_file_paths(base_path: str) -> tuple:
    if flag_oh_folders:
        thing_file = os.path.join(base_path, 'things', 'mqtt.things')
        item_file = os.path.join(base_path, 'items', 'default.items')
        sitemap_file = os.path.join(base_path, 'sitemaps', 'default.sitemap')
    else:
        thing_file = os.path.join(base_path, 'mqtt.things')
        item_file = os.path.join(base_path, 'default.items')
        sitemap_file = os.path.join(base_path, 'default.sitemap')
    return thing_file, item_file, sitemap_file


def get_all_devices(data: dict, parent: dict = None) -> list:
    if not isinstance(data, dict):
        return []
    devices = []
    if not parent and 'label' in data:
        parent = data
    for key in data:
        if key == 'devices':
            # insert parent name in each device
            for dev in data[key]:
                dev['parent'] = parent
            devices.extend(data[key])
        elif isinstance(data[key], dict):
            devices.extend(get_all_devices(data[key], data.get('label')))
        elif isinstance(data[key], list):
            for ele in data[key]:
                devices.extend(get_all_devices(ele))

    return devices


def process(dev_yaml: str, conf_path: str):
    data = get_my_devices(dev_yaml)
    all_devices = get_all_devices(data)

    # create things
    things, formed_devs = create_bridge_and_things(all_devices, data)
    # create group and items
    groups = create_groups(data['locations'])
    items = create_items(formed_devs)
    sitemap = create_sitemap(items, groups, data, formed_devs)

    # create things, items, sitemap file
    thing_file, item_file, sitemap_file = get_oh_file_paths(conf_path)
    write_to_file(things, thing_file)
    write_to_file(groups + items, item_file)
    write_to_file(sitemap, sitemap_file)

    print('Success ..')


if __name__ == '__main__':
    #my_devices_path = r'my_devices_template.yaml'
    my_devices_path = r'test_dev.yaml'
    my_devices_path = r'D:\oh-test\my_devices.yaml'
    conf_folder = r'D:\openhab-3.0.2\conf'
    process(my_devices_path, conf_folder)
