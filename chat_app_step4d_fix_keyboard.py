"""
Step 4d: Fix keyboard capture for proper typing
This configures the keyboard CHOP properly and creates a floating viewer window
that captures keyboard input without TD shortcuts interfering
"""

def step4d_fix_keyboard_capture():
    """Fix keyboard input to work properly"""

    project = op('/project1')

    # Check prerequisites
    text_comp = project.op('test_text_comp')
    composite = project.op('test_composite')

    print("=" * 60)
    print("STEP 4D: Fix Keyboard Capture")
    print("=" * 60)

    if not text_comp:
        print("ERROR: test_text_comp not found! Run step 2 first.")
        return
    if not composite:
        print("ERROR: test_composite not found! Run step 2 first.")
        return

    # Remove old keyboard if exists
    if project.op('test_keyboard'):
        project.op('test_keyboard').destroy()
    if project.op('test_key_callbacks'):
        project.op('test_key_callbacks').destroy()

    print("\nCreating keyboard capture system...")

    # Create Keyboard In CHOP
    keyboard = project.create(keyboardinCHOP, 'test_keyboard')
    keyboard.nodeX = 0
    keyboard.nodeY = 200

    # Create CHOP Execute DAT
    execute = project.create(chopexecuteDAT, 'test_key_callbacks')
    execute.nodeX = 200
    execute.nodeY = 200

    # Configure execute
    execute.par.chop = keyboard
    execute.par.valuechange = True

    # Updated callback code with better handling
    callback_code = '''# Keyboard callbacks with proper handling

# Initialize on first run
parent_comp = op('..')
if parent_comp.fetch('input_buffer', None) is None:
    parent_comp.store('input_buffer', "")
    parent_comp.store('keyboard_active', True)

def onValueChange(channel, sampleIndex, val, prev):
    """Called when key is pressed"""

    # Only process key press (val == 1)
    if val == 0:
        return

    parent_comp = op('..')

    # Check if keyboard is active
    if not parent_comp.fetch('keyboard_active', True):
        return

    key_name = channel.name
    buffer = parent_comp.fetch('input_buffer', "")

    # Get text display
    text_top = parent_comp.op('test_text_comp')
    if not text_top:
        return

    # Handle special keys
    if key_name == 'enter':
        print(f"SUBMITTED: '{buffer}'")
        parent_comp.store('input_buffer', "")
        text_top.par.text = "[Submitted]\\nType to continue..."

    elif key_name == 'backspace':
        if buffer:
            buffer = buffer[:-1]
            parent_comp.store('input_buffer', buffer)
            display_text = f"> {buffer}_" if buffer else "> _"
            text_top.par.text = display_text

    elif key_name == 'escape':
        parent_comp.store('input_buffer', "")
        text_top.par.text = "[Cleared]\\nType to continue..."

    elif key_name == 'space':
        buffer += ' '
        parent_comp.store('input_buffer', buffer)
        text_top.par.text = f"> {buffer}_"

    elif len(key_name) == 1 and key_name.isprintable():
        # Regular printable character
        buffer += key_name
        parent_comp.store('input_buffer', buffer)
        text_top.par.text = f"> {buffer}_"

    # Show buffer in console for debugging
    if key_name not in ['enter', 'escape']:
        print(f"Key: {key_name} | Buffer: '{buffer}'")
'''

    execute.text = callback_code

    # Initialize display
    project.store('input_buffer', "")
    project.store('keyboard_active', True)
    text_comp.par.text = "Click viewer window below, then type..."

    # Create a window COMP to display the output
    if project.op('chat_viewer'):
        project.op('chat_viewer').destroy()

    viewer = project.create(windowCOMP, 'chat_viewer')
    viewer.nodeX = 400
    viewer.nodeY = 200

    # Configure window
    viewer.par.winw = 1280
    viewer.par.winh = 720
    viewer.par.borders = True

    # Set the window to display our composite
    viewer.par.operator = composite

    # Open window after configuration
    viewer.par.winopen = True

    print("✓ Keyboard CHOP created and configured")
    print("✓ Keyboard callbacks updated")
    print("✓ Viewer window created")
    print("\n" + "=" * 60)
    print("HOW TO USE:")
    print("=" * 60)
    print("1. A window titled 'Chat Interface' should open")
    print("2. CLICK on that window to give it keyboard focus")
    print("3. Start typing - text should appear!")
    print("4. Press ENTER to submit")
    print("5. Press BACKSPACE to delete")
    print("6. Press ESCAPE to clear")
    print("\n" + "=" * 60)
    print("TROUBLESHOOTING:")
    print("=" * 60)
    print("- If no window opens, click 'chat_viewer' and")
    print("  toggle the 'Open Window in Separate Window' parameter")
    print("- Make sure to CLICK the viewer window first!")
    print("- Keys only work when the viewer window has focus")
    print("=" * 60)

    return keyboard, execute, viewer

# Execute
if __name__ == "__main__":
    result = step4d_fix_keyboard_capture()
