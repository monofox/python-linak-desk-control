# python-linak-desk-control

This is a simple program for controlling LINAK Desk Control Cable in linux with simple python and libusb.

Its a python implementation of [C-Routine of ranma1988](https://github.com/ranma1988/usb2lin06-HID-in-linux-for-LINAK-Desk-Control-Cable)

Tested on: Gentoo x64 (December 2018). Might work on Windows too.
Tested on model: usb2lin06 with CONTROL BOX CBD6S without safety limit.

### Dependencies
this is using: **libusb-1.0**
```sh
$ pip install -r requirements.txt
```

The installation of libusb1 package of python may need to have the libusb-1.0 devel packages installed on most linux systems.

### Capabilities
* setting height
* retrieve current height

### Usage
Just trying out in your shell is easy:
```sh
$ python3 linak-desk-control.py
```

It will show you mostly the whole help in order to understand which commands can be executed.
E.g. to get the current height:
```sh
$ python3 linak-desk-control.py height
```

And to bring the desk to height 4414:
```sh
$ python3 linak-desk-control.py move 4414
```

### License 
This piece of work is distributed with GNU GPLv3 or later.