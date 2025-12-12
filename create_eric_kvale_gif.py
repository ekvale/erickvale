"""
Animated ASCII Art GIF - ERIC KVALE

Creates a looping GIF that builds up the name ERIC KVALE using ASCII characters

Slower animation than the DHALGREN version
"""

from PIL import Image, ImageDraw, ImageFont
import math


def create_eric_kvale_ascii_gif():
    """Create an animated ASCII GIF that spells ERIC KVALE"""
    
    # Configuration - Higher resolution for better quality
    width = 1200
    height = 600
    bg_color = '#1a1a2e'  # Dark background
    text_color = '#e94560'  # Pink/red color (same as Dhalgren)
    
    # Font setup - Larger font for better visibility
    try:
        # Try to use a monospace font for ASCII art feel
        font_size = 90  # Increased from 65
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", font_size)
        small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 14)  # Slightly larger
    except:
        font = ImageFont.load_default()
        small_font = ImageFont.load_default()
    
    # The name we're building
    name = "ERIC KVALE"
    
    # ASCII characters to use in the animation
    ascii_chars = ['@', '#', '$', '%', '&', '*', '+', '=', '-', ':', '.', ' ']
    
    frames = []
    # Extended phases - longer ASCII snow, no fade out
    total_frames = 200
    
    # Phase 1: Random ASCII snow (frames 0-60) - EXTENDED from 30
    # Phase 2: Letters appearing one by one (frames 60-160) - Extended
    # Phase 3: Final name stable (frames 160-200) - Hold at end, no fade
    
    for frame_num in range(total_frames):
        # Create new frame
        img = Image.new('RGB', (width, height), color=bg_color)
        draw = ImageDraw.Draw(img)
        
        # Determine which phase we're in
        if frame_num < 60:
            # Phase 1: Random ASCII snow (EXTENDED - 60 frames)
            progress = frame_num / 60
            
            # Draw random ASCII characters in a grid
            for y in range(0, height, 20):
                for x in range(0, width, 15):
                    if hash((x, y, frame_num)) % 100 < 20:  # 20% density
                        char = ascii_chars[hash((x, y, frame_num)) % len(ascii_chars)]
                        alpha = int(100 * progress)  # Fade in
                        color = f'#{alpha:02x}{alpha:02x}{alpha:02x}'
                        draw.text((x, y), char, font=small_font, fill=color)
        
        elif frame_num < 160:
            # Phase 2: Letters appearing one by one
            progress = (frame_num - 60) / 100  # 100 frames for letter building
            
            # Calculate how many letters to show
            letters_to_show = int(progress * len(name)) + 1
            letters_to_show = min(letters_to_show, len(name))
            
            # For each letter, draw it being "constructed" from ASCII
            current_name = name[:letters_to_show]
            
            # Calculate centered position
            bbox = font.getbbox(name)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            start_x = (width - text_width) // 2
            start_y = (height - text_height) // 2
            
            # Draw each letter with effects
            x_offset = start_x
            for i, letter in enumerate(current_name):
                # Calculate letter progress (SLOWER per letter)
                letter_progress = (progress * len(name) - i)
                letter_progress = max(0, min(1, letter_progress))
                
                # Get letter bounds
                letter_bbox = font.getbbox(letter)
                letter_width = letter_bbox[2] - letter_bbox[0]
                letter_height = letter_bbox[3] - letter_bbox[1]
                
                if letter == ' ':
                    # Just add space for the space character
                    x_offset += letter_width
                    continue
                
                if letter_progress < 1:
                    # Letter is still being constructed (SLOWER BUILD)
                    # Draw ASCII characters morphing into the letter
                    density = int(letter_progress * 100)
                    
                    for dy in range(0, letter_height, 3):
                        for dx in range(0, letter_width, 3):
                            if hash((dx, dy, i, frame_num)) % 100 < density:
                                char = ascii_chars[hash((dx, dy, i)) % (len(ascii_chars) - 3)]
                                draw.text((x_offset + dx, start_y + dy), char, 
                                         font=small_font, fill=text_color)
                    
                    # Fade in the actual letter (SLOWER)
                    alpha_val = int(letter_progress * 233) + 22  # 22-255 range
                    letter_color = f'#{alpha_val:02x}{int(alpha_val*0.27):02x}{int(alpha_val*0.38):02x}'  # Pink/red
                    draw.text((x_offset, start_y), letter, font=font, fill=letter_color)
                else:
                    # Letter is fully formed
                    draw.text((x_offset, start_y), letter, font=font, fill=text_color)
                
                x_offset += letter_width + 3
        
        else:
            # Phase 3: Stable name - hold at end (no fade, plays once)
            # Draw complete name
            bbox = font.getbbox(name)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            start_x = (width - text_width) // 2
            start_y = (height - text_height) // 2
            
            draw.text((start_x, start_y), name, font=font, fill=text_color)
        
        # Add subtle title at bottom
        if frame_num >= 100 and frame_num < 180:
            subtitle_alpha = min(255, int((frame_num - 100) * 4))  # Fade in during letter building
            if frame_num >= 160:
                subtitle_alpha = 255  # Keep at full opacity in final phase
            
            subtitle_color = f'#{subtitle_alpha:02x}{subtitle_alpha:02x}{subtitle_alpha:02x}'
            subtitle = "Hermeneutic Learning Cartographer | Spaceship Earth"
            
            try:
                subtitle_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
            except:
                subtitle_font = small_font
            
            subtitle_bbox = subtitle_font.getbbox(subtitle)
            subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
            subtitle_x = (width - subtitle_width) // 2
            draw.text((subtitle_x, height - 60), subtitle, font=subtitle_font, fill=subtitle_color)
        
        frames.append(img)
    
    # Save as GIF
    output_path = './eric_kvale_ascii_animation.gif'
    
    # Use all frames for smooth animation (higher resolution needs it)
    # Could reduce to every frame for smaller file, but quality is priority
    
    frames[0].save(
        output_path,
        save_all=True,
        append_images=frames[1:],
        duration=80,  # 80ms per frame
        loop=1,  # Play once (loop=1 means play once, then stop)
        optimize=True
    )
    
    print(f"✓ Created animated GIF: {output_path}")
    print(f"  Frames: {len(frames)}")
    print(f"  Duration: ~{len(frames) * 80 / 1000:.1f} seconds (plays once)")
    print(f"  Size: {width}x{height} (higher resolution)")
    print(f"  Font size: {font_size}px")
    print(f"  ASCII snow: 60 frames (extended)")
    print(f"  Loop: Once (stops at end)")
    
    return output_path


