"""
Step 4e: Keyboard capture using Keyboard In DAT (captures ALL keys)
Based on TouchDesigner documentation
"""

def step4e_simple_keyboard():
    """Create keyboard capture using Keyboard In DAT"""

    project = op('/project1')

    # Check prerequisites
    text_comp = project.op('test_text_comp')
    composite = project.op('test_composite')

    print("=" * 60)
    print("STEP 4E: Keyboard Capture (Keyboard In DAT)")
    print("=" * 60)

    if not text_comp:
        print("ERROR: test_text_comp not found! Run step 2 first.")
        return
    if not composite:
        print("ERROR: test_composite not found! Run step 2 first.")
        return

    # Remove old components
    for old_name in ['test_keyboard', 'test_key_callbacks', 'chat_viewer']:
        if project.op(old_name):
            project.op(old_name).destroy()

    print("\nCreating keyboard system...")

    # Create Keyboard In DAT (not CHOP!)
    keyboard_dat = project.create(keyboardinDAT, 'test_keyboard')
    keyboard_dat.nodeX = 0
    keyboard_dat.nodeY = 200

    # CRITICAL: Leave keys parameter BLANK to capture all keys
    keyboard_dat.par.keys = ''  # Blank = capture all keys
    keyboard_dat.par.maxlines = 1  # Only keep most recent key
    keyboard_dat.par.perform = False  # Capture keys anytime (easier for testing)

    print("✓ Keyboard In DAT created (captures ALL keys)")
    print("✓ Keyboard capture enabled (works anytime for testing)")

    # Create callbacks DAT
    callbacks_dat = project.create(textDAT, 'test_key_callbacks')
    callbacks_dat.nodeX = 200
    callbacks_dat.nodeY = 200

    # Set keyboard_dat to use this callbacks DAT
    keyboard_dat.par.callbacks = callbacks_dat

    # Callback code for Keyboard In DAT
    callback_code = '''# Keyboard In DAT callbacks

parent_comp = op('..')

# Initialize buffer
if parent_comp.fetch('input_buffer', None) is None:
    parent_comp.store('input_buffer', "")

def onKey(dat, key, character, alt, lAlt, rAlt, ctrl, lCtrl, rCtrl, shift, lShift, rShift, state, time):
    """Called when a key event occurs"""

    # Only process key press (state == True means key pressed, False means released)
    if not state:
        return

    parent_comp = op('..')
    buffer = parent_comp.fetch('input_buffer', "")
    text_top = parent_comp.op('test_text_comp')

    if not text_top:
        return

    # Handle special keys by name
    if key == 'return':
        print(f"SUBMITTED: '{buffer}'")
        parent_comp.store('input_buffer', "")
        text_top.par.text = "[Submitted]\\n\\nType to continue..."

    elif key == 'backspace':
        if buffer:
            buffer = buffer[:-1]
            parent_comp.store('input_buffer', buffer)
            text_top.par.text = f"> {buffer}_" if buffer else "> _"

    elif key == 'escape':
        parent_comp.store('input_buffer', "")
        text_top.par.text = "[Cleared]\\n\\nType to continue..."

    elif character and character.isprintable():
        # Use character for regular keys (handles space automatically)
        buffer += character
        parent_comp.store('input_buffer', buffer)
        text_top.par.text = f"> {buffer}_"
'''

    callbacks_dat.text = callback_code

    # Initialize
    project.store('input_buffer', "")
    text_comp.par.text = "> _"

    print("✓ Callbacks installed")
    print("\n" + "=" * 60)
    print("TEST IT (Single Screen):")
    print("=" * 60)
    print("1. Click 'test_composite' and press '1' to view")
    print("2. Type - letters should appear over background!")
    print("\nKEYS: ENTER=submit, BACKSPACE=delete, ESC=clear")
    print("\nFor your 2-monitor fullscreen setup:")
    print("- Set keyboard_dat.par.perform = True")
    print("- Configure Window COMP for fullscreen")
    print("- Press F1 for Perform Mode (no TD shortcuts!)")
    print("\nTo change which Window COMP is used for F1:")
    print("- Go to Dialogs → Window Placement")
    print("- Set the 'Perform Window' column")
    print("=" * 60)

    return keyboard_dat, callbacks_dat

# Execute
if __name__ == "__main__":
    result = step4e_simple_keyboard()
