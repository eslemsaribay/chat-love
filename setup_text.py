"""
Setup Text Rendering and Composite
Creates text display and composites it over background image
"""

def setup_text():
    """Create text TOP and composite it over background"""

    project = op('/project1')

    print("=" * 60)
    print("SETUP: Text Rendering")
    print("=" * 60)

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
    if project.op('chat_composite'):
        project.op('chat_composite').destroy()
    if project.op('chat_text'):
        project.op('chat_text').destroy()

    print("\nCreating text and composite...")

    # Create Text TOP
    text_top = project.create(textTOP, 'chat_text')
    text_top.par.text = "> _"
    text_top.par.fontsizex = 36
    text_top.par.fontsizey = 36
    text_top.par.fontcolorr = 0.2
    text_top.par.fontcolorg = 0.8
    text_top.par.fontcolorb = 1.0
    text_top.nodeX = 0
    text_top.nodeY = 0

    # Create Composite TOP
    comp_top = project.create(compositeTOP, 'chat_composite')
    comp_top.nodeX = 200
    comp_top.nodeY = 0

    # Connect layers
    comp_top.inputConnectors[0].connect(bg_out)  # Bottom: background
    comp_top.inputConnectors[1].connect(text_top)  # Top: text

    # Set to 'add' for proper text overlay
    comp_top.par.operand = 'add'

    print(f"✓ Text TOP created: {text_top.path}")
    print(f"✓ Composite created: {comp_top.path}")
    print("\n" + "=" * 60)
    print("Setup complete! Components ready:")
    print("  - chat_text: Text rendering")
    print("  - chat_composite: Final output (text over background)")
    print("=" * 60)

    return text_top, comp_top

# Execute
if __name__ == "__main__":
    result = setup_text()