def create_eric_kvale_typewriter_gif():
    """Alternative: Typewriter effect version"""
    
    width = 900
    height = 200
    bg_color = '#1a1a2e'
    text_color = '#e94560'  # Pink/red (same as Dhalgren)
    
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 80)
    except:
        font = ImageFont.load_default()
    
    name = "ERIC KVALE"
    frames = []
    
    # Typing phase: 10 characters (including space) + cursor blinks
    for i in range(len(name) + 1):
        for blink in range(3):  # INCREASED blinks from 2 to 3
            img = Image.new('RGB', (width, height), color=bg_color)
            draw = ImageDraw.Draw(img)
            
            current_text = name[:i]
            
            # Calculate position
            bbox = font.getbbox(name)
            text_height = bbox[3] - bbox[1]
            start_y = (height - text_height) // 2
            start_x = 50
            
            # Draw text
            draw.text((start_x, start_y), current_text, font=font, fill=text_color)
            
            # Draw cursor if blinking on
            if blink == 0 and i < len(name):
                cursor_bbox = font.getbbox(current_text)
                cursor_x = start_x + (cursor_bbox[2] - cursor_bbox[0]) + 5
                draw.rectangle([cursor_x, start_y, cursor_x + 15, start_y + text_height], 
                              fill=text_color)
            
            frames.append(img)
            
            # Add more frames for the first blink state (SLOWER)
            if blink == 0:
                for _ in range(3):  # INCREASED from 2 to 3
                    frames.append(img.copy())
    
    # Hold complete name (LONGER hold)
    for _ in range(30):  # INCREASED from 20 to 30
        frames.append(frames[-1].copy())
    
    # Fade out (SLOWER)
    for fade in range(15):  # INCREASED from 10 to 15
        alpha = int(255 * (1 - fade / 15))
        img = Image.new('RGB', (width, height), color=bg_color)
        draw = ImageDraw.Draw(img)
        
        fade_color = f'#{alpha:02x}{int(alpha*0.27):02x}{int(alpha*0.38):02x}'  # Pink/red
        draw.text((start_x, start_y), name, font=font, fill=fade_color)
        frames.append(img)
    
    output_path = './eric_kvale_typewriter.gif'
    frames[0].save(
        output_path,
        save_all=True,
        append_images=frames[1:],
        duration=120,  # INCREASED from 100ms to 120ms
        loop=0,
        optimize=True
    )
    
    print(f"✓ Created typewriter GIF: {output_path}")
    print(f"  Speed: 20% slower than DHALGREN typewriter")
    return output_path


def main():
    """Create both versions"""
    print("Creating ERIC KVALE animated ASCII art GIFs...")
    print()
    
    print("1. ASCII Art Animation (50% slower letter creation):")
    ascii_path = create_eric_kvale_ascii_gif()
    
    print()
    print("2. Typewriter Animation (20% slower typing):")
    typewriter_path = create_eric_kvale_typewriter_gif()
    
    print()
    print("✓ Done! Created 2 animated GIFs")
    print()
    print("Comparison to DHALGREN versions:")
    print("  - ASCII animation: ~7.2s loop (vs 4.0s)")
    print("  - Letter creation: 50% slower")
    print("  - Color: Same pink/red (#e94560) as Dhalgren")


if __name__ == "__main__":
    main()

