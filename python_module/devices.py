"""
Device/Hardware specific python classes
"""
from typing import List
import abc
from openhab_ds import *
from configs import get_esphome_openhab_config, get_device_configs


# ######### Some global objects################
on_command = ChannelCommand('on', 'ON')
off_command = ChannelCommand('off', 'OFF')


class RootDev(object):
    def __init__(self, device: dict):
        self.device_data = device
        self.name = device.get('name')
        # Below will be updated in derived class
        self.thing_id = None
        self.items_dict: List[dict] = None

    @abc.abstractmethod
    def create_thing(self) -> OHThingBase:
        pass

    @abc.abstractmethod
    def get_thing(self) -> OHThingBase:
        pass

    @abc.abstractmethod
    def create_items(self) -> List[OHItem]:
        pass


class MqttDev(RootDev):
    def __init__(self, mqtt_bridge: OHMqttBridge, device: dict, dev_type: str):
        super(MqttDev, self).__init__(device)
        self.mqtt_bridge = mqtt_bridge
        self.channels: List[OHChannel] = None
        self.thing_id = device['id']
        self.dev_type = dev_type
        self.groups = device.get('groups', [])
        self.items_dict = device.get('items', [])
        self.thing: OHMqttThings = self.create_thing()

    def create_thing(self) -> OHThingBase:
        device = self.device_data
        device_config = get_device_configs()
        bridge = self.mqtt_bridge
        if not bridge:
            print('[things] Error: mqtt_broker configuration is required for mqtt devices.',
                  f'mqtt is used for {device["name"]} ({device["id"]}).')
            raise ValueError('mqtt configuration missing')

        # check inside bridge if this device is already added
        for thing in bridge.get_things():
            if thing.get_thing_id() == device['id']:
                return thing

        thing = OHMqttThings(device['id'], device['name'])
        channels = self.create_channels(device['id'], device_config[self.dev_type])
        thing.add_channels(channels)
        bridge.add_thing(thing)
        # add thing reference to channels
        list(map(lambda x: x.add_thing(thing), channels))
        # add bridge reference to thing
        thing.add_bridge(bridge)

        self.channels = channels
        return thing

    def get_thing(self) -> OHThingBase:
        # for mqtt device bridge will have all the things
        return self.mqtt_bridge

    def create_channels(self, dev_id: str, dev_config: dict) -> List[OHChannel]:
        channels = []
        esphab_config = get_esphome_openhab_config()

        for entity in dev_config:
            channel_type = self.get_channel_type(entity, esphab_config)

            # entity is having child members (Ex- wifi_signal, touch_key0, relay_0 etc.)
            children = dev_config[entity]
            if not children:
                # entity which is not having any member (Ex- status, debug)
                children = [entity]

            # if entity is 'light', change the format
            if entity == 'light':
                children = list(map(lambda x: x['id'], children))

            for entity_child in children:
                channel_name = f'ch_{entity_child}_{dev_id}'
                channel = OHChannel(channel_type, channel_name, entity_child)
                commands = self.get_channel_commands(entity, esphab_config, dev_id, entity_child)
                channel.add_commands(commands)
                channels.append(channel)
            # end inner for
        # end for

        return channels

    def get_channel_commands(self, entity: str, esphab_config: dict, device_id: str, entity_child: str = '') \
            -> List[ChannelCommand]:
        # supported openhab commands, ex- stateTopic, commandTopic
        command_oh = esphab_config['openhab_ch'][entity]['channels']
        # mqtt topics defined for entity type, ex- state, command
        topics = esphab_config['esphome'][entity]
        no_child_topic_flag = False
        if not topics:
            topics = [x for x in range(len(command_oh))]  # No special topic for entities like status and debug.
            no_child_topic_flag = True

        commands = []
        for topic in topics:
            if no_child_topic_flag and entity != entity_child:
                mqtt_topic = f'{device_id}/{entity}/{entity_child}'
            elif no_child_topic_flag:
                mqtt_topic = f'{device_id}/{entity}'
            else:
                mqtt_topic = f'{device_id}/{entity}/{entity_child}/{topic}'
            command = ChannelCommand(command_oh[topic], mqtt_topic)
            commands.append(command)

        # add the ON and OFF in case of switch
        if entity == 'switch':
            commands.append(on_command)
            commands.append(off_command)

        return commands

    def get_channel_type(self, entity: str, esphab_config: dict) -> str:
        channel_type = 'String'
        if entity in esphab_config['openhab_ch']:
            channel_type = esphab_config['openhab_ch'][entity]['datatype']
        return channel_type

    def create_items(self) -> List[OHItem]:
        if 'items' not in self.device_data:
            print('[items] No items found for device', self.device_data['name'])
            return []

        all_items = []
        for item_data in self.device_data['items']:
            if isinstance(item_data, str):
                # raw item
                item = OHItem(raw_item=item_data)
                all_items.append(item)
            elif 'item_type' in item_data:
                channel = self.get_channel(item_data['id'])
                created_items = self.create_item(item_data, self.groups, channel)
                all_items.extend(created_items)
        return all_items

    def get_channel(self, item_id: str) -> OHChannel:
        channel = next(filter(lambda x: x.get_entity_name() == item_id, self.thing.get_channels()), None)
        if not channel:
            raise ValueError(f'[items] device_config.yaml is not having \'{item_id}\' for device \'{self.thing_id}\'.')
        return channel

    def create_item(self, item_data: dict, parent_groups: List[str], channel: OHChannel) -> List[OHItem]:
        item_name = f'{item_data["id"]}_{self.thing_id}'
        item = OHItem(name=item_name, **item_data)
        item.add_groups(parent_groups)
        item.set_device_id(self.thing_id)

        created_items = [item]
        # create updater items (for lights or any other)
        if 'update_mode' in item_data:
            # add group in last created item (this group will take input from UI)
            item.add_group(item_data['update_mode'])

            # additional item
            item_name = item_data['update_mode'] + '_' + item_name
            item = OHItem(name=item_name, main_ui='no')
            item.add_groups(parent_groups)
            item.add_group('esp_' + item_data['update_mode'])  # this group will receive input from esp and update UI
            if 'groups' in item_data:
                item.add_groups(item_data['groups'])
            created_items.append(item)

        # add the channel in target item
        item.add_channel(channel)

        return created_items


