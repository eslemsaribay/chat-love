# TouchDesigner Chat Application - AI Context

## Project Overview
TouchDesigner chat app with Ollama LLM integration. Text-based chat with username extraction, scrollable viewport, and real-time LLM responses. Multi-monitor window management for routing views to screens.

## Architecture
- **chat_manager.py**: Core state (messages, input, scroll, username)
- **setup_chat_app.py**: TD operator setup, keyboard/mouse callbacks
- **chat_config.py**: Layout, colors, scroll settings
- **chat_llm_worker.py**: Background thread for LLM calls
- **llm/**: Ollama API integration, prompts, examples
- **window_manager.py**: Multi-monitor view switching API
- **window_manager_config.py**: View definitions, monitor assignments
- **setup_window_manager.py**: Creates window manager operator network

## CRITICAL: TouchDesigner Y-Axis (Text COMP Specification DAT)
- **Bottom-left origin**: Y=0 is at BOTTOM of panel, Y increases UPWARD
- Higher Y value = higher position on screen (toward top)
- Lower Y value = lower position on screen (toward bottom)
- Reference: https://docs.derivative.ca/Text_COMP

## Scroll System - ANCHOR FROM BOTTOM
- Content is anchored at the BOTTOM of the visible window
- When `scroll_offset = 0`: Input line is at window bottom, newest messages visible - DEFAULT VIEW
- When `scroll_offset > 0`: Content shifts DOWN (lower Y), revealing older messages from above
- Formula: `current_y = first_line_y - scroll_offset` where:
  - `first_line_y = window_bottom_y + (total_lines - 1) * line_height`
  - `window_bottom_y = canvas_height - (window_top_px + window_height)` (TD coordinate)
- Window clipping: Only render lines where `window_bottom_y <= current_y <= window_top_y`
- Arrow UP = scroll UP (increase offset, content moves DOWN, see older messages)
- Arrow DOWN = scroll DOWN (decrease offset, content moves UP, see newer messages)
- Bounds: offset ∈ [0, max_scroll] where max = max(0, content_height - window_height)
- Auto-scroll on new message: `reset_scroll()` sets `offset = 0` (shows bottom/newest)

## Text Rendering
- Text COMP in Specification DAT mode (bottom-left origin coordinate system)
- Per-row positioning: `[x, y, text, fontsize, r, g, b]`
- X/Y measured from bottom-left corner in panel units
- Manual word wrap via Python `textwrap.wrap()` (spec DAT doesn't auto-wrap)

## LLM Context Management
- Username extraction: Use temp LLM context, then CLEAR to prevent pollution
- Chat conversations: Pass `"context": []` to Ollama to prevent KV cache persistence
- F5 reset: Clears messages, scroll, LLM context, reloads config/prompt modules

## Module Reload on F5
F5 reset reloads:
- `chat_config.py`
- `llm.prompts.examples`
- `llm.prompts.system_instructions`

## Setup Execution
```python
import sys; sys.path.insert(0, project.folder); exec(open(project.folder + '/setup_chat_app.py').read())
```

## Username Extraction
- First message triggers extraction via LLM
- Validates: alphabetic ratio, no special chars `<>_`
- Supports international names (Turkish, Japanese, Arabic examples in prompt)

## Message Flow
1. User types → `append_to_input()`
2. ENTER → `submit_input()` → username extraction OR chat LLM
3. LLM worker (background thread) → `add_assistant_message()`
4. Display update → `_regenerate_table()` → Text COMP render

## Key Files
- `chat_manager.py:224` - Auto-scroll on message add (`reset_scroll()`)
- `setup_chat_app.py:100` - `_regenerate_table_from_manager()` - Main scroll/rendering logic
- `setup_chat_app.py:460` - `_regenerate_table()` in callbacks - Keyboard/mouse scroll rendering
- `chat_config.py` - Window bounds, scroll step
- `llm/core/ollama_inference_engine.py` - Context clearing (`"context": []`)

## Window Manager
Multi-monitor view switching via `winop` parameter on Window COMPs.

### Architecture
- Container COMP `/project1/window_manager` with 4 In TOPs + 1 COMP reference
- **in1/in2**: intro_video_1, intro_video_2 → wrapped in Container COMPs (`top_view_0`, `top_view_1`)
- **in3/in4**: avatar, real_life → routed through Switch TOP (`main_view_switch`) → `main_view_display`
- **chat**: COMP source, `/project1/chat_application` (referenced by path)
- Switch TOP has blend enabled for transition animation between avatar/real_life

### Phases & Signals
- **INTRO**: screen0=intro_video_1, screen1=intro_video_2
- **ACTIVE**: screen0=chat, screen1=main_view (avatar via Switch TOP index 0)
- **REVEALED**: screen0=chat, screen1=main_view (real_life via Switch TOP index 1)
- `signal_intro_complete()`: INTRO → ACTIVE
- `signal_reveal()`: ACTIVE → REVEALED
- `signal_reset()`: any → INTRO

### API (from any script)
```python
wm = op('/project1/window_manager').fetch('window_manager')
wm.signal_intro_complete()               # INTRO -> ACTIVE
wm.signal_reveal()                       # ACTIVE -> REVEALED
wm.signal_reset()                        # -> INTRO
wm.open_all() / wm.close_all()          # window control
wm.set_switch_blend(0.5)                 # mid-transition blend
wm.phase                                 # current phase name
wm.add_phase_listener(callback)          # listen for PhaseChangeEvent
```

### Setup
```python
import sys; sys.path.insert(0, project.folder); exec(open(project.folder + '/setup_window_manager.py').read())
```
