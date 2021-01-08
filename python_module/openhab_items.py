"""
Items will be generated from items added under my devices.
"""

from openhab_ds import OHMqttBridge, OHItem, OHChannel, OHGroup
from typing import List


def create_items(bridge: OHMqttBridge, devices: List[dict]) -> List[OHItem]:
    all_items = []
    for device in devices:
        dev_id = device['id']
        dev_groups = device['groups']
        if 'items' not in device:
            continue
        for item_data in device['items']:
            if isinstance(item_data, str):
                item = OHItem(raw_item=item_data)
                all_items.append(item)
            elif 'item_type' in item_data:
                item = create_item(item_data, dev_id, dev_groups)
                channel = get_channel(bridge, dev_id, item.get_item_id())
                item.add_channel(channel)
                all_items.append(item)
        # end inner for
    # end for

    # print
    #print()
    #items_str = map(lambda x: x.convert_to_string(), all_items)
    #items_str2 = reduce(lambda x, y: x + y, items_str)
    #text = '\n'.join(items_str2)
    #print(text)

    return all_items


def create_item(data: dict, device_id: str, parent_groups: List[str]) -> OHItem:
    item_name = f'{data["id"]}_{device_id}'
    item = OHItem(name=item_name, **data)
    item.add_groups(parent_groups)
    item.set_device_id(device_id)

    return item


def get_channel(bridge: OHMqttBridge, device_id: str, item_id: str) -> OHChannel:
    thing = next(filter(lambda x: x.get_thing_id() == device_id, bridge.get_things()))
    channel = next(filter(lambda x: x.get_entity_name() == item_id, thing.get_channels()))
    return channel


def create_groups(group_list: list) -> List[OHGroup]:
    groups = []
    for g in group_list:
        if isinstance(g, str):
            # raw groups
            group = OHGroup(raw_grp=g)
        else:
            group = OHGroup(**g)
        groups.append(group)

    # print('\n'.join(reduce(lambda x, y: x + y, map(lambda x: x.convert_to_string(), groups))))
    return groups