class EspHomeDev(MqttDev):
    def __init__(self, mqtt_bridge: OHMqttBridge, device: dict):
        super(EspHomeDev, self).__init__(mqtt_bridge, device)


class WledDev(RootDev):
    def __init__(self, device: dict, dev_type: str):
        super(WledDev, self).__init__(device)
        self.thing_id = self.get_wled_thing_id(device['id'])
        self.dev_type = dev_type
        self.thing = self.create_thing()
        self.groups = device.get('groups', [])

    def create_thing(self) -> OHThingBase:
        device = self.device_data
        thing = OHWledThing(thing_id=self.thing_id, label=device['name'], address=device['id'])
        return thing

    def get_thing(self) -> OHThingBase:
        return self.thing

    @staticmethod
    def get_wled_thing_id(dev_id: str) -> str:
        thing_id = 'wled_' + dev_id
        thing_id = thing_id.replace('.', '')
        return thing_id

    def create_items(self) -> List[OHItem]:
        device_config = get_device_configs()
        self.items_dict = self.device_data.get('items') or device_config[self.dev_type]['items']

        all_items = []
        for item_data in device_config[self.dev_type]['items']:
            if 'item_type' not in item_data:
                continue
            item = self.create_item(item_data, self.groups)
            all_items.append(item)

        return all_items

    def create_item(self, item_data: dict, parent_groups: List[str]) -> OHItem:
        item_name = f'{item_data["id"]}_{self.thing_id}'
        item = OHItem(name=item_name, **item_data)
        item.add_groups(parent_groups)
        item.set_device_id(self.thing_id)

        channel = OHChannel(name=item_data['id'], ch_type=item_data['item_type'], entity_name=item_data['label'])
        channel.add_thing(self.thing)
        item.add_channel(channel)
        return item
