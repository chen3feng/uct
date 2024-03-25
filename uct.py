"""
UCT -- Unreal Command Tool.
A powerful command line tool for unreal engine.
"""

import argparse
import configparser
import fnmatch
import json
import os
import re
import platform
import subprocess
import sys

import console

from typing import Optional

# https://pypi.org/project/argcomplete/
# PYTHON_ARGCOMPLETE_OK
try:
    # pyright: reportMissingImports=false
    import argcomplete
except ImportError:
    argcomplete = None

VERSION = '0.1'

PLATFORM_MAP = {
    'win64': 'Win64',
    'linux': 'Linux',
    'mac': 'Mac'
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

# https://www.gnu.org/software/bash/manual/html_node/Exit-Status.html
EXIT_COMMAND_NOT_FOUND = 127


def build_arg_parser():
    """
    Build the argument parser.

    This command parser support multiple subcommands. Each subcommand has its own
    set of arguments.
    """
    parser = argparse.ArgumentParser(prog='UCT', description='Unreal command line tool')
    parser.add_argument('--version', action='version', version='%(prog)s ' + VERSION)

    subparsers = parser.add_subparsers(dest='command', help='Available subcommands')
    subparsers.required = True

    config = argparse.ArgumentParser(add_help=False)
    config.add_argument('-p', '--platform', dest='platform', type=str,
                        choices=PLATFORM_MAP.keys(),
                        help='target platform')
    config.add_argument('-c', '--config', dest='config', type=str,
                        choices=CONFIG_MAP.keys(),
                        help='build configuration')

    build_parents = [config]

    subparsers.add_parser('generate-project-files', help='Generate project files')

    list_targets = subparsers.add_parser('list-targets', help='List targets')
    list_targets.add_argument('--project', action='store_true')
    list_targets.add_argument('--engine', action='store_true')
    list_targets.add_argument('--verbose', action='store_true')

    build = subparsers.add_parser('build', help='Build specified targets', parents=build_parents)

    build.add_argument('-m', '--modules', type=str, nargs='+',
                        help='modules to build')
    build.add_argument('-f', '--files', type=str, nargs='+',
                        help='source files to compile')

    subparsers.add_parser('clean', help='Clean specified targets', parents=build_parents)

    subparsers.add_parser(
        'run',
        help='Build and run a single target',
        epilog='Any arguments after the empty "--" will be passed to the program',
        parents=build_parents)

    test = subparsers.add_parser(
        'test',
        help='Build and run tests',
        epilog='Any arguments after the empty "--" will be passed to the program',
        parents=[config])
    test.add_argument('--list', dest='list', action='store_true', help='list all tests')
    test.add_argument('--run-all', dest='run_all', action='store_true', help='Run all test')
    test.add_argument('--run', dest='tests', type=str,  nargs='+', help='Run tests')
    test.add_argument('--cmds', dest='test_cmds', type=str, nargs='+', help='Any extra test commands')

    return parser


def parse_command_line():
    """Parse and validate commandparameters"""
    parser = build_arg_parser()

    if argcomplete:
        argcomplete.autocomplete(parser)

    # If '--' in arguments, use all other arguments after it as run
    # arguments
    args = sys.argv[1:]
    if '--' in args:
        pos = args.index('--')
        extra_args = args[pos + 1:]
        args = args[:pos]
    else:
        extra_args = []

    options, targets = parser.parse_known_args(args)
    return options, targets, extra_args


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


def find_files_under(dir, pattern, excluded_dirs=None, relpath=False) -> list[str]:
    """Find files under dir matching pattern."""
    result = []
    for root, dirs, files in os.walk(dir):
        if excluded_dirs:
            dirs[:] = [d for d in dirs if d not in excluded_dirs]
        for file in files:
            if fnmatch.fnmatch(file, pattern):
                path = os.path.join(root, file)
                if relpath:
                    path = os.path.relpath(path, dir)
                result.append(path)
    return result

class UnrealCommandTool:
    """Unreal Command Line Tool."""
    def __init__(self, options, targets, extra_args):
        self.engine_root, self.project_file = self._find_project()
        self.engine_dir = os.path.join(self.engine_root, 'Engine')
        self.project_dir = os.path.dirname(self.project_file) if self.project_file else ''
        self.host_platform = self._host_platform()

        self.options = options
        self.extra_args = extra_args
        self._expand_options(options)

        self.ubt = self._find_ubt()
        assert os.path.exists(self.ubt), self.ubt

        self.__engine_targets = None
        self.__project_targets = None
        self.__all_targets = None

        self.command_targets = targets
        self.__targets = None

    def _find_project(self):
        """Find the project file and engine root."""
        project_file = os.environ.get('PROJECT_FILE')
        if not project_file:
            project_file = find_file_bottom_up('*.uproject')
        engine_root =  os.environ.get('ENGINE_ROOT')
        if not engine_root:
            key_file = find_file_bottom_up('GenerateProjectFiles.bat')
            if key_file:
                engine_root = os.path.dirname(key_file)
        if not engine_root:
            engine_root = self._find_engine_by_project(project_file)
        if not engine_root:
            console.error("Can't find engine root")
            sys.exit(1)
        return engine_root, project_file

    def _find_engine_by_project(self, project_file) -> str:
        if os.name == 'posix':
            return self._find_engine_root_posix(project_file)
        # On windows, this program is always call from the uct.bat,
        # finding engine by project was done there, we needn't query registry here.
        return ''

    def _find_engine_root_posix(self, project_file) -> str:
        engine_id = self._find_engine_association(project_file)
        if not engine_id:
            return ''
        config_file = os.path.expanduser('~/.config/Epic/UnrealEngine/Install.ini')
        config = configparser.ConfigParser()
        config.read(config_file)
        if 'Installations' not in config:
            console.error(f"Invalid config file '{config_file}'.")
            return ''
        installations = config['Installations']
        if engine_id not in installations:
            console.error(f"Engine '{engine_id}' is not registered in '{config_file}'.")
            return ''

        return config['Installations'][engine_id]

    def _find_engine_association(self, project_file) -> str:
        project = self._parse_project_file(project_file)
        if project:
            return project['EngineAssociation']
        return ''

    def _parse_project_file(self, project_file) -> Optional[dict[str, any]]:
        try:
            with open(project_file, encoding='utf8') as f:
                return json.load(f)
        except Exception as e:
            console.error(f"Error parsing '{project_file}': {e}")
            return None

    def _find_ubt(self):
        """Find full path of UBT based on host platform."""
        if self.host_platform == 'Win64':
            return os.path.normpath(os.path.join(self.engine_dir, 'Build/BatchFiles/Build.bat'))
        return os.path.normpath(
            os.path.join(self.engine_dir, f'Build/BatchFiles/{self.host_platform}/Build.sh'))

    def _host_platform(self):
        """Get host platform name as UE form."""
        system = platform.system()
        if system == 'Windows':
            return 'Win64'
        if system == 'Darwin':
            return 'Mac'
        return system

    def _expand_options(self, options):
        """Expand option values."""
        if hasattr(options, 'platform'):
            self.platform = PLATFORM_MAP.get(options.platform, self.host_platform)
        if hasattr(options, 'config'):
            self.config = CONFIG_MAP.get(options.config, 'Development')

    @property
    def targets(self):
        """All expanded targets from command line."""
        self._expand_targets(self.command_targets)
        return self.__targets

    def _expand_targets(self, targets):
        """Expand targets (maybe wildcard) from the command line to full list."""
        if self.__targets is not None:
            return
        if not targets:
            self.__targets = []
            return
        has_wildcard = False
        all_target_names = [t['Name'] for t in self.all_targets]
        expanded_targets = []
        for target in targets:
            if self._is_wildcard(target):
                has_wildcard = True
                expanded_targets += fnmatch.filter(all_target_names, target)
            else:
                if target not in all_target_names:
                    console.warn(f"target '{target}' doesn't exist")
                    continue
                expanded_targets.append(target)

        if has_wildcard:
            print(f'Targets: {" ".join(expanded_targets)}')

        self.__targets = expanded_targets

    def _is_wildcard(self, text):
        """Check whether a string is a wildcard."""
        for c in text:
            if c in '*?![]':
                return True
        return False

    @property
    def all_targets(self):
        """All target info in the engine and the game project."""
        self._collect_all_targets()
        return self.__all_targets

    @property
    def engine_targets(self):
        """Target info in the engine."""
        self._collect_all_targets()
        return self.__engine_targets

    @property
    def project_targets(self):
        """Target info in the game project."""
        self._collect_all_targets()
        return self.__project_targets

    def _collect_all_targets(self):
        """Load target info from the the engine and game project."""
        if self.__all_targets is not None:
            return
        self.__engine_targets = self._collect_targets(self.engine_dir)
        assert self.__engine_targets
        self.__project_targets = []
        if self.project_dir:
            self.__project_targets = self._collect_targets(self.project_dir)
        self.__all_targets = self.__engine_targets + self.__project_targets

    def _collect_targets(self, dir) -> list[str]:
        # Try 2 ways to collect target info.
        targets = self._query_targets(dir)
        if not targets:
            targets = self._scan_targets(dir)
        return targets

    def _query_targets(self, dir) -> list[str]:
        """Use UBT to query build targets."""
        cmd = [self.ubt, '-Mode=QueryTargets']
        if dir == self.project_dir:
            cmd.append(f'-Project={self.project_file}')
        p = subprocess.run(cmd, text=True, capture_output=True, check=False)
        if p.returncode != 0:
            console.warn(f'QueryTargets failed: {" ".join(cmd)}\n{p.stdout}')
            return []
        return self._load_target_info(dir)

    def _load_target_info(self, dir) -> list[str]:
        """Try load target info from TargetInfo.json under the dir."""
        path = os.path.join(dir, 'Intermediate', 'TargetInfo.json')
        try:
            with open(path, encoding='utf8') as f:
                return json.load(f)['Targets']
        except FileNotFoundError:
            # print(f"Can't open {path} for read")
            pass
        return []

    def _scan_targets(self, dir) -> list[dict[str, str]]:
        """
        Scan and load all .Target.cs files under the dir.
        This is slower than _query_targets but can be a failover.
        """
        targets = []
        pattern = '*.Target.cs'
        excluded_dirs = ['Binaries', 'DerivedDataCache', 'Intermediate']
        files = []
        files += find_files_under(os.path.join(dir, 'Source'), pattern, excluded_dirs=excluded_dirs)
        files += find_files_under(os.path.join(dir, 'Plugins'), pattern, excluded_dirs=excluded_dirs)
        for file in files:
            target = self._parse_target_cs(file)
            if target:
                targets.append(target)
        return targets

    def _parse_target_cs(self, file):
        """Parses a .Target.cs file to get target info."""
        name = ''
        with open(file, encoding='utf8') as f:
            for line in f:
                line = line.strip()
                m = re.match(r'public\s+class\s+(\w+)Target\b', line)
                if m:
                    name = m.group(1)
                    continue
                if name:
                    m = re.match(r'Type\s*=\s*TargetType.(\w+)\s*;', line)
                    if m:
                        target_type = m.group(1)
                        return {'Name': name, 'Path': file, 'Type': target_type}
        return None

    def execute(self) -> int:
        """
        Execute the command from command line.
        Return 0 if success
        """
        command = self.options.command.replace('-', '_')
        assert command in dir(self), f'{command} method is not defined'
        return getattr(self, command)()

    def list_targets(self) -> int:
        """Print out available build targets."""
        # print('List targets')
        if self.options.engine:
            self._print_targets(self.engine_targets)
        if self.options.project:
            if not self.project_file:
                console.error('You are not under a game project directory')
                return 1
            self._print_targets(self.project_targets)
        if not self.options.engine and not self.options.project:
            self._print_targets(self.all_targets)
        return 0

    def generate_project_files(self) -> int:
        """Run the GenerateProjectFiles.bat or sh."""
        suffix = 'bat' if self.host_platform == 'Win64' else 'sh'
        cmd = [os.path.join(self.engine_root, 'GenerateProjectFiles.' + suffix)]
        if self.project_file:
            cmd.append(self.project_file)
        cmd += self.extra_args
        return subprocess.call(cmd)

    def _print_targets(self, targets):
        if self.options.verbose:
            print(f'{"Type":10}{"Name":32}{"Path"}')
            print('-' * 120)
            for t in targets:
                print(f'{t["Type"]:10}{t["Name"]:32}{t["Path"]}')
        else:
            for t in targets:
                print(t['Name'])

    def _is_project_target(self, name):
        for target in self.project_targets:
            if target['Name'] == name:
                return True
        return False

    def build(self) -> int:
        """Build the specified targets."""
        if not self.targets:
            console.error('Missing targets, nothing to build')
            return 1
        returncode = 0
        project = f'-Project={self.project_file}' if self.project_file else ''
        for target in self.targets:
            print(f'Build {target}')
            cmd = [self.ubt, project, target, self.platform, self.config]
            if self.options.files:
                cmd += [f'--singlefile={f}' for f in self.options.files]
            cmd += self.extra_args
            ret = subprocess.call(cmd)
            if ret != 0: # Use first failed exitcode
                returncode = ret
        return returncode

    def clean(self) -> int:
        """Clean the specified targets."""
        if not self.targets:
            console.error('Missing targets, nothing to clean.')
            return 1
        returncode = 0
        project = f'-Project={self.project_file}' if self.project_file else ''
        for target in self.targets:
            print(f'Clean {target}')
            cmd = [self.ubt, project, target, self.platform, self.config, '-Clean']
            cmd += self.extra_args
            ret = subprocess.call(cmd)
            if ret != 0: # Use first failed exitcode
                returncode = ret
        return returncode

    def run(self) -> int:
        """Run the specified targets."""
        if not self.targets:
            console.error('Missing targets, nothing to run.')
            return 1
        returncode = 0
        for target in self.targets:
            executable = self._full_path_of_target(target)
            if not executable or not os.path.exists(executable):
                if executable:
                    console.error(f"{executable} doesn't exist, please build it first.")
                returncode = EXIT_COMMAND_NOT_FOUND
                continue
            cmd = [executable] + self.extra_args
            print(f'Run {" ".join(cmd)}')
            ret = subprocess.call(cmd)
            if ret != 0 and returncode == 0: # Use first failed exitcode
                returncode = ret
        return returncode

    def _full_path_of_target(self, target, key='Launch'):
        info = self._get_target_info(target)
        if not info:
            return ''
        executable = info[key]
        executable = executable.replace('$(EngineDir)', self.engine_dir)
        executable = executable.replace('$(ProjectDir)', self.project_dir)
        return executable

    def _get_target_info(self, target) -> Optional[dict]:
        """Find and parse the target info from the target file."""
        root = self.project_dir if self.project_file else self.engine_dir
        suffix = ''
        if self.config != 'Development':
            suffix = f'-{self.platform}-{self.config}'
        target_file = os.path.join(root, 'Binaries', self.platform, target + suffix + '.target')
        try:
            with open(target_file, encoding='utf8') as f:
                info = json.load(f)
                return info
        except FileNotFoundError:
            console.warn(f"target file {target_file} doesn't exist")

        return None

    def test(self) -> int:
        """Run the automation tests."""
        test_cmds = self._make_test_cmds()
        if not test_cmds:
            console.error('No test command to execute')
            return 0
        # Example command line:
        # G:\UnrealEngine-5.1\Engine\Binaries\Win64\UnrealEditor-Cmd.exe %CD%/MyGame.uproject \
        #   -log -NoSplash -Unattended -ExecCmds="Automation RunTests System; Quit"
        editor = self._full_path_of_target('UnrealEditor', 'LaunchCmd')
        if not os.path.exists(editor):
            console.error(f"{editor} doesn't exist, build it first")
            return EXIT_COMMAND_NOT_FOUND
        test_cmds = f'Automation {test_cmds}; Quit'
        print(f'Test command: {test_cmds}')
        cmd = [editor, self.project_file, '-log', '-NoSplash', '-Unattended', f'-ExecCmds="{test_cmds}"'] + \
               self.extra_args
        if self.host_platform == 'Win64':
            # Neither pass the list directly nor use subprocess.list2cmd works because they convert
            # -ExecCmds="Automation List; Quit" to "-ExecCmds=\"Automation List; Quit\"",
            # But simplay join the list with spaces works.
            cmd = ' '.join(cmd)
        print(f'Command line: {cmd}')
        return subprocess.call(cmd)

    def _make_test_cmds(self) -> str:
        cmds = []
        if self.options.list:
            cmds.append('List')
        if self.options.run_all:
            cmds.append('RunAll')
        if self.options.tests:
            # The RunTests command use '+' to split multiple tests
            cmds.append(f'RunTests {"+".join(self.options.tests)}')
        if self.options.test_cmds:
            cmds += self.options.test_cmds
        return '; '.join(cmds)


def check_targets(targets):
    """Check the correctness of targets."""
    ok = True
    for target in targets:
        if target.startswith('-'):
            console.error(f"Unknown option '{target}'.")
            ok = False
    if not ok:
        sys.exit(1)


def main():
    # print('Welcome to UCT: the Unreal CommandLine Tool')
    options, targets, extra_args = parse_command_line()
    check_targets(targets)
    uct = UnrealCommandTool(options, targets, extra_args)
    ret = uct.execute()
    if ret != 0:
        console.error(f'{options.command} failed with exit code {ret}.')
        sys.exit(ret)


if __name__ == '__main__':
    main()
