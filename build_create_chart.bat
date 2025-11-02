@echo off
echo Installing required packages...
pip install -r requirements.txt

echo Building executable...
pyinstaller create_chart.spec

echo Build complete! Executable is in the dist folder.
pause 