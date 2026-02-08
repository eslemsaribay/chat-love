"""
Setup Window Manager
Creates a multi-monitor view switching system with:
- 4 In TOPs (intro_video_1, intro_video_2, avatar, real_life)
- Wrapper Container COMPs for intro videos (winop targets)
- Switch TOP for avatar/real_life transition with wrapper Container
- 2 Window COMPs (one per monitor)
- Phase-based signal system (intro -> active -> revealed)

Usage:
    import sys; sys.path.insert(0, project.folder)
    exec(open(project.folder + '/setup_window_manager.py').read())
"""

import importlib
import sys

# Force reload to get latest changes
for mod in ['global_context', 'window_manager_config', 'window_manager']:
    if mod in sys.modules:
        del sys.modules[mod]

from global_context import GLOBAL_CONTEXT
from window_manager_config import WINDOW_MANAGER_CONFIG


def setup_window_manager():
    """Main setup function - creates complete window manager system."""

    print("=" * 60)
    print("SETUP: Window Manager")
    print("=" * 60)

    config = WINDOW_MANAGER_CONFIG
    parent = op(config["parent_path"])

    if parent is None:
        print(f"ERROR: Parent path not found: {config['parent_path']}")
        return None

    # Step 1: Create container
    container = _create_container(parent, config)
    if not container:
        return None

    # Step 2: Create 4 In TOPs
    in_tops = _create_top_inputs(container, config)

    # Step 3: Create wrapper containers for intro videos (in1, in2)
    _create_intro_wrappers(container, config, in_tops)

    # Step 4: Create Switch TOP for avatar/real_life (in3, in4) + wrapper
    _create_main_view_switch(container, config, in_tops)

    # Step 5: Create Window COMPs
    _create_window_comps(container, config)

    # Step 6: Create view registry Table DAT
    _create_view_registry(container, config)

    # Step 7: Initialize WindowManager and apply defaults
    _initialize_manager(container, config)

    # Done
    _print_completion(container, config)

    return container


# ============================================
# Container
# ============================================

def _create_container(parent, config):
    """Create or recreate the window_manager Container COMP."""

    name = config["container_name"]
    print(f"\n[1/7] Creating container '{name}'...")

    existing = parent.op(name)
    if existing:
        existing.destroy()
        print(f"  Removed existing {name}")

    container = parent.create(containerCOMP, name)
    container.nodeX = -400
    container.nodeY = 600
    container.color = (0.2, 0.5, 0.8)

    container.par.w = GLOBAL_CONTEXT.width
    container.par.h = GLOBAL_CONTEXT.height

    print(f"  OK Created: {container.path}")
    print(f"  Resolution: {GLOBAL_CONTEXT.width}x{GLOBAL_CONTEXT.height}")
    return container


# ============================================
# TOP Source Inputs (In TOPs)
# ============================================

def _create_top_inputs(container, config):
    """Create 4 In TOPs for wired TOP sources."""

    num_inputs = config["num_top_inputs"]
    views = config["views"]
    switch_cfg = config.get("main_view_switch", {})
    switch_labels = switch_cfg.get("labels", [])
    switch_indices = switch_cfg.get("input_indices", [])

    print(f"\n[2/7] Creating {num_inputs} TOP source inputs...")

    in_tops = []
    for i in range(num_inputs):
        in_top = container.create(inTOP, f'in{i + 1}')
        in_top.nodeX = -200 + (i * 250)
        in_top.nodeY = 300

        # Find label for this input
        label = ""
        for name, view_def in views.items():
            if view_def.get("type") == "top" and view_def.get("input_index") == i:
                label = f" ('{name}')"
                break

        if not label and i in switch_indices:
            pos = switch_indices.index(i)
            if pos < len(switch_labels):
                label = f" ('{switch_labels[pos]}' -> Switch TOP)"

        print(f"  OK in{i + 1}{label}: {in_top.path}")
        in_tops.append(in_top)

    return in_tops


