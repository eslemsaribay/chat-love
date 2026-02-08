"""
Window Manager - Multi-monitor view switching API

Manages view routing and window display across multiple screens.
Supports TOP sources (wired inputs), COMP sources (external panels),
and a Switch TOP for avatar/real_life transitions.

Phases:
    INTRO     - Both screens show intro videos
    ACTIVE    - Screen 0 = chat, Screen 1 = avatar (via Switch TOP)
    REVEALED  - Screen 0 = chat, Screen 1 = real_life (via Switch TOP)

Signals:
    signal_intro_complete()  - INTRO -> ACTIVE
    signal_reveal()          - ACTIVE -> REVEALED
    signal_reset()           - any -> INTRO

Usage from any TD script:
    wm = op('/project1/window_manager').fetch('window_manager')
    wm.signal_intro_complete()   # transition to chat + avatar
    wm.signal_reveal()           # transition avatar -> real_life
"""

from typing import Dict, Optional, List, Callable


# Phase constants
PHASE_INTRO = "intro"
PHASE_ACTIVE = "active"
PHASE_REVEALED = "revealed"


class ViewSwitchEvent:
    """Event data for view switch callbacks."""

    def __init__(self, screen_index: int, view_name: str,
                 previous_view: Optional[str] = None):
        self.screen_index = screen_index
        self.view_name = view_name
        self.previous_view = previous_view

    def __repr__(self):
        return (f"ViewSwitchEvent(screen={self.screen_index}, "
                f"view='{self.view_name}', prev='{self.previous_view}')")


class PhaseChangeEvent:
    """Event data for phase change callbacks."""

    def __init__(self, phase: str, previous_phase: Optional[str] = None):
        self.phase = phase
        self.previous_phase = previous_phase

    def __repr__(self):
        return (f"PhaseChangeEvent(phase='{self.phase}', "
                f"prev='{self.previous_phase}')")


