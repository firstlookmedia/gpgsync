# -*- mode: python -*-
import platform
p = platform.system()

# Get the version
version = open('share/version').read().strip().lstrip('v')

a = Analysis(
    ['scripts/gpgsync-pyinstaller'],
    pathex=['.'],
    binaries=None,
    datas=[('../share/*', 'share')],
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None)

pyz = PYZ(
    a.pure, a.zipped_data,
    cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    exclude_binaries=True,
    name='gpgsync',
    debug=False,
    strip=False,
    upx=True,
    console=True)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name='gpgsync')

if p == 'Darwin':
  app = BUNDLE(
      coll,
      name='GPG Sync.app',
      icon='install/gpgsync.icns',
      bundle_identifier='org.firstlook.gpgsync',
      info_plist={
          'LSUIElement': True,
          'NSHighResolutionCapable': True,
          'CFBundleShortVersionString': version
      })
