"""
Setup Text Rendering and Composite
Creates text display and composites it over background image
"""

# ============================================
# CONFIGURATION - Edit these to adjust chat area
# ============================================
CHAT_CONFIG = {
    # Font settings
    'font_size': 24,           # Font size in pixels
    'font_color': (0.2, 0.8, 1.0),  # RGB (cyan)

    # Text area position (in pixels from top-left of 1280x720 canvas)
    'text_x': 300,             # Left edge of chat area
    'text_y': 800,             # Top of chat area (from bottom)

    # Text area size (for layout reference, not render resolution)
    'text_width': 800,         # Width of chat area
    'text_height': 400,        # Height of chat area

    # Text alignment
    'align_x': 'left',         # 'left', 'center', 'right'
    'align_y': 'top',          # 'top', 'center', 'bottom'

    # Line spacing
    'line_spacing': 1.2,       # Multiplier for line height (1.0 = single space)
}

def setup_text(config=None):
    """Create text TOP and composite it over background

    Args:
        config: Optional dict with configuration overrides
    """

    # Use provided config or defaults
    if config is None:
        config = CHAT_CONFIG
    else:
        # Merge with defaults
        cfg = CHAT_CONFIG.copy()
        cfg.update(config)
        config = cfg

    project = op('/project1')

    print("=" * 60)
    print("SETUP: Text Rendering")
    print("=" * 60)
    print(f"Font size: {config['font_size']}px")
    print(f"Chat area: {config['text_x']},{config['text_y']} ({config['text_width']}x{config['text_height']})")

    # Check for background
    bg_out = project.op('background_simple')
    if not bg_out:
        print("ERROR: Need background_simple operator!")
        print("Run setup_background_simple.py first")
        return

    # Handle both container and single TOP backgrounds
    if hasattr(bg_out, 'children') and len(bg_out.children) > 0:
        # It's a container, find output inside
        for child in bg_out.children:
            if child.type == nullTOP or 'OUT' in child.name.upper():
                bg_out = child
                break
        if not bg_out or not hasattr(bg_out, 'width'):
            # Try to find any TOP
            for child in bg_out.children:
                if hasattr(child, 'width'):
                    bg_out = child
                    break

    if not hasattr(bg_out, 'width'):
        print("ERROR: background_simple is not a valid image/TOP")
        return

    print(f"Using background: {bg_out.path}")

    # Remove existing components
    if project.op('chat_text'):
        project.op('chat_text').destroy()

    print("\nCreating text with built-in composite...")

    # Create Text TOP
    text_top = project.create(textTOP, 'chat_text')
    text_top.par.text = "HELLO WORLD TEST"  # Large test text for visibility

    # Font settings - use large size for initial testing
    text_top.par.fontsizex = 100
    text_top.par.fontsizey = 100
    text_top.par.fontcolorr = config['font_color'][0]
    text_top.par.fontcolorg = config['font_color'][1]
    text_top.par.fontcolorb = config['font_color'][2]

    # Make background transparent (critical for overlay!)
    text_top.par.bgalpha = 0

    # Text area position and size - center for initial testing
    text_top.par.alignx = 'center'
    text_top.par.aligny = 'center'

    # Resolution (match final output resolution, not chat area)
    text_top.par.resolutionw = 1280
    text_top.par.resolutionh = 720

    # Output aspect mode (use defined resolution aspect ratio)
    text_top.par.outputaspect = 'resolution'

    # Position in network
    text_top.nodeX = 0
    text_top.nodeY = 0

    # Connect background to text input
    text_top.inputConnectors[0].connect(bg_out)

    # Use Text TOP's built-in compositing (much simpler!)
    text_top.par.compoverinput = True

    print(f"✓ Text TOP created: {text_top.path}")
    print(f"  - Resolution: {text_top.width}x{text_top.height}")
    print(f"  - Text: '{text_top.par.text}'")
    print(f"  - Font size: {text_top.par.fontsizex}x{text_top.par.fontsizey}")
    print(f"  - Font color: R={text_top.par.fontcolorr}, G={text_top.par.fontcolorg}, B={text_top.par.fontcolorb}")
    print(f"  - BG alpha: {text_top.par.bgalpha}")
    print(f"  - Align: {text_top.par.alignx}, {text_top.par.aligny}")
    print(f"  - Background input: {text_top.inputs[0] if text_top.inputs else 'None'}")
    print(f"  - Comp Over Input: {text_top.par.compoverinput}")

    print("\n" + "=" * 60)
    print("Setup complete! View 'chat_text' to see text over background.")
    print("Text should be large and centered for initial testing.")
    print("=" * 60)

    return text_top

# Execute
if __name__ == "__main__":
    result = setup_text()
