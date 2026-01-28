"""
Step 1: Create a simple Text TOP that displays "Hello World"
This tests basic text rendering (no background needed)
"""

def step1_simple_text():
    """Create a simple text display"""

    project = op('/project1')

    # Remove existing if present
    if project.op('test_text'):
        project.op('test_text').destroy()

    print("Creating simple text...")

    # Create a simple Text TOP
    text_top = project.create(textTOP, 'test_text')
    text_top.par.text = "Hello World\\nThis is a test\\nPress 1 to view this"
    text_top.par.fontsizex = 48
    text_top.par.fontsizey = 48
    text_top.par.fontcolorr = 0.2
    text_top.par.fontcolorg = 0.8
    text_top.par.fontcolorb = 1.0

    # Position it
    text_top.nodeX = 100
    text_top.nodeY = 100

    print(f"✓ Created text at: {text_top.path}")
    print("✓ Click on 'test_text' and press '1' to view it")
    print("✓ You should see cyan text on black background")

    return text_top

# Execute
if __name__ == "__main__":
    result = step1_simple_text()
