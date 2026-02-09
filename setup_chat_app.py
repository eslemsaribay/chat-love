"""
Setup Complete Chat Application
Single script that creates the full chat system with keyboard input
"""

import importlib
import sys

# Force reload global_context to get latest changes
if 'config.global_context' in sys.modules:
    del sys.modules['config.global_context']

from config.global_context import GLOBAL_CONTEXT

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
    keyboard_dat, callbacks_dat = _create_keyboard_input(container, python_dat)

    # Setup panel callbacks for mouse wheel / touchpad scrolling on the text COMP
    text_comp = container.op('chat_display')
    if text_comp:
        try:
            # Enable panel interact mode and set wheel callback
            text_comp.par.enablepanel = True
            text_comp.par.wheelcallbacks = callbacks_dat.path
            print(f"\n  OK Mouse/touchpad scroll enabled on text display")
        except AttributeError as e:
            print(f"\n  Note: Could not enable wheel callbacks: {e}")
            print(f"        Use arrow keys (Up/Down) for scrolling")

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
# Helper: Text Wrapping
# ============================================

def _wrap_text(text, max_chars=60):
    """Wrap text to fit within max_chars per line, returns list of lines"""
    import textwrap
    return textwrap.wrap(text, width=max_chars, break_long_words=True, break_on_hyphens=True) or [text]


# ============================================
# Helper: Table Regeneration
# ============================================

def _regenerate_table_from_manager(chat_manager, table_dat, config):
    """Regenerate table DAT from ChatManager state (used by update callback)"""
    table_dat.clear()
    table_dat.appendRow(['x', 'y', 'text', 'fontsize', 'fontcolorr', 'fontcolorg', 'fontcolorb'])

    wrap_chars = config.get("wrap_chars", 80)
    line_height = config.get("line_height", 20)

    # Visible window bounds (for clipping)
    # TouchDesigner Y-axis: Y=0 at bottom, increases upward
    canvas_height = config["canvas_height"]
    window_top_px = config.get("chat_window_top", config["chat_y"])  # Distance from top of canvas
    window_height = config.get("chat_window_height", 400)

    # Convert to TD coordinates (Y from bottom)
    window_top_y = canvas_height - window_top_px  # Top of visible area (high Y)
    window_bottom_y = canvas_height - (window_top_px + window_height)  # Bottom of visible area (low Y)

    # Get scroll offset from chat manager
    scroll_offset = getattr(chat_manager, 'scroll_offset', 0)

    # Get all messages and calculate total lines
    messages = chat_manager.get_display_messages()
    total_lines = 0
    message_lines = []  # List of (msg, wrapped_lines)
    for msg in messages:
        wrapped = _wrap_text(msg.text, wrap_chars)
        message_lines.append((msg, wrapped))
        total_lines += len(wrapped)

    # ANCHOR FROM BOTTOM: Position content so input (last line) is at window bottom when scroll_offset=0
    # First line Y = window_bottom_y + (total_lines - 1) * line_height
    # Last line Y = window_bottom_y
    # Scroll offset SUBTRACTS from Y, moving content DOWN, revealing older messages from above
    first_line_y = window_bottom_y + (total_lines - 1) * line_height
    current_y = first_line_y - scroll_offset

    for msg, wrapped_lines in message_lines:
        if msg.role == "user":
            color = config["user_color"]
        elif msg.role == "input":
            color = config["input_color"]
        else:
            color = config["assistant_color"]

        for line in wrapped_lines:
            # Only add row if within visible window (TD Y coordinates)
            if window_bottom_y <= current_y <= window_top_y:
                table_dat.appendRow([
                    config["chat_x"], current_y, line,
                    config["font_size"], color[0], color[1], color[2]
                ])

            current_y -= line_height  # Move down for next line (lower Y)

    table_dat.cook(force=True)


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

    # Set container layout dimensions from global context
    container.par.w = GLOBAL_CONTEXT.width
    container.par.h = GLOBAL_CONTEXT.height

    # Initialize ChatManager (force module reload to get latest code)
    import importlib
    import sys

    # Remove cached modules to force reload
    for mod in ['chat_config', 'chat_manager', 'chat_llm_worker']:
        if mod in sys.modules:
            del sys.modules[mod]

    from config.chat_config import CHAT_CONFIG
    from chat_manager import ChatManager

    # Create update callback that will regenerate the table when messages change
    # This closure captures 'container' reference for later use by LLM worker threads
    def on_chat_update():
        """Callback to regenerate table when messages change (called from worker threads)"""
        # Use TouchDesigner's run() to execute on main thread (thread-safe)
        def do_update():
            try:
                table_dat = container.op('chat_spec_generator')
                chat_mgr = container.fetch('chat_manager', None)
                if table_dat and chat_mgr:
                    _regenerate_table_from_manager(chat_mgr, table_dat, CHAT_CONFIG)
            except Exception as e:
                print(f"Chat update error: {e}")

        # Schedule on main thread
        run("args[0]()", do_update, delayFrames=1)

    chat_manager = ChatManager(CHAT_CONFIG, on_update_callback=on_chat_update)

    # Try to initialize LLM (will print error if it fails, but continue)
    try:
        chat_manager.initialize_llm()
    except Exception as e:
        print(f"WARNING: LLM initialization failed: {e}")
        print("Chat will work without AI responses")

    chat_manager.add_initial_message()  # Add bot's greeting

    container.store('chat_manager', chat_manager)

    print(f"OK Container created: {container.path}")
    print(f"  - Resolution: {GLOBAL_CONTEXT.width}x{GLOBAL_CONTEXT.height}")
    return container


