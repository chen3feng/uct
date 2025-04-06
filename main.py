"""
UCT -- Unreal Command Tool.
A powerful command line tool for unreal engine.
"""

import filecmp
import glob
import json
import os
import re
import shutil
import subprocess
import sys

from typing import Optional, Tuple

import command_line
import constants
import console
import engine
import fs

from utils import subprocess_call, subprocess_run

sys.path.append(os.path.join(os.path.dirname(__file__), 'vendor'))
import cutie # pylint: disable = wrong-import-order, wrong-import-position


# https://www.gnu.org/software/bash/manual/html_node/Exit-Status.html
EXIT_COMMAND_NOT_FOUND = 127


class UnrealCommandTool:
    """Unreal Command Line Tool."""
    def __init__(self, options, targets, extra_args):
        self.__installed_engines = None
        self.__source_build_engines = None
        self.__engine_targets = None
        self.__project_targets = None
        self.__all_targets = None
        self.__targets = None
        self.host_platform = self._host_platform()

        self.options = options
        self.raw_targets = targets
        self.extra_args = extra_args
        self._expand_options(options)

        self.project_file = self._find_project_file()
        self.engine_root = self._find_engine(self.project_file)

        if not self._command_need_engine(options):
            return

        if not self.engine_root:
            if self.project_file:
                console.error("Can't find engine root fot this project.")
            else:
                console.error("UCT should be ran under the directory of an engine or a game project.")
            sys.exit(1)

        self.engine_dir = os.path.join(self.engine_root, 'Engine')
        self.engine_version, self.engine_major_version = engine.parse_version(self.engine_root)
        self.ubt = self._find_ubt()
        assert os.path.exists(self.ubt), self.ubt

        if self.host_platform == 'Win64' and self.platform.startswith('Linux'):
            self.setup_linux_cross_tool()

        self.project_dir = os.path.dirname(self.project_file)

    def _command_need_engine(self, options):
        if options.command == 'switch':
            # The engine associated with the current project maybe does not exist.
            return False
        if options.command == 'list' and options.subcommand == 'engine':
            return False
        return True

    def setup_linux_cross_tool(self):
        """
        Different engine has different cross tools version requirement. but when there are multipls engine source trees
        and cross tools in the system, UBT can't select correct cross tool according to its engine verson, it always use
        the global environment variable LINUX_MULTIARCH_ROOT.
        This function fixup this problems to support select correct cross tool automatically.
        """
        engine_version = (self.engine_version['MajorVersion'], self.engine_version['MinorVersion'], self.engine_version['PatchVersion'])
        tools = list_cross_tools()

        # NOTE: Keep the descending order!!!
        engine_toolchain_requirements = [
            # https://dev.epicgames.com/documentation/en-us/unreal-engine/linux-development-requirements-for-unreal-engine
            ('5.5', 'v23'),
            ('5.3', 'v22'),
            ('5.2', 'v21'),
            ('5.1', 'v20'),
            ('5.0.2', 'v20'),
            ('5.0', 'v19'),
            # https://dev.epicgames.com/documentation/en-us/unreal-engine/cross-compiling-for-linux
            ('4.27', 'v19'),
            ('4.26', 'v17'),
            ('4.25', 'v16'),
            ('4.23', 'v15'),
            ('4.22', 'v13'),
            ('4.19', 'v11'),
            ('4.18', 'v10'),
            ('4.16', 'v9'),
            ('4.14', 'v8'),
            ('4.11', 'v7'),
            ('4.9', 'v6'),
            ('4.8', 'v4'),
        ]

        for ev, tv in engine_toolchain_requirements:
            ev = tuple(map(int, ev.split('.')))
            if engine_version >= ev:
                if tv not in tools:
                    console.error(f'Cross toolchain {tv} is not installed in your system, see \n'
                                  'https://dev.epicgames.com/documentation/en-us/unreal-engine/linux-development-requirements-for-unreal-engine')
                    sys.exit(1)
                install_dir = tools[tv]
                os.environ['LINUX_MULTIARCH_ROOT'] = install_dir
                return

        console.error(f"Error finding correct linux cross tools for the engine '{self.engine_dir}'")
        sys.exit(1)

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
        if not engine_root and project_file:
            engine_root = self._find_engine_by_project(project_file)
        return engine_root

    def _find_engine_by_project(self, project_file) -> str:
        engine_id = self._find_engine_association(project_file)
        if not engine_id:
            return ''
        if engine_id.startswith('{'): # Id of a built engine is a UUID encloded in '{}'.
            return self._find_source_build_engine(engine_id)
        return self._find_installed_engine(engine_id)

    def _find_engine_association(self, project_file) -> str:
        project = self._parse_project_file(project_file)
        if project:
            return project['EngineAssociation']
        return ''

    def _find_source_build_engine(self, engine_id: str) -> str:
        for eng in self.source_build_engines:
            if eng.id == engine_id:
                return eng.root
        console.error(f"Engine '{engine_id}' is not registered in '{engine.SOURCE_BUILD_REGISTRY}'.")
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
    def source_build_engines(self):
        """"All source build engines."""
        if self.__source_build_engines is None:
            self.__source_build_engines = engine.find_source_builds()
        return self.__source_build_engines

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
        self.platform = constants.PLATFORM_MAP.get(getattr(options, 'platform', None), self.host_platform)
        self.config = constants.CONFIG_MAP.get(getattr(options, 'config', None), 'Development')

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
        search_in_engine, search_in_project = self._get_search_scope()
        if search_in_project:
            candidate_targets += self.project_targets
        if search_in_engine:
            candidate_targets += self.engine_targets

        all_target_names = [t['Name'] for t in candidate_targets]
        expanded_targets = []
        has_wildcard = False
        for target in targets:
            if fs.is_wildcard(target):
                has_wildcard = True
            matched_targets = fs.fnmatch_ifilter(all_target_names, target)
            if not matched_targets:
                console.warn(f"target '{target}' doesn't exist.")
                continue
            expanded_targets += matched_targets

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
            cmd.append(self._make_path_argument('-Project', self.project_file))
        p = subprocess_run(cmd, text=True, capture_output=True, check=False)
        if p.returncode != 0:
            cmdstr = ' '.join(cmd) if isinstance(cmd, list) else cmd
            console.warn(f'QueryTargets failed: {cmdstr}\n{p.stdout}')
            return []
        targets = self._load_target_info(start_dir)
        if start_dir == self.project_dir:
            # Engine targets are also included since UE 5.5, filter them out.
            targets = [t for t in targets if t['Path'].startswith(start_dir)]
        return targets

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

    def _make_path_argument(self, name, value):
        """Return something like -Project=/Full/Path/To/NameOf.uproject."""
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
        assert command in dir(self), f'method {command} is not defined'
        return getattr(self, command)()

    def setup(self) -> int:
        """Handle the `setup` command."""
        setup = 'Setup.' + ('bat' if self.host_platform == 'Win64' else 'sh')
        return subprocess_call(os.path.join(self.engine_root, setup))

    def generate_project(self) -> int:
        """Handle the `generate project` command."""
        cmd = [self.ubt, '-ProjectFiles']
        if self.project_file and not hasattr(self.options, 'engine'):
            cmd.append(self._make_path_argument('-Project', self.project_file))
            cmd.append('-Game')
        cmd += self.extra_args
        print(' '.join(cmd))
        return subprocess_call(cmd)

    def gpf(self) -> int:
        """Handle the `gpf` command, The short alias for the `generate project` command."""
        return self.generate_project()

    def switch_engine(self):
        """Handle the `switch engine` command."""
        if not self.project_file:
            console.error('You are not under the directory of a game project.')
            return 1
        print('Switch engine')
        options = []
        engines = []
        caption_indices = []
        selected_index = 0
        if self.installed_engines:
            caption_indices.append(len(options))
            options.append('Installed engines:')
            engines.append(None)
            for eng in self.installed_engines:
                if self._is_current_engine(eng):
                    selected_index = len(engines)
                options.append(f'{eng.version_string():8} {eng.root}')
                engines.append(eng)
        if self.source_build_engines:
            caption_indices.append(len(options))
            options.append('Source build engines:')
            engines.append(None)
            for eng in self.source_build_engines:
                if self._is_current_engine(eng):
                    selected_index = len(engines)
                options.append(f'{eng.version_string():8} {eng.root}')
                engines.append(eng)
        selected = cutie.select(options, caption_indices, confirm_on_select=False, selected_index=selected_index)
        if selected < 0 or not engines[selected]:
            return 0
        return self._modify_engine_association(self.project_file, engines[selected])

    def _is_current_engine(self, engine) -> bool:
        return os.path.normpath(self.engine_root) == os.path.normpath(engine.root)

    def _modify_engine_association(self, project_file, engine):
        """Modify the project file to use the specified engine."""
        engine_id = engine.id
        if engine_id.startswith('UE_'): # Python 2.7 in UE4 doesn't support removesuffix
            engine_id = engine_id[3:]
        project_file_new = project_file + '.new'
        # Modify the value of "EngineAssociation" field in the project file.
        # The format of a .uproject file is json. Using string replacement instead of python's
        # json module is to ensure that the file format is unchanged.
        with open(project_file, encoding='utf8') as infile:
            with open(project_file_new, 'w', encoding='utf8') as outfile:
                for line in infile:
                    if 'EngineAssociation' in line:
                        line = re.sub(r'(?<=\"EngineAssociation\": )\".*\"', f'"{engine_id}"', line)
                    outfile.write(line)
        if not filecmp.cmp(project_file_new, project_file):
            self.update_project_file(project_file, project_file_new)
            print(f'Engine is switched to {engine}.')
        else:
            print('Engine is not changed.')
            os.remove(project_file_new)
        return 0

    def update_project_file(self, project_file, project_file_new):
        """Update the project file."""
        project_file_old = project_file + '.old'
        if not self.is_file_managed_by_git(project_file):
            # Backup the project file.
            try:
                os.remove(project_file_old)
            except OSError:
                pass
            os.rename(project_file, project_file_old)
        else:
            os.remove(project_file)
        os.rename(project_file_new, project_file)

    def switch_clang(self) -> int:
        """Switch the Linux crosstool globally"""
        print('Switch clang')
        tools = list_cross_tools()
        current, is_system = read_windows_variable('LINUX_MULTIARCH_ROOT')

        selected_index = 0
        candidates = []
        options = []
        caption_indices = []
        caption_indices.append(len(options))
        options.append('Installed crosstools:')
        candidates.append(None)
        for ver, path in tools.items():
            if os.path.normpath(path) == os.path.normpath(current):
                selected_index = len(candidates)
            options.append(f'{ver:8} {path}')
            candidates.append(path)
        selected = cutie.select(options, caption_indices, confirm_on_select=False, selected_index=selected_index)
        if selected < 0 or not options[selected]:
            return 0
        ret = set_crosstool(candidates[selected])
        if ret != 0:
            return ret
        print(f'Linux cross tool was switched to {candidates[selected]}. Reopen the terminal to apply the change.')
        return 0

    def switch_xcode(self) -> int:
        """Switch system Xcode versison."""
        xcodes = list_installed_xcode()
        current = get_active_xcode()

        options = []
        caption_indices = []
        selected_index = 0
        caption_indices.append(len(options))
        candidates = []
        options.append('Installed Xcodes:')
        candidates.append(None)
        for ver, path in xcodes.items():
            if path == current:
                selected_index = len(candidates)
            options.append(f'{ver:8} {path}')
            candidates.append(path)
        selected = cutie.select(options, caption_indices, confirm_on_select=False, selected_index=selected_index)
        if selected < 0 or not options[selected]:
            return 0
        selected_app = candidates[selected]
        if selected_app == current:
            print('Xcode is not switched.')
            return 0
        ret = subprocess.call(['sudo', 'xcode-select', '--switch', f'{selected_app}/Contents/Developer'])
        if ret == 0:
            print(f'Xcode is switched to {selected_app}')
        return ret

    def is_file_managed_by_git(self, file):
        """Check if the file is managed by git."""
        return subprocess_run(['git', 'ls-files', '--error-unmatch', file], check=False, capture_output=True).returncode == 0

    def list_target(self) -> int:
        """Handle the `list target` command."""
        if self.raw_targets:
            targets = [t for t in self.all_targets if t['Name'] in self.targets]
            self._print_targets(targets)
            return 0
        search_in_engine, search_in_project = self._get_search_scope()
        if search_in_engine and search_in_project:
            self._print_targets(self.all_targets)
        elif search_in_engine:
            self._print_targets(self.engine_targets)
        elif search_in_project:
            self._print_targets(self.project_targets)
        else:
            # Specified `--project`` but not under a project directory.
            return 1

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

    def list_engine(self) -> int:
        """
        Handle the `list engine` command.
        List all engines in current system.
        """
        if self.installed_engines:
            print('Installed engines:')
            for eng in self.installed_engines:
                print(eng)
        if self.source_build_engines:
            if self.installed_engines:
                print()
            print('Registered source build engines:')
            for eng in self.source_build_engines:
                print(eng)
        return 0

    def open_file(self):
        """Handle the `open file` command."""
        if len(self.raw_targets) != 1:
            console.error('open file command accept exactly one file name')
            return 1
        return self._open_file(self.raw_targets[0])

    def open_module(self):
        """Handle the `open module` command."""
        if len(self.raw_targets) != 1:
            console.error('open module command accept exactly one module name')
            return 1
        ret = self._open_module_by_manifest(self.raw_targets[0])
        if ret is not None:
            return ret
        return self._open_file(self.raw_targets[0] + '.Build.cs')

    def _open_module_by_manifest(self, name) -> Optional[int]:
        search_in_engine, search_in_project = self._get_search_scope()
        if search_in_project:
            ret = self._open_module_by_manifest_under(self.project_dir, name)
            if ret is not None:
                return ret
        if search_in_engine:
            return self._open_module_by_manifest_under(self.engine_dir, name)
        return None

    def _open_module_by_manifest_under(self, start_dir, name) -> Optional[int]:
        for manifest in glob.glob(os.path.join(start_dir, 'Intermediate/Build/BuildRules', '*Manifest.json')):
            with open(manifest, encoding='utf8') as f:
                for build_file in json.load(f)['SourceFiles']:
                    if os.path.basename(build_file).lower() == (name + '.Build.cs').lower():
                        return fs.reveal_file(build_file)
        return None

    def open_plugin(self):
        """Handle the `open plugin` command."""
        if len(self.raw_targets) != 1:
            console.error('open plugin command accept exactly one plugin name')
            return 1
        return self._open_file(self.raw_targets[0] + '.uplugin')

    def _get_search_scope(self) -> Tuple[bool, bool]:
        if not hasattr(self.options, 'engine'):
            return True, True
        search_in_project = False
        search_in_engine = self.options.engine
        if self.options.project:
            if self.project_dir:
                search_in_project = True
            else:
                console.error('You are not under a game project directory.')
        if not self.options.project and not self.options.engine:
            search_in_project = bool(self.project_dir)
            search_in_engine = True
        return search_in_engine, search_in_project

    def _open_file(self, filename):
        fullpath = self._find_file(filename)
        if not fullpath:
            console.error(f"Can't find '{filename}'")
            return 1
        return fs.reveal_file(fullpath[0])

    def _find_file(self, filename):
        search_in_engine, search_in_project = self._get_search_scope()
        if search_in_project:
            build_file = fs.find_source_files_under(self.project_dir, [filename], limit=1)
            if build_file:
                return build_file
        if search_in_engine:
            return fs.find_source_files_under(self.engine_dir, [filename], limit=1)
        return ''

    def runuat(self):
        """Execute the RunUAT command."""
        uat = self._find_build_script('RunUAT', platform='')
        return subprocess_call([uat] + self.extra_args)

    def runubt(self):
        """Execute the RunUBT command."""
        return subprocess_call([self.ubt] + self.extra_args)

    def build(self, is_rebuild=False) -> int:
        """
        Handle the `build` command.
        Build the specified targets.
        """
        if not self.targets:
            console.error('Missing targets, nothing to build.')
            return 1
        returncode = 0
        cmd_base = [self._find_build_script('Build'), self.platform, self.config]
        if is_rebuild:
            cmd_base.append('-Rebuild')
        if self.project_file:
            cmd_base.append(self._make_path_argument('-Project', self.project_file))
        failed_targets = []
        for target in self.targets:
            action = 'Rebuild' if is_rebuild else 'Build'
            print(f'{action} {target}')
            cmd = cmd_base + [target]
            if self.options.files:
                files = self._expand_files(self.options.files)
                if not files:
                    console.error(f"Can't find {self.options.files}")
                    return 1
                cmd += [self._make_path_argument('-singlefile', f) for f in files]
            cmd += self.extra_args
            ret = subprocess_call(cmd)
            if ret != 0:
                # Use first failed exitcode
                returncode = returncode or ret
                failed_targets.append(target)
        if failed_targets:
            console.error(f'Failed to build {" ".join(failed_targets)}.')
        return returncode

    def _expand_files(self, files) -> list:
        return fs.expand_source_files(files, self.engine_dir)

    def rebuild(self) -> int:
        """Rebuild targets."""
        return self.build(True)

    def clean(self) -> int:
        """
        Handle the `clean` command.
        Clean the specified targets.
        """
        if not self.targets:
            console.error('Missing targets, nothing to clean.')
            return 1
        returncode = 0
        cmd_base = [self.ubt, self.platform, self.config]
        if self.project_file:
            cmd_base.append(self._make_path_argument('-Project', self.project_file))
        failed_targets = []
        for target in self.targets:
            print(f'Clean {target}')
            cmd = cmd_base + ['-Clean', target]
            cmd += self.extra_args
            ret = subprocess_call(cmd)
            if ret != 0:
                # Use first failed exitcode
                returncode = returncode or ret
                failed_targets.append(target)
        if failed_targets:
            console.error(f'Failed to clean {" ".join(failed_targets)}.')
        return returncode

    def run(self) -> int:
        """
        Handle the `run` command.
        Run the specified targets.
        """
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
            cmd = [executable]
            if self._is_project_target(target):
                info = self._get_target_info(target, None, None)
                assert info
                if info['TargetType'] != 'Program' and self.project_file:
                    cmd.append(self._make_path_argument('-Project', self.project_file))
            cmd += self.extra_args
            print(f'Run {" ".join(cmd)}')
            if self.options.dry_run:
                continue
            ret = subprocess_call(cmd)
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
        executable = os.path.normpath(executable)
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
        """
        Handle the `test` command.
        Run the different kinds of tests.
        """
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
        return subprocess_call(cmd)

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

    def pack_target(self) -> int:
        """
        Handle the `pack target` command.
        Pack targets.
        """
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
                uat, self._make_path_argument('-ScriptsForProject', self.project_file),
                # Turnkey
                'Turnkey', '-command=VerifySdk', f'-target={target}', f'-platform={self.platform}',
                '-UpdateIfNeeded', self._make_path_argument('-Project', self.project_file),
                # BuildCookRun
                'BuildCookRun', '-nop4', '-utf8output', '-nocompile', '-nocompileeditor', '-nocompileuat',
                '-skipbuildeditor', '-cook', self._make_path_argument('-Project', self.project_file),
                '-stage', '-archive', '-package', '-build', '-pak', '-iostore', '-compressed', '-prereqs',
                f'-target={target}', self._make_path_argument('-unrealexe', editor), f'-platform={self.platform}',
                f'-clientconfig={self.config}', f'-serverconfig={self.config}',
                self._make_path_argument('-archivedirectory', os.path.abspath(self.options.output))
            ]
            # print(f'Run {' '.join(cmd)}')
            ret = subprocess_call(cmd)
            if ret != 0:
                return ret
        return 0

    def pack_plugin(self) -> int:
        """
        Handle the `pack target` command.
        Pack targets.
        """
        plugin_file = self._find_plugin_file_to_pack()
        if not plugin_file:
            return 1
        pack_dir = os.path.abspath(self.options.output)
        cmd = [
            self._find_build_script('RunUAT', platform=''),
            'BuildPlugin', self._make_path_argument('-Plugin', plugin_file),
            self._make_path_argument('-Package', pack_dir),
            '-CreateSubFolder'
        ]
        if self.options.platforms:
            platforms = [constants.PLATFORM_MAP[p] for p in self.options.platforms]
            cmd.append('-TargetPlatforms=' + '+'.join(platforms))
        cmd += self.extra_args

        ret = subprocess_call(cmd)
        if ret != 0:
            return ret

        return self._cleanup_packed_plugin(pack_dir)

    def _find_plugin_file_to_pack(self) -> str:
        if not self.project_dir:
            console.error('This command must run under a game project.')
            return ''
        if not self.raw_targets:
            console.error('Missing plugin name, nothing to pack.')
            return ''
        if len(self.raw_targets) != 1:
            console.error('Too many plugin names, only accept one.')
            return ''
        plugin_name = self.raw_targets[0]
        plugins = fs.find_source_files_under(self.project_dir, [plugin_name + '.uplugin'], limit=1)
        if not plugins:
            console.error(f"Can't find plugin '{plugin_name}'")
            return ''
        return plugins[0]

    def _cleanup_packed_plugin(self, pack_dir):
        shutil.rmtree(os.path.join(pack_dir, 'Intermediate'), ignore_errors=True)
        shutil.rmtree(os.path.join(pack_dir, 'Binaries'), ignore_errors=True)
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


