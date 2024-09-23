import sys
import os
import re
import argparse
import serial
from PIL import Image, ImageDraw, ImageFont, ImageOps

from labelmaker import do_print_job, reset_printer


def set_args():
    """
    Similar to parse_args() in labelmaker, with the addition of
    two other parameters and some change in the help.
    """
    p = argparse.ArgumentParser()
    p.add_argument(
        'comport',
        metavar='COM_PORT',
        help='Printer COM port.'
    )
    p.add_argument(
        'fontname',
        metavar='FONT_NAME',
        help='Pathname of the used TrueType font.'
    )
    p.add_argument(
        'text_to_print',
        metavar='TEXT_TO_PRINT',
        help='Text to be printed.'
    )
    p.add_argument(
        '-l', '--lines',
        help='Add horizontal lines for drawing area (dotted red) and tape (cyan).',
        action='store_true'
    )
    p.add_argument(
        '-s', '--show',
        help='Show the created image and quit.',
        action='store_true'
    )
    p.add_argument(
        '-i', '--image',
        help='Image file to print. If this option is used, TEXT_TO_PRINT and FONT_NAME are ignored.'
    )
    p.add_argument(
        '-n', '--no-print',
        help='Only configure the printer and send the image but do not send print command.',
        action='store_true'
    )
    p.add_argument(
        '-F', '--no-feed',
        help='Disable feeding at the end of the print (chaining).',
        action='store_true'
    )
    p.add_argument(
        '-a', '--auto-cut',
        help='Enable auto-cutting (or print label boundary on e.g. PT-P300BT).',
        action='store_true'
    )
    p.add_argument(
        '-m', '--end-margin',
        help='End margin (in dots).',
        default=0,
        type=int
    )
    p.add_argument(
        '-r', '--raw',
        help='Send the image to printer as-is without any pre-processing.',
        action='store_true'
    )
    p.add_argument(
        '-C', '--nocomp',
        help='Disable compression.',
        action='store_true'
    )
    return p

def main():
    p = set_args()
    args = p.parse_args()
    data = None
    if args.image is None:
        height_of_the_printable_area = 64  # px: number of vertical pixels of the PT-P300BT printer (9 mm)
        height_of_the_tape = 86  # 64 px / 9 mm * 12 mm (the borders over the printable area will not be printed)
        height_of_the_image = 88  # px (can be any value >= height_of_the_tape, but height_of_the_tape + 2 border lines is good)
        h_padding = 5  # horizontal padding (left and right)

        # Compute max TT font size to remain within height_of_the_printable_area
        font_size = 1
        font_height = 0
        while font_height < height_of_the_printable_area - 1:
            font = ImageFont.truetype(
                args.fontname, font_size, encoding='utf-8'
            )
            font_width, font_height = font.getbbox(
                args.text_to_print, anchor="lt"
            )[2:]
            font_size += 1

        # Create a drawing context for the image
        image = Image.new(
            "RGB",
            (font_width + h_padding * 2 + 1, height_of_the_image),
            "white"
        )
        draw = ImageDraw.Draw(image)
        print_border = (height_of_the_image - height_of_the_printable_area) / 2
        draw.text(
            (h_padding, print_border + 1),
            args.text_to_print,
            font=font, fill="black", anchor="lt"
        )

        if args.lines:
            # Draw a dotted horizontal line over the top and below the bottom borders of the printable area
            for x in range(0, image.width, 5):
                draw.line(
                    (x, print_border, x + 1, print_border),
                    fill="red", width=1
                )
                draw.line(
                    (
                        x, height_of_the_image - print_border, x + 1,
                        height_of_the_image - print_border
                    ),
                    fill="red", width=1
                )
            # Draw a cyan line showing the tape borders
            tape_border = int((height_of_the_image - height_of_the_tape) / 2)
            if tape_border > 0:
                draw.line(
                    (0, tape_border - 1, image.width, tape_border - 1),
                    fill="cyan", width=1
                )
                draw.line(
                    (
                        0, height_of_the_image - tape_border,
                        image.width, height_of_the_image - tape_border
                    ),
                    fill="cyan", width=1
                )

        if args.show:
            image.show()

        # Convert and rotate (similar to read_png() of labelmaker_encode.py)
        tmp = image.convert('1', dither=Image.Dither.FLOYDSTEINBERG)
        tmp = ImageOps.invert(tmp.convert('L')).convert('1')
        tmp = tmp.rotate(-90, expand=True)
        tmp = ImageOps.mirror(tmp)
        w, h = tmp.size
        padded = Image.new('1', (128, h))
        x, y = (128-w)//2, 0
        nw, nh = x+w, y+h
        padded.paste(tmp, (x, y, nw, nh))
        if args.show:
            padded.show()
            if args.no_print:
                quit()
        data = padded.tobytes()

    # Similar to main() in labelmaker.py
    try:
        ser = serial.Serial(args.comport)
    except serial.SerialException:
        p.error(
            'Printer on Bluetooth serial port "'
            + args.comport
            + '" is unavailable or unreachable.'
        )
    except Exception as e:
        p.error(e)

    try:
        assert data is not None
        do_print_job(ser, args, data)
    finally:
        # Initialize
        reset_printer(ser)

if __name__ == "__main__":
    main()
