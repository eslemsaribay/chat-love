"""
Step 3: Add keyboard input capture
This tests if we can capture keystrokes and display them
"""

def step3_keyboard_input():
    """Create keyboard input system"""

    project = op('/project1')

    # Remove existing
    if project.op('test_keyboard'):
        project.op('test_keyboard').destroy()
    if project.op('test_key_callbacks'):
        project.op('test_key_callbacks').destroy()

    print("Creating keyboard system...")

    # Create Keyboard In CHOP
    keyboard = project.create(keyboardinCHOP, 'test_keyboard')
    keyboard.nodeX = 0
    keyboard.nodeY = 200

    # Create CHOP Execute DAT for callbacks
    execute = project.create(chopexecuteDAT, 'test_key_callbacks')
    execute.nodeX = 200
    execute.nodeY = 200

    # Set up execute to monitor keyboard
    execute.par.chop = keyboard
    execute.par.valuechange = True

    # Add callback code
    callback_code = '''# Test keyboard callbacks

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

    # Handle keys
    if key_name == 'enter':
        print(f"SUBMITTED: {buffer}")
        parent_comp.store('input_buffer', "")
    elif key_name == 'backspace':
        buffer = buffer[:-1]
        parent_comp.store('input_buffer', buffer)
        print(f"INPUT: {buffer}")
    elif key_name == 'escape':
        parent_comp.store('input_buffer', "")
        print("CLEARED")
    elif len(key_name) == 1:
        buffer += key_name
        parent_comp.store('input_buffer', buffer)
        print(f"INPUT: {buffer}")
    elif key_name == 'space':
        buffer += ' '
        parent_comp.store('input_buffer', buffer)
        print(f"INPUT: {buffer}")
'''

    execute.text = callback_code

    print(f"✓ Created keyboard at: {keyboard.path}")
    print(f"✓ Created callbacks at: {execute.path}")
    print("\nTEST IT:")
    print("1. Click anywhere in TouchDesigner window")
    print("2. Type some text")
    print("3. Watch the Textport (Alt+T) for output")
    print("4. Press ENTER to submit")
    print("5. Press BACKSPACE to delete")
    print("6. Press ESCAPE to clear")

    return keyboard, execute

# Execute
if __name__ == "__main__":
    result = step3_keyboard_input()
