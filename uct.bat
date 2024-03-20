@echo off

setlocal EnableDelayedExpansion

set ENGINE_ROOT=
set PROJECT_FILE=

call :FindFileBottomUp GenerateProjectFiles.*
if defined FOUND_FILE (
    for %%I in ("%FOUND_FILE%") do set "ENGINE_ROOT=%%~dpI"
    :: Remove trailing backslashes
    if "!ENGINE_ROOT:~-1!"=="\" set "ENGINE_ROOT=!ENGINE_ROOT:~0,-1!"
) else (
    call :FindFileBottomUp *.uproject
    if defined FOUND_FILE (
        set "PROJECT_FILE=!FOUND_FILE!"
        ::echo Found unreal project "!PROJECT_FILE!"
        call :FindProjectEngineDir !PROJECT_FILE!
    )
)

if defined ENGINE_ROOT (
    :: echo Find unreal engine "!ENGINE_ROOT!"
    set "PYTHON_EXE=!ENGINE_ROOT!\Engine\Binaries\ThirdParty\Python3\Win64\python.exe"
    if exist !PYTHON_EXE! (
        set PYTHONDONTWRITEBYTECODE=1
        !PYTHON_EXE! %~dp0uct.py
    ) else (
        echo Can't find python !PYTHON_EXE! in your engine, maybe it is not setup. 1>&2
    )
) else (
    echo Can't find unreal engine, you must under the directory of an engine or a game project. 1>&2
    exit /b 1
)

goto :EOF

::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:: Functions
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

:: Find file bottom up
:: Args:
::  file pattern: wildcard
:FindFileBottomUp
set FOUND_FILE=
set "currentDir=%CD%"
:FindUpper
call :FindFileInDir %1 %currentDir%
if defined FOUND_FILE exit /b
set parentDir=
for %%I in ("%currentDir%") do set "parentDir=%%~dpI"
if not defined parentDir exit /b
:: Remove trailing backslashes
if "%parentDir:~-1%"=="\" set "parentDir=%parentDir:~0,-1%"

:: Return if parentDir is the drive name
:: The spaces before "|" are also echoed, such as echo A | findstr... will echo "A "
:: make it can't match the "$" in regex. so I have to use "{}" around the text. stupid cmd prompt.
echo "{%parentDir%}" | findstr /R "{[A-Za-z]:}" >nul
if %errorlevel% == 0 exit /b

if not "%parentDir%" == "%currentDir%" (
    set "currentDir=!parentDir!"
    goto :FindUpper
)
exit /b

:: Find file in dir
:: Args:
::  file pattern: wildcard
::  target directory
:FindFileInDir
for %%F in ("%2\%1") do (
    set "FOUND_FILE=%%F"
    exit /b
)
exit /b


:FindProjectEngineDir

set "key=HKEY_CURRENT_USER\Software\Epic Games\Unreal Engine\Builds"
:: Iterate over each line in the file
for /f "tokens=*" %%a in ('type "%1" ^| findstr /C:"EngineAssociation"') do (
    for /f "tokens=2 delims={}" %%b in ("%%a") do (
        :: Read the registry value
        for /f "tokens=3*" %%c in ('reg query "%key%" /v "{%%b}" 2^>nul ^| findstr /C:"REG_SZ"') do (
            set "ENGINE_ROOT=%%c"
            :: Replace forward slashes with backslashes
            set "ENGINE_ROOT=!ENGINE_ROOT:/=\!"
        )
    )
)
exit /b
