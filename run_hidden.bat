@echo off
:loop
echo [%date% %time%] Demarrage du bot... >> "%~dp0bot.log"
cd /d "%~dp0"
py bot.py >> "%~dp0bot.log" 2>&1
echo [%date% %time%] Bot arrete. Redemarrage dans 5s... >> "%~dp0bot.log"
timeout /t 5 /nobreak >nul
goto loop