import sys
import os
import re
import argparse
import serial
from PIL import Image, ImageDraw, ImageFont, ImageOps
from pdf2image import convert_from_path

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
        nargs='?', default='arial.ttf',
        help='Pathname of the used TrueType or OpenType font.'
    )
    p.add_argument(
        'text_to_print',
        metavar='TEXT_TO_PRINT',
        nargs='*',
        help='Text to be printed. UTF8 characters are accepted.'
    )
    p.add_argument(
        '-u', '--unicode',
        help='Use Unicode escape sequences in TEXT_TO_PRINT.',
        action='store_true'
    )
    p.add_argument(
        '-l', '--lines',
        help='Add horizontal lines for drawing area (dotted red) and tape (cyan).',
        action='store_true'
    )
    p.add_argument(
        '-s', '--show',
        help='Show the created image. (If also using -n, terminate.)',
        action='store_true'
    )
    p.add_argument(
        '-c', '--show-conv',
        help='Show the converted image. (If also using -n, terminate.)',
        action='store_true'
    )
    p.add_argument(
        '-i', '--image',
        metavar='FILE_NAME',
        help='Image file to print. If this option is used (legacy mode), TEXT_TO_PRINT and FONT_NAME are ignored.'
    )
    p.add_argument(
        '-M', '--merge',
        metavar='FILE_NAME',
        action='append',
        help='Merge the image file before the text. Can be used multiple times.'
    )
    p.add_argument(
        '-R', '--resize',
        type=float,
        metavar='FLOAT',
        help='With image merge, additionaly resize it (floating point number).',
        default = 1.0
    )
    p.add_argument(
        '-X', '--x-merge',
        type=int,
        metavar='DOTS',
        help='With image merge, shift right the image of X dots.',
        default = 0
    )
    p.add_argument(
        '-Y', '--y-merge',
        metavar='DOTS',
        type=int,
        help='With image merge, shift down the image of Y dots.',
        default = 12
    )
    p.add_argument(
        '-S', '--save',
        metavar='FILE_NAME',
        help='Save the produced image to a PNG file.'
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
        metavar='DOTS',
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
    p.add_argument(
        '--fill-color',
        dest="fill",
        help='Fill color for the text (e.g., "white"; default = "black").',
        default="black",
    )
    p.add_argument(
        '--stroke-fill',
        help='Stroke Fill color for the text (e.g., "black"; default = None).',
        default=None,
    )
    p.add_argument(
        '--stroke-width',
        help='Width of the text stroke (e.g., 1 or 2).',
        type=int,
        default=0,
    )
    p.add_argument(
        '--text-size',
        help='Horizontally stretch the text to fit the specified size.',
        metavar='MILLIMETERS',
        type=int,
        default=None,
    )
    p.add_argument(
        '--white-level',
        help='Minimum pixel value to consider it "white" when'
        ' cropping the image. Set it to a value close to 255. (Default: 240)',
        metavar='NUMBER',
        type=int,
        default=240,
    )
    p.add_argument(
        '--threshold',
        help='Custom thresholding when converting the image to binary, to'
        ' manually decide which pixel values become black or white'
        ' (Default: 75)',
        metavar='NUMBER',
        type=int,
        default=75,
    )
    return p


def process_image(image_path, resize, white_level, target_height):
    # Determines if the image is a PDF and converts it to PNG if necessary
    if image_path.lower().endswith('.pdf'):
        image_path = convert_pdf(image_path)  # Sends image_path to convert_pdf() and returns the output_filename

    # Open the image
    img = Image.open(image_path)
    
    # Convert the image to RGBA to ensure it has an alpha channel
    img = img.convert("RGBA")
    pixels = img.load()

    # Create a new white background image with the same size as the original
    white_background = Image.new("RGBA", img.size, (255, 255, 255, 255))
    
    # Paste the original image onto the white background
    white_background.paste(img, (0, 0), img)
    
    # Now 'white_background' has no transparency (transparency is replaced by white)
    img = white_background
    
    # Convert the image to grayscale
    img = img.convert("L")  # "L" mode is for grayscale images
    
    # Get image dimensions
    width, height = img.size

    # Initialize the bounding box coordinates
    left, top, right, bottom = width, height, 0, 0
    
    # Iterate over each pixel to find the bounding box of non-white pixels
    for y in range(height):
        for x in range(width):
            pixel = img.getpixel((x, y))
            
            # White pixels in grayscale have a value close to 255
            if pixel < white_level:  # Consider pixels that are not white
                left = min(left, x)
                right = max(right, x)
                top = min(top, y)
                bottom = max(bottom, y)
    
    # Crop the image to the bounding box
    if right > left and bottom > top:
        cropped_img = img.crop((left, top, right + 1, bottom + 1))
        
        # Get the size of the cropped image
        cropped_width, cropped_height = cropped_img.size
        
        # Calculate the new width to maintain the aspect ratio with target height
        aspect_ratio = cropped_width / cropped_height
        new_width = int(target_height * aspect_ratio)
        
        # Resize the image to target height while maintaining aspect ratio
        return cropped_img.resize(
            (int(new_width * resize), int(target_height * resize)),
            Image.Resampling.LANCZOS
        )
    else:
        print("No content detected to crop.")
    return None

def convert_pdf(filename):
    # Converts the first page of a PDF to a PNG, returns PNG
    output_filename = filename.replace('.pdf', '.png')
    images = convert_from_path(filename, dpi=300, first_page=1, last_page=1) # used defaults, 300dpi may even be overkill for labels
    images[0].save(output_filename, "PNG")
    return output_filename

def main():
    p = set_args()
    args = p.parse_args()
    data = None
    if args.image is None: # not using the legacy mode
        height_of_the_printable_area = 64  # px: number of vertical pixels of the PT-P300BT printer (9 mm)
        height_of_the_tape = 86  # 64 px / 9 mm * 12 mm (the borders over the printable area will not be printed)
        height_of_the_image = 88  # px (can be any value >= height_of_the_tape, but height_of_the_tape + 2 border lines is good)
        h_padding = 5  # horizontal padding (left and right)

        # Compute max TT font size to remain within height_of_the_printable_area
        font_size = 0
        font_height = 0
        print_border = (height_of_the_image - height_of_the_printable_area) / 2
        text = " ".join(args.text_to_print)
        if text:
            if args.unicode:
                text = text.encode().decode('unicode_escape')
            stop = False
            while font_height != height_of_the_printable_area:
                if font_height > height_of_the_printable_area:
                    font_size -= 1
                    stop = True
                else:
                    font_size += 1
                try:
                    font = ImageFont.truetype(
                        args.fontname, font_size, encoding='utf-8'
                    )
                except Exception as e:
                    p.error(f'Cannot load font "{args.fontname}" - {e}')
                font_width, font_height = font.getbbox(text, anchor="lt")[2:]
                if stop:
                    print(
                        "The max height of this text with font "
                        f'"{args.fontname}" is {font_height} dots'
                        f' instead of {height_of_the_printable_area}.')
                    break

            # Create a drawing context for the image
            image = Image.new(
                "RGB",
                (font_width + h_padding * 2 + 1, height_of_the_image),
                "white"
            )
            draw = ImageDraw.Draw(image)
            try:
                draw.text(
                    (h_padding, print_border), text,
                    font=font,
                    fill=args.fill,
                    anchor="lt",
                    stroke_width=args.stroke_width,
                    stroke_fill=args.stroke_fill
                )
            except Exception as e:
                p.error(f"Invalid parameter: {e}")
            if args.text_size:
                text_size = (
                    int(args.text_size / 0.149)
                    - h_padding
                    - args.end_margin
                )  # mm to dot
                _, _, text_width, text_height = draw.textbbox(
                    (0, 0), text,
                    anchor="lt",
                    font=font,
                    stroke_width=args.stroke_width,
                )
                scale_factor = text_width / text_size
                image = image.transform(
                    (text_size + args.end_margin, height_of_the_image),
                    Image.Transform.AFFINE,
                    (scale_factor, 0, 0, 0, 1, 0),
                )
                while image.getpixel((image.width - 1, 0)) == (0, 0, 0):
                    crop_box = (0, 0, image.width - 1, height_of_the_image)
                    image = image.crop(crop_box)
                draw = ImageDraw.Draw(image)
        else:  # null image
            image = Image.new(
                "RGB",
                (0, height_of_the_image),
                "white"
            )
            draw = ImageDraw.Draw(image)

        if args.merge:
            for i in reversed(args.merge):
                loaded_image = process_image(
                    i,
                    args.resize,
                    white_level=args.white_level,
                    target_height=height_of_the_printable_area
                )
                if not loaded_image:
                    p.error(f'Invalid image "{i}"')
                dst = Image.new(
                    "RGB",
                    (loaded_image.width + image.width, height_of_the_image),
                    "white"
                )
                dst.paste(loaded_image, (args.x_merge, args.y_merge))
                dst.paste(image, (loaded_image.width, 0))
                image = dst
            # Convert the image to binary
            draw = ImageDraw.Draw(image)

        if args.lines:
            # Draw ruler (in)
            draw.text(
                (0, 1), "in",
                anchor="la",
                fill="magenta"
            )
            x = -1
            i = 0
            while x < image.width:
                if x > 0:
                    draw.line(  # top
                        (
                            int(x), print_border - (4 if i % 4 else 9),
                            int(x), print_border - 2
                        ),
                        fill="magenta", width=2
                    )
                x += 43.18
                i += 1
            # Draw ruler (cm)
            draw.text(
                (0, 76), "cm",
                anchor="la",
                fill="magenta"
            )
            x = -1
            i = 0
            while x < image.width:
                if x > 0:
                    draw.line(
                        (
                            int(x), height_of_the_image - print_border + 1,
                            int(x), height_of_the_image - print_border
                            + (5 if i % 10 else 9)
                        ),
                        fill="magenta", width=2
                    )
                x += 68
                i += 1
            # Draw a dotted horizontal line over the top border and below the bottom border of the printable area
            for x in range(0, image.width, 5):
                draw.line(  # top
                    (x, print_border - 1, x + 1, print_border - 1),
                    fill="red", width=1
                )
                draw.line(
                    (  # bottom
                        x, height_of_the_image - print_border,
                        x + 1, height_of_the_image - print_border
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

        # Convert to greyscale and rotate/invert/mirror the image
        rotated_image = ImageOps.invert(
            image.convert('L', dither=Image.Dither.FLOYDSTEINBERG)
            .rotate(-90, expand=True, resample=Image.BICUBIC)
        )
        rotated_image = ImageOps.mirror(rotated_image)

        # Manual binarization with a threshold (smoother control of artifacts)
        bin_image = rotated_image.point(lambda p: p > args.threshold and 255)

        # Convert to '1' mode (binary image)
        binary_img = bin_image.convert('1')

        # Add padding to increase the height from height_of_the_image to 128
        # (similar to the last part of read_png() code in labelmaker_encode.py)
        w, h = binary_img.size
        padded = Image.new('1', (128, h))
        x, y = (128 - w) // 2, 0
        nw, nh = x + w, y + h
        padded.paste(binary_img, (x, y, nw, nh))

        # Compute tape length and print duration
        print_length = padded.size[1] * 0.149  # mm
        print(
            "Length of the printed tape:",
            "%.1f" % (print_length / 10),
            "cm = %.1f" % (print_length / 10 / 2.54),
            "in, printed in",
            "%.1f" % (print_length / 20),
            "sec."
        )
        print_length += (25 + 1)  # 2.5 cm of wasted tape before, 1 mm after
        print(
            "Length of the used tape (adding header and footer):",
            "%.1f" % (print_length / 10),
            "cm = %.1f" % (print_length / 10 / 2.54),
            "in, printed in",
            "%.1f" % (print_length / 20),
            "sec."
        )

        # Check max tape length
        if print_length > 499:
            print("Print length exceeding 49.9 cm = 19.6 in")
            quit()

        # Image save and show
        if args.save:
            print(f'Saving image "{args.save}".')
            image.save(args.save)
            if args.no_print:
                quit()
        if args.show:
            image.show()
            if not args.show_conv and args.no_print:
                quit()
        if args.show_conv:
            padded.show()
            if args.no_print:
                quit()

        data = padded.tobytes()

    # Similar to main() in labelmaker.py
    try:
        ser = serial.Serial(args.comport, timeout=5)
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
    except serial.SerialTimeoutException:
        p.error("Timeout while communicating with printer. Please check connection and try again.")
    finally:
        # Initialize
        reset_printer(ser)

if __name__ == "__main__":
    main()
