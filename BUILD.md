# Build instructions

Install dependencies in Debian:

```sh
sudo apt-get install python3-pyqt5 python3-pycurl python3-nose
```

Install dependencies in Arch:

```sh
sudo pacman -S python-pyqt5 python-pycurl python-nose
```

## Run the tests

From the `pgpsync` folder run:

```sh
nosetests
```

Note that one of the tests will fail if you don't have SOCKS5 proxy server listening on port 9050 (e.g. Tor installed).
