#!/bin/bash
ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )"
cd $ROOT

# Deleting dist
echo Deleting dist folder
rm -rf $ROOT/dist &>/dev/null 2>&1

# Build the .app
echo Building .app
pyinstaller install/pyinstaller-osx.spec --clean

if [ "$1" = "--release" ]; then
  APP_PATH="dist/GPG Sync.app"
  PKG_PATH="dist/GPGSync.pkg"
  IDENTITY_NAME_APPLICATION="Developer ID Application: FIRST LOOK PRODUCTIONS, INC."
  IDENTITY_NAME_INSTALLER="Developer ID Installer: FIRST LOOK PRODUCTIONS, INC."

  echo "Codesigning the app bundle"
  codesign --deep -s "$IDENTITY_NAME_APPLICATION" "$APP_PATH"

  echo "Creating an installer"
  productbuild --sign "$IDENTITY_NAME_INSTALLER" --component "$APP_PATH" /Applications "$PKG_PATH"

  echo "Cleaning up"
  rm -rf dist/gpgsync "$APP_PATH"

  echo "All done, your installer is in: $PKG_PATH"
fi
