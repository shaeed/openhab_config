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
                # raw item
                item = OHItem(raw_item=item_data)
                all_items.append(item)
            elif 'item_type' in item_data:
                channel = get_channel(bridge, dev_id, item_data['id'])
                created_items = create_item(item_data, dev_id, dev_groups, channel)
                # item.add_channel(channel)
                all_items.extend(created_items)
        # end inner for
    # end for

    # print
    # items_str = map(lambda x: x.convert_to_string(), all_items)
    # items_str2 = reduce(lambda x, y: x + y, items_str)
    # text = '\n'.join(items_str2)
    # print(text)

    return all_items


def create_item(data: dict, device_id: str, parent_groups: List[str], channel: OHChannel) -> List[OHItem]:
    item_name = f'{data["id"]}_{device_id}'
    item = OHItem(name=item_name, **data)
    item.add_groups(parent_groups)
    item.set_device_id(device_id)

    created_items = [item]

    # create updater items (for lights or any other)
    if 'update_mode' in data:
        # add group in last created item (this group will take input from UI)
        item.add_group(data['update_mode'])

        # additional item
        item_name = data['update_mode'] + '_' + item_name
        item = OHItem(name=item_name, main_ui='no')
        item.add_groups(parent_groups)
        item.add_group('esp_' + data['update_mode'])  # this group will receive input from esp and update UI
        if 'groups' in data:
            item.add_groups(data['groups'])
        created_items.append(item)

    # add the channel in target item
    item.add_channel(channel)

    return created_items


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
