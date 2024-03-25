# UCT：虚幻引擎命令行工具

[English](README.md) | 简体中文

## UCT 是什么？

UCT 是 Unreal Commandline Tool 的缩写，它是一个强大的命令行工具，可以让你更轻松地进行虚幻引擎下的构建、测试、运行等日常开发工作。

## 背景

很多情况下，我更喜欢命令行工具，因为它们是快速且容易自动化。 我经常在 VS Code 中为 UE 编写代码，因为它比 Visual Studio 更快更轻量，git 集成更好。
所以我经常需要手动调用 [UBT](https://docs.unrealengine.com/4.27/en-US/ProductionPipelines/BuildTools/UnrealBuildTool/) 和 Editor，
但它们的命令行界面非常冗长。

例如，要构建一个程序：

```console
G:\MyGame> G:\UnrealEngine-5.1\Engine\Build\BatchFiles\Build.bat Benchmark Win64 Development -Project="G:\MyGame\MyGame.uproject"
```

要从命令行运行测试：

```console
G:\MyGame>G:\UnrealEngine-5.1\Engine\Binaries\Win64\UnrealEditor-Cmd.exe %CD%/MyGame.uproject -ExecCmds="Automation RunAll"
```

这些命令行界面主要有如下问题：

- 你必须使用正确的引擎目录下的 UBT 来构建游戏工程。在我的开发机上有好几个版本的引擎，而且都在使用，所以无法把 UBT 的路径加入 PATH 环境变量，只能使用全路径。
- UBT 和其他脚本的路径和后缀在 Windows 和 Mac/Linux 上都不一样。
- `-Project` 参数的路径必须是绝对路径，这很无聊，我们可以使用 `%CD%` 来简化，但它仍然需要项目文件名。
- 有些选项比如 `Development` 等太长了。
- 编辑器的文件名对不同的配置有不同的后缀，例如 `UnrealEditor-Win64-Debug.exe`。

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

UCT 支持在 Win64、Linux 和 Mac 中运行.

## 安装

只需使用 `git clone` 下载代码，然后执行 `install.bat` 即可：

```console
git clone https://github.com/chen3feng/uct
cd uct
install.bat
```

UCT 的路径就会注册到您的 PATH 环境中，您可以从系统中的任何位置调用它。

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

### list-targets

列出所有目标：

```console
$ uct list-targets
BaseTextureBuildWorker
BenchmarkTool
BlankProgram
BuildPatchTool
...
```

列出所有引擎目标：

```console
$ uct list-targets --engine
BaseTextureBuildWorker
BenchmarkTool
BlankProgram
BuildPatchTool
...
```

列出所有项目目标：

```console
$ uct list-targets --project
MyGameTest
MyGameClient
MyGameEditor
MyGameServer
MyGameBenchmark
````

用 `--verbose` 选项输出详情：

```console
$ uct list-targets --verbose
Type      Name                            Path
------------------------------------------------------------------------------------------------------------------------
Program   BaseTextureBuildWorker          G:\UnrealEngine-5.1\Engine\Source\Programs\BaseTextureBuildWorker\BaseTextureBuildWorker.Target.cs
Program   BenchmarkTool                   G:\UnrealEngine-5.1\Engine\Source\Programs\BenchmarkTool\BenchmarkTool.Target.cs
Program   BlankProgram                    G:\UnrealEngine-5.1\Engine\Source\Programs\BlankProgram\BlankProgram.Target.cs
```

### generate-project-files

为引擎或游戏项目生成项目文件。

```console
$ uct generate-project-files
...
```

根据当前目录生成项目或引擎的项目文件。

### build

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

请参阅上面的 `build` 命令以供参考。

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

## 计划的功能

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
