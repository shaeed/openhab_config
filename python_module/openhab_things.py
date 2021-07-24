"""
Things and channels will be created based on Device type not by the items added under device.
Device type will be taken from my_devices and from that device things will be taken from
device_configs.yaml.
"""
from openhab_ds import OHMqttBridge, OHMqttThings, ChannelCommand, OHChannel, OHThingBase, OHWledThing
from configs import get_esphome_openhab_config, get_device_configs
from typing import List, Tuple


# ######### Some global objects################
on_command = ChannelCommand('on', 'ON')
off_command = ChannelCommand('off', 'OFF')


def get_mqtt_bridge(**kwargs) -> OHMqttBridge:
    mqtt_bridge = OHMqttBridge(**kwargs)
    return mqtt_bridge


def create_things_channels(bridge: OHMqttBridge, devices: List[dict]):
    """ delete this
    Things and channels will be created based on Device type.
    """
    device_config = get_device_configs()

    unique_things = {}
    for device in devices:
        if device['id'] in unique_things:
            continue
        thing_details = {'id': device['id'],
                         'name': device['name'],
                         'type': device['type']}
        unique_things[device['id']] = thing_details

    for dev_id, device in unique_things.items():
        thing = OHMqttThings(device['id'], device['name'])
        channels = create_channels(device['id'], device_config[device['type']])
        thing.add_channels(channels)
        bridge.add_thing(thing)

        # add thing reference to channels
        list(map(lambda x: x.add_thing(thing), channels))
        # add bridge reference to thing
        thing.add_bridge(bridge)

    # str form
    # text = bridge.convert_to_string()
    # print()
    # print('\n'.join(text))


def get_channel_type(entity: str, esphab_config: dict) -> str:
    channel_type = 'String'
    if entity in esphab_config['openhab_ch']:
        channel_type = esphab_config['openhab_ch'][entity]['datatype']
    return channel_type


def get_channel_commands(entity: str, esphab_config: dict, device_id: str, entity_child: str = '') \
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


def create_channels(dev_id: str, dev_config: dict) -> List[OHChannel]:
    channels = []
    esphab_config = get_esphome_openhab_config()

    for entity in dev_config:
        channel_type = get_channel_type(entity, esphab_config)

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
            commands = get_channel_commands(entity, esphab_config, dev_id, entity_child)
            channel.add_commands(commands)
            channels.append(channel)
        # end inner for
    # end for

    return channels


def create_bridge_and_things(devices: List[dict], data: dict) -> List[OHThingBase]:
    """
    Things and channels will be created based on Device type.
    """
    device_config = get_device_configs()
    things = []
    # mqtt bridge
    mqtt_bridge = None
    if 'mqtt_broker' in data:
        mqtt_bridge = get_mqtt_bridge(**data['mqtt_broker'])
        things.append(mqtt_bridge)

    for dev in devices:
        if 'type' not in dev:
            print('[things] Device type is missing and things are not created for', dev)
        else:
            thing_type, dev_type = get_thing_and_dev_type(dev['type'])
            if thing_type == 'mqtt':
                create_thing_mqtt(dev, mqtt_bridge, device_config)
            elif thing_type == 'wled':
                thing = create_thing_wled(dev)
                things.append(thing)
            print('[things] thing created for device', dev['id'])
    return things


def get_thing_and_dev_type(dev_type_str: str) -> Tuple[str, str]:
    if '::' not in dev_type_str:
        return 'mqtt', dev_type_str
    sep_ind = dev_type_str.index('::')
    return dev_type_str[:sep_ind], dev_type_str[sep_ind+2:]


def get_wled_thing_id(dev_id: str) -> str:
    thing_id = 'wled_' + dev_id
    thing_id = thing_id.replace('.', '')
    return thing_id


def create_thing_wled(device: dict) -> OHThingBase:
    thing_id = get_wled_thing_id(device['id'])
    thing = OHWledThing(thing_id=thing_id, label=device['name'], address=device['id'])
    return thing


def create_thing_mqtt(device: dict, bridge: OHMqttBridge, device_config: dict) -> OHThingBase:
    if not bridge:
        print('[things] Error: mqtt_broker configuration is required for mqtt devices.',
              f'mqtt is used for {device["name"]} ({device["id"]}).')
        raise ValueError('mqtt configuration missing')

    # check inside bridge if this device is already added
    for thing in bridge.get_things():
        if thing.get_thing_id() == device['id']:
            return thing

    thing = OHMqttThings(device['id'], device['name'])
    channels = create_channels(device['id'], device_config[device['type']])
    thing.add_channels(channels)
    bridge.add_thing(thing)
    # add thing reference to channels
    list(map(lambda x: x.add_thing(thing), channels))
    # add bridge reference to thing
    thing.add_bridge(bridge)

    return thing
