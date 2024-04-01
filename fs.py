"""
File system utility.
"""

import fnmatch
import os


def is_wildcard(text):
    """Check whether a string is a wildcard."""
    for c in text:
        if c in '*?![]':
            return True
    return False


def find_file_bottom_up(pattern, from_dir=None) -> str:
    """Find the specified file/dir from from_dir bottom up until found or failed.
       Returns abspath if found, or empty if failed.
    """
    if from_dir is None:
        from_dir = os.getcwd()
    finding_dir = os.path.abspath(from_dir)
    while True:
        files = os.listdir(finding_dir)
        for file in files:
            if fnmatch.fnmatch(file, pattern):
                return os.path.join(finding_dir, file)
        parent_dir = os.path.dirname(finding_dir)
        if parent_dir == finding_dir:
            return ''
        finding_dir = parent_dir
    return ''


def find_files_under(start_dir, patterns, excluded_dirs=None, relpath=False) -> list:
    """Find files under dir matching pattern."""
    result = []
    for root, dirs, files in os.walk(start_dir):
        if excluded_dirs:
            dirs[:] = [d for d in dirs if d not in excluded_dirs]
        for file in files:
            for pattern in patterns:
                if fnmatch.fnmatch(file, pattern):
                    path = os.path.join(root, file)
                    if relpath:
                        path = os.path.relpath(path, start_dir)
                    result.append(path)
    return result
