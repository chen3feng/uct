# UCT：虚幻引擎命令行工具

[English](README.md) | 简体中文

## UCT 是什么？

UCT 是 Unreal Commandline Tool 的缩写，它是一个强大的命令行工具，可以让你更轻松地进行虚幻引擎下的构建、测试、运行等日常开发工作。

先看个演示吧：

[![asciicast](https://asciinema.org/a/6KbwPkTAF2iqzYuzbYuYvqb6O.svg)](https://asciinema.org/a/6KbwPkTAF2iqzYuzbYuYvqb6O)

在 Windows 和 UE 4.27 上:

[![asciicast](https://asciinema.org/a/nDX0Gdw5KFvDckNGp7HA12PGJ.svg)](https://asciinema.org/a/nDX0Gdw5KFvDckNGp7HA12PGJ)

## 背景

通常 EU 上的开发是在 Windows 系统上的 Visual Studio 和 Editor 中进行。但是有些时候，

- 出差或者在家时，无法访问办公室里的 Windows 工作站，要在 Mac 系统上开发构建测试。
- 即使在 Windows 工作站中，我也常用 Visual Studio Code 来打开项目，因为它更轻量，插件丰富，启动速度快，git 集成也更好。

在这些情况下，都需要用到命令行工具，比如 [UBT](https://docs.unrealengine.com/4.27/zh-CN/ProductionPipelines/BuildTools/UnrealBuildTool/)、
[UAT](https://docs.unrealengine.com/4.27/en-US/ProductionPipelines/BuildTools/AutomationTool/) 和
[Editor](https://docs.unrealengine.com/4.27/zh-CN/ProductionPipelines/CommandLineArguments/)。

而且很多情况下，用命令行工具更方便，因为它们容易批量化和自动化。

但是 UE 系统中的命令行界面都非常冗长。

例如，要构建一个程序：

```console
G:\MyGame> G:\UnrealEngine-5.1\Engine\Build\BatchFiles\Build.bat Benchmark Win64 Development -Project="G:\MyGame\MyGame.uproject"
```

要从命令行运行测试：

```console
G:\MyGame>G:\UnrealEngine-5.1\Engine\Binaries\Win64\UnrealEditor-Cmd.exe %CD%/MyGame.uproject -ExecCmds="Automation RunAll"
```

打包就是更复杂到疯狂了:

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

这些命令行界面主要有如下问题：

- 你必须使用正确的引擎目录下的 UBT 来构建游戏工程。在我的开发机上有好几个版本的引擎，而且都在使用，所以无法把 UBT 的路径加入 PATH 环境变量，只能使用全路径。
- UBT 和其他脚本的路径和后缀在 Windows 和 Mac/Linux 上都不一样。
- 编辑器的文件名对不同的配置也有不同的后缀，例如 `UnrealEditor-Win64-Debug.exe`。
- `-Project` 参数的路径必须是绝对路径，这很无聊，我们可以使用 `%CD%` 来简化，但它仍然需要项目文件名。
- 有些选项比如 `Development` 等太长了。

因此，我开发了这个便利的工具，以方便我的生活，也许能同样方便您的生活。

有了这个工具，您不再需要：

- 输入 UBT 的完整路径。
  如果当前目录在游戏工程或引擎目录下，UCT 就会自动找到它。
- 传入 `-Project=/Full/Path/To/YourGame.uproject`。
  如果你的当前目录在游戏项目下，UCT 也会自动找到它。
- 输入 `Win64`。
  UCT 默认目标平台就是主机平台（当然也可以通过参数指定）。
- 输入 `Development`。
  UCT 默认 Development 构建，即使要指定，用 `-c dev` 也更简单。

## 支持的系统

UCT 支持在 Win64、Linux 和 Mac 中运行，在 UE 5.1、5.2、5.3 和 4.27 上测试通过。

## 安装

只需使用 `git clone` 下载代码，然后执行 `install` 命令 即可：

```console
git clone https://github.com/chen3feng/uct
cd uct
install.bat
```

UCT 的路径就会注册到您的 PATH 环境中，您可以从系统中的任何位置调用它。

在 Linux 或者 Mac 下，安装命令是 `./install`。

## 基本概念

请参阅 UE 文档了解以下概念：

- [Target](https://docs.unrealengine.com/4.27/en-US/ProductionPipelines/BuildTools/UnrealBuildTool/TargetFiles/) 每个 `.Target.cs` 文件描述一个目标。
- [目标平台](https://unrealcommunity.wiki/6100e8109c9d1a89e0c31618) UE 支持 `Win64`、`Linux`、`Mac` 和一些其他平台，例如 `Hololens`。
- [配置](https://docs.unrealengine.com/4.27/en-US/ProductionPipelines/DevelopmentSetup/BuildConfigurations/)，例如 `Debug`、`Development`、`Shipping` 和 `Test`。
- [模块](https://docs.unrealengine.com/4.27/en-US/ProductionPipelines/BuildTools/UnrealBuildTool/ModuleFiles/) 每个 `.Build.cs` 文件描述一个模块。

## 命令行界面

基本接口是：

`uct` \<命令\> 选项...

例如：

```console
uct build -c dbg -p linux Benchmark
```

`build` 是命令，`-c dbg` 和 `-p linux` 是选项，`Benchmark` 是构建目标。

就像 `git` 命令一样。 很简单吧？

UCT 支持以下命令：

### setup

执行引擎根目录下的 `Setup.bat` 或者 `Setup.sh` 命令.

```console
$ uct setup
...
```

### generate-project

根据当前目录的是项目还是引擎来生成相应的项目文件。

```console
$ uct generate-project
...
```

### list

#### list targets

列出所有目标：

```console
$ uct list targets
BaseTextureBuildWorker
BenchmarkTool
BlankProgram
BuildPatchTool
...
```

列出所有引擎目标：

```console
$ uct list targets --engine
BaseTextureBuildWorker
BenchmarkTool
BlankProgram
BuildPatchTool
...
```

列出所有项目目标：

```console
$ uct list targets --project
MyGameTest
MyGameClient
MyGameEditor
MyGameServer
MyGameBenchmark
````

用 `--verbose` 选项输出详情：

```console
$ uct list targets --verbose
Type      Name                            Path
------------------------------------------------------------------------------------------------------------------------
Program   BaseTextureBuildWorker          G:\UnrealEngine-5.1\Engine\Source\Programs\BaseTextureBuildWorker\BaseTextureBuildWorker.Target.cs
Program   BenchmarkTool                   G:\UnrealEngine-5.1\Engine\Source\Programs\BenchmarkTool\BenchmarkTool.Target.cs
Program   BlankProgram                    G:\UnrealEngine-5.1\Engine\Source\Programs\BlankProgram\BlankProgram.Target.cs
```

#### list engines

列出当前系统中所有的虚幻引擎：

```console
$ uct list engines
Installed engines:
UE_5.1  5.1.1    /Volumes/SSD/software/EpicGames/UE_5.1
UE_5.2  5.2.1    /Volumes/SSD/software/EpicGames/UE_5.2
UE_5.3  5.3.2    /Volumes/SSD/software/EpicGames/UE_5.3

Registered source built engines:
{46E95257-8C4E-4D80-C21A-AB88D9179249}  5.1.0    /Volumes/SSD/code/UnrealEngine-5.1
{CCB0C841-B544-47A2-A486-C3908D365428}  5.2.1    /Volumes/SSD/code/UnrealEngine-5.2
{3BC4DCDD-7743-67E3-8361-5D90FEB4A5B2}  4.27.2   /Volumes/SSD/code/UnrealEngine-4.27
```

### build

构建指定的目标。

#### 目标语法

构建一个目标：

```console
$ uct build UnrealEditor
...
```

构建多个目标：

```console
$ uct build Benchmark UnrealEditor
...
```

它还支持通配符目标名：

```console
uct build MyProject*
uct build *Editor
uct build MyProject* *Editor
```

在 Linux 和 Mac 上，由于通配符是由 shell 展开的，必要时要加上引号以避免展开为匹配的工程文件名：

```console
uct build "MyProject*"
uct build *Editor
uct build "MyProject*" *Editor
```

在 Linux 和 Mac 上，单引号和双引号都可以。在 Windows 上，由于通配符是由程序自己而不是 shell 来展开的，
引号不是必需的，但是如果要用，只能用双引号不能用单引号。

默认情况下，目标将同时在项目和引擎中匹配。 您可以使用 `--project` 或 `--engine` 选项来限制匹配范围。

```console
uct build --project "*"
```

构建游戏项目中的所有目标。

#### 目标平台和配置

它支持指定[构建配置](https://dev.epicgames.com/documentation/en-us/unreal-engine/build-configurations-reference-for-unreal-engine?application_version=5.3)
和[目标平台](https://unrealcommunity.wiki/6100e8109c9d1a89e0c31618)：

```console
uct build -c debug -p linux
```

不同目标平台所用的选项值：

- `Win64`：`win64`
- `Linux`：`linux`
- `Mac`：`mac`

不同构建配置的选项值：

- `Debug`： `dbg` 或 `debug`
- `DebugGame`： `dbgm` 或 `debuggame`
- `Development`： `dev` 或 `develop`
- `Shipping`: `ship`
- `Test`: `test`

为了简化输入，在 UCT 中，这些名称均为小写。

#### 编译单个文件

构建命令还支持 `-f` 或 `--files` 来指定仅编译的文件。这对快速验证语法和非统一构建的正确性非常有用，因为单文件编译模式总是禁用 Unity Build。

本选项的参数支持以下格式：

- 绝对路径：`/Work/MyGame/Source/MyGame/HelloWorldGreeterImpl.cpp`
- 相对路径：`MyGame/HelloWorldGreeterImpl.cpp`，相对当前目录。
- 带有 `@engine` 前缀的路径：`@engine/Source/Runtime/Engine/Private/NetDriver.cpp`，表示在引擎目录下。

以上格式均支持通配符模式：`Source/**/*Test.cpp`，`**` 表示任意层的子目录。引号的使用规则和构建目标中一样。

示例：

```console
# Build all source files.
uct build MyGame -f "Source/**/HelloWorldGreeterImpl.cpp"

# Compile NetDriver.cpp and DataChannel.cpp under the engine directory.
uct build MyGame -f "@engine/Source/**/NetDriver.cpp" "@engine/Source/**/DataChannel.cpp"

# Build all source files under MyModule.
uct Build MyGame -f "Source/MyModule/**/*.cpp"
```

#### 传递 UBT 选项

UCT 会根据命令行参数生成合适的 UBT 命令进行实际的构建。
要将额外的[构建参数](https://ikrima.dev/ue4guide/build-guide/utilities/devops-build-automation/)传递给 UBT，请这样将它们放在单独的 `--` 后面：

```console
uct build MyGame -- -StaticAnalyzer=VisualCpp
```

### clean

清理一个或多个目标，例如：

```console
$ uct clean Benchmark UnrealEditor
...
```

支持的选项和 `build` 类似，请参阅上面的 `build` 命令。

### run

运行一个或者多个程序：

```console
$ uct run Benchmark
Run G:\MyGame\Binaries\Win64\Benchmark.exe
LogBenchmark: Display: Running 'BM_Serialize<FFieldTest>'...
LogBenchmark: Display: Running 'BM_Serialize<FBenchmarkTest>'...
LogBenchmark: Display: Running 'BM_Deserialize<FFieldTest>'...
LogBenchmark: Display: Serialized size=109
...

第一个 `--` 之后的所有参数都会被传递给程序：

```console
uct run Benchmark -- --help --help
```

该程序就会收到 `--help ---help` 参数。

### test

UCT 使用 [`-ExecCmds Automation ...`](https://docs.unrealengine.com/4.27/en-US/TestingAndOptimization/Automation/TechnicalGuide/)
执行自动化测试。

选项：

- `--list`：列出所有测试
- `--run-all`：运行所有测试
- `--run`：运行指定的测试，以空格分隔
- `--cmds`：您想要运行的任何额外测试命令

例子：

```console
# 列出所有测试
uct test --list

# 运行所有测试
uct test --run-all

# 运行所有以“System.Core”开头的测试
uct test --run System.Core
```

`--cmds` 选项可用于向系统传递更多[测试命令](https://forums.unrealengine.com/t/run-automated-testing-from-command-line/294995)。

例子：

```console
uct test --cmds List RunAll "RunTests System" Quit
```

-ExecCmd 命令是 `Automation List; RunAll; "RunTests System"; Quit`.

根据 UE 的源码，可以使用以下测试命令：

```text
Automation List
Automation RunTests <test string>
Automation RunAll
Automation RunFilter <filter name>
Automation SetFilter <filter name>
Automation Quit
```

### open

打开特定的文件。

#### open module

打开当前工作空间中指定模块的 `.Build.cs` 文件。

根据当前所在的终端环境：

- 如果是在 Visual Studio 或者 Visual Studio Code 的集成终端中，在相应的文本编辑器中打开。
- 否则，在系统的文件浏览器中打开。

本命令支持 `--engine` 和 `--project` 选项。

示例：

```console
uct open module MyGameModule
uct open module Core
uct open module Engine
```

#### open plugin

类似 `open module`，打开指定插件的 `.uplugin` 文件。

示例：

```console
uct open plugin Paper2D
uct open plugin OnlineSubsystem
```

### pack

将目标打包到指定的输出目录。

参数：

- `--output` 打包结果的输出目录。

示例：

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

### 帮助

要查看帮助，使用 `--help` 参数，要查看命令的帮助，在命令后加 `--test`。

```console
# 查看帮助
uct --help

# 查看 build 命令的帮助
uct build --help
```

### 命令行补全

UCT 通过使用 `argcomplete` 库来支持 bash 和 zsh 中的命令自动补全，
请参阅其[文档](https://pypi.org/project/argcomplete/) 来启用它。

## 工作原理

了解 UCT 的工作原理对使用有帮助，也欢迎贡献代码。

### 启动

UCT 必须在项目或者引擎的目录下运行。当 UCT 被调用时，它会先从当前目录往上搜索 `uproject` 文件，如果找到就认为是在项目目录中，
解析项目文件得到项目关联的引擎 ID，根据系统不同，用不同的方式得到引擎所在的目录。

- 在 Windows 上，读取注册表 `HKEY_CURRENT_USER\Software\Epic Games\Unreal Engine\Builds`
- 在 Mac 和 Linux 上，读取配置文件 `~/.config/Epic/UnrealEngine/Install.ini`。

如果找不到项目文件，就用类似的方式找 UE 引擎的特征文件（GenerateProjectFiles.bat），得到引擎的根目录。

在 Linux 和 Mac 下，上述查找过程是在 python 中进行的的。

在 Windows 上，上述查找过程是用批处理，然后通过环境变量的传给 UE 内置的 python 解释器（`Engine\Binaries\ThirdParty\Python3\Win64\python.exe`）。这是因为 Windows 系统缺乏统一的 Python 安装，而引擎中已经内置了 Python 解释器。

找到了项目和引擎的目录，UBT 路径等就不在话下了。

### `list-targets`

用 `-Mode=QueryTargets` 参数调用 UBT，生成 `Intermediate/TargetInfo.json` 文件，解析即可得到结果。

### `build` 和 `clean`

调用 UBT 的 `Build` 和 `Clean` 功能。

### `run`

UBT 会为每个目标生成一个 JSON 格式的 \<目标名\>`.target` 文件，解析其 `Launch` 字段即可得到的到可执行文件的路径。

### `test`

目前仅支持在编辑器中的 `Automation` 测试，工作原理为找到引擎命令版的可执行文件（`UnrealEditor-Cmd`），生成测试命令传给它执行。

## 计划的功能

```console
# Run explicit test
uct test MyGameTest

# Create a new module
uct new module

# Create a new C++ class
# Create a ExamEventLoop.h in the Public directory and ExamEventLoop.cpp in the Private directory
uct new class --public FExamEventLoop

```
