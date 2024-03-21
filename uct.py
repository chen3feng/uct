import argparse
import fnmatch
import json
import os
import pprint
import subprocess
import sys

# https://pypi.org/project/argcomplete/
try:
    # pyright: reportMissingImports=false
    import argcomplete
except ImportError:
    argcomplete = None

VERSION = '1.0'


PLATFORM_MAP = {
    'win': 'Win64',
    'win64': 'Win64',
    'linux': 'Linux',
    'mac': 'Mac'
}

CONFIG_MAP = {
    'debug': 'Debug',
    'dbg': 'Debug',
    'dev': 'Development',
    'ship': 'Shipping',
    'test': 'Test',
}


def build_arg_parser():
    parser = argparse.ArgumentParser(prog='UCT', description='Unreal command line tool')
    parser.add_argument('--version', action='version', version='%(prog)s ' + VERSION)

    subparsers = parser.add_subparsers(dest='command', help='Available subcommands')
    subparsers.required = True

    list_targets = subparsers.add_parser('list-targets', help='List targets')
    list_targets.add_argument('--project', action='store_true')
    list_targets.add_argument('--engine', action='store_true')
    list_targets.add_argument('--verbose', action='store_true')

    build = subparsers.add_parser('build', help='Build specified targets')

    build.add_argument('-p', '--platform', dest='platform', type=str,
                        choices=PLATFORM_MAP.keys(),
                        help='target platform')
    build.add_argument('-c', '--config', dest='config', type=str,
                        choices=CONFIG_MAP.keys(),
                        help='build configuration')
    build.add_argument('-t', '--targets', type=str, nargs='+',
                        help='targets to build')
    build.add_argument('-m', '--modules', type=str, nargs='+',
                        help='modules to build')
    build.add_argument('-f', '--files', type=str, nargs='+',
                        help='source files to compile')
    clean = subparsers.add_parser('clean', help='Clean specified targets', parents=[build], add_help=False)

    run = subparsers.add_parser(
        'run',
        help='Build and run a single target',
        epilog='Any arguments after the empty "--" will be passed to the program',
        parents=[build], add_help=False)

    test = subparsers.add_parser(
        'test',
        help='Build and run tests',
        epilog='Any arguments after the empty "--" will be passed to the program',
        parents=[build], add_help=False)
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

    return parser.parse_args(args), extra_args


class UnrealCommandTool:
    """Unreal Command Line Tool."""
    def __init__(self, options, extra_args):
        self.engine_root, self.project_file = self._find_project()
        self.engine_dir = os.path.join(self.engine_root, 'Engine')
        self.project_dir = os.path.dirname(self.project_file) if self.project_file else ''
        self.ubt = self._find_ubt()
        self._load_project_targets()

        self.options = options
        self.extra_args = extra_args

    def _find_project(self):
        return os.environ.get('ENGINE_ROOT'), os.environ.get('PROJECT_FILE')

    def _find_ubt(self):
        return os.path.normpath(os.path.join(self.engine_dir, 'Build/BatchFiles/Build.bat'))

    def _parse_build_options(self, options):
        self.platform = PLATFORM_MAP.get(options.platform, 'Win64')
        self.config = CONFIG_MAP.get(options.config, 'Development')
        self.targets = self._expand_targets(options.targets)

    def _expand_targets(self, targets):
        if targets is None:
            return []
        has_wildcard = False
        all_target_names = [t['Name'] for t in self.all_targets]
        print(all_target_names)
        expanded_targets = []
        for target in targets:
            if self._is_wildcard(target):
                has_wildcard = True
                expanded_targets += fnmatch.filter(all_target_names, target)
            else:
                if target not in all_target_names:
                    print(f"Target {target}' doesn't exist", file=sys.stderr)
                else:
                    expanded_targets.append(target)
        if has_wildcard:
            print(f'Targets: {" ".join(expanded_targets)}')

        return expanded_targets

    def _is_wildcard(self, text):
        for c in text:
            if c in '*?![]':
                return True
        return False

    def _load_project_targets(self):
        self.engine_targets = self._load_target_info(self.engine_dir)
        self.all_targets = self.engine_targets.copy()
        if self.project_dir:
            self.project_targets = self._load_target_info(self.project_dir)
            self.all_targets += self.project_targets

    def _load_target_info(self, dir):
        path = os.path.join(dir, 'Intermediate', 'TargetInfo.json')
        with open(path, encoding='utf8') as f:
            return json.load(f)['Targets']
        return {}

    def execute(self) -> int:
        command = self.options.command.replace('-', '_')
        assert command in dir(self), f'{command} method is not defined'
        return getattr(self, command)()

    def list_targets(self) -> int:
        # print('List targets')
        if self.options.engine:
            self.print_targets(self.engine_targets)
        if self.options.project:
            self.print_targets(self.project_targets)
        if not self.options.engine and not self.options.project:
            self.print_targets(self.all_targets)
        return 0

    def print_targets(self, targets):
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
        # print('Build')
        self._parse_build_options(self.options)
        returncode = 0
        for target in self.targets:
            print(f'Build {target}')
            cmd = [
                self.ubt, f'-Project={self.project_file}', target, self.platform, self.config
            ] + self.extra_args
            ret = subprocess.call(cmd)
            if ret != 0: # Use first failed exitcode
                returncode = ret
        return returncode

    def clean(self) -> int:
        print('Clean')
        return 0

    def run(self) -> int:
        self._parse_build_options(self.options)
        returncode = 0
        for target in self.targets:
            root = self.project_dir if self._is_project_target(target) else self.engine_dir
            suffix = '.exe' if self.platform == 'Win64' else ''
            executable = os.path.join(root, 'Binaries', self.platform, target + suffix)
            cmd = [executable] + self.extra_args
            print(f'Run {" ".join(cmd)}')
            ret = subprocess.call(cmd)
            if ret != 0: # Use first failed exitcode
                returncode = ret
        return returncode

    def test(self) -> int:
        self._parse_build_options(self.options)
        test_cmds = self._make_test_cmds()
        if not test_cmds:
            print('No test command to execute')
            return 0
        # Example command line:
        # G:\UnrealEngine-5.1\Engine\Binaries\Win64\UnrealEditor-Cmd.exe %CD%/MyGame.uproject -log -NoSplash -Unattended -ExecCmds="Automation RunTests System; Quit"
        editor = os.path.join(self.engine_dir, 'Binaries', self.platform, 'UnrealEditor-Cmd.exe')
        test_cmds = f'Automation {test_cmds}; Quit'
        print(f'Test command: {test_cmds}')
        cmd = [editor, self.project_file, '-log', '-NoSplash', '-Unattended', f'-ExecCmds="{test_cmds}"'] + \
               self.extra_args
        # Neither pass list directly nor use subprocess.list2cmd works because tney convert
        # -ExecCmds="Automation RunTests System.Core; Quit" to "-ExecCmds=\"Automation RunTests System.Core; Quit\""
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


def main():
    # print('Welcome to UCT: the Unreal CommandLine Tool')
    options, extra_args = parse_command_line()
    # print(options)
    uct = UnrealCommandTool(options, extra_args)
    sys.exit(uct.execute())


if __name__ == '__main__':
    main()
