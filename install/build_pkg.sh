#!/bin/bash
ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )"
BUILD_PATH="$ROOT/build"
DIST_PATH="$ROOT/dist"
SCRIPTS_PATH="$ROOT/install/macos-packaging/scripts"

# Get the version
VERSION=$(cat share/version)
VERSION=${VERSION:1}

cd $ROOT

echo "Deleting older builds"
rm -rf $BUILD_PATH $DIST_PATH &>/dev/null 2>&1

echo "Building the app bundle"
pyinstaller install/pyinstaller.spec --clean

if [ "$1" = "--release" ]; then
  APP_PATH="$DIST_PATH/GPG Sync.app"
  PKG_PATH="$DIST_PATH/GPGSync-$VERSION.pkg"
  IDENTITY_NAME_APPLICATION="Developer ID Application: FIRST LOOK PRODUCTIONS, INC."
  IDENTITY_NAME_INSTALLER="Developer ID Installer: FIRST LOOK PRODUCTIONS, INC."

  echo "Codesigning the app bundle"
  codesign --deep -s "$IDENTITY_NAME_APPLICATION" "$APP_PATH"

  echo "Creating an installer"
  productbuild --sign "$IDENTITY_NAME_INSTALLER" --scripts "$SCRIPTS_PATH" --component "$APP_PATH" /Applications "$PKG_PATH"

  echo "Cleaning up"
  rm -rf "$APP_PATH"

  echo "All done, your installer is in: $PKG_PATH"
fi

if [ "$1" = "--release-without-codesigning" ]; then
  APP_PATH="$DIST_PATH/GPG Sync.app"
  PKG_PATH="$DIST_PATH/GPGSync-$VERSION.pkg"

  echo "Creating an installer"
  productbuild --scripts "$SCRIPTS_PATH" --component "$APP_PATH" /Applications "$PKG_PATH"

  echo "Cleaning up"
  rm -rf "$APP_PATH"

  echo "All done, your installer is in: $PKG_PATH"
fi
