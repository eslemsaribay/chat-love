"""
Setup Complete Chat Application
Single script that creates the full chat system with keyboard input
"""

import importlib
import sys

# Force reload global_context to get latest changes
if 'global_context' in sys.modules:
    del sys.modules['global_context']

from global_context import GLOBAL_CONTEXT

def setup_chat_app():
    """Main setup function - creates complete chat application"""

    print("=" * 60)
    print("SETUP: Complete Chat Application")
    print("=" * 60)

    project = op('/project1')

    # Verify prerequisites
    if not _check_prerequisites(project):
        return

    # Create container
    container = _create_container(project)
    if not container:
        return

    # Create container input for background
    _create_container_input(container)

    # Setup components
    python_dat = _create_spec_generator(container)
    _create_text_display(container, python_dat)
    _create_keyboard_input(container, python_dat)
    _create_output(container)

    # Done
    _print_completion_message(container)

    return container


# ============================================
# Prerequisites
# ============================================

def _check_prerequisites(project):
    """Check that background exists"""
    bg_out = project.op('background_simple')
    if not bg_out:
        print("ERROR: Need background_simple operator!")
        print("Run setup_background_simple.py first")
        return False

    # Handle container backgrounds
    if hasattr(bg_out, 'children') and len(bg_out.children) > 0:
        for child in bg_out.children:
            if child.type == nullTOP or 'OUT' in child.name.upper():
                bg_out = child
                break

    if not hasattr(bg_out, 'width'):
        print("ERROR: background_simple is not a valid image/TOP")
        return False

    print(f"OK Background ready: {bg_out.path}")
    return True


# ============================================
# Container Setup
# ============================================

def _create_container(project):
    """Create or recreate the chat_application container"""

    # Remove existing
    if project.op('chat_application'):
        project.op('chat_application').destroy()
        print("Removed existing chat_application")

    # Create container
    container = project.create(containerCOMP, 'chat_application')
    container.nodeX = 0
    container.nodeY = 400
    container.color = (0.3, 0.7, 0.5)

    # Initialize ChatManager (force module reload to get latest code)
    import importlib
    import sys

    # Remove cached modules to force reload
    for mod in ['chat_config', 'chat_manager', 'chat_llm_worker']:
        if mod in sys.modules:
            del sys.modules[mod]

    from chat_config import CHAT_CONFIG
    from chat_manager import ChatManager

    chat_manager = ChatManager(CHAT_CONFIG)

    # Try to initialize LLM (will print error if it fails, but continue)
    try:
        chat_manager.initialize_llm()
    except Exception as e:
        print(f"WARNING: LLM initialization failed: {e}")
        print("Chat will work without AI responses")

    chat_manager.add_initial_message()  # Add bot's greeting

    container.store('chat_manager', chat_manager)

    print(f"OK Container created: {container.path}")
    return container


# ============================================
# Container Input
# ============================================

def _create_container_input(container):
    """Create In TOP inside container to accept background input"""

    print("\n[0/4] Creating container input...")

    # Create In TOP
    in_top = container.create(inTOP, 'in1')
    in_top.nodeX = -200
    in_top.nodeY = 0

    print(f"  OK Created: {in_top.path}")
    print(f"    - Container now has input connector")

    return in_top


# ============================================
# Specification Generator (Python DAT)
# ============================================

def _create_spec_generator(container):
    """Create Table DAT with initial messages from ChatManager"""

    print("\n[1/4] Creating specification table...")

    # Create Table DAT
    table_dat = container.create(tableDAT, 'chat_spec_generator')
    table_dat.nodeX = 0
    table_dat.nodeY = 0

    # Clear and populate from ChatManager
    table_dat.clear()

    # Header row
    table_dat.appendRow(['x', 'y', 'text', 'fontsize', 'fontcolorr', 'fontcolorg', 'fontcolorb'])

    # Get messages from ChatManager
    chat_manager = container.fetch('chat_manager', None)
    if chat_manager:
        from chat_config import CHAT_CONFIG
        messages = chat_manager.get_display_messages()

        for msg in messages:
            # Determine color based on role
            if msg.role == "user":
                color = CHAT_CONFIG["user_color"]
            elif msg.role == "input":
                color = CHAT_CONFIG["input_color"]
            else:  # assistant
                color = CHAT_CONFIG["assistant_color"]

            # Add row with message data
            table_dat.appendRow([
                CHAT_CONFIG["chat_x"],
                msg.y_position,
                msg.text,
                CHAT_CONFIG["font_size"],
                color[0], color[1], color[2]
            ])

    print(f"  OK Created: {table_dat.path}")
    print(f"    - Rows: {table_dat.numRows}, Cols: {table_dat.numCols}")

    return table_dat


