@echo off
cd /d "%~dp0"

start "" cmd /k "bin\neo4j-admin server console"

:waitloop
timeout /t 2 >nul
curl -s http://localhost:7474/ >nul
if errorlevel 1 goto waitloop

start http://localhost:7474/