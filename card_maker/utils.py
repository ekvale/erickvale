"""
Card generation utilities for creating printable card images.
"""
from PIL import Image, ImageDraw, ImageFont
import os
from django.conf import settings


def get_rarity_color(rarity):
    """Get color for rarity."""
    colors = {
        'common': '#808080',      # Gray
        'uncommon': '#00FF00',    # Green
        'rare': '#0080FF',        # Blue
        'epic': '#8000FF',        # Purple
        'legendary': '#FF8000',   # Orange
    }
    return colors.get(rarity.lower(), '#808080')


def get_font(size, bold=False):
    """Get font with fallbacks."""
    font_paths = [
        'arial.ttf',
        'Arial.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf' if bold else '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
    ]
    
    for path in font_paths:
        try:
            if os.path.exists(path):
                return ImageFont.truetype(path, size)
        except:
            continue
    
    # Fallback to default
    try:
        return ImageFont.truetype("arial.ttf", size)
    except:
        return ImageFont.load_default()


def generate_kvale_card(
    title,
    rarity='common',
    album_label='',
    energy=0,
    power=0,
    artwork_path=None,
    trigger='',
    description='',
    tags=None,
    edition='',
    collection='',
    output_path=None
):
    """
    Generate a Kvale card image with TCG-style layout.
    
    Card dimensions: 750x1050px (standard playing card size at 300 DPI)
    Layout: Stats in top corners, artwork center, description bottom
    """
    # Card dimensions
    CARD_WIDTH = 750
    CARD_HEIGHT = 1050
    BACKGROUND_COLOR = '#0F1419'
    BORDER_COLOR = '#2a2a2a'
    
    # Create base image
    img = Image.new('RGB', (CARD_WIDTH, CARD_HEIGHT), BACKGROUND_COLOR)
    draw = ImageDraw.Draw(img)
    
    # Get fonts
    font_title = get_font(40, bold=True)
    font_rarity = get_font(18, bold=True)
    font_album = get_font(11)
    font_stat_value = get_font(32, bold=True)
    font_stat_label = get_font(10)
    font_trigger = get_font(22, bold=True)
    font_description = get_font(16)
    font_tag = get_font(11)
    font_footer = get_font(11)
    
    # Get rarity color
    rarity_color = get_rarity_color(rarity)
    
    # Draw card border with rarity color
    border_width = 4
    draw.rounded_rectangle(
        [(border_width, border_width), 
         (CARD_WIDTH - border_width, CARD_HEIGHT - border_width)],
        radius=15,
        fill=BACKGROUND_COLOR,
        outline=rarity_color,
        width=border_width
    )
    
    # TOP SECTION - Stats in corners
    top_margin = 30
    corner_stat_size = 80
    corner_stat_radius = 40
    
    # Energy (top left corner)
    energy_x = 30
    energy_y = top_margin
    
    # Draw energy circle
    draw.ellipse(
        [(energy_x, energy_y),
         (energy_x + corner_stat_size, energy_y + corner_stat_size)],
        fill='#1a1a1a',
        outline=rarity_color,
        width=3
    )
    
    # Energy value
    energy_text = str(energy)
    energy_bbox = draw.textbbox((0, 0), energy_text, font=font_stat_value)
    energy_text_width = energy_bbox[2] - energy_bbox[0]
    energy_text_height = energy_bbox[3] - energy_bbox[1]
    energy_text_x = energy_x + (corner_stat_size - energy_text_width) // 2
    energy_text_y = energy_y + (corner_stat_size - energy_text_height) // 2 - 8
    draw.text((energy_text_x, energy_text_y), energy_text, fill='#FFFFFF', font=font_stat_value)
    
    # Energy label
    energy_label = "ENERGY"
    energy_label_bbox = draw.textbbox((0, 0), energy_label, font=font_stat_label)
    energy_label_width = energy_label_bbox[2] - energy_label_bbox[0]
    energy_label_x = energy_x + (corner_stat_size - energy_label_width) // 2
    energy_label_y = energy_y + corner_stat_size - 15
    draw.text((energy_label_x, energy_label_y), energy_label, fill='#808080', font=font_stat_label)
    
    # Power (top right corner)
    power_x = CARD_WIDTH - corner_stat_size - 30
    power_y = top_margin
    
    # Draw power circle
    draw.ellipse(
        [(power_x, power_y),
        (power_x + corner_stat_size, power_y + corner_stat_size)],
        fill='#1a1a1a',
        outline=rarity_color,
        width=3
    )
    
    # Power value
    power_text = str(power)
    power_bbox = draw.textbbox((0, 0), power_text, font=font_stat_value)
    power_text_width = power_bbox[2] - power_bbox[0]
    power_text_height = power_bbox[3] - power_bbox[1]
    power_text_x = power_x + (corner_stat_size - power_text_width) // 2
    power_text_y = power_y + (corner_stat_size - power_text_height) // 2 - 8
    draw.text((power_text_x, power_text_y), power_text, fill='#FFFFFF', font=font_stat_value)
    
    # Power label
    power_label = "POWER"
    power_label_bbox = draw.textbbox((0, 0), power_label, font=font_stat_label)
    power_label_width = power_label_bbox[2] - power_label_bbox[0]
    power_label_x = power_x + (corner_stat_size - power_label_width) // 2
    power_label_y = power_y + corner_stat_size - 15
    draw.text((power_label_x, power_label_y), power_label, fill='#808080', font=font_stat_label)
    
    # Title Section (centered, below stats)
    title_y = top_margin + corner_stat_size + 20
    title_text = title.upper()
    title_bbox = draw.textbbox((0, 0), title_text, font=font_title)
    title_width = title_bbox[2] - title_bbox[0]
    title_x = (CARD_WIDTH - title_width) // 2
    
    # Draw title shadow
    draw.text((title_x + 2, title_y + 2), title_text, fill='#000000', font=font_title)
    # Draw main title
    draw.text((title_x, title_y), title_text, fill='#FFFFFF', font=font_title)
    
    title_bottom = title_y + (title_bbox[3] - title_bbox[1]) + 10
    
    # Rarity Badge (below title)
    badge_width = 200
    badge_height = 35
    badge_x = (CARD_WIDTH - badge_width) // 2
    badge_y = title_bottom + 10
    
    # Draw rounded rectangle for badge
    draw.rounded_rectangle(
        [(badge_x, badge_y), (badge_x + badge_width, badge_y + badge_height)],
        radius=8,
        fill='#1a1a1a',
        outline=rarity_color,
        width=2
    )
    
    # Badge text
    badge_text = f"★ {rarity.upper()} ★"
    badge_bbox = draw.textbbox((0, 0), badge_text, font=font_rarity)
    badge_text_width = badge_bbox[2] - badge_bbox[0]
    badge_text_x = badge_x + (badge_width - badge_text_width) // 2
    badge_text_y = badge_y + (badge_height - (badge_bbox[3] - badge_bbox[1])) // 2
    draw.text((badge_text_x, badge_text_y), badge_text, fill=rarity_color, font=font_rarity)
    
    badge_bottom = badge_y + badge_height + 15
    
    # Album Label (if provided, below rarity)
    if album_label:
        album_text = album_label.upper()
        album_bbox = draw.textbbox((0, 0), album_text, font=font_album)
        album_width = album_bbox[2] - album_bbox[0]
        album_x = (CARD_WIDTH - album_width) // 2
        draw.text((album_x, badge_bottom), album_text, fill='#808080', font=font_album)
        badge_bottom += 20
    
    # Card Artwork (550x300px, centered)
    artwork_width = 550
    artwork_height = 300
    artwork_x = (CARD_WIDTH - artwork_width) // 2
    artwork_y = badge_bottom + 15
    
    # Draw frame
    draw.rounded_rectangle(
        [(artwork_x - 3, artwork_y - 3),
         (artwork_x + artwork_width + 3, artwork_y + artwork_height + 3)],
        radius=10,
        fill='#000000',
        outline=BORDER_COLOR,
        width=2
    )
    
    # Load and paste artwork
    if artwork_path and os.path.exists(artwork_path):
        try:
            artwork_img = Image.open(artwork_path)
            artwork_img = artwork_img.resize((artwork_width, artwork_height), Image.Resampling.LANCZOS)
            
            # Create mask for rounded corners
            mask = Image.new('L', (artwork_width, artwork_height), 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.rounded_rectangle(
                [(0, 0), (artwork_width, artwork_height)],
                radius=10,
                fill=255
            )
            
            img.paste(artwork_img, (artwork_x, artwork_y), mask)
        except Exception as e:
            # Placeholder if image fails to load
            draw.rounded_rectangle(
                [(artwork_x, artwork_y),
                 (artwork_x + artwork_width, artwork_y + artwork_height)],
                radius=10,
                fill='#1a1a1a',
                outline=BORDER_COLOR
            )
            placeholder_text = "ARTWORK"
            placeholder_bbox = draw.textbbox((0, 0), placeholder_text, font=font_title)
            placeholder_x = artwork_x + (artwork_width - (placeholder_bbox[2] - placeholder_bbox[0])) // 2
            placeholder_y = artwork_y + (artwork_height - (placeholder_bbox[3] - placeholder_bbox[1])) // 2
            draw.text((placeholder_x, placeholder_y), placeholder_text, fill='#404040', font=font_title)
    else:
        # Placeholder
        draw.rounded_rectangle(
            [(artwork_x, artwork_y),
             (artwork_x + artwork_width, artwork_y + artwork_height)],
            radius=10,
            fill='#1a1a1a',
            outline=BORDER_COLOR
        )
    
    # Darkening overlay for artwork
    overlay = Image.new('RGBA', (artwork_width, artwork_height), (0, 0, 0, 20))
    img.paste(overlay, (artwork_x, artwork_y), overlay)
    
    artwork_bottom = artwork_y + artwork_height + 20
    
    # Ability Trigger Bar (if provided, below artwork)
    if trigger:
        trigger_height = 40
        trigger_x = artwork_x
        trigger_y = artwork_bottom
        trigger_width = artwork_width
        
        draw.rounded_rectangle(
            [(trigger_x, trigger_y),
             (trigger_x + trigger_width, trigger_y + trigger_height)],
            radius=8,
            fill='#1a1a1a',
            outline=rarity_color,
            width=2
        )
        
        trigger_text = f"⚡ {trigger.upper()}"
        trigger_bbox = draw.textbbox((0, 0), trigger_text, font=font_trigger)
        trigger_text_width = trigger_bbox[2] - trigger_bbox[0]
        trigger_text_x = trigger_x + (trigger_width - trigger_text_width) // 2
        trigger_text_y = trigger_y + (trigger_height - (trigger_bbox[3] - trigger_bbox[1])) // 2
        draw.text((trigger_text_x, trigger_text_y), trigger_text, fill=rarity_color, font=font_trigger)
        
        artwork_bottom = trigger_y + trigger_height + 15
    
    # Description Box (bottom section, 180px height)
    desc_height = 180
    desc_x = artwork_x
    desc_y = CARD_HEIGHT - desc_height - 80  # Leave room for tags and footer
    desc_width = artwork_width
    
    draw.rounded_rectangle(
        [(desc_x, desc_y),
         (desc_x + desc_width, desc_y + desc_height)],
        radius=8,
        fill=BACKGROUND_COLOR,
        outline=BORDER_COLOR,
        width=1
    )
    
    # Wrap description text (max 6 lines, 24px line height)
    if description:
        words = description.split()
        lines = []
        current_line = []
        line_height = 24
        max_width = desc_width - 20
        
        for word in words:
            test_line = ' '.join(current_line + [word]) if current_line else word
            # Measure text width
            try:
                # Try textlength first (Pillow 9.2+)
                test_width = draw.textlength(test_line, font=font_description)
            except AttributeError:
                # Fallback for older PIL versions
                test_bbox = draw.textbbox((0, 0), test_line, font=font_description)
                test_width = test_bbox[2] - test_bbox[0]
            
            if test_width <= max_width and len(lines) < 6:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
                if len(lines) >= 6:
                    # Truncate last word if needed
                    break
        
        if current_line and len(lines) < 6:
            lines.append(' '.join(current_line))
        
        # Draw lines
        for i, line in enumerate(lines):
            line_y = desc_y + 10 + (i * line_height)
            draw.text((desc_x + 10, line_y), line, fill='#E0E0E0', font=font_description)
    
    # Tags (above description box)
    if tags:
        tag_y = desc_y - 35
        tag_x = desc_x
        tag_spacing = 10
        max_tags = min(len(tags), 4)
        
        for i, tag in enumerate(tags[:max_tags]):
            tag_text = f"#{tag.upper()}"
            tag_bbox = draw.textbbox((0, 0), tag_text, font=font_tag)
            tag_width = tag_bbox[2] - tag_bbox[0] + 16
            tag_height = tag_bbox[3] - tag_bbox[1] + 8
            
            # Draw pill
            draw.rounded_rectangle(
                [(tag_x, tag_y),
                 (tag_x + tag_width, tag_y + tag_height)],
                radius=10,
                fill='#1a1a1a',
                outline=BORDER_COLOR,
                width=1
            )
            
            # Draw text
            draw.text((tag_x + 8, tag_y + 4), tag_text, fill='#E0E0E0', font=font_tag)
            
            tag_x += tag_width + tag_spacing
    
    # Footer (bottom)
    footer_height = 30
    footer_y = CARD_HEIGHT - footer_height - 20
    footer_x = 0
    
    if edition and collection:
        footer_text = f"{edition.upper()} • {collection.upper()}"
    elif edition:
        footer_text = edition.upper()
    elif collection:
        footer_text = collection.upper()
    else:
        footer_text = ""
    
    if footer_text:
        footer_bbox = draw.textbbox((0, 0), footer_text, font=font_footer)
        footer_text_width = footer_bbox[2] - footer_bbox[0]
        footer_text_x = (CARD_WIDTH - footer_text_width) // 2
        draw.text((footer_text_x, footer_y), footer_text, fill='#808080', font=font_footer)
    
    # Save image
    if output_path:
        img.save(output_path, 'PNG', quality=95)
    
    return img