# ============================================
# Null TOPs for Intro Videos
# ============================================

def _create_intro_wrappers(container, config, in_tops):
    """Create Null TOPs for intro video In TOPs (in1, in2).

    Window COMP can display Null TOPs directly via winop.
    Container COMPs with internal Out TOPs do not render in windows.
    """

    views = config["views"]
    print(f"\n[3/7] Creating intro video Null TOPs...")

    for name, view_def in views.items():
        if view_def.get("type") != "top":
            continue

        idx = view_def["input_index"]
        if idx >= len(in_tops):
            print(f"  SKIP {name}: input_index {idx} out of range")
            continue

        parent_in_top = in_tops[idx]
        null_name = f'top_view_{idx}'

        null_top = container.create(nullTOP, null_name)
        null_top.nodeX = parent_in_top.nodeX
        null_top.nodeY = 100
        null_top.inputConnectors[0].connect(parent_in_top)

        print(f"  OK {null_name}: Null TOP from in{idx + 1} ('{name}')")


# ============================================
# Switch TOP for avatar/real_life + wrapper
# ============================================

def _create_main_view_switch(container, config, in_tops):
    """Create Switch TOP for avatar/real_life transition with wrapper Container."""

    switch_cfg = config.get("main_view_switch", {})
    input_indices = switch_cfg.get("input_indices", [2, 3])
    labels = switch_cfg.get("labels", ["avatar", "real_life"])
    default_index = switch_cfg.get("default_index", 0)

    print(f"\n[4/7] Creating main_view Switch TOP...")

    # Create the Switch TOP
    switch_top = container.create(switchTOP, 'main_view_switch')
    switch_x = -200 + (input_indices[0] * 250)
    switch_top.nodeX = switch_x + 125  # center between the two inputs
    switch_top.nodeY = 100

    # Wire avatar and real_life In TOPs as inputs
    for connector_idx, in_idx in enumerate(input_indices):
        if in_idx < len(in_tops):
            switch_top.inputConnectors[connector_idx].connect(in_tops[in_idx])
            label = labels[connector_idx] if connector_idx < len(labels) else f"input {in_idx}"
            print(f"  Wired in{in_idx + 1} ('{label}') -> Switch input {connector_idx}")

    # Set default index and enable blend for transitions
    switch_top.par.index = default_index
    switch_top.par.blend = True

    default_label = labels[default_index] if default_index < len(labels) else str(default_index)
    print(f"  Default: {default_label} (index {default_index}), blend enabled")

    # Create Null TOP after Switch TOP output
    # Window COMP renders Null TOPs correctly (not Container COMPs with Out TOPs)
    null_out = container.create(nullTOP, 'main_view_display')
    null_out.nodeX = switch_top.nodeX
    null_out.nodeY = -50
    null_out.inputConnectors[0].connect(switch_top)

    print(f"  OK main_view_display: Null TOP from Switch TOP output")


# ============================================
# Window COMPs
# ============================================

def _create_window_comps(container, config):
    """Create Window COMPs for each screen."""

    num_screens = config["num_screens"]
    print(f"\n[5/7] Creating {num_screens} Window COMPs...")

    for screen_idx in range(num_screens):
        window = container.create(windowCOMP, f'screen{screen_idx}_window')
        window.nodeX = -200 + (screen_idx * 400)
        window.nodeY = -300

        monitor = config.get("screen_monitors", {}).get(
            screen_idx, screen_idx + 1
        )
        window.par.monitor = monitor

        if config.get("borderless", True):
            window.par.borders = False

        window.par.size = 'exclusive'

        window.par.winw = GLOBAL_CONTEXT.width
        window.par.winh = GLOBAL_CONTEXT.height

        print(f"  OK screen{screen_idx}_window: monitor={monitor}, "
              f"borderless={config.get('borderless', True)}")


# ============================================
# View Registry Table DAT
# ============================================

