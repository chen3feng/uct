import os
import sys
import termios

from ._config import config


# Initially taken from:
# http://code.activestate.com/recipes/134892/
# Thanks to Danny Yoo
# more infos from:
# https://gist.github.com/michelbl/efda48b19d3e587685e3441a74457024
# Thanks to Michel Blancard
def _readkeybuffer(maxlength: int) -> str:
    """Reads at most  maxlength characters from the input stream.
    Blocks until a character is available."""

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    term = termios.tcgetattr(fd)
    try:
        # http://www.unixwiz.net/techtips/termios-vmin-vtime.html
        term[3] &= ~(termios.ICANON | termios.ECHO | termios.IGNBRK | termios.BRKINT)
        term[6][termios.VMIN] = 1  # wait at least one character
        term[6][termios.VTIME] = 0 #
        termios.tcsetattr(fd, termios.TCSAFLUSH, term)
        ch = os.read(fd, maxlength).decode('utf8')
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch


def readchar() -> str:
    """Reads a single character from the input stream.
    Blocks until a character is available."""
    return _readkeybuffer(1)


def readkey() -> str:
    """Get a keypress. If an escaped key is pressed, the full sequence is
    read and returned as noted in `_posix_key.py`."""
    # It can be quite long when input is from IME.
    return _readkeybuffer(1000)
