@echo off
rem Double-click to start Minku. No console window: quit from the Minku icon in the tray.
rem Problems are written to logs\minku.log. To see output live, run: .venv\Scripts\python.exe main.py
cd /d "%~dp0"
start "" ".venv\Scripts\pythonw.exe" main.py
