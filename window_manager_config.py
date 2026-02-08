"""
Window Manager Configuration
All configurable constants for multi-monitor view switching
"""

from global_context import GLOBAL_CONTEXT

WINDOW_MANAGER_CONFIG = {
    # Resolution (from global context)
    "width": GLOBAL_CONTEXT.width,
    "height": GLOBAL_CONTEXT.height,

    # Number of screens/windows to manage
    "num_screens": 2,

    # Number of In TOPs for wired TOP sources
    "num_top_inputs": 4,

    # Monitor assignments (TD monitor indices, 0-based)
    "screen_monitors": {
        0: 0,   # screen0 -> monitor 0 (primary)
        1: 1,   # screen1 -> monitor 1 (secondary)
    },

    # Window settings
    "borderless": True,

    # View definitions
    # "top" = wired through In TOP at input_index
    # "comp" = external COMP referenced by path
    # "switch_top" = output of the main_view Switch TOP (avatar/real_life)
    "views": {
        "intro_video_1": {"type": "top", "input_index": 0},
        "intro_video_2": {"type": "top", "input_index": 1},
        "main_view":     {"type": "switch_top"},
        "chat":          {"type": "comp", "path": "/project1/chat_application"},
    },

    # Switch TOP for avatar/real_life transition
    # in3 (avatar) and in4 (real_life) are wired as inputs
    "main_view_switch": {
        "input_indices": [2, 3],       # indices into In TOPs (in3, in4)
        "labels": ["avatar", "real_life"],
        "default_index": 0,            # start on avatar
    },

    # Phase definitions (what each screen shows per phase)
    "phases": {
        "intro": {
            0: "intro_video_1",
            1: "intro_video_2",
        },
        "active": {
            0: "chat",
            1: "main_view",    # Switch TOP at avatar (index 0)
        },
        "revealed": {
            0: "chat",
            1: "main_view",    # Switch TOP at real_life (index 1)
        },
    },

    # Default phase on startup
    "default_phase": "intro",

    # Key bindings for window manager signals
    "key_bindings": {
        "signal_intro_complete": "F3",  # skip intro (only during INTRO phase)
        "signal_reveal": "space",       # trigger reveal (only when chat_manager.reveal_ready)
        "signal_reset": "F9",           # reset to INTRO phase
    },

    # TD operator path where window_manager container is created
    "parent_path": "/project1",
    "container_name": "window_manager",
}
