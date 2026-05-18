# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for Restaurant POS Windows .exe
# Build: pyinstaller restaurant_pos.spec  (run from apps/restaurant_pos/)

import os
from PyInstaller.utils.hooks import collect_all

apps_root = os.path.abspath(os.path.join(SPECPATH, '..'))

# Collect all PyQt6 binaries/data so Qt plugins are bundled correctly
qt_datas, qt_binaries, qt_hiddenimports = collect_all('PyQt6')

a = Analysis(
    [os.path.join(SPECPATH, 'main.py')],
    pathex=[SPECPATH, apps_root],
    binaries=qt_binaries,
    datas=qt_datas,
    hiddenimports=qt_hiddenimports + [
        'shared.frappe_client',
        'shared.config',
        'shared.login_window',
        'ui.table_grid',
        'ui.order_panel',
        'requests',
        'urllib3',
        'charset_normalizer',
        'certifi',
        'idna',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['kivy', 'tkinter', 'matplotlib', 'numpy'],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='RestaurantPOS',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,            # No console window (GUI app)
    disable_windowed_traceback=False,
    icon=None,                # Replace with 'restaurant_pos.ico' if you have one
)
