"""
Data structure for openhab.
"""

from typing import List, Union
from functools import reduce


class OpenHAB(object):
    # base class
    def convert_to_string(self) -> List[str]:
        pass


class OHBase(OpenHAB):
    indent = '  '

    def convert_to_string_child(self, children: List[OpenHAB], indent: bool = True) -> List[str]:
        if not children:
            return []
        all_stats = []
        for child in children:
            all_stats.extend(child.convert_to_string())
        # add indentation to all strings
        if indent:
            all_stats = list(map(lambda x: self.indent + x, all_stats))
        return all_stats


class ChannelCommand(OHBase):
    """Commands for channels.

    Ex- stateTopic="relay_6_mpr_c/status"
    """
    def __init__(self, key, value):
        self.key = key
        self.value = value

    def __str__(self):
        return f'{self.key}="{self.value}"'

    def convert_to_string(self) -> str:
        return self.__str__()


class OHChannel(OHBase):
    """OpenHAB channel class"""
    def __init__(self, ch_type='string', name='', entity_name: str = ''):
        self.type: str = ch_type
        self.name: str = name
        self.commands: List[ChannelCommand] = []
        self.entity_name = entity_name  # ex- wifi_signal, relay_0 etc.
        self.thing: OHThings = None  # thing in which this channel is added. will be used in creating items.

    def __str__(self):
        return 'Channel ' + self.name

    def add_command(self, command: ChannelCommand):
        self.commands.append(command)

    def add_commands(self, commands: List[ChannelCommand]):
        self.commands.extend(commands)

    def add_thing(self, thing):
        self.thing = thing

    def get_channel_name(self) -> str:
        return self.name

    def get_entity_name(self) -> str:
        return self.entity_name

    def convert_to_string(self) -> List[str]:
        commands_str = map(lambda x: x.convert_to_string(), self.commands)
        commands = reduce(lambda x, y: f'{x}, {y}', commands_str)
        ch_str = f'Type {self.type} : {self.name} [ {commands} ]'
        return [ch_str]

    def channel_for_item(self) -> str:
        channel = f'{self.thing.thing_for_item()}:{self.name}'
        return channel


class OHThings(OHBase):
    def __init__(self, binding_id: str, type_id: str, thing_id: str, label: str = '', location: str = 'home'):
        self.binding_id: str = binding_id
        self.type_id: str = type_id
        self.thing_id: str = thing_id
        if label:
            self.label = label
        else:
            self.label = thing_id
        self.location: str = location
        self.channels: List[OHChannel] = []
        self.bridge: OHMqttBridge = None  # mqtt bridge in which this thing is added. Will be used in creating items.

    def add_channel(self, channel: OHChannel):
        self.channels.append(channel)

    def add_channels(self, channels: List[OHChannel]):
        self.channels.extend(channels)

    def add_bridge(self, bridge):
        self.bridge = bridge

    def thing_for_item(self) -> str:
        thing = f'{self.bridge.bridge_for_item()}:{self.thing_id}'
        return thing

    def get_thing_id(self) -> str:
        return self.thing_id

    def get_channels(self) -> List[OHChannel]:
        return self.channels


class OHMqttThings(OHThings):
    def __init__(self, thing_id: str, label: str = '', location: str = 'home'):
        super().__init__('', '', thing_id, label, location)

    def convert_to_string(self) -> List[str]:
        header = f'Thing topic {self.thing_id} "{self.label}" {{'
        channels = self.convert_to_string_child(self.channels)
        all_stats = [header, 'Channels:'] + channels + ['}', '']

        return all_stats


class OHMqttBridge(OHBase):
    def __init__(self, bridge_id: str = 'mybroker', mqtt_host: str = 'localhost', secure: bool = False,
                 username: str = '', password: str = ''):
        self.bridge_id = bridge_id
        self.mqtt_host = mqtt_host
        self.secure = secure
        self.mqtt_user_name = username
        self.mqtt_password = password
        self.things: List[OHThings] = []

    def convert_to_string(self) -> List[str]:
        header = f'Bridge mqtt:broker:{self.bridge_id} [ host="{self.mqtt_host}", secure={str(self.secure).lower()}'
        if self.mqtt_user_name:
            header += f', username="{self.mqtt_user_name}", password="{self.mqtt_password}"'
        header += ' ] {'
        things = self.convert_to_string_child(self.things)
        all_stats = [header] + things + ['}', '']

        return all_stats

    def add_thing(self, thing: OHThings):
        self.things.append(thing)

    def get_things(self) -> List[OHThings]:
        return self.things

    def bridge_for_item(self) -> str:
        bridge = f'mqtt:topic:{self.bridge_id}'
        return bridge


