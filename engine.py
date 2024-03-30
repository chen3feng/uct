"""
Unreal Engine management.
"""

import configparser
import json
import os
import platform

from typing import Tuple

import console


def _installed_engine_registry() -> str:
    path = 'Epic/UnrealEngineLauncher/LauncherInstalled.dat'
    if os.name == 'nt':
        path = os.path.join(os.path.expandvars('%ProgramData%'), path).replace('/', '\\')
    else:
        path = os.path.expanduser('~/Library/Application Support/' + path)
    return path


def _built_engine_registry() -> str:
    path = '~/.config/Epic/UnrealEngine/Install.ini'
    if platform.system() == 'Darwin':
        path = '~/Library/Application Support/Epic/UnrealEngine/Install.ini'
    return os.path.expanduser(path)


INSTALLED_REGISTRY = _installed_engine_registry()
BUILT_REGISTRY = _built_engine_registry()



class Engine:
    """Engine class."""
    def __init__(self, id, root) -> None:
        self.id = id
        self.root = root
        self.version, self.major_version = parse_version(root)

    def __repr__(self) -> str:
        ver = self.version
        version = f'{ver['MajorVersion']}.{ver['MinorVersion']}.{ver['PatchVersion']}'
        return f'{self.id}  {version:8} {self.root}'


def find_builts() -> list:
    """Find all source built engines in current system."""
    if os.name == 'posix':
        return _find_built_engines_posix()
    elif os.name == 'nt':
        return _find_built_engines_windows()
    return []


def _find_built_engines_posix() -> list:
    config_file = BUILT_REGISTRY
    config = configparser.ConfigParser()
    config.read(config_file)
    if 'Installations' not in config:
        console.error(f"Invalid config file '{config_file}'.")
        return []
    engines = []
    for id, root in config['Installations'].items():
        if not os.path.exists(root):
            console.warn(f"Find built engines: {root} doesn't exist.")
            continue
        id = id.upper()
        if not id.startswith('{'): # UE4 format: ID isn't enclosed in '{}'
            id = '{' + id + '}'
        engines.append(Engine(id, root))

    return engines


def _find_built_engines_windows() -> list:
    # On windows, this program is always called from the uct.bat,
    # finding engine by project was done there, we needn't query registry here.
    return []


def find_installed() -> list:
    """Find all installed engines in current system."""
    engines = []
    with open(INSTALLED_REGISTRY, encoding='utf8') as f:
        for install in json.load(f)['InstallationList']:
            name = install['AppName']
            if name.startswith('UE_'):
                engines.append(Engine(name, install['InstallLocation']))
    return engines

def parse_version(engine_root) -> Tuple[dict, int]:
    """Parse version information of an engine."""
    with open(os.path.join(engine_root, 'Engine/Build/Build.version'), encoding='utf8') as f:
        version = json.load(f)
        return version, int(version['MajorVersion'])
