import argparse
import os
import sys

# https://pypi.org/project/argcomplete/
try:
    # pyright: reportMissingImports=false
    import argcomplete
except ImportError:
    argcomplete = None

VERSION = '1.0'

def build_arg_parser():
    parser = argparse.ArgumentParser(prog='UCT', description='Unreal command line tools')
    parser.add_argument('--version', action='version', version='%(prog)s ' + VERSION)

    subparsers = parser.add_subparsers(dest='command', help='Available subcommands')
    subparsers.required = True

    build = subparsers.add_parser('build', help='Build specified targets')

    build.add_argument('-p', '--platform', dest='platform', type=str,
                        choices=['win', 'linux', 'mac'],
                        help='target platform')
    build.add_argument('-c', '--config', dest='config', type=str,
                        choices=['debug', 'develop', 'ship'],
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
        epilog='Any arguments after the empty "--" will be passed to the program')

    test = subparsers.add_parser(
        'test',
        help='Build and run tests',
        epilog='Any arguments after the empty "--" will be passed to the program')


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


class UnrealCommandTools:
    def __init__(self, options, extra_args):
        self.engine_dir, self.project_file = self._find_project()
        self.options = options
        self.extra_args = extra_args

    def _find_project(self):
        return os.environ.get('ENGINE_ROOT'), os.environ.get('PROJECT_FILE')

    def execute(self):
        command = self.options.command
        assert command in dir(self), f'{command} method is not defined'
        getattr(self, command)()

    def build(self):
        print('Build')

def main():
    print('Welcome to UCT: the Unreal CommandLine Tools')
    options, extra_args = parse_command_line()
    uct = UnrealCommandTools(options, extra_args)
    uct.execute()


if __name__ == '__main__':
    main()
