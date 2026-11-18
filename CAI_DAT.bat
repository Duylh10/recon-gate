@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Recon-Gate: cai dat (chi lam 1 lan)
where py >nul 2>nul
if %errorlevel%==0 (set PY=py -3) else (
  where python >nul 2>nul
  if %errorlevel%==0 (set PY=python) else (
    echo Chua co Python. Dang cai Python 3.12 qua winget...
    winget install -e --id Python.Python.3.12 --accept-source-agreements --accept-package-agreements
    if errorlevel 1 (
      echo Khong cai duoc tu dong. Tai Python tai https://www.python.org/downloads/ ^(tick "Add python.exe to PATH"^), roi chay lai file nay.
      pause & exit /b 1
    )
    set PY=py -3
  )
)
%PY% -m venv .venv || (echo Tao moi truong that bai. & pause & exit /b 1)
.venv\Scripts\python -m pip install --disable-pip-version-check -q -r requirements.txt || (echo Cai thu vien that bai. Kiem tra mang. & pause & exit /b 1)
echo.
echo Cai xong. Bam dup CHAY_THU.bat de chay bo du lieu mau.
pause
