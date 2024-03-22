# [WIP] Command Line Tool for Unreal Engine

## What is it?

This is a powerful command line tool to run unreal build and editor commands much easier.

## Background

Many cases, I prefer command line tools because they are fast and easy automation. I often write code for UE in VS Code,
so I often need to call [UBT](https://docs.unrealengine.com/4.27/en-US/ProductionPipelines/BuildTools/UnrealBuildTool/) manually.
But the its command line interface are very verbose.

For example, to build a Program:

```console
G:\MyGame> G:\UnrealEngine-5.1\Engine\Build\BatchFiles\Build.bat Benchmark Win64 Development -Project="G:\MyGame\MyGame.uproject"
```

To run a test from command line:

```console
G:\Pb4ueRpc>G:\UnrealEngine-5.1\Engine\Binaries\Win64\UnrealEditor-Cmd.exe %CD%/Pb4ueTest.uproject -ExecCmds="Automation RunAll"
```

Its user interface has so many problems:

- You must use UBT under the correct engine directory, here is `G:\UnrealEngine-5.1\Engine\Build\BatchFiles\Build.bat`, but we often have many engines.
- The path of the `-Project` argument must be a absolute path, it's boring, we can use %CD% to simplify but it still need the project file name.
- The options such as `Development` are so long.

So, I developed this handy tool, to simplify my life, and, maybe yours.

With this tool, you needn't:

- Type the the full path of UBT, uct can find it automatically if your current directory is under the game project or the engine directory.
- Pass the -Project=YourGame.uproject, uct can find it automatically if your current directory is under the game project.
- Type `Win64`, uct assume the target platform is also the host platform.
- Type `Development`, `dev` is enough.

## Install

Just use git to clone the code, and execute the `install.bat`:

```console
git clone https://github.com/chen3feng/uct
cd uct
install.bat
```

The path of uct is registered into your `PATH` environment, you can call it from any where in you system.

## Basic Concepts

See UE documents for the following concepts:

- [Target](https://docs.unrealengine.com/4.27/en-US/ProductionPipelines/BuildTools/UnrealBuildTool/TargetFiles/) Each `.Target.cs` describes a target.
- [Target Platform](https://unrealcommunity.wiki/6100e8109c9d1a89e0c31618) UE Support `Win64`, `Linux`, `Mac` and some other such as `Hololens`.
- [Configuration](https://docs.unrealengine.com/4.27/en-US/ProductionPipelines/DevelopmentSetup/BuildConfigurations/), Such as `Debug`, `Development`, `Shipping` and `Test`.
- [Module](https://docs.unrealengine.com/4.27/en-US/ProductionPipelines/BuildTools/UnrealBuildTool/ModuleFiles/) Each `.Build.cs` describes a module.

## Basic Usage

### Command Line Interface

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
uct list-targets --project
MyGameTest
MyGameClient
MyGameEditor
MyGameServer
MyGameBenchmark
```

Verbose output:

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

Build one target

```console
$ uct build -t Benchmark UnrealEditor
...
```

Build multiple targets:

```console
$ uct build -t Benchmark UnrealEditor
...
```

It supports wildcard:

```console
uct build -t MyProject*
uct build -t *Editor
uct build -t MyProject* *Editor
```

It supports specifing [build configuration](https://dev.epicgames.com/documentation/en-us/unreal-engine/build-configurations-reference-for-unreal-engine?application_version=5.3)
and [target platform](https://unrealcommunity.wiki/6100e8109c9d1a89e0c31618):

```console
uct build -c debug -p linux
```

To simplify typing, in UCT, all configuration name are lowercase.
Valid configurations:

- win, win64: Win64
- linux: Linux
- mac: Mac

To pass [extra arguments](https://ikrima.dev/ue4guide/build-guide/utilities/devops-build-automation/) to UBT, put them after a standalone `--`:

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

Run a program:

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

## Test

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

The -ExecCmd command is `Automation List; RunAll; "RunTests System"; Quit`

According to the source code of UE, you can use the following test commands:

```text
Automation List
Automation RunTests <test string>
Automation RunAll
Automation RunFilter <filter name>
Automation SetFilter <filter name>
Automation Quit
```

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