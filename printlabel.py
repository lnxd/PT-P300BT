import sys
import os
import re
import serial
from PIL import Image, ImageDraw, ImageFont, ImageOps

from labelmaker import parse_args, do_print_job, reset_printer

def create_label(fontname, label_text, mode="standard"):
    # Define font sizes based on the mode
    if mode == "uppercase":
        font_size = 86
    else:
        font_size = 70

    try:
        # Load a font (ensure you have a valid TTF file path or use a default one)
        font = ImageFont.truetype(fontname, font_size)
    except IOError:
        print("Font file not found. Make sure 'arial.ttf' or another TTF file is available.")
        sys.exit(1)

    # Create a drawing context for the image
    if mode == "uppercase":
        image = Image.new("RGB", (1, 1), "white")  # Dummy image to calculate size
        draw = ImageDraw.Draw(image)

        # Get the bounding box for the text
        _, _, text_width, text_height = draw.textbbox(
            (0, 0), label_text, font=font
        )

        # Add some space for the border and padding
        image = Image.new("RGB", (text_width + 20, text_height + 20), "white")
        draw = ImageDraw.Draw(image)
        draw.text((10, 3), label_text, font=font, fill="black")
    else:
        # Standard mode, with different alignment and padding
        image = Image.new("RGB", (1, 1), "white")
        draw = ImageDraw.Draw(image)
        _, _, text_width, text_height = draw.textbbox(
            (0, 0), label_text, font=font
        )

        image = Image.new("RGB", (text_width + 10, text_height + 30), "white")
        draw = ImageDraw.Draw(image)
        draw.text((5, 10), label_text, font=font, fill="black")

    #image.show()
    #quit()
    return image

def main():
    label = None
    fontname = None
    if len(sys.argv) > 1:
        label = sys.argv.pop()
    if len(sys.argv) > 1:
        fontname = sys.argv.pop()
    p, args = parse_args()
    if not label or not fontname:
        p.error(f"Missing parameters: {sys.argv[0]} comport font text")
    data = None
    if args.image is None:
        # Check if label is in uppercase mode (A-Z, 0-9, space, and hyphen)
        if re.match(r"^[A-Z0-9\ -]+$", label):
            print("UPPERCASE MODE (bigger font)")
            image = create_label(fontname, label, mode="uppercase")
        else:
            print("standard mode")
            image = create_label(fontname, label, mode="standard")

        # Convert and rotate
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
