@echo off
:: Build both Windows .exe files using PyInstaller
:: Output: apps\release\HotelDesk.exe and apps\release\RestaurantPOS.exe
:: Run from the apps\ directory

setlocal

set APPS_DIR=%~dp0
set RELEASE_DIR=%APPS_DIR%release

echo ============================================================
echo  Output folder: %RELEASE_DIR%
echo ============================================================

echo.
echo ============================================================
echo  Building HotelDesk.exe
echo ============================================================
cd /d "%APPS_DIR%hotel_desk"
pyinstaller hotel_desk.spec --clean --noconfirm --distpath "%RELEASE_DIR%"
if errorlevel 1 (
    echo ERROR: HotelDesk build failed.
    pause
    exit /b 1
)
echo HotelDesk.exe  ->  %RELEASE_DIR%\HotelDesk.exe

echo.
echo ============================================================
echo  Building RestaurantPOS.exe
echo ============================================================
cd /d "%APPS_DIR%restaurant_pos"
pyinstaller restaurant_pos.spec --clean --noconfirm --distpath "%RELEASE_DIR%"
if errorlevel 1 (
    echo ERROR: RestaurantPOS build failed.
    pause
    exit /b 1
)
echo RestaurantPOS.exe  ->  %RELEASE_DIR%\RestaurantPOS.exe

echo.
echo ============================================================
echo  All builds complete.  Files in: %RELEASE_DIR%
echo ============================================================
pause
