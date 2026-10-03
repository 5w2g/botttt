@echo off
:loop
echo [%date% %time%] Demarrage du bot...
py bot.py
echo [%date% %time%] Bot arrete. Redemarrage dans 5s...
timeout /t 5 /nobreak >nul
goto loop