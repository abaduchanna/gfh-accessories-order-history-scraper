# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Gfh Accessories Order History Scraper
Developed by Abad Umair Channa © 2026

Build command: pyinstaller Accessories_order_history_scraper.spec
"""

block_cipher = None

a = Analysis(
    ['Accessories_order_history_scraper.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'tkinter',
        'selenium',
        'selenium.webdriver',
        'selenium.webdriver.chrome',
        'selenium.webdriver.edge',
        'pyautogui',
        'openpyxl',
        'pyperclip',
        'requests',
        'theme_manager',
        'PIL',
        'pandas',
        'gspread',
        'oauth2client',
        'pywin32',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludedimports=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Accessories_order_history_scraper',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
