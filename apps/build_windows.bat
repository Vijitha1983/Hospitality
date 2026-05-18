@echo off
:: Build both Windows .exe files using PyInstaller
:: Run from the apps\ directory

setlocal

set APPS_DIR=%~dp0

echo ============================================================
echo  Building HotelDesk.exe
echo ============================================================
cd /d "%APPS_DIR%hotel_desk"
pyinstaller hotel_desk.spec --clean --noconfirm
if errorlevel 1 (
    echo ERROR: HotelDesk build failed.
    pause
    exit /b 1
)
echo HotelDesk.exe built at: %APPS_DIR%hotel_desk\dist\HotelDesk.exe

echo.
echo ============================================================
echo  Building RestaurantPOS.exe
echo ============================================================
cd /d "%APPS_DIR%restaurant_pos"
pyinstaller restaurant_pos.spec --clean --noconfirm
if errorlevel 1 (
    echo ERROR: RestaurantPOS build failed.
    pause
    exit /b 1
)
echo RestaurantPOS.exe built at: %APPS_DIR%restaurant_pos\dist\RestaurantPOS.exe

echo.
echo ============================================================
echo  All builds complete.
echo ============================================================
pause
