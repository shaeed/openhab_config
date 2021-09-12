"""
Things and channels will be created based on Device type not by the items added under device.
Device type will be taken from my_devices and from that device things will be taken from
device_configs.yaml.
"""
from openhab_ds import OHMqttBridge, OHThingBase
from typing import List, Tuple
from devices import MqttDev, WledDev, RootDev


def get_mqtt_bridge(**kwargs) -> OHMqttBridge:
    mqtt_bridge = OHMqttBridge(**kwargs)
    return mqtt_bridge


def create_bridge_and_things(devices: List[dict], data: dict) -> Tuple[List[OHThingBase], List[RootDev]]:
    """
    Things and channels will be created based on Device type.
    """
    things = []
    # mqtt bridge
    mqtt_bridge = None
    if 'mqtt_broker' in data:
        mqtt_bridge = get_mqtt_bridge(**data['mqtt_broker'])
        things.append(mqtt_bridge)

    formed_devs = []
    for dev in devices:
        if 'type' not in dev:
            print('[things] Device type is missing and things are not created for', dev)
        else:
            thing_type, dev_type = get_thing_and_dev_type(dev['type'])
            if thing_type == 'mqtt':
                mqtt_dev = MqttDev(mqtt_bridge, dev, dev_type)
                formed_devs.append(mqtt_dev)
            elif thing_type == 'wled':
                wled_dev = WledDev(dev, dev_type)
                formed_devs.append(wled_dev)
                things.append(wled_dev.thing)
            print('[things] thing created for device', dev['id'])
    return things, formed_devs


def get_thing_and_dev_type(dev_type_str: str) -> Tuple[str, str]:
    if '::' not in dev_type_str:
        return 'mqtt', dev_type_str
    sep_ind = dev_type_str.index('::')
    return dev_type_str[:sep_ind], dev_type_str[sep_ind+2:]