def _create_view_registry(container, config):
    """Create Table DAT with view name -> type -> path mapping."""

    print(f"\n[6/7] Creating view registry table...")

    table = container.create(tableDAT, 'view_registry')
    table.nodeX = 600
    table.nodeY = 300

    table.clear()
    table.appendRow(["name", "type", "path"])

    views = config.get("views", {})
    for name, view_def in views.items():
        vtype = view_def["type"]
        if vtype == "top":
            path = f"top_view_{view_def['input_index']}"
        elif vtype == "switch_top":
            path = "main_view_display"
        else:
            path = view_def["path"]
        table.appendRow([name, vtype, path])
        print(f"  [{vtype}] {name} -> {path}")


# ============================================
# Initialize WindowManager
# ============================================

def _initialize_manager(container, config):
    """Create WindowManager instance, store it, and apply default phase."""

    print(f"\n[7/7] Initializing WindowManager...")

    from window_manager import WindowManager

    wm = WindowManager(config, td_op=op)

    # Store on container
    container.store('window_manager', wm)

    # Apply default phase (sets winop for each screen)
    default_phase = config.get("default_phase", "intro")
    phases = config.get("phases", {})
    phase_def = phases.get(default_phase, {})

    for screen_idx, view_name in phase_def.items():
        if view_name in wm._view_paths:
            target_path = wm._view_paths[view_name]
            window = container.op(f'screen{screen_idx}_window')
            if window:
                window.par.winop = target_path
                wm._screen_views[screen_idx] = view_name
                print(f"  Screen {screen_idx}: '{view_name}' ({target_path})")

    print(f"  Phase: '{default_phase}'")
    print(f"  OK WindowManager stored at {container.path}")


# ============================================
# Completion
# ============================================

def _print_completion(container, config):
    """Print setup completion message."""

    print("\n" + "=" * 60)
    print("Window Manager Setup Complete!")
    print("=" * 60)

    print(f"\nOperator network: {container.path}")

    print(f"\nTOP inputs to wire:")
    switch_cfg = config.get("main_view_switch", {})
    labels = switch_cfg.get("labels", [])
    input_indices = switch_cfg.get("input_indices", [])

    for i in range(config["num_top_inputs"]):
        view_name = None
        for name, view_def in config["views"].items():
            if view_def.get("type") == "top" and view_def.get("input_index") == i:
                view_name = name
                break
        if view_name:
            print(f"  in{i+1} <- {view_name}")
        elif i in input_indices:
            pos = input_indices.index(i)
            lbl = labels[pos] if pos < len(labels) else f"switch_{pos}"
            print(f"  in{i+1} <- {lbl} (-> Switch TOP)")

    print(f"\nCOMP sources (no wiring needed):")
    for name, view_def in config["views"].items():
        if view_def.get("type") == "comp":
            print(f"  {name} -> {view_def['path']}")

    print(f"\nPhases & Signals:")
    print(f"  INTRO:    screen0=intro_video_1, screen1=intro_video_2")
    print(f"  ACTIVE:   screen0=chat, screen1=avatar (Switch TOP)")
    print(f"  REVEALED: screen0=chat, screen1=real_life (Switch TOP)")
    print(f"")
    print(f"  wm.signal_intro_complete()  # INTRO -> ACTIVE")
    print(f"  wm.signal_reveal()          # ACTIVE -> REVEALED")
    print(f"  wm.signal_reset()           # any -> INTRO")

    print(f"\nPython API:")
    print(f"  wm = op('{container.path}').fetch('window_manager')")
    print(f"  wm.open_all()                    # open windows")
    print(f"  wm.signal_intro_complete()       # chat + avatar")
    print(f"  wm.signal_reveal()               # avatar -> real_life")
    print(f"  wm.set_switch_blend(0.5)         # mid-transition")
    print(f"  wm.phase                         # current phase name")

    print("=" * 60)


# ============================================
# Execute
# ============================================

setup_window_manager()
