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
    Generate a Kvale card image with DORA-style TCG layout.
    
    Card dimensions: 750x1050px (standard playing card size at 300 DPI)
    Layout: Cost top-left, stats circles, name, artwork, text box, bottom info
    """
    # Card dimensions
    CARD_WIDTH = 750
    CARD_HEIGHT = 1050
    BACKGROUND_COLOR = '#1a1a1a'
    BORDER_COLOR = '#2a2a2a'
    TEXT_COLOR = '#E0E0E0'
    LIGHT_TEXT = '#B0B0B0'
    
    # Create base image
    img = Image.new('RGB', (CARD_WIDTH, CARD_HEIGHT), BACKGROUND_COLOR)
    draw = ImageDraw.Draw(img)
    
    # Get fonts
    font_cost = get_font(36, bold=True)
    font_name = get_font(28, bold=True)
    font_stat_value = get_font(24, bold=True)
    font_stat_label = get_font(10)
    font_description = get_font(14)
    font_ability = get_font(13, bold=True)
    font_footer = get_font(10)
    font_type = get_font(11)
    
    # Get rarity color
    rarity_color = get_rarity_color(rarity)
    
    # Draw card border
    border_width = 3
    draw.rounded_rectangle(
        [(border_width, border_width), 
         (CARD_WIDTH - border_width, CARD_HEIGHT - border_width)],
        radius=12,
        fill=BACKGROUND_COLOR,
        outline=rarity_color,
        width=border_width
    )
    
    # TOP SECTION - Cost and Name
    top_section_height = 80
    top_section_y = 20
    
    # Cost circle (top left)
    cost_circle_size = 50
    cost_x = 25
    cost_y = top_section_y + 15
    
    # Draw cost circle
    draw.ellipse(
        [(cost_x, cost_y),
         (cost_x + cost_circle_size, cost_y + cost_circle_size)],
        fill='#2a2a2a',
        outline=rarity_color,
        width=2
    )
    
    # Cost value (using energy as cost)
    cost_text = str(energy)
    cost_bbox = draw.textbbox((0, 0), cost_text, font=font_cost)
    cost_text_width = cost_bbox[2] - cost_bbox[0]
    cost_text_height = cost_bbox[3] - cost_bbox[1]
    cost_text_x = cost_x + (cost_circle_size - cost_text_width) // 2
    cost_text_y = cost_y + (cost_circle_size - cost_text_height) // 2
    draw.text((cost_text_x, cost_text_y), cost_text, fill=TEXT_COLOR, font=font_cost)
    
    # Card Name (centered, below cost)
    name_y = cost_y + cost_circle_size + 10
    name_text = title.upper()
    name_bbox = draw.textbbox((0, 0), name_text, font=font_name)
    name_width = name_bbox[2] - name_bbox[0]
    name_x = (CARD_WIDTH - name_width) // 2
    draw.text((name_x, name_y), name_text, fill=TEXT_COLOR, font=font_name)
    
    name_bottom = name_y + (name_bbox[3] - name_bbox[1]) + 15
    
    # STAT CIRCLES (three circles below name, like DORA)
    stat_circle_size = 55
    stat_circle_spacing = 20
    stat_section_y = name_bottom + 10
    stat_section_width = (stat_circle_size * 3) + (stat_circle_spacing * 2)
    stat_section_x = (CARD_WIDTH - stat_section_width) // 2
    
    # Calculate health/defense (could be power or a derived stat)
    health = max(1, power // 2) if power > 0 else 1
    
    stats = [
        ('ENERGY', energy),
        ('POWER', power),
        ('HEALTH', health),
    ]
    
    for i, (label, value) in enumerate(stats):
        circle_x = stat_section_x + (i * (stat_circle_size + stat_circle_spacing))
        circle_y = stat_section_y
        
        # Draw stat circle
        draw.ellipse(
            [(circle_x, circle_y),
             (circle_x + stat_circle_size, circle_y + stat_circle_size)],
            fill='#2a2a2a',
            outline=rarity_color,
            width=2
        )
        
        # Stat value
        stat_text = str(value)
        stat_bbox = draw.textbbox((0, 0), stat_text, font=font_stat_value)
        stat_text_width = stat_bbox[2] - stat_bbox[0]
        stat_text_height = stat_bbox[3] - stat_bbox[1]
        stat_text_x = circle_x + (stat_circle_size - stat_text_width) // 2
        stat_text_y = circle_y + (stat_circle_size - stat_text_height) // 2 - 8
        draw.text((stat_text_x, stat_text_y), stat_text, fill=TEXT_COLOR, font=font_stat_value)
        
        # Stat label
        label_bbox = draw.textbbox((0, 0), label, font=font_stat_label)
        label_width = label_bbox[2] - label_bbox[0]
        label_x = circle_x + (stat_circle_size - label_width) // 2
        label_y = circle_y + stat_circle_size - 12
        draw.text((label_x, label_y), label, fill=LIGHT_TEXT, font=font_stat_label)
    
    stat_section_bottom = stat_section_y + stat_circle_size + 20
    
    # ARTWORK SECTION (large central area)
    artwork_margin = 30
    artwork_width = CARD_WIDTH - (artwork_margin * 2)
    artwork_height = 380
    artwork_x = artwork_margin
    artwork_y = stat_section_bottom
    
    # Draw artwork frame
    draw.rounded_rectangle(
        [(artwork_x - 2, artwork_y - 2),
         (artwork_x + artwork_width + 2, artwork_y + artwork_height + 2)],
        radius=8,
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
                radius=8,
                fill=255
            )
            
            img.paste(artwork_img, (artwork_x, artwork_y), mask)
        except Exception as e:
            # Placeholder if image fails to load
            draw.rounded_rectangle(
                [(artwork_x, artwork_y),
                 (artwork_x + artwork_width, artwork_y + artwork_height)],
                radius=8,
                fill='#0a0a0a',
                outline=BORDER_COLOR
            )
            placeholder_text = "ARTWORK"
            placeholder_bbox = draw.textbbox((0, 0), placeholder_text, font=font_name)
            placeholder_x = artwork_x + (artwork_width - (placeholder_bbox[2] - placeholder_bbox[0])) // 2
            placeholder_y = artwork_y + (artwork_height - (placeholder_bbox[3] - placeholder_bbox[1])) // 2
            draw.text((placeholder_x, placeholder_y), placeholder_text, fill='#404040', font=font_name)
    else:
        # Placeholder
        draw.rounded_rectangle(
            [(artwork_x, artwork_y),
             (artwork_x + artwork_width, artwork_y + artwork_height)],
            radius=8,
            fill='#0a0a0a',
            outline=BORDER_COLOR
        )
    
    artwork_bottom = artwork_y + artwork_height + 15
    
    # TEXT BOX (description and abilities)
    text_box_height = 180
    text_box_x = artwork_x
    text_box_y = artwork_bottom
    text_box_width = artwork_width
    
    # Draw text box background
    draw.rounded_rectangle(
        [(text_box_x, text_box_y),
         (text_box_x + text_box_width, text_box_y + text_box_height)],
        radius=6,
        fill='#0f0f0f',
        outline=BORDER_COLOR,
        width=1
    )
    
    # Description text
    text_start_y = text_box_y + 12
    text_start_x = text_box_x + 12
    max_text_width = text_box_width - 24
    line_height = 20
    
    if description:
        words = description.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word]) if current_line else word
            try:
                test_width = draw.textlength(test_line, font=font_description)
            except AttributeError:
                test_bbox = draw.textbbox((0, 0), test_line, font=font_description)
                test_width = test_bbox[2] - test_bbox[0]
            
            if test_width <= max_text_width and len(lines) < 6:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
                if len(lines) >= 6:
                    break
        
        if current_line and len(lines) < 6:
            lines.append(' '.join(current_line))
        
        # Draw description lines
        for i, line in enumerate(lines):
            line_y = text_start_y + (i * line_height)
            draw.text((text_start_x, line_y), line, fill=TEXT_COLOR, font=font_description)
        
        text_start_y += len(lines) * line_height + 8
    
    # Ability/Trigger text (if provided)
    if trigger:
        ability_text = f"⚡ {trigger.upper()}"
        draw.text((text_start_x, text_start_y), ability_text, fill=rarity_color, font=font_ability)
        text_start_y += line_height + 5
    
    text_box_bottom = text_box_y + text_box_height
    
    # BOTTOM SECTION (type, edition, collection)
    bottom_section_height = 50
    bottom_y = CARD_HEIGHT - bottom_section_height - 15
    
    # Draw bottom section background
    draw.rounded_rectangle(
        [(artwork_x, bottom_y),
         (artwork_x + artwork_width, bottom_y + bottom_section_height)],
        radius=6,
        fill='#0f0f0f',
        outline=BORDER_COLOR,
        width=1
    )
    
    # Card type (from tags or card_type)
    type_text = ''
    if tags and isinstance(tags, list) and len(tags) > 0:
        type_text = tags[0].upper()
    elif album_label:
        type_text = album_label.upper()
    
    if type_text:
        type_bbox = draw.textbbox((0, 0), type_text, font=font_type)
        type_x = text_start_x
        type_y = bottom_y + 15
        draw.text((type_x, type_y), type_text, fill=LIGHT_TEXT, font=font_type)
    
    # Edition/Collection (right side)
    footer_text = ''
    if edition and collection:
        footer_text = f"{edition.upper()} • {collection.upper()}"
    elif edition:
        footer_text = edition.upper()
    elif collection:
        footer_text = collection.upper()
    
    if footer_text:
        footer_bbox = draw.textbbox((0, 0), footer_text, font=font_footer)
        footer_text_width = footer_bbox[2] - footer_bbox[0]
        footer_text_x = artwork_x + artwork_width - footer_text_width - 12
        footer_text_y = bottom_y + 15
        draw.text((footer_text_x, footer_text_y), footer_text, fill=LIGHT_TEXT, font=font_footer)
    
    # Rarity indicator (small badge in bottom right corner)
    rarity_badge_size = 30
    rarity_badge_x = CARD_WIDTH - rarity_badge_size - 15
    rarity_badge_y = bottom_y + 10
    
    draw.rounded_rectangle(
        [(rarity_badge_x, rarity_badge_y),
         (rarity_badge_x + rarity_badge_size, rarity_badge_y + rarity_badge_size)],
        radius=4,
        fill='#2a2a2a',
        outline=rarity_color,
        width=1
    )
    
    # Rarity star
    star_text = "★"
    star_bbox = draw.textbbox((0, 0), star_text, font=font_stat_label)
    star_x = rarity_badge_x + (rarity_badge_size - (star_bbox[2] - star_bbox[0])) // 2
    star_y = rarity_badge_y + (rarity_badge_size - (star_bbox[3] - star_bbox[1])) // 2
    draw.text((star_x, star_y), star_text, fill=rarity_color, font=font_stat_label)
    
    # Save image
    if output_path:
        img.save(output_path, 'PNG', quality=95)
    
    return img
