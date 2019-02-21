# Build instructions

## Mac OS X

Install Xcode from the Mac App Store. Once it's installed, run it for the first time to set it up. Also, run this to make sure command line tools are installed: `xcode-select --install`. And finally, open Xcode, go to Preferences > Locations, and make sure under Command Line Tools you select an installed version from the dropdown. (This is required for installing Qt5.)

Download and install Python 3.7.2 from https://www.python.org/downloads/release/python-372/. I downloaded `python-3.7.2-macosx10.9.pkg`.

Install Qt 5.11.3 from https://www.qt.io/download-open-source/. I downloaded `qt-unified-mac-x64-3.0.6-online.dmg`. In the installer, you can skip making an account, and all you need is `Qt` > `Qt 5.11.3` > `macOS`.

Now install some python dependencies with pip (note, there's issues building a .app if you install this in a virtualenv):

```sh
pip3 install -r install/requirements.txt
pip3 install -r install/requirements-tests.txt
pip3 install -r install/requirements-macos.txt
pip3 install -r install/requirements-package.txt
```

Here's how you run GPG Sync, without having to build an app bundle:

```sh
./dev_scripts/gpgsync
```

Here's how you build an app bundle:

```sh
install/build_pkg.sh
```

Now you should have `dist/GPG Sync.app`.

To codesign and build a .pkg for distribution:

```sh
install/build_pkg.sh --release
```

Now you should have `dist/GPG Sync-{version}.pkg`.

## Windows

Download Python 3.7.2, 32-bit (x86) from https://www.python.org/downloads/release/python-372/. I downloaded `python-3.7.2.exe`. When installing it, make sure to check the "Add Python 3.7 to PATH" checkbox on the first page of the installer.

Open a command prompt, cd to the gpgsync folder, and install dependencies with pip:

```cmd
pip install -r install\requirements.txt
pip install -r install\requirements-tests.txt
pip install -r install\requirements-windows.txt
# skip this if you're building for distribution
pip install -r install\requirements-package.txt
```

Install the Qt 5.11.3 from https://www.qt.io/download-open-source/. I downloaded `qt-unified-windows-x86-3.0.6-online.exe`. In the installer, you can skip making an account, and all you need `Qt` > `Qt 5.11.3` > `MSVC 2015 32-bit`.

After that you can launch GPG Sync during development with:

```
python dev_scripts\gpg_sync --debug
```

### To make a .exe:

These instructions include adding folders to the path in Windows. To do this, go to Start and type "advanced system settings", and open "View advanced system settings" in the Control Panel. Click Environment Variables. Under "System variables" double-click on Path. From there you can add and remove folders that are available in the PATH.

Download and install the 32-bit [Visual C++ Redistributable for Visual Studio 2015](https://www.microsoft.com/en-us/download/details.aspx?id=48145). I downloaded `vc_redist.x86.exe`.

Download and install the standalone [Windows 10 SDK](https://dev.windows.com/en-us/downloads/windows-10-sdk). Note that you may not need this if you already have Visual Studio.

Add the following directories to the path:

* `C:\Program Files (x86)\Windows Kits\10\bin\10.0.17763.0\x86`
* `C:\Program Files (x86)\Windows Kits\10\Redist\10.0.17763.0\ucrt\DLLs\x86`
* `C:\Users\user\AppData\Local\Programs\Python\Python37-32\Lib\site-packages\PyQt5\Qt\bin`

Finally, open a command prompt, cd into the gpgsync directory, and type: `pyinstaller install\pyinstaller.spec`. `gpgsync.exe` and all of their supporting files will get created inside the `dist` folder.

### If you want the .exe to not get falsely flagged as malicious by anti-virus software

GPG Sync uses PyInstaller to turn the python source code into Windows executable `.exe` file. Apparently, malware developers also use PyInstaller, and some anti-virus vendors have included snippets of PyInstaller code in their virus definitions. To avoid this, you have to compile the Windows PyInstaller bootloader yourself instead of using the pre-compiled one that comes with PyInstaller.

(If you don't care about this, you can install PyInstaller with `pip install PyInstaller==3.4`.)

Here's how to compile the PyInstaller bootloader:

Download and install [Microsoft Build Tools for Visual Studio 2017](https://www.visualstudio.com/downloads/#build-tools-for-visual-studio-2017). I downloaded `vs_buildtools.exe`. In the installer, check the box next to "Visual C++ build tools". Click "Individual components", and under "Compilers, build tools and runtimes", check "Windows Universal CRT SDK". Then click install. When installation is done, you may have to reboot your computer.

Then, enable the 32-bit Visual C++ Toolset on the Command Line like this:

```
cd "C:\Program Files (x86)\Microsoft Visual Studio\2017\BuildTools\VC\Auxiliary\Build"
vcvars32.bat
```

Make sure you have a new enough `setuptools`:

```
pip install setuptools==40.6.3
```

Now make sure you don't have PyInstaller installed from pip:

```
pip uninstall PyInstaller
rmdir C:\Users\user\AppData\Local\Programs\Python\Python37-32\Lib\site-packages\PyInstaller /S
```

Change to a folder where you keep source code, and clone the PyInstaller git repo:

```
git clone https://github.com/pyinstaller/pyinstaller.git
```

To verify the git tag, you first need the signing key's PGP key, which means you need `gpg`. If you installed git from git-scm.com, you can run this from Git Bash:

```
gpg --keyserver hkps://keyserver.ubuntu.com:443 --recv-key 0xD4AD8B9C167B757C4F08E8777B752811BF773B65
```

And now verify the tag:

```
cd pyinstaller
git tag -v v3.4
```

It should say `Good signature from "Hartmut Goebel <h.goebel@goebel-consult.de>`. If it verified successfully, checkout the tag:

```
git checkout v3.4
```

And compile the bootloader, following [these instructions](https://pythonhosted.org/PyInstaller/bootloader-building.html). To compile, run this:

```
cd bootloader
python waf distclean all --target-arch=32bit --msvc_targets=x86
```

Finally, install the PyInstaller module into your local site-packages:

```
cd ..
python setup.py install
```

Now the next time you use PyInstaller to build GPG Sync, the `.exe` file should not be flagged as malicious by anti-virus.

### To build the installer:

* Go to http://nsis.sourceforge.net/Download and download the latest NSIS. I downloaded `nsis-3.04-setup.exe`.
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
python setup.py pytest
```

Note that one of the tests will fail if you don't have SOCKS5 proxy server listening on port 9050 (e.g. Tor installed).
