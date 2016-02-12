# Build instructions

## Mac OS X

Install Xcode from the Mac App Store. Once it's installed, run it for the first time to set it up.

Install the [latest Python 3.x from python.org](https://www.python.org/downloads/). If you use the built-in version of python that comes with OS X, your .app might not run on other people's computers.

Download and install Qt5 from https://www.qt.io/download-open-source/. I downloaded `qt-unified-mac-x64-2.0.2-2-online.dmg`. There's no need to login to a Qt account during installation. Make sure you install the latest Qt 5.x for clang.

Download the source code for [SIP](http://www.riverbankcomputing.co.uk/software/sip/download) and [PyQt](http://www.riverbankcomputing.co.uk/software/pyqt/download5). I downloaded `sip-4.17.tar.gz` and `PyQt-gpl-5.5.1.tar.gz`.

Now extract the source code:

```sh
tar xvf sip-4.17.tar.gz
tar xvf PyQt-gpl-5.5.1.tar.gz
```

Compile SIP:

```sh
cd sip-4.17
python3 configure.py --arch x86_64
make
sudo make install
sudo make clean
```

Compile PyQt:

```sh
cd ../PyQt-gpl-5.5.1
python3 configure.py --qmake ~/Qt/5.5/clang_64/bin/qmake --sip /Library/Frameworks/Python.framework/Versions/3.5/bin/sip --disable=QtPositioning
make
sudo make install
sudo make clean
```

Finally, install some dependencies using pip3: `sudo pip3 install py2app pycurl`

Now you're ready to build the actual app. Go to the `pgpsync` folder before and run this to build the app:

```sh
install/build_osx.sh
```

Now you should have `dist/PGP Sync.app`.

To codesign and build a .pkg for distribution:

```sh
install/build_osx.sh --sign
```

Now you should have `dist/PGP Sync.pkg`. NOTE: This isn't implemented yet.

## Linux distributions

*Debian / Ubuntu / Mint*

Install dependencies:

```sh
sudo apt-get install python3-pyqt5 python3-pycurl python3-nose python3-stdeb
```

Make and install a .deb:

```sh
./install/build_deb.sh
sudo dpkg -i deb_dist/pgpsync_*.deb
```

*Arch*

```sh
sudo pacman -S python-pyqt5 python-pycurl python-nose
```

## Run the tests

From the `pgpsync` folder run:

```sh
nosetests
```

Note that one of the tests will fail if you don't have SOCKS5 proxy server listening on port 9050 (e.g. Tor installed).