class WindowManager:
    """
    Manages multi-monitor view switching for TouchDesigner.

    Controls Window COMPs by changing their winop parameter to route
    different views to different screens/monitors.

    View types:
    - TOP views: Wired In TOPs, auto-wrapped in Container COMPs.
    - COMP views: External COMPs referenced by path.
    - Switch TOP view: avatar/real_life routed through a Switch TOP
      with blend support for transition animation.
    """

    def __init__(self, config: dict, td_op=None):
        """
        Args:
            config: Configuration dictionary from window_manager_config.py
            td_op: TouchDesigner's op() function. Required because imported
                   Python modules don't have op() in their namespace.
        """
        self.config = config
        self._op = td_op
        self.container_path = (
            f"{config['parent_path']}/{config['container_name']}"
        )
        self.num_screens = config["num_screens"]

        # View paths: name -> operator path (for winop)
        self._view_paths: Dict[str, str] = {}

        # Current view per screen: screen_index -> view_name
        self._screen_views: Dict[int, Optional[str]] = {
            i: None for i in range(self.num_screens)
        }

        # Current phase
        self._phase: str = config.get("default_phase", PHASE_INTRO)

        # Event listeners
        self._view_listeners: List[Callable[[ViewSwitchEvent], None]] = []
        self._phase_listeners: List[Callable[[PhaseChangeEvent], None]] = []

        # Build view paths from config
        self._build_view_paths(config.get("views", {}))

    # ================================================================
    # View Registry
    # ================================================================

    def _build_view_paths(self, views: dict):
        """Build _view_paths from config view definitions."""
        for name, view_def in views.items():
            if view_def["type"] == "top":
                idx = view_def["input_index"]
                self._view_paths[name] = f"top_view_{idx}"
            elif view_def["type"] == "comp":
                self._view_paths[name] = view_def["path"]
            elif view_def["type"] == "switch_top":
                self._view_paths[name] = "main_view_display"

    def register_top_view(self, name: str, input_index: int):
        """Register a named view for a wired TOP input."""
        self._view_paths[name] = f"top_view_{input_index}"
        self._update_registry_table()
        print(f"[WINDOW MGR] Registered TOP view '{name}' -> top_view_{input_index}")

    def register_comp_view(self, name: str, comp_path: str):
        """Register a named view for an external COMP."""
        self._view_paths[name] = comp_path
        self._update_registry_table()
        print(f"[WINDOW MGR] Registered COMP view '{name}' -> {comp_path}")

    def unregister_view(self, name: str):
        """Remove a named view from the registry."""
        if name in self._view_paths:
            del self._view_paths[name]
            self._update_registry_table()
            print(f"[WINDOW MGR] Unregistered view '{name}'")

    def get_views(self) -> Dict[str, str]:
        """Return copy of view name -> path mapping."""
        return dict(self._view_paths)

    def get_view_names(self) -> List[str]:
        """Return list of registered view names."""
        return list(self._view_paths.keys())

    # ================================================================
    # Phases & Signals
    # ================================================================

    @property
    def phase(self) -> str:
        """Current phase: 'intro', 'active', or 'revealed'."""
        return self._phase

    def signal_intro_complete(self):
        """Signal: intro phase is done.

        Transitions INTRO -> ACTIVE:
        - Screen 0 switches to chat
        - Screen 1 switches to main_view (avatar via Switch TOP)
        - Switch TOP set to index 0 (avatar)
        """
        if self._phase != PHASE_INTRO:
            print(f"[WINDOW MGR] WARNING: signal_intro_complete called "
                  f"during '{self._phase}' phase, expected '{PHASE_INTRO}'")

        # Set Switch TOP to avatar before switching views
        self._set_switch_index(0)

        self._apply_phase(PHASE_ACTIVE)

    def signal_reveal(self):
        """Signal: reveal real_life view.

        Transitions ACTIVE -> REVEALED:
        - Screen layout stays the same (chat + main_view)
        - Switch TOP transitions from avatar (0) to real_life (1)
        """
        if self._phase != PHASE_ACTIVE:
            print(f"[WINDOW MGR] WARNING: signal_reveal called "
                  f"during '{self._phase}' phase, expected '{PHASE_ACTIVE}'")

        self._set_switch_index(1)

        previous = self._phase
        self._phase = PHASE_REVEALED
        event = PhaseChangeEvent(PHASE_REVEALED, previous)
        self._fire_phase_event(event)
        print(f"[WINDOW MGR] Phase: '{previous}' -> '{PHASE_REVEALED}' "
              f"(Switch TOP -> real_life)")

    def signal_reset(self):
        """Signal: reset to intro phase.

        Resets everything:
        - Both screens back to intro videos
        - Switch TOP back to avatar (index 0)
        """
        self._set_switch_index(0)
        self._apply_phase(PHASE_INTRO)

    def _apply_phase(self, phase: str):
        """Apply a phase: switch all screens to phase layout."""
        phases = self.config.get("phases", {})
        phase_def = phases.get(phase)
        if phase_def is None:
            print(f"[WINDOW MGR] ERROR: Unknown phase '{phase}'")
            return

        previous = self._phase
        self._phase = phase

        for screen_idx, view_name in phase_def.items():
            self.switch_view(screen_idx, view_name)

        event = PhaseChangeEvent(phase, previous)
        self._fire_phase_event(event)
        print(f"[WINDOW MGR] Phase: '{previous}' -> '{phase}'")

    # ================================================================
    # Switch TOP Control (avatar / real_life)
    # ================================================================

    def _get_switch_op(self):
        """Get the main_view Switch TOP operator."""
        path = f"{self.container_path}/main_view_switch"
        return self._op(path)

    def _set_switch_index(self, index: int):
        """Set the Switch TOP index (0=avatar, 1=real_life)."""
        switch_op = self._get_switch_op()
        if switch_op is None:
            print("[WINDOW MGR] ERROR: main_view_switch not found")
            return
        switch_op.par.index = index

        labels = self.config.get("main_view_switch", {}).get("labels", [])
        label = labels[index] if index < len(labels) else str(index)
        print(f"[WINDOW MGR] Switch TOP -> {label} (index {index})")

    def get_switch_index(self) -> int:
        """Get current Switch TOP index."""
        switch_op = self._get_switch_op()
        if switch_op is None:
            return 0
        return int(switch_op.par.index.eval())

    def set_switch_blend(self, value: float):
        """Set the Switch TOP index as a float for blend transitions.

        0.0 = fully avatar, 1.0 = fully real_life.
        Intermediate values blend between the two (requires blend enabled).
        """
        switch_op = self._get_switch_op()
        if switch_op is None:
            print("[WINDOW MGR] ERROR: main_view_switch not found")
            return
        switch_op.par.index = value

    # ================================================================
    # View Switching (Core API)
    # ================================================================

    def switch_view(self, screen_index: int, view_name: str):
        """Switch a screen to display a named view.

        Args:
            screen_index: Which screen (0-based)
            view_name: Name of the registered view to display
        """
        if view_name not in self._view_paths:
            available = ", ".join(self._view_paths.keys())
            raise ValueError(
                f"Unknown view '{view_name}'. Available: {available}"
            )
        if screen_index < 0 or screen_index >= self.num_screens:
            raise ValueError(
                f"Invalid screen_index {screen_index}. "
                f"Range: 0-{self.num_screens - 1}"
            )

        target_path = self._view_paths[view_name]
        previous_view = self._screen_views.get(screen_index)

        window_path = f"{self.container_path}/screen{screen_index}_window"
        window_op = self._op(window_path)
        if window_op is None:
            print(f"[WINDOW MGR] ERROR: Window not found at {window_path}")
            return

        window_op.par.winop = target_path
        self._screen_views[screen_index] = view_name

        event = ViewSwitchEvent(
            screen_index=screen_index,
            view_name=view_name,
            previous_view=previous_view,
        )
        self._fire_view_event(event)

        print(
            f"[WINDOW MGR] Screen {screen_index}: "
            f"'{previous_view}' -> '{view_name}' ({target_path})"
        )

    def get_current_view(self, screen_index: int) -> Optional[str]:
        """Get the current view name for a screen."""
        return self._screen_views.get(screen_index)

    def swap_screens(self):
        """Swap the views between screen 0 and screen 1."""
        if self.num_screens < 2:
            return
        view0 = self._screen_views.get(0)
        view1 = self._screen_views.get(1)
        if view1:
            self.switch_view(0, view1)
        if view0:
            self.switch_view(1, view0)

    # ================================================================
    # Window Management
    # ================================================================

    def open_all(self):
        """Open all Window COMPs on their assigned monitors."""
        for i in range(self.num_screens):
            self.open_screen(i)

    def open_screen(self, screen_index: int):
        """Open a specific screen's window on its assigned monitor."""
        window_path = f"{self.container_path}/screen{screen_index}_window"
        window_op = self._op(window_path)
        if window_op is None:
            print(f"[WINDOW MGR] ERROR: Window not found at {window_path}")
            return

        monitor = self.config.get("screen_monitors", {}).get(
            screen_index, screen_index + 1
        )
        window_op.par.monitor = monitor
        window_op.par.winopen.pulse()
        print(f"[WINDOW MGR] Opened screen {screen_index} on monitor {monitor}")

    def close_all(self):
        """Close all Window COMPs."""
        for i in range(self.num_screens):
            self.close_screen(i)

    def close_screen(self, screen_index: int):
        """Close a specific screen's window."""
        window_path = f"{self.container_path}/screen{screen_index}_window"
        window_op = self._op(window_path)
        if window_op is None:
            return
        window_op.par.winclose.pulse()
        print(f"[WINDOW MGR] Closed screen {screen_index}")

    def is_open(self, screen_index: int) -> bool:
        """Check if a screen's window is currently open."""
        window_path = f"{self.container_path}/screen{screen_index}_window"
        window_op = self._op(window_path)
        if window_op is None:
            return False
        return window_op.isOpen

    # ================================================================
    # Event System
    # ================================================================

    def add_listener(self, callback: Callable[[ViewSwitchEvent], None]):
        """Register a callback for view switch events."""
        self._view_listeners.append(callback)

    def remove_listener(self, callback):
        """Remove a view switch callback."""
        if callback in self._view_listeners:
            self._view_listeners.remove(callback)

    def add_phase_listener(self, callback: Callable[[PhaseChangeEvent], None]):
        """Register a callback for phase change events."""
        self._phase_listeners.append(callback)

    def remove_phase_listener(self, callback):
        """Remove a phase change callback."""
        if callback in self._phase_listeners:
            self._phase_listeners.remove(callback)

    def _fire_view_event(self, event: ViewSwitchEvent):
        """Notify view listeners."""
        for listener in self._view_listeners:
            try:
                listener(event)
            except Exception as e:
                print(f"[WINDOW MGR] View listener error: {e}")

    def _fire_phase_event(self, event: PhaseChangeEvent):
        """Notify phase listeners."""
        for listener in self._phase_listeners:
            try:
                listener(event)
            except Exception as e:
                print(f"[WINDOW MGR] Phase listener error: {e}")

    # ================================================================
    # Internal
    # ================================================================

    def _update_registry_table(self):
        """Sync the view_registry Table DAT with current state."""
        table_path = f"{self.container_path}/view_registry"
        table_op = self._op(table_path)
        if table_op is None:
            return
        table_op.clear()
        table_op.appendRow(["name", "type", "path"])
        for name, path in self._view_paths.items():
            if path.startswith("top_view_"):
                view_type = "top"
            elif path == "main_view_display":
                view_type = "switch_top"
            else:
                view_type = "comp"
            table_op.appendRow([name, view_type, path])

    def reset(self):
        """Reset to intro phase (alias for signal_reset)."""
        self.signal_reset()
