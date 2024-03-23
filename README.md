# Command Line Tool for Unreal Engine

English | [简体中文](README-zh.md)

## What is UCT?

UCT (Unreal Commandline Tool) is a powerful command line tool to buid, test and run unreal engine based project easier.

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

Its user interface has so many problems:

- You must use the UBT in the correct engine directory to build the game project.
  There are several versions of the engine on my workstation, and they are all in use,
  so I can not add the UBT path to the PATH environment variable. I have to use the full path.
- The path and suffix of UBT and other scripts are different between Windows and Mac/Linux.
- The path of the `-Project` argument must be a absolute path, it's boring, we can use `%CD%` to simplify it
  but it still need the project file name.
- Some options such as `Development` are so long.
- The file name of the editor have different suffix for different configurations, for example `UnrealEditor-Win64-Debug.exe`.

So, I developed this handy tool, to simplify my life, and, maybe yours.

With this tool, you need n't:

- Type the the full path of UBT. UCT can find it automatically if your current directory is under the game project or the engine directory.
- Pass the `-Project=/Full/Path/To/YourGame.uproject`. UCT can find it automatically if your current directory is under the game project.
- Type `Win64`. UCT assume the target platform is also the host platform by default, of cause you can also change it.
- Type `Development`. UCT use `Development` by default. Even if you want to specify it, using `-c dev` is also easier.

## Install

Just use git to clone the code, and execute the `install.bat`:

```console
git clone https://github.com/chen3feng/uct
cd uct
install.bat
```

The path of UCT is registered into your `PATH` environment, you can call it from any where in you system.

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
uct build -t Benchmark
```

`build` is the command, `-t Benchmark` is an option.

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
$ uct build -t UnrealEditor
...
```

Build multiple targets:

```console
$ uct build -t Benchmark UnrealEditor
...
```

It supports wildcard target names:

```console
uct build -t MyProject*
uct build -t *Editor
uct build -t MyProject* *Editor
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
uct build -t MyGame -- -StaticAnalyzer=VisualCpp
```

### Clean

Clean one or more targets, example:

```console
$ uct clean -t Benchmark UnrealEditor
...
```

See the above `build` command for reference.

### Run

Run one or more programs:

```console
$ uct run -t Benchmark
Run G:\MyGame\Binaries\Win64\Benchmark.exe
LogBenchmark: Display: Running 'BM_Serialize<FFieldTest>'...
LogBenchmark: Display: Running 'BM_Serialize<FBenchmarkTest>'...
LogBenchmark: Display: Running 'BM_Deserialize<FFieldTest>'...
LogBenchmark: Display: Serialized size=109
...
```

All arguments after the first `--` is passed to the program:

```console
uct run -t Benchmark -- --help --help
```

The program got `--help -- --help` aruguments.

### Test

UCT use [`-ExecCmds Automation ...`](https://forums.unrealengine.com/t/run-automated-testing-from-command-line/294995)
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

The `--cmds` option can be used to pass more test commands to the system.

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

## Planned Features

```console
# Run Setup, in engine only
uct setup

# Pack
uct pack

# Create a new module
uct new module

# Create a new C++ class
# Create a ExamEventLoop.h in the Public directory and ExamEventLoop.cpp in the Private directory
cltue new class --public FExamEventLoop
```
