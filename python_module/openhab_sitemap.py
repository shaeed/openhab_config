"""
Sitemap will be generated from items added under my devices and Sitemap data from my devices.
"""

from openhab_ds import OHItem, OHSiteMapFrame, OHBase, OHSiteMap, OHSiteMapItem, OHGroup
from typing import List, Union
from functools import reduce


def create_sitemap(items: List[OHItem], groups: List[OHGroup], sitemap_data: dict, devices: List[dict]) -> OHSiteMap:
    # sitemap label
    label = 'Home'
    if 'label' in sitemap_data:
        label = sitemap_data['label']

    sitemap = OHSiteMap(label=label)
    # user sitemap
    if 'items' in sitemap_data:
        children = create_sitems(sitemap_data['items'], items)
        sitemap.add_children(children)

    # items from configured devices & groups
    dev_sitems = sitemap_for_devices(items, groups, devices)
    sitemap.add_children(dev_sitems)

    # text = '\n'.join(sitemap.convert_to_string())
    # print(text)
    return sitemap


def create_sitems(sitems: list, items: List[OHItem]) -> List[OHBase]:
    created_sitems = []
    for data in sitems:
        created_sitem = create_sitem(data, items)
        created_sitems.append(created_sitem)
    return created_sitems


def create_sitem(sitemap_data: Union[str, dict], items: List[OHItem]) -> OHBase:
    can_have_child = False
    if isinstance(sitemap_data, str):
        sitem = OHSiteMapItem(raw_sitem=sitemap_data)
    elif sitemap_data['stype'] == 'Frame':
        sitem = OHSiteMapFrame(label=sitemap_data['label'])
        can_have_child = True
    else:
        sitem = OHSiteMapItem(**sitemap_data)
        if 'dev_id' in sitemap_data:
            # search for exact item in items list
            item_from_dev = get_item(sitemap_data['item'], sitemap_data['dev_id'], items)
            sitem.item = item_from_dev
        can_have_child = True

    if can_have_child and 'items' in sitemap_data:
        children = create_sitems(sitemap_data['items'], items)
        sitem.add_children(children)

    return sitem


def get_item(item_id: str, dev_id: str, items: List[OHItem]) -> Union[OHItem, str]:
    for item in items:
        if item.get_device_id() == dev_id and item.get_item_id() == item_id:
            return item
    return item_id


def sitemap_for_devices(items: List[OHItem], groups: List[OHGroup], devices: List[dict]) -> List[OHBase]:
    # status and settings frame
    status_frame = OHSiteMapFrame()
    status_settings = OHSiteMapItem(sitem_type='Text', label='Status & Settings', icon='settings')
    status_frame.add_child(status_settings)

    # all the individual device frames
    devices_frame = OHSiteMapFrame()

    for device in devices:
        dev_entry = OHSiteMapItem(sitem_type='Text', label=device['name'], icon=device['icon'])
        dev_setting_frame = OHSiteMapFrame(label=device['name'])

        flag_add_dev_frame = False
        flag_add_dev_setting_frame = False
        for item in device['items']:
            if isinstance(item, str):
                continue
            actual_item = get_item(item['id'], device['id'], items)
            if 'sitem_type' in item:
                # this is just sitemap component
                actual_sitem = OHSiteMapItem(**item)
                actual_sitem.set_item(actual_item)
            else:
                actual_sitem = OHSiteMapItem(item=actual_item)
            if 'main_ui' in item and not item['main_ui']:
                dev_setting_frame.add_child(actual_sitem)
                flag_add_dev_setting_frame = True
            else:
                dev_entry.add_child(actual_sitem)
                flag_add_dev_frame = True
        if flag_add_dev_frame:
            devices_frame.add_child(dev_entry)
        if flag_add_dev_setting_frame:
            status_settings.add_child(dev_setting_frame)
    # add group to status and settings
    group_sitem = sitemap_for_groups(groups)
    status_settings.add_child(group_sitem)

    return [status_frame, devices_frame]


def sitemap_for_groups(groups: List[OHGroup]) -> OHBase:
    group_frame = OHSiteMapFrame()
    for group in groups:
        if group.raw_grp:
            continue
        group_sitem = OHSiteMapItem(sitem_type='Group', item=group.id, label=group.label, icon=group.icon)
        group_frame.add_child(group_sitem)
    return group_frame
