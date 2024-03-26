# Command Line Tool for Unreal Engine

English | [简体中文](README-zh.md)

## What is UCT?

UCT (Unreal Commandline Tool) is a powerful command line tool to buid, test and run unreal engine based project easier.

Let's see a demo.

[![asciicast](https://asciinema.org/a/6KbwPkTAF2iqzYuzbYuYvqb6O.svg)](https://asciinema.org/a/6KbwPkTAF2iqzYuzbYuYvqb6O)

## Background

In many cases, I prefer command line tools because they are fast and easy automation. I often write code for UE in VS Code,
because it is much fast and lightweight than Visual Studio, has better git integration.
so I often need to call [UBT](https://docs.unrealengine.com/4.27/en-US/ProductionPipelines/BuildTools/UnrealBuildTool/) and editor manually,
but the their command line interface are very verbose.

For example, to build a program:

```console
G:\MyGame> G:\UnrealEngine-5.1\Engine\Build\BatchFiles\Build.bat Benchmark Win64 Development -Project="G:\MyGame\MyGame.uproject"
```

To run tests from command line:

```console
G:\MyGame>G:\UnrealEngine-5.1\Engine\Binaries\Win64\UnrealEditor-Cmd.exe %CD%/MyGame.uproject -ExecCmds="Automation RunAll"
```

These user interface has the following problems:

- You must use the UBT in the correct engine directory to build the game project.
  There are several versions of the engine on my workstation, and they are all in use,
  so I can not add the UBT path to the PATH environment variable. I have to use the full path.
- The path and suffix of UBT and other scripts are different between Windows and Mac/Linux.
- The path of the `-Project` argument must be a absolute path, it's boring, we can use `%CD%` to simplify it
  but it still need the project file name.
- Some options such as `Development` are so long.
- The file name of the editor have different suffix for different configurations, for example `UnrealEditor-Win64-Debug.exe`.

So, I developed this handy tool, to simplify my life, and, maybe yours.

With this tool, you needn't:

- Type the the full path of UBT.
  UCT can find it automatically if your current directory is under the game project or the engine directory.
- Pass the `-Project=/Full/Path/To/YourGame.uproject`.
  UCT can find it automatically if your current directory is under the game project.
- Type `Win64`.
  UCT assume the target platform is also the host platform by default, of cause you can also change it.
- Type `Development`.
  UCT use `Development` by default. Even if you want to specify it, using `-c dev` is also easier.

## Supported Systems

UCT supports running in Win64, Linux and Mac, and tested on UE 5.1, 5.2, 5.3 and 4.27.

## Install

Just use git to clone the code, and execute the `install` command:

```console
git clone https://github.com/chen3feng/uct
cd uct
install
```

The path of UCT is registered into your `PATH` environment, you can call it from any where in you system.

On Linux or Mac, the install command is `./install`.

## Basic Concepts

See UE documents for the following concepts:

- [Target](https://docs.unrealengine.com/4.27/en-US/ProductionPipelines/BuildTools/UnrealBuildTool/TargetFiles/) Each `.Target.cs` file describes a target.
- [Target Platform](https://unrealcommunity.wiki/6100e8109c9d1a89e0c31618) UE Support `Win64`, `Linux`, `Mac` and some other such as `Hololens`.
- [Configuration](https://docs.unrealengine.com/4.27/en-US/ProductionPipelines/DevelopmentSetup/BuildConfigurations/), Such as `Debug`, `Development`, `Shipping` and `Test`.
- [Module](https://docs.unrealengine.com/4.27/en-US/ProductionPipelines/BuildTools/UnrealBuildTool/ModuleFiles/) Each `.Build.cs` file describes a module.

## Command Line Interface

The basic interface is:

`uct` \<command\> options...

For example:

```console
uct build -c dbg -p linux Benchmark
```

`build` is the command, `-c dbg` and `-p linux` are options, `Benchmark` is a target.

Just like the git command. easy?

UCT support the following commands:

### List targets

List all targets:

```console
$ uct list-targets
BaseTextureBuildWorker
BenchmarkTool
BlankProgram
BuildPatchTool
...
```

List all engine targets:

```console
$ uct list-targets --engine
BaseTextureBuildWorker
BenchmarkTool
BlankProgram
BuildPatchTool
...
```

List all project targets:

```console
$ uct list-targets --project
MyGameTest
MyGameClient
MyGameEditor
MyGameServer
MyGameBenchmark
```

Make verbose output with the `--verbose` option:

```console
$ uct list-targets --verbose
Type      Name                            Path
------------------------------------------------------------------------------------------------------------------------
Program   BaseTextureBuildWorker          G:\UnrealEngine-5.1\Engine\Source\Programs\BaseTextureBuildWorker\BaseTextureBuildWorker.Target.cs
Program   BenchmarkTool                   G:\UnrealEngine-5.1\Engine\Source\Programs\BenchmarkTool\BenchmarkTool.Target.cs
Program   BlankProgram                    G:\UnrealEngine-5.1\Engine\Source\Programs\BlankProgram\BlankProgram.Target.cs
```

### Generate Project Files

Generate project files for the engine or game project.

```console
$ uct generate-project-files
...
```

Generate project files for the project or engine according to the current directory.

### Build

Build one target:

```console
$ uct build UnrealEditor
...
```

Build multiple targets:

```console
$ uct build Benchmark UnrealEditor
...
```

It supports wildcard target names:

```console
uct build MyProject*
uct build *Editor
uct build MyProject* *Editor
```

On Linux and Mac, since wildcards are expanded by the shell, add quotes if necessary to avoid expansion into matching project file names:

```console
uct build 'MyProject*'
uct build *Editor
uct build 'MyProject*' *Editor
```

It supports specifying [build configuration](https://dev.epicgames.com/documentation/en-us/unreal-engine/build-configurations-reference-for-unreal-engine?application_version=5.3)
and [target platform](https://unrealcommunity.wiki/6100e8109c9d1a89e0c31618):

```console
uct build -c debug -p linux
```

Option values for target platforms:

- `Win64`: `win64`
- `Linux`: `linux`
- `Mac`: `mac`

Option values for build configurations:

- `Debug`: `dbg` or `debug`
- `DebugGame`： `dbgm` or `debuggame`
- `Development`: `dev` or `develop`
- `Shipping`: `ship`
- `Test`: `test`

To simplify typing, in UCT, all these values are lowercase.

UCT will generate appropriate UBT commands based on the command line parameters for the actual build.
To pass extra [arguments](https://ikrima.dev/ue4guide/build-guide/utilities/devops-build-automation/) to UBT, put them after a standalone `--` like this:

```console
uct build MyGame -- -StaticAnalyzer=VisualCpp
```

### Clean

Clean one or more targets, example:

```console
$ uct clean Benchmark UnrealEditor
...
```

See the above `build` command for reference.

### Run

Run one or more programs:

```console
$ uct run Benchmark
Run G:\MyGame\Binaries\Win64\Benchmark.exe
LogBenchmark: Display: Running 'BM_Serialize<FFieldTest>'...
LogBenchmark: Display: Running 'BM_Serialize<FBenchmarkTest>'...
LogBenchmark: Display: Running 'BM_Deserialize<FFieldTest>'...
LogBenchmark: Display: Serialized size=109
...
```

All arguments after the first `--` is passed to the program:

```console
uct run Benchmark -- --help --help
```

The program got `--help -- --help` aruguments.

### Test

UCT use [`-ExecCmds Automation ...`](https://docs.unrealengine.com/4.27/en-US/TestingAndOptimization/Automation/TechnicalGuide/)
to execute automation tests.

Options:

- `--list`: list all tests
- `--run-all`: Run all test
- `--run`: Run specified tests, separted by space
- `--cmds`: Any extra test commands you want to run

Examples:

```console
# List all tests
uct test --list

# Run all tests
uct test --run-all

# Run all tests starts with 'System.Core'
uct test --run System.Core
```

The `--cmds` option can be used to pass more [test commands](https://forums.unrealengine.com/t/run-automated-testing-from-command-line/294995) to the system.

Example:

```console
uct test --cmds List RunAll "RunTests System" Quit
```

The -ExecCmd command is `Automation List; RunAll; "RunTests System"; Quit`.

According to the source code of UE, you can use the following test commands:

```text
Automation List
Automation RunTests <test string>
Automation RunAll
Automation RunFilter <filter name>
Automation SetFilter <filter name>
Automation Quit
```

### help

To view help, use the `--help` parameter. To view help for a command, add `--test` after the command.

```console
# View help
uct --help

# View help for the build command
uct build --help
```

### Command Line Completion

UCT support command auto completion in bash and zsh by using the `argcomplete` library,
see its [document](https://pypi.org/project/argcomplete/) to enable it.

## How it works

Understanding how UCT works is helpful, and code contributions are welcome.

### Startup

UCT must be run under the project or engine directory. When UCT is called, it will first search for the `.uproject` file from the current directory upwards. If it is found, it is considered to be in the project directory.
Parse the uproject file to get the engine ID associated with the project. Depending on the system, use different methods to get the directory where the engine is located.

- On Windows, read the registry key `HKEY_CURRENT_USER\Software\Epic Games\Unreal Engine\Builds`
- On Mac and Linux, read configuration files `~/.config/Epic/UnrealEngine/Install.ini`.

If the project file cannot be found, use a similar method to find the feature file of the UE engine (GenerateProjectFiles.bat) and obtain the root directory of the engine.

Under Linux and Mac, the above lookup process is performed in python.

On Windows, the above search process is batch processed, and then passed to UE's built-in python interpreter (`Engine\Binaries\ThirdParty\Python3\Win64\python.exe`) through environment variables. This is because Windows systems lack a unified Python installation, and the Python interpreter is already built into the engine.

Once the project and engine directories were found, Other paths such as UBT, are no longer a problem.

### `list-targets`

Use the `-Mode=QueryTargets` parameter to call UBT to generate the `Intermediate/TargetInfo.json` file, and parse it to get the result.

### `build` and `clean`

Use UBT's `Build` and `Clean` functionality.

### `run`

UBT will generate a \<target name\>`.target` file in JSON format for each target, and parse its `Launch` field to get the path to the executable file.

### `test`

Currently only `Automation` testing in the editor is supported. The working principle is to find the executable file of the engine command version (`UnrealEditor-Cmd`), generate test commands and pass them to it for execution.

## Planned Features

```console
# Run Setup, in engine only
uct setup

# Run explicit test
uct test MyGameTest

# Pack
uct pack

# Create a new module
uct new module

# Create a new C++ class
# Create a ExamEventLoop.h in the Public directory and ExamEventLoop.cpp in the Private directory
cltue new class --public FExamEventLoop
```
