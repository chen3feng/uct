"""
File system utility.
"""

import fnmatch
import os
import pathlib
import subprocess
import sys

import console

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


def find_files_under(start_dir, patterns, excluded_dirs=None, relpath=False, limit=sys.maxsize) -> list:
    """Find files under dir matching pattern."""
    assert isinstance(patterns, list)
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
                    if len(result) >= limit:
                        return result
    return result


def find_source_files_under(start_dir, patterns, excluded_dirs=None, relpath=False, limit=sys.maxsize) -> list:
    """Find source files under dir matching pattern."""
    result = []
    excluded_dirs = ['Binaries', 'Intermediate']
    result += _find_files_under_subdir(start_dir, 'Source', patterns, excluded_dirs=excluded_dirs,
                                       relpath=relpath, limit=limit)
    if len(result) >= limit:
        return result
    result += _find_files_under_subdir(start_dir, 'Plugins', patterns, excluded_dirs=excluded_dirs,
                                       relpath=relpath, limit=limit-len(result))
    return result


def _find_files_under_subdir(start_dir, subdir, patterns, relpath, **kwargs) -> list:
    files = find_files_under(os.path.join(start_dir, subdir), patterns, relpath=relpath, **kwargs)
    if relpath:
        return [os.path.join(subdir, f) for f in files]
    return files


def expand_source_files(files, engine_dir) -> list:
    """
    Expand source file patterns to file list.
    files support the following format:
        An absolute path: /Work/MyGame/Source/MyGame/HelloWorldGreeterImpl.cpp
        A relative path: MyGame/HelloWorldGreeterImpl.cpp
        A wildcard pattern: Source/**/*Test.cpp
        A wildcard pattern with the @engine prefix: @engine/**/NetDriver.cpp
    Returns:
        A list of absolute paths of matching files.
    """
    matched_files = []
    patterns = []
    for file in files:
        start_dir = os.getcwd()
        if file.startswith('@engine'):
            file = file.removeprefix('@engine')
            if file.startswith('/') or file.startswith('\\'):
                file = file[1:]
            start_dir = engine_dir
        if not is_wildcard(file):
            matched_files.append(os.path.join(start_dir, file))
        else:
            patterns.append((start_dir, file))

    if patterns:
        for start_dir, pattern in patterns:
            for path in pathlib.Path(start_dir).glob(pattern):
                if 'Intermediate' in path.parts:
                    continue
                matched_files.append(str(path.absolute()))

    return matched_files


def reveal_file(path):
    """Open a file in system specific file explorer."""
    if _in_vscode():
        return _reveal_file_vscode(path)
    if _in_visual_studio():
        return _reveal_file_visual_studio(path)
    if sys.platform.startswith('win'):
        return _reveal_file_windows(path)
    if sys.platform.startswith('darwin'):
        return _reveal_file_mac(path)
    console.error(f'Unsupported platform {sys.platform}')
    return 1


def _in_vscode():
    if os.environ.get('TERM_PROGRAM') != 'vscode':
        return False
    if os.name == 'nt':
        return subprocess.call('where code', stdout=subprocess.DEVNULL) == 0
    return subprocess.call(['which', 'code'], stdout=subprocess.DEVNULL) == 0


def _in_visual_studio():
    return os.environ.get('VSAPPIDNAME')


def _reveal_file_visual_studio(path):
    return subprocess.call(f'{os.environ.get("VSAPPIDNAME")} /edit "{path}"')


def _reveal_file_windows(path):
    # pylint: disable=all
    # Taken from https://github.com/exaile/exaile/blob/master/xl/common.py#L352
    #
    # We could run `explorer /select,filename`, but that doesn't support
    # reusing an existing Explorer window when selecting a file in a
    # directory that is already open.

    import ctypes # pylint: disable=import-outside-toplevel

    CoInitialize = ctypes.windll.ole32.CoInitialize
    CoInitialize.argtypes = [ctypes.c_void_p]
    CoInitialize.restype = ctypes.HRESULT
    CoUninitialize = ctypes.windll.ole32.CoUninitialize
    CoUninitialize.argtypes = []
    CoUninitialize.restype = None
    ILCreateFromPath = ctypes.windll.shell32.ILCreateFromPathW
    ILCreateFromPath.argtypes = [ctypes.c_wchar_p]
    ILCreateFromPath.restype = ctypes.c_void_p
    ILFree = ctypes.windll.shell32.ILFree
    ILFree.argtypes = [ctypes.c_void_p]
    ILFree.restype = None
    SHOpenFolderAndSelectItems = ctypes.windll.shell32.SHOpenFolderAndSelectItems
    SHOpenFolderAndSelectItems.argtypes = [
        ctypes.c_void_p,
        ctypes.c_uint,
        ctypes.c_void_p,
        ctypes.c_ulong,
    ]
    SHOpenFolderAndSelectItems.restype = ctypes.HRESULT

    CoInitialize(None)
    pidl = ILCreateFromPath(path)
    res = SHOpenFolderAndSelectItems(pidl, 0, None, 0)
    ILFree(pidl)
    CoUninitialize()
    return int(res)

    # This method is much slower and alyways returns 1.
    # cmd = ['explorer.exe', f'/select,"{path}"']
    # return subprocess.call(' '.join(cmd))


def _reveal_file_vscode(path):
    cmd = ['code', path]
    if os.name == 'nt':
        return subprocess.call(' '.join(cmd), shell=True)
    return subprocess.call(cmd)


def _reveal_file_mac(path):
    cmd = ['open', '--reveal', path]
    return subprocess.call(cmd)