# ============================================
# Container Input
# ============================================

def _create_container_input(container):
    """Create In TOP inside container to accept background input"""

    print("\n[1/4] Creating container input...")

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

    print("\n[2/4] Creating specification table...")

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
        from config.chat_config import CHAT_CONFIG
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
    """Create Text COMP that renders from specification DAT with per-row colors"""

    print("\n[3/4] Creating text display...")

    in_top = container.op('in1')

    # Create Text COMP (supports per-row font colors in spec DAT)
    text_comp = container.create(textCOMP, 'chat_display')

    # Resolution (from global context)
    text_comp.par.w = GLOBAL_CONTEXT.width
    text_comp.par.h = GLOBAL_CONTEXT.height

    # Background TOP (composite text over background from container input)
    text_comp.par.top = in_top

    # Specification DAT mode
    text_comp.par.mode = 'specdat'
    text_comp.par.specdat = spec_dat.path

    # Word wrap
    text_comp.par.wordwrap = True

    # Font settings
    text_comp.par.fontsize = 24

    # Alignment
    text_comp.par.alignx = 'left'
    text_comp.par.aligny = 'top'

    # Position in network
    text_comp.nodeX = 0
    text_comp.nodeY = -200

    # Note: Text COMP IS a TOP - no need to find 'out1' inside it
    # The text_comp itself is the output that can be connected to other TOPs

    print(f"  OK Created: {text_comp.path}")
    print(f"    - Resolution: {GLOBAL_CONTEXT.width}x{GLOBAL_CONTEXT.height}")
    print(f"    - Reading spec from: {spec_dat.path}")
    print(f"    - Background TOP: {in_top.path}")
    print(f"    - Per-row font colors enabled")
    print(f"    - Output: text_comp itself (is a TOP)")

    return text_comp


# ============================================
# Keyboard Input
# ============================================

