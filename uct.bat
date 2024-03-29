@echo off

setlocal EnableDelayedExpansion

set ENGINE_ROOT_KEY_FILE=
set ENGINE_ROOT=
set PROJECT_FILE=

call :FindFileBottomUp GenerateProjectFiles.* ENGINE_ROOT_KEY_FILE
if defined ENGINE_ROOT_KEY_FILE (
    for %%I in ("%ENGINE_ROOT_KEY_FILE%") do set "ENGINE_ROOT=%%~dpI"
    :: Remove trailing backslash
    if "!ENGINE_ROOT:~-1!"=="\" set "ENGINE_ROOT=!ENGINE_ROOT:~0,-1!"
) else (
    call :FindFileBottomUp *.uproject PROJECT_FILE
    if defined PROJECT_FILE (
        ::echo Found unreal project "!PROJECT_FILE!"
        call :FindEngineByProject "!PROJECT_FILE!" ENGINE_ROOT
		if not defined ENGINE_ROOT (
		    echo Can't find associated unreal engine, check the "EngineAssociation" field in !PROJECT_FILE!. 1>&2
		)
    )
)

if defined ENGINE_ROOT (
    :: echo Find unreal engine "!ENGINE_ROOT!"
    set "PYTHON_EXE=!ENGINE_ROOT!\Engine\Binaries\ThirdParty\Python3\Win64\python.exe"
    if exist !PYTHON_EXE! (
        set PYTHONDONTWRITEBYTECODE=1
        !PYTHON_EXE! %~dp0uct.py %*
    ) else if "%1" == "setup" (
        :: The python in UE is downloaded in setup.
        call %ENGINE_ROOT%\Setup.bat
    ) else (
        echo Can't find python !PYTHON_EXE! in your engine, maybe it is not setup. 1>&2
    )
) else (
    if "%1" == "/?" (
        echo UCT: Unreal command line tool. 1>&2
        echo You should run this command under the directory of an engine or a game project. 1>&2
    ) else (
        echo Can't find the engine, you must under the directory of an engine or a game project. 1>&2
    )
    exit /b 1
)

goto :EOF

::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:: Functions
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

:: function FindFileBottomUp(pattern: wildcard, &found_file: varname)
:: Find file bottom up
:: return: set the FOUND_FILE variable
:FindFileBottomUp
    setlocal
    set found_file=
    set "currentDir=%CD%"

:FindFileBottomUp_upper
    call :FindFileInDir %1 "%currentDir%" found_file
    if defined found_file goto :FindFileBottomUp_exit
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
        goto :FindFileBottomUp_upper
    )

:FindFileBottomUp_exit
    endlocal & set "%2=%found_file%"
exit /b


:: function FindFileInDir(pattern: wildcard, target_directory: directory, &found_file: varname)
:: Find file in dir
:FindFileInDir
    for %%F in ("%~2\%1") do (
        set "%3=%%F"
        exit /b
    )
exit /b


:: function FindEngineByProject(project_file: path, &engine_root: varname)
:FindEngineByProject
    setlocal EnableDelayedExpansion
    :: Iterate over each line in the file
    for /f "tokens=*" %%a in ('type "%~1" ^| findstr /C:"EngineAssociation"') do (
        :: Using double quote in delims by escape, see https://ss64.com/nt/for_f.html
        for /f tokens^=3^ delims^=^" %%b in ("%%a") do (
            call :FindBuiltEngine %%b found_engine_root
            if defined found_engine_root goto :FindEngineByProject_exit
            call :FindInstalledEngine  %%b found_engine_root
        )
    )
:FindEngineByProject_exit
    endlocal & set "%2=%found_engine_root%"
exit /b


:: function FindBuiltEngine(engine_id, &path path)
:FindBuiltEngine
    setlocal
    set "key=HKEY_CURRENT_USER\Software\Epic Games\Unreal Engine\Builds"
    for /f "tokens=3*" %%a in ('reg query "%key%" /v "%1" 2^>nul ^| findstr /C:"REG_SZ"') do (
        set "found_engine_root=%%a"
        :: Replace forward slashes with backslashes
        set "found_engine_root=!found_engine_root:/=\!"
    )
    endlocal & set "%2=%found_engine_root%"
exit /b


:: function FindInstalledEngine(engine_id, &path path)
:FindInstalledEngine
    setlocal
    set "config_file=%ProgramData%\Epic\UnrealEngineLauncher\LauncherInstalled.dat"
    for /f "tokens=*" %%a in ('type "%config_file%"') do (
        for /f tokens^=1^,3^ delims^=^" %%b in ("%%a") do (
            if "%%b" == "InstallLocation" (
                set InstallLocation=%%c
            ) else if "%%b" == "ArtifactId" (
                if "%%c" == "UE_%1" goto :FindInstalledEngine_found
            )
        )
    )
    set InstallLocation=
:FindInstalledEngine_found
    endlocal & set %~2=%InstallLocation:\\=\%
exit /b
