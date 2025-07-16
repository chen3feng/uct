"""
# This module provides functionality to handle command aliases similar to shell aliases.
# It allows adding aliases, loading them from an INI file, and expanding commands.
"""

import os
import sys
import configparser
import shlex
from typing import List


class CommandAlias:
    """Class to handle command aliases, similar to shell aliases"""
    def __init__(self):
        self.aliases: dict[str, str] = {}

    def add(self, alias: str, command: str):
        """Adds an alias for a command"""
        self.aliases[alias] = command

    def load(self, inifile: str) -> bool:
        """Loads aliases from an INI file"""
        if not inifile:
            # print('No INI file specified for command aliases.')
            return False
        inifile = os.path.expanduser(inifile)
        if not os.path.exists(inifile):
            # print(f'INI file {inifile} does not exist.')
            return False
        config = configparser.ConfigParser()
        config.read(inifile, encoding='utf-8')
        if 'Alias' not in config:
            # print(f'No [Alias] section found in {inifile}.')
            return False
        for key, value in config['Alias'].items():
            self.add(key.strip(), value.strip())
        return True

    def clear(self):
        """Clears all aliases"""
        self.aliases.clear()

    def __bool__(self) -> bool:
        """Returns True if there are any aliases defined"""
        return bool(self.aliases)

    def has(self, alias: str) -> bool:
        """Checks if an alias exists"""
        return alias in self.aliases

    def get(self, alias: str) -> str:
        """Returns the command for a given alias"""
        return self.aliases.get(alias, '')

    def __str__(self) -> str:
        """String representation of the command aliases"""
        if not self.aliases:
            return 'No command aliases defined.'
        return 'command aliases:\n' + '\n'.join(f'  {alias} = {command}' for alias, command in self.aliases.items())

    def expand(self, cmd: str) -> List[str]:
        """Expands a single alias to a command list (like shlex.split)"""
        if cmd in self.aliases:
            return shlex.split(self.aliases[cmd])
        return [cmd]

    def expand_argv(self, argv: List[str] = None) -> List[str]:
        """Expands argv with alias substitution on argv[1]"""
        if argv is None:
            argv = sys.argv

        if len(argv) >= 2:
            first = argv[1]
            if first in self.aliases:
                expanded = self.expand(first)
                return [argv[0]] + expanded + argv[2:]

        return argv
