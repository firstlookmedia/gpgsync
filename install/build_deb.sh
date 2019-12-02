#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )"
cd $DIR

VERSION=`cat share/version`

# clean up from last build
rm -r deb_dist >/dev/null 2>&1

# build source package
python3 setup.py --command-packages=stdeb.command sdist_dsc

# build binary package
python3 setup.py --command-packages=stdeb.command bdist_deb

# return install instructions if build succeeds
if [[ $? -eq 0 ]]; then
    echo ""
    echo "To install, run:"
    echo "sudo dpkg -i deb_dist/gpgsync_*.deb"
else
    echo ""
    echo "GPG Sync failed to build!"
fi
