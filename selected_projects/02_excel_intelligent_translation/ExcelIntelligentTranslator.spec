# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

import os
import sys
import glob

# 动态寻找 aeosa 目录（因为在虚拟环境中通过 .pth 引用）
aeosa_path = ''
for path in sys.path:
    if path.endswith('site-packages'):
        possible_aeosa = os.path.join(path, 'aeosa')
        if os.path.exists(possible_aeosa):
            aeosa_path = possible_aeosa
            break

if not aeosa_path:
    # 备用方案
    site_packages = glob.glob('venv/lib/python*/site-packages')
    if site_packages:
        aeosa_path = os.path.join(site_packages[0], 'aeosa')

pathex_list = ['src']
if aeosa_path and os.path.exists(aeosa_path):
    pathex_list.append(aeosa_path)

datas = []
if os.path.exists('assets'):
    datas.append(('assets', 'assets'))

a = Analysis(
    ['app.py'],
    pathex=pathex_list,
    binaries=[],
    datas=datas,
    hiddenimports=['tkinter', '_tkinter', 'appscript', 'aem', 'osax', 'psutil', 'xlwings'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# 确保过滤掉 local_dict_mapping.txt
a.datas = [d for d in a.datas if 'local_dict_mapping.txt' not in d[0] and 'local_dict_mapping.txt' not in d[1]]

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ExcelIntelligentTranslator',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ExcelIntelligentTranslator',
)

app = BUNDLE(
    coll,
    name='ExcelIntelligentTranslator.app',
    icon=None,
    bundle_identifier=None,
    info_plist={
        'NSAppleEventsUsageDescription': '此应用需要控制 Microsoft Excel 进行后台翻译读写'
    }
)
