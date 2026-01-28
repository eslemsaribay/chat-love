"""
TouchDesigner Chat Application Setup Script
Run this in TouchDesigner's Textport or a DAT Execute

Creates a complete chat interface with:
- Keyboard input capture
- LLM integration via Ollama
- Text display over background
- Configurable layout and styling

NOTE: This script uses TouchDesigner built-in types (containerCOMP, keyboardinCHOP, etc.)
that are only available in TouchDesigner's Python environment. Pylance/IDE warnings
about undefined variables are expected and can be ignored - the code will run correctly
inside TouchDesigner.
"""

# TouchDesigner types (defined in TD Python environment, not available to static analysis)
# containerCOMP, keyboardinCHOP, executeDAT, textDAT, tableDAT, textTOP, nullTOP

def setup_chat_application():
    """Create chat application in TouchDesigner"""

    project = op('/project1')

    # Validate prerequisites
    if not project.op('background_simple'):
        raise RuntimeError(
            "Background not found. Run setup_background_simple.py first.\n"
            "Execute: exec(open('c:/ARKHE/Projects/TouchDesigner/Eslem/setup_background_simple.py').read())"
        )

    # Remove existing if present
    if project.op('chat_application'):
        print("Removing existing chat_application...")
        project.op('chat_application').destroy()

    print("Creating chat application...")

    # Create container
    chat_container = project.create(containerCOMP, 'chat_application')
    chat_container.nodeX = 500
    chat_container.nodeY = -400
    chat_container.color = (0.3, 0.7, 0.5)
    chat_container.comment = "Chat Application with LLM"

    # Add custom parameters
    _add_custom_parameters(chat_container)

    # Create operators
    keyboard_chop = _create_keyboard_input(chat_container)
    execute_dat = _create_keyboard_callbacks(chat_container, keyboard_chop)
    spec_dat = _create_spec_generator(chat_container)
    text_top = _create_text_display(chat_container, spec_dat)
    over_top = _create_compositor(chat_container, text_top)
    out_null = _create_output(chat_container, over_top)

    # Layout operators
    _layout_operators(
        keyboard_chop, execute_dat, spec_dat,
        text_top, over_top, out_null
    )

    print("✓ Chat application created successfully!")
    print(f"✓ Container: {chat_container.path}")
    print(f"✓ Output: {out_null.path}")
    print("\n" + "=" * 60)
    print("INSTRUCTIONS:")
    print("=" * 60)
    print("1. Click anywhere in the TouchDesigner window to focus")
    print("2. Start typing your message")
    print("3. Press ENTER to send message to LLM")
    print("4. Press BACKSPACE to delete characters")
    print("5. Press ESCAPE to clear input")
    print("\nNote: Make sure Ollama is running with llama3.2 model!")
    print("=" * 60)

    return chat_container


def _add_custom_parameters(container):
    """Add custom parameters for configuration"""

    page = container.appendCustomPage('Chat Config')

    # Layout parameters
    p = page.appendInt('Chatx', label='Chat X Position')[0]
    p.default = 100
    p.normMin = 0
    p.normMax = 1920

    p = page.appendInt('Chaty', label='Chat Y Position')[0]
    p.default = 800
    p.normMin = 0
    p.normMax = 1080

    p = page.appendInt('Messagespacing', label='Message Spacing')[0]
    p.default = 40
    p.normMin = 10
    p.normMax = 100

    p = page.appendInt('Fontsize', label='Font Size')[0]
    p.default = 24
    p.normMin = 8
    p.normMax = 72

    p = page.appendInt('Maxmessages', label='Max Messages')[0]
    p.default = 20
    p.normMin = 5
    p.normMax = 100

    # Color parameters - RGB creates 3 separate params (r, g, b)
    page.appendRGB('Usercolor', label='User Color')
    container.par.Usercolorr.default = 0.2
    container.par.Usercolorg.default = 0.8
    container.par.Usercolorb.default = 1.0
    container.par.Usercolorr.val = 0.2
    container.par.Usercolorg.val = 0.8
    container.par.Usercolorb.val = 1.0

    page.appendRGB('Assistantcolor', label='Assistant Color')
    container.par.Assistantcolorr.default = 1.0
    container.par.Assistantcolorg.default = 1.0
    container.par.Assistantcolorb.default = 1.0
    container.par.Assistantcolorr.val = 1.0
    container.par.Assistantcolorg.val = 1.0
    container.par.Assistantcolorb.val = 1.0

    page.appendRGB('Systemcolor', label='System Color')
    container.par.Systemcolorr.default = 0.8
    container.par.Systemcolorg.default = 0.8
    container.par.Systemcolorb.default = 0.8
    container.par.Systemcolorr.val = 0.8
    container.par.Systemcolorg.val = 0.8
    container.par.Systemcolorb.val = 0.8

    # LLM parameters
    p = page.appendStr('Ollamamodel', label='Ollama Model')[0]
    p.default = "llama3.2"
    p.val = "llama3.2"

    p = page.appendToggle('Streamingenabled', label='Enable Streaming')[0]
    p.default = True
    p.val = True

    p = page.appendInt('Maxtokens', label='Max Tokens')[0]
    p.default = 512
    p.normMin = 64
    p.normMax = 2048

    p = page.appendFloat('Temperature', label='Temperature')[0]
    p.default = 0.7
    p.normMin = 0.0
    p.normMax = 1.0


def _create_keyboard_input(container):
    """Create keyboard input CHOP"""

    keyboard = container.create(keyboardinCHOP, 'keyboard_in')
    keyboard.color = (0.8, 0.6, 0.3)
    keyboard.comment = "Captures keyboard input"

    return keyboard


