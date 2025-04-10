from PIL import Image, ImageDraw, ImageSequence, ImageFont


def get_text_dimensions(text_string, font: ImageFont.FreeTypeFont) -> tuple[int, int]:
    ascent, descent = font.getmetrics()
    text_width = font.getmask(text_string).getbbox()[2]
    text_height = font.getmask(text_string).getbbox()[3] + descent
    return (text_width, text_height)


def wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: float)-> str:
    words = text.split()
    wrapped_lines = []
    current_line = ''
    for word in words:
        # Check if adding the next word exceeds the max width
        test_line = f"{current_line} {word}".strip()
        width, _ = get_text_dimensions(test_line, font)
        if width <= max_width:
            current_line = test_line
        else:
            wrapped_lines.append(current_line)
            current_line = word
    wrapped_lines.append(current_line)  # add the last line
    return "\n".join(wrapped_lines)


def build_lines(text: str, font: ImageFont.FreeTypeFont, max_width: float) -> tuple[list[tuple[str, int, int]], int]:
    """Builds a list of lines including their dimensions, and a total height."""
    wrapped_text = wrap_text(text, font, max_width)
    lines = wrapped_text.split('\n')
    lines_with_dimensions = [
        (line, *get_text_dimensions(line, font))
        for line in lines
    ]
    return (lines_with_dimensions, sum(dim[2] for dim in lines_with_dimensions))


def add_text_to_gif(input_gif, output_gif, text, font_path='arial.ttf', font_size=20):
    font = ImageFont.truetype(font_path, font_size)
    with Image.open(input_gif) as img:
        frames: list[Image.Image] = []
        img_width = img.width * 0.9  # Use 90% of the image width for text
        lines, total_lines_height = build_lines(text, font, img_width)

        for frame in ImageSequence.Iterator(img):
            # Convert the frame to work with drawing
            frame_copy = frame.copy().convert('RGBA')
            draw = ImageDraw.Draw(frame_copy)
            
            # Calculate Y position for text to be 10 pixels above the bottom
            text_y = img.height - total_lines_height - 10
            current_y = text_y

            # Draw each line
            for line, line_width, line_height in lines:
                # Center the line
                text_x = (img_width - line_width) / 2
                draw.text((text_x, current_y), line, fill=(255, 255, 255, 255), font=font)
                current_y += line_height  # Move to the next line

            frames.append(frame_copy)

        # Save the frames as a new GIF
        frames[0].save(output_gif, format="GIF", save_all=True, append_images=frames[1:], optimize=False, loop=0, duration=img.info['duration'])