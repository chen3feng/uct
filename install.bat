@echo off

set THIS_DIR=%~dp0
set "PATH=%THIS_DIR%;%PATH%"

reg query "HKCU\Environment" /v "Path"
reg query "HKCU\Environment" /v "Path" | findstr %THIS_DIR% >NUL
if errorlevel 1 (
    echo ::reg add "HKCU\Environment" /v "Path" /t REG_EXPAND_SZ /d "%PATH%;%THIS_DIR%" /f
)

