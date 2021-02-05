# Build instructions

## Mac OS X

Download and install Python 3.8.7 from https://www.python.org/downloads/release/python-387/. I downloaded `python-3.8.7-macosx10.9.pkg`.

Make sure you have `poetry` installed (`pip3 install --user poetry`), then install dependencies:

```sh
poetry install
```

Here's how you run GPG Sync, without having to build an app bundle:

```sh
poetry run ./dev_scripts/gpgsync
```

Here's how you build an app bundle:

```sh
poetry run install/build_app.sh
```

Now you should have `dist/GPG Sync.app`.

To build a .pkg for distribution:

```sh
poetry run install/build_pkg.sh # this requires codesigning certificates
poetry run install/build_pkg.sh --without-codesign # this doesn't
```

Now you should have `dist/GPGSync-{version}.pkg`.

## Windows

Download Python 3.8.7, 32-bit (x86) from https://www.python.org/downloads/release/python-387/. I downloaded `python-3.8.7.exe`. When installing it, make sure to check the "Add Python 3.8 to PATH" checkbox on the first page of the installer.

Open a command prompt and cd to the gpgsync folder. If you don't have it already, install poetry (`pip install poetry`). Then install dependencies:

```cmd
poetry install
```

After that you can launch GPG Sync during development with:

```cmd
poetry run python dev_scripts\gpgsync -v
```

### To make a .exe:

These instructions include adding folders to the path in Windows. To do this, go to Start and type "advanced system settings", and open "View advanced system settings" in the Control Panel. Click Environment Variables. Under "System variables" double-click on Path. From there you can add and remove folders that are available in the PATH.

Download and install the standalone [Windows 10 SDK](https://developer.microsoft.com/en-US/windows/downloads/windows-10-sdk/).

Add the following directories to the path:

* `C:\Program Files (x86)\Windows Kits\10\bin\10.0.19041.0\x86`
* `C:\Program Files (x86)\Windows Kits\10\Redist\10.0.19041.0\ucrt\DLLs\x86`

Finally, open a command prompt, cd into the gpgsync directory, and run:

```cmd
poetry run pyinstaller install\pyinstaller.spec
```

`gpgsync.exe` and all of their supporting files will get created inside the `dist` folder.

### To build the installer:

* Go to http://nsis.sourceforge.net/Download and download the latest NSIS. I downloaded `nsis-3.06.1-setup.exe`.
* Add `C:\Program Files (x86)\NSIS` to the path.

Now install the Processes NSIS plugin.

* Go to https://nsis.sourceforge.io/NsProcess_plugin and download NsProcess. I downloaded `nsProcess_1_6.7z` (with sha256 hash `fc19fc66a5219a233570fafd5daeb0c9b85387b379f6df5ac8898159a57c5944`)
* Decompress it. You will probably need [7-Zip](https://www.7-zip.org/)
* Copy `nsProcess_1.6/Plugin/*.dll` to `C:\Program Files (x86)\NSIS\Plugins\x86-ansi`
* Copy `nsProcess_1.6/Include/ncProcess.nsh` to `C:\Program Files (x86)\NSIS\Include`

If you want to sign binaries with Authenticode:

* You'll need a code signing certificate. I got an open source code signing certificate from [Certum](https://www.certum.eu/certum/cert,offer_en_open_source_cs.xml).
* Once you get a code signing key and certificate and covert it to a pfx file, import it into your certificate store.

Note that you must have a codesigning certificate installed in order to use the `install\build_exe.bat` script, because it codesigns `gpgsync.exe`, `uninstall.exe`, and `gpgsync-setup.exe`.

Open a command prompt, cd to the gpgsync directory, and run:

```cmd
poetry run install\build_exe.bat
```

This will prompt you to codesign three binaries and execute one unsigned binary. When you're done clicking through everything you will have `dist\gpgsync-setup.exe`.


## Linux distributions

*Debian / Ubuntu / Mint*

Install dependencies:

```sh
sudo apt install -y python-all dh-python python3-pytest python3-pytest-runner python3-stdeb python3-pyside2.qtcore python3-pyside2.qtwidgets python3-pyside2.qtgui python3-requests python3-socks python3-packaging python3-dateutil gnupg2
```

Make and install a .deb:

```sh
./install/build_deb.sh
sudo apt install deb_dist/gpgsync_*.deb
```

*Fedora*

Install dependencies:

```sh
sudo dnf install -y rpm-build python3-pytest-runner python3-pyside2 python3-requests python3-packaging python3-dateutil gnupg2
```

Make and install a .rpm:

```sh
./install/build_rpm.sh
sudo dnf install dist/gpgsync-*-1.noarch.rpm
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

# Release instructions

This section documents the release process. Unless you're a GPG Sync developer making a release, you'll probably never need to follow it.

## Changelog, version, and signed git tag

Before making a release, all of these should be complete:

- `share/version` should have the correct version
- `install/gpgsync.nsi` should have the correct version, for the Windows installer
- `CHANGELOG.md` should be updated to include a list of all major changes since the last release
- There must be a PGP-signed git tag for the version, e.g. for GPG Sync 0.3.4, the tag must be `v0.3.4`

The first step for the macOS and Windows releases is the same:

Verify the release git tag:

```sh
git fetch
git tag -v v$VERSION
```

If the tag verifies successfully, check it out:

```
git checkout v$VERSION
```

## macOS release

To make a macOS release, go to macOS build machine:

- Build machine should be running macOS 10.13
- Verify and checkout the git tag for this release
- Run `poetry run ./install/build_app.sh`; this will make `dist/GPG Sync.app` but won't codesign it
- Copy `dist/GPG Sync.app` from the build machine to the `dist` folder on the release machine

Then move to the macOS release machine:

- Release machine should be running the latest version of macOS, and must have:
  - Apple-trusted `Developer ID Application: FIRST LOOK PRODUCTIONS, INC.` and `Developer ID Installer: FIRST LOOK PRODUCTIONS, INC.` code-signing certificates installed
  - An app-specific Apple ID password saved in the login keychain called `gpgsync-notarize`
- Verify and checkout the git tag for this release
- Run `poetry run ./install/build_pkg.sh`; this will make a codesigned installer package called `dist/GPGSync-$VERSION.pkg`
- Notarize it: `xcrun altool --notarize-app --primary-bundle-id "org.firstlook.gpgsync" -u "micah@firstlook.org" -p "@keychain:gpgsync-notarize" --file GPGSync-$VERSION.pkg`
- Wait for it to get approved, check status with: `xcrun altool --notarization-history 0 -u "micah@firstlook.org" -p "@keychain:gpgsync-notarize"`
- After it's approved, staple the ticket: `xcrun stapler staple GPGSync-$VERSION.pkg`

This process ends up with the final file:

```
dist/GPGSync-$VERSION.pkg
```

## Windows release

To make a Windows release, go to Windows build machine:

- Build machine should be running Windows 10, and have the Windows codesigning certificate installed
- Verify and checkout the git tag for this release
- Run `install\build_exe.bat`; this will make a codesigned installer package called `dist\gpgsync-setup.exe`
- Rename `gpgsync-setup.exe` to `gpgsync-$VERSION-setup.exe`

This process ends up with the final file:

```
gpgsync-$VERSION-setup.exe
```

## Publishing the release

To publish the release:

- Create a new release on GitHub, put the changelog in the description of the release, and upload the Windows and macOS installers
- Make a PR to [homebrew-cask](https://github.com/homebrew/homebrew-cask) to update the macOS version
