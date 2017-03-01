# Build instructions

## Mac OS X

Install Xcode from the Mac App Store. Once it's installed, run it for the first time to set it up.

Install Python 3.5.3 from https://www.python.org/downloads/release/python-353/. I downloaded `python-3.5.3-macosx10.6.pkg`. (Note that PyQt does not yet work with Python 3.6.)

Install Qt 5.7.1 from https://www.qt.io/download-open-source/. I downloaded `qt-unified-mac-x64-2.0.4-online.dmg`. In the installer, you can skip making an account, and all you need is Qt 5.7 for macOS.

Now install some python dependencies with pip (note, there's issues building a .app if you install this in a virtualenv):

```sh
sudo pip3 install -r install/requirements.txt
```

Here's how you run GPG Sync, without having to build an app bundle:

```sh
./dev_scripts/gpgsync
```

Here's how you build an app bundle:

```sh
install/build_osx.sh
```

Now you should have `dist/GPG Sync.app`.

To codesign and build a .pkg for distribution:

```sh
install/build_osx.sh --release
```

Now you should have `dist/GPG Sync.pkg`.

## Linux distributions

*Debian / Ubuntu / Mint*

Install dependencies:

```sh
sudo apt install -y python3-pyqt5 python3-nose python3-stdeb python3-requests python3-socks python3-packaging python3-dateutil gnupg2
```

Make and install a .deb:

```sh
./install/build_deb.sh
sudo dpkg -i deb_dist/gpgsync_*.deb
```

*Fedora*

Install dependencies:

```sh
sudo dnf install -y rpm-build python3-qt5 python3-requests python3-nose python3-packaging python3-dateutil gnupg2
```

Make and install a .rpm:

```sh
./install/build_rpm.sh
sudo dnf install dist/gpgsync_*.rpm
```

## Run the tests

From the `gpgsync` folder run:

```sh
nosetests
```

Note that one of the tests will fail if you don't have SOCKS5 proxy server listening on port 9050 (e.g. Tor installed).