class OHItem(OHBase):
    def __init__(self, name: str = None, item_type: str = 'String', label: str = '', icon: str = None,
                 groups: List[str] = None, tags: List[str] = None, main_ui: str = 'yes', id: str = None,
                 raw_item: str = None, **kwargs):
        self.item_type = item_type
        self.item_name = name
        if label: self.label = label
        else: self.label = name
        self.icon = icon
        if groups: self.groups = groups
        else: self.groups = []
        if tags: self.tags = tags
        else: self.tags = []
        self.main_ui = main_ui
        self.id = id  # id of this item (this will match with channel entity).
        self.device_id: str = None
        self.raw_item = raw_item
        self.channel: OHChannel = None

    def add_channel(self, channel: OHChannel):
        self.channel = channel

    def add_group(self, group: str):
        self.groups.append(group)

    def add_groups(self, groups: List[str]):
        self.groups.extend(groups)

    def set_device_id(self, dev_id: str):
        self.device_id = dev_id

    def get_device_id(self) -> str:
        return self.device_id

    def get_item_id(self) -> str:
        return self.id

    def get_item_type(self) -> str:
        return self.item_type

    def get_item_name(self) -> str:
        return self.item_name

    def get_main_ui(self) -> str:
        return self.main_ui

    def convert_to_string(self) -> List[str]:
        if self.raw_item:
            return [self.raw_item]

        item = f'{self.item_type} {self.item_name}'
        if self.label:
            item += f' "{self.label}"'
        if self.icon:
            item += f' <{self.icon}>'
        if self.groups:
            grps = ', '.join(self.groups)
            item += f' ({grps})'
        if self.tags:
            tags_with_quotes = map(lambda x: f'"{x}"', self.tags)
            tags = ', '.join(tags_with_quotes)
            item += f' [{tags}]'
        if self.channel:
            item += f' {{channel="{self.channel.channel_for_item()}"}}'
        return [item]


class OHGroup(OHBase):
    def __init__(self, id: str = None, label: str = None, icon: str = None, groups: List[str] = None,
                 semantic_class: str = '', raw_grp: str = None, main_ui: str = 'yes'):
        self.id = id  # group name
        self.label = label
        self.icon = icon
        if groups: self.groups = groups
        else: self.groups = []
        self.semantic_class = semantic_class
        self.raw_grp = raw_grp
        self.main_ui = main_ui

    def get_main_ui(self) -> str:
        return self.main_ui

    def convert_to_string(self) -> List[str]:
        if self.raw_grp:
            return [self.raw_grp]

        group = f'Group {self.id}'
        if self.label:
            group += f' "{self.label}"'
        if self.icon:
            group += f' <{self.icon}>'
        if self.groups:
            grp_part_of = ', '.join(self.groups)
            group += f' ({grp_part_of})'
        if self.semantic_class:
            group += f' ["{self.semantic_class}"]'

        return [group]


class OHSiteMapItem(OHBase):
    def __init__(self, sitem_type: str = 'Default', item: Union[OHItem, str] = None, label: str = None,
                 icon: str = None, sitemap_extras: str = None, raw_sitem: str = None, **kwargs):
        self.stype = sitem_type  # type
        self.item = item
        self.label = label
        self.icon = icon
        self.sitemap_extras = sitemap_extras
        self.raw_sitem = raw_sitem
        self.children: List[OHSiteMapItem] = []

    def set_item(self, item):
        self.item = item

    def add_child(self, child):
        self.children.append(child)

    def add_children(self, children):
        self.children.extend(children)

    def convert_to_string(self) -> List[str]:
        if self.raw_sitem:
            return [self.raw_sitem]

        row = self.stype
        if isinstance(self.item, OHItem):
            row += f' item={self.item.get_item_name()}'
        elif self.item:
            row += f' item={self.item}'
        if self.label:
            row += f' label="{self.label}"'
        if self.icon:
            row += f' icon="{self.icon}"'
        if self.sitemap_extras:
            row += f' {self.sitemap_extras}'

        rows = [row]
        if self.children:
            rows = [row + ' {']
            rows += self.convert_to_string_child(self.children)
            rows.append('}')
            rows.append('')

        return rows


class OHSiteMapFrame(OHBase):
    def __init__(self, label: str = None):
        self.label = label
        self.children: List[OHSiteMapItem, OHSiteMapFrame] = []

    def add_child(self, child):
        self.children.append(child)

    def add_children(self, children):
        self.children.extend(children)

    def get_children(self) -> list:
        return self.children

    def convert_to_string(self) -> List[str]:
        # if no children, then skip this frame.
        if not self.children:
            return []

        row = f'Frame'
        if self.label:
            row += f' label="{self.label}"'
        row += ' {'

        rows = [row]
        if self.children:
            rows += self.convert_to_string_child(self.children)
        rows.append('}')
        rows.append('')

        return rows


class OHSiteMap(OHBase):
    def __init__(self, sitemapname: str = 'default', label: str = 'Home'):
        self.sitemapname = sitemapname
        self.label = label
        self.children: List[OHSiteMapFrame, OHSiteMapItem] = []

    def add_child(self, child):
        self.children.append(child)

    def add_children(self, children):
        self.children.extend(children)

    def convert_to_string(self) -> List[str]:
        row = f'sitemap {self.sitemapname} label="{self.label}" {{'
        rows = [row]
        if self.children:
            rows += self.convert_to_string_child(self.children)
        rows.append('}')

        return rows


if __name__ == '__main__':
    print('OpenHAB channel, items and sitemap DS module.')
