@echo off
title HoneyClean - EXE Builder (onedir)
color 0A
cd /d "%~dp0"

echo.
echo  [1/3] Installiere Abhaengigkeiten...
py -m pip install pyinstaller tkinterdnd2 -q

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
  --hidden-import multiprocessing ^
  --collect-all rembg ^
  --collect-all tkinterdnd2 ^
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
