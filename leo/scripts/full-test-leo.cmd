@echo off
cls
cd %~dp0..\..

echo full-test-leo

call reindent-leo.cmd
call beautify-leo.cmd
call test-leo.cmd

rem echo.
call ruff-leo.cmd
call mypy-leo.cmd
rem call flake8-leo.cmd
rem call pylint-leo.cmd
rem echo.
echo Done!
