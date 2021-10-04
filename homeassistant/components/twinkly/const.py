"""Const for Twinkly."""

DOMAIN = "twinkly"

# Keys of the config entry
CONF_ENTRY_ID = "id"
CONF_ENTRY_HOST = "host"
CONF_ENTRY_NAME = "name"
CONF_ENTRY_MODEL = "model"

# Strongly named HA attributes keys
ATTR_HOST = "host"

# Keys of attributes read from the get_device_info
DEV_ID = "uuid"
DEV_NAME = "device_name"
DEV_MODEL = "product_code"
DEV_ATTRIBUTES = {
    ### Device identification
    "product_name": str,  # eg. 'Twinkly'
    # "product_code": str, # Already exposed in the normalized 'model' property, eg. 'TWI190SPP'
    # "device_name": str, # Name given by the user, already exposed in the normalized 'name' property
    # "uuid": uuid.UUID,  # Already exposed as id of the entity eg. 'C8D50BDB-5F6E-497D-A64D-57C6FD2E3A2A'
    "hardware_version": str,  # Received as quoted string, so we keep original format eg. '100'
    "hw_id": str,  # eg. '5f1cfc'
    ### Device status
    "uptime": int,  # Received as quoted string, eg. '1527920729'
    "measured_frame_rate": float,  # eg. 28.57
    "fw_family": str,  # eg. 'G'
    ### Flashing information
    "flash_size": int,  # eg. 64
    "movie_capacity": int,  # eg. 992
    "bytes_per_led": int,  # eg. 4
    "max_supported_led": int,  # eg. 1200
    "number_of_led": int,  # eg. 190
    "led_profile": str,  # eg. 'RGBW'
    "led_type": int,  # eg. 12
    "frame_rate": int,  # eg. 24
    "wire_type": int,  # eg. 4
    ### Irrelevant values
    # "copyright" # We should not display a copyright "LEDWORKS 2018" in the Home-Assistant UI
    # "mac" # Does not report the actual device mac address
    # "code" # This is the internal status code of the API response
}
