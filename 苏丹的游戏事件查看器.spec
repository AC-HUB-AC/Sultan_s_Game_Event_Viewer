# -*- mode: python ; coding: utf-8 -*-
import os
import PyInstaller.config

# 输出 exe 到 spec 文件所在目录的上级（即主文件夹），build 缓存留在 code/ 下
PyInstaller.config.CONF['distpath'] = os.path.join(SPECPATH, '..')
PyInstaller.config.CONF['workpath'] = os.path.join(SPECPATH, 'build')

a = Analysis(
    [os.path.join(SPECPATH, '苏丹的游戏事件查看器.py')],
    pathex=[SPECPATH],
    binaries=[],
    datas=[(os.path.join(SPECPATH, 'rite'), 'rite')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='苏丹的游戏事件查看器(GitHub：AC-HUB-AC)',
    debug=False,
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
    version=os.path.join(SPECPATH, 'version.txt'),
    icon=[os.path.join(SPECPATH, '图标.ico')],
)