def _create_keyboard_callbacks(container, keyboard_chop):
    """Create Execute DAT with keyboard callbacks"""

    execute_dat = container.create(chopexecuteDAT, 'keyboard_callbacks')
    execute_dat.color = (0.6, 0.3, 0.8)
    execute_dat.comment = "Keyboard event handlers"

    # Set up CHOP Execute DAT to monitor keyboard CHOP
    execute_dat.par.chop = keyboard_chop
    execute_dat.par.valuechange = True

    # Embed callback code
    callback_code = '''# Keyboard callbacks for chat application
import sys
import os

# Get ChatManager from parent storage
parent_comp = op('..')
chat_manager = parent_comp.fetch('chat_manager', None)

if chat_manager is None:
    # Initialize on first run
    try:
        # Add project directory to path
        script_dir = "c:/ARKHE/Projects/TouchDesigner/Eslem"
        if script_dir not in sys.path:
            sys.path.insert(0, script_dir)

        from chat_manager import ChatManager
        from chat_config import CHAT_CONFIG

        # Create and initialize
        chat_manager = ChatManager(CHAT_CONFIG)
        chat_manager.initialize_llm()

        # Store in parent
        parent_comp.store('chat_manager', chat_manager)

        print("Chat manager initialized successfully")
    except Exception as e:
        print(f"Error initializing chat manager: {e}")
        import traceback
        traceback.print_exc()


def onValueChange(channel, sampleIndex, val, prev):
    """Called when keyboard key is pressed"""

    if chat_manager is None:
        return

    # Only process key press (val == 1)
    if val == 0:
        return

    key_name = channel.name

    # Handle special keys
    if key_name == 'enter':
        chat_manager.submit_input()
    elif key_name == 'backspace':
        chat_manager.backspace_input()
    elif key_name == 'escape':
        chat_manager.clear_input()
    elif len(key_name) == 1:
        # Regular character
        chat_manager.append_to_input(key_name)
    elif key_name == 'space':
        chat_manager.append_to_input(' ')

    # Force spec DAT to update
    try:
        op('chat_spec_table').cook(force=True)
    except:
        pass
'''

    execute_dat.text = callback_code

    return execute_dat


def _create_spec_generator(container):
    """Create DAT for specification table generation"""

    spec_dat = container.create(textDAT, 'chat_spec_table')
    spec_dat.par.extension = 'dat'
    spec_dat.color = (0.3, 0.6, 0.8)
    spec_dat.comment = "Text rendering specification"

    # Embed spec generation code
    spec_code = '''# Specification table generator for Text TOP
import time

parent_comp = op('..')
chat_manager = parent_comp.fetch('chat_manager', None)

if chat_manager:
    messages = chat_manager.get_display_messages()
    config = chat_manager.config

    # Header row
    print("x\\ty\\ttext\\tfontsize\\tfontcolorr\\tfontcolorg\\tfontcolorb")

    # Message rows
    for msg in messages:
        # Determine color based on role
        if msg.role in ["user", "input"]:
            color = config["user_color"]
        elif msg.role == "assistant":
            color = config["assistant_color"]
        else:
            color = config["system_color"]

        # Output table row (tab-separated)
        print(f"{config['chat_x']}\\t{msg.y_position}\\t{msg.text}\\t"
              f"{config['font_size']}\\t{color[0]}\\t{color[1]}\\t{color[2]}")
else:
    # No manager yet, output empty table
    print("x\\ty\\ttext\\tfontsize\\tfontcolorr\\tfontcolorg\\tfontcolorb")
'''

    spec_dat.text = spec_code

    return spec_dat


def _create_text_display(container, spec_dat):
    """Create Text TOP for rendering"""

    text_top = container.create(textTOP, 'chat_display')
    text_top.color = (0.8, 0.4, 0.4)
    text_top.comment = "Text rendering"

    # Configure Text TOP
    text_top.par.specdat = spec_dat

    # Text display settings
    text_top.par.fontsizex = 24
    text_top.par.fontsizey = 24
    text_top.par.fontfile = 'default'

    return text_top


def _create_compositor(container, text_top):
    """Create Over TOP to composite text over background"""

    over_top = container.create(overTOP, 'compositor')
    over_top.color = (0.5, 0.7, 0.5)
    over_top.comment = "Composite text over background"

    # Get background
    bg_out = op('/project1/background_simple/OUT')

    # Over TOP structure:
    # - Input 0: Bottom layer (background)
    # - Input 1: Top layer (text to overlay)
    # OR use operand parameter for top layer

    # Connect background to input 0
    try:
        over_top.inputConnectors[0].connect(bg_out)
    except:
        print("Could not connect background to Over TOP")

    # Set text as operand (top layer)
    over_top.par.operand = text_top

    return over_top


def _create_output(container, compositor):
    """Create output NULL TOP"""

    out_null = container.create(nullTOP, 'OUT')

    # Connect compositor output
    out_null.inputConnectors[0].connect(compositor)

    out_null.color = (0.4, 0.4, 0.8)
    out_null.comment = "Final composite output"

    return out_null


def _layout_operators(keyboard, execute, spec_dat, text, compositor, output):
    """Arrange operators in network view"""

    # Top row - input handling
    keyboard.nodeX = -400
    keyboard.nodeY = 0
    keyboard.nodeWidth = 100

    execute.nodeX = -200
    execute.nodeY = 0
    execute.nodeWidth = 150

    # Middle row - spec generation
    spec_dat.nodeX = -100
    spec_dat.nodeY = -100
    spec_dat.nodeWidth = 150

    # Bottom row - rendering
    text.nodeX = 0
    text.nodeY = -200

    compositor.nodeX = 0
    compositor.nodeY = -300

    output.nodeX = 0
    output.nodeY = -400


# Execute
if __name__ == "__main__":
    result = setup_chat_application()
