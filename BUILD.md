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
sudo pip3 install pyinstaller requests requests[socks]
```

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
sudo apt-get install python3-pyqt5 python3-nose python3-stdeb python3-requests python3-socks gnupg2
```

Make and install a .deb:

```sh
./install/build_deb.sh
sudo dpkg -i deb_dist/pgpsync_*.deb
```

## Run the tests

From the `pgpsync` folder run:

```sh
nosetests
```

Note that one of the tests will fail if you don't have SOCKS5 proxy server listening on port 9050 (e.g. Tor installed).
