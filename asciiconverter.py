#!/usr/bin/env python3
"""
Alex Eidt

Converts videos/images into ASCII video/images in various formats.
"""

import argparse
import json
import os
import sys

import imageio
import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from tqdm import tqdm as ProgressBar


def get_font_bitmaps(fontsize, boldness, reverse, background, chars, font):
    """
    Returns a list of font bitmaps.

    Parameters
        fontsize    - Font size to use for ASCII characters.
        boldness    - Stroke size to use when drawing ASCII characters.
        reverse     - Reverse the ordering of the ASCII characters.
        background  - Background color.
        chars       - ASCII characters to use in media.
        font        - Font to use.

    Returns
        List of font bitmaps corresponding to the characters in 'chars'.
    """
    bitmaps = {}
    min_width = min_height = float("inf")
    font_ttf = ImageFont.truetype(font, size=fontsize)

    for char in chars:
        if char in bitmaps:
            continue
        w, h = font_ttf.getsize(char)
        min_width, min_height = min(min_width, w), min(min_height, h)
        # Draw font character as a w x h image.
        image = Image.new("RGB", (w, h), (background,) * 3)
        draw = ImageDraw.Draw(image)
        draw.text(
            (0, -(fontsize // 6)),
            char,
            fill=(255 - background,) * 3,
            font=font_ttf,
            stroke_width=boldness,
        )
        bitmap = np.array(image)
        if background == 255:
            np.subtract(255, bitmap, out=bitmap)
        bitmaps[char] = bitmap.astype(np.uint8)

    # Crop the font bitmaps to all have the same dimensions based on the
    # minimum font width and height of all font bitmaps.
    fonts = [bitmaps[char][: int(min_height), : int(min_width)] for char in chars]
    # Sort font bitmaps by pixel density.
    fonts.sort(key=lambda x: x.sum(), reverse=not reverse)
    return np.array(fonts)


def get_text_matrix(buffer, chars):
    # Create an empty list to store rows of text
    text_matrix = []

    # Iterate over each row in the buffer array
    for row in buffer:
        # Create an empty string to store characters for the current row
        row_text = ""

        # Iterate over each pixel value in the row and map it to the corresponding ASCII character
        for pixel in row:
            # Extract the intensity value from the pixel
            intensity = int(pixel[0])

            # Ensure the intensity value is within the range of the chars array
            if intensity < len(chars):
                # Append the corresponding ASCII character to row_text
                row_text += chars[intensity]
            else:
                # If the intensity value exceeds the length of chars, append a placeholder character
                row_text += " "

        # Append the row_text string to the text_matrix list
        text_matrix.append(row_text)

    # Return the text_matrix as a list of strings
    return text_matrix


def draw_ascii(frame, chars, background, clip, monochrome, font_bitmaps, buffer=None):
    """
    Draws an ASCII Image.

    Parameters
        frame           - Numpy array representing image. Must be 3 channels RGB.
        chars           - ASCII characters to use in media.
        background      - Background color.
        clip            - Clip characters to not go outside of image bounds.
        monochrome      - Color to use for monochromatic. None if not monochromatic.
        font_bitmaps    - List of font bitmaps.
        buffer          - Optional buffer for intermediary calculations.
                          Must have shape: ((h // fh + 1) * fh, (w // fw + 1) * fw, 3) where
                          h, w are the height and width of the frame and fw, fh are the font width and height.

    NOTE: Characters such as q, g, y, etc... are not rendered properly in this implementation
    due to the lower ends being cut off.
    """
    # fh -> font height, fw -> font width.
    fh, fw = font_bitmaps[0].shape[:2]
    # oh -> Original height, ow -> Original width.
    oh, ow = frame.shape[:2]
    # Sample original frame at steps of font width and height.
    frame = frame[::fh, ::fw]
    h, w = frame.shape[:2]

    if buffer is None:
        buffer = np.empty(
            (h * fh, w * fw, 3), dtype=np.uint16 if len(chars) < 32 else np.uint32
        )

    buffer_view = buffer[:h, :w]
    if len(monochrome) != 0:
        buffer_view[:] = 1
        if background == 255:
            monochrome = 255 - monochrome
        np.multiply(buffer_view, monochrome, out=buffer_view)
    else:
        if background == 255:
            np.subtract(255, frame, out=buffer_view)
        else:
            buffer_view[:] = frame

    colors = buffer_view.repeat(fw, 1).astype(np.uint16, copy=False).repeat(fh, 0)

    # Grayscale original frame and normalize to ASCII index.
    buffer_view = buffer_view[..., 0]
    np.sum(frame * np.array([3, 4, 1]), axis=2, dtype=buffer.dtype, out=buffer_view)
    buffer_view *= len(chars)
    buffer_view >>= 11
    # print(buffer_view.shape)
    # print(buffer_view)
    # print(buffer_view[32])
    # print((buffer_view[32]))

    charlist = []
    for j in buffer_view:
        char_view = ""
        for i in j:
            char_view += chars[i]
        charlist.append(char_view)
        # print(char_view)

    # Create a new list with each font bitmap based on the grayscale value.
    image = (
        font_bitmaps[buffer_view].transpose(0, 2, 1, 3, 4).reshape(h * fh, w * fw, 3)
    )

    if clip:
        colors = colors[:oh, :ow]
        image = image[:oh, :ow]
        buffer = buffer[:oh, :ow]

    np.multiply(image, colors, out=buffer)
    np.floor_divide(buffer, 255, out=buffer)
    buffer = buffer.astype(np.uint8, copy=False)
    if background == 255:
        np.subtract(255, buffer, out=buffer)
    return buffer, charlist


def ascii_video(
    filename,
    output,
    chars,
    monochrome,
    fontsize=20,
    boldness=2,
    reverse=False,
    background=255,
    clip=True,
    font="cour.ttf",
    audio=False,
    quality=5,
):
    font_bitmaps = get_font_bitmaps(
        fontsize, boldness, reverse, background, chars, font
    )

    video = imageio_ffmpeg.read_frames(filename)
    data = next(video)

    w, h = data["size"]
    frame_size = (h, w, 3)
    # Read and convert first frame to figure out frame size.
    first_frame = np.frombuffer(next(video), dtype=np.uint8).reshape(frame_size)
    first_frame, first_charlist = draw_ascii(
        first_frame, chars, background, clip, monochrome, font_bitmaps
    )

    # Smaller data types can speed up operations. The minimum data type required will be
    # 2^n / (255 * 8) > len(chars) where n = 16 or 32.
    buffer = np.empty_like(
        first_frame, dtype=np.uint16 if len(chars) < 32 else np.uint32
    )
    h, w = first_frame.shape[:2]

    kwargs = {"fps": data["fps"], "quality": int(min(max(quality, 0), 10))}
    if audio:
        kwargs["audio_path"] = filename

    writer = imageio_ffmpeg.write_frames(output, (w, h), **kwargs)
    writer.send(None)
    writer.send(first_frame)
    del first_frame

    image_csv_list = [first_charlist]
    for frame in ProgressBar(video, total=int(data["fps"] * data["duration"] - 0.5)):
        frame = np.frombuffer(frame, dtype=np.uint8).reshape(frame_size)
        buffer_color, charlist = draw_ascii(
            frame, chars, background, clip, monochrome, font_bitmaps, buffer
        )
        image_csv_list.append(charlist)
        writer.send(buffer_color)
    writer.close()

    json_data = json.dumps(image_csv_list)

    # Write the JSON data to a file
    with open("tomato.json", "w") as json_file:
        json_file.write(json_data)
    # csv.writer(open("tomato" + ".csv", "w")).writerows(image_csv_list)
    # output_dir = "text"
    # os.makedirs(output_dir, exist_ok=True)
    # frame_count = 0
    # for frame in ProgressBar(video, total=int(data["fps"] * data["duration"] - 0.5)):
    #     frame = np.frombuffer(frame, dtype=np.uint8).reshape(frame_size)
    #     ascii_frame = draw_ascii(
    #         frame, chars, background, clip, monochrome, font_bitmaps, buffer
    #     )

    #     # Save the ASCII frame as a text file
    #     output_file = os.path.join(output_dir, f"frame_{frame_count:05d}.txt")
    #     print(output_file)
    #     with open(output_file, "w") as f:
    #         for row in ascii_frame:
    #             print(row)
    #             f.write("".join(chars[int(pixel)] for pixel in row) + "\n")

    #     frame_count += 1


def ascii_image(
    filename,
    output,
    chars,
    monochrome,
    fontsize=20,
    boldness=2,
    reverse=False,
    background=255,
    clip=True,
    font="cour.ttf",
):
    image = imageio.imread(filename)[:, :, :3]
    font_bitmaps = get_font_bitmaps(
        fontsize, boldness, reverse, background, chars, font
    )
    image, _ = draw_ascii(image, chars, background, clip, monochrome, font_bitmaps)
    imageio.imsave(output, image)


def parse_args():
    parser = argparse.ArgumentParser(description="Blazing fast ASCII Media converter.")

    parser.add_argument("filename", help="File name of the input image.")
    parser.add_argument("output", help="File name of the output image.")

    parser.add_argument(
        "-chars",
        "--characters",
        help="ASCII chars to use in media.",
        default="@%#*+=-:. ",
    )
    parser.add_argument(
        "-r", "--reverse", help="Reverse the character order.", action="store_true"
    )
    parser.add_argument("-f", "--fontsize", help="Font size.", type=int, default=20)
    parser.add_argument(
        "-b",
        "--bold",
        help="Boldness of characters. Recommended: 1/10 font size.",
        type=int,
        default=2,
    )
    parser.add_argument(
        "-bg",
        "--background",
        help="Background color. Must be 255 (white) or 0 (black).",
        type=int,
        default=255,
    )
    parser.add_argument(
        "-m",
        "--monochrome",
        help='Color to use for Monochromatic characters in "R,G,B" format.',
    )
    parser.add_argument(
        "-c",
        "--clip",
        help="Clip characters to not go outside of image bounds.",
        action="store_false",
    )
    parser.add_argument(
        "-font", "--font", help="Font to use.", type=str, default="cour.ttf"
    )
    parser.add_argument(
        "-a",
        "--audio",
        help="Add audio from the input file to the output file.",
        action="store_true",
    )
    parser.add_argument(
        "-q",
        "--quality",
        help="Quality of the output video. (0-10), 0 worst, 10 best.",
        type=int,
        default=5,
    )

    return parser.parse_args()


def convert_ascii(args, filename, output, chars, monochrome):
    try:
        imageio.imread(filename)
    except Exception:
        ascii_video(
            filename,
            output,
            chars,
            monochrome,
            args.fontsize,
            args.bold,
            args.reverse,
            args.background,
            args.clip,
            args.font,
            args.audio,
            args.quality,
        )
    else:
        ascii_image(
            filename,
            output,
            chars,
            monochrome,
            args.fontsize,
            args.bold,
            args.reverse,
            args.background,
            args.clip,
            args.font,
        )


def main():
    args = parse_args()

    assert args.fontsize > 0, "Font size must be > 0."
    assert args.bold >= 0, "Boldness must be >= 0."
    assert args.background in [0, 255], "Background must be either 0 or 255."

    chars = np.array(list(args.characters))
    monochrome = np.array(
        list(map(int, args.monochrome.split(","))) if args.monochrome else [],
        dtype=np.uint16,
    )

    if os.path.isdir(args.filename):
        os.makedirs(args.output, exist_ok=True)
        for filename in ProgressBar(os.listdir(args.filename)):
            path = os.path.join(args.filename, filename)
            output = os.path.join(args.output, filename)
            convert_ascii(args, path, output, chars, monochrome)
    else:
        convert_ascii(args, args.filename, args.output, chars, monochrome)


if __name__ == "__main__":
    main()
