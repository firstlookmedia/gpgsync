#!/bin/bash
ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )"
BUILD_PATH="$ROOT/build"
DIST_PATH="$ROOT/dist"

cd $ROOT

# Delete old build
echo Deleting dist folder
rm -rf $BUILD_PATH $DIST_PATH &>/dev/null 2>&1

# Get the version
VERSION=$(cat share/version | cut -d"v" -f2)

# Build the .app
echo Building GPG Sync.app
pyinstaller install/pyinstaller.spec --clean

if [ "$1" = "--release" ]; then
  APP_PATH="$DIST_PATH/GPG Sync.app"
  PKG_PATH="$DIST_PATH/GPGSync.pkg"
  PRODUCT_PATH="$DIST_PATH/GPGSync-$VERSION.pkg"
  IDENTITY_NAME_APPLICATION="Developer ID Application: FIRST LOOK PRODUCTIONS, INC."
  IDENTITY_NAME_INSTALLER="Developer ID Installer: FIRST LOOK PRODUCTIONS, INC."

  echo "Codesigning the app bundle"
  codesign --deep -s "$IDENTITY_NAME_APPLICATION" "$APP_PATH"

  echo "Creating an installer"
  pkgbuild --sign "$IDENTITY_NAME_INSTALLER" --root "$DIST_PATH" --component-plist install/macos-packaging/gpgsync-component.plist --scripts install/macos-packaging/scripts "$PKG_PATH"
  productbuild --sign "$IDENTITY_NAME_INSTALLER" --package "$PKG_PATH" "$PRODUCT_PATH"

  echo "Cleaning up"
  rm -rf "$APP_PATH" "$PKG_PATH"

  echo "All done, your installer is in: $PRODUCT_PATH"
fi
