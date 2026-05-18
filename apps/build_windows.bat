@echo off
:: Build both Windows .exe files and Windows installers
:: Output: apps\release\HotelDesk.exe, RestaurantPOS.exe
::         apps\release\HotelDesk_Setup.exe, RestaurantPOS_Setup.exe
:: Run from the apps\ directory

setlocal

set APPS_DIR=%~dp0
set RELEASE_DIR=%APPS_DIR%release
set ISCC=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe

echo ============================================================
echo  Output folder: %RELEASE_DIR%
echo ============================================================

:: ── Build HotelDesk.exe ─────────────────────────────────────────────────────

echo.
echo ============================================================
echo  Building HotelDesk.exe
echo ============================================================
cd /d "%APPS_DIR%hotel_desk"
python -m PyInstaller hotel_desk.spec --clean --noconfirm --distpath "%RELEASE_DIR%"
if errorlevel 1 (
    echo ERROR: HotelDesk build failed.
    pause
    exit /b 1
)
echo HotelDesk.exe  ->  %RELEASE_DIR%\HotelDesk.exe

:: ── Build RestaurantPOS.exe ─────────────────────────────────────────────────

echo.
echo ============================================================
echo  Building RestaurantPOS.exe
echo ============================================================
cd /d "%APPS_DIR%restaurant_pos"
python -m PyInstaller restaurant_pos.spec --clean --noconfirm --distpath "%RELEASE_DIR%"
if errorlevel 1 (
    echo ERROR: RestaurantPOS build failed.
    pause
    exit /b 1
)
echo RestaurantPOS.exe  ->  %RELEASE_DIR%\RestaurantPOS.exe

:: ── Build Windows Installers ────────────────────────────────────────────────

if not exist "%ISCC%" (
    echo.
    echo Inno Setup not found — skipping installer build.
    echo Install from: https://jrsoftware.org/isinfo.php
    goto :done
)

echo.
echo ============================================================
echo  Building HotelDesk_Setup.exe  (Windows installer)
echo ============================================================
cd /d "%APPS_DIR%hotel_desk"
"%ISCC%" hotel_desk.iss
if errorlevel 1 ( echo ERROR: HotelDesk installer failed. & pause & exit /b 1 )
echo HotelDesk_Setup.exe  ->  %RELEASE_DIR%\HotelDesk_Setup.exe

echo.
echo ============================================================
echo  Building RestaurantPOS_Setup.exe  (Windows installer)
echo ============================================================
cd /d "%APPS_DIR%restaurant_pos"
"%ISCC%" restaurant_pos.iss
if errorlevel 1 ( echo ERROR: RestaurantPOS installer failed. & pause & exit /b 1 )
echo RestaurantPOS_Setup.exe  ->  %RELEASE_DIR%\RestaurantPOS_Setup.exe

:done
echo.
echo ============================================================
echo  All builds complete.  Files in: %RELEASE_DIR%
echo ============================================================
pause
