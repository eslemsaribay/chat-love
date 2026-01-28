"""
Debug script to see what channels exist in the keyboard CHOP
"""

def debug_keyboard_channels():
    """Show all available keyboard channels"""

    project = op('/project1')
    keyboard = project.op('test_keyboard')

    if not keyboard:
        print("ERROR: test_keyboard not found!")
        return

    print("=" * 60)
    print("KEYBOARD CHOP DEBUG")
    print("=" * 60)

    # List all channels
    print(f"\nTotal channels: {len(keyboard.chans())}")
    print("\nFirst 50 channels:")
    for i, chan in enumerate(keyboard.chans()[:50]):
        print(f"  {i}: {chan.name}")

    print("\n" + "=" * 60)
    print("Looking for letter keys...")
    print("=" * 60)

    # Look for common keys
    search_keys = ['a', 'b', 'c', 'space', 'enter', 'backspace',
                   'ka', 'kb', 'kc', 'k1', 'k2',
                   'alpha_a', 'alpha_b', 'key_a']

    for key in search_keys:
        chan = keyboard.chan(key)
        if chan:
            print(f"  Found: {key} (value: {chan.eval()})")

    print("\n" + "=" * 60)
    print("INSTRUCTIONS:")
    print("=" * 60)
    print("Look at the channel names above.")
    print("Find the pattern for letter keys.")
    print("We need to update the callback to match those names.")
    print("=" * 60)

# Execute
if __name__ == "__main__":
    debug_keyboard_channels()
