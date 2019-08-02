#!/bin/bash
ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )"
DIST_PATH="$ROOT/dist"
SCRIPTS_PATH="$ROOT/install/macos-packaging/scripts"

# Get the version
VERSION=$(cat share/version)
VERSION=${VERSION:1}

cd $ROOT

DIST_ROOT_PATH="$DIST_PATH/root"
DIST_APPLICATIONS_PATH="$DIST_ROOT_PATH/Applications"
APP_PATH="$DIST_APPLICATIONS_PATH/GPG Sync.app"

# Make sure the .app package exists
if [ ! -d "$DIST_PATH/GPG Sync.app" ]; then
    echo "App bundle doesn't exist yet, should be in: $DIST_PATH/GPG Sync.app"
    exit
fi

mkdir -p "$DIST_APPLICATIONS_PATH"
cp -r "$DIST_PATH/GPG Sync.app" "$APP_PATH"

SCRIPTS_PATH="$ROOT/install/macos-packaging/scripts"
COMPONENT_PLIST_PATH="$ROOT/install/macos-packaging/gpgsync-component.plist"
COMPONENT_PATH="$DIST_PATH/GPGSyncComponent.pkg"
PKG_PATH="$DIST_PATH/GPGSync-$VERSION.pkg"

if [ "$1" = "--without-codesigning" ]; then
  echo "Creating an installer without codesigning"
  pkgbuild \
    --root "$DIST_ROOT_PATH" \
    --component-plist "$COMPONENT_PLIST_PATH" \
    --scripts "$SCRIPTS_PATH" \
    "$COMPONENT_PATH"
  productbuild \
    --package "$COMPONENT_PATH" \
    "$PKG_PATH"
else
    IDENTITY_NAME_APPLICATION="Developer ID Application: FIRST LOOK PRODUCTIONS, INC."
    IDENTITY_NAME_INSTALLER="Developer ID Installer: FIRST LOOK PRODUCTIONS, INC."

    echo "Codesigning the app bundle"
    codesign --options runtime --timestamp --deep -s "$IDENTITY_NAME_APPLICATION" "$APP_PATH"

    echo "Creating a codesigned installer"
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
fi

echo "Cleaning up"
  rm -rf "$COMPONENT_PATH" "$DIST_ROOT_PATH" "$DIST_PATH/gpgsync"

  echo "All done, your installer is in: $PKG_PATH"