Rem Batch to run data_validate FROM `canoa`
@echo Off
REM 🖋️ Authored by mgd — Annotated for the curious, ignored by the hurried.
Rem cspell:ignore setlocal endlocal popd pushd venv py_args errorlevel enabledelayedexpansion quotes findstr
Rem cspell:ignore Desenv barometro
Rem mgd 2024-05-27 v1
Rem mgd 2024-07-27 v2 (param1: data_validate folder)
Rem mgd 2025-02-04 v3
Rem     %* does not "comply" with `shift`: call python main.py %*
Rem     1) save params in py_args, 2) setlocal 3) pushd/popd
Rem mgd 2025-02-05 v4 fix 2 bugs, (27: "py_args=!py_args! %~1" => "py_args=!py_args! "%~1"") & DEBUG
Rem mgd 2025-10-03 v4.1 echo to stderr Eho Ups! >&2
Rem mgd 2025-10-04 v4.2 Four Copilot recommendations

Rem --------------------------------------------
Rem Example:
Rem cd F:\Desenv\Git\AdaptaBrasil\data_tunnel
Rem run_validate.bat F:\Desenv\Git\AdaptaBrasil\data_validate --input_folder F:\Desenv\Git\AdaptaBrasil\data_tunnel\0021a\data --output_folder F:\Desenv\Git\AdaptaBrasil\data_tunnel\0021a\report --user "miguel" --file "impactos_0502.zip" --sector "barometro/Infraestrutura Portuária (fake)" --no-spellchecker

Rem --------------------------------------------
Rem /!\ Keep synced with run_validate.sh
Rem --------------------------------------------
Rem Set DEBUG to T or leave empty for no debug
set DEBUG=


Rem --------------------------------------------
echo Starting run_validate.bat v 2025-10-03 v4.2
if not "%DEBUG%"=="" echo Debug mode is == ON ==

Rem --------------------------------------------
Rem Go to data_validate folder [param 1]
pushd "%~1"

Rem --------------------------------------------
Rem Save params from 2 to n in py_args (param 1 is this bat folder)
if not "%DEBUG%"=="" echo looping:
set "py_args="
setlocal enabledelayedexpansion
:add_args
	shift
	if not "%DEBUG%"=="" echo arg[%~1]
	if "%~1"=="" goto args_ready
	Rem set quotes (removed by who knows who) if not is a flag (--)
	set "arg="%~1""
	echo %~1 | findstr /B /C:"--" >nul && set "arg=%~1"
	set "py_args=!py_args! %arg%"
	goto add_args
:args_ready
endlocal & set "py_args=%py_args%"
if not "%DEBUG%"=="" echo %py_args%

Rem --------------------------------------------
where python >nul 2>&1 || (echo Python not found in PATH. >&2 & exit /b 3)

Rem --------------------------------------------
if exist .venv\Scripts\activate.bat (
	echo Activating data_validate environment in Windows...
	call .venv\Scripts\activate.bat
) else (
Rem Delivers the message (to stderr) and exits with a non-zero code in one breath.
	echo Virtual environment not found. >&2 & exit /b 1
)

Rem --------------------------------------------
if not exist "main.py" (
	echo main.py not found in the current directory & exit /b 2
)

Rem --------------------------------------------
echo Running data_validate...
call python main.py %py_args%
set "exit_code=%ERRORLEVEL%"

Rem --------------------------------------------
echo Deactivating data_validate environment...
if exist .venv\Scripts\deactivate.bat (
	call .venv\Scripts\deactivate.bat
) else (
	echo Virtual environment deactivation script not found
)

Rem --------------------------------------------
Rem Return to initial folder
popd
echo Exiting to Canoa with code [%exit_code%].
exit /b %exit_code%
Rem eof