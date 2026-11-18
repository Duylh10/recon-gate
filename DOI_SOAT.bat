@echo off
chcp 65001 >nul
rem Keo tha 2 file Excel/CSV vao file nay (giu Ctrl de chon 2 file).
set "A=%~1"
set "B=%~2"
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (echo Chua cai dat. Bam dup CAI_DAT.bat truoc. & pause & exit /b 1)
if "%A%"=="" (
  echo Keo tha 2 file vao DOI_SOAT.bat, hoac nhap duong dan:
  set /p "A=File ben A: "
  set /p "B=File ben B: "
)
if "%B%"=="" (set /p "B=File ben B: ")
.venv\Scripts\python -m recon_gate "%A%" "%B%"
pause
