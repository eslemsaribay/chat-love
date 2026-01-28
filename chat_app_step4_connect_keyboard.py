"""
Step 4: Connect keyboard input to text display
This connects test_keyboard to test_text_comp so typed text appears on screen
"""

def step4_connect_keyboard_to_text():
    """Connect keyboard input to text composite"""

    project = op('/project1')

    # Check prerequisites
    keyboard = project.op('test_keyboard')
    callbacks = project.op('test_key_callbacks')
    text_comp = project.op('test_text_comp')
    composite = project.op('test_composite')

    print("=" * 60)
    print("STEP 4: Connect Keyboard to Text Display")
    print("=" * 60)

    if not keyboard:
        print("ERROR: test_keyboard not found! Run step 3 first.")
        return
    if not callbacks:
        print("ERROR: test_key_callbacks not found! Run step 3 first.")
        return
    if not text_comp:
        print("ERROR: test_text_comp not found! Run step 2 first.")
        return
    if not composite:
        print("ERROR: test_composite not found! Run step 2 first.")
        return

    print("✓ All components found")
    print("\nUpdating keyboard callbacks to update text display...")

    # Update callback code to modify text_comp
    callback_code = '''# Keyboard callbacks that update text display

# Initialize input buffer
parent_comp = op('..')
if parent_comp.fetch('input_buffer', None) is None:
    parent_comp.store('input_buffer', "")

def onValueChange(channel, sampleIndex, val, prev):
    """Called when key is pressed"""

    # Only on key press (val == 1)
    if val == 0:
        return

    key_name = channel.name
    parent_comp = op('..')
    buffer = parent_comp.fetch('input_buffer', "")

    # Get the text TOP to update
    text_top = parent_comp.op('test_text_comp')
    if not text_top:
        print("ERROR: test_text_comp not found")
        return

    # Handle keys
    if key_name == 'enter':
        print(f"SUBMITTED: {buffer}")
        parent_comp.store('input_buffer', "")
        # Clear text display
        text_top.par.text = "Press any key to start typing..."
    elif key_name == 'backspace':
        buffer = buffer[:-1]
        parent_comp.store('input_buffer', buffer)
        # Update text display
        display_text = f"> {buffer}" if buffer else "> _"
        text_top.par.text = display_text
        print(f"INPUT: {buffer}")
    elif key_name == 'escape':
        parent_comp.store('input_buffer', "")
        text_top.par.text = "Cleared. Press any key to start typing..."
        print("CLEARED")
    elif len(key_name) == 1:
        buffer += key_name
        parent_comp.store('input_buffer', buffer)
        # Update text display
        text_top.par.text = f"> {buffer}_"
        print(f"INPUT: {buffer}")
    elif key_name == 'space':
        buffer += ' '
        parent_comp.store('input_buffer', buffer)
        # Update text display
        text_top.par.text = f"> {buffer}_"
        print(f"INPUT: {buffer}")
'''

    # Update the execute DAT
    callbacks.text = callback_code

    # Initialize the text display
    project.store('input_buffer', "")
    text_comp.par.text = "Press any key to start typing..."

    print("✓ Keyboard callbacks updated")
    print("✓ Text display initialized")
    print("\n" + "=" * 60)
    print("TEST IT:")
    print("=" * 60)
    print("1. Click on 'test_composite' and press '1' to view")
    print("2. Click anywhere in TouchDesigner window")
    print("3. Start typing - you should see text appear on screen!")
    print("4. Press ENTER to submit (clears input)")
    print("5. Press BACKSPACE to delete characters")
    print("6. Press ESCAPE to clear")
    print("\nNOTE: If keyboard only responds to '1' key,")
    print("try clicking the network editor pane first,")
    print("then typing.")
    print("=" * 60)

    return keyboard, callbacks, text_comp, composite

# Execute
if __name__ == "__main__":
    result = step4_connect_keyboard_to_text()