def _create_keyboard_input(container, spec_dat):
    """Create keyboard input DAT and callbacks"""

    print("\n[4/4] Creating keyboard input...")

    # Create Keyboard In DAT
    keyboard_dat = container.create(keyboardinDAT, 'keyboard_in')
    keyboard_dat.nodeX = 200
    keyboard_dat.nodeY = 0

    # Configure - leave keys empty to capture all keys
    keyboard_dat.par.keys = ''
    keyboard_dat.par.maxlines = 1
    keyboard_dat.par.active = True  # Enable keyboard capture

    # Create callbacks DAT
    callbacks_dat = container.create(textDAT, 'keyboard_callbacks')
    callbacks_dat.nodeX = 400
    callbacks_dat.nodeY = 0

    # Link keyboard to callbacks - use PATH, not object
    keyboard_dat.par.callbacks = callbacks_dat.path

    # Callback code
    callback_code = '''# Keyboard callbacks
import textwrap

def _wrap_text(text, max_chars=60):
    """Wrap text to fit within max_chars per line, returns list of lines"""
    return textwrap.wrap(text, width=max_chars, break_long_words=True, break_on_hyphens=True) or [text]

def _get_window_manager():
    """Get the WindowManager instance (None if not set up)."""
    wm_container = op('/project1/window_manager')
    if wm_container is None:
        return None
    return wm_container.fetch('window_manager', None)

def _handle_window_signals(key, character, chat_manager):
    """Handle window manager signal keys. Returns True if key was consumed."""
    wm = _get_window_manager()
    if wm is None:
        return False

    from config.window_manager_config import WINDOW_MANAGER_CONFIG
    bindings = WINDOW_MANAGER_CONFIG.get("key_bindings", {})

    # INTRO phase: block all keys from chat, only F3 triggers transition
    if wm.phase == "intro":
        intro_key = bindings.get("signal_intro_complete", "F3")
        if key == intro_key:
            wm.signal_intro_complete()
        return True  # consume ALL keys during intro

    # Reset key (works in any phase)
    reset_key = bindings.get("signal_reset", "F9")
    if key == reset_key:
        wm.signal_reset()
        if chat_manager is not None:
            chat_manager.reset()
        return True

    # Reveal key (only during ACTIVE phase, blocked during REVEALED to prevent duplicate timers)
    reveal_key = bindings.get("signal_reveal", "space")
    if key == reveal_key and wm.phase == "active":
        wm.signal_reveal()
        return True

    return False

def onKey(dat, key, character, alt, lAlt, rAlt, ctrl, lCtrl, rCtrl, shift, lShift, rShift, state, time):
    """Handle key press events"""

    try:
        parent_comp = op('..')
        chat_manager = parent_comp.fetch('chat_manager', None)
        table_dat = parent_comp.op('chat_spec_generator')

        # Window manager signals work even without chat_manager/LLM
        if state:
            if _handle_window_signals(key, character, chat_manager):
                return

        if not chat_manager or not table_dat:
            return

        # Import config for colors
        from config.chat_config import CHAT_CONFIG

        # Process key press (state=True) and key repeat events
        if state:
            # Handle special keys
            if key == 'enter':
                # Submit input via ChatManager
                chat_manager.submit_input()
                _regenerate_table(chat_manager, table_dat, CHAT_CONFIG)

            elif key == 'backspace':
                # Remove last character
                chat_manager.backspace_input()
                _regenerate_table(chat_manager, table_dat, CHAT_CONFIG)

            elif key == 'esc':
                # Clear input
                chat_manager.clear_input()
                _regenerate_table(chat_manager, table_dat, CHAT_CONFIG)

            elif key == 'F5':
                # Reset entire chat (F5 = refresh/reset)
                chat_manager.reset()
                _regenerate_table(chat_manager, table_dat, CHAT_CONFIG)

            elif key == 'up':
                # Scroll up to see older messages
                chat_manager.scroll_up()
                _regenerate_table(chat_manager, table_dat, CHAT_CONFIG)

            elif key == 'down':
                # Scroll down to see newer messages
                chat_manager.scroll_down()
                _regenerate_table(chat_manager, table_dat, CHAT_CONFIG)

            elif key == 'home':
                # Scroll to oldest messages (max scroll)
                chat_manager.scroll_offset = 9999
                _regenerate_table(chat_manager, table_dat, CHAT_CONFIG)

            elif key == 'end':
                # Scroll to newest messages
                chat_manager.reset_scroll()
                _regenerate_table(chat_manager, table_dat, CHAT_CONFIG)

            elif character and character.isprintable():
                # Add character
                chat_manager.append_to_input(character)
                _regenerate_table(chat_manager, table_dat, CHAT_CONFIG)

    except Exception as e:
        print(f"ERROR in keyboard callback: {e}")
        import traceback
        traceback.print_exc()

def _regenerate_table(chat_manager, table_dat, config):
    """Regenerate the entire specification table from ChatManager with word wrapping and scroll support"""
    table_dat.clear()

    # Header row
    table_dat.appendRow(['x', 'y', 'text', 'fontsize', 'fontcolorr', 'fontcolorg', 'fontcolorb'])

    # Get wrap settings from config
    wrap_chars = config.get("wrap_chars", 50)
    line_height = config.get("line_height", 30)

    # Visible window bounds (for clipping)
    # TouchDesigner Y-axis: Y=0 at bottom, increases upward
    canvas_height = config["canvas_height"]
    window_top_px = config.get("chat_window_top", config["chat_y"])  # Distance from top of canvas
    window_height = config.get("chat_window_height", 400)

    # Convert to TD coordinates (Y from bottom)
    window_top_y = canvas_height - window_top_px  # Top of visible area (high Y)
    window_bottom_y = canvas_height - (window_top_px + window_height)  # Bottom of visible area (low Y)

    # Get scroll offset from chat manager
    scroll_offset = getattr(chat_manager, 'scroll_offset', 0)

    # Get all display messages and calculate total lines
    messages = chat_manager.get_display_messages()
    total_lines = 0
    message_lines = []  # List of (msg, wrapped_lines)
    for msg in messages:
        wrapped = _wrap_text(msg.text, wrap_chars)
        message_lines.append((msg, wrapped))
        total_lines += len(wrapped)

    # ANCHOR FROM BOTTOM: Position content so input (last line) is at window bottom when scroll_offset=0
    # First line Y = window_bottom_y + (total_lines - 1) * line_height
    # Last line Y = window_bottom_y
    # Scroll offset SUBTRACTS from Y, moving content DOWN, revealing older messages from above
    first_line_y = window_bottom_y + (total_lines - 1) * line_height
    current_y = first_line_y - scroll_offset

    for msg, wrapped_lines in message_lines:
        # Determine color based on role
        if msg.role == "user":
            color = config["user_color"]
        elif msg.role == "input":
            color = config["input_color"]
        else:  # assistant
            color = config["assistant_color"]

        for line in wrapped_lines:
            # Only add row if within visible window (TD Y coordinates)
            if window_bottom_y <= current_y <= window_top_y:
                table_dat.appendRow([
                    config["chat_x"],
                    current_y,
                    line,
                    config["font_size"],
                    color[0], color[1], color[2]
                ])

            current_y -= line_height  # Move down for next line (lower Y)

    # Force cook to ensure display updates immediately
    table_dat.cook(force=True)

def onWheel(comp, wheelDelta, x, y, buttons, ext):
    """Handle mouse wheel / touchpad scroll events"""
    try:
        parent_comp = comp.parent()
        chat_manager = parent_comp.fetch('chat_manager', None)
        table_dat = parent_comp.op('chat_spec_generator')

        if not chat_manager or not table_dat:
            return

        from config.chat_config import CHAT_CONFIG

        # wheelDelta is positive when scrolling up, negative when scrolling down
        # Invert the logic: scroll up = see older messages (increase offset)
        if wheelDelta > 0:
            # Mouse wheel up / touchpad scroll up = see older messages
            chat_manager.scroll_up()
        else:
            # Mouse wheel down / touchpad scroll down = see newer messages
            chat_manager.scroll_down()

        _regenerate_table(chat_manager, table_dat, CHAT_CONFIG)

    except Exception as e:
        print(f"ERROR in wheel callback: {e}")
        import traceback
        traceback.print_exc()
'''

    callbacks_dat.text = callback_code

    print(f"  OK Created: {keyboard_dat.path}")
    print(f"  OK Created: {callbacks_dat.path}")
    print(f"    - Linked and ready")

    return keyboard_dat, callbacks_dat