def list_cross_tools() -> dict[str, str]:
    """
    List all installed crosstools in the system.
    dict[version, installed_path]
    """
    import winreg     # pylint: disable=import-outside-toplevel,import-error
    import itertools  # pylint: disable=import-outside-toplevel,import-error
    toolchains = {}
    try:
        key_name = 'SOFTWARE\\WOW6432Node\\'
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_name) as hkey:
            for i in itertools.count():
                try:
                    key_name = winreg.EnumKey(hkey, i)
                    if not key_name.startswith('Unreal Linux Toolchain'):
                        continue
                    with winreg.OpenKey(hkey, key_name) as toolchain_key:
                        install_dir, _ = winreg.QueryValueEx(toolchain_key, 'Install_Dir')
                        toolchains[parse_toolchain_version(key_name)] = install_dir
                except OSError:
                    # ERROR_NO_MORE_ITEMS
                    break
    except OSError as e:
        print(f"winreg.OpenKey: {e}: '{key_name}'.")
    return toolchains


def parse_toolchain_version(key_name):
    """
    Extract cross tool version from registry key name. Example:
    Get 'v20' from 'Unreal Linux Toolchain v20_clang-13.0.1-centos7'.
    """
    m = re.match(r'Unreal Linux Toolchain (v\d+).*', key_name)
    return m.group(1) if m else ''


