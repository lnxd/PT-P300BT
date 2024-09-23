# Printing to a Brother P-Touch Cube PT-P300BT label printer from a computer

## Introduction

The [Brother P-touch Cube PT-P300BT labelling machine](https://support.brother.com/g/b/producttop.aspx?c=gb&lang=en&prod=p300bteuk) is intended to be controlled from the official Brother P-touch Design&Print 2 app for [Android](https://play.google.com/store/apps/details?id=com.brother.ptouch.designandprint2) and [iOS](https://apps.apple.com/it/app/brother-p-touch-design-print/id1105307806) devices.

This repository provides a command-line tool in pure Python to print from a computer. It is based on the scripts included in the following Gists:

- [PT-P300BT Gist](https://gist.github.com/Ircama/bd53c77c98ecd3d7db340c0398b22d8a)
- [dogtopus/Pipfile Gist](https://gist.github.com/dogtopus/64ae743825e42f2bb8ec79cea7ad2057)
- [stecman Gist](https://gist.github.com/stecman/ee1fd9a8b1b6f0fdd170ee87ba2ddafd)
- [vsigler Gist](https://gist.github.com/vsigler/98eafaf8cdf2374669e590328164f5fc)

The scripts convert text labels to appropriate images compatible with 12mm width craft tapes like [TZe-131](https://www.brother-usa.com/products/tze131) or [TZe-231](https://www.brother-usa.com/products/tze231), tuned for the max allowed character size with this printer, regardless the used font. The scripts also include the code to drive the printer via serial Bluetooth interface.

Comparing with the PT-P300BT Gist, the Python *printlabel.py* program has been introduced, replacing *printlabel.cmd* and *printlabel.sh*. It supports any TrueType font, automatically selects the maximum font size to fit the printable area of the tape, avoids creating temporary image files, and does not rely on ImageMagick. Text strings including characters which do not [overshoot](https://en.wikipedia.org/wiki/Overshoot_(typography)) below the [baseline](https://en.wikipedia.org/wiki/Baseline_(typography)) (e.g., uppercase letters) are automatically printed with a bigger font.

Standard usage: `python3 printlabel.py COM_PORT FONT_NAME TEXT_TO_PRINT`

Examples:

```
python3 printlabel.py COM7 "arial.ttf" "Lorem Ipsum"
```

or:

```
printlabel.exe COM7 "arial.ttf" "Lorem Ipsum"
```

In addition, all options included in *labelmaker.py* are available.

```
usage: printlabel.py [-h] [-l] [-s] [-i IMAGE] [-n] [-F] [-a] [-m END_MARGIN] [-r] [-C] COM_PORT FONT_NAME TEXT_TO_PRINT

positional arguments:
  COM_PORT              Printer COM port.
  FONT_NAME             Pathname of the used TrueType font.
  TEXT_TO_PRINT         Text to be printed.

optional arguments:
  -h, --help            show this help message and exit
  -l, --lines           Add horizontal lines for drawing area (dotted red) and tape (cyan).
  -s, --show            Show the created image.
  -i IMAGE, --image IMAGE
                        Image file to print. If this option is used, TEXT_TO_PRINT and FONT_NAME are ignored.
  -n, --no-print        Only configure the printer and send the image but do not send print command.
  -F, --no-feed         Disable feeding at the end of the print (chaining).
  -a, --auto-cut        Enable auto-cutting (or print label boundary on e.g. PT-P300BT).
  -m END_MARGIN, --end-margin END_MARGIN
                        End margin (in dots).
  -r, --raw             Send the image to printer as-is without any pre-processing.
  -C, --nocomp          Disable compression.
```

## Installation

```
git clone https://github.com/Ircama/PT-P300BT && cd PT-P300BT
pip install -r requirements.txt
```

## Bluetooth printer connection on Windows

The following steps allow connecting a Windows COM port to the Bluetooth printer.

- Open Windows Settings
- Go to Bluetooth & devices
- Press "View more devices"
- Press "More Bluetooth settings"
- Select "COM Ports" tab
- Press Add... (wait for a while)
- Select Ongoing
- Press Browse...
- Search for PT-P300BT9000 and select it
- Select PT-P300BT9000
- Service: Serial
- Read the name of the COM port
- Press OK
- Press OK

Perform the device peering. 

## Usage on WSL

Pair the printer with an RFCOMM COM port using the Windows Bluetooth panel.

Check the outbound RFCOMM COM port number and use it to define /dev/ttyS_serial_port_number; for instance, COM5 is /dev/ttyS5.

Usage: `python3 printlabel.py /dev/ttyS_serial_port_number FONT_NAME TEXT_TO_PRINT`

## Bluetooth printer connection on Ubuntu

Connect the printer via [Ubuntu Bluetooth panel](https://help.ubuntu.com/stable/ubuntu-help/bluetooth-connect-device.html.en) (e.g., Settings, Bluetooth).

To read the MAC address: `hcitool scan`. Setup /dev/rfcomm0.

Usage: `python3 printlabel.py /dev/rfcomm0 FONT_NAME TEXT_TO_PRINT`

## Creating an executable asset for the GUI

To build an executable file via [pyinstaller](https://pyinstaller.org/en/stable/), first install *pyinstaller* with `pip install pyinstaller`.

The *printlabel.spec* file helps building the executable program. Run it with the following command.

```
pip install pyinstaller  # if not yet installed
pyinstaller printlabel.spec
```

Then run the executable file created in the *dist/* folder.

This repository includes a Windows *printlabel.exe* executable file which is automatically generated by a [GitHub Action](https://github.com/Ircama/PT-P300BT/blob/main/.github/workflows/build.yml). It is packaged in a ZIP file named *printlabel.zip* and uploaded into the [Releases](https://github.com/Ircama/PT-P300BT/releases/latest) folder.


## Other resources

- https://github.com/probonopd/ptouch-770
- https://github.com/kacpi2442/labelmaker

## Acknowledgments

[stecman](https://gist.github.com/stecman) and his [Gist](https://gist.github.com/stecman/ee1fd9a8b1b6f0fdd170ee87ba2ddafd).
