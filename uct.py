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

ENGINE_ROOT = ''
PROJECT_FILE = None

def parse_command_line():
    parser = argparse.ArgumentParser(prog='UCT', description='Unreal command line tools')
    parser.add_argument('--version', action='version', version='%(prog)s ' + VERSION)
    subparsers = parser.add_subparsers(dest='command', help='Available subcommands')
    subparsers.required = True
    build = subparsers.add_parser('build', help='Build specified targets')

    build.add_argument('integers', metavar='N', type=int, nargs='+',
                        help='an integer for the accumulator')
    build.add_argument('--sum', dest='accumulate', action='store_const',
                        const=sum, default=max,
                        help='sum the integers (default: find the max)')

    clean = subparsers.add_parser('clean')
    clean.add_argument('integers', metavar='N', type=int, nargs='+',
                        help='an integer for the accumulator')
    clean.add_argument('--sum', dest='accumulate', action='store_const',
                        const=sum, default=max,
                        help='sum the integers (default: find the max)')

    if argcomplete:
        argcomplete.autocomplete(parser)

    options, others = parser.parse_known_args()
    # If '--' in arguments, use all other arguments after it as run
    # arguments
    if '--' in others:
        pos = others.index('--')
        targets = others[:pos]
        options.args = others[pos + 1:]
    else:
        targets = others
        options.args = []

    for t in targets:
        if t.startswith('-'):
            print('Unrecognized option %s, use uct [action] --help to get all the options' % t)

    return options, targets


def main():
    global ENGINE_ROOT, PROJECT_FILE
    ENGINE_ROOT = os.environ['ENGINE_ROOT']
    PROJECT_FILE = os.environ.get('PROJECT_FILE')

    print('Welcome to UCT: the Unreal CommandLine Tools')
    options, targets = parse_command_line()
    print(options, targets)

if __name__ == '__main__':
    main()