def read_windows_variable(name: str) -> Tuple[Optional[str], bool]:
    value = read_env_var_from_registry(name, system=False)
    if value:
        return value, False
    value = read_env_var_from_registry(name, system=True)
    if value:
        return value, True
    return None, False


def read_env_var_from_registry(name :str, system=True) -> Optional[str]:
    """Read global environment variable"""
    import winreg # pylint: disable=import-outside-toplevel,import-error
    try:
        if system:
            root = winreg.HKEY_LOCAL_MACHINE
            path = r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment"
        else:
            root = winreg.HKEY_CURRENT_USER
            path = r"Environment"

        with winreg.OpenKey(root, path) as key:
            value, _ = winreg.QueryValueEx(key, name)
            return value
    except FileNotFoundError:
        return None


def set_crosstool(path: str) -> int:
    ret = subprocess_call(f'setx LINUX_MULTIARCH_ROOT {path}', stdout=subprocess.DEVNULL)
    if ret != 0:
        return ret
    broadcast_env_change()
    return 0

def broadcast_env_change():
    # It doesn't work to most programs.
    import ctypes
    HWND_BROADCAST = 0xFFFF
    WM_SETTINGCHANGE = 0x1A
    SMTO_ABORTIFHUNG = 0x0002

    result = ctypes.windll.user32.SendMessageTimeoutW(
        HWND_BROADCAST,
        WM_SETTINGCHANGE,
        0,
        "Environment",
        SMTO_ABORTIFHUNG,
        5000,
        None
    )



def list_installed_xcode() -> dict[str, str]:
    """List all installed Xcode."""
    result = {}
    cmd = ['mdfind', "kMDItemCFBundleIdentifier == 'com.apple.dt.Xcode'"]
    out = subprocess.check_output(cmd, text=True)
    for app in out.splitlines():
        if '/Applications/' not in app: # Not installed
            continue
        result[get_xcode_version(app)] = app
    return result


def get_xcode_version(app) -> str:
    version_file = os.path.join(app, 'Contents/version.plist')
    cmd = ['/usr/libexec/PlistBuddy', '-c', 'Print CFBundleShortVersionString', version_file]
    version = subprocess.check_output(cmd, text=True)
    return version.strip()


def get_active_xcode() -> str:
    path = subprocess.check_output(['xcode-select', '--print-path'], text=True).strip()
    return path.removesuffix('/Contents/Developer')


def main():
    """Welcome to UCT: the Unreal CommandLine Tool."""
    options, targets, extra_args = command_line.parse()
    check_targets(targets)
    uct = UnrealCommandTool(options, targets, extra_args)
    ret = uct.execute()
    if ret != 0:
        console.error(f'{options.command} failed.')
        sys.exit(ret)


if __name__ == '__main__':
    main()
