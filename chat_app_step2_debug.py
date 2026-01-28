"""
Debug script for Step 2 - Check what's happening with the composite
"""

def debug_step2():
    """Check the composite setup"""

    project = op('/project1')

    print("=" * 60)
    print("STEP 2 DEBUG")
    print("=" * 60)

    # Check if operators exist
    bg = project.op('background_simple')
    text_comp = project.op('test_text_comp')
    composite = project.op('test_composite')

    print(f"\n1. Operators exist:")
    print(f"   background_simple: {'YES' if bg else 'NO'}")
    print(f"   test_text_comp: {'YES' if text_comp else 'NO'}")
    print(f"   test_composite: {'YES' if composite else 'NO'}")

    if not (bg and text_comp and composite):
        print("\n   ERROR: Some operators missing!")
        return

    # Check text TOP settings
    print(f"\n2. Text TOP (test_text_comp) settings:")
    print(f"   Text: {text_comp.par.text.eval()}")
    print(f"   Font size: {text_comp.par.fontsizex.eval()} x {text_comp.par.fontsizey.eval()}")
    print(f"   Color: R={text_comp.par.fontcolorr.eval()}, G={text_comp.par.fontcolorg.eval()}, B={text_comp.par.fontcolorb.eval()}")
    print(f"   Resolution: {text_comp.width} x {text_comp.height}")

    # Check composite connections
    print(f"\n3. Composite TOP (test_composite) connections:")
    inputs = composite.inputs
    print(f"   Number of inputs: {len(inputs)}")
    for i, inp in enumerate(inputs):
        print(f"   Input {i}: {inp.path if inp else 'None'}")

    # Check if composite has output
    print(f"\n4. Composite output:")
    print(f"   Resolution: {composite.width} x {composite.height}")
    print(f"   Has output: {'YES' if composite.width > 0 else 'NO'}")

    print("\n" + "=" * 60)
    print("TO VIEW THE COMPOSITE:")
    print("=" * 60)
    print("1. Click on the 'test_composite' operator in the network")
    print("2. Press '1' on your keyboard")
    print("3. You should see cyan text over the background")
    print("\nIf you still don't see text, the issue might be:")
    print("- Text color blending with background")
    print("- Text resolution mismatch")
    print("- Composite blending mode")
    print("=" * 60)

# Execute
if __name__ == "__main__":
    debug_step2()
