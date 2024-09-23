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
        help='Add two invisible horizontal lines (exprerimental, to be tuned).',
        action='store_true'
    )
    p.add_argument(
        '-s', '--show',
        help='Show the created image and quit.',
        action='store_true'
    )
    p.add_argument(
        '-i', '--image',
        help='Image file to print. If this option is used, TEXT_TO_PRINT is ignored.'
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
        # Load a fixed size to get the bottom part of the text vs. font baseline
        # (ensure you have a valid TTF file path)
        try:
            font = ImageFont.truetype(args.fontname, 100, encoding='utf-8')
        except IOError:
            p.error("Font file not found. Make sure 'arial.ttf' or another TTF file is available.")

        if font.getbbox(args.text_to_print, anchor="ls")[3] < 3:
            use_big_font = True
            font_size = 86
            print("UPPERCASE MODE (bigger font)")
        else:  # here the characters overshoot below the baseline
            use_big_font = False
            font_size = 67
            print("standard mode")

        font = ImageFont.truetype(args.fontname, font_size, encoding='utf-8')

        image = Image.new("RGB", (1, 1), "white")  # Dummy image to calculate size
        # Get the bounding box for the text
        draw = ImageDraw.Draw(image)
        _, _, text_width, text_height = draw.textbbox(
            (0, 0), args.text_to_print, font=font
        )

        # Create a drawing context for the image
        height_of_the_tape = 122
        if use_big_font:
            # Add some space for the border and padding
            image = Image.new("RGB", (text_width + 21, height_of_the_tape), "white")
            draw = ImageDraw.Draw(image)
            draw.text((10, 15), args.text_to_print, font=font, fill="black")
        else:
            # Standard mode, with different alignment and padding
            image = Image.new("RGB", (text_width + 1, height_of_the_tape), "white")
            draw = ImageDraw.Draw(image)
            draw.text((0, 19), args.text_to_print, font=font, fill="black")

        if args.lines:
            # Draw a horizontal line at the top and bottom borders
            dim = 29
            draw.line((0, dim, image.width, dim), fill="red", width=1)
            draw.line((0, image.height - dim, image.width, image.height - dim), fill="red", width=1)

        if args.show:
            image.show()
            if args.no_print:
                quit()

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
        data = padded.tobytes()

    # Similar to main() in labelmaker.py
    try:
        ser = serial.Serial(args.comport)
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
