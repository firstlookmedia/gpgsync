# Build instructions

At the moment, this is only for Arch Linux. More platforms coming soon.

## Install dependencies

```sh
sudo pacman -S python-pip python-pyqt5 python-pycurl
```

If you'd like to run the tests:

```sh
sudo pacman -S python-nose
```

## Run the tests

From the `pgpsync` folder run:

```sh
nosetests
```
