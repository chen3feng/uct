"""
UCT -- Unreal Command Tool.
A powerful command line tool for unreal engine.
"""

import fnmatch
import json
import os
import re
import subprocess
import sys

from typing import Optional

import command_line
import constants
import console
import engine
import fs

# https://www.gnu.org/software/bash/manual/html_node/Exit-Status.html
EXIT_COMMAND_NOT_FOUND = 127


class UnrealCommandTool:
    """Unreal Command Line Tool."""
    def __init__(self, options, targets, extra_args):
        self.__installed_engines = None
        self.__built_engines = None
        self.__engine_targets = None
        self.__project_targets = None
        self.__all_targets = None
        self.__targets = None
        self.host_platform = self._host_platform()

        self.options = options
        self.raw_targets = targets
        self.extra_args = extra_args
        self._expand_options(options)

        if not self._need_engine(options):
            return

        self.project_file = self._find_project_file()
        self.engine_root = self._find_engine(self.project_file)
        self.engine_dir = os.path.join(self.engine_root, 'Engine')
        self.engine_version, self.engine_major_version = engine.parse_version(self.engine_root)
        self.ubt = self._find_ubt()
        assert os.path.exists(self.ubt), self.ubt

        self.project_dir = os.path.dirname(self.project_file)

    def _need_engine(self, options):
        return (options.command != 'list' or
                not hasattr(options, 'subcommand') or options.subcommand != 'engines')

    def _find_project_file(self):
        """Find the project file and engine root."""
        project_file = os.environ.get('PROJECT_FILE')
        if not project_file:
            project_file = fs.find_file_bottom_up('*.uproject')
        return project_file

    def _find_engine(self, project_file):
        engine_root =  os.environ.get('ENGINE_ROOT')
        if not engine_root:
            key_file = fs.find_file_bottom_up('GenerateProjectFiles.bat')
            if key_file:
                engine_root = os.path.dirname(key_file)
        if not engine_root:
            if not project_file:
                console.error("UCT should be ran under the directory of an engine or a game project.")
                sys.exit(1)
            engine_root = self._find_engine_by_project(project_file)
        if not engine_root:
            console.error("Can't find engine root.")
            sys.exit(1)
        return engine_root

    def _find_engine_by_project(self, project_file) -> str:
        engine_id = self._find_engine_association(project_file)
        if not engine_id:
            return ''
        if engine_id.startswith('{'): # Id of a built engine is a UUID encloded in '{}'.
            return self._find_built_engine(engine_id)
        return self._find_installed_engine(engine_id)

    def _find_engine_association(self, project_file) -> str:
        project = self._parse_project_file(project_file)
        if project:
            return project['EngineAssociation']
        return ''

    def _find_built_engine(self, engine_id: str) -> str:
        for eng in self.built_engines:
            if eng.id == engine_id:
                return eng.root
        console.error(f"Engine '{engine_id}' is not registered in '{engine.BUILT_REGISTRY}'.")
        return ''

    def _parse_project_file(self, project_file) -> Optional[dict]:
        try:
            with open(project_file, encoding='utf8') as f:
                return json.load(f)
        except Exception as e:
            console.error(f"Error parsing '{project_file}': {e}")
            return None

    def _find_installed_engine(self, engine_id) -> str:
        engine_id = 'UE_' + engine_id
        for eng in self.installed_engines:
            if eng.id == engine_id:
                return eng.root
        console.error(f'{engine_id} is not installed in your system, see {engine.INSTALLED_REGISTRY}.')
        return ''

    @property
    def installed_engines(self):
        """"All installed engines."""
        if self.__installed_engines is None:
            self.__installed_engines = engine.find_installed()
        return self.__installed_engines

    @property
    def built_engines(self):
        """"All source built engines."""
        if self.__built_engines is None:
            self.__built_engines = engine.find_builts()
        return self.__built_engines

    def _find_ubt(self):
        """Find full path of UBT based on host platform."""
        return self._find_build_script('Build')

    def _find_build_script(self, name, platform=None):
        """Find the full path of script under the Engine/Build/BatchFiles."""
        suffix = '.bat' if self.host_platform == 'Win64' else '.sh'
        if platform is None:
            platform = self.host_platform
            if platform == 'Win64':
                platform = ''
        return os.path.join(self.engine_dir, 'Build', 'BatchFiles', platform, name + suffix)

    def _host_platform(self):
        """Get host platform name as UE form."""
        import platform # pylint: disable=import-outside-toplevel
        system = platform.system()
        if system == 'Windows':
            return 'Win64'
        if system == 'Darwin':
            return 'Mac'
        return system

    def _expand_options(self, options):
        """Expand option values."""
        if hasattr(options, 'platform'):
            self.platform = constants.PLATFORM_MAP.get(options.platform, self.host_platform)
        if hasattr(options, 'config'):
            self.config = constants.CONFIG_MAP.get(options.config, 'Development')

    @property
    def targets(self):
        """All expanded targets from command line."""
        self._expand_targets(self.raw_targets)
        return self.__targets

    def _expand_targets(self, targets):
        """Expand targets (maybe wildcard) from the command line to full list."""
        if self.__targets is not None:
            return
        if not targets:
            self.__targets = []
            return

        candidate_targets = []
        if self.options.project:
            if not self.project_file:
                console.error('You are not under a game project directory.')
                sys.exit(1)
            candidate_targets += self.project_targets
        if self.options.engine:
            candidate_targets += self.engine_targets
        if not self.options.project and not self.options.engine:
            candidate_targets = self.all_targets

        all_target_names = [t['Name'] for t in candidate_targets]
        expanded_targets = []
        has_wildcard = False
        for target in targets:
            if fs.is_wildcard(target):
                has_wildcard = True
                expanded_targets += fnmatch.filter(all_target_names, target)
            else:
                if target not in all_target_names:
                    console.warn(f"target '{target}' doesn't exist.")
                    continue
                expanded_targets.append(target)

        if has_wildcard:
            print(f'Targets: {" ".join(expanded_targets)}')

        self.__targets = expanded_targets

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

    def _collect_targets(self, start_dir) -> list:
        # Try 2 ways to collect target info.
        targets = self._query_targets(start_dir)
        if not targets:
            targets = self._scan_targets(start_dir)
        return targets

    def _query_targets(self, start_dir) -> list:
        """Use UBT to query build targets."""
        cmd = [self.ubt, '-Mode=QueryTargets']
        if start_dir == self.project_dir:
            cmd.append(self._escape_argument('-Project', self.project_file))
            if os.name == 'nt':
                cmd = ' '.join(cmd)
        p = subprocess.run(cmd, text=True, capture_output=True, check=False)
        if p.returncode != 0:
            console.warn(f'QueryTargets failed: {" ".join(cmd)}\n{p.stdout}')
            return []
        return self._load_target_info(start_dir)

    def _load_target_info(self, start_dir) -> list:
        """Try load target info from TargetInfo.json under the dir."""
        path = os.path.join(start_dir, 'Intermediate', 'TargetInfo.json')
        try:
            with open(path, encoding='utf8') as f:
                return json.load(f)['Targets']
        except FileNotFoundError:
            # print(f"Can't open {path} for read")
            pass
        return []

    def _escape_argument(self, name, value):
        """Return -Project=/Full/Path/To/NameOf.uproject."""
        assert self.project_file
        if os.name == 'nt':
            # On windows, double quote is necessary if path contains space.
            return f'{name}="{value}"'
        # On Linux and Mac, add double quote may cause runtime error.
        return f'{name}={value}'

    def _scan_targets(self, start_dir) -> list:
        """
        Scan and load all .Target.cs files under the dir.
        This is slower than _query_targets but can be a failover.
        """
        targets = []
        pattern = '*.Target.cs'
        excluded_dirs = ['Binaries', 'DerivedDataCache', 'Intermediate']
        files = []
        files += fs.find_files_under(os.path.join(start_dir, 'Source'), [pattern], excluded_dirs)
        files += fs.find_files_under(os.path.join(start_dir, 'Plugins'), [pattern], excluded_dirs)
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
        command = self.options.command
        if hasattr(self.options, 'subcommand'):
            command += '_' + self.options.subcommand
        command = command.replace('-', '_')
        assert command in dir(self), f'{command} method is not defined'
        return getattr(self, command)()

    def _run_command(self, cmd, *args, **kwargs):
        """Run an external command."""
        if self.host_platform == 'Win64':
            # Windows can't handle command arguments correctly.
            # For example, in the handling of test command,
            # neither pass the list directly nor use subprocess.list2cmd works because they convert
            # -ExecCmds="Automation List; Quit" to "-ExecCmds=\"Automation List; Quit\"",
            # But simplay join the list with spaces works.
            return subprocess.call(' '.join(cmd), *args, **kwargs)
        return subprocess.call(cmd, *args, **kwargs)

    def setup(self) -> int:
        """Run the Setup script in the engine."""
        setup = 'Setup.' + ('bat' if self.host_platform == 'Win64' else 'sh')
        return subprocess.call(os.path.join(self.engine_root, setup))

    def generate_project(self) -> int:
        """Run the GenerateProjectFiles.bat or sh."""
        cmd = [self.ubt, '-ProjectFiles', '-SharedBuildEnvironment']
        if self.project_file:
            cmd.append(self.project_file)
        cmd += self.extra_args
        print(' '.join(cmd))
        return self._run_command(cmd)

    def list_targets(self) -> int:
        """Print out available build targets."""
        # print('List targets')
        if self.options.engine:
            self._print_targets(self.engine_targets)
        if self.options.project:
            if not self.project_file:
                console.error('You are not under a game project directory.')
                return 1
            self._print_targets(self.project_targets)
        if not self.options.engine and not self.options.project:
            self._print_targets(self.all_targets)
        return 0

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

    def list_engines(self) -> int:
        """List all engines in current system."""
        if self.installed_engines:
            print('Installed engines:')
            for eng in self.installed_engines:
                print(eng)
        if self.built_engines:
            if self.installed_engines:
                print()
            print('Registered source built engines:')
            for eng in self.built_engines:
                print(eng)
        return 0

    def open_module(self):
        """Reveal a module in file explorer."""
        if len(self.raw_targets) != 1:
            console.error('open module command accept exactly one module name')
            return 1
        return self._open_file(self.raw_targets[0] + '.Build.cs')

    def open_plugin(self):
        """Reveal a uplugin in file explorer."""
        if len(self.raw_targets) != 1:
            console.error('open plugin command accept exactly one plugin name')
            return 1
        return self._open_file(self.raw_targets[0] + '.uplugin')

    def _open_file(self, filename):
        fullpath = self._find_file(filename)
        if not fullpath:
            console.error(f"Can't find '{filename}'")
            return 1
        return fs.reveal_file(fullpath[0])

    def _find_file(self, filename):
        search_in_project = False
        search_in_engine = self.options.engine
        if self.options.project:
            if not self.project_dir:
                console.error('You are not under a game project directory.')
                return ''
            search_in_project = True
        if not self.options.project and not self.options.engine:
            search_in_project = bool(self.project_dir)
            search_in_engine = True
        if search_in_project:
            build_file = fs.find_files_under(self.project_dir, [filename], limit=1)
            if build_file:
                return build_file
        if search_in_engine:
            return fs.find_files_under(self.engine_dir, [filename], limit=1)
        return ''

    def build(self) -> int:
        """Build the specified targets."""
        if not self.targets:
            console.error('Missing targets, nothing to build.')
            return 1
        returncode = 0
        cmd_base = [self.ubt, self.platform, self.config]
        if self.project_file:
            cmd_base.append(self._escape_argument('-Project', self.project_file))
        failed_targets = []
        for target in self.targets:
            print(f'Build {target}')
            cmd = cmd_base + [target]
            if self.options.files:
                files = self._expand_files(self.options.files)
                if not files:
                    console.error(f"Can't find {self.options.files}")
                    return 1
                cmd += [self._escape_argument('-singlefile',f) for f in files]
            cmd += self.extra_args
            ret = self._run_command(cmd)
            if ret != 0:
                # Use first failed exitcode
                returncode = returncode or ret
                failed_targets.append(target)
        if failed_targets:
            console.error(f'Failed to build {" ".join(failed_targets)}.')
        return returncode

    def _expand_files(self, files) -> list:
        return fs.expand_source_files(files, self.engine_dir)

    def clean(self) -> int:
        """Clean the specified targets."""
        if not self.targets:
            console.error('Missing targets, nothing to clean.')
            return 1
        returncode = 0
        cmd_base = [self.ubt, self.platform, self.config]
        if self.project_file:
            cmd_base.append(self._escape_argument('-Project', self.project_file))
        failed_targets = []
        for target in self.targets:
            print(f'Clean {target}')
            cmd = cmd_base + ['-Clean', target]
            cmd += self.extra_args
            ret = self._run_command(cmd)
            if ret != 0:
                # Use first failed exitcode
                returncode = returncode or ret
                failed_targets.append(target)
        if failed_targets:
            console.error(f'Failed to clean {" ".join(failed_targets)}.')
        return returncode

    def run(self) -> int:
        """Run the specified targets."""
        if not self.targets:
            console.error('Missing targets, nothing to run.')
            return 1
        returncode = 0
        failed_targets = []
        for target in self.targets:
            executable = self._full_path_of_target(target)
            if not executable or not os.path.exists(executable):
                if executable:
                    console.error(f"{executable} doesn't exist, please build it first.")
                returncode = EXIT_COMMAND_NOT_FOUND
                continue
            cmd = [executable] + self.extra_args
            print(f'Run {" ".join(cmd)}')
            if self.options.dry_run:
                continue
            ret = self._run_command(cmd)
            if ret != 0:
                # Use first failed exitcode
                returncode = returncode or ret
                failed_targets.append(target)
        if failed_targets:
            console.error(f'Failed to run {" ".join(failed_targets)}.')
        return returncode

    def _full_path_of_target(self, target, key='Launch', platform=None, config=None):
        info = self._get_target_info(target, platform, config)
        if not info:
            return ''
        executable = info[key]
        executable = executable.replace('$(EngineDir)', self.engine_dir)
        executable = executable.replace('$(ProjectDir)', self.project_dir)
        return executable

    def _get_target_info(self, target, platform, config=None) -> Optional[dict]:
        """Find and parse the target info from the target file."""
        target_file = self._get_target_file(target, platform, config)
        if not target_file:
            return None

        try:
            with open(target_file, encoding='utf8') as f:
                info = json.load(f)
                return info
        except FileNotFoundError:
            console.warn(f'Error parsing {target_file}.')

        return None

    def _get_target_file(self, target, platform=None, config=None) -> str:
        """Get path of the {TargetName}.target file."""
        platform = platform or self.platform
        config = config or self.config
        suffix = f'-{self.platform}-{config}' if config != 'Development' else ''

        # When a engine target is built with the -Project option,
        # its target file is generated in the project directory.
        if self.project_dir:
            target_file = os.path.join(self.project_dir, 'Binaries', platform, target + suffix + '.target')
            if os.path.exists(target_file):
                return target_file

        # Also find it in the engine directory if it is an engine target.
        if self._is_engine_target(target):
            target_file = os.path.join(self.engine_dir, 'Binaries', platform, target + suffix + '.target')
            if os.path.exists(target_file):
                return target_file

        console.error(f"Can't find {target_file}, please build it first.")
        return ''

    def _is_engine_target(self, target):
        return any(t['Name'] == target for t in self.engine_targets)

    def test(self) -> int:
        """Run the automation tests."""
        test_cmds = self._make_test_cmds()
        if not test_cmds:
            console.error('No test command to execute.')
            return 0
        # Example command line:
        # G:\UnrealEngine-5.1\Engine\Binaries\Win64\UnrealEditor-Cmd.exe %CD%/MyGame.uproject \
        #   -log -NoSplash -Unattended -ExecCmds="Automation RunTests System; Quit"
        editor = self._full_path_of_editor(is_cmd=True)
        if not os.path.exists(editor):
            console.error(f"{editor} doesn't exist, build it first.")
            return EXIT_COMMAND_NOT_FOUND
        test_cmds = f'Automation {test_cmds}; Quit'
        print(f'Test command: {test_cmds}')
        cmd = [editor, self.project_file, '-log', '-NoSplash', '-Unattended', f'-ExecCmds="{test_cmds}"']
        if self._is_list_test_only():
            cmd += ['-LogCmds="global Error, LogAutomationCommandLine Display"', '-NullRHI']
        cmd += self.extra_args
        print(f'Command line: {cmd}')
        return self._run_command(cmd)

    def _full_path_of_editor(self, is_cmd=False, platform=None, config=None):
        if self.engine_major_version >= 5:
            return self._full_path_of_target('UnrealEditor', 'LaunchCmd' if is_cmd else 'Launch',
                                             self.host_platform, config)
        # There is no LaunchCmd field in UE4's target file.
        editor = self._full_path_of_target('UE4Editor', 'Launch', platform, config)
        if is_cmd:
            if editor.endswith('.exe'):
                return editor.replace('.exe', '-Cmd.exe')
            return editor + '-Cmd'
        return editor

    def _is_list_test_only(self):
        if not self.options.list:
            return False
        if  self.options.run_all or self.options.tests or self.options.test_cmds:
            return False
        return True

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

    def pack(self) -> int:
        """Pack targets"""
        if not self.project_file:
            console.error('not in project directory')
            return 0

        uat = self._find_build_script('RunUAT', platform='')
        # UnrealEditor does not support the Shipping configuration
        editor = self._full_path_of_editor(is_cmd=True, platform=self.host_platform, config='Development')
        if not editor:
            return 1

        for target in self.targets:
            print(f'Pack {target}')
            cmd = [
                uat, self._escape_argument('-ScriptsForProject', self.project_file),
                'Turnkey', '-command=VerifySdk', f'-target={target}', f'-platform={self.platform}',
                '-UpdateIfNeeded', self._escape_argument('-Project', self.project_file),
                'BuildCookRun', '-nop4', '-utf8output', '-nocompile', '-nocompileeditor', '-nocompileuat',
                '-skipbuildeditor', '-cook', self._escape_argument('-Project', self.project_file),
                '-stage', '-archive', '-package', '-build', '-pak', '-iostore', '-compressed', '-prereqs',
                f'-target={target}', self._escape_argument('-unrealexe', editor),
                f'-clientconfig={self.config}', f'-serverconfig={self.config}',
                self._escape_argument('-archivedirectory', os.path.abspath(self.options.output))
            ]
            # print(f'Run {' '.join(cmd)}')
            ret = self._run_command(cmd)
            if ret != 0:
                return ret
        return 0


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
    """Welcome to UCT: the Unreal CommandLine Tool."""
    options, targets, extra_args = command_line.parse()
    check_targets(targets)
    uct = UnrealCommandTool(options, targets, extra_args)
    ret = uct.execute()
    if ret != 0:
        console.error(f'{options.command} failed with exit code {ret}.')
        sys.exit(ret)


if __name__ == '__main__':
    main()
