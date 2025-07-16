"""
The config module.
"""

PLATFORM_MAP = {
    'win64': 'Win64',
    'linux': 'Linux',
    'linuxarm64': 'LinuxArm64',
    'mac': 'Mac',
    'android': 'Android',
    'ios': 'IOS',
    'tvos': 'TVOS',
    'hololens': 'HoloLens',
}

CONFIG_MAP = {
    'debug': 'Debug',
    'dbg': 'Debug',
    'debuggame': 'DebugGame',
    'dbgm': 'DebugGame',
    'dev': 'Development',
    'ship': 'Shipping',
    'test': 'Test',
}

CONFIG_FILE_PATH = '~/.local/uct/Config.ini'
