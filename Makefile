VERSION=`cat share/version`

.PHONY: build-fedora27-rpm
build-fedora27-rpm:
	@docker run -it -v "${PWD}:/mnt" -w /mnt fedora:27 sh -c "dnf install -y rpm-build python3-qt5 python3-requests python3-nose python3-packaging python3-dateutil gnupg2 && ./install/build_rpm.sh"

.PHONY: build-debianstretch-deb
build-debianstretch-deb:
	@docker run -it -v "${PWD}:/mnt" -w /mnt debian:stretch sh -c "apt-get update && apt-get install -y python3-pyqt5 python3-nose python3-stdeb python3-requests python3-socks python3-packaging python3-dateutil gnupg2 python-all && ./install/build_deb.sh"