# ============================================
# Completion Message
# ============================================

def _print_completion_message(container):
    """Print setup completion message"""

    from config.chat_config import CHAT_CONFIG

    print("\n" + "=" * 60)
    print("Setup complete!")
    print("=" * 60)
    print(f"\nChat application ready!")
    print(f"\nResolution: {CHAT_CONFIG['canvas_width']}x{CHAT_CONFIG['canvas_height']}, outputresolution: {GLOBAL_CONTEXT.output_res}")
    print(f"Bot name: {CHAT_CONFIG['bot_name']}")
    print(f"Initial message: {CHAT_CONFIG['initial_message']}")
    print("\nManual connections required:")
    print(f"  1. Connect background_simple -> {container.path} input connector")
    print(f"  2. Connect {container.path} to a Window COMP for viewing")
    print("\nArchitecture:")
    print(f"  - Inside container: in1 -> chat_display (text over background)")
    print(f"  - Text COMP composites text over background internally")
    print(f"  - Per-row font colors enabled via specification DAT")
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
    print("  - F5: Reset chat (clear all messages, context, username)")
    print("\nScroll controls:")
    print("  - UP ARROW: Scroll up to see older messages")
    print("  - DOWN ARROW: Scroll down to see newer messages")
    print("  - HOME: Jump to oldest messages")
    print("  - END: Jump to newest messages")
    print("  - MOUSE WHEEL / TOUCHPAD: Scroll through messages")
    print("\nNote: Username will be extracted from first message")
    print("=" * 60)


# ============================================
# Execute
# ============================================

if __name__ == "__main__":
    result = setup_chat_app()
