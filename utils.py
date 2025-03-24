"""
Some utility functions.
"""

import subprocess
import os

from typing import Union, List


def subprocess_call(cmd: Union[str, List[str]], *args, **kwargs) -> int:
    """Run an external command."""
    if os.name == 'nt' and isinstance(cmd, list):
        # Windows can't handle command arguments correctly.
        # For example, in the handling of test command,
        # neither pass the list directly nor use subprocess.list2cmd works because they convert
        # -ExecCmds="Automation List; Quit" to "-ExecCmds=\"Automation List; Quit\"",
        # But simplay join the list with spaces works.
        return subprocess.call(' '.join(cmd), *args, **kwargs)
    return subprocess.call(cmd, *args, **kwargs)


def subprocess_run(cmd: Union[str, List[str]], *args, **kwargs):
    """Run an external command."""
    if os.name == 'nt' and isinstance(cmd, list):
        # For the above same reason.
        return subprocess.run(' '.join(cmd), *args, **kwargs, check=False)
    return subprocess.run(cmd, *args, **kwargs, check=False)
