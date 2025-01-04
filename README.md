# Printing to a Brother P-Touch Cube PT-P300BT label printer from a computer

## Introduction

The [Brother P-touch Cube PT-P300BT labelling machine](https://support.brother.com/g/b/producttop.aspx?c=gb&lang=en&prod=p300bteuk) is intended to be controlled from the official Brother P-touch Design&Print 2 app for [Android](https://play.google.com/store/apps/details?id=com.brother.ptouch.designandprint2) and [iOS](https://apps.apple.com/it/app/brother-p-touch-design-print/id1105307806) devices.

This repository provides a command-line tool in pure Python to print from a computer. It is based on the scripts included in the following Gists:

- [PT-P300BT Gist](https://gist.github.com/Ircama/bd53c77c98ecd3d7db340c0398b22d8a)
- [dogtopus/Pipfile Gist](https://gist.github.com/dogtopus/64ae743825e42f2bb8ec79cea7ad2057)
- [stecman Gist](https://gist.github.com/stecman/ee1fd9a8b1b6f0fdd170ee87ba2ddafd)
- [vsigler Gist](https://gist.github.com/vsigler/98eafaf8cdf2374669e590328164f5fc)

The scripts convert text labels to appropriate images (including the first page of a PDF conversion with "pdf2image" and which requires poppler to be installed) compatible with 12mm width craft tapes like [TZe-131](https://www.brother-usa.com/products/tze131) or [TZe-231](https://www.brother-usa.com/products/tze231), tuned for the max allowed character size with this printer, regardless the used font. The scripts also include the code to drive the printer via serial Bluetooth interface.

Comparing with the PT-P300BT Gist, the Python *printlabel.py* program has been introduced, replacing *printlabel.cmd* and *printlabel.sh*. It supports any TrueType and OpenType font, automatically selects the maximum font size to fit the printable area of the tape, avoids creating temporary image files, provides more accurate image processing and does not rely on ImageMagick. Text strings including characters which do not [overshoot](https://en.wikipedia.org/wiki/Overshoot_(typography)) below the [baseline](https://en.wikipedia.org/wiki/Baseline_(typography)) (e.g., uppercase letters) are automatically printed with a bigger font. In addition, the program calculates the size of the printed tape and the print duration and processes images.

Standard usage: `python3 printlabel.py COM_PORT FONT_NAME TEXT_TO_PRINT`

Examples:

```
python3 printlabel.py COM7 "arial.ttf" "Lorem Ipsum"
```

or:

```
printlabel.exe COM7 "arial.ttf" "Lorem Ipsum"
```

In addition, all options included in *labelmaker.py* are available, with several extensions.

```
usage: printlabel.py [-h] [-u] [-l] [-s] [-c] [-i FILE_NAME] [-M FILE_NAME] [-R FLOAT] [-X DOTS]
                     [-Y DOTS] [-S FILE_NAME] [-n] [-F] [-a] [-m DOTS] [-r] [-C]
                     [--fill-color FILL] [--stroke-fill STROKE_FILL]
                     [--stroke-width STROKE_WIDTH] [--text-size MILLIMETERS]
                     [--white-level NUMBER] [--threshold NUMBER]
                     COM_PORT FONT_NAME TEXT_TO_PRINT [TEXT_TO_PRINT ...]

positional arguments:
  COM_PORT              Printer COM port.
  FONT_NAME             Pathname of the used TrueType or OpenType font.
  TEXT_TO_PRINT         Text to be printed. UTF8 characters are accepted.

optional arguments:
  -h, --help            show this help message and exit
  -u, --unicode         Use Unicode escape sequences in TEXT_TO_PRINT.
  -l, --lines           Add horizontal lines for drawing area (dotted red) and tape (cyan).
  -s, --show            Show the created image. (If also using -n, terminate.)
  -c, --show-conv       Show the converted image. (If also using -n, terminate.)
  -i FILE_NAME, --image FILE_NAME
                        Image file to print. If this option is used (legacy mode), TEXT_TO_PRINT
                        and FONT_NAME are ignored.
  -M FILE_NAME, --merge FILE_NAME
                        Merge the image file before the text. Can be used multiple times.
  -R FLOAT, --resize FLOAT
                        With image merge, additionaly resize it (floating point number).
  -X DOTS, --x-merge DOTS
                        With image merge, shift right the image of X dots.
  -Y DOTS, --y-merge DOTS
                        With image merge, shift down the image of Y dots.
  -S FILE_NAME, --save FILE_NAME
                        Save the produced image to a PNG file.
  -n, --no-print        Only configure the printer and send the image but do not send print
                        command.
  -F, --no-feed         Disable feeding at the end of the print (chaining).
  -a, --auto-cut        Enable auto-cutting (or print label boundary on e.g. PT-P300BT).
  -m DOTS, --end-margin DOTS
                        End margin (in dots).
  -r, --raw             Send the image to printer as-is without any pre-processing.
  -C, --nocomp          Disable compression.
  --fill-color FILL     Fill color for the text (e.g., "white"; default = "black").
  --stroke-fill STROKE_FILL
                        Stroke Fill color for the text (e.g., "black"; default = None).
  --stroke-width STROKE_WIDTH
                        Width of the text stroke (e.g., 1 or 2).
  --text-size MILLIMETERS
                        Horizontally stretch the text to fit the specified size.
  --white-level NUMBER  Minimum pixel value to consider it "white" when cropping the image. Set
                        it to a value close to 255. (Default: 240)
  --threshold NUMBER    Custom thresholding when converting the image to binary, to manually
                        decide which pixel values become black or white (Default: 75)
```

Options `-sln` are useful to simulate the print, showing the created image and adding a ruler in inches and centimeters (magenta), with horizontal lines to mark the drawing area (dotted red) and the tape borders (cyan).

Before generating the text (`TEXT_TO_PRINT`), the tool allows concatenating images with the `-M` option; it can be used more times for multiple images (transparent images are also accepted). The final image can also be saved with the `-S` option and then reused by running again the tool with the `-M` option; when also setting `TEXT_TO_PRINT` to a null string (`""`), the reused image will remain unchanged. Merged images are automatically resized to fit the printable area, removing white borders without modifying the proportion. Resize and traslation of merged images can also be manually controlled with `-R` (floating point number), `-X`, `-Y`. The `--text-size` option horizontally stretches or squeezes the text so that it fits the specified size in millimeters; the size parameter includes `--end-margin` and default left and right paddings, but does not include the size of merged images if used, which have a fixed length that has to be kept proportioned.

`-i` runs the legacy process of *labelmaker.py* and disables image processing.

Example of merging image and text, automatically resizing and traslating the image so that it fits the printable area:

```
curl https://raw.githubusercontent.com/uroesch/pngpetite/main/samples/pngpetite/happy-sun.png -o happy-sun.png
python printlabel.py -sl -M happy-sun.png COM7 "Gabriola.ttf" "Hello!"
```

Same as before, but uses the PDF version of happy-sun (it is designed for single page PDFs, like barcodes or other custom icons)

```
curl https://raw.githubusercontent.com/uroesch/pngpetite/main/samples/pngpetite/happy-sun.png -o happy-sun.png
python printlabel.py -sl -M happy-sun.pdf COM7 "Gabriola.ttf" "Hello!"
```

Same as the happy sun png example, but resizing the text so that its length is about 7 centimeters plus heading image, with a small white border at the end:
```
python printlabel.py -sl -M happy-sun.png COM7 --text-size 70 --end-margin 10 "micross.ttf" "lorem ipsum dolor sit amet"
```

Example of usage of Unicode escape sequences:

```
python printlabel.py -slnu COM7 "calibri.ttf" "\u2469Note"
```

Examples of using text stroke:

```
python printlabel.py -sln --stroke-width 2 -m 10 COM7 "arial.ttf" "Bolded text"
python printlabel.py -sln --stroke-width 1 --fill-color="white" --stroke-fill="black" -m 10 COM7 "Gabriola.ttf" "Text stroke"
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

## Notes

The printer has 180 DPI (dot per inch) square resolution at 20 mm/sec.

The max. length of the printable area is 0,499 m.

Even if the Brother TZe tape size is 12 mm, the height of the printable area is 64 pixels, which is 9 mm at 180 DPI: 64 pixels / 180 DPI / 0.0393701 inch/mm = 9 mm.

On this printer, tape is wasted before and after the printable area on each label (about 2.5 cm of additional tape before the printed area and about 1 mm after it).

## Other resources

- https://github.com/piksel/pytouch-cube
- https://github.com/probonopd/ptouch-770
- https://github.com/kacpi2442/labelmaker

## Acknowledgments

[stecman](https://gist.github.com/stecman) and his [Gist](https://gist.github.com/stecman/ee1fd9a8b1b6f0fdd170ee87ba2ddafd).
