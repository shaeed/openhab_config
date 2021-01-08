
"""Config generator for openHAB"""

from openhab_things import get_mqtt_bridge, create_things_channels
from openhab_items import create_items, create_groups
from openhab_sitemap import create_sitemap
from openhab_ds import OHBase
from configs import read_yaml_file
from typing import List, Union
from functools import reduce
import os


flag_write_to_file = True


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


def process(my_devices_path: str, conf_path: str):
    my_devices = get_my_devices(my_devices_path)

    mqtt_bridge = get_mqtt_bridge(**my_devices['mqtt_broker'])
    create_things_channels(mqtt_bridge, my_devices['devices'])
    groups = create_groups(my_devices['locations'])
    items = create_items(mqtt_bridge, my_devices['devices'])
    sitemap = create_sitemap(items, groups, my_devices['sitemap'], my_devices['devices'])

    # create things file
    thing_file = os.path.join(conf_path, 'things', 'mqtt.things')
    write_to_file(mqtt_bridge, thing_file)

    # items file
    item_file = os.path.join(conf_path, 'items', 'default.items')
    write_to_file(groups + items, item_file)

    # sitemap file
    sitemap_file = os.path.join(conf_path, 'sitemaps', 'default.sitemap')
    write_to_file(sitemap, sitemap_file)

    print('Success ..')


if __name__ == '__main__':
    my_devices_path = r'my_devices_template.yaml'
    my_devices_path = r'my_devices.yaml'
    conf_folder = r'D:\Shaeed\openhab-3.0.0\conf'
    process(my_devices_path, conf_folder)
