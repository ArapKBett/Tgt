@echo off
cd /d "%~dp0"
call venv\Scripts\activate
python telegram_bot.py
pause
