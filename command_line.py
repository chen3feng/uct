"""
Command line parser.
"""

import argparse
import sys

import constants

VERSION = '0.1'


def build_parser():
    """
    Build the argument parser.

    This command parser support multiple subcommands. Each subcommand has its own
    set of arguments.
    """
    parser = argparse.ArgumentParser(prog='UCT', description='Unreal command line tool')
    parser.add_argument('--version', action='version', version='%(prog)s ' + VERSION)

    subparsers = parser.add_subparsers(dest='command', help='Available commands', required=True)

    build_config = argparse.ArgumentParser(add_help=False)
    build_config.add_argument('-p', '--platform', dest='platform', type=str,
                              choices=constants.PLATFORM_MAP.keys(),
                              help='target platform')
    build_config.add_argument('-c', '--config', dest='config', type=str,
                              choices=constants.CONFIG_MAP.keys(),
                              help='build configuration')

    scope = argparse.ArgumentParser(add_help=False)
    scope.add_argument('--project', action='store_true', help='in project scope')
    scope.add_argument('--engine', action='store_true', help='in engine scope')

    build_parents = [build_config, scope]

    subparsers.add_parser('setup', help='Setup the engine')

    add_dual_subcommand(subparsers, 'generate', 'project', help='Generate project files')
    add_dual_subcommand(subparsers, 'switch', 'engine', help='Swith engine for current project')

    list_parsers = subparsers.add_parser('list', help='List objects in the workspace').add_subparsers(
        dest='subcommand', help='Available subcommands', required=True)
    targets = list_parsers.add_parser('target', help='list build targets', parents=[scope])
    targets.add_argument('--verbose', action='store_true', help='show detailed information')

    list_parsers.add_parser('engine', help='list all unreal engines in this computer')

    open_parsers = subparsers.add_parser('open', help='Open objects in the workspace').add_subparsers(
        dest='subcommand', help='Available subcommands', required=True)
    open_parsers.add_parser('file', help='open file', parents=[scope])
    open_parsers.add_parser('module', help='open module', parents=[scope])
    open_parsers.add_parser('plugin', help='open plugin', parents=[scope])

    subparsers.add_parser('runubt', help='Run UnrelBuildTool')
    subparsers.add_parser('runuat', help='Run AutomationTool')

    build = subparsers.add_parser('build', help='Build specified targets', parents=build_parents)
    build.add_argument('-m', '--modules', type=str, nargs='+',
                        help='modules to build')
    build.add_argument('-f', '--files', type=str, nargs='+',
                        help='source files to compile')
    subparsers.add_parser('rebuild', help='Rebuild specified targets', parents=[build], add_help=False)

    subparsers.add_parser('clean', help='Clean specified targets', parents=build_parents)

    run = subparsers.add_parser(
        'run',
        help='Build and run a single target',
        epilog='Any arguments after the empty "--" will be passed to the program',
        parents=build_parents)
    run.add_argument('--dry-run', action='store_true',
                     help="Don't actually run any commands; just print them.")

    test = subparsers.add_parser(
        'test',
        help='Build and run tests',
        epilog='Any arguments after the empty "--" will be passed to the program',
        parents=[build_config])
    test.add_argument('--list', dest='list', action='store_true', help='list all tests')
    test.add_argument('--run-all', dest='run_all', action='store_true', help='Run all test')
    test.add_argument('--run', dest='tests', type=str,  nargs='+', help='Run tests')
    test.add_argument('--cmds', dest='test_cmds', type=str, nargs='+', help='Extra test commands')

    pack = subparsers.add_parser('pack', help='Pack some objects').add_subparsers(
        dest='subcommand', help='Available subcommands', required=True)
    pack_target = pack.add_parser('target', help='Pack game targets',
                                  epilog='Any arguments after the empty "--" will be passed to UAT',
                                  parents=[build_config])
    pack_target.add_argument('-o', '--output', dest='output', type=str, required=True,
                             help='directory to archive the builds to')

    pack_plugin = pack.add_parser('plugin', help='Pack plugin',
                                  epilog='Any arguments after the empty "--" will be passed to UAT')
    pack_plugin.add_argument('-o', '--output', dest='output', type=str, required=True,
                             help='directory to archive the plugin to')
    pack_plugin.add_argument('-p', '--platforms', type=str, nargs='+', choices=constants.PLATFORM_MAP.keys(),
                             help='Target platforms')
    return parser


def add_dual_subcommand(subparsers, command, subcommand, **kwargs):
    """Add a dual sub command like `list engine`."""
    subparsers = subparsers.add_parser(command, help=command + ' command').add_subparsers(
        dest='subcommand', help='Available subcommands', required=True)
    return subparsers.add_parser(subcommand, **kwargs)


def parse():
    """Parse and validate commandparameters"""
    parser = build_parser()

    # https://pypi.org/project/argcomplete/
    # PYTHON_ARGCOMPLETE_OK
    try:
        import argcomplete # pylint: disable=import-error, import-outside-toplevel
        argcomplete.autocomplete(parser)
    except ImportError:
        pass

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
