"""
Step 2: Composite text over background using Composite TOP
This tests if we can layer text over the background image
"""

def step2_composite_text():
    """Composite text over background"""

    project = op('/project1')

    # Check prerequisites - look for background_simple
    bg_out = project.op('background_simple')
    if not bg_out:
        print("ERROR: Need background_simple operator!")
        print("Available operators:", [op.name for op in project.children])
        return

    # Check if it's a container (COMP) or a single TOP
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

    # If it's just a single TOP (like moviefilein), use it directly
    if not hasattr(bg_out, 'width'):
        print("ERROR: background_simple is not a valid image/TOP")
        return

    print(f"Using background: {bg_out.path}")

    # Remove existing
    if project.op('test_composite'):
        project.op('test_composite').destroy()
    if project.op('test_text_comp'):
        project.op('test_text_comp').destroy()

    print("Creating text and composite...")

    # Create Text TOP
    text_top = project.create(textTOP, 'test_text_comp')
    text_top.par.text = "Hello from Chat!\\nPress ENTER to send"
    text_top.par.fontsizex = 36
    text_top.par.fontsizey = 36
    text_top.par.fontcolorr = 0.2
    text_top.par.fontcolorg = 0.8
    text_top.par.fontcolorb = 1.0
    text_top.nodeX = 0
    text_top.nodeY = 0

    # Create Composite TOP (simpler than Over TOP)
    comp_top = project.create(compositeTOP, 'test_composite')
    comp_top.nodeX = 200
    comp_top.nodeY = 0

    # Connect layers to Composite TOP
    # Composite takes multiple inputs and layers them
    comp_top.inputConnectors[0].connect(bg_out)  # Bottom layer
    comp_top.inputConnectors[1].connect(text_top)  # Top layer

    # Set operation to "add" for proper text overlay
    # (default "multiply" would make background black)
    comp_top.par.operand = 'add'

    print(f"✓ Created composite at: {comp_top.path}")
    print("✓ Click on 'test_composite' and press '1' to view")
    print("✓ You should see text over the background image")

    return comp_top

# Execute
if __name__ == "__main__":
    result = step2_composite_text()
