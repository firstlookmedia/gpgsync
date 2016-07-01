# -*- mode: python -*-

block_cipher = None

# Get the version
version = open('share/version').read().strip().lstrip('v')

a = Analysis(
    ['pgpsync-osx.py'],
    pathex=['.'],
    binaries=None,
    datas=[('../share/*', 'share')],
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher)

pyz = PYZ(
    a.pure, a.zipped_data,
    cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    exclude_binaries=True,
    name='pgpsync',
    debug=False,
    strip=False,
    upx=True,
    console=False)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name='pgpsync')

app = BUNDLE(
    coll,
    name='PGP Sync.app',
    icon='install/pgpsync.icns',
    bundle_identifier='org.firstlook.pgpsync',
    info_plist={
        'LSUIElement': 'True',
        'NSHighResolutionCapable': 'True',
        'CFBundleShortVersionString': version
    })
