# [WIP] Command Line Tools for Unreal Engine

Planed features:

```console
# Run Setup, in engine only
uct setup

# Generate project files
uct project vscode

# Build targets
uct build game editor client server

# Build with configurations
uct build -c debug -p linux

# Clean
uct clean

# Run program
uct run

# Pack
uct pack

# Create a new module
uct new module

# Create a new C++ class
# Create a ExamEventLoop.h in the Public directory and ExamEventLoop.cpp in the Private directory
cltue new class --public FExamEventLoop
```
