# Build instructions

## Mac OS X

Install Xcode from the Mac App Store. Once it's installed, run it for the first time to set it up.

If you don't already have it installed, install [Homebrew](http://brew.sh/).

Install some dependencies using Homebrew:

```sh
brew install python3 pyqt5 qt5
```

Install some dependencies using pip3:

```sh
sudo pip3 install requests requests[socks] packaging
```

Install the latest development version of cx_Freeze:

* Download a [snapshot](https://bitbucket.org/anthony_tuininga/cx_freeze/downloads) of the latest development version of cx_Freeze, extract it, and cd into the folder you extracted it to
* Build the package: `python3 setup.py bdist_wheel`
* Install it with pip: `sudo pip3 install dist/cx_Freeze-5.0-cp35-cp35m-macosx_10_11_x86_64.whl`

Now you're ready to build the actual app. Go to the `gpgsync` folder before and run this to build the app:

```sh
install/build_osx.sh
```

Now you should have `dist/GPG Sync.app`.

To codesign and build a .pkg for distribution:

```sh
install/build_osx.sh --sign
```

Now you should have `dist/GPG Sync.pkg`. NOTE: This isn't implemented yet.

## Linux distributions

*Debian / Ubuntu / Mint*

Install dependencies:

```sh
sudo apt-get install python3-pyqt5 python3-nose python3-stdeb python3-requests python3-socks python3-packaging gnupg2
```

Make and install a .deb:

```sh
./install/build_deb.sh
sudo dpkg -i deb_dist/gpgsync_*.deb
```

## Run the tests

From the `gpgsync` folder run:

```sh
nosetests
```

Note that one of the tests will fail if you don't have SOCKS5 proxy server listening on port 9050 (e.g. Tor installed).
