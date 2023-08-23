@echo off
:: Copyright 2023 The Chromium Authors
:: Use of this source code is governed by a BSD-style license that can be
:: found in the LICENSE file.
setlocal

:: Ensure that "depot_tools" is somewhere in PATH so this tool can be used
:: standalone, but allow other PATH manipulations to take priority.
set PATH=%PATH%;%~dp0


set scriptdir=%~dp0

:: Defer control.
:: Add double quotes to the arguments to preserve the special '^' character.
:: See autosiso.py for more information.
%scriptdir%python-bin\python3.bat "%~dp0\autosiso.py" "%*"
