@echo off
setlocal EnableExtensions

REM Usage: generate myfile.mmd
if "%~1"=="" (
  echo Usage: %~nx0 ^<file.mmd^>
  exit /b 1
)

set "IN=%~1"

REM Ensure extension is .mmd
if /I not "%~x1"==".mmd" (
  echo Error: input must be a .mmd file
  exit /b 1
)

REM Output SVG next to input, same base name
set "OUT=%~dpn1.svg"

REM Parsed output produced by transform_svg.py
set "PARSED=%~dp1parsed\%~n1.svg"

REM Destination folder
set "DEST=C:\sade-prototype\documentation\workflow\svg"
set "DESTFILE=%DEST%\%~n1.svg"

echo [1/3] Rendering: "%IN%" -> "%OUT%"
call mmdc -i "%IN%" -o "%OUT%"
if errorlevel 1 (
  echo Error: mmdc failed.
  exit /b 1
)

echo [2/3] Transforming SVG: "%OUT%"
call python ".\transform_svg.py" "%OUT%" --svg-width 700 --strip-max-width
if errorlevel 1 (
  echo Error: transform_svg.py failed.
  exit /b 1
)

echo [3/3] Copying parsed SVG to: "%DESTFILE%"
if not exist "%DEST%" (
  mkdir "%DEST%"
)
copy /Y "%PARSED%" "%DESTFILE%" >nul
if errorlevel 1 (
  echo Error: copy failed. Is "%PARSED%" present?
  exit /b 1
)

echo Done.
exit /b 0

