# Command Line Tool for Unreal Engine

English | [简体中文](README-zh.md)

## What is UCT?

UCT (Unreal Commandline Tool) is a powerful command line tool to buid, test and run unreal engine based project easier.

Let's see a demo.

[![asciicast](https://asciinema.org/a/6KbwPkTAF2iqzYuzbYuYvqb6O.svg)](https://asciinema.org/a/6KbwPkTAF2iqzYuzbYuYvqb6O)

Used in windows and UE 4.27:

[![asciicast](https://asciinema.org/a/nDX0Gdw5KFvDckNGp7HA12PGJ.svg)](https://asciinema.org/a/nDX0Gdw5KFvDckNGp7HA12PGJ)

## Background

Usually development on EU is done in Visual Studio and Editor on Windows systems. But sometimes,

- When traveling or at home, without access to the Windows workstation in the office, I have to develop, build, and test on a Mac system.
- Even on the Windows workstation, I often use Visual Studio Code to open projects because it is more lightweight,
  rich in plug-ins, fast to start, and has better git integration.

In these cases, you need to use command line tools, such as [UBT](https://docs.unrealengine.com/4.27/en-US/ProductionPipelines/BuildTools/UnrealBuildTool/),
[UAT](https://docs.unrealengine.com/4.27/en-US/ProductionPipelines/BuildTools/AutomationTool/) and
[Editor](https://docs.unrealengine.com/4.27/en-US/ProductionPipelines/CommandLineArguments/).

And in many cases, it is more convenient to use command line tools because they are easy to batch and automate.
Additionally, some UE features can only be accessed from the command line, such as [implicit tests in the low level tests](https://dev.epicgames.com/documentation/en-us/unreal-engine/build-and-run-low-level-tests-in-unreal-engine).

But the command line interfaces in UE systems are very boring.

For example, to build a program:

```console
G:\MyGame> G:\UnrealEngine-5.1\Engine\Build\BatchFiles\Build.bat Benchmark Win64 Development -Project="G:\MyGame\MyGame.uproject"
```

To run tests from command line:

```console
G:\MyGame>G:\UnrealEngine-5.1\Engine\Binaries\Win64\UnrealEditor-Cmd.exe %CD%/MyGame.uproject -ExecCmds="Automation RunAll"
```

To packing is insanely more complicated:

```console
E:\UE_5.2\Build\BatchFiles\RunUAT.bat ^
BuildCookRun -project=E:/AllProject/UE_5_2_0/BuildTest/BuildTest.uproject ^
-ScriptsForProject=E:/AllProject/UE_5_2_0/BuildTest/BuildTest.uproject ^
Turnkey -command=VerifySdk -platform=Android -UpdateIfNeeded ^
BuildCookRun -nop4 -utf8output -nocompileeditor -skipbuildeditor -cook ^
-project=E:/AllProject/UE_5_2_0/BuildTest/BuildTest.uproject -target=BuildTest ^
-unrealexe=E:\UE\UE_4.27_Source\UnrealEngine\Engine\Binaries\Win64\UnrealEditor-Cmd.exe ^
-platform=Android -cookflavor=ASTC -stage -archive -package -build -pak -iostore -compressed -prereqs ^
-archivedirectory=E:/AllProject/UE_5_2_0/BuildTest/PakOutputX -clientconfig=Development -nocompile -nocompileuat
```

These user interface has the following problems:

- You must use the UBT in the correct engine directory to build the game project.
  There are several versions of the engine on my workstation, and they are all in use,
  so I can not add the UBT path to the PATH environment variable. I have to use the full path.
- The path and suffix of UBT and other scripts are different between Windows and Mac/Linux.
- The file name of the editor also have different suffix for different configurations, for example `UnrealEditor-Win64-Debug.exe`.
- The path of the `-Project` argument must be a absolute path, it's boring, we can use `%CD%` to simplify it
  but it still need the project file name.
- Some options such as `Development` are so long.

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

### Setup

Execute the `Setup.bat` or `Setup.sh` in the engine root directory.

```console
$ uct setup
...
```

### Generate Project Files

Generate project files for the engine or game project.

```console
$ uct generate project
...
```

### switch engine

When this command is executed, UCT generates a menu listing all installed engines and engines built from source code
on the current system. Use the up and down arrows to select, press Enter to confirm, and ESC to cancel.

```console
G:\MyGame>switch engine
Switch engine
Installed engines:
[ ] 5.1.1    D:\Game\UE_5.1
[ ] 5.3.2    D:\Game\UE_5.3
[ ] 5.2.1    D:\Game\UE_5.2
Source build engines:
[x] 5.1.1    G:\UnrealEngine-5.1
[ ] 4.27.2   G:\UnrealEngine-4.27.2
[ ] 5.3.1    G:\UnrealEngine-5.3.1
Engine is switched to {750E0EB6-4428-07C4-DFB6-888F4E6452A6}  5.1.1    G:\UnrealEngine-5.1
```

### List

#### list targets

List all targets:

```console
$ uct list targets
BaseTextureBuildWorker
BenchmarkTool
BlankProgram
BuildPatchTool
...
```

List all engine targets:

```console
$ uct list targets --engine
BaseTextureBuildWorker
BenchmarkTool
BlankProgram
BuildPatchTool
...
```

List all project targets:

```console
$ uct list targets --project
MyGameTest
MyGameClient
MyGameEditor
MyGameServer
MyGameBenchmark
```

Make verbose output with the `--verbose` option:

```console
$ uct list targets --verbose
Type      Name                            Path
------------------------------------------------------------------------------------------------------------------------
Program   BaseTextureBuildWorker          G:\UnrealEngine-5.1\Engine\Source\Programs\BaseTextureBuildWorker\BaseTextureBuildWorker.Target.cs
Program   BenchmarkTool                   G:\UnrealEngine-5.1\Engine\Source\Programs\BenchmarkTool\BenchmarkTool.Target.cs
Program   BlankProgram                    G:\UnrealEngine-5.1\Engine\Source\Programs\BlankProgram\BlankProgram.Target.cs
```

#### list engines

List all unreal engines in the current system.

```console
$ uct list engines
Installed engines:
UE_5.1  5.1.1    /Volumes/SSD/software/EpicGames/UE_5.1
UE_5.2  5.2.1    /Volumes/SSD/software/EpicGames/UE_5.2
UE_5.3  5.3.2    /Volumes/SSD/software/EpicGames/UE_5.3

Registered source build engines:
{46E95257-8C4E-4D80-C21A-AB88D9179249}  5.1.0    /Volumes/SSD/code/UnrealEngine-5.1
{CCB0C841-B544-47A2-A486-C3908D365428}  5.2.1    /Volumes/SSD/code/UnrealEngine-5.2
{3BC4DCDD-7743-67E3-8361-5D90FEB4A5B2}  4.27.2   /Volumes/SSD/code/UnrealEngine-4.27
```

### Build

Build specified targets.

#### Targets Syntax

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

This command supports wildcard target names:

```console
uct build MyProject*
uct build *Editor
uct build MyProject* *Editor
```

On Linux or Mac, in some cases wildcards need to be quoted in order to work properly, see below for details.

Target patterns are case insensitive, so you can also use `unrealeditor` to build `UnrealEditor`:

```console
$ uct build unrealeditor
...
```

The targets will be matched in both project and engine by default. You can use `--project` or `--engine` option to limit the matching scope.

```console
uct build --project "*"
```

build all targets in the game project.

#### Target Platform and Configuration

This command supports specifying [build configuration](https://dev.epicgames.com/documentation/en-us/unreal-engine/build-configurations-reference-for-unreal-engine?application_version=5.3)
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

#### Compile Single File

The build command also supports `-f` or `--files` to specify files to comile only.
It is useful to verify the syntax and non-unity build correctness quickly.
Bucause in the single file compile mode unity build is always disabled.

This option supports the following formats:

- An absolute path: `/Work/MyGame/Source/MyGame/HelloWorldGreeterImpl.cpp`.
- A relative path: `MyGame/HelloWorldGreeterImpl.cpp` from current directory.
- A path with @engine prefix: `@engine/Source/Runtime/Engine/Private/NetDriver.cpp` means under the engine directory.

All above format supports wildcard pattern: `Source/**/*Test.cpp`, `**` means any layer of subdirectories.
The rules for using quotes are the same as in build targets.

Example:

```console
# Build all source files.
uct build MyGame -f "Source/**/HelloWorldGreeterImpl.cpp"

# Compile NetDriver.cpp and DataChannel.cpp under the engine directory.
uct build MyGame -f "@engine/Source/**/NetDriver.cpp" "@engine/Source/**/DataChannel.cpp"

# Build all source files under MyModule.
uct Build MyGame -f "Source/MyModule/**/*.cpp"
```

#### Pass UBT flags

UCT will generate appropriate UBT commands based on the command line parameters for the actual build.

UBT has many [options](https://ikrima.dev/ue4guide/build-guide/utilities/devops-build-automation/),
Some useful usecases:

- Enable [Clang Sanitizers](https://dev.epicgames.com/documentation/en-us/unreal-engine/using-clang-sanitizers-in-unreal-engine-projects)
- Enable [Static Code Analysis](https://dev.epicgames.com/documentation/en-us/unreal-engine/static-code-analysis-in-unreal-engine)

To pass extra options to UBT, put them after a standalone `--` like this:

```console
uct build MyGame -- -StaticAnalyzer=VisualCpp
```

### Clean

Clean one or more targets, example:

```console
$ uct clean Benchmark UnrealEditor
...
```

The supported options are similar to `build`, See the above `build` for reference.

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

### open

Open specified file.

According to your terminal environment:

- If you in the integrated terminal in Visual Studio or Visual Studio Code, it will be opened in the according text editor.
- Otherwise, it will be opend in file explorer.

This command supports the `--engine` and `--project` option.

#### open file

Open specified source file.

Examples:

```console
# Open Engine/Source/Runtime/Core/Private/Containers/String.cpp
uct open file string.cpp

# Open Engine/Source/Runtime/Core/Public/Containers/UnrealString.h
uct open file unrealstring.h

# Open Engine/Source/Runtime/Core/Core.Build.cs
uct open file "core.*.cs"
```

#### open module

Open the `.Build.cs` file for the specified module in your workspace.

Example:

```console
uct open module MyGameModule
uct open module Core
uct open module Engine
```

#### open plugin

Similar to `open module`, but open the `.uplugin` file.

Example:

```console
uct open plugin Paper2D
uct open plugin OnlineSubsystem
```

### pack

Pack the target to specified output directory.

Arguments:

- `--output` Output directory of the packed result.

Example:

```console
$ uct pack --config=ship --output=pack_dir MyGame
...
Archive command time: 1.13 s
********** ARCHIVE COMMAND COMPLETED **********
BuildCookRun time: 58.27 s
BUILD SUCCESSFUL
AutomationTool executed for 0h 0m 59s
AutomationTool exiting with ExitCode=0 (Success)
```

### runubt and runuat

Building and packaging are performed by calling UBT or UAT, which are their specific usage modes. UCT also provides the ability to fully use them by calling them directly:

- `runubt`: Run [UnrealBuildTool](https://docs.unrealengine.com/4.27/en-US/ProductionPipelines/BuildTools/UnrealBuildTool/)
- `runuat`: Run [AutomationTool](https://docs.unrealengine.com/4.27/en-US/ProductionPipelines/BuildTools/AutomationTool/)

All options after the first standalone `--` are passed to the tool.

Example:

```console
$ uct runuat -- -help
...
$ uct runubt -- -help
...
```

The advantage compared to directly calling the corresponding script in the engine is that there is no need to specify the path and extension (`.bat` or `.sh`).

### help

To view help, use the `--help` parameter. To view help for a command, add `--test` after the command.

```console
# View help
uct --help

# View help for the build command
uct build --help
```

### Wildcards

Many commands supports wildcards:

```console
uct build MyProject*
uct build *Editor
uct build MyProject* *Editor
```

On Linux and Mac, since wildcards are expanded by the shell, add quotes if necessary to avoid expansion into matching project file names:

```console
uct build "MyProject*"
uct build *Editor
uct build "MyProject*" *Editor
```

On Linux and Mac, both single and double quotes are OK. On Windows, since wildcards are expanded by the program itself
rather than by the shell, quotation marks are not necessary, but if they are used, they must be double quotation marks
and not single quotation marks.

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
# Run explicit test
uct test MyGameTest

# Create a new module
uct new module

# Create a new C++ class
# Create a ExamEventLoop.h in the Public directory and ExamEventLoop.cpp in the Private directory
cltue new class --public FExamEventLoop
```
