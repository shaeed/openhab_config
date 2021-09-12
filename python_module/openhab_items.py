"""
Items will be generated from items added under my devices.
"""

from openhab_ds import OHItem, OHGroup
from devices import RootDev
from typing import List


def create_items(devices: List[RootDev]) -> List[OHItem]:
    all_items = []
    for dev in devices:
        all_items.extend(dev.create_items())

    # print
    # items_str = map(lambda x: x.convert_to_string(), all_items)
    # items_str2 = reduce(lambda x, y: x + y, items_str)
    # text = '\n'.join(items_str2)
    # print(text)

    return all_items


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
