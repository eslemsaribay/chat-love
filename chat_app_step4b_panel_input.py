"""
Step 4b: Create a proper text input panel for typing
This creates a UI panel with text field that captures keyboard input properly
without interfering with TD shortcuts
"""

def step4b_create_text_input_panel():
    """Create a text input panel for proper typing"""

    project = op('/project1')

    # Check prerequisites
    text_comp = project.op('test_text_comp')
    composite = project.op('test_composite')

    print("=" * 60)
    print("STEP 4B: Create Text Input Panel")
    print("=" * 60)

    if not text_comp:
        print("ERROR: test_text_comp not found! Run step 2 first.")
        return
    if not composite:
        print("ERROR: test_composite not found! Run step 2 first.")
        return

    print("✓ All components found")

    # Remove old keyboard components (they're not working well)
    if project.op('test_keyboard'):
        print("Removing old keyboard_in...")
        project.op('test_keyboard').destroy()
    if project.op('test_key_callbacks'):
        print("Removing old keyboard_callbacks...")
        project.op('test_key_callbacks').destroy()

    # Remove existing panel if present
    if project.op('chat_input_panel'):
        project.op('chat_input_panel').destroy()
    if project.op('input_monitor'):
        project.op('input_monitor').destroy()

    print("\nCreating input panel...")

    # Create a Container COMP for the panel
    panel_comp = project.create(containerCOMP, 'chat_input_panel')
    panel_comp.nodeX = 0
    panel_comp.nodeY = 300
    panel_comp.par.w = 800
    panel_comp.par.h = 100

    # Enable panel display
    panel_comp.par.display = True
    panel_comp.par.enableviewing = True

    # Add custom parameter for text input
    page = panel_comp.appendCustomPage('Input')
    text_par = page.appendStr('Userinput', label='Type Here')[0]
    text_par.default = ""

    # Create DAT Execute to monitor the text parameter
    monitor_dat = project.create(chopexecuteDAT, 'input_monitor')
    monitor_dat.nodeX = 200
    monitor_dat.nodeY = 300

    # Create execute code that monitors the text parameter
    # We'll use a different approach - use a DAT Execute that runs on frame
    monitor_dat.par.executemode = 'framestart'

    monitor_code = '''# Monitor text input and update display

parent_comp = op('..')
panel = parent_comp.op('chat_input_panel')
text_display = parent_comp.op('test_text_comp')

if not panel or not text_display:
    return

# Get current input
current_input = panel.par.Userinput.eval()

# Store previous input to detect changes
if parent_comp.fetch('prev_input', None) is None:
    parent_comp.store('prev_input', "")

prev_input = parent_comp.fetch('prev_input', "")

# Check if input changed
if current_input != prev_input:
    parent_comp.store('prev_input', current_input)

    # Update text display
    if current_input:
        text_display.par.text = f"> {current_input}_"
    else:
        text_display.par.text = "> _"

# Check for ENTER key - user must clear input manually for now
# (We'll add proper ENTER handling in the chat flow step)
'''

    # Actually, let's use a better approach with Panel Execute
    monitor_dat.destroy()

    # Create a Panel Execute DAT instead
    panel_execute = project.create(panelexecuteDAT, 'input_monitor')
    panel_execute.nodeX = 200
    panel_execute.nodeY = 300

    # Set it to monitor the panel comp
    panel_execute.par.panelcomp = panel_comp
    panel_execute.par.valuechange = True
    panel_execute.par.offtooff = True

    panel_code = '''# Monitor panel parameter changes

parent_comp = op('..')

def onValueChange(panelValue):
    """Called when panel parameter changes"""

    # Get the parameter that changed
    try:
        par = panelValue.par

        # Check if it's our text input parameter
        if par.name == 'Userinput':
            text_display = parent_comp.op('test_text_comp')
            if text_display:
                current_text = par.eval()

                if current_text:
                    text_display.par.text = f"> {current_text}_"
                else:
                    text_display.par.text = "> _"

                print(f"Input: {current_text}")
    except:
        pass
'''

    panel_execute.text = panel_code

    print("✓ Text input panel created")
    print("✓ Input monitor created")
    print("\n" + "=" * 60)
    print("TEST IT:")
    print("=" * 60)
    print("1. Right-click on 'chat_input_panel' and select")
    print("   'View...' or 'Edit Contents'")
    print("2. In the parameter window, find 'Type Here' field")
    print("3. Click in the text field and start typing")
    print("4. Watch test_composite - text should update as you type!")
    print("\nOR:")
    print("1. Click on 'chat_input_panel' operator")
    print("2. Press 'P' to open Parameters window")
    print("3. Find the 'Type Here' field under 'Input' page")
    print("4. Type in that field")
    print("\n" + "=" * 60)
    print("NOTE: This is a parameter-based input for now.")
    print("In Step 5, we'll add proper ENTER key handling")
    print("and send to LLM.")
    print("=" * 60)

    return panel_comp, panel_execute

# Execute
if __name__ == "__main__":
    result = step4b_create_text_input_panel()
