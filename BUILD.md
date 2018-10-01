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

### PyInstaller note

If you'd like to build an app bundle that hides the dock icon ([#7](https://github.com/firstlookmedia/gpgsync/issues/7)), you must have a version of PyInstaller installed that fixes [this bug](https://github.com/pyinstaller/pyinstaller/issues/1917). At time of writing the fix for that isn't merged yet, but manually installing PyInstaller from [this PR branch](https://github.com/pyinstaller/pyinstaller/pull/3566) does the trick for me.

## Windows

Download Python 3.6.4, 32-bit (x86) from https://www.python.org/downloads/release/python-364/. I downloaded `python-3.6.4.exe`. When installing it, make sure to check the "Add Python 3.6 to PATH" checkbox on the first page of the installer.

Open a command prompt, cd to the gpgsync folder, and install dependencies with pip:

```cmd
pip3 install -r install\requirements.txt
```

Download and install Qt5 from https://www.qt.io/download-open-source/. I downloaded `qt-unified-windows-x86-3.0.4-online.exe`. There's no need to login to a Qt account during installation. Make sure you install the latest Qt 5.x. I installed Qt 5.11.0. You only need to install the `MSVC 2015 32-bit` component, as well as all of the the `Qt` components, for that that version.

After that you can launch GPG Sync during development with:

```
python dev_scripts\gpg_sync --debug
```

### To make a .exe:

These instructions include adding folders to the path in Windows. To do this, go to Start and type "advanced system settings", and open "View advanced system settings" in the Control Panel. Click Environment Variables. Under "System variables" double-click on Path. From there you can add and remove folders that are available in the PATH.

Download and install the 32-bit [Visual C++ Redistributable for Visual Studio 2015](https://www.microsoft.com/en-US/download/details.aspx?id=48145). I downloaded `vc_redist.x86.exe`.

Download and install the standalone [Windows 10 SDK](https://dev.windows.com/en-us/downloads/windows-10-sdk). Note that you may not need this if you already have Visual Studio.

Add the following directories to the path:

* `C:\Program Files (x86)\Windows Kits\10\bin\10.0.16299.0\x86`
* `C:\Program Files (x86)\Windows Kits\10\Redist\ucrt\DLLs\x86`
* `C:\Users\user\AppData\Local\Programs\Python\Python36-32\Lib\site-packages\PyQt5\Qt\bin`

Finally, open a command prompt, cd into the gpgsync directory, and type: `pyinstaller install\pyinstaller.spec`. `gpgsync.exe` and all of their supporting files will get created inside the `dist` folder.

### To build the installer:

* Go to http://nsis.sourceforge.net/Download and download the latest NSIS. I downloaded `nsis-3.03-setup.exe`.
* Add `C:\Program Files (x86)\NSIS` to the path.

If you want to sign binaries with Authenticode:

* You'll need a code signing certificate. I got an open source code signing certificate from [Certum](https://www.certum.eu/certum/cert,offer_en_open_source_cs.xml).
* Once you get a code signing key and certificate and covert it to a pfx file, import it into your certificate store.

Note that you must have a codesigning certificate installed in order to use the `install\build_exe.bat` script, because it codesigns `gpgsync.exe`, `uninstall.exe`, and `gpgsync-setup.exe`.

Open a command prompt, cd to the gpgsync directory, and type: `install\build_exe.bat`

This will prompt you to codesign three binaries and execute one unsigned binary. When you're done clicking through everything you will have `dist\gpgsync-setup.exe`.


## Linux distributions

*Debian / Ubuntu / Mint*

Install dependencies:

```sh
sudo apt install -y python3-pyqt5 python3-pytest python3-pytest-runner python3-stdeb python3-requests python3-socks python3-packaging python3-dateutil gnupg2
```

Make and install a .deb:

```sh
./install/build_deb.sh
sudo dpkg -i deb_dist/gpgsync_*.deb
```

*Fedora*

Install dependencies:

```sh
sudo dnf install -y rpm-build python3-qt5 python3-requests python3-pytest-runner python3-packaging python3-dateutil gnupg2
```

Make and install a .rpm:

```sh
./install/build_rpm.sh
sudo dnf install dist/gpgsync_*.rpm
```

## Alternatively utilize Docker to build the relevant debian/rpm

There are `make` commands to build for the latest stable of debian (`stretch`)
and fedora (`27`):

```sh
make build-fedora27-rpm
```

or

```sh
make build-debianstretch-deb
```

## Run the tests

From the `gpgsync` folder run:

```sh
pytest
```

Note that one of the tests will fail if you don't have SOCKS5 proxy server listening on port 9050 (e.g. Tor installed).
