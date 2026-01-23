"""
TouchDesigner Script: Simple Background Display (2D)
Run this in TouchDesigner's Textport or a DAT Execute

This creates a simple 2D background display (no 3D rendering).
Use this if you just want to display the image directly.
"""

def setup_background_simple():
    """Create a simple 2D background display"""

    # Get the project container
    project = op('/project1')

    # Check if background_simple already exists
    if project.op('background_simple'):
        print("Removing existing background_simple...")
        project.op('background_simple').destroy()

    print("Creating simple background display...")

    # Create a container
    bg_container = project.create(containerCOMP, 'background_simple')
    bg_container.nodeX = 500
    bg_container.nodeY = -200
    bg_container.color = (0.5, 0.3, 0.7)  # Purple tint
    bg_container.comment = "Simple 2D Background Display"

    # Create Movie File In TOP to load the background image
    bg_image = bg_container.create(moviefileinTOP, 'bg_image')
    bg_image.par.file = '../resources/background.jpeg'
    bg_image.par.play = False  # Static image
    bg_image.par.cuelength = 1  # Load just one frame

    # Create a Fit TOP to ensure proper aspect ratio
    fit = bg_container.create(fitTOP, 'fit1')
    fit.setInput(0, bg_image)
    fit.par.hmode = 'fit'
    fit.par.vmode = 'fit'

    # Create a Level TOP for any color adjustments
    level = bg_container.create(levelTOP, 'adjust')
    level.setInput(0, fit)
    level.par.opacity = 1

    # Create output NULL TOP
    output_null = bg_container.create(nullTOP, 'OUT')
    output_null.setInput(0, level)
    output_null.color = (0.4, 0.4, 0.8)

    # Layout
    bg_image.nodeX = -200
    bg_image.nodeY = 0
    fit.nodeX = -100
    fit.nodeY = 0
    level.nodeX = 0
    level.nodeY = 0
    output_null.nodeX = 100
    output_null.nodeY = 0

    print("✓ Simple background display created!")
    print(f"✓ Container: {bg_container.path}")
    print(f"✓ Output: {output_null.path}")
    print(f"\nConnect {output_null.path} to any display/composite operator")

    return bg_container

# Execute
if __name__ == "__main__":
    result = setup_background_simple()
