"""
Console and log support.
"""

import os
import sys
import subprocess

ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
INVALID_HANDLE_VALUE = -1

def _windows_console_support_ansi_color():
    from ctypes import byref, windll, wintypes # pylint: disable=import-outside-toplevel

    handle = windll.kernel32.GetStdHandle(subprocess.STD_OUTPUT_HANDLE)
    if handle == INVALID_HANDLE_VALUE:
        return False

    mode = wintypes.DWORD()
    if not windll.kernel32.GetConsoleMode(handle, byref(mode)):
        return False

    if not (mode.value & ENABLE_VIRTUAL_TERMINAL_PROCESSING):
        if windll.kernel32.SetConsoleMode(
            handle,
            mode.value | ENABLE_VIRTUAL_TERMINAL_PROCESSING) == 0:
            print('kernel32.SetConsoleMode to enable ANSI sequences failed',
                file=sys.stderr)
    return True

def _console_support_ansi_color():
    if os.name == 'nt':
        return _windows_console_support_ansi_color()
    return sys.stdout.isatty() and os.environ.get('TERM') not in ('emacs', 'dumb')

# Global color enabled or not
_color_enabled = _console_support_ansi_color()

_COLORS = {
    'red': '\033[1;31m',
    'green': '\033[1;32m',
    'yellow': '\033[1;33m',
    'blue': '\033[1;34m',
    'purple': '\033[1;35m',
    'cyan': '\033[1;36m',
    'white': '\033[1;37m',
    'gray': '\033[1;38m',
    'dimpurple': '\033[2;35m',
    'end': '\033[0m',
}

# Global color enabled or not
_color_enabled = (sys.stdout.isatty() and
                  os.environ.get('TERM') not in ('emacs', 'dumb'))

def colored(text, color):
    """Return ansi color code enclosed text"""
    if _color_enabled:
        return _COLORS[color] + text + _COLORS['end']
    return text


def error(message: str) -> None:
    """Write a error message to the console."""
    print(colored(f'Error: {message}', 'red'), file=sys.stderr)


def warn(message: str) -> None:
    """Write a warning message to the console."""
    print(colored(f'Warning: {message}', 'yellow'), file=sys.stderr)


def info(message: str) -> None:
    """Write a info message to the console."""
    print(colored(f'Info: {message}', 'cyan'), file=sys.stderr)
