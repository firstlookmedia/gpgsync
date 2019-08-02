#!/bin/bash
ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )"
BUILD_PATH="$ROOT/build"
DIST_PATH="$ROOT/dist"

# Get the version
VERSION=$(cat share/version)
VERSION=${VERSION:1}

cd $ROOT

echo "Deleting older builds"
rm -rf $BUILD_PATH $DIST_PATH &>/dev/null 2>&1

echo "Building the app bundle"
pyinstaller install/pyinstaller.spec --clean