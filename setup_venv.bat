@echo off
python -m venv venv
call venv\Scripts\activate.bat
pip install -r requirements.txt
echo Virtual environment created and packages installed.
echo To activate: venv\Scripts\activate.bat
