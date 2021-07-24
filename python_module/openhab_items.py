"""
Items will be generated from items added under my devices.
"""

from openhab_ds import OHMqttBridge, OHItem, OHChannel, OHGroup, OHThingBase
from openhab_things import get_thing_and_dev_type, get_wled_thing_id
from configs import get_device_configs
from typing import List


def create_items(things: List[OHThingBase], devices: List[dict]) -> List[OHItem]:
    all_items = []
    for dev in devices:
        thing_type, dev_type = get_thing_and_dev_type(dev['type'])
        if thing_type == 'mqtt':
            items = create_items_mqtt(dev, things)
            all_items.extend(items)
        elif thing_type == 'wled':
            items = create_items_wled(dev, dev_type, things)
            all_items.extend(items)

    # print
    # items_str = map(lambda x: x.convert_to_string(), all_items)
    # items_str2 = reduce(lambda x, y: x + y, items_str)
    # text = '\n'.join(items_str2)
    # print(text)

    return all_items


def create_items_wled(device: dict, dev_type: str, things: List[OHThingBase]) -> List[OHItem]:
    device_config = get_device_configs()
    thing_id = get_wled_thing_id(device['id'])
    thing = next(filter(lambda x: x.get_thing_id() == thing_id, things))

    all_items = []
    if 'groups' not in device:
        device['groups'] = []
    for item_data in device_config[dev_type]['items']:
        if 'item_type' not in item_data:
            continue
        item = create_wled_item(item_data, thing_id, device['groups'], thing)
        all_items.append(item)

    return all_items


def create_wled_item(data: dict, device_id: str, parent_groups: List[str], thing: OHThingBase) -> OHItem:
    item_name = f'{data["id"]}_{device_id}'
    item = OHItem(name=item_name, **data)
    item.add_groups(parent_groups)
    item.set_device_id(device_id)

    channel = OHChannel(name=data['id'], ch_type=data['item_type'], entity_name=data['label'])
    channel.add_thing(thing)
    item.add_channel(channel)
    return item


def create_items_mqtt(device: dict, things: List[OHThingBase]) -> List[OHItem]:
    try:
        mqtt_bridge: OHMqttBridge = next(filter(lambda x: isinstance(x, OHMqttBridge), things))
    except StopIteration as e:
        print('[items] Error: mqtt broker not configured.')
        raise e
    if 'items' not in device:
        print('[items] No items found for device', device['name'])
        return []

    all_items = []
    for item_data in device['items']:
        if isinstance(item_data, str):
            # raw item
            item = OHItem(raw_item=item_data)
            all_items.append(item)
        elif 'item_type' in item_data:
            channel = get_mqtt_channel(mqtt_bridge, device['id'], item_data['id'])
            created_items = create_mqtt_item(item_data, device['id'], device['groups'], channel)
            all_items.extend(created_items)
    return all_items


def create_mqtt_item(data: dict, device_id: str, parent_groups: List[str], channel: OHChannel) -> List[OHItem]:
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


def get_mqtt_channel(bridge: OHMqttBridge, device_id: str, item_id: str) -> OHChannel:
    thing = next(filter(lambda x: x.get_thing_id() == device_id, bridge.get_things()))
    try:
        channel = next(filter(lambda x: x.get_entity_name() == item_id, thing.get_channels()))
    except StopIteration as e:
        print(f'[items] device_config.yaml is not having \'{item_id}\' for device \'{device_id}\'.')
        raise e
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
