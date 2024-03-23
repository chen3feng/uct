@echo off

set THIS_DIR=%~dp0
:: Remove trailing back slash if any
if "%THIS_DIR:~-1%" == "\" set "THIS_DIR=%THIS_DIR:~0,-1%"

set "PATH=%THIS_DIR%;%PATH%"

set UserPath=
for /f "tokens=3*" %%i in ('reg query "HKCU\Environment" /v "Path" 2^>nul') do set "UserPath=%%i"

echo %UserPath% | findstr /C:%THIS_DIR%
if errorlevel 1 (
    setx PATH "%UserPath%;%THIS_DIR%"
    echo UCT is added to you user PATH.
) else (
    echo UCT is already in your path
)
