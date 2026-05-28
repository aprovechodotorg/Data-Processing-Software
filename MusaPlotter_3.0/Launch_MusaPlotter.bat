@echo off
echo Starting MusaPlotter v3.0...
cd /d "%~dp0"

IF NOT EXIST "venv\Scripts\activate.bat" (
    echo No virtual environment found. Creating 'venv'...
    python -m venv venv
)

echo Activating virtual environment...
call "venv\Scripts\activate.bat"

echo Ensuring dependencies are installed (this is fast if already installed)...
pip install -r requirements.txt

echo Launching application...
python MusaPlotter_3.0.py

IF %ERRORLEVEL% NEQ 0 (
    echo.
    echo MusaPlotter closed with an error. Please review the output above.
    pause
)
