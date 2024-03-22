# 虚幻引擎命令行工具

[English](README.md) | 简体中文


## 它是什么？

这是一个强大的命令行工具，可以更轻松地运行虚幻构建和编辑器命令。

## 背景

很多情况下，我更喜欢命令行工具，因为它们是快速且简单的自动化。 我经常在VS Code中为UE编写代码，
所以我经常需要手动调用[UBT](https://docs.unrealengine.com/4.27/en-US/ProductionPipelines/BuildTools/UnrealBuildTool/)。
但它的命令行界面非常冗长。

例如，要构建一个程序：

```console
G:\MyGame> G:\UnrealEngine-5.1\Engine\Build\BatchFiles\Build.bat 基准 Win64 开发 -Project="G:\MyGame\MyGame.uproject"
```

要从命令行运行测试：

```console
G:\MyGame>G:\UnrealEngine-5.1\Engine\Binaries\Win64\UnrealEditor-Cmd.exe %CD%/MyGame.uproject -ExecCmds="Automation RunAll"
```

它的用户界面有很多问题：

- 你必须在正确的引擎目录下使用UBT，这里是`G:\UnrealEngine-5.1\Engine\Build\BatchFiles\Build.bat`，但是我们经常有很多引擎。
- `-Project` 参数的路径必须是绝对路径，这很无聊，我们可以使用 %CD% 来简化，但它仍然需要项目文件名。
- “Development”等选项太长了。

因此，我开发了这个方便的工具，以简化我的生活，也许也能同样方便您的生活。

有了这个工具，您不需要：

- 输入UBT的完整路径，如果当前目录在游戏工程或引擎目录下，uct会自动找到。
- 传入-Project=YourGame.uproject，如果你当前目录在游戏项目下，uct会自动找到。
- 输入“Win64”，假设目标平台也是主机平台。
- 输入“Development”、“dev”就足够了。

## 安装

只需使用 git clone 代码，然后执行 `install.bat`：

```console
git clone https://github.com/chen3feng/uct
cd uct
install.bat
```

uct 的路径就会注册到您的 PATH 环境中，您可以从系统中的任何位置调用它。

## 基本概念

请参阅 UE 文档了解以下概念：

- [Target](https://docs.unrealengine.com/4.27/en-US/ProductionPipelines/BuildTools/UnrealBuildTool/TargetFiles/) 每个 `.Target.cs` 描述一个目标。
- [目标平台](https://unrealcommunity.wiki/6100e8109c9d1a89e0c31618) UE 支持 `Win64`、`Linux`、`Mac` 和其他一些，例如 `Hololens`。
- [配置](https://docs.unrealengine.com/4.27/en-US/ProductionPipelines/DevelopmentSetup/BuildConfigurations/)，例如“调试”、“开发”、“运输”和“测试”。
- [模块](https://docs.unrealengine.com/4.27/en-US/ProductionPipelines/BuildTools/UnrealBuildTool/ModuleFiles/) 每个 `.Build.cs` 描述一个模块。

## 命令行界面

基本接口是：

`uct` \<命令\> 选项...

例如：

```console
uct build -t Benchmark
```

`build` 是命令，`-t Benchmark` 是一个选项。

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
uct list-targets --project
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
$ uct build -t UnrealEditor
...
```

构建多个目标：

```console
$ uct build -t Benchmark UnrealEditor
...
```

它还支持通配符：

```console
uct build -t MyProject*
uct build -t *Editor
uct build -t MyProject* *Editor
```

它支持指定[构建配置](https://dev.epicgames.com/documentation/en-us/unreal-engine/build-configurations-reference-for-unreal-engine?application_version=5.3)
和[目标平台](https://unrealcommunity.wiki/6100e8109c9d1a89e0c31618)：

```console
uct build -c debug -p linux
```

不同目标平台所用的选项值：

- `Win64`：`win` 或者 `win64`
- `Linux`：`linux`
- `Mac`：`mac`

不同构建配置的选项值：

- `Development`： `dev` 或 `develop`
- `Debug`： `dbg` 或 `debug`
- `Test`: `test`
- `Shipping`: `ship`

为了简化输入，在 UCT 中，这些名称均为小写。

要将[额外参数](https://ikrima.dev/ue4guide/build-guide/utilities/devops-build-automation/)传递给UBT，请将它们放在单独的 `--` 后面：

```console
uct build -t MyGame -- -StaticAnalyzer=VisualCpp
```

### clean

清理一个或多个目标，例如：

```console
$ uct clean -t Benchmark UnrealEditor
...
```

请参阅上面的 `build` 命令以供参考。

### run

运行一个或者多个程序：

```console
$ uct run -t Benchmark
Run G:\MyGame\Binaries\Win64\Benchmark.exe
LogBenchmark: Display: Running 'BM_Serialize<FFieldTest>'...
LogBenchmark: Display: Running 'BM_Serialize<FBenchmarkTest>'...
LogBenchmark: Display: Running 'BM_Deserialize<FFieldTest>'...
LogBenchmark: Display: Serialized size=109
...

第一个 `--` 之后的所有参数都会被传递给程序：

```console
uct run -t Benchmark -- --help --help
```

该程序就会收到 `--help ---help` 参数。

### test

UCT 使用 [`-ExecCmds Automation ...`](https://forums.unrealengine.com/t/run-automated-testing-from-command-line/294995)
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

`--cmds` 选项可用于向系统传递更多测试命令。

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
