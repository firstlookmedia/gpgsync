#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )"
cd $DIR

VERSION=`cat share/version`
VERSION=${VERSION:1}

# clean up from last build
rm -r build dist >/dev/null 2>&1

# build binary package
python3 setup.py bdist_rpm --requires="python3-qt5, python3-requests, python3-packaging, python3-dateutil, gnupg2"

# return install instructions if build succeeds
if [[ $? -eq 0 ]]; then
    echo ""
    echo "To install, run:"
    echo "sudo dnf install dist/gpgsync-$VERSION-1.noarch.rpm"
else
    echo ""
    echo "GPG Sync failed to build!"
fi
