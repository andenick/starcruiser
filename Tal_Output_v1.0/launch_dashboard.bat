@echo off
echo =========================================
echo StarCruiser Dashboard Launcher
echo =========================================
echo.
echo Starting dashboard...
cd /d "%~dp0Dashboard"
Rscript -e "shiny::runApp(launch.browser=TRUE)"
pause
