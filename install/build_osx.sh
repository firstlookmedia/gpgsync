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
  echo "Codesigning is not yet implemented"
  productbuild --component "dist/GPG Sync.app" /Applications "dist/GPG Sync.pkg"
fi
