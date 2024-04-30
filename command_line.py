"""
Command line parser.
"""

import argparse
import sys

import constants

VERSION = '0.1'

_SUB_COMMAND_HELP = 'Available subcommands'


def build_parser():
    """
    Build the argument parser.

    This command parser support multiple subcommands. Each subcommand has its own
    set of arguments.
    """
    parser = argparse.ArgumentParser(prog='UCT', description='Unreal command line tool.',
                                     epilog='Document and source code: https://github.com/chen3feng/uct')
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
    scope.add_argument('--project', action='store_true', help='in the project scope')
    scope.add_argument('--engine', action='store_true', help='in the engine scope')

    build_parents = [build_config, scope]

    subparsers.add_parser('setup', help='Setup the engine')

    _add_dual_subcommand(subparsers, 'generate', 'project', help='Generate project files')
    _add_dual_subcommand(subparsers, 'switch', 'engine', help='Swith engine for current project')

    list_parsers = subparsers.add_parser('list', help='List objects in the workspace').add_subparsers(
        dest='subcommand', help=_SUB_COMMAND_HELP, required=True)
    targets = list_parsers.add_parser('target', help='List build targets', parents=[scope])
    targets.add_argument('--verbose', action='store_true', help='show detailed information')

    list_parsers.add_parser('engine', help='list all unreal engines in this computer')

    open_parsers = subparsers.add_parser('open', help='Open objects in the workspace').add_subparsers(
        dest='subcommand', help=_SUB_COMMAND_HELP, required=True)
    open_parsers.add_parser('file', help='Open file', parents=[scope])
    open_parsers.add_parser('module', help='Open module', parents=[scope])
    open_parsers.add_parser('plugin', help='Open plugin', parents=[scope])

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
        epilog='Any arguments after the first bare "--" will be passed to the program.',
        parents=build_parents)
    run.add_argument('--dry-run', action='store_true',
                     help="Don't actually run any commands; just print them.")

    test = subparsers.add_parser(
        'test',
        help='Build and run tests',
        epilog='Any arguments after the first bare "--" will be passed to the program.',
        parents=[build_config])
    test.add_argument('--list', dest='list', action='store_true', help='list all tests')
    test.add_argument('--run-all', dest='run_all', action='store_true', help='Run all test')
    test.add_argument('--run', dest='tests', type=str,  nargs='+', help='Run tests')
    test.add_argument('--cmds', dest='test_cmds', type=str, nargs='+', help='Extra test commands')

    pack = subparsers.add_parser('pack', help='Pack specified artifacts').add_subparsers(
        dest='subcommand', help=_SUB_COMMAND_HELP, required=True)
    pack_target = pack.add_parser('target', help='Pack game targets',
                                  epilog='Any arguments after the first bare "--" will be passed to UAT.',
                                  parents=[build_config])
    pack_target.add_argument('-o', '--output', dest='output', type=str, required=True,
                             help='directory to archive the builds to')

    pack_plugin = pack.add_parser('plugin', help='Pack plugin',
                                  epilog='Any arguments after the first bare "--" will be passed to UAT.')
    pack_plugin.add_argument('-o', '--output', dest='output', type=str, required=True,
                             help='directory to archive the plugin to')
    pack_plugin.add_argument('-p', '--platforms', type=str, nargs='+', choices=constants.PLATFORM_MAP.keys(),
                             help='Target platforms')

    try:
        _fixup_parser(parser)
    except NameError:
        # In case of different name in different python version.
        pass

    return parser


def _fixup_parser(parser: argparse.ArgumentParser):
    # pylint: disable=protected-access
    """Add missing attributes."""
    if parser._subparsers is None:
        return
    for sp in parser._subparsers._group_actions:
        for name, subparser in sp._name_parser_map.items(): # type: ignore
            if subparser.description is None:
                ssp = _find_parser_in_subparsers(name, sp)
                if ssp:
                    subparser.description = ssp.help + '.'
            _fixup_parser(subparser)


def _find_parser_in_subparsers(name, subparsers):
    # pylint: disable=protected-access
    for ch in subparsers._choices_actions:
        if ch.dest == name:
            return ch
    return None


def _add_dual_subcommand(subparsers, command, subcommand, **kwargs):
    """Add a dual sub command like `list engine`."""
    subparsers = subparsers.add_parser(command, help=command.capitalize() + ' command').add_subparsers(
        dest='subcommand', help=_SUB_COMMAND_HELP, required=True)
    return subparsers.add_parser(subcommand, **kwargs)


def parse():
    """Parse and validate commandparameters"""
    parser = build_parser()

    # https://pypi.org/project/argcomplete/
    # PYTHON_ARGCOMPLETE_OK
    try:
        # pylint: disable=import-error, import-outside-toplevel
        import argcomplete # type: ignore
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
