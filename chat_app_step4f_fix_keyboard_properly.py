"""
Step 4f: Actually configure the keyboard CHOP correctly
The issue: Keyboard In CHOP needs to be configured to capture ALL keys
"""

def step4f_configure_keyboard_properly():
    """Configure keyboard CHOP to actually capture all keys"""

    project = op('/project1')

    # Check prerequisites
    text_comp = project.op('test_text_comp')
    composite = project.op('test_composite')

    print("=" * 60)
    print("STEP 4F: Fix Keyboard Configuration")
    print("=" * 60)

    if not text_comp:
        print("ERROR: test_text_comp not found! Run step 2 first.")
        return
    if not composite:
        print("ERROR: test_composite not found! Run step 2 first.")
        return

    # Remove old keyboard components
    for old_name in ['test_keyboard', 'test_key_callbacks']:
        if project.op(old_name):
            project.op(old_name).destroy()

    print("\nCreating properly configured keyboard CHOP...")

    # Create Keyboard In CHOP
    keyboard = project.create(keyboardinCHOP, 'test_keyboard')
    keyboard.nodeX = 0
    keyboard.nodeY = 200

    # CRITICAL: Configure to capture ALL keys
    # The Keyboard In CHOP has a parameter for which keys to monitor
    try:
        # Try setting to capture all keys
        keyboard.par.capturemode = 'all'  # Capture all keys mode
    except:
        pass

    try:
        # Or try setting a key list to include common keys
        keyboard.par.keys = 'abcdefghijklmnopqrstuvwxyz0123456789 '
    except:
        pass

    try:
        # Or enable all alpha keys
        keyboard.par.alpha = True
        keyboard.par.numeric = True
        keyboard.par.special = True
    except:
        pass

    # Check what parameters actually exist
    print("\nKeyboard CHOP parameters:")
    print("Available parameters:")
    for par in keyboard.pars():
        if 'key' in par.name.lower() or 'capture' in par.name.lower() or 'alpha' in par.name.lower():
            print(f"  {par.name}: {par.val}")

    print("\n" + "=" * 60)
    print("DIAGNOSIS:")
    print("=" * 60)
    print("The Keyboard In CHOP needs configuration.")
    print("Please manually configure it:")
    print("\n1. Click on 'test_keyboard' operator")
    print("2. Look at its parameters (press 'P')")
    print("3. Find parameters related to:")
    print("   - Which keys to capture")
    print("   - Key mode or capture mode")
    print("   - Enable all keys / alpha / numeric")
    print("\n4. Tell me what parameters you see!")
    print("=" * 60)

    return keyboard

# Execute
if __name__ == "__main__":
    result = step4f_configure_keyboard_properly()
