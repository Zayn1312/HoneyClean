@echo off
title HoneyClean - EXE Builder (onedir)
color 0A
cd /d "%~dp0"

echo.
echo  [1/3] Installiere Abhaengigkeiten...
py -m pip install pyinstaller tkinterdnd2 customtkinter -q

REM Find customtkinter package path for --add-data
for /f "delims=" %%i in ('py -c "import customtkinter; import os; print(os.path.dirname(customtkinter.__file__))"') do set CTK_PATH=%%i

echo.
echo  [2/3] Baue HoneyClean.exe (onedir + windowed)...
py -m PyInstaller ^
  --onedir ^
  --windowed ^
  --name "HoneyClean" ^
  --hidden-import rembg ^
  --hidden-import rembg.sessions ^
  --hidden-import PIL ^
  --hidden-import PIL._tkinter_finder ^
  --hidden-import onnxruntime ^
  --hidden-import pooch ^
  --hidden-import scipy ^
  --hidden-import skimage ^
  --hidden-import numpy ^
  --hidden-import tkinter ^
  --hidden-import tkinterdnd2 ^
  --hidden-import customtkinter ^
  --hidden-import multiprocessing ^
  --hidden-import zipfile ^
  --hidden-import pymatting ^
  --collect-all rembg ^
  --collect-all tkinterdnd2 ^
  --collect-all customtkinter ^
  --add-data "%CTK_PATH%;customtkinter" ^
  --clean ^
  --noconfirm ^
  HoneyClean.py

echo.
if exist "dist\HoneyClean\HoneyClean.exe" (
    echo  FERTIG: dist\HoneyClean\HoneyClean.exe
    explorer dist\HoneyClean
) else (
    echo  FEHLER: EXE nicht erstellt.
)
pause
