# [WIP] Command Line Tools for Unreal Engine

Planed features:

```console
# Run Setup, in engine only
cltue setup

# Generate project files
cltue project vscode

# Build targets
cltue build game editor client server

# Build with configurations
cltue build -c debug -p linux

# Clean
cltue clean

# Run program
cltue run

# Pack
clute pack

# Create a new module
cltue new module

# Create a new C++ class
# Create a ExamEventLoop.h in the Public directory and ExamEventLoop.cpp in the Private directory
cltue new class --public FExamEventLoop
```
