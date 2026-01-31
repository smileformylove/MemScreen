#!/usr/bin/env python3
"""
MemScreen Logo Generator

Generates a professional PNG logo for MemScreen project.
Usage: python generate_logo.py
"""

from PIL import Image, ImageDraw, ImageFont
import os
import math

def draw_owl(draw, x, y, size=60):
    """Draw a cute owl mascot."""
    # Body
    body_color = '#06D6A0'
    draw.ellipse([x, y, x + size, y + size * 1.2], fill=body_color, outline='white', width=2)

    # Eyes (big circles)
    eye_radius = size // 5
    eye_y = y + size // 3
    # Left eye
    draw.ellipse([x + size//4 - eye_radius, eye_y - eye_radius,
                  x + size//4 + eye_radius, eye_y + eye_radius],
                 fill='white', outline='white', width=2)
    # Right eye
    draw.ellipse([x + size*3//4 - eye_radius, eye_y - eye_radius,
                  x + size*3//4 + eye_radius, eye_y + eye_radius],
                 fill='white', outline='white', width=2)

    # Pupils
    pupil_radius = eye_radius // 2
    draw.ellipse([x + size//4 - pupil_radius, eye_y - pupil_radius,
                  x + size//4 + pupil_radius, eye_y + pupil_radius],
                 fill='#1a1a2e')
    draw.ellipse([x + size*3//4 - pupil_radius, eye_y - pupil_radius,
                  x + size*3//4 + pupil_radius, eye_y + pupil_radius],
                 fill='#1a1a2e')

    # Beak
    beak_y = eye_y + eye_radius + 5
    draw.polygon([
        (x + size//2, beak_y),
        (x + size//2 - 8, beak_y + 15),
        (x + size//2 + 8, beak_y + 15)
    ], fill='#FFD93D')

    # Feet
    draw.ellipse([x + size//3, y + size * 1.15, x + size//3 + 10, y + size * 1.25], fill='#FFD93D')
    draw.ellipse([x + size*2//3 - 10, y + size * 1.15, x + size*2//3, y + size * 1.25], fill='#FFD93D')

    # Ears/tufts
    draw.polygon([
        (x + 5, y + 5),
        (x + 15, y - 10),
        (x + 25, y + 5)
    ], fill=body_color, outline='white', width=1)
    draw.polygon([
        (x + size - 25, y + 5),
        (x + size - 15, y - 10),
        (x + size - 5, y + 5)
    ], fill=body_color, outline='white', width=1)


def draw_simple_owl(draw, center_x, center_y, size):
    """Draw a simplified cute owl for circular logo."""
    # Body (ellipse)
    body_height = int(size * 0.85)
    body_width = int(size * 0.75)
    draw.ellipse([center_x - body_width//2, center_y - body_height//2,
                   center_x + body_width//2, center_y + body_height//2],
                  fill='#06D6A0', outline='white', width=2)

    # Eyes
    eye_radius = size // 7
    eye_y = center_y - size // 10
    # Left eye
    draw.ellipse([center_x - size//4 - eye_radius, eye_y - eye_radius,
                  center_x - size//4 + eye_radius, eye_y + eye_radius],
                 fill='white', outline='white', width=2)
    # Right eye
    draw.ellipse([center_x + size//4 - eye_radius, eye_y - eye_radius,
                  center_x + size//4 + eye_radius, eye_y + eye_radius],
                 fill='white', outline='white', width=2)

    # Pupils (looking at screen)
    pupil_radius = eye_radius // 2
    draw.ellipse([center_x - size//4 - pupil_radius, eye_y - pupil_radius,
                  center_x - size//4 + pupil_radius, eye_y + pupil_radius],
                 fill='#0f0f23')
    draw.ellipse([center_x + size//4 - pupil_radius, eye_y - pupil_radius,
                  center_x + size//4 + pupil_radius, eye_y + pupil_radius],
                 fill='#0f0f23')

    # Beak (small triangle)
    beak_y = eye_y + eye_radius + 3
    draw.polygon([
        (center_x, beak_y),
        (center_x - 6, beak_y + 10),
        (center_x + 6, beak_y + 10)
    ], fill='#FFD93D')

    # Ears/tufts (small)
    draw.polygon([
        (center_x - body_width//2 + 5, center_y - body_height//2 + 5),
        (center_x - body_width//2 + 12, center_y - body_height//2 - 8),
        (center_x - body_width//2 + 20, center_y - body_height//2 + 5)
    ], fill='#06D6A0', outline='white', width=1)
    draw.polygon([
        (center_x + body_width//2 - 20, center_y - body_height//2 + 5),
        (center_x + body_width//2 - 12, center_y - body_height//2 - 8),
        (center_x + body_width//2 - 5, center_y - body_height//2 + 5)
    ], fill='#06D6A0', outline='white', width=1)


def draw_circular_text(draw, text, center_x, center_y, radius, font, color, start_angle=-90):
    """Draw text along a circular path."""
    text = text.upper()
    total_chars = len(text)

    # Calculate angle per character
    angle_per_char = 140 / total_chars  # Spread over 140 degrees at top

    for i, char in enumerate(text):
        # Calculate angle for this character (spread across top of circle)
        angle = math.radians(start_angle + i * angle_per_char)

        # Calculate character position on circle
        char_x = center_x + radius * math.cos(angle)
        char_y = center_y + radius * math.sin(angle)

        # Create a new image for rotation
        char_img = Image.new('RGBA', (60, 60), (0, 0, 0, 0))
        char_draw = ImageDraw.Draw(char_img)

        # Draw character
        char_draw.text((30, 30), char, font=font, fill=color)

        # Rotate character to align with circle (perpendicular to radius)
        rotation = math.degrees(angle) + 90
        rotated_char = char_img.rotate(-rotation, expand=True, center=(30, 30))

        # Calculate paste position
        paste_x = int(char_x - rotated_char.width // 2)
        paste_y = int(char_y - rotated_char.height // 2)

        # Paste onto main image (need to handle RGBA)
        if draw.im:
            # For simple cases, just draw the text directly without rotation
            draw.text((char_x - 10, char_y - 15), char, font=font, fill=color)


def generate_circular_logo(size=500, output_path='logo.png'):
    """Generate a minimal circular logo with clean layout."""

    # Create square image
    img = Image.new('RGB', (size, size), color='#0f0f23')
    draw = ImageDraw.Draw(img)

    center = size // 2
    radius = max(size // 2 - int(size * 0.16), 20)  # Scaled margin, minimum 20px

    # Draw outer ring (thick green)
    draw.ellipse([center - radius, center - radius,
                   center + radius, center + radius],
                  outline='#06D6A0', width=8)

    # Draw inner ring (thin blue accent) - more spacing for depth
    inner_gap = 15
    draw.ellipse([center - radius + inner_gap, center - radius + inner_gap,
                   center + radius - inner_gap, center + radius - inner_gap],
                  outline='#118AB2', width=3)

    # Draw owl in upper center (make owl even larger)
    owl_size = size // 2.5
    owl_y = center - 20  # Moved down slightly
    draw_simple_owl(draw, center, owl_y, owl_size)

    # Add "MemScreen" text horizontally below the owl (make text smaller)
    try:
        font_size = max(int(size * 0.075), 14)  # Smaller font size
        font = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', font_size)
    except:
        font = ImageFont.load_default()

    text = "MemScreen"
    text_y = owl_y + owl_size // 2 + 8  # Moved text up (was +15)

    # Get text dimensions for centering
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_x = center - text_width // 2

    # Draw text with shadow
    draw.text((text_x + 2, text_y + 2), text, font=font, fill='#000000')
    draw.text((text_x, text_y), text, font=font, fill='#06D6A0')

    img.save(output_path, 'PNG', optimize=True)
    print(f"✅ Circular logo generated: {output_path}")
    print(f"   Size: {size}x{size}px")

    return img


def generate_logo(width=1200, height=400, output_path='logo.png'):
    """Generate MemScreen logo as PNG image."""

    # Create image with dark gradient background
    img = Image.new('RGB', (width, height), color='#0f0f23')
    draw = ImageDraw.Draw(img)

    # Try to use a nice font, fallback to default if not available
    try:
        # Try different font options
        font_options = [
            '/System/Library/Fonts/Helvetica.ttc',  # macOS
            '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',  # Linux
            'C:\\Windows\\Fonts\\segoeui.ttf',  # Windows
            'arial.ttf'
        ]

        title_font = None
        for font_path in font_options:
            if os.path.exists(font_path):
                try:
                    title_font = ImageFont.truetype(font_path, 72)
                    break
                except:
                    continue

        if title_font is None:
            title_font = ImageFont.load_default()

        subtitle_font = ImageFont.truetype(font_path, 32) if title_font != ImageFont.load_default() else ImageFont.load_default()
        tagline_font = ImageFont.truetype(font_path, 24) if title_font != ImageFont.load_default() else ImageFont.load_default()

    except Exception as e:
        print(f"Font loading warning: {e}")
        title_font = ImageFont.load_default()
        subtitle_font = ImageFont.load_default()
        tagline_font = ImageFont.load_default()

    # Color scheme
    primary_color = '#06D6A0'  # Teal green
    secondary_color = '#118AB2'  # Blue
    text_color = '#ffffff'
    border_color = '#457B9D'

    # Draw decorative border with rounded corners effect
    border_margin = 15
    draw.rectangle(
        [border_margin, border_margin, width - border_margin, height - border_margin],
        outline=border_color,
        width=2
    )

    # Draw owl mascot on the left
    owl_x = 80
    owl_y = height // 2 - 50
    draw_owl(draw, owl_x, owl_y, size=90)

    # Draw "MemScreen" text (shifted right to make room for owl)
    title_text = "MemScreen"
    title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
    title_width = title_bbox[2] - title_bbox[0]
    title_x = owl_x + 140  # Shifted right
    title_y = 110

    # Draw text shadow with more blur effect
    for offset in range(4, 0, -1):
        alpha = int(30 * (5 - offset) / 4)
        draw.text((title_x + offset, title_y + offset), title_text, font=title_font, fill='#000000')

    # Draw main text with gradient effect (bright green to teal)
    draw.text((title_x, title_y), title_text, font=title_font, fill='#00FFB4')

    # Draw decorative screen icon next to text
    screen_x = title_x + title_width + 30
    screen_y = title_y + 10
    screen_size = 50
    # Monitor frame
    draw.rectangle([screen_x, screen_y, screen_x + screen_size, screen_y + screen_size * 0.7],
                   outline=primary_color, width=3)
    # Screen content (gradient lines)
    for i in range(3):
        line_y = screen_y + 15 + i * 12
        draw.rectangle([screen_x + 8, line_y, screen_x + screen_size - 8, line_y + 6],
                      fill=secondary_color)
    # Monitor stand
    draw.rectangle([screen_x + screen_size//2 - 5, screen_y + screen_size * 0.7,
                    screen_x + screen_size//2 + 5, screen_y + screen_size * 0.7 + 10],
                   fill=border_color)

    # Draw subtitle
    subtitle_text = "AI-Powered Visual Memory"
    subtitle_bbox = draw.textbbox((0, 0), subtitle_text, font=subtitle_font)
    subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
    subtitle_x = title_x + 10
    subtitle_y = title_y + 90

    # Subtle shadow
    draw.text((subtitle_x + 2, subtitle_y + 2), subtitle_text, font=subtitle_font, fill='#00000055')
    draw.text((subtitle_x, subtitle_y), subtitle_text, font=subtitle_font, fill=secondary_color)

    # Draw tagline
    tagline_text = "100% Local • 100% Private"
    tagline_bbox = draw.textbbox((0, 0), tagline_text, font=tagline_font)
    tagline_width = tagline_bbox[2] - tagline_bbox[0]
    tagline_x = title_x + 10
    tagline_y = subtitle_y + 50

    draw.text((tagline_x, tagline_y), tagline_text, font=tagline_font, fill='#ffffff')

    # Add decorative elements - modern corner accents
    corner_size = 20
    corner_offset = 30

    # Top left corner
    draw.rectangle([corner_offset, corner_offset, corner_offset + corner_size, corner_offset + 4],
                   fill=primary_color)
    draw.rectangle([corner_offset, corner_offset, corner_offset + 4, corner_offset + corner_size],
                   fill=primary_color)

    # Top right corner
    draw.rectangle([width - corner_offset - corner_size, corner_offset,
                    width - corner_offset, corner_offset + 4],
                   fill=primary_color)
    draw.rectangle([width - corner_offset - 4, corner_offset,
                    width - corner_offset, corner_offset + corner_size],
                   fill=primary_color)

    # Bottom left corner
    draw.rectangle([corner_offset, height - corner_offset - 4,
                    corner_offset + corner_size, height - corner_offset],
                   fill=secondary_color)
    draw.rectangle([corner_offset, height - corner_offset - corner_size,
                    corner_offset + 4, height - corner_offset],
                   fill=secondary_color)

    # Bottom right corner
    draw.rectangle([width - corner_offset - corner_size, height - corner_offset - 4,
                    width - corner_offset, height - corner_offset],
                   fill=secondary_color)
    draw.rectangle([width - corner_offset - 4, height - corner_offset - corner_size,
                    width - corner_offset, height - corner_offset],
                   fill=secondary_color)

    # Add subtle glow effect around the owl
    for i in range(10):
        alpha = int(15 * (10 - i) / 10)
        glow_size = 90 + i * 4
        # We can't do real alpha with PIL's basic draw, so we skip this for simplicity

    # Save the image
    img.save(output_path, 'PNG', optimize=True)
    print(f"✅ Logo generated successfully: {output_path}")
    print(f"   Size: {width}x{height}px")
    print(f"   Format: PNG")

    return img

def generate_small_logo(output_path='logo_small.png'):
    """Generate a smaller version for badges/icons."""
    img = generate_logo(width=300, height=100, output_path=output_path)
    return img

def generate_favicon(output_path='favicon.png'):
    """Generate a favicon-sized logo with owl."""
    img = Image.new('RGB', (64, 64), color='#0f0f23')
    draw = ImageDraw.Draw(img)

    # Draw a mini owl in center
    owl_size = 50
    x = (64 - owl_size) // 2
    y = (64 - int(owl_size * 1.2)) // 2

    # Body
    draw.ellipse([x, y, x + owl_size, y + int(owl_size * 1.2)],
                 fill='#06D6A0', outline='white', width=1)

    # Eyes
    eye_radius = 6
    eye_y = y + owl_size // 3
    draw.ellipse([x + owl_size//4 - eye_radius, eye_y - eye_radius,
                  x + owl_size//4 + eye_radius, eye_y + eye_radius],
                 fill='white')
    draw.ellipse([x + owl_size*3//4 - eye_radius, eye_y - eye_radius,
                  x + owl_size*3//4 + eye_radius, eye_y + eye_radius],
                 fill='white')

    # Pupils
    pupil_radius = 3
    draw.ellipse([x + owl_size//4 - pupil_radius, eye_y - pupil_radius,
                  x + owl_size//4 + pupil_radius, eye_y + pupil_radius],
                 fill='#0f0f23')
    draw.ellipse([x + owl_size*3//4 - pupil_radius, eye_y - pupil_radius,
                  x + owl_size*3//4 + pupil_radius, eye_y + pupil_radius],
                 fill='#0f0f23')

    # Beak
    beak_y = eye_y + eye_radius + 2
    draw.polygon([
        (x + owl_size//2, beak_y),
        (x + owl_size//2 - 4, beak_y + 8),
        (x + owl_size//2 + 4, beak_y + 8)
    ], fill='#FFD93D')

    img.save(output_path, 'PNG', optimize=True)
    print(f"✅ Favicon generated: {output_path}")

if __name__ == '__main__':
    print("🎨 Generating MemScreen logos...\n")

    # Generate main circular logo (large)
    generate_circular_logo(size=500, output_path='assets/logo.png')

    # Generate medium circular logo
    generate_circular_logo(size=300, output_path='assets/logo_medium.png')

    # Generate small circular logo
    generate_circular_logo(size=150, output_path='assets/logo_small.png')

    # Generate favicon (already circular owl)
    generate_favicon('assets/favicon.png')

    print("\n✨ All logos generated successfully!")
    print("📁 Location: assets/ directory")
