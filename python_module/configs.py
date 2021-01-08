
import yaml

device_config_path = r'device_configs.yaml'
esphab_config_path = r'esphome_gen.yaml'


def read_yaml_file(file_path: str) -> dict:
    with open(file_path, 'r') as p_file:
        return yaml.load(p_file, Loader=yaml.SafeLoader)


def get_device_configs() -> dict:
    return read_yaml_file(device_config_path)


def get_esphome_openhab_config() -> dict:
    return read_yaml_file(esphab_config_path)