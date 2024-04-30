"""
Unreal Engine management.
"""

import configparser
import itertools
import json
import os
import platform

from typing import Tuple

import console


def _installed_engine_registry() -> str:
    path = 'Epic/UnrealEngineLauncher/LauncherInstalled.dat'
    if platform.system() == 'Windows':
        return os.path.join(os.path.expandvars('%ProgramData%'), path).replace('/', '\\')
    if platform.system() == 'Darwin':
        return os.path.expanduser('~/Library/Application Support/' + path)
    if platform.system() == 'Linux':
        return os.path.expanduser('~/.config/') + path
    assert False, f'Unsupported platform {platform.system()}'
    return ''

def _source_build_engine_registry() -> str:
    if platform.system() == 'Windows':
        return r"HKEY_CURRENT_USER\Software\Epic Games\Unreal Engine\Builds"
    path = '~/.config/Epic/UnrealEngine/Install.ini'
    if platform.system() == 'Darwin':
        path = '~/Library/Application Support/Epic/UnrealEngine/Install.ini'
    return os.path.expanduser(path)


INSTALLED_REGISTRY = _installed_engine_registry()
SOURCE_BUILD_REGISTRY = _source_build_engine_registry()


class Engine:
    """Engine class."""
    def __init__(self, id, root) -> None:
        self.id = id
        self.root = root
        self.version, self.major_version = parse_version(root)
        self.is_installed = os.path.join(root, 'Engine/Build', 'InstalledBuild.txt')

    def __repr__(self) -> str:
        return f'{self.id}  {self.version_string():8} {self.root}'

    def version_string(self):
        ver = self.version
        return f"{ver['MajorVersion']}.{ver['MinorVersion']}.{ver['PatchVersion']}"


def find_source_builds() -> list:
    """Find all source build engines in current system."""
    if os.name == 'posix':
        return _find_built_engines_posix()
    elif os.name == 'nt':
        return _find_built_engines_windows()
    return []


def _find_built_engines_posix() -> list:
    config_file = SOURCE_BUILD_REGISTRY
    config = configparser.ConfigParser()
    config.read(config_file)
    if 'Installations' not in config:
        console.error(f"Invalid config file '{config_file}'.")
        return []
    engines = []
    for uuid, root in config['Installations'].items():
        if not os.path.exists(root):
            console.warn(f"Source build engine: {root} doesn't exist.")
            continue
        uuid = uuid.upper()
        if not uuid.startswith('{'): # UE4 format: ID isn't enclosed in '{}'
            uuid = '{' + uuid + '}'
        engines.append(Engine(uuid, root))

    return engines


def _find_built_engines_windows() -> list:
    # On windows, this program is always called from the uct.bat,
    # finding engine by project was done there, we needn't query registry here.
    import winreg # pylint: disable=import-outside-toplevel,import-error
    engines = []
    try:
        key_name = r"Software\Epic Games\Unreal Engine\Builds"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_name) as hkey:
            for i in itertools.count():
                try:
                    uuid, value, value_type = winreg.EnumValue(hkey, i)
                    if value_type == winreg.REG_SZ:
                        path = os.path.normpath(value)
                        if not os.path.exists(path):
                            console.warn(f"Source build engine {uuid}: {path} doesn't exist.")
                            continue
                        engines.append(Engine(uuid, path))
                except OSError:
                    # ERROR_NO_MORE_ITEMS
                    break
    except OSError as e:
        print(f"winreg.OpenKey: {e}: '{key_name}'.")

    return engines


def find_installed() -> list:
    """Find all installed engines in current system."""
    engines = []
    try:
        with open(INSTALLED_REGISTRY, encoding='utf8') as f:
            for install in json.load(f)['InstallationList']:
                name = install['AppName']
                if name.startswith('UE_'):
                    location = install['InstallLocation']
                    if not os.path.exists(location):
                        console.warn(f"Installed engine {name}: {location} doesn't exist.")
                        continue
                    engines.append(Engine(name, location))
    except FileNotFoundError:
        # There can be no installed engine.
        pass
    return engines

def parse_version(engine_root) -> Tuple[dict, int]:
    """Parse version information of an engine."""
    with open(os.path.join(engine_root, 'Engine/Build/Build.version'), encoding='utf8') as f:
        version = json.load(f)
        return version, int(version['MajorVersion'])
