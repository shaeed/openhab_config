"""
Sitemap will be generated from items added under my devices and Sitemap data from my devices.
"""

from openhab_ds import OHItem, OHSiteMapFrame, OHBase, OHSiteMap, OHSiteMapItem, OHGroup
from openhab_things import get_thing_and_dev_type, get_wled_thing_id
from configs import get_device_configs
from typing import List, Union, Tuple


def create_sitemap(items: List[OHItem], groups: List[OHGroup], data: dict, devices: List[dict]) -> OHSiteMap:
    # sitemap label
    label = 'Home'
    if 'sitemap' in data and 'lable' in data['sitemap']:
        label = data['sitemap']['label']

    sitemap = OHSiteMap(label=label)
    # user sitemap
    if 'sitemap' in data and 'items' in data['sitemap']:
        children = create_sitems(data['sitemap']['items'], items)
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


def get_device_sitemap_frames(device: dict, devices: List[dict]):
    dev_frame = OHSiteMapFrame(label=device['name'])
    # status & settings item
    # check if device name is used more than 1
    dev_name_count = sum([1 for x in devices if x['name'] == device['name']])
    if dev_name_count == 1:
        # just one instance
        dev_setting_frame = OHSiteMapFrame(label=device['name'])
    else:
        # more than one instance (Add device id also in label)
        dev_setting_frame = OHSiteMapFrame(label=f"{device['name']} ({device['id']})")

    return dev_frame, dev_setting_frame


def get_location_dev_frame(devices_frame: OHSiteMapFrame, label: str, icon: str) -> Tuple[OHSiteMapItem, bool]:
    for child in devices_frame.get_children():
        if label == child.label:
            dev_frame = child
            return dev_frame, False
    else:
        dev_frame = OHSiteMapItem(sitem_type='Text', label=label, icon=icon)
        return dev_frame, True


def sitemap_for_devices(items: List[OHItem], groups: List[OHGroup], devices: List[dict]) -> List[OHBase]:
    # status and settings frame
    status_frame = OHSiteMapFrame()
    status_settings = OHSiteMapItem(sitem_type='Text', label='Status & Settings', icon='settings')
    status_frame.add_child(status_settings)
    # all the individual device frames
    collapse_dev_frame = OHSiteMapFrame()

    # sitemap items/frames
    all_sitems = [collapse_dev_frame]

    for device in devices:
        print(f'[sitemap] Creating sitemap for {device["name"]}.')
        dev_frame, dev_sett_frame = sitemap_for_device(device, devices, items)
        if dev_frame:
            if device['parent']:
                # get frame for devices belongs to Location
                parent_frame, is_new = get_location_dev_frame(collapse_dev_frame, device['parent']['label'],
                                                              device['parent']['icon'])
                if is_new:
                    collapse_dev_frame.add_child(parent_frame)
                if 'expand' in device and device['expand']:
                    # expanded device under location
                    parent_frame.add_child(dev_frame)
                else:
                    # don't expand device under location
                    dev_text = OHSiteMapItem(sitem_type='Text', label=device['name'], icon=device['icon'])
                    dev_text.add_child(dev_frame)
                    parent_frame.add_child(dev_text)
            else:
                if 'expand' in device and device['expand']:
                    # Need to expand this device on home screen
                    all_sitems.append(dev_frame)
                else:
                    # add under collapsed devices
                    parent_frame, is_new = get_location_dev_frame(collapse_dev_frame, device['name'], device['icon'])
                    if is_new:
                        collapse_dev_frame.add_child(parent_frame)
                    parent_frame.add_child(dev_frame)
        if dev_sett_frame:
            status_settings.add_child(dev_sett_frame)
    # end for

    # add group to status and settings
    group_sitem = sitemap_for_groups(groups)
    status_settings.add_child(group_sitem)

    all_sitems.append(status_frame)

    return all_sitems


def sitemap_for_device(device: dict, devices: List[dict], items: List[OHItem]):
    dev_entry, dev_setting_frame = get_device_sitemap_frames(device, devices)
    flag_add_dev_frame = False
    flag_add_dev_setting_frame = False
    dev_id, items_data = get_device_id_and_items(device)
    for item in items_data:
        if isinstance(item, str):
            # raw items, no need to add in sitemaps
            continue
        actual_item = get_item(item['id'], dev_id, items)
        if 'sitem_type' in item:
            # this is just sitemap component
            actual_sitem = OHSiteMapItem(**item)
            actual_sitem.set_item(actual_item)
        else:
            actual_sitem = OHSiteMapItem(item=actual_item)

        # where to add this item/sitem
        flag_dev, flag_setting = add_item_to_places(item, actual_sitem, dev_entry, dev_setting_frame)
        flag_add_dev_frame = flag_dev or flag_add_dev_frame
        flag_add_dev_setting_frame = flag_setting or flag_add_dev_setting_frame
    # end for
    ret = (dev_entry if flag_add_dev_frame else None, dev_setting_frame if flag_add_dev_setting_frame else None)
    return ret


def get_device_id_and_items(device: dict) -> Tuple[str,  List[dict]]:
    thing_type, dev_type = get_thing_and_dev_type(device['type'])
    if thing_type == 'mqtt' and 'items' in device:
        return device['id'], device['items']
    elif thing_type == 'wled':
        device_config = get_device_configs()
        dev_id = get_wled_thing_id(device['id'])
        return dev_id, device_config[dev_type]['items']
    return device['id'], []


def add_item_to_places(item: dict, actual_sitem: OHSiteMapItem, dev_entry, dev_setting_frame):
    flag_add_dev_frame = False
    flag_add_dev_setting_frame = False

    if 'main_ui' not in item:
        # default case, add it to main ui
        dev_entry.add_child(actual_sitem)
        flag_add_dev_frame = True
    else:
        if 'yes' in item['main_ui']:
            dev_entry.add_child(actual_sitem)
            flag_add_dev_frame = True
        if 'setting' in item['main_ui']:
            dev_setting_frame.add_child(actual_sitem)
            flag_add_dev_setting_frame = True

    return flag_add_dev_frame, flag_add_dev_setting_frame


def sitemap_for_groups(groups: List[OHGroup]) -> OHBase:
    group_frame = OHSiteMapFrame()
    for group in groups:
        if group.raw_grp:
            continue
        if group.get_main_ui() == 'no':
            continue
        group_sitem = OHSiteMapItem(sitem_type='Group', item=group.id, label=group.label, icon=group.icon)
        group_frame.add_child(group_sitem)
    return group_frame
