#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import inspect
import subprocess
import shutil
import argparse
import glob
import itertools

root = os.path.dirname(
    os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
)


def run(cmd):
    subprocess.run(cmd, cwd=root, check=True)


def codesign(path, entitlements, identity):
    run(
        [
            "codesign",
            "--sign",
            identity,
            "--entitlements",
            str(entitlements),
            "--timestamp",
            "--deep",
            str(path),
            "--force",
            "--options",
            "runtime",
        ]
    )


def main():
    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--with-codesign",
        action="store_true",
        dest="with_codesign",
        help="Codesign the app bundle",
    )
    args = parser.parse_args()

    build_path = os.path.join(root, "build")
    dist_path = os.path.join(root, "dist")
    dist_root_path = os.path.join(root, "dist", "root")
    app_path = os.path.join(dist_path, "GPG Sync.app")
    component_pkg_path = os.path.join(root, "dist", "GPGSyncComponent.pkg")
    pkg_path = os.path.join(dist_path, "GPGSync.pkg")

    print("○ Deleting old build and dist")
    if os.path.exists(build_path):
        shutil.rmtree(build_path)
    if os.path.exists(dist_path):
        shutil.rmtree(dist_path)

    print("○ Building app bundle")
    run(["pyinstaller", os.path.join(root, "install/pyinstaller.spec"), "--clean"])
    shutil.rmtree(os.path.join(dist_path, "gpgsync"))

    print(f"○ Finished build app: {app_path}")

    if args.with_codesign:
        print("○ Code signing app bundle")
        identity_name_application = (
            "Developer ID Application: FIRST LOOK PRODUCTIONS, INC. (P24U45L8P5)"
        )
        identity_name_installer = (
            "Developer ID Installer: FIRST LOOK PRODUCTIONS, INC. (P24U45L8P5)"
        )
        entitlements_plist_path = os.path.join(
            root, "install", "macos-packaging", "entitlements.plist"
        )

        for path in itertools.chain(
            glob.glob(f"{app_path}/**/*.so", recursive=True),
            glob.glob(f"{app_path}/**/*.dylib", recursive=True),
            glob.glob(f"{app_path}/**/Python3", recursive=True),
            [app_path],
        ):
            codesign(path, entitlements_plist_path, identity_name_application)
        print(f"○ Signed app bundle: {app_path}")

        os.makedirs(os.path.join(dist_root_path, "Applications"))
        shutil.move(app_path, os.path.join(dist_root_path, "Applications"))

        run(
            [
                "pkgbuild",
                "--sign",
                identity_name_installer,
                "--root",
                dist_root_path,
                "--component-plist",
                os.path.join(
                    root, "install", "macos-packaging", "gpgsync-component.plist"
                ),
                "--scripts",
                os.path.join(root, "install", "macos-packaging", "scripts"),
                component_pkg_path,
            ]
        )
        run([
            "productbuild",
            "--sign",
            identity_name_installer,
            "--package",
            component_pkg_path,
            pkg_path
        ])

        print(f"○ Finished building package: {pkg_path}")

    else:
        print("○ Skipping code signing")


if __name__ == "__main__":
    main()