# ============================================
# Text Display (Text TOP)
# ============================================

def _create_text_display(container, spec_dat):
    """Create Text TOP that renders from specification DAT"""

    print("\n[2/4] Creating text display...")

    # Create Text TOP
    text_top = container.create(textTOP, 'chat_display')

    # Resolution (from global context)
    text_top.par.resolutionw = GLOBAL_CONTEXT.width
    text_top.par.resolutionh = GLOBAL_CONTEXT.height
    text_top.par.outputresolution = GLOBAL_CONTEXT.output_res
    text_top.par.outputaspect = GLOBAL_CONTEXT.output_aspect

    # Specification DAT mode
    text_top.par.text = ''
    text_top.par.specdat = spec_dat.path

    # Transparent background (alpha = 0)
    text_top.par.bgalpha = 0

    # Word wrap
    text_top.par.wordwrap = True

    # Font settings
    text_top.par.fontsizex = 24
    text_top.par.fontsizey = 24

    # Alignment
    text_top.par.alignx = 'left'
    text_top.par.aligny = 'top'

    # Position in network
    text_top.nodeX = 0
    text_top.nodeY = -200

    print(f"  OK Created: {text_top.path}")
    print(f"    - Resolution: {GLOBAL_CONTEXT.width}x{GLOBAL_CONTEXT.height}, outputresolution: {GLOBAL_CONTEXT.output_res}")
    print(f"    - Reading spec from: {spec_dat.path}")
    print(f"    - Transparent background for compositing")

    return text_top


# ============================================
# Keyboard Input
# ============================================

def _create_keyboard_input(container, spec_dat):
    """Create keyboard input DAT and callbacks"""

    print("\n[3/4] Creating keyboard input...")

    # Create Keyboard In DAT
    keyboard_dat = container.create(keyboardinDAT, 'keyboard_in')
    keyboard_dat.nodeX = 200
    keyboard_dat.nodeY = 0

    # Configure
    keyboard_dat.par.keys = ''
    keyboard_dat.par.maxlines = 1
    keyboard_dat.par.perform = False

    # Create callbacks DAT
    callbacks_dat = container.create(textDAT, 'keyboard_callbacks')
    callbacks_dat.nodeX = 400
    callbacks_dat.nodeY = 0

    # Link keyboard to callbacks
    keyboard_dat.par.callbacks = callbacks_dat

    # Callback code
    callback_code = '''# Keyboard callbacks

def onKey(dat, key, character, alt, lAlt, rAlt, ctrl, lCtrl, rCtrl, shift, lShift, rShift, state, time):
    """Handle key press events"""

    # Only process key press (not release)
    if not state:
        return

    parent_comp = op('..')
    chat_manager = parent_comp.fetch('chat_manager', None)
    table_dat = parent_comp.op('chat_spec_generator')

    if not chat_manager or not table_dat:
        return

    # Import config for colors
    from chat_config import CHAT_CONFIG

    # Handle special keys
    if key == 'return':
        # Submit input via ChatManager
        chat_manager.submit_input()
        _regenerate_table(chat_manager, table_dat, CHAT_CONFIG)

    elif key == 'backspace':
        # Remove last character
        chat_manager.backspace_input()
        _regenerate_table(chat_manager, table_dat, CHAT_CONFIG)

    elif key == 'escape':
        # Clear input
        chat_manager.clear_input()
        _regenerate_table(chat_manager, table_dat, CHAT_CONFIG)

    elif character and character.isprintable():
        # Add character
        chat_manager.append_to_input(character)
        _regenerate_table(chat_manager, table_dat, CHAT_CONFIG)

def _regenerate_table(chat_manager, table_dat, config):
    """Regenerate the entire specification table from ChatManager"""
    table_dat.clear()

    # Header row
    table_dat.appendRow(['x', 'y', 'text', 'fontsize', 'fontcolorr', 'fontcolorg', 'fontcolorb'])

    # Get all display messages
    messages = chat_manager.get_display_messages()

    for msg in messages:
        # Determine color based on role
        if msg.role == "user":
            color = config["user_color"]
        elif msg.role == "input":
            color = config["input_color"]
        else:  # assistant
            color = config["assistant_color"]

        # Add row
        table_dat.appendRow([
            config["chat_x"],
            msg.y_position,
            msg.text,
            config["font_size"],
            color[0], color[1], color[2]
        ])
'''

    callbacks_dat.text = callback_code

    print(f"  OK Created: {keyboard_dat.path}")
    print(f"  OK Created: {callbacks_dat.path}")
    print(f"    - Linked and ready")

    return keyboard_dat, callbacks_dat


