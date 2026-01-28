"""
Step 4c: Create a visible text field for typing input
This creates an actual text field UI element that can be clicked and typed into
"""

def step4c_create_textfield():
    """Create a visible text field for chat input"""

    project = op('/project1')

    # Check prerequisites
    text_comp = project.op('test_text_comp')
    composite = project.op('test_composite')

    print("=" * 60)
    print("STEP 4C: Create Text Field Input")
    print("=" * 60)

    if not text_comp:
        print("ERROR: test_text_comp not found! Run step 2 first.")
        return
    if not composite:
        print("ERROR: test_composite not found! Run step 2 first.")
        return

    print("✓ All components found")

    # Remove existing input components
    for old_name in ['test_keyboard', 'test_key_callbacks', 'chat_input_panel',
                     'input_monitor', 'text_input_field', 'field_monitor']:
        if project.op(old_name):
            project.op(old_name).destroy()

    print("\nCreating text input field...")

    # Create a simple text DAT that will hold the input
    input_dat = project.create(textDAT, 'text_input_field')
    input_dat.nodeX = 0
    input_dat.nodeY = 300
    input_dat.text = ""

    # Enable the text DAT as a panel so it can be edited
    input_dat.par.extension = ''
    input_dat.dock = True

    # Create a CHOP Execute to monitor changes to this DAT
    monitor = project.create(datexecuteDAT, 'field_monitor')
    monitor.nodeX = 200
    monitor.nodeY = 300

    # Set it to monitor the text DAT
    monitor.par.dat = input_dat
    monitor.par.tablechange = True

    monitor_code = '''# Monitor text field changes

parent_comp = op('..')

def onTableChange(dat):
    """Called when text DAT content changes"""

    text_display = parent_comp.op('test_text_comp')
    if not text_display:
        return

    # Get current text from the DAT
    current_text = dat.text.strip()

    # Store it
    parent_comp.store('current_input', current_text)

    # Update the display
    if current_text:
        text_display.par.text = f"> {current_text}_"
    else:
        text_display.par.text = "> _"

    print(f"Input: {current_text}")
'''

    monitor.text = monitor_code

    # Initialize
    project.store('current_input', "")
    text_comp.par.text = "> _"

    print("✓ Text input field created")
    print("✓ Field monitor created")
    print("\n" + "=" * 60)
    print("TEST IT:")
    print("=" * 60)
    print("1. Click on 'test_composite' and press '1' to view")
    print("   (This opens the viewer window)")
    print("\n2. In the network editor, RIGHT-CLICK on")
    print("   'text_input_field' and select 'Edit'")
    print("\n3. A text editor window will open")
    print("   Type in that window - your text should appear")
    print("   in the test_composite viewer!")
    print("\n4. Each time you finish typing and click away,")
    print("   the text should update")
    print("\n" + "=" * 60)
    print("ALTERNATIVE - Use Keyboard CHOP properly:")
    print("=" * 60)
    print("If you want keyboard input to work while viewing:")
    print("1. Open the viewer (press '1' on test_composite)")
    print("2. Make sure the VIEWER WINDOW has focus")
    print("3. The viewer window needs to be active to capture keys")
    print("\n" + "=" * 60)

    return input_dat, monitor

# Execute
if __name__ == "__main__":
    result = step4c_create_textfield()
