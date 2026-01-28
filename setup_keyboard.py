"""
Setup Keyboard Input with Keyboard In DAT
Captures all keyboard input and updates chat text display
"""

def setup_keyboard():
    """Create Keyboard In DAT with callbacks for text input"""

    project = op('/project1')

    print("=" * 60)
    print("SETUP: Keyboard Input")
    print("=" * 60)

    # Check for text display
    text_comp = project.op('chat_text')
    if not text_comp:
        print("ERROR: chat_text not found!")
        print("Run setup_text.py first")
        return

    # Remove old keyboard components
    for old_name in ['chat_keyboard', 'chat_keyboard_callbacks']:
        if project.op(old_name):
            project.op(old_name).destroy()

    print("\nCreating keyboard system...")

    # Create Keyboard In DAT
    keyboard_dat = project.create(keyboardinDAT, 'chat_keyboard')
    keyboard_dat.nodeX = 0
    keyboard_dat.nodeY = 200

    # Configure: blank keys = capture all keys
    keyboard_dat.par.keys = ''
    keyboard_dat.par.maxlines = 1
    keyboard_dat.par.perform = False  # Set to True for production (Perform Mode only)

    # Create callbacks DAT
    callbacks_dat = project.create(textDAT, 'chat_keyboard_callbacks')
    callbacks_dat.nodeX = 200
    callbacks_dat.nodeY = 200

    # Link keyboard to callbacks
    keyboard_dat.par.callbacks = callbacks_dat

    # Callback code
    callback_code = '''# Keyboard In DAT callbacks

parent_comp = op('..')

# Initialize input buffer
if parent_comp.fetch('input_buffer', None) is None:
    parent_comp.store('input_buffer', "")

def onKey(dat, key, character, alt, lAlt, rAlt, ctrl, lCtrl, rCtrl, shift, lShift, rShift, state, time):
    """Called when a key event occurs"""

    # Only process key press (not release)
    if not state:
        return

    parent_comp = op('..')
    buffer = parent_comp.fetch('input_buffer', "")
    text_top = parent_comp.op('chat_text')

    if not text_top:
        return

    # Handle special keys
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
        # Regular printable character (includes space)
        buffer += character
        parent_comp.store('input_buffer', buffer)
        text_top.par.text = f"> {buffer}_"
'''

    callbacks_dat.text = callback_code

    # Initialize input buffer
    project.store('input_buffer', "")
    text_comp.par.text = "> _"

    print("✓ Keyboard In DAT created (captures ALL keys)")
    print("✓ Callbacks installed")
    print("\n" + "=" * 60)
    print("Setup complete!")
    print("\nTesting:")
    print("  1. Click 'chat_composite' and press '1' to view")
    print("  2. Type - text should appear over background!")
    print("\nKeys: ENTER=submit, BACKSPACE=delete, ESC=clear")
    print("\nFor production (Perform Mode):")
    print("  - Set keyboard_dat.par.perform = True")
    print("  - Press F1 to enter Perform Mode (no TD shortcuts)")
    print("=" * 60)

    return keyboard_dat, callbacks_dat

# Execute
if __name__ == "__main__":
    result = setup_keyboard()
