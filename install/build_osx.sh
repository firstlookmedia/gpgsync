#!/bin/bash
ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )"
cd $ROOT

# Deleting dist
echo Deleting dist folder
rm -rf $ROOT/dist &>/dev/null 2>&1

# Build the .app
echo Building .app
python3 setup.py py2app

if [ "$1" = "--sign" ]; then
  echo "Codesigning is not yet implemented"
fi
