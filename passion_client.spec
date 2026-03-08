# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['passion_client.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'numpy',
        'numpy.core._multiarray_umath',
        'pymem',
        'psutil',
        'wmi',
        'browser_cookie3',
        'Cryptodome.Cipher.AES',
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
        'requests',
        'win32crypt',
        'ctypes',
        'ctypes.wintypes',
        'sqlite3',
        'pickle',
    ],
    # Minimal excludes for debugging
    excludes=[
        'tkinter',
        'test',
        'unittest',
        'pdb',
        'doctest',
        'pip',
        'setuptools',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    noarchive=False,
)

import os
import numpy
numpy_path = os.path.dirname(numpy.__file__)
a.binaries += [(
    os.path.join('numpy', 'core', '_multiarray_umath.pyd'),
    os.path.join(numpy_path, 'core', '_multiarray_umath.pyd'),
    'BINARY'
)]

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='PassionClient',
    debug=True,  # Enable debug mode temporarily
    bootloader_ignore_signals=False,
    strip=True,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico'
)