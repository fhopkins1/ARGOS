@echo off
setlocal
set "ARGOS_ROOT=%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%ARGOS_ROOT%Scripts\launch_argos_control_panel.ps1"
endlocal
