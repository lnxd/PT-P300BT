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
        # Check if label is all in uppercase mode (A-Z, 0-9, space, and hyphen)
        # Define font sizes
        if re.match(r"^[A-Z0-9\ -]+$", args.text_to_print):
            mode = "uppercase"
            font_size = 86
            print("UPPERCASE MODE (bigger font)")
        else:
            mode = "standard"
            font_size = 70
            print("standard mode")

        try:
            # Load a font (ensure you have a valid TTF file path)
            font = ImageFont.truetype(args.fontname, font_size)
        except IOError:
            p.error("Font file not found. Make sure 'arial.ttf' or another TTF file is available.")

        image = Image.new("RGB", (1, 1), "white")  # Dummy image to calculate size
        # Get the bounding box for the text
        draw = ImageDraw.Draw(image)
        _, _, text_width, text_height = draw.textbbox(
            (0, 0), args.text_to_print, font=font
        )

        # Create a drawing context for the image
        if mode == "uppercase":
            # Add some space for the border and padding
            image = Image.new("RGB", (text_width + 20, text_height + 20), "white")
            draw = ImageDraw.Draw(image)
            draw.text((10, 3), args.text_to_print, font=font, fill="black")
        else:
            # Standard mode, with different alignment and padding
            image = Image.new("RGB", (text_width + 10, text_height + 30), "white")
            draw = ImageDraw.Draw(image)
            draw.text((5, 10), args.text_to_print, font=font, fill="black")

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