# ============================================
# Output
# ============================================

def _create_output(container):
    """Create Over TOP to composite chat over background, then output"""

    print("\n[4/4] Creating Over TOP composite and output...")

    in_top = container.op('in1')
    text_top = container.op('chat_display')

    # Create Over TOP for compositing
    over_top = container.create(overTOP, 'chat_composite')

    # Resolution (from global context - MUST match all other components)
    over_top.par.resolutionw = GLOBAL_CONTEXT.width
    over_top.par.resolutionh = GLOBAL_CONTEXT.height
    over_top.par.outputresolution = GLOBAL_CONTEXT.output_res
    over_top.par.outputaspect = GLOBAL_CONTEXT.output_aspect

    # Input 0 = Overlay Layer (chat text on top)
    # Input 1 = Fixed Layer (background from container input)
    over_top.inputConnectors[0].connect(text_top)
    over_top.inputConnectors[1].connect(in_top)

    over_top.nodeX = 0
    over_top.nodeY = -300

    print(f"  OK Created Over TOP: {over_top.path}")
    print(f"    - Resolution: {GLOBAL_CONTEXT.width}x{GLOBAL_CONTEXT.height}, outputresolution: {GLOBAL_CONTEXT.output_res}")
    print(f"    - Input 0 (Overlay): {text_top.path}")
    print(f"    - Input 1 (Fixed): {in_top.path} (container input)")

    # Create Out TOP for container output
    out_top = container.create(outTOP, 'out1')
    out_top.inputConnectors[0].connect(over_top)
    out_top.nodeX = 0
    out_top.nodeY = -500

    # Make the container display its output when viewed
    container.viewer = True
    container.activeViewer = True

    # Set display flag on output
    out_top.display = True
    out_top.viewer = True

    print(f"  OK Created Out TOP: {out_top.path}")
    print(f"    - Container now has output connector")

    return out_top


# ============================================
# Completion Message
# ============================================

def _print_completion_message(container):
    """Print setup completion message"""

    from chat_config import CHAT_CONFIG

    print("\n" + "=" * 60)
    print("Setup complete!")
    print("=" * 60)
    print(f"\nChat application ready!")
    print(f"\nResolution: {CHAT_CONFIG['canvas_width']}x{CHAT_CONFIG['canvas_height']}, outputresolution: {GLOBAL_CONTEXT.output_res}")
    print(f"Bot name: {CHAT_CONFIG['bot_name']}")
    print(f"Initial message: {CHAT_CONFIG['initial_message']}")
    print("\nManual connections required:")
    print(f"  1. Connect background_simple -> {container.path} input connector (with mouse)")
    print(f"  2. Create viewer and connect {container.path} output connector to it (optional)")
    print("\nArchitecture:")
    print(f"  - Inside container: in1 -> Over TOP <- chat_display -> out1")
    print(f"  - Container has input/output connectors (MediaPipe style)")
    print(f"  - All components use outputresolution='fit' from global_context.py")
    print("\nHow to use:")
    print("  1. Click on 'chat_view' in project1")
    print("  2. Click anywhere to focus TouchDesigner window")
    print("  3. Type your response to the bot's question")
    print("  4. Press ENTER - bot will extract your name")
    print("  5. Continue chatting normally")
    print("\nKeyboard controls:")
    print("  - Type: Add characters")
    print("  - ENTER: Submit message (first message extracts username)")
    print("  - BACKSPACE: Delete last character")
    print("  - ESC: Clear input")
    print("\nNote: Username will be extracted from first message")
    print("=" * 60)


# ============================================
# Execute
# ============================================

if __name__ == "__main__":
    result = setup_chat_app()
