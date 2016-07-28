#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )"
cd $DIR

VERSION=`cat version`

# clean up from last build
rm -r deb_dist >/dev/null 2>&1

# build binary package
python3 setup.py --command-packages=stdeb.command bdist_deb

# return install instructions if build succeeds
echo ""
if [[ $? -eq 0 ]]; then
    echo "To install, run:"
    echo "sudo dpkg -i deb_dist/gpgsync_*.deb"
else
    echo "GPG Sync failed to build!"
fi
