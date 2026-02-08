"""
TouchDesigner Master Setup Script
Runs all setup scripts in order. Use in TD textport:

    import sys; sys.path.insert(0, project.folder)
    exec(open(project.folder + '/setup_td.py').read())

After setup, `recalibrate()` is available in the textport.
"""

import sys
import traceback

# Ensure project folder is on path
if project.folder not in sys.path:
    sys.path.insert(0, project.folder)

print("=" * 60)
print("MASTER SETUP: Running all setup scripts")
print("=" * 60)

_setup_scripts = [
    ('Chat App',        'setup_chat_app.py'),
    ('Head Tracking',   'setup_head_tracking.py'),
    ('Auto-Scale',      'setup_auto_scale.py'),
    ('Window Manager',  'setup_window_manager.py'),
]

_failed = []

for label, script in _setup_scripts:
    print(f"\n{'=' * 60}")
    print(f"RUNNING: {label} ({script})")
    print(f"{'=' * 60}")
    try:
        exec(open(project.folder + '/' + script).read())
        print(f"\nOK: {label} complete")
    except Exception as e:
        print(f"\nFAILED: {label} - {e}")
        traceback.print_exc()
        _failed.append(label)

# Register recalibrate() in textport globals
# setup_head_tracking.py defines it via exec(), so it should already
# be in scope. Verify and re-export if needed.
if 'recalibrate' not in dir():
    try:
        from setup_head_tracking import recalibrate, disable_tracking, enable_tracking, reset_tracking
    except ImportError:
        print("\nWARNING: Could not register recalibrate() - head tracking may have failed")

print(f"\n{'=' * 60}")
print("MASTER SETUP COMPLETE")
if _failed:
    print(f"  FAILED: {', '.join(_failed)}")
else:
    print("  All scripts ran successfully")
print(f"{'=' * 60}")
print("\nAvailable commands:")
print("  recalibrate()      - Reset head tracking neutral position")
print("  disable_tracking() - Pause head tracking")
print("  enable_tracking()  - Resume head tracking")
print("  reset_tracking()   - Full head tracking reset")
