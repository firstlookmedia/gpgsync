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
  DIST_ROOT_PATH="$DIST_PATH/root"
  DIST_APPLICATIONS_PATH="$DIST_ROOT_PATH/Applications"
  APP_PATH="$DIST_APPLICATIONS_PATH/GPG Sync.app"

  mkdir -p "$DIST_APPLICATIONS_PATH"
  mv "$DIST_PATH/GPG Sync.app" "$APP_PATH"

  SCRIPTS_PATH="$ROOT/install/macos-packaging/scripts"
  COMPONENT_PLIST_PATH="$ROOT/install/macos-packaging/gpgsync-component.plist"
  COMPONENT_PATH="$DIST_PATH/GPGSyncComponent.pkg"
  PKG_PATH="$DIST_PATH/GPGSync-$VERSION.pkg"

  IDENTITY_NAME_APPLICATION="Developer ID Application: FIRST LOOK PRODUCTIONS, INC."
  IDENTITY_NAME_INSTALLER="Developer ID Installer: FIRST LOOK PRODUCTIONS, INC."

  echo "Codesigning the app bundle"
  codesign --deep -s "$IDENTITY_NAME_APPLICATION" "$APP_PATH"

  echo "Creating an installer"
  pkgbuild \
    --sign "$IDENTITY_NAME_INSTALLER" \
    --root "$DIST_ROOT_PATH" \
    --component-plist "$COMPONENT_PLIST_PATH" \
    --scripts "$SCRIPTS_PATH" \
    "$COMPONENT_PATH"
  productbuild \
    --sign "$IDENTITY_NAME_INSTALLER" \
    --package "$COMPONENT_PATH" \
    "$PKG_PATH"

  echo "Cleaning up"
  rm -rf "$COMPONENT_PATH" "$DIST_ROOT_PATH" "$DIST_PATH/gpgsync"

  echo "All done, your installer is in: $PKG_PATH"
fi

if [ "$1" = "--release-without-codesigning" ]; then
  DIST_ROOT_PATH="$DIST_PATH/root"
  DIST_APPLICATIONS_PATH="$DIST_ROOT_PATH/Applications"
  APP_PATH="$DIST_APPLICATIONS_PATH/GPG Sync.app"

  mkdir -p "$DIST_APPLICATIONS_PATH"
  mv "$DIST_PATH/GPG Sync.app" "$APP_PATH"

  SCRIPTS_PATH="$ROOT/install/macos-packaging/scripts"
  COMPONENT_PLIST_PATH="$ROOT/install/macos-packaging/gpgsync-component.plist"
  COMPONENT_PATH="$DIST_PATH/GPGSyncComponent.pkg"
  PKG_PATH="$DIST_PATH/GPGSync-$VERSION.pkg"

  echo "Creating an installer"
  pkgbuild \
    --root "$DIST_ROOT_PATH" \
    --component-plist "$COMPONENT_PLIST_PATH" \
    --scripts "$SCRIPTS_PATH" \
    "$COMPONENT_PATH"
  productbuild \
    --package "$COMPONENT_PATH" \
    "$PKG_PATH"

  echo "Cleaning up"
  rm -rf "$COMPONENT_PATH" "$DIST_ROOT_PATH" "$DIST_PATH/gpgsync"

  echo "All done, your installer is in: $PKG_PATH"
fi
