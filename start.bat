chcp 65001 >nul
cd /d "%~dp0"
py app\main.py > run.log 2>&1
if errorlevel 1 (
    echo Error! See run.log
    type run.log
    pause
)
